import React from 'react';
import { ThumbsUp, ThumbsDown, User, Bot, AlertTriangle, CloudRain, Sun, Info } from 'lucide-react';
import InteractiveCards from './InteractiveCards';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function MessageBubble({ msg, idx, isLast, onFeedback, feedbackState }) {
  const isUser = msg.sender === 'user';
  
  return (
    <div className={`flex gap-3 max-w-[85%] sm:max-w-[80%] mb-4 ${isUser ? 'ml-auto' : 'mr-auto'}`}>
      {/* Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center shrink-0 border border-green-200 mt-1">
          <Bot className="w-4 h-4 text-green-700" />
        </div>
      )}

      <div className={`flex flex-col w-full ${isUser ? 'items-end' : 'items-start'}`}>
        {/* The Bubble */}
        <div 
          className={`px-4 py-3 rounded-2xl text-[13px] leading-relaxed shadow-sm w-full overflow-hidden
            ${isUser 
              ? 'bg-green-600 text-white rounded-tr-none' 
              : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none'
            }`}
        >
          {isUser ? (
            <div className="whitespace-pre-wrap">{msg.text}</div>
          ) : (
            <div className="markdown-body prose prose-sm max-w-none prose-p:my-1 prose-headings:my-2 prose-ul:my-1 prose-li:my-0.5 prose-table:my-2">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.text}
              </ReactMarkdown>
            </div>
          )}

          {/* Render Context/Interactive Cards if attached */}
          {!isUser && msg.contextPayload && (
            <InteractiveCards contextPayload={msg.contextPayload} />
          )}

          {/* Loading dot indicator for streaming */}
          {msg.isStreaming && isLast && (
             <span className="inline-block w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse ml-1 align-middle"></span>
          )}
        </div>

        {/* Metadata & Actions */}
        <div className={`flex items-center gap-3 mt-1.5 px-1 w-full ${isUser ? 'justify-end' : 'justify-between'}`}>
          <div className="flex items-center gap-1.5 text-[9px] text-slate-400 font-bold select-none">
            <span>{msg.time}</span>
            {!isUser && msg.source && (
              <>
                <span>•</span>
                <span className="text-green-700 uppercase flex items-center gap-1">
                  <Info className="w-2.5 h-2.5" />
                  {msg.source}
                </span>
                {msg.topic && (
                  <>
                    <span>•</span>
                    <span className="text-slate-500 capitalize">{msg.topic.replace(/_/g, ' ')}</span>
                  </>
                )}
              </>
            )}
          </div>
          
          {/* Feedback Buttons */}
          {!isUser && idx > 0 && !msg.isStreaming && (
            <div className="flex items-center gap-1">
              <button 
                onClick={() => onFeedback(idx, 1)}
                className={`p-1 rounded transition-colors ${feedbackState === 1 ? 'text-green-600 bg-green-50' : 'text-slate-400 hover:text-green-600 hover:bg-slate-50'}`}
                disabled={!!feedbackState}
                title="Helpful"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
              </button>
              <button 
                onClick={() => onFeedback(idx, -1)}
                className={`p-1 rounded transition-colors ${feedbackState === -1 ? 'text-rose-600 bg-rose-50' : 'text-slate-400 hover:text-rose-600 hover:bg-slate-50'}`}
                disabled={!!feedbackState}
                title="Not helpful"
              >
                <ThumbsDown className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
