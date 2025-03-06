from flask import Blueprint, request, jsonify
import uuid
import asyncio
import asyncpg
import json
from app.config import Config
from app.request_logger import RequestLogger
from app.llm_processor import GeminiProcessor
from app.request_classifier import RequestClassifier
from app.semaphore_manager import SemaphoreManager
from app.utils import custom_logging
from asgiref.sync import async_to_sync

api_blueprint = Blueprint("api", __name__)
db_pool = None
request_logger = None
gemini_processor = GeminiProcessor(Config.GEMINI_API_KEY)
request_classifier = RequestClassifier()
semaphore_manager = SemaphoreManager(Config.REDIS_URL, Config.RATE_LIMITS, 5)
logger = custom_logging()
redis_client = None
app_loop = None

# Initialize async resources
async def init_async_resources():
    global db_pool, request_logger, redis_client, app_loop
    app_loop = asyncio.get_running_loop()
    db_pool = await asyncpg.create_pool(Config.DATABASE_URL)
    request_logger = RequestLogger(db_pool)
    await semaphore_manager.initialize()
    
    # Initialize Redis client for queue operations
    import aioredis
    redis_client = await aioredis.from_url(Config.REDIS_URL, decode_responses=True)

# Run initialization
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(init_async_resources())

# Helper function to run async code in the main application loop
def run_async(coro):
    if asyncio.get_event_loop() == app_loop:
        return asyncio.run_coroutine_threadsafe(coro, app_loop).result()
    else:
        return async_to_sync(lambda: coro)()

@api_blueprint.route('/submit', methods=['POST'])
def submit_request():
    """Synchronous wrapper around the async implementation"""
    return run_async(_submit_request())

async def _submit_request():
    """Async implementation of submit_request"""
    files = request.files.getlist("file")
    text_data = None
    if request.content_type == "application/json":
        text_data = request.json.get("text")
    else:
        text_data = request.form.get("text")
    print(files)
    if not files and not text_data:
        return jsonify({"error": "Either text or a file must be provided"}), 400
    
    req_id = str(uuid.uuid4())
    
    # Use the synchronous version to avoid await issues
    input_type, input_data = request_classifier.classify_request_sync(text_data, files)
    
    try:
        # Try to acquire the semaphore
        await semaphore_manager.acquire_semaphore(input_type)
        
        # If successful, process the request immediately
        response_data = await gemini_processor.process_llm_request(input_type, input_data)        
        await request_logger.save_request(req_id, input_type, input_data, response_data)
        
        # Release the semaphore
        await semaphore_manager.release_semaphore(input_type)
        
        return jsonify({"request_id": req_id, "response": response_data})
        
    except TimeoutError:
        # If semaphore acquisition fails, queue the request for later processing
        logger.warning(f"Request {req_id} rate-limited. Queuing for later processing.")
        
        # Save the request with 'queued' status
        await request_logger.save_request(req_id, input_type, input_data, None, "queued")
        
        # Add to the appropriate Redis queue
        queue_key = f"queue:{input_type}"
        request_data = {
            "id": req_id,
            "input_type": input_type,
            "input_data": str(input_data)
        }
        await redis_client.rpush(queue_key, json.dumps(request_data))
        
        # Return a response indicating the request is queued
        return jsonify({
            "request_id": req_id, 
            "status": "queued",
            "message": "Your request has been queued due to high demand. Check status later."
        }), 202

    except Exception as e:
        logger.error(f"Error processing request {req_id}: {str(e)}")
        return jsonify({"error": "Internal server error. Please try again later."}), 500

@api_blueprint.route('/status/<request_id>', methods=['GET'])
def check_status(request_id):
    """Synchronous wrapper around the async implementation"""
    return run_async(_check_status(request_id))

async def _check_status(request_id):
    """Async implementation of check_status"""
    try:
        request_data = await request_logger.get_request(request_id)
        if not request_data:
            return jsonify({"error": "Request not found"}), 404
            
        return jsonify(request_data)
    except Exception as e:
        logger.error(f"Error checking status for request {request_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

