import time
import aioredis
import asyncio
import threading

class SemaphoreManager:
    def __init__(self, redis_url, rate_limits, timeout):
        self.redis_url = redis_url
        self.rate_limits = rate_limits 
        self.timeout = timeout  # Timeout in seconds for acquiring a semaphore
        self.redis_client = None
        # Start a background thread to reset Redis counters periodically
        self.reset_thread = threading.Thread(target=self._reset_periodically_sync, daemon=True)
        self.reset_thread.start()

    async def initialize(self):
        """Initialize the Redis connection"""
        if self.redis_client is None:
            self.redis_client = await aioredis.from_url(self.redis_url, decode_responses=True)
            await self.reset_semaphores()

    async def acquire_semaphore(self, input_type):
        """Acquire a semaphore for the given input type"""
        if self.redis_client is None:
            await self.initialize()
            
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            # Check and decrement the Redis counter (only proceed if available)
            current_value = await self.redis_client.get(input_type)

            if current_value is not None and int(current_value) > 0:
                print(current_value)
                await self.redis_client.decr(input_type)
                return  # Acquired successfully

            await asyncio.sleep(1)  # Simple backoff before retrying
        
        raise TimeoutError(f"Could not acquire semaphore for {input_type} within {self.timeout} seconds")

    async def release_semaphore(self, input_type):
        """Release the Redis semaphore by incrementing the counter."""
        if self.redis_client is None:
            await self.initialize()
        await self.redis_client.incr(input_type)

    def _reset_periodically_sync(self):
        """Background thread that resets Redis rate limits at fixed intervals."""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async reset function in this loop
        try:
            loop.run_until_complete(self._reset_periodically_loop())
        except Exception as e:
            print(f"Error in reset thread: {e}")
        finally:
            loop.close()
        
    async def _reset_periodically_loop(self):
        """Async loop to reset semaphores periodically"""
        # Initialize Redis client for this thread
        self.thread_redis_client = await aioredis.from_url(self.redis_url, decode_responses=True)
        
        while True:
            try:
                await asyncio.sleep(30)  # Reset every 30 seconds
                await self._reset_semaphores_thread()
            except Exception as e:
                print(f"Error resetting semaphores: {e}")
                await asyncio.sleep(5)  # Wait a bit before retrying

    async def _reset_semaphores_thread(self):
        """Reset all rate limits in Redis according to predefined values (thread-specific)."""
        for input_type, limit in self.rate_limits.items():
            await self.thread_redis_client.set(input_type, limit)

    async def reset_semaphores(self):
        """Reset all rate limits in Redis according to predefined values."""
        if self.redis_client is None:
            self.redis_client = await aioredis.from_url(self.redis_url, decode_responses=True)
            
        for input_type, limit in self.rate_limits.items():
            await self.redis_client.set(input_type, limit)
