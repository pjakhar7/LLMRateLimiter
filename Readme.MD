# LLM Rate Limiter Project

This project provides an API wrapper over large language models (LLMs) that enforces distributed concurrency limits using Redis. It supports various request types including text-only, multi-modal (text plus file), and image generation requests. Additionally, it stores request and response details in a database for audit and analysis.

## Features

- **Distributed Concurrency Control:**  
  Uses Redis with Lua scripting for atomic semaphore operations, ensuring global concurrency limits across distributed service instances.

- **Multiple Request Types:**  
  - **Text-only requests**
  - **Multi-modal requests:** Accepts text and file uploads.
  - **Image generation requests:** Can be triggered using an image file or an image URI.

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
Configuration
Create a .env file in the project root with the following variables:

dotenv
Copy
Edit
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://localhost:6379/0
GEMINI_API_KEY=your_gemini_api_key
You can adjust the rate limits and semaphore timeout in the Config class (e.g., in app/config.py):

python
Copy
Edit
class Config:
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_URL = os.getenv("REDIS_URL")
    RATE_LIMITS = {"text_only": 5, "multi_modal": 3, "image_generation": 2}
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SEMAPHORE_TIMEOUT = 3
Usage
Running the API Server
Start the FastAPI application with Uvicorn:

bash
Copy
Edit
uvicorn app.main:app --reload
Your endpoints will be available at http://localhost:8000.

API Endpoints
POST /submit:
Submit a request to the LLM. Accepts multipart form data with:

text: The prompt text.
files: (Optional) File upload for multi-modal requests.
image_uri: (Optional) URI for an image generation request.
POST /stream:
Streams responses from the LLM based on the provided prompt and image input (either as a file or URI).

Example Curl Commands
Text-only Request:

bash
Copy
Edit
curl -X POST "http://localhost:8000/submit" \
     -F 'text=Tell me a joke.'
Multi-modal Request (Text + File):

bash
Copy
Edit
curl -X POST "http://localhost:8000/submit" \
     -F 'text=What is shown in this image?' \
     -F 'files=@cat.png'
Image Generation Request (Using Image URI):

bash
Copy
Edit
curl -X POST "http://localhost:8000/submit" \
     -F 'text=Generate an image of a sunset.' \
     -F 'image_uri=gs://generativeai-downloads/images/sunset.jpg'
Streaming Response with Multipart Input:

bash
Copy
Edit
curl -N "http://localhost:8000/stream" \
     -F 'text=Describe this image:' \
     -F 'file=@cat.png'
Testing
A sample shell script (scripts/test_requests.zsh) is provided to simulate concurrent API calls. The script accepts an argument to select the request type (0 for text-only, 1 for multi-modal, 2 for image generation) and iterates five times over the chosen function.

Make it executable and run as follows:

bash
Copy
Edit
chmod +x scripts/test_requests.zsh
./scripts/test_requests.zsh 0  # for text-only requests
Distributed Rate Limiting Strategy
The project implements distributed rate limiting using Redis:

Atomic Operations with Lua Scripts:
Ensures that semaphore acquisition and release are done atomically to prevent race conditions.
Centralized Concurrency Control:
All instances of the service share the same Redis-based semaphores, enforcing global limits on concurrent LLM requests.
Fallbacks and Robustness:
Provides fallback mechanisms for both request classification and semaphore management, ensuring the system remains resilient under load.
Contributing
Contributions are welcome! Please fork the repository and open a pull request for any enhancements or bug fixes. For major changes, please open an issue first to discuss your ideas.

License
This project is licensed under the MIT License.





curl -X POST "http://localhost:5080/submit" \
     -H "Content-Type: application/json" \
     -d '{
           "data": "Explain the importance of cybersecurity in modern businesses."
         }'


curl -X POST "http://localhost:5080/submit" \
     -H "Content-Type: multipart/form-data" \
     -F "data=Describe this document in detail" \
     -F "file=@/path/to/document.pdf"


curl -X POST "http://localhost:5080/submit" \
     -H "Content-Type: application/json" \
     -d '{
           "data": "Generate an image of a futuristic city with flying cars."
         }'

 curl -N "http://localhost:8000/llm/stream" \          
     -H "Content-Type: multipart/form-data" \
     -F 'text="What is modern family?"'

curl -N "http://localhost:8000/llm/status/73c6a877-cde7-4092-9f26-3fd44b907686"  
