// ---------------------- Create chat bubble ----------------------
function createMessageElement(text, sender) {
  const div = document.createElement("div");
  div.className = sender;
  div.innerHTML = sender === "user" ? `👤 ${text}` : `🤖 ${text}`;
  return div;
}

// ---------------------- Send message ----------------------
function sendMessage() {
  const inputField = document.getElementById("userInput");
  const userInput = inputField.value.trim();
  if (!userInput) return;

  const chatBox = document.getElementById("chatBox");

  // Add user message
  chatBox.appendChild(createMessageElement(userInput, "user"));
  inputField.value = "";

  // Send to backend
  fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_input: userInput })
  })
    .then(res => res.json())
    .then(data => {
      const botReply = data.response;

      // Add bot reply
      chatBox.appendChild(createMessageElement(botReply, "bot"));

      // Add feedback buttons
      const feedbackDiv = document.createElement("div");
      feedbackDiv.className = "feedback";
      feedbackDiv.innerHTML = `<span>Feedback:</span>`;

      const likeBtn = document.createElement("button");
      likeBtn.textContent = "👍";
      likeBtn.addEventListener("click", () =>
        sendFeedback(userInput, botReply, "👍", likeBtn)
      );

      const dislikeBtn = document.createElement("button");
      dislikeBtn.textContent = "👎";
      dislikeBtn.addEventListener("click", () =>
        sendFeedback(userInput, botReply, "👎", dislikeBtn)
      );

      feedbackDiv.appendChild(likeBtn);
      feedbackDiv.appendChild(dislikeBtn);

      chatBox.appendChild(feedbackDiv);

      // Auto-scroll
      chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(err => console.error("Chat request failed:", err));
}

// ---------------------- Send feedback ----------------------
function sendFeedback(original, reply, feedback, btnElement) {
  fetch("/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      original_input: original,
      bot_reply: reply,
      feedback: feedback
    })
  })
    .then(() => {
      const buttons = btnElement.parentNode.querySelectorAll("button");
      buttons.forEach(btn => (btn.disabled = true));

      btnElement.style.backgroundColor = "#0077b6";
      btnElement.style.color = "white";
      btnElement.style.opacity = "0.8";
    })
    .catch(err => console.error("Feedback save failed:", err));
}

// ---------------------- Reset chat ----------------------
function resetChat() {
  fetch("/reset", {
    method: "POST"
  })
    .then(res => res.json())
    .then(data => {
      const chatBox = document.getElementById("chatBox");
      chatBox.innerHTML = "";
      chatBox.appendChild(createMessageElement("New conversation started!", "bot"));
    })
    .catch(err => console.error("Reset failed:", err));
}

// ---------------------- Event listeners ----------------------
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("send-btn").addEventListener("click", sendMessage);
  document.getElementById("userInput").addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      sendMessage();
    }
  });
  document.getElementById("reset-btn").addEventListener("click", resetChat);
});
