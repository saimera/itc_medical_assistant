import { useEffect, useRef, useState } from "react";

const SOURCE_PATTERN = /\s\*Source:\s\*https?:\/\/\S+/gi;

function Message({ role, text, sources }) {
  const isUser = role === "user";

  return (
    <div
      className={`my-2.5 whitespace-pre-wrap break-words leading-relaxed ${
        isUser
          ? "ml-auto max-w-[90%] rounded-3xl bg-[#193b70] px-4 py-3 text-slate-100 sm:max-w-[82%]"
          : "py-3"
      }`}
    >
      {text}

      {sources?.length > 0 && (
        <div className="mt-2.5 text-[13px]">
          Sources:
          {sources.map((source) => (
            <a
              key={source.url}
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-1 block break-words text-[#086b67] hover:underline"
            >
              {source.title}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

export default function MedicalRag() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  const chatStarted = messages.length > 0;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const addMessage = (message) => setMessages((prev) => [...prev, message]);

  async function handleSubmit(event) {
    event.preventDefault();

    const text = question.trim();
    if (!text || loading) return;

    addMessage({ role: "user", text });
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }),
      });

      if (!response.ok) throw new Error(`Request failed: ${response.status}`);

      const data = await response.json();

      addMessage({
        role: "assistant",
        text: (data.answer || "No answer returned.")
          .replace(SOURCE_PATTERN, "")
          .trim(),
        sources: data.sources,
      });
    } catch (error) {
      console.error("Error fetching response:", error);
      addMessage({
        role: "assistant",
        text: "Could not get a response. Check that the backend is running.",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex h-dvh flex-col overflow-hidden bg-sky-50 px-4 pb-3 pt-4 text-gray-800 sm:px-7">
      <header>
        <p className="text-[13px] text-slate-600">
          Explore clinic, treatment, FAQ and reviews information from ITC’s
          PlacidWay profile.
        </p>
      </header>

      <section
        className={`mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col ${
          chatStarted ? "" : "justify-center"
        }`}
      >
        {chatStarted ? (
          <div
            aria-live="polite"
            className="flex-1 overflow-y-auto py-6 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          >
            {messages.map((message, index) => (
              <Message key={index} {...message} />
            ))}
            {loading && <Message role="assistant" text="Searching the profile…" />}
            <div ref={bottomRef} />
          </div>
        ) : (
          <h2 className="mb-6 text-center text-xl">
            How can we help you explore ITC?
          </h2>
        )}

        <form
          onSubmit={handleSubmit}
          className="flex w-full max-w-[750px] items-center gap-1 self-center rounded-full border border-[#cbd9df] bg-white p-1.5 focus-within:border-[#218779] focus-within:ring-[3px] focus-within:ring-[#218779]/15"
        >
          <input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask a question..."
            aria-label="Your question"
            autoComplete="off"
            autoFocus
            className="min-w-0 flex-1 bg-transparent px-4 py-3 text-[15px] outline-none placeholder:text-slate-500"
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            aria-label="Send message"
            className="h-9 w-9 shrink-0 rounded-full bg-[#34a294] text-lg text-white disabled:cursor-not-allowed disabled:opacity-60"
          >
            ↑
          </button>
        </form>
      </section>

      <footer className="pt-2 text-center text-[13px] text-slate-600">
        Answers are based on the source profile and are not medical advice.
      </footer>
    </main>
  );
}