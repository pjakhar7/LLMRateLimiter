
curl -X POST "http://localhost:5080/submit" \
     -H "Content-Type: application/json" \
     -d '{
           "data": "Explain the importance of cybersecurity in modern businesses."
         }'


curl -X POST "http://localhost:5080/submit" \
     -H "Content-Type: multipart/form-data" \
     -F "data=Describe this document in detail" \
     -F "file=@/path/to/document.pdf"


curl -X POST "http://localhost:5080/submit" \
     -H "Content-Type: application/json" \
     -d '{
           "data": "Generate an image of a futuristic city with flying cars."
         }'

 curl -N "http://localhost:8000/llm/stream" \          
     -H "Content-Type: multipart/form-data" \
     -F 'text="What is modern family?"'

curl -N "http://localhost:8000/llm/status/73c6a877-cde7-4092-9f26-3fd44b907686"  
