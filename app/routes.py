from fastapi import FastAPI, File, UploadFile, Form, HTTPException, APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional
import uuid
import asyncpg
import json
import redis.asyncio as redis
from app.config import Config
from app.request_logger import RequestLogger
from app.llm_processor import GeminiProcessor
from app.request_classifier import RequestClassifier
from app.semaphore_manager import SemaphoreManager
from app.utils import custom_logging
from pydantic import BaseModel


router = APIRouter()
db_pool = None
request_logger = None
gemini_processor = GeminiProcessor(Config.GEMINI_API_KEY)
request_classifier = RequestClassifier(gemini_processor=gemini_processor)
semaphore_manager = SemaphoreManager(Config.REDIS_URL, Config.RATE_LIMITS, Config.SEMAPHORE_TIMEOUT)
logger = custom_logging()
redis_client = None

@router.on_event("startup")
async def startup_event():
    """Initialize async resources when the application starts"""
    global db_pool, request_logger, redis_client
    
    # Initialize database connection pool
    db_pool = await asyncpg.create_pool(Config.DATABASE_URL)
    request_logger = RequestLogger(db_pool)
    
    # Initialize Redis client
    redis_client = await redis.from_url(Config.REDIS_URL, decode_responses=True)
    
    # Initialize semaphore manager
    await semaphore_manager.initialize()

@router.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the application shuts down"""
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()
    # Cleanup semaphore manager
    await semaphore_manager.cleanup()

class TextRequest(BaseModel):
    text: str

@router.post("/submit")
async def submit_request(
    text: Optional[str] = Form(None),
    files: List[UploadFile] = File([])
):
    if not files and not text:
        raise HTTPException(status_code=400, detail="Either text or a file must be provided")
    
    req_id = str(uuid.uuid4())
    
    input_type, input_data = await request_classifier.classify_request(text, files)
    logger.info(f"Processing request: {req_id} of type: {input_type}")
    try:
        # Try to acquire the semaphore
        await semaphore_manager.acquire_semaphore(input_type)
        
        try:
            # If successful, process the request immediately
            response_data = await gemini_processor.process_llm_request(input_type, input_data)        
            await request_logger.save_request(req_id, input_type, input_data, response_data)
            
            return {"request_id": req_id, "response": response_data}
            
        finally:
            # Always release the semaphore if we acquired it
            await semaphore_manager.release_semaphore(input_type)
        
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
        return JSONResponse(
            status_code=202,
            content={
                "request_id": req_id,
                "status": "queued",
                "message": "Your request has been queued due to high demand. Check status later."
            }
        )

    except Exception as e:
        logger.error(f"Error processing request {req_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@router.get("/status/{request_id}")
async def check_status(request_id: str):
    """Endpoint to check the status of a request"""
    try:
        request_data = await request_logger.get_request(request_id)
        if not request_data:
            raise HTTPException(status_code=404, detail="Request not found")
            
        return request_data
    except Exception as e:
        logger.error(f"Error checking status for request {request_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/stream")
async def stream_response(text: Optional[str] = Form(None)):
    async def generate_chunks():
        async for chunk in gemini_processor.stream_content(text):
            yield chunk

    return StreamingResponse(generate_chunks(), media_type="text/plain")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        async with db_pool.acquire() as conn:
            await conn.execute("SELECT 1")
        
        # Check Redis connection
        await redis_client.ping()
        
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

