from google import genai

client = genai.Client(api_key="AIzaSyC0eDOtjtV52oEa3oogHRhrQkHOf5abdMs")

# response = client.models.generate_content(
#     model="gemini-2.0-flash",
#     contents=["Explain how AI works"],
# )

for chunk in client.models.generate_content_stream(
        model='gemini-2.0-flash',
        contents='''What is modern family?'''
      ):
        print(chunk.text)

# print(response.text)