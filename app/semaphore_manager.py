import time
import asyncio
import redis.asyncio as redis
from app.utils import custom_logging

logger = custom_logging(__name__)

class SemaphoreManager:
    def __init__(self, redis_url, rate_limits, timeout):
        self.redis_url = redis_url
        self.rate_limits = rate_limits 
        self.timeout = timeout  # Timeout in seconds for acquiring a semaphore
        self.redis_client = None
        self.reset_task = None

    async def initialize(self):
        """Initialize the Redis connection and reset semaphores."""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
            await self.reset_semaphores()
            # Optionally, start the periodic reset task.
            # self.reset_task = asyncio.create_task(self._reset_periodically())

    async def acquire_semaphore(self, input_type):
        """Acquire a semaphore for the given input type using an atomic Lua script."""
        if self.redis_client is None:
            await self.initialize()
            
        start_time = time.time()

        # Lua script to atomically check the value and decrement if available.
        lua_script = """
        local current = tonumber(redis.call('GET', KEYS[1]))
        if current and current > 0 then
            return redis.call('DECR', KEYS[1])
        else
            return -1
        end
        """

        while time.time() - start_time < self.timeout:
            result = await self.redis_client.eval(lua_script, 1, input_type)
            if result != -1:
                logger.info(f"Acquired semaphore for '{input_type}'. New value: {result}")
                return  # Acquired successfully
            # Wait briefly before retrying
            await asyncio.sleep(1)
        
        raise TimeoutError(f"Could not acquire semaphore for '{input_type}' within {self.timeout} seconds")

    async def release_semaphore(self, input_type):
        """Release the Redis semaphore by incrementing the counter only if it is below the max limit."""
        if self.redis_client is None:
            await self.initialize()
            
        max_limit = self.rate_limits.get(input_type)
        if max_limit is None:
            # Optionally, handle the case where input_type is not defined.
            max_limit = 1  # Fallback maximum
        
        lua_script = """
        local current = tonumber(redis.call('GET', KEYS[1]))
        local max = tonumber(ARGV[1])
        if current and current < max then
            return redis.call('INCR', KEYS[1])
        else
            return current or 0
        end
        """
        new_value = await self.redis_client.eval(lua_script, 1, input_type, max_limit)
        logger.info(f"Released semaphore for '{input_type}'. New value: {new_value}")

    async def _reset_periodically(self):
        """Async task that resets Redis rate limits at fixed intervals."""
        try:
            while True:
                await asyncio.sleep(60)  # Reset every 60 seconds
                await self.reset_semaphores()
        except asyncio.CancelledError:
            # Handle task cancellation gracefully
            pass
        except Exception as e:
            logger.error(f"Error in reset task: {e}")
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
