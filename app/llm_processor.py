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
                # print(type(file))
                contents.append(types.Part.from_bytes(
                    mime_type=file["type"],
                    data=file["data"]
                ))

        # Run the synchronous API call in a thread pool
        response = await asyncio.to_thread(
            self._generate_content,
            model=model,
            contents=contents
        )
        # return "Processed a response successfully"
        return response.text

    def _generate_content(self, model, contents):
        """Synchronous helper method to call the API"""
        return self.client.models.generate_content(
            model=model,
            contents=contents
        )
    
    