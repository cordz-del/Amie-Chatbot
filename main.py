import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from empathy9 import process_audio_response, process_empathy  # Import necessary functions
import openai

# Set up OpenAI API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint for handling text-based chat requests.
    """
    try:
        data = request.get_json()
        if not data or "message" not in data or "age" not in data:
            return jsonify({"error": "Invalid input. Both 'message' and 'age' are required."}), 400

        user_input = data["message"]
        age = data["age"]

        # Call OpenAI API for response
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful and empathetic assistant specializing in social and emotional learning."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=150,
        )
        chatbot_response = response['choices'][0]['message']['content'].strip()

        # Generate audio response
        audio_base64 = process_audio_response(chatbot_response, age)

        return jsonify({
            "response": chatbot_response,
            "audio": audio_base64
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/voice', methods=['POST'])
def voice():
    """
    Endpoint for handling voice-based chat requests.
    """
    try:
        data = request.get_json()
        if not data or "audio" not in data or "age" not in data:
            return jsonify({"error": "Invalid input. Both 'audio' and 'age' are required."}), 400

        audio_file = data["audio"]
        age = data["age"]

        # Process voice data (e.g., transcribe audio to text)
        from empathy9 import recognizer
        with open(audio_file, "rb") as source:
            audio = recognizer.record(source)
        user_input = recognizer.recognize_google(audio)

        # Generate chatbot response
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful and empathetic assistant specializing in social and emotional learning."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=150,
        )
        chatbot_response = response['choices'][0]['message']['content'].strip()

        # Generate audio response
        audio_base64 = process_audio_response(chatbot_response, age)

        return jsonify({
            "response": chatbot_response,
            "audio": audio_base64,
            "user_input": user_input
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/test', methods=['GET'])
def test():
    """
    Endpoint for testing the server is operational.
    """
    return "Test route is working!", 200


if __name__ == "__main__":
    # Retrieve host and port from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))

    # Run the Flask development server for local testing
    app.run(host=host, port=port, debug=True)
