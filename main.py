from flask import Flask, request, jsonify
import sqlite3
import threading
import queue
import time
from datetime import datetime

app = Flask(__name__)

# Rate limits (requests per minute)
RATE_LIMITS = {
    'text': 5,       # 5 text requests per minute
    'multimodal': 3, # 3 multimodal requests per minute
    'image_gen': 2   # 2 image generation requests per minute
}

# Queues for each request type
queues = {
    'text': queue.Queue(),
    'multimodal': queue.Queue(),
    'image_gen': queue.Queue()
}

# Active request counters
active_requests = {
    'text': 0,
    'multimodal': 0,
    'image_gen': 0
}

# Lock for thread-safe updates to active_requests
lock = threading.Lock()

# Database setup
def init_db():
    conn = sqlite3.connect('requests.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS requests
                 (id INTEGER PRIMARY KEY, type TEXT, input TEXT, output TEXT, timestamp DATETIME)''')
    conn.commit()
    conn.close()

init_db()

# Log a request to the database
def log_request(request_type, input_data, output_data):
    conn = sqlite3.connect('requests.db')
    c = conn.cursor()
    c.execute("INSERT INTO requests (type, input, output, timestamp) VALUES (?, ?, ?, ?)",
              (request_type, str(input_data), str(output_data), datetime.now()))
    conn.commit()
    conn.close()

# Simulate processing a request (replace with actual LLM call)
def process_request(request_type, input_data):
    # Simulate processing time
    time.sleep(2)
    if request_type == 'text':
        return f"Processed text request: {input_data}"
    elif request_type == 'multimodal':
        return f"Processed multimodal request: {input_data}"
    elif request_type == 'image_gen':
        return f"Processed image generation request: {input_data}"
    else:
        return "Invalid request type"

# Worker function to process requests from the queue
def worker(request_type):
    while True:
        # Get the next request from the queue
        input_data = queues[request_type].get()

        # Process the request
        output = process_request(request_type, input_data)
        log_request(request_type, input_data, output)

        # Decrement the active request counter
        with lock:
            active_requests[request_type] -= 1

        # Notify the queue that the task is done
        queues[request_type].task_done()

# Start worker threads for each request type
for request_type in queues:
    threading.Thread(target=worker, args=(request_type,), daemon=True).start()

# API endpoint to handle requests
@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    request_type = data.get('type')
    input_data = data.get('input')

    # Validate request type
    if request_type not in queues:
        return jsonify({"error": "Invalid request type"}), 400

    # Check if the rate limit is exceeded
    with lock:
        if active_requests[request_type] >= RATE_LIMITS[request_type]:
            # Add the request to the queue
            queues[request_type].put(input_data)
            return jsonify({"message": "Request queued due to rate limit"}), 202
        else:
            # Increment the active request counter
            active_requests[request_type] += 1

    # Process the request immediately
    output = process_request(request_type, input_data)
    log_request(request_type, input_data, output)

    # Decrement the active request counter
    with lock:
        active_requests[request_type] -= 1

    return jsonify({"message": "Request processed", "output": output}), 200

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)