from flask import Flask, request, jsonify
from flask_cors import CORS
import pyttsx3
import openai
import sounddevice as sd
import speech_recognition as sr
import random
import time
import os
import base64
import io
import soundfile as sf
import wave

# Set your OpenAI API Key from an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Initialize pyttsx3 TTS and Coqui TTS
engine = pyttsx3.init()
try:
    from TTS.api import TTS
    tts = TTS(model_name="tts_models/en/ljspeech/vits--neon", progress_bar=False, gpu=False)
    coqui_tts_enabled = True
except ImportError:
    print("Coqui TTS is not available. Defaulting to pyttsx3 for TTS.")
    coqui_tts_enabled = False

# Initialize Speech Recognition
recognizer = sr.Recognizer()

# Filters for inappropriate content
FORBIDDEN_TOPICS = ["race", "religion", "nationality", "violence", "hate", "insult", "offensive"]

# Quit keywords
QUIT_KEYWORDS = ["goodbye", "exit", "leave", "quit", "bye"]

# Prompts for conversations
CONVERSATION_PROMPTS = [
    {"prompt": "What do you love most about your day so far?", "context": "general"},
    {"prompt": "How do you think your friend felt during [specific situation]?", "context": "empathy"},
    {"prompt": "What’s something interesting you learned about someone else’s culture or background?", "context": "cultural_awareness"},
    {"prompt": "If you could invent something to make life easier, what would it be?", "context": "creativity"},
    {"prompt": "When we disagree with a friend, what could we say to solve the problem together?", "context": "conflict_resolution"}
]

# Function to set the pyttsx3 voice to Zira
def set_voice_to_zira():
    voices = engine.getProperty('voices')
    for voice in voices:
        if "zira" in voice.name.lower():
            engine.setProperty('voice', voice.id)
            print(f"Voice set to: {voice.name}")
            break
    engine.setProperty('volume', 1.0)  # Set volume to maximum

set_voice_to_zira()

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

# Function to record audio using sounddevice
def record_audio():
    fs = 16000  # Sample rate
    duration = 5  # Duration in seconds
    print("Recording audio...")
    audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()  # Wait for the recording to finish
    return audio_data

# Function to process audio and convert to text
def process_audio(audio_data):
    # Save the recorded audio to a file
    with wave.open("audio_input.wav", "wb") as wf:
        wf.setnchannels(1)  # Mono audio
        wf.setsampwidth(2)  # 2 bytes per sample
        wf.setframerate(16000)  # Sample rate
        wf.writeframes(audio_data)

    # Use SpeechRecognition to process the saved file
    with sr.AudioFile("audio_input.wav") as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"Recognized Speech: {text}")
            return text
        except sr.UnknownValueError:
            print("Speech Recognition could not understand audio.")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results from Speech Recognition service; {e}")
            return ""

# Function to generate chatbot responses
def generate_response(user_input, conversation_log):
    if not user_input:
        return "I didn't catch that. Could you try again?", False
    if filter_inappropriate_content(user_input):
        return "Let's keep our conversation kind and positive.", False
    if is_quit_command(user_input):
        return "Goodbye! It was so nice talking to you!", True

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful and empathetic assistant."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=150
        )
        chatbot_response = response['choices'][0]['message']['content'].strip()
        conversation_log.append({"user": user_input, "assistant": chatbot_response})
        return chatbot_response, False
    except Exception as e:
        print(f"Error generating response: {e}")
        return f"An error occurred: {e}", False

# Flask route for chatbot interactions
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_input = data.get("message", "")
        conversation_log = data.get("conversation_log", [])

        chatbot_response, quit_flag = generate_response(user_input, conversation_log)

        # Generate TTS audio for the response
        if coqui_tts_enabled:
            audio_data = tts.tts(chatbot_response)
            audio_buffer = io.BytesIO()
            sf.write(audio_buffer, audio_data, samplerate=tts.synthesizer.output_sample_rate, format='WAV')
            audio_buffer.seek(0)
            audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
        else:
            engine.say(chatbot_response)
            engine.runAndWait()
            audio_base64 = None

        return jsonify({
            "response": chatbot_response,
            "should_end": quit_flag,
            "conversation_log": conversation_log,
            "audio": audio_base64
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Flask route for audio recording test
@app.route("/test-audio", methods=["POST"])
def test_audio():
    try:
        audio_data = record_audio()
        user_input = process_audio(audio_data)
        return jsonify({"recognized_text": user_input})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Entry point for the application
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run chatbot in web or voice mode.")
    parser.add_argument("--mode", choices=["web", "voice"], default="web", help="Mode to run the chatbot.")
    args = parser.parse_args()

    if args.mode == "web":
        app.run(host="0.0.0.0", port=5000, debug=True)
    elif args.mode == "voice":
        print("Voice mode is not fully supported in this integration.")
