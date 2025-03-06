import redis.asyncio as redis
import asyncpg
import asyncio
import time
import random
import json
from app.config import Config
from app.llm_processor import GeminiProcessor
from app.semaphore_manager import SemaphoreManager
from app.utils import custom_logging

class AsyncWorker:
    def __init__(self):
        self.db_pool = None
        self.redis_client = None
        self.gemini_processor = GeminiProcessor(Config.GEMINI_API_KEY)
        self.logger = custom_logging()
        self.semaphore_manager = None
        
    async def initialize(self):
        """Initialize database and Redis connections"""
        self.db_pool = await asyncpg.create_pool(Config.DATABASE_URL)
        self.redis_client = await redis.from_url(Config.REDIS_URL, decode_responses=True)
        self.semaphore_manager = SemaphoreManager(Config.REDIS_URL, Config.RATE_LIMITS, 10)  # Longer timeout for worker
        await self.semaphore_manager.initialize()
        
    async def process_request(self, req_id, input_type, input_data):
        """Process a single request using the semaphore manager"""
        self.logger.info(f"Processing queued request {req_id} of type {input_type}")
        
        try:
            # Try to acquire the semaphore with exponential backoff
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    # Attempt to acquire the semaphore
                    await self.semaphore_manager.acquire_semaphore(input_type)
                    
                    # If we get here, we've acquired the semaphore
                    self.logger.info(f"Acquired semaphore for request {req_id} on attempt {attempt+1}")
                    
                    # Process the request
                    response = await self.gemini_processor.process_llm_request(input_type, input_data)
                    
                    # Update the request status in the database
                    await self.update_request_status(req_id, "completed", response)
                    
                    self.logger.info(f"Successfully processed request {req_id}")
                    
                    # Release the semaphore
                    await self.semaphore_manager.release_semaphore(input_type)
                    return
                    
                except TimeoutError:
                    # If we couldn't acquire the semaphore, back off and retry
                    backoff_time = min(2 ** attempt + random.uniform(0, 1), 60)
                    self.logger.info(f"Failed to acquire semaphore on attempt {attempt+1}, backing off for {backoff_time:.2f} seconds")
                    await asyncio.sleep(backoff_time)
            
            # If we've exhausted all attempts, log an error and update the request status
            self.logger.error(f"Failed to acquire semaphore for request {req_id} after {max_attempts} attempts")
            await self.update_request_status(
                req_id,
                "failed",
                {"error": "Failed to acquire resources after multiple attempts"}
            )
            
        except Exception as e:
            self.logger.error(f"Error processing request {req_id}: {str(e)}")
            # Update with error status
            await self.update_request_status(
                req_id,
                "failed",
                {"error": str(e)}
            )
            
            # Make sure to release the semaphore if we acquired it
            try:
                await self.semaphore_manager.release_semaphore(input_type)
            except:
                pass

    async def update_request_status(self, req_id, status, response_data):
        """Update request status and response in the database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE requests 
                SET status=$1, response=$2, updated_at=NOW() 
                WHERE id=$3
                """,
                status, str(response_data), req_id
            )

    async def process_queue(self, input_type):
        """Process all requests in a queue"""
        queue_key = f"queue:{input_type}"
        
        # Get the queue length
        queue_length = await self.redis_client.llen(queue_key)
        if queue_length > 0:
            self.logger.info(f"Found {queue_length} requests in {input_type} queue")
        
        # Process each request in the queue
        while True:
            # Pop a request from the queue (non-blocking)
            request_json = await self.redis_client.lpop(queue_key)
            if not request_json:
                break
                
            try:
                # Parse the request data
                request_data = json.loads(request_json)
                req_id = request_data.get("id")
                input_type = request_data.get("input_type")
                input_data_str = request_data.get("input_data")
                
                # Convert input_data back to a dictionary if needed
                try:
                    import ast
                    input_data = ast.literal_eval(input_data_str)  # Safer than eval
                except:
                    input_data = input_data_str
                
                # Process the request
                await self.process_request(req_id, input_type, input_data)
                
            except Exception as e:
                self.logger.error(f"Error processing queued request: {str(e)}")

    async def run(self):
        """Main worker loop"""
        self.logger.info("Starting async worker")
        await self.initialize()
        
        while True:
            # Process each queue type
            tasks = []
            for input_type in Config.RATE_LIMITS.keys():
                tasks.append(self.process_queue(input_type))
                
            # Wait for all queue processing to complete
            await asyncio.gather(*tasks)
            
            # Sleep to avoid busy waiting
            await asyncio.sleep(1)

    async def cleanup(self):
        """Cleanup resources"""
        if self.db_pool:
            await self.db_pool.close()
        if self.redis_client:
            await self.redis_client.close()
        if self.semaphore_manager:
            await self.semaphore_manager.cleanup()

async def main():
    worker = AsyncWorker()
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
