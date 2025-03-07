from google import genai
API_KEY = "AIzaSyC0eDOtjtV52oEa3oogHRhrQkHOf5abdMs"
client = genai.Client(api_key=API_KEY)

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=["Explain how AI works"],
)

# for chunk in client.models.generate_content_stream(
#         model='gemini-2.0-flash',
#         contents='''What is modern family?'''
#       ):
#         print(chunk.text)

# print(response.text)

from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client(api_key=API_KEY)

# response = client.models.generate_images(
#     model='imagen-3.0-generate-002',
#     prompt='Fuzzy bunnies in my kitchen',
#     config=types.GenerateImagesConfig(
#         number_of_images= 4,
#     )
# )
# for generated_image in response.generated_images:
#   image = Image.open(BytesIO(generated_image.image.image_bytes))
#   image.show()