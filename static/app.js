// Select DOM elements
const startRecordBtn = document.getElementById('start-record-btn');
const stopRecordBtn = document.getElementById('stop-record-btn');
const status = document.getElementById('status');
const chatResponse = document.getElementById('chat-response');
const chatHistory = document.getElementById('chat-history');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');

let recognition;

// Check for browser support for Speech Recognition
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
} else if ('SpeechRecognition' in window) {
    recognition = new SpeechRecognition();
} else {
    alert('Your browser does not support speech recognition.');
}

// Configure recognition if supported
if (recognition) {
    recognition.continuous = false; // Stop after each utterance
    recognition.interimResults = false; // Don't show interim results
    recognition.lang = 'en-US'; // Set language to English

    recognition.onstart = () => {
        status.textContent = 'Listening...';
        startRecordBtn.disabled = true;
        stopRecordBtn.disabled = false;
    };

    recognition.onresult = async (event) => {
        const transcript = event.results[0][0].transcript.trim();
        status.textContent = `You said: ${transcript}`;
        if (transcript) {
            await sendMessage(transcript);
        } else {
            chatResponse.textContent = "No input detected. Please try again.";
        }
    };

    recognition.onerror = (event) => {
        status.textContent = `Error occurred: ${event.error}`;
    };

    recognition.onend = () => {
        startRecordBtn.disabled = false;
        stopRecordBtn.disabled = true;
    };

    startRecordBtn.addEventListener('click', () => {
        recognition.start();
    });

    stopRecordBtn.addEventListener('click', () => {
        recognition.stop();
    });
}

// Handle form submission for text-based chat
chatForm.addEventListener('submit', async (event) => {
    event.preventDefault(); // Prevent form from reloading the page
    const message = chatInput.value.trim();
    if (message) {
        await sendMessage(message);
        chatInput.value = ''; // Clear input field after sending
    } else {
        chatResponse.textContent = "Please enter a message.";
    }
});

// Function to send a message to the chatbot API
async function sendMessage(message) {
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });

        const data = await response.json();
        if (data && data.response) {
            chatResponse.textContent = `Chatbot: ${data.response}`;
            speakText(data.response);

            // Add messages to chat history
            chatHistory.innerHTML += `
                <p><strong>You:</strong> ${message}</p>
                <p><strong>Chatbot:</strong> ${data.response}</p>`;
            chatHistory.scrollTop = chatHistory.scrollHeight; // Auto-scroll to the latest message
        } else if (data.error) {
            chatResponse.textContent = `Error: ${data.error}`;
        } else {
            chatResponse.textContent = "Error: No response from the chatbot.";
        }
    } catch (error) {
        chatResponse.textContent = `Error: ${error.message}`;
        console.error("Error in sendMessage:", error);
    }
}

// Function to speak chatbot responses
function speakText(text) {
    const synth = window.speechSynthesis;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.onerror = () => {
        console.error("Error occurred during speech synthesis.");
    };
    synth.speak(utterance);
}
