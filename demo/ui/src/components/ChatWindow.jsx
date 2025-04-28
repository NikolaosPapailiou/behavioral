import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import './ChatWindow.css';

const ChatWindow = ({ messages }) => {
  const messagesEndRef = useRef(null);
  const chatWindowRef = useRef(null);

  // Auto-scroll to bottom on new messages only if already near bottom
  useEffect(() => {
    const shouldAutoScroll = () => {
      if (!chatWindowRef.current) return true;
      
      const { scrollTop, scrollHeight, clientHeight } = chatWindowRef.current;
      // If user is within 100px of bottom, auto-scroll
      return scrollHeight - scrollTop - clientHeight < 100;
    };

    if (shouldAutoScroll()) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <div className="chat-window" ref={chatWindowRef}>
      {messages.map((msg, index) => (
        <div 
          key={index} 
          className={`message ${msg.role === 'user' ? 'user-message' : 'assistant-message'}`}
        >
          <div className="message-content">
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          </div>
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatWindow; 