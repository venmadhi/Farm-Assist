import React, { useRef, useEffect } from 'react';
import { Send, Mic, MicOff, X } from 'lucide-react';

export default function ChatComposer({
  inputText,
  setInputText,
  handleSend,
  loading,
  isRecording,
  toggleRecording
}) {
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [inputText]);

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  };

  return (
    <div className="border-t border-slate-150 pt-3 flex flex-col gap-2 relative bg-white">
      <form onSubmit={handleSend} className="flex gap-2 sm:gap-3 items-end px-2 sm:px-4 pb-4">

        {/* Voice Input Button */}
        <button
          type="button"
          onClick={toggleRecording}
          disabled={loading}
          className={`p-2.5 sm:p-3 rounded-lg border transition-all duration-300 relative flex items-center justify-center shrink-0 h-10 sm:h-11 ${
            isRecording 
              ? 'bg-rose-50 text-rose-600 border-rose-200' 
              : 'bg-slate-50 border-slate-200 text-slate-500 hover:text-green-600 hover:border-slate-300'
          }`}
        >
          {isRecording ? (
            <>
              <MicOff className="w-4 h-4 animate-pulse" />
              <span className="absolute bottom-full mb-2 bg-rose-50 text-[9px] text-rose-700 font-bold px-2 py-0.5 rounded border border-rose-200 whitespace-nowrap hidden sm:block">Listening...</span>
            </>
          ) : (
            <Mic className="w-4 h-4" />
          )}
        </button>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={isRecording ? "Listening..." : "Ask your farm companion advisor..."}
          disabled={isRecording || loading}
          rows={1}
          className="flex-1 resize-none bg-slate-50 border border-slate-200 rounded-lg px-3 sm:px-4 py-2.5 sm:py-3 text-[13px] text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600 disabled:opacity-50 min-h-[40px] sm:min-h-[44px] max-h-[120px] transition-all"
        />

        {/* Send Button */}
        <button
          type="submit"
          disabled={!inputText.trim() || loading}
          className={`p-2.5 sm:p-3 rounded-lg font-bold transition-all flex items-center justify-center shrink-0 h-10 sm:h-11 ${
            inputText.trim() && !loading
              ? 'bg-green-600 hover:bg-green-700 text-white shadow-sm' 
              : 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed'
          }`}
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
