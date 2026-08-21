import React, { useState, useEffect, useRef } from 'react';
import { 
  MessageSquareCode, 
  Send, 
  Mic, 
  MicOff, 
  Volume2, 
  Sparkles, 
  Key,
  Info,
  HelpCircle,
  Globe
} from 'lucide-react';
import { chatbotAPI } from '../utils/api';

export default function AICompanion() {
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: "Namaskaram! I am FarmAssist, your agricultural assistant. You can ask me questions about farming in Malayalam or English.\n\nഎനിക്ക് നിങ്ങളെ എങ്ങനെ സഹായിക്കാൻ കഴിയും? (How can I help you today?)",
      time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
      source: 'System greeting',
      topic: 'Introduction'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [geminiKey, setGeminiKey] = useState(localStorage.getItem('agrigenie_gemini_key') || '');
  const [showKeyInput, setShowKeyInput] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('en'); // 'en' or 'ml'
  
  // Voice Recording States
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    // Configure Web Speech API recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = false;
      rec.lang = 'ml-IN'; 

      rec.onstart = () => {
        setIsRecording(true);
      };

      rec.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputText((prev) => prev ? `${prev} ${transcript}` : transcript);
      };

      rec.onerror = (e) => {
        console.error('Speech recognition error:', e);
        setIsRecording(false);
      };

      rec.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = rec;
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleKeySave = (e) => {
    e.preventDefault();
    localStorage.setItem('agrigenie_gemini_key', geminiKey);
    setShowKeyInput(false);
  };

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      alert("Voice speech recognition is not supported in this browser. Please use Google Chrome or Microsoft Edge.");
      return;
    }

    if (isRecording) {
      recognitionRef.current.stop();
    } else {
      // Toggle language based on toggle state
      recognitionRef.current.lang = selectedLanguage === 'ml' ? 'ml-IN' : 'en-IN';
      recognitionRef.current.start();
    }
  };

  const executeChat = async (textToSend) => {
    // Append User Message
    const userMsg = {
      sender: 'user',
      text: textToSend,
      time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const response = await chatbotAPI.chat(textToSend, geminiKey || null);
      
      const botMsg = {
        sender: 'bot',
        text: response.response,
        time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
        source: response.source,
        topic: response.matched_topic
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error(err);
      const errorMsg = {
        sender: 'bot',
        text: "Sorry, I am facing connectivity issues. Ensure your backend FastAPI application is running.",
        time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
        source: 'Error handler',
        topic: 'System Connection'
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    const text = inputText;
    setInputText('');
    await executeChat(text);
  };

  const handleSuggestedQuestion = async (question) => {
    await executeChat(question);
  };

  const suggestedQuestions = [
    { label: 'Jeevamrutham preparation?', val: 'How to prepare Jeevamrutham?' },
    { label: 'Coconut beetle control?', val: 'How to control Rhinoceros Beetle in coconut palms?' },
    { label: 'Pepper Quick Wilt preventive?', val: 'How to prevent Quick Wilt in Black Pepper?' },
  ];

  return (
    <div className="p-8 h-[calc(100vh-64px)] flex flex-col gap-6 bg-slate-50/50">
      
      {/* Top Advisory Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-green-50 border border-green-200 flex items-center justify-center">
            <MessageSquareCode className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <h3 className="font-bold text-slate-800 text-xs">Conversational Farm Assistant</h3>
            <p className="text-xs text-slate-500">Ask regional farming guidelines in Malayalam or English</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Language Toggle switch */}
          <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200">
            <button
              onClick={() => setSelectedLanguage('en')}
              className={`px-3 py-1 rounded-md text-[10px] font-bold transition-all ${
                selectedLanguage === 'en' ? 'bg-white text-slate-800 shadow-xs' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              English
            </button>
            <button
              onClick={() => setSelectedLanguage('ml')}
              className={`px-3 py-1 rounded-md text-[10px] font-bold transition-all ${
                selectedLanguage === 'ml' ? 'bg-white text-slate-800 shadow-xs' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              മലയാളം
            </button>
          </div>

          <button
            onClick={() => setShowKeyInput(!showKeyInput)}
            className="px-3.5 py-1.5 border border-slate-250 bg-white hover:bg-slate-50 text-[10px] font-bold text-slate-700 rounded-lg shadow-xs transition-colors flex items-center gap-1.5"
          >
            <Key className="w-3.5 h-3.5 text-green-600" />
            {geminiKey ? 'Gemini Active' : 'API Key Config'}
          </button>
        </div>
      </div>

      {/* API Key Modal Overlay */}
      {showKeyInput && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-md max-w-md mx-auto space-y-3 z-20 absolute top-28 left-0 right-0">
          <div className="space-y-1">
            <h4 className="font-bold text-xs text-slate-800">Configure LLM Credentials</h4>
            <p className="text-xs text-slate-500">Add your Gemini API Key to enable general LLM assistance. Defaults to the offline guideline dictionary if left blank.</p>
          </div>
          <form onSubmit={handleKeySave} className="flex gap-2">
            <input 
              type="password"
              placeholder="AIzaSy..."
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              className="flex-1 bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
            />
            <button
              type="submit"
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors"
            >
              Save
            </button>
          </form>
        </div>
      )}

      {/* Main Chat Panel */}
      <div className="flex-1 bg-white border border-slate-200 rounded-xl p-6 flex flex-col justify-between overflow-hidden relative shadow-sm">
        
        {/* Messages Body */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4">
          {messages.map((msg, idx) => (
            <div 
              key={idx} 
              className={`flex flex-col max-w-[75%] ${msg.sender === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'}`}
            >
              {/* Message bubble */}
              <div className={`p-3.5 rounded-xl text-xs whitespace-pre-wrap leading-relaxed shadow-2xs ${
                msg.sender === 'user' 
                  ? 'bg-green-600 text-white font-medium rounded-tr-none' 
                  : 'bg-slate-55 border border-slate-200 text-slate-800 rounded-tl-none'
              }`}>
                {msg.text}
              </div>

              {/* Message metadata / logs */}
              <div className="flex items-center gap-1.5 mt-1 text-[9px] text-slate-400 font-bold px-1 select-none">
                <span>{msg.time}</span>
                {msg.sender === 'bot' && (
                  <>
                    <span>•</span>
                    <span className="text-green-700 uppercase">{msg.source}</span>
                    <span>•</span>
                    <span className="text-slate-500 capitalize">Topic: {msg.topic}</span>
                  </>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex flex-col items-start max-w-[75%]">
              <div className="p-3 bg-slate-55 border border-slate-200 text-slate-500 rounded-xl rounded-tl-none flex items-center gap-1.5 text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-bounce"></span>
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-bounce [animation-delay:0.2s]"></span>
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-bounce [animation-delay:0.4s]"></span>
                <span>Farming advisor is formulating response...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Actions panel */}
        {messages.length === 1 && (
          <div className="mb-4 space-y-2 border-t border-slate-100 pt-4">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Suggested Questions:</p>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSuggestedQuestion(q.val)}
                  className="px-3 py-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-medium rounded-lg transition-colors shadow-2xs"
                >
                  {q.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Bar */}
        <form onSubmit={handleSend} className="border-t border-slate-150 pt-4 flex gap-3 items-center">
          
          {/* Voice Input Button */}
          <button
            type="button"
            onClick={toggleRecording}
            className={`p-3 rounded-lg border transition-all duration-300 relative flex items-center justify-center shrink-0 ${
              isRecording 
                ? 'bg-rose-50 text-rose-600 border-rose-200' 
                : 'bg-slate-50 border-slate-200 text-slate-500 hover:text-green-600 hover:border-slate-300'
            }`}
          >
            {isRecording ? (
              <>
                <MicOff className="w-4 h-4 animate-pulse" />
                <span className="absolute bottom-full mb-2 bg-rose-50 text-[9px] text-rose-700 font-bold px-2 py-0.5 rounded border border-rose-200 whitespace-nowrap">Listening...</span>
              </>
            ) : (
              <>
                <Mic className="w-4 h-4" />
              </>
            )}
          </button>

          <input 
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={isRecording ? "Listening to your voice..." : "Ask your farm companion advisor..."}
            disabled={isRecording}
            className="flex-1 bg-white border border-slate-200 rounded-lg px-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600 disabled:opacity-50"
          />

          <button
            type="submit"
            disabled={!inputText.trim()}
            className={`p-2.5 rounded-lg font-bold transition-all flex items-center justify-center shrink-0 ${
              inputText.trim() 
                ? 'bg-green-600 hover:bg-green-700 text-white shadow-xs' 
                : 'bg-slate-50 text-slate-400 border border-slate-200 cursor-not-allowed'
            }`}
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
