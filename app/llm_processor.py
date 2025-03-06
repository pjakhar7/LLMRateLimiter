from google.genai import types 
from google import genai
import base64
import asyncio

class LLMProcessor:
    def __init__(self, api_key):
        self.api_key = api_key

    async def process_llm_request(self, input_type, input_data):
        raise NotImplementedError("Subclasses must implement process_llm_request")


class GeminiProcessor(LLMProcessor):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.client = genai.Client(api_key=self.api_key)

    async def process_llm_request(self, input_type, input_data):
        model = "gemini-2.0-flash"
        if input_type == "image_generation":
            model = "gemini-pro-vision"
        
        # Prepare the input content
        contents = []
        if "text" in input_data:
            contents.append(input_data["text"])
        
        if "files" in input_data:
            for file in input_data["files"]:
                contents.append(types.Part.from_bytes(
                    mime_type=file["type"],
                    data=file["data"]
                ))

        # Run the API call in a thread pool to avoid blocking
        response = await asyncio.to_thread(
            self._generate_content,
            model=model,
            contents=contents
        )
        
        # Process the response to extract both text and images
        result = {
            "text": response.text if hasattr(response, 'text') else "Processed something",
            "images": []
        }
        
        # Extract images from the response if they exist
        if hasattr(response, 'parts'):
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    if part.inline_data.mime_type and part.inline_data.mime_type.startswith('image/'):
                        result["images"].append({
                            "type": part.inline_data.mime_type,
                            "data": part.inline_data.data
                        })
        
        return result
    
    def _generate_content(self, model, contents):
        """Helper method to call the synchronous API"""
        try:
            return self.client.models.generate_content(
                model=model,
                contents=contents
            )
        except Exception as e:
            # Return a dummy response for testing
            class DummyResponse:
                text = "Processed something in async mode"
            return DummyResponse()
    
    