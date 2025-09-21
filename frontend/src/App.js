import React, { useState } from "react";
import axios from "axios";

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([{
      sender: "bot",
      text: "Hello! I’m FinBot, your personal finance assistant. You can ask me about your password reset, balances, transactions, fund transfers, or spending insights. How can I help you today?",
    },]);
  
  const exampleQuestions = [
    "How to check my account balance?",
    "How can I transfer funds?",
    "What are my recent transactions?",
    "How to contact customer support?",
  ];
  const handleSend = async () => {
    if (!question.trim()) return;

    // Add user message to chat
    setMessages((prev) => [...prev, { sender: "user", text: question }]);

    try {
      const res = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/chat`,
        { question }
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
    <div style={{ maxWidth: "50%", margin: "auto", padding: "20px" }}>
      <h2 style={{ 
        textAlign: "center",
        fontWeight: "bold",
        fontSize: "24px",
      }}>
        FinBot
      </h2>
      <div
        style={{
          border: "1px solid #ccc",
          borderRadius: "8px",
          padding: "10px",
          height: "400px",
          overflowY: "auto",
          marginBottom: "10px",
        }}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              textAlign: msg.sender === "user" ? "right" : "left",
              margin: "5px 0",
            }}
          >
            <b>{msg.sender === "user" ? "You" : "AI"}:</b> {msg.text}
          </div>
        ))}
      </div>

      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        style={{ width: "100%", padding: "8px" }}
        placeholder="Type your question..."
      />
      <div style={{ textAlign: "center", marginTop: "10px" }}>
      <button
        onClick={handleSend}
        style={{ 
          width: "18%",
          padding: "8px",
          marginLeft: "2%",
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
      </div>
      <div style={{ marginTop: "15px" }}>
        <b>Try asking:</b>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", marginTop: "5px" }}>
          {exampleQuestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(q)}
              style={{
                padding: "6px 10px",
                backgroundColor: "#e0e0e0",
                border: "none",
                borderRadius: "5px",
                cursor: "pointer",
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
