import asyncio
import aiohttp
import base64
from io import BytesIO
from PIL import Image
import json
import os

async def test_text_request(session, url):
    """Test a text-only request"""
    print("\nTest 1: Text-only request")
    payload = {
        "text": "Explain quantum computing in simple terms."
    }
    
    async with session.post(url, json=payload) as response:
        print(f"Status code: {response.status}")
        if response.status == 200:
            data = await response.json()
            print(f"Request ID: {data.get('request_id')}")
            print_response(data.get('response'))
        else:
            print("Error:", await response.text())

async def test_image_analysis(session, url, image_path):
    """Test image analysis request"""
    print("\nTest 2: Image analysis request")
    
    # Check if the image exists
    if not os.path.exists(image_path):
        print(f"Warning: {image_path} not found. Creating a sample image.")
        create_sample_image(image_path)
    
    # Prepare multipart form data
    data = aiohttp.FormData()
    data.add_field('file', 
                  open(image_path, 'rb'),
                  filename=os.path.basename(image_path),
                  content_type='image/jpeg')
    data.add_field('text', "Describe what's in this image")
    
    async with session.post(url, data=data) as response:
        print(f"Status code: {response.status}")
        if response.status == 200:
            data = await response.json()
            print(f"Request ID: {data.get('request_id')}")
            print_response(data.get('response'))
        else:
            print("Error:", await response.text())

async def test_image_generation(session, url):
    """Test image generation request"""
    print("\nTest 3: Image generation request")
    payload = {
        "text": "Generate an image of a sunset over mountains"
    }
    
    async with session.post(url, json=payload) as response:
        print(f"Status code: {response.status}")
        if response.status == 200:
            data = await response.json()
            print(f"Request ID: {data.get('request_id')}")
            response_data = data.get('response')
            print_response(response_data)
            await save_response_images(response_data)
        else:
            print("Error:", await response.text())

def print_response(response_data):
    """Print the response details"""
    if isinstance(response_data, str):
        print("Text response:", response_data[:100] + "..." if len(response_data) > 100 else response_data)
    elif isinstance(response_data, dict):
        if 'text' in response_data:
            text = response_data['text']
            print("Text response:", text[:100] + "..." if len(text) > 100 else text)
        if 'images' in response_data:
            print(f"Number of images: {len(response_data['images'])}")

async def save_response_images(response_data):
    """Extract and save any images from the response"""
    if isinstance(response_data, dict) and 'images' in response_data:
        images = response_data['images']
        for i, img_data in enumerate(images):
            if 'data' in img_data and 'type' in img_data:
                # Decode base64 image data if needed
                image_bytes = img_data['data']
                if isinstance(image_bytes, str):
                    image_bytes = base64.b64decode(image_bytes)
                
                # Determine file extension from MIME type
                ext = img_data['type'].split('/')[-1]
                filename = f"response_image_{i}.{ext}"
                
                # Save the image
                with open(filename, 'wb') as f:
                    f.write(image_bytes)
                print(f"Saved image to {filename}")

def create_sample_image(path):
    """Create a simple test image"""
    img = Image.new('RGB', (300, 200), color=(73, 109, 137))
    img.save(path)
    print(f"Created sample image at {path}")

async def main():
    url = "http://localhost:5000/api/submit"  # Adjust the URL as needed
    image_path = "test_image.jpg"
    
    async with aiohttp.ClientSession() as session:
        await test_text_request(session, url)
        await test_image_analysis(session, url, image_path)
        await test_image_generation(session, url)

if __name__ == "__main__":
    asyncio.run(main()) 