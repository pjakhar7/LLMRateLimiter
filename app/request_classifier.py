import mimetypes
import re
from fastapi import File, UploadFile
from typing import List, Optional, Tuple, Dict, Any

class RequestClassifier:
    IMAGE_GEN_KEYWORDS = [
        "generate an image", "create an image", "draw", "paint", "illustrate",
        "design a picture", "make an image of", "visualize", "art of", "sketch"
    ]

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

        if text_data and self.is_requesting_image(text_data):
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

    def is_requesting_image(self, text: str) -> bool:
        """
        Check if the text is requesting image generation.
        Args:
            text: Input text to check 
        Returns:
            bool: True if text requests image generation
        """
        return any(re.search(rf"\b{keyword}\b", text, re.IGNORECASE) for keyword in self.IMAGE_GEN_KEYWORDS)
