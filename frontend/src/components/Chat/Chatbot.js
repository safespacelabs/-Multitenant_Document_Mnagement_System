import React, { useState, useEffect, useRef } from 'react';
import { chatAPI } from '../../services/api';
import { Send, Bot, User, Loader } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadChatHistory();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatHistory = async () => {
    try {
      const response = await chatAPI.getHistory();
      const history = response.data.slice(0, 10).reverse();
      const formattedHistory = history.flatMap(chat => [
        { type: 'user', content: chat.question, timestamp: chat.created_at },
        { type: 'bot', content: chat.answer, timestamp: chat.created_at }
      ]);
      setMessages(formattedHistory);
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    const userMessage = { type: 'user', content: inputMessage, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await chatAPI.sendMessage(inputMessage);
      const botMessage = {
        type: 'bot',
        content: response.data.answer,
        timestamp: response.data.created_at
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        type: 'bot',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow h-[calc(100vh-12rem)] flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-2xl font-bold flex items-center">
          <Bot className="h-6 w-6 mr-2 text-blue-500" />
          Document Assistant
        </h2>
        <p className="text-gray-600 text-sm">
          Ask questions about your documents and get intelligent answers
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <Bot className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>Start a conversation by asking about your documents!</p>
            <p className="text-sm mt-2">
              Try: "What documents do I have?" or "Summarize my recent uploads"
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.type === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <div className="flex items-start space-x-2">
                {message.type === 'bot' && (
                  <Bot className="h-4 w-4 mt-1 text-blue-500" />
                )}
                {message.type === 'user' && (
                  <User className="h-4 w-4 mt-1 text-white" />
                )}
                <div className="flex-1">
                  {message.type === 'bot' ? (
                    <ReactMarkdown className="prose prose-sm max-w-none">
                      {message.content}
                    </ReactMarkdown>
                  ) : (
                    <p>{message.content}</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-800 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <Bot className="h-4 w-4 text-blue-500" />
                <Loader className="h-4 w-4 animate-spin text-blue-500" />
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={sendMessage} className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask about your documents..."
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !inputMessage.trim()}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
    </div>
  );
}

export default Chatbot;