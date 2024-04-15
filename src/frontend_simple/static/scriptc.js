// Enter button for sending messages to the chatbot
document.addEventListener('DOMContentLoaded', (event) => {
    var input = document.getElementById("message-input");

    input.addEventListener("keyup", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });
});

function sendMessage() {
    var messageInput = document.getElementById("message-input");
    var message = messageInput.value.trim();
    var conversationDiv = document.getElementById("conversation");
    var chatLogo = document.querySelector(".chat-logo");

    // Hiding chatbot logo when chat starts
    if (chatLogo && message.trim() !== "") {chatLogo.style.display = "none";}

    // Display user message in the conversation
    appendMessage("User: " + message);

    // Use fetch to send data to Flask backend
    fetch('/{{state}}/{{hospital.url}}/chatbot/response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message }),
    })
        .then(response => response.json())
        .then(data => {
            // Display chatbot response in the conversation
            appendMessage("Chatbot: " + data.response);
        })
        .catch((error) => {
            console.error('Error:', error);
        });

    // Clear the input field after sending the message
    messageInput.value = "";
}

function appendMessage(message) {
    var conversationDiv = document.getElementById("conversation");
    var messageDiv = document.createElement("div");
    messageDiv.textContent = message;
    conversationDiv.appendChild(messageDiv);
    messageDiv.scrollIntoView({ behavior: "smooth" });
}