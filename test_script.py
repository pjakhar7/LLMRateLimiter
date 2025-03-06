import requests
import concurrent.futures
import time

BASE_URL = 'http://127.0.0.1:5080/api/submit'

def test_text_request():
    """Send a text-only request."""
    payload = {"text": "Hello LLM, this is a text-only request."}
    response = requests.post(BASE_URL, json=payload)
    print("Text Request Response:")
    print("Status Code:", response.status_code)
    print("Response:", response.json())
    print("-" * 50)

def test_multi_modal_request():
    """Send a multi-modal request with text and a file (simulate a PDF)."""
    data = {"text": "Multi-modal input with text and PDF file."}
    # Using a dummy PDF file content.
    files = {
        "file": ("dummy.pdf", b"%PDF-1.4 dummy pdf content", "application/pdf")
    }
    response = requests.post(BASE_URL, data=data, files=files)
    print("Multi-Modal Request Response:")
    print("Status Code:", response.status_code)
    print("Response:", response.json())
    print("-" * 50)

def test_image_generation_request():
    """Send an image generation request (file only)."""
    # Simulate an image upload (e.g., PNG file)
    files = {
        "file": ("dummy.png", b"\x89PNG\r\n\x1a\n dummy image content", "image/png")
    }
    response = requests.post(BASE_URL, files=files)
    print("Image Generation Request Response:")
    print("Status Code:", response.status_code)
    print("Response:", response.json())
    print("-" * 50)

def test_concurrent_text_requests(num_requests=5):
    """Fire multiple text-only requests concurrently to test rate limiting."""
    payload = {"text": "Concurrent text request for rate limiter test."}

    def send_request(i):
        resp = requests.post(BASE_URL, json=payload)
        print(f"Concurrent Request {i}: {resp.status_code} - {resp.json()}")

    print("Starting concurrent text requests...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(send_request, i) for i in range(num_requests)]
        concurrent.futures.wait(futures)
    print("-" * 50)

if __name__ == '__main__':
    print("=== Testing API Calls ===")
    time.sleep(1)  # Small delay to ensure server is ready
    
    test_text_request()
    test_multi_modal_request()
    test_image_generation_request()
    test_concurrent_text_requests()
