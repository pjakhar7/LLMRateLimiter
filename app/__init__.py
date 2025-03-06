from fastapi import FastAPI
from app.routes import router

def create_app():
    app = FastAPI(title="LLM Rate Limiter API")
    app.include_router(router, prefix="/llm", tags=["llm"])
    return app