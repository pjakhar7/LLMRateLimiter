
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
