import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "👋 Hello! I’m **FinBot**, your personal finance assistant.\n\nYou can ask your financial queries and I will try my best to answer them.",
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);

  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  const exampleQuestions = [
    "How to check my account balance?",
    "How can I transfer funds?",
    "What is Sofi",
    "What is the current interest rates offered by Sofi?",
  ];

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
    inputRef.current?.focus();
  }, [messages, isTyping]);

  const handleSend = async (q = null) => {
    const userQuestion = q || question;
    if (!userQuestion.trim()) return;

    setMessages((prev) => [...prev, { sender: "user", text: userQuestion }]);
    setIsTyping(true);
    setQuestion("");

    try {
      const res = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/chat`,
        { question: userQuestion }
      );

      const answer = res.data.answer;
      setMessages((prev) => [...prev, { sender: "bot", text: answer }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "⚠️ Waiting for server to spin up. Please retry your question." },
      ]);
    }

    setIsTyping(false);
  };

  return (
    <div
      className="chat-container"
      style={{
        maxWidth: "600px",
        margin: "auto",
        padding: "20px",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <h2 style={{ textAlign: "center", fontWeight: "bold", fontSize: "24px" }}>
        💬 FinBot
      </h2>

      {/* Chat window */}
      <div
        style={{
          border: "1px solid #ccc",
          borderRadius: "12px",
          padding: "15px",
          height: "450px",
          overflowY: "auto",
          marginBottom: "15px",
          background: "#f7f7f7",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              display: "flex",
              justifyContent: msg.sender === "user" ? "flex-end" : "flex-start",
              margin: "6px 0",
            }}
          >
            <div
              style={{
                background: msg.sender === "user"
                  ? "linear-gradient(135deg, #4facfe, #00f2fe)"
                  : "#e0e0e0",
                color: msg.sender === "user" ? "white" : "black",
                padding: "12px",
                borderRadius: "16px",
                maxWidth: "75%",
                boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
                wordWrap: "break-word",
                whiteSpace: "pre-wrap",
                animation: "fadeIn 0.3s ease",
              }}
            >
              <ReactMarkdown
                components={{
                  a: ({ node, ...props }) => (
                    <a
                      {...props}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {props.children /* <-- ensures content is inside the link */}
                    </a>
                  ),
                }}
              >
                {msg.text}
              </ReactMarkdown>

            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {isTyping && (
          <div style={{ display: "flex", alignItems: "center", marginTop: "5px", gap: "4px", paddingLeft: "5px" }}>
            <div style={{ fontStyle: "italic", color: "#888" }}>AI is typing</div>
            <div style={{ display: "flex", gap: "2px" }}>
              <div className="dot" />
              <div className="dot" />
              <div className="dot" />
            </div>
          </div>
        )}

        {/* Invisible div to scroll */}
        <div ref={chatEndRef} />
      </div>

      {/* Input + Send button */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        style={{ display: "flex", gap: "8px", marginBottom: "15px" }}
      >
        <input
          ref={inputRef}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Type your question..."
          style={{
            flex: 1,
            padding: "12px",
            fontSize: "16px",
            borderRadius: "8px",
            border: "1px solid #ccc",
          }}
        />
        <button
          type="submit"
          style={{
            padding: "12px 18px",
            backgroundColor: "#007bff",
            color: "white",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: "bold",
            fontSize: "16px",
          }}
        >
          Send
        </button>
      </form>

      {/* Suggested Questions */}
      <div>
        <b>Try asking:</b>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "10px",
            marginTop: "6px",
          }}
        >
          {exampleQuestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(q)}
              style={{
                padding: "8px 16px",
                borderRadius: "50px",
                border: "1px solid #ddd",
                backgroundColor: "#f1f1f1",
                cursor: "pointer",
                fontSize: "14px",
                transition: "0.3s",
              }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = "#007bff";
                e.target.style.color = "white";
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = "#f1f1f1";
                e.target.style.color = "black";
              }}
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Typing animation dots */}
      <style>
        {`
          .dot {
            width: 8px;
            height: 8px;
            background-color: #888;
            border-radius: 50%;
            animation: bounce 1.4s infinite;
          }
          .dot:nth-child(2) { animation-delay: 0.2s; }
          .dot:nth-child(3) { animation-delay: 0.4s; }

          @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
          }

          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}
      </style>
    </div>
  );
}

export default App;
