import time
from typing import AsyncGenerator
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
        # if input_type == "image_generation":
        #     model = "gemini-pro-vision"
        
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
        # time.sleep(3)
        # return "Processed a response successfully"
        return response.text

    def _generate_content(self, model, contents):
        """Synchronous helper method to call the API"""
        return self.client.models.generate_content(
            model=model,
            contents=contents
        )
    
    def _generate_content_stream(self, prompt: str):
        """
        Synchronously call the LLM client's streaming generator.
        """
        model = "gemini-2.0-flash"
        contents = [
            prompt
        ]
        return self.client.models.generate_content_stream(
            model=model,
            contents=contents
        )

    async def stream_content(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Asynchronously stream content from the LLM by offloading the synchronous call
        to a separate thread.
        """
        # Offload synchronous LLM call to a thread.
        print(prompt)
        chunks = await asyncio.to_thread(self._generate_content_stream, prompt)
        for chunk in chunks:
            # Yield each chunk’s text followed by a newline.
            yield chunk.text + "\n"
    
    