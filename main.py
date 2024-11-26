from flask import Flask, request, jsonify
from flask_cors import CORS
from function import generate_response  # Import the function from function.py
import logging
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Root route for status check
@app.route('/')
def home():
    return "Welcome to the ChatBot API. Use /chat for interactions."

# Chat route for processing user input
@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Log incoming request
        logging.debug("Received request: %s", request.json)

        # Ensure the request contains JSON with the 'message' key
        if request.json and 'message' in request.json:
            user_input = request.json['message']
            conversation_log = request.json.get('conversation_log', [])  # Retrieve or initialize conversation log
            logging.debug("User input: %s", user_input)

            # Generate response using the function from function.py
            response, should_end = generate_response(user_input, conversation_log)

            # Return the response as JSON
            return jsonify({
                'response': response,
                'should_end': should_end,
                'conversation_log': conversation_log
            })
        else:
            logging.error("Invalid request body: %s", request.json)
            return jsonify({'error': 'Invalid request, "message" key not found'}), 400

    except Exception as e:
        # Log unexpected errors
        logging.error("Unexpected Error in /chat route: %s", e, exc_info=True)
        return jsonify({'error': f'Unexpected Error: {str(e)}'}), 500

# Test route (optional, for debugging)
@app.route('/test', methods=['GET'])
def test_route():
    return "This is a test route!"

# Ensure the necessary environment variables are set
@app.before_first_request
def check_environment():
    if not os.getenv("OPENAI_API_KEY"):
        logging.error("OPENAI_API_KEY environment variable is not set!")
        raise EnvironmentError("Please set the OPENAI_API_KEY environment variable.")

# Main entry point for Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
