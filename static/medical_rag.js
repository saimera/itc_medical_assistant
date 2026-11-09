const app = document.querySelector(".app");
const footer = document.querySelector("footer");
const welcome = document.querySelector("#welcome");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#question");
const send = document.querySelector("#send");
const messages = document.querySelector("#messages");

function addMessage(text, role) {
  const bubble = document.createElement("div");
  bubble.className = `message ${role}`;
  bubble.textContent = text;
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
  return bubble;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) return;
  if (!app.classList.contains("chat-started")) {
    app.classList.add("chat-started");
    footer.before(form);
    welcome.remove();
  }

  addMessage(question, "user");
  input.value = "";
  send.disabled = true;

  const reply = addMessage("Searching the profile…", "assistant");

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });

    if (!response.ok) throw new Error();
    const data = await response.json();

    reply.textContent = (data.answer || "No answer returned.")
      .replace(/\s*Source:\s*https?:\/\/\S+/gi, "")
      .trim();

    if (data.sources?.length) {
      const sourceBox = document.createElement("div");
      sourceBox.className = "sources";
      sourceBox.textContent = "Sources:";

      data.sources.forEach((url) => {
        const link = document.createElement("a");
        link.href = url;
        link.textContent = url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        sourceBox.appendChild(link);
      });

      reply.appendChild(sourceBox);
    }
  } catch {
    reply.textContent = "Could not get a response. Check that the backend is running.";
  } finally {
    send.disabled = false;
    input.focus();
    messages.scrollTop = messages.scrollHeight;
  }
});
