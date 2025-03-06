import asyncio
import mimetypes
import re
from fastapi import File, UploadFile
from typing import List, Optional, Tuple, Dict, Any

class RequestClassifier:
    IMAGE_GEN_KEYWORDS = [
        "generate an image", "create an image", "draw", "paint", "illustrate",
        "design a picture", "make an image of", "visualize", "art of", "sketch"
    ]

    def __init__(self, gemini_processor):
        self.gemini_processor = gemini_processor

    async def classify_request(self, text_data: Optional[str], files: List[UploadFile] = File([])) -> Tuple[str, Dict[str, Any]]:
        """
        Asynchronously classify the request based on text and file.
        
        Args:
            text_data: Optional text input
            file: Optional FastAPI UploadFile object
        
        Returns:
            Tuple of (input_type, input_data)
        """
        input_data = {"text": text_data, "files": []}

        if text_data and await self.is_requesting_image(text_data):
            return "image_generation", input_data

        if files:
            for file in files:
                content = await file.read()                
                mime_type = file.content_type
                if not mime_type:
                    mime_type, _ = mimetypes.guess_type(file.filename)
                
                input_data["files"].append({
                    "filename": file.filename,
                    "type": mime_type or "application/octet-stream",
                    "data": content
                })
                
                await file.seek(0)
            
            return "multi_modal", input_data

        return "text_only", input_data

    async def is_requesting_image(self, text: str) -> bool:
        """
        Use the LLM to determine if the provided text requests image generation.
        This function offloads the (synchronous) LLM call to a thread.

        Args:
            text: The input text to check.

        Returns:
            bool: True if the LLM indicates the text is requesting image generation, else False.
        """        
        prompt = (
            "Based on the following text, determine if the user is requesting an image to be generated. "
            "Answer with 'yes' or 'no' only.\n\n"
            f"Text: {text}\n\n"
            "Answer:"
        )
        return any(
                re.search(rf"\b{re.escape(keyword)}\b", text, re.IGNORECASE)
                for keyword in self.IMAGE_GEN_KEYWORDS
            )
        try:
            # Call the LLM processor 
            response = await self.gemini_processor.process_llm_request({"text": prompt})
            result = response.strip().lower() if response else ""
            return result in ("yes", "y", "true", "1")
        except Exception as e:
            print(f"LLM call failed: {e}. Falling back to keyword matching.")
            # Fallback: perform simple keyword matching
            return any(
                re.search(rf"\b{re.escape(keyword)}\b", text, re.IGNORECASE)
                for keyword in self.IMAGE_GEN_KEYWORDS
            )