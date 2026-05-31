import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const FloatingChat = ({ initialText, emotion, topic }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatStarted, setChatStarted] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const startChat = async () => {
    setLoading(true);
    try {
      const res = await axios.post('http://localhost:8000/api/chat/start', {
        text: initialText || "I need support"
      });
      
      setSessionId(res.data.session_id);
      setMessages([
        { 
          id: Date.now(), 
          role: 'bot', 
          text: res.data.first_message,
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
      setChatStarted(true);
    } catch (error) {
      console.error('Failed to start chat:', error);
      setMessages([{ 
        id: Date.now(), 
        role: 'bot', 
        text: "Sorry, I'm having trouble connecting. Please try again. 💙",
        timestamp: new Date().toLocaleTimeString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !sessionId) return;
    
    const userMessage = input.trim();
    setMessages(prev => [...prev, { 
      id: Date.now(), 
      role: 'user', 
      text: userMessage,
      timestamp: new Date().toLocaleTimeString()
    }]);
    setInput('');
    setLoading(true);
    
    try {
      const res = await axios.post('http://localhost:8000/api/chat/message', {
        session_id: sessionId,
        message: userMessage
      });
      
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        role: 'bot', 
        text: res.data.response,
        timestamp: new Date().toLocaleTimeString()
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        role: 'bot', 
        text: "I'm having trouble responding. Please try again. 💙",
        timestamp: new Date().toLocaleTimeString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (timestamp) => {
    return timestamp || new Date().toLocaleTimeString();
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg hover:shadow-xl transform hover:scale-110 transition-all duration-300 flex items-center justify-center group"
      >
        {isOpen ? (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        )}
        
        {/* Notification badge */}
        {!isOpen && (
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full animate-pulse"></span>
        )}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 w-[380px] h-[550px] bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col animate-slideUp">
          
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-pink-500 p-4 text-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                  <span className="text-2xl animate-pulse">🤖</span>
                </div>
                <div>
                  <h3 className="font-bold text-lg">AI Support Assistant</h3>
                  <p className="text-xs opacity-90">Here to listen and help 💙</p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-white/80 hover:text-white transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Context info if available */}
            {(emotion || topic) && (
              <div className="mt-2 flex gap-2 text-xs">
                {emotion && (
                  <span className="px-2 py-0.5 bg-white/20 rounded-full">
                    😞 {emotion}
                  </span>
                )}
                {topic && (
                  <span className="px-2 py-0.5 bg-white/20 rounded-full">
                    🎯 {topic}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
            {!chatStarted ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mb-4">
                  <span className="text-4xl animate-bounce">💬</span>
                </div>
                <p className="text-gray-600 text-sm mb-2">Want to talk about what happened?</p>
                <p className="text-gray-400 text-xs">This will start a private conversation</p>
                <button
                  onClick={startChat}
                  disabled={loading}
                  className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-full text-sm hover:bg-purple-700 disabled:opacity-50 transition-colors"
                >
                  {loading ? 'Starting...' : '💬 Start Chat'}
                </button>
              </div>
            ) : (
              <>
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] p-3 rounded-2xl ${
                        msg.role === 'user'
                          ? 'bg-purple-600 text-white rounded-br-none'
                          : 'bg-white text-gray-800 rounded-bl-none shadow-sm'
                      }`}
                    >
                      <p
                        className="text-sm whitespace-pre-line"
                        dangerouslySetInnerHTML={{
                          __html: msg.text
                            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                            .replace(/\*(.*?)\*/g, '<em>$1</em>')
                            .replace(/\n/g, '<br/>')
                        }}
                      />
                      <span className={`text-[10px] mt-1 block ${
                        msg.role === 'user' ? 'text-purple-200' : 'text-gray-400'
                      }`}>
                        {formatTime(msg.timestamp)}
                      </span>
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-white p-3 rounded-2xl rounded-bl-none shadow-sm">
                      <div className="flex gap-1">
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></span>
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input Area */}
          {chatStarted && (
            <div className="p-4 bg-white border-t">
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:border-purple-500 text-sm"
                />
                <button
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                  className="w-10 h-10 bg-purple-600 text-white rounded-full flex items-center justify-center hover:bg-purple-700 disabled:opacity-50 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
              <p className="text-xs text-gray-400 text-center mt-2">
                💙 Your conversation is private and confidential
              </p>
            </div>
          )}
        </div>
      )}

      <style jsx>{`
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-slideUp {
          animation: slideUp 0.3s ease-out;
        }
      `}</style>
    </>
  );
};

export default FloatingChat;