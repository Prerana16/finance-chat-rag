import React, { useState } from "react";
import axios from "axios";

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Hello! I’m FinBot, your personal finance assistant. You can ask me about your password reset, balances, transactions, fund transfers, or spending insights. How can I help you today?",
    },
  ]);

  const exampleQuestions = [
    "How to check my account balance?",
    "How can I transfer funds?",
    "What are my recent transactions?",
    "How to contact customer support?",
  ];

  const handleSend = async (q = null) => {
    const userQuestion = q || question;
    if (!userQuestion.trim()) return;

    setMessages((prev) => [...prev, { sender: "user", text: userQuestion }]);

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
        { sender: "bot", text: "Error connecting to backend." },
      ]);
    }

    setQuestion("");
  };

  return (
    <div
      style={{
        maxWidth: "600px",
        margin: "auto",
        padding: "20px",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <h2
        style={{
          textAlign: "center",
          fontWeight: "bold",
          fontSize: "24px",
        }}
      >
        FinBot
      </h2>

      {/* Chat window */}
      <div
        style={{
          border: "1px solid #ccc",
          borderRadius: "8px",
          padding: "10px",
          height: "400px",
          overflowY: "auto",
          marginBottom: "10px",
          backgroundColor: "#fafafa",
        }}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              textAlign: msg.sender === "user" ? "right" : "left",
              margin: "5px 0",
              wordWrap: "break-word",
            }}
          >
            <b>{msg.sender === "user" ? "You" : "AI"}:</b> {msg.text}
          </div>
        ))}
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
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          style={{
            flex: 1,
            padding: "10px",
            fontSize: "16px",
            borderRadius: "5px",
            border: "1px solid #ccc",
          }}
          placeholder="Type your question..."
        />
        <button
          type="submit"
          style={{
            padding: "10px 16px",
            backgroundColor: "#007bff",
            color: "white",
            border: "none",
            borderRadius: "5px",
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
            marginTop: "5px",
          }}
        >
          {exampleQuestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(q)}
              style={{
                padding: "8px 12px",
                backgroundColor: "#e0e0e0",
                border: "none",
                borderRadius: "5px",
                cursor: "pointer",
                fontSize: "14px",
              }}
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
