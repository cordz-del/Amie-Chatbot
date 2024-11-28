import openai
import os
from typing import Tuple, List, Dict

# Set your OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

# Categorized prompts for dynamic and engaging interaction
EMPATHY_PROMPTS = [
    "How do you think your friend felt during [specific situation]?",
    "What would you say to make someone feel better if they were having a tough day?",
    "Can you think of a time when you felt like someone really understood you?",
]

CONFLICT_RESOLUTION_PROMPTS = [
    "When we disagree with a friend, what could we say to stay calm and solve the problem together?",
    "How could you let someone know how you feel without hurting their feelings?",
    "What’s one nice thing you could say to help someone feel better in an argument?",
]

GENERAL_PROMPTS = [
    "Tell me more about how you're feeling right now.",
    "What do you enjoy doing in your free time?",
    "How can I help you today?",
]

ALL_PROMPTS = EMPATHY_PROMPTS + CONFLICT_RESOLUTION_PROMPTS + GENERAL_PROMPTS

# Quit keywords
QUIT_KEYWORDS = ["quit", "goodbye", "exit", "bye"]

def is_quit_command(user_input: str) -> bool:
    """
    Check if the user input contains a quit command.

    Args:
        user_input (str): The user's input message.

    Returns:
        bool: True if quit command is found, False otherwise.
    """
    for quit_word in QUIT_KEYWORDS:
        if quit_word in user_input.lower():
            return True
    return False

# Function to dynamically select a prompt
def select_prompt(conversation_log: List[Dict[str, str]]) -> str:
    """
    Select a prompt dynamically based on conversation history.

    Args:
        conversation_log (list): A list of previous conversation turns.

    Returns:
        str: A dynamically chosen prompt.
    """
    if len(conversation_log) < len(ALL_PROMPTS):
        return ALL_PROMPTS[len(conversation_log)]
    return "What else would you like to share?"

# Function to generate chatbot response
def generate_response(user_input: str, conversation_log: List[Dict[str, str]]) -> Tuple[str, bool]:
    """
    Generate a response based on user input and conversation history.

    Args:
        user_input (str): The user's input message.
        conversation_log (list): A list of previous conversation turns.

    Returns:
        tuple[str, bool]: The generated chatbot response and a flag indicating if the conversation should end.
    """
    # Check for quit commands
    if is_quit_command(user_input):
        return "Goodbye! It was nice talking to you!", True

    # Select an appropriate prompt based on conversation context
    prompt = select_prompt(conversation_log)

    try:
        # Use OpenAI's ChatCompletion to generate a response
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful and empathetic assistant."},
                *conversation_log,
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": prompt}
            ],
            max_tokens=150,
        )

        # Extract and validate the response structure
        if "choices" in response and len(response['choices']) > 0:
            chatbot_response = response['choices'][0].get('message', {}).get('content', "").strip()
        else:
            return "Error: Invalid API response structure.", False

        # Add the new conversation turn to the log
        conversation_log.append({"user": user_input, "assistant": chatbot_response})
        return chatbot_response, False

    except openai.error.OpenAIError as e:
        # Handle OpenAI-specific errors
        error_message = f"OpenAI API error: {str(e)}"
        print(error_message)
        return error_message, False

    except Exception as e:
        # Handle other exceptions such as network issues
        error_message = f"An unexpected error occurred: {str(e)}"
        print(error_message)
        return error_message, False
