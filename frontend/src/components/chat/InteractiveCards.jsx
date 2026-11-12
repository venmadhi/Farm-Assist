import React from 'react';
import { CloudRain, TrendingUp, Sprout, ShieldCheck } from 'lucide-react';

export default function InteractiveCards({ contextPayload }) {
  if (!contextPayload || !contextPayload.intent) return null;
  const { intent, realtime_context, crop_entity } = contextPayload;

  // We only render a card if there is actual realtime context attached
  if (!realtime_context || realtime_context.length < 5) return null;

  if (intent === 'WEATHER' || intent === 'HEATWAVE') {
    return (
      <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-3">
        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
          <CloudRain className="w-4 h-4 text-blue-600" />
        </div>
        <div>
          <h4 className="text-xs font-bold text-blue-900 uppercase">Live Weather Data</h4>
          <p className="text-[11px] text-blue-800 mt-1 whitespace-pre-wrap leading-relaxed">{realtime_context}</p>
          <div className="mt-2 flex gap-2">
            <button className="text-[10px] px-2 py-1 bg-white border border-blue-200 text-blue-700 rounded hover:bg-blue-100 transition-colors">Should I irrigate?</button>
            <button className="text-[10px] px-2 py-1 bg-white border border-blue-200 text-blue-700 rounded hover:bg-blue-100 transition-colors">Pest risk</button>
          </div>
        </div>
      </div>
    );
  }

  if (intent.includes('MARKET') || intent === 'MSP') {
    return (
      <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
        <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
          <TrendingUp className="w-4 h-4 text-amber-600" />
        </div>
        <div>
          <h4 className="text-xs font-bold text-amber-900 uppercase">{crop_entity || 'Market'} Prices</h4>
          <p className="text-[11px] text-amber-800 mt-1 whitespace-pre-wrap leading-relaxed">{realtime_context}</p>
          <div className="mt-2 flex gap-2">
            <button className="text-[10px] px-2 py-1 bg-white border border-amber-200 text-amber-700 rounded hover:bg-amber-100 transition-colors">View 7-day trend</button>
            <button className="text-[10px] px-2 py-1 bg-white border border-amber-200 text-amber-700 rounded hover:bg-amber-100 transition-colors">Storage advice</button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
