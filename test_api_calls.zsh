#!/bin/zsh

MODE=$1
NUM_REQUESTS=$2
URL="http://localhost:8000/llm/submit"

function send_text_only_request {
  echo "Sending text-only request..."
  curl -s -X POST "$URL" \
       -H "Content-Type: multipart/form-data" \
       -F 'text="Hi, What are semaphores? Give a short and concise answer"'
  echo "\n-----------------------------\n"
}

function send_multi_modal_request {
  echo "Sending request..."
  curl -s -X POST "$URL" \
       -H "Content-Type: multipart/form-data" \
       -F 'text="What is in this picture?"' \
       -F 'files=@cat.png'
  echo "\n-----------------------------\n"
}

function send_image_generation_request {
  echo "Sending image generation request..."
  curl -s -X POST "$URL" \
       -H "Content-Type: multipart/form-data" \
       -F 'text="Draw a picture of a circle?"' 
  echo "\n-----------------------------\n"
}

echo "Starting requests..."
case $MODE in
  0)
    echo "Mode: Text-only requests"
    for i in {1..$NUM_REQUESTS}; do
      echo "Request $i:"
      send_text_only_request &
    done
    ;;
  1)
    echo "Mode: Multi-modal requests"
    for i in {1..$NUM_REQUESTS}; do
      echo "Request $i:"
      send_multi_modal_request &
    done
    ;;
  2)
    echo "Mode: Image generation requests"
    for i in {1..$NUM_REQUESTS}; do
      echo "Request $i:"
      send_image_generation_request &
    done
    ;;
  *)
    echo "Invalid mode: $MODE. Please use 0, 1, or 2."
    exit 1
    ;;
esac

echo "All requests complete."
