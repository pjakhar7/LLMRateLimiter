#!/usr/bin/env python3
import asyncio
import logging
import sys
import os
import signal
import time

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.worker import AsyncWorker
from app.utils import custom_logging

# Configure logging
logger = custom_logging()

# Global variable to track the worker
worker = None

async def shutdown(signal, loop):
    """Cleanup tasks tied to the service's shutdown."""
    logger.info(f"Received exit signal {signal.name}...")
    
    # Cancel all running tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
    logger.info("Shutdown complete.")

def handle_exception(loop, context):
    """Handle exceptions in the event loop."""
    msg = context.get("exception", context["message"])
    logger.error(f"Caught exception: {msg}")
    logger.info("Shutting down...")
    asyncio.create_task(shutdown(signal.SIGTERM, loop))

async def main():
    """Main entry point for the worker."""
    # Setup signal handlers
    loop = asyncio.get_running_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(s, loop))
        )
    
    # Set exception handler
    loop.set_exception_handler(handle_exception)
    
    try:
        # Create and start the worker
        global worker
        worker = AsyncWorker()
        logger.info("Starting worker process")
        await worker.run()
    except Exception as e:
        logger.error(f"Error in worker process: {e}")
        raise

if __name__ == "__main__":
    try:
        # Create a new event loop and set it as the current one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info("Initializing worker process")
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Worker process interrupted")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
    finally:
        logger.info("Worker process shutdown complete")
        # Clean up the event loop
        if 'loop' in locals() and loop.is_running():
            loop.close() 