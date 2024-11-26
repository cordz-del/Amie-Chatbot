from flask import Flask, request, jsonify
import pyttsx3
import openai
import speech_recognition as sr
import time
import os

# Set your OpenAI API Key from an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__)

# Initialize speech recognizer and text-to-speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Filters for inappropriate content
FORBIDDEN_TOPICS = ["race", "religion", "nationality", "violence", "hate", "insult", "offensive"]

# Quit keywords
QUIT_KEYWORDS = ["goodbye", "exit", "leave", "quit", "bye"]

# Function to set the voice to "English (America, New York City)" and max volume
def set_voice_to_nyc():
    voices = engine.getProperty("voices")
    for voice in voices:
        if "english (america, new york city)" in voice.name.lower():
            engine.setProperty("voice", voice.id)
            print(f"Voice set to: {voice.name}")
            break
    else:
        print("Desired voice not found. Using default voice.")
    engine.setProperty("volume", 1.0)
    print("Volume set to maximum.")

set_voice_to_nyc()

# Function to speak and display text
def speak_and_display(text):
    print(f"Chatbot: {text}")
    engine.say(text)
    engine.runAndWait()
    time.sleep(0.3)

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
            model="gpt-3.5-turbo",  # Ensure the correct model is being used
            messages=[
                {"role": "system", "content": "You are a helpful chatbot."},
                {"role": "user", "content": user_input},
            ]
        )

        chatbot_response = response.choices[0].message.content.strip()  # Corrected response access
        conversation_history.append({"user": user_input, "assistant": chatbot_response})
        return chatbot_response, False

    except Exception as e:
        return f"An error occurred: {str(e)}", False

# Function to process empathy data
def process_empathy(data):
    """
    Process the input data to generate an empathetic response.

    Args:
        data (dict): Input data containing user messages and context.

    Returns:
        dict: Processed data with an empathetic response.
    """
    message = data.get("message", "")
    empathetic_response = f"I understand that you're feeling: {message}. It's important to acknowledge these emotions."
    return {"response": empathetic_response}

# Flask route for JSON-based interaction
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_input = data.get("message", "")
        conversation_history = data.get("history", [])

        # Process empathy if a key exists in the data
        if "empathy" in data:
            empathy_response = process_empathy(data)
            return jsonify(empathy_response)

        # Generate chatbot response
        response, quit_flag = generate_response(user_input, conversation_history)
        return jsonify({"reply": response, "history": conversation_history, "quit": quit_flag})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Function for speech-to-text chatbot interaction
def voice_chat():
    print("Starting voice interaction mode...")
    conversation_history = []

    speak_and_display("Hi there! How are you today?")
    while True:
        try:
            with sr.Microphone() as source:
                speak_and_display("Please share your thoughts.")
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=8)
                user_input = recognizer.recognize_google(audio)
                print(f"User: {user_input}")
        except sr.UnknownValueError:
            speak_and_display("I'm sorry, I didn't catch that. Could you try again?")
            continue
        except sr.WaitTimeoutError:
            speak_and_display("I didn't hear anything. Could you try again?")
            continue

        if is_quit_command(user_input):
            speak_and_display("Goodbye! It was so nice talking to you!")
            break

        response, quit_flag = generate_response(user_input, conversation_history)
        conversation_history.append({"user": user_input, "bot": response})
        speak_and_display(response)

# Entry point for the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
