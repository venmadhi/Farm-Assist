import React, { useState, useEffect, useRef } from 'react';
import { MessageSquareCode, Trash2, ArrowLeft } from 'lucide-react';
import { chatbotAPI, diseaseAPI, twinAPI } from '../utils/api';
import ChatWelcomeState from '../components/chat/ChatWelcomeState';
import ChatComposer from '../components/chat/ChatComposer';
import ChatContextPanel from '../components/chat/ChatContextPanel';
import MessageBubble from '../components/chat/MessageBubble';

export default function AICompanion() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [feedbackMap, setFeedbackMap] = useState({});
  const [farmerProfile, setFarmerProfile] = useState(null);
  
  // Voice Recording States
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Fetch profile for context panel
    twinAPI.getSummary().then(res => {
      setFarmerProfile(res.farmer_profile);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = false;
      rec.lang = 'ml-IN'; 

      rec.onstart = () => setIsRecording(true);
      rec.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputText((prev) => prev ? `${prev} ${transcript}` : transcript);
      };
      rec.onerror = (e) => {
        console.error('Speech recognition error:', e);
        setIsRecording(false);
      };
      rec.onend = () => setIsRecording(false);

      recognitionRef.current = rec;
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      alert("Voice speech recognition is not supported in this browser. Please use Google Chrome or Microsoft Edge.");
      return;
    }
    if (isRecording) {
      recognitionRef.current.stop();
    } else {
      const currentLanguage = localStorage.getItem('agrigenie_chat_language') || 'en';
      recognitionRef.current.lang = currentLanguage === 'ml' ? 'ml-IN' : 'en-IN';
      recognitionRef.current.start();
    }
  };

  const executeChat = async (textToSend) => {
    if (loading) return;
    
    // Add User Message
    const userMsg = {
      sender: 'user',
      text: textToSend,
      time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
    };
    
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    // Initial placeholder for Bot message while streaming
    setMessages((prev) => [
      ...prev, 
      {
        sender: 'bot',
        text: '',
        time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
        isStreaming: true,
        contextPayload: null
      }
    ]);

    let finalQuery = textToSend;

    try {
      const currentLanguage = localStorage.getItem('agrigenie_chat_language') || 'en';
      await chatbotAPI.streamChat(
        finalQuery, 
        currentLanguage,
        null,
        // onContext
        (contextData) => {
          setMessages(prev => {
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            newMessages[lastIdx] = {
              ...newMessages[lastIdx],
              contextPayload: contextData,
              topic: contextData.intent,
              source: contextData.sources?.[0] || 'AI Companion'
            };
            return newMessages;
          });
        },
        // onToken
        (token) => {
          setMessages(prev => {
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            newMessages[lastIdx] = {
              ...newMessages[lastIdx],
              text: newMessages[lastIdx].text + token
            };
            return newMessages;
          });
        },
        // onError
        (err) => {
          console.error('Chat error:', err);
          setMessages(prev => {
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            newMessages[lastIdx] = {
              ...newMessages[lastIdx],
              isStreaming: false,
              text: newMessages[lastIdx].text || "Sorry, I am facing connectivity issues. Please try again."
            };
            return newMessages;
          });
          setLoading(false);
        },
        // onComplete
        () => {
          setMessages(prev => {
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            newMessages[lastIdx] = {
              ...newMessages[lastIdx],
              isStreaming: false
            };
            return newMessages;
          });
          setLoading(false);
        }
      );
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  const handleSend = (e) => {
    if (e) e.preventDefault();
    if (!inputText.trim()) return;
    const text = inputText;
    setInputText('');
    executeChat(text);
  };

  const handleSuggestionClick = (query) => {
    executeChat(query);
  };

  const handleClearChat = () => {
    setMessages([]);
    setFeedbackMap({});
  };

  const handleFeedback = async (idx, rating) => {
    if (feedbackMap[idx]) return;
    const botMsg = messages[idx];
    const userMsg = messages[idx - 1]?.sender === 'user' ? messages[idx - 1] : null;
    if (!userMsg) return;

    try {
      await chatbotAPI.submitFeedback(
        userMsg.text,
        botMsg.text,
        botMsg.topic || null,
        null,
        rating
      );
      setFeedbackMap((prev) => ({ ...prev, [idx]: rating }));
    } catch (err) {
      console.error('Failed to submit feedback', err);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] bg-slate-50 relative overflow-hidden">
      
      {/* Top Advisory Bar - Mobile Friendly */}
      <div className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-green-50 border border-green-200 flex items-center justify-center shrink-0">
            <MessageSquareCode className="w-4 h-4 text-green-600" />
          </div>
          <div className="hidden sm:block">
            <h3 className="font-bold text-slate-800 text-xs">FarmAssist AI</h3>
            <p className="text-[10px] text-slate-500">Your intelligent farming companion</p>
          </div>
          <div className="sm:hidden flex items-center gap-2">
            <span className="font-bold text-slate-800 text-sm">FarmAssist</span>
            <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-4">
          <button 
            onClick={handleClearChat}
            disabled={messages.length === 0}
            className="p-2 text-slate-400 hover:text-rose-600 rounded-md transition-colors disabled:opacity-50"
            title="Clear Chat"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Main Chat Panel */}
        <div className="flex-1 flex flex-col relative overflow-hidden bg-white/50">
          
          <div className="flex-1 overflow-y-auto px-2 sm:px-6 pt-6 pb-2">
            {messages.length === 0 ? (
              <ChatWelcomeState onSuggestionClick={handleSuggestionClick} />
            ) : (
              messages.map((msg, idx) => (
                <MessageBubble 
                  key={idx} 
                  msg={msg} 
                  idx={idx} 
                  isLast={idx === messages.length - 1}
                  onFeedback={handleFeedback}
                  feedbackState={feedbackMap[idx]}
                />
              ))
            )}
            
            {loading && messages.length > 0 && messages[messages.length - 1].sender === 'user' && (
              <div className="flex gap-3 max-w-[80%] mb-4 mr-auto animate-in fade-in">
                <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center shrink-0 border border-slate-200 mt-1">
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
                </div>
                <div className="px-4 py-3 rounded-2xl text-[13px] bg-white border border-slate-200 text-slate-500 rounded-tl-none">
                  Understanding your question...
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          <ChatComposer 
            inputText={inputText}
            setInputText={setInputText}
            handleSend={handleSend}
            loading={loading}
            isRecording={isRecording}
            toggleRecording={toggleRecording}
          />
        </div>

        {/* Side Context Panel */}
        <ChatContextPanel farmerProfile={farmerProfile} />
      </div>
    </div>
  );
}
