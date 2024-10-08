document.addEventListener("DOMContentLoaded", function() {
    // Select elements
    const chatbotToggler = document.querySelector(".chatbot-toggler");
    const closeBtn = document.querySelector(".close-btn");
    const chatbox = document.querySelector(".chatbox");
    const chatInput = document.querySelector(".chat-input textarea");
    const sendChatBtn = document.querySelector(".chat-input span");

    // Check if elements are found
    if (!chatInput || !chatbox) {
        console.error("Required elements are missing from the DOM.");
        return;
    }

    let userMessage = null; // Variable to store user's message
    const inputInitHeight = chatInput.scrollHeight;

    // Gemini API configuration
    const API_KEY = "AIzaSyBSnnUpQG1Hwoahpnpjr2z9icLkbHl-DlQ"; // Replace with your Gemini API key
    const API_URL = `https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=${API_KEY}`;

    const createChatLi = (message, className) => {
        // Create a chat <li> element with passed message and className
        const chatLi = document.createElement("li");
        chatLi.classList.add("chat", `${className}`);
        let chatContent = className === "outgoing" ? `<p></p>` : `<span class="material-symbols-outlined">smart_toy</span><p></p>`;
        chatLi.innerHTML = chatContent;
        chatLi.querySelector("p").textContent = message;
        return chatLi; // return chat <li> element
    }

    const generateResponse = async (chatElement) => {
        const messageElement = chatElement.querySelector("p");
    
        const requestOptions = {
            method: "POST",
            headers: { 
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                contents: [
                    {
                        role: "user",
                        parts: [
                            {
                                text: userMessage
                            }
                        ]
                    }
                ]
            }),
        }
    
        console.log('Request options:', requestOptions); // Log request options for debugging
    
        try {
            const response = await fetch(API_URL, requestOptions);
            console.log('Response status:', response.status); // Log response status
            const data = await response.json();
            console.log('Response data:', data); // Log response data
    
            if (!response.ok) {
                // Adjust error handling to check for the presence of an error message
                throw new Error(data.error ? data.error.message : 'Unknown error');
            }
    
            // Extract the text content from the response
            const responseText = data.candidates?.[0]?.content?.parts?.[0]?.text || 'No response text available';
            messageElement.textContent = responseText;
        } catch (error) {
            messageElement.classList.add("error");
            messageElement.textContent = error.message;
        } finally {
            chatbox.scrollTo(0, chatbox.scrollHeight);
        }
    }
    
    const handleChat = () => {
        userMessage = chatInput.value.trim(); // Get user entered message and remove extra whitespace
        if (!userMessage) return;
        console.log("userMessage", userMessage);
        // Clear the input textarea and set its height to default
        chatInput.value = "";
        chatInput.style.height = `${inputInitHeight}px`;

        // Append the user's message to the chatbox
        chatbox.appendChild(createChatLi(userMessage, "outgoing"));
        chatbox.scrollTo(0, chatbox.scrollHeight);

        setTimeout(() => {
            // Display "Thinking..." message while waiting for the response
            const incomingChatLi = createChatLi("Thinking...", "incoming");
            chatbox.appendChild(incomingChatLi);
            chatbox.scrollTo(0, chatbox.scrollHeight);
            generateResponse(incomingChatLi);
        }, 600);
    }

    chatInput.addEventListener("input", () => {
        // Adjust the height of the input textarea based on its content
        chatInput.style.height = `${inputInitHeight}px`;
        chatInput.style.height = `${chatInput.scrollHeight}px`;
    });

    chatInput.addEventListener("keydown", (e) => {
        // If Enter key is pressed without Shift key and the window 
        // width is greater than 800px, handle the chat
        if (e.key === "Enter" && !e.shiftKey && window.innerWidth > 800) {
            e.preventDefault();
            handleChat();
        }
    });

    sendChatBtn.addEventListener("click", handleChat);
    closeBtn.addEventListener("click", () => document.body.classList.remove("show-chatbot"));
    chatbotToggler.addEventListener("click", () => document.body.classList.toggle("show-chatbot"));
});
