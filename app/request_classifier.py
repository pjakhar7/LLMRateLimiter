import mimetypes
import re
import asyncio

class RequestClassifier:
    IMAGE_GEN_KEYWORDS = [
        "generate an image", "create an image", "draw", "paint", "illustrate",
        "design a picture", "make an image of", "visualize", "art of", "sketch"
    ]

    async def classify_request(self, text_data, files):
        """Async version of classify_request"""
        # This method doesn't actually need to be async since it doesn't do I/O,
        # but making it async for consistency with the rest of the codebase
        return self.classify_request_sync(text_data, files)
        
    def classify_request(self, text_data, files):
        """Kept for backward compatibility"""
        return self.classify_request_sync(text_data, files)

    def classify_request_sync(self, text_data, files):
        """Synchronous implementation of classify_request"""
        input_data = {"text": text_data, "files": []}

        if text_data and self.is_requesting_image(text_data):
            return "image_generation", input_data  

        if files:
            for file in files:
                file_type, _ = mimetypes.guess_type(file.filename)
                input_data["files"].append({"filename": file.filename, "type": file_type, "data": file.read()})
            return "multi_modal", input_data  
        
        return "text_only", input_data

    def is_requesting_image(self, text):
        return any(re.search(rf"\b{keyword}\b", text, re.IGNORECASE) for keyword in self.IMAGE_GEN_KEYWORDS)
