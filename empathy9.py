from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from TTS.api import TTS
import openai
import os
import soundfile as sf
import io

# Set your OpenAI API Key from an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Coqui TTS
# Replace 'tts_models/en/ljspeech/vits--neon' with your desired TTS model
tts = TTS(model_name="tts_models/en/ljspeech/vits--neon", progress_bar=False, gpu=False)

# Filters for inappropriate content
FORBIDDEN_TOPICS = ["race", "religion", "nationality", "violence", "hate", "insult", "offensive"]

# Quit keywords
QUIT_KEYWORDS = ["goodbye", "exit", "leave", "quit", "bye"]

# Function to filter inappropriate content
def filter_inappropriate_content(user_input):
    if not user_input:
        return False
    for topic in FORBIDDEN_TOPICS:
        if topic in user_input.lower():
            return True
    return False

# Function to recognize quit commands
def is_quit_command(user_input):
    if not user_input:
        return False
    for quit_word in QUIT_KEYWORDS:
        if quit_word in user_input.lower():
            return True
    return False

# Function to process user input using OpenAI's API
def generate_response(user_input, conversation_history):
    try:
        if not user_input:
            return "I didn't catch that. Could you say it again?", False
        if filter_inappropriate_content(user_input):
            return "Let's keep our conversation kind and positive.", False
        if is_quit_command(user_input):
            return "Goodbye! It was so nice talking to you!", True

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful chatbot."},
                {"role": "user", "content": user_input},
            ]
        )

        chatbot_response = response.choices[0].message.content.strip()
        conversation_history.append({"user": user_input, "assistant": chatbot_response})
        return chatbot_response, False

    except Exception as e:
        return f"An error occurred: {str(e)}", False

# Flask route for JSON-based interaction
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_input = data.get("message", "")
        conversation_history = data.get("history", [])

        # Generate chatbot response
        response, quit_flag = generate_response(user_input, conversation_history)

        # Convert response to speech using Coqui TTS
        audio_data = tts.tts(response)
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio_data, samplerate=tts.synthesizer.output_sample_rate, format='WAV')
        audio_buffer.seek(0)

        # Save the audio file to static for Replit
        with open("static/response.wav", "wb") as f:
            f.write(audio_buffer.read())

        return jsonify({"reply": response, "history": conversation_history, "quit": quit_flag})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Flask route to serve audio file
@app.route("/audio/response", methods=["GET"])
def get_audio_response():
    try:
        return send_file("static/response.wav", mimetype="audio/wav")
    except Exception as e:
        return jsonify({"error": f"Could not fetch audio file: {e}"}), 500

# Entry point for the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
