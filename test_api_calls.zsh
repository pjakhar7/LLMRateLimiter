#!/bin/zsh
# test_api_calls.zsh
# This script sends multiple concurrent API calls to test the rate limiter.
# Ensure your Flask API is running on http://localhost:5080 before running this script.

# Function to send a single request.
function send_multi_modal_request {
  echo "Sending request..."
  curl -s -X POST "http://localhost:5080/submit" \
       -H "Content-Type: multipart/form-data" \
       -F 'text="What is in this picture?"' \
       -F 'file=@cat.png'
  echo "\n-----------------------------\n"
}

# Number of concurrent requests to simulate.
NUM_REQUESTS=5

echo "Sending $NUM_REQUESTS concurrent requests..."

# Loop to send multiple requests concurrently.
for i in {1..$NUM_REQUESTS}; do
  echo $i
  send_multi_modal_request &
done

# Wait for all background processes to complete.
wait

echo "All requests complete."
