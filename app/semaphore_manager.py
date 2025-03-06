import time
import redis.asyncio as redis
import asyncio
import threading
from app.utils import custom_logging

logger = custom_logging()

class SemaphoreManager:
    def __init__(self, redis_url, rate_limits, timeout):
        self.redis_url = redis_url
        self.rate_limits = rate_limits 
        self.timeout = timeout  # Timeout in seconds for acquiring a semaphore
        self.redis_client = None
        self.reset_task = None

    async def initialize(self):
        """Initialize the Redis connection and start reset task"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
            await self.reset_semaphores()
            
            # Start the periodic reset task
            self.reset_task = asyncio.create_task(self._reset_periodically())

    async def acquire_semaphore(self, input_type):
        """Acquire a semaphore for the given input type"""
        if self.redis_client is None:
            await self.initialize()
            
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            # Check and decrement the Redis counter (only proceed if available)
            current_value = await self.redis_client.get(input_type)

            if current_value is not None and int(current_value) > 0:
                # Use Redis WATCH/MULTI/EXEC for atomic decrement
                try:
                    tr = self.redis_client.pipeline()
                    await tr.watch(input_type)
                    
                    # Check value again inside transaction
                    current_value = await self.redis_client.get(input_type)
                    if current_value is not None and int(current_value) > 0:
                        logger.info(f"Current val: {current_value}")
                        tr.multi()
                        tr.decr(input_type)
                        await tr.execute()
                        return  # Acquired successfully
                    
                except redis.WatchError:
                    # Someone else modified the value, retry
                    continue
                finally:
                    await tr.unwatch()

            await asyncio.sleep(1)  # Simple backoff before retrying
        
        raise TimeoutError(f"Could not acquire semaphore for {input_type} within {self.timeout} seconds")

    async def release_semaphore(self, input_type):
        """Release the Redis semaphore by incrementing the counter."""
        if self.redis_client is None:
            await self.initialize()
        await self.redis_client.incr(input_type)

    async def _reset_periodically(self):
        """Async task that resets Redis rate limits at fixed intervals."""
        try:
            while True:
                await asyncio.sleep(30)  # Reset every 30 seconds
                await self.reset_semaphores()
        except asyncio.CancelledError:
            # Handle task cancellation gracefully
            pass
        except Exception as e:
            print(f"Error in reset task: {e}")
            # Restart the task if it fails
            await asyncio.sleep(5)
            self.reset_task = asyncio.create_task(self._reset_periodically())

    async def reset_semaphores(self):
        """Reset all rate limits in Redis according to predefined values."""
        if self.redis_client is None:
            await self.initialize()
            
        # Use pipeline for atomic updates
        async with self.redis_client.pipeline() as pipe:
            for input_type, limit in self.rate_limits.items():
                pipe.set(input_type, limit)
            await pipe.execute()

    async def cleanup(self):
        """Cleanup resources when shutting down."""
        if self.reset_task:
            self.reset_task.cancel()
            try:
                await self.reset_task
            except asyncio.CancelledError:
                pass
        
        if self.redis_client:
            await self.redis_client.close()
