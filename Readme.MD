# LLM Rate Limiter Project

This project provides an API wrapper over large language models (LLMs) that enforces distributed concurrency limits using Redis. It supports various request types including text-only, multi-modal (text plus file), and image generation requests. Additionally, it stores request and response details in a database for audit and analysis.

## Features

- **Distributed Concurrency Control:**  
  Uses Redis with Lua scripting for atomic semaphore operations, ensuring global concurrency limits across distributed service instances.

- **Rate-Limited Query Queueing:**  
  When concurrency limits are exceeded, requests are automatically pushed to a queue in Redis. Asynchronous workers later process these queued requests to ensure no query is dropped.

- **Multiple Request Types:**  
  - **Text-only requests**
  - **Multi-modal requests:** Accepts text and file uploads.
  - **Image generation requests:** Can be triggered using an image file or an image URI.
Note: Image generation requests are not supported on free tier of Gemini

- **Asynchronous Processing:**  
  Built on FastAPI with asynchronous endpoints and non-blocking operations (using `asyncio` and `asyncio.to_thread`).

- **LLM Integration:**  
  Leverages a dedicated `GeminiProcessor` class to interface with the Gemini LLM.

- **Robust Request Classification:**  
  Uses an LLM-based approach with a fallback to keyword matching to determine if a request is for image generation.

- **Custom Logging:**  
  Implements consistent logging via a custom logging utility.

## Requirements

- Python 3.8+
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [Redis](https://redis.io/) (with `redis.asyncio`)
- [asyncpg](https://github.com/MagicStack/asyncpg)
- [python-dotenv](https://github.com/theskumar/python-dotenv)
- Other dependencies as listed in `requirements.txt`

pip install -r requirements.txt
## Configuration
Create a .env file in the project root with the following variables:

```
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://localhost:6379/0
GEMINI_API_KEY=your_gemini_api_key
```

You can adjust the rate limits and semaphore timeout in the Config class (e.g., in app/config.py):

```
class Config:
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_URL = os.getenv("REDIS_URL")
    RATE_LIMITS = {"text_only": 5, "multi_modal": 3, "image_generation": 2}
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SEMAPHORE_TIMEOUT = 3
```

## Usage
### Running the API Server
Start the FastAPI application and worker:

```
   python3 run_app.py
   python3 run_worker.py
```

Your endpoints will be available at http://localhost:8000.

## API Endpoints
#### POST llm/submit:
Submit a request to the LLM. Accepts multipart form data with:

 - text: The prompt text.
 - files: (Optional) File upload for multi-modal requests.

#### GET llm/status/{request_id}
Fetch response for a previous request using request_id

#### POST llm/stream:
Streams responses from the LLM based on the provided prompt 

Example Curl Commands
Text-only Request:
curl -s -X POST "http://localhost:8000/llm/submit" \
       -H "Content-Type: multipart/form-data" \
       -F 'text="Hi, What are semaphores? Give a short and concise answer"'

Multi-modal Request:
curl -s -X POST "http://localhost:8000/llm/submit" \
       -H "Content-Type: multipart/form-data" \
       -F 'text="What is in this picture?"' \
       -F 'files=@cat.png'

Image-generation Request:
curl -s -X POST "http://localhost:8000/llm/submit" \
       -H "Content-Type: multipart/form-data" \
       -F 'text="Draw a picture of a circle?"' 

Streaming Request:
 curl -N "http://localhost:8000/llm/stream" \           
     -H "Content-Type: multipart/form-data" \
     -F 'text="Who is donald trump?"'

Fetching Response using request_id
curl -N "http://localhost:8000/llm/status/73c6a877-cde7-4092-9f26-3fd44b907686"  

## Testing
A sample shell script (test_api_calls.zsh) is provided to simulate concurrent API calls. The script accepts two argument to select the request type (0 for text-only, 1 for multi-modal, 2 for image generation) and number of requests to send of that type 

Make it executable and run as follows:
```
chmod +x scripts/test_api_calls.zsh
./scripts/test_api_calls.zsh 0 7 # for text-only requests
```

### Distributed Rate Limiting Strategy
The project implements distributed rate limiting using Redis:

- Atomic Operations with Lua Scripts:
Ensures that semaphore acquisition and release are done atomically to prevent race conditions.
- Centralized Concurrency Control:
All instances of the service share the same Redis-based semaphores, enforcing global limits on concurrent LLM requests.
- Fallbacks and Robustness:
Provides fallback mechanisms for both request classification and semaphore management, ensuring the system remains resilient under load.






