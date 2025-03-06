import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_URL = os.getenv("REDIS_URL")
    RATE_LIMITS = {"text_only": 5, "multi_modal": 3, "image_generation": 2}
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SEMAPHORE_TIMEOUT = 3