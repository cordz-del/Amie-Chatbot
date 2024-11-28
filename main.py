from flask import Flask, request, jsonify
from flask_cors import CORS
from function import generate_response  # Import function from function.py
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def home():
    """
    Root endpoint for the chatbot API.
    """
    return "Welcome to the ChatBot API! Use /chat for chatbot interactions."

@app.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint for processing user input and generating chatbot responses.

    Returns:
        JSON response containing the chatbot reply, conversation log, and audio if applicable.
    """
    try:
        # Log incoming request
        logging.debug("Received request: %s", request.json)

        # Extract data from request
        if not request.json or 'message' not in request.json:
            logging.error("Invalid request: Missing 'message' key.")
            return jsonify({"error": "Invalid request, 'message' key not found."}), 400

        user_input = request.json['message']
        conversation_log = request.json.get('conversation_log', [])

        # Generate response using the imported function
        response, should_end = generate_response(user_input, conversation_log)

        # If `empathy9.py` includes audio processing, encode the TTS response
        try:
            from empathy9 import process_audio_response
            audio_base64 = process_audio_response(response)  # Generate audio from the chatbot response
        except ImportError as e:
            logging.warning("TTS functionality not available. Skipping audio generation.")
            audio_base64 = None

        # Build the JSON response
        return jsonify({
            "response": response,
            "should_end": should_end,
            "conversation_log": conversation_log,
            "audio": audio_base64  # Include audio in the response if available
        })
    except Exception as e:
        logging.error("An error occurred in /chat: %s", str(e), exc_info=True)
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

# Test route to ensure the server is running
@app.route('/test', methods=['GET'])
def test_route():
    """
    Test endpoint for verifying the server is operational.
    """
    return "Test route is working fine!"

if __name__ == '__main__':
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)
