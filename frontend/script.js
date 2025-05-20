// Global state for conversation
let conversationHistory = [];
let isConversationMode = false;

// Function to add a message to the chat UI
function addMessageToChat(content, isUser = false) {
  const chatContainer = document.getElementById("chatContainer");
  const messageDiv = document.createElement("div");
  
  messageDiv.className = isUser 
    ? "message user-message bg-indigo-100 p-3 rounded-lg ml-8" 
    : "message assistant-message bg-white border p-3 rounded-lg mr-8 shadow-sm";
  
  // For multi-paragraph responses
  const formattedContent = content.split('\n').map(line => 
    line.trim() === '' ? '<br>' : line
  ).join('<br>');
  
  messageDiv.innerHTML = `<p class="whitespace-pre-wrap">${formattedContent}</p>`;
  chatContainer.appendChild(messageDiv);
  
  // Scroll to bottom of chat
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Function to reset conversation
function resetConversation() {
  conversationHistory = [];
  isConversationMode = false;
  document.getElementById("conversationMode").classList.add("hidden");
  
  // Clear chat except for the welcome message
  const chatContainer = document.getElementById("chatContainer");
  while (chatContainer.childNodes.length > 1) {
    chatContainer.removeChild(chatContainer.lastChild);
  }
}

async function submitQuery() {
  const input = document.getElementById("queryInput").value.trim();
  
  if (!input) {
    alert("Please enter your query.");
    return;
  }
  
  // Add user message to chat
  addMessageToChat(input, true);
  
  // Clear input field
  document.getElementById("queryInput").value = "";
  
  try {
    // Close any existing streaming
    if (window.eventSource) {
      window.eventSource.close();
    }
    
    // Create payload with conversation history if in conversation mode
    const payload = {
      user_input: input,
      conversation_history: isConversationMode ? conversationHistory : []
    };

    // Make request to API
    const response = await fetch("http://127.0.0.1:8000/api/vakeel", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      let errorMessage = "Unknown error";
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || "Unknown error";
      } catch (e) {
        errorMessage = await response.text() || "Unknown error";
      }
      addMessageToChat(`Error: ${errorMessage}`);
      return;
    }

    // Variables for tracking response
    let currentResponseText = "";
    let intent = null;

    // Use the ReadableStream API for streaming
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    let buffer = ""; // Buffer for incomplete chunks

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      // Decode the chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });
      
      // Process SSE format (data: {...})
      let lines = buffer.split("\n\n");
      
      // Last line might be incomplete, keep it in buffer
      buffer = lines.pop() || "";
      
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.substring(6));
            
            // Handle intent information
            if (data.intent && !intent) {
              intent = data.intent;
              console.log("Detected intent:", intent);
              
              // If legal intent, enable conversation mode
              if (intent === "legal" && !isConversationMode) {
                isConversationMode = true;
                document.getElementById("conversationMode").classList.remove("hidden");
              }
            }
            
            // Handle content chunks
            if (data.content) {
              currentResponseText += data.content;
              
              // If we have an existing message element, update it
              const messages = document.querySelectorAll('.assistant-message');
              const lastMessage = messages[messages.length - 1];
              
              if (lastMessage && lastMessage.querySelector('p').innerHTML === "Thinking...") {
                lastMessage.querySelector('p').innerHTML = currentResponseText;
              } else {
                // Otherwise, create a temporary element showing that the assistant is responding
                if (currentResponseText.length === data.content.length) {
                  addMessageToChat("Thinking...");
                }
              }
            }
          } catch (e) {
            console.error("Failed to parse chunk:", line, e);
          }
        }
      }
    }

    // Process any remaining data in buffer
    if (buffer && buffer.startsWith("data: ")) {
      try {
        const data = JSON.parse(buffer.substring(6));
        if (data.content) {
          currentResponseText += data.content;
        }
      } catch (e) {
        console.error("Failed to parse final chunk:", buffer, e);
      }
    }
    
    // Update the message with the complete response
    const messages = document.querySelectorAll('.assistant-message');
    const lastMessage = messages[messages.length - 1];
    
    if (lastMessage && lastMessage.querySelector('p').innerHTML === "Thinking...") {
      lastMessage.querySelector('p').innerHTML = currentResponseText;
    } else {
      addMessageToChat(currentResponseText);
    }
    
    // If in conversation mode, update the history
    if (isConversationMode && intent === "legal") {
      conversationHistory.push(
        {role: "user", content: input},
        {role: "assistant", content: currentResponseText}
      );
    }

  } catch (error) {
    console.error("Streaming error:", error);
    addMessageToChat("Something went wrong. Please try again.");
  }
}