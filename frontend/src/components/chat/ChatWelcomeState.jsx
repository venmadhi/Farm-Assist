import React from 'react';
import { Cloud, Sprout, Bug, FlaskConical, TrendingUp, Landmark, Map, Box } from 'lucide-react';

const SUGGESTIONS = [
  { id: 'weather', icon: Cloud, label: 'Weather', query: 'Will it rain today?' },
  { id: 'crop', icon: Sprout, label: 'Crop Recommendation', query: 'Which crop should I plant now?' },
  { id: 'pest', icon: Bug, label: 'Pest Management', query: 'How to control pests organically?' },
  { id: 'fertilizer', icon: FlaskConical, label: 'Fertilizer', query: 'Fertilizer dosage for coconut' },
  { id: 'market', icon: TrendingUp, label: 'Market Prices', query: 'What is today\'s pepper price?' },
  { id: 'soil', icon: Map, label: 'Soil Management', query: 'How to manage acidic soil?' },
  { id: 'schemes', icon: Landmark, label: 'Government Schemes', query: 'What are the subsidies for PM-KISAN?' },
  { id: 'storage', icon: Box, label: 'Storage', query: 'How to store harvested paddy?' },
];

export default function ChatWelcomeState({ onSuggestionClick }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4 animate-in fade-in zoom-in duration-500">
      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-6 shadow-sm border border-green-200">
        <Sprout className="w-8 h-8 text-green-600" />
      </div>
      
      <h2 className="text-2xl font-bold text-slate-800 mb-2">Hello! I'm FarmAssist.</h2>
      <p className="text-slate-500 max-w-md mb-8 text-sm">
        I can help you with crops, soil, weather, pests, diseases, irrigation, markets, and government schemes.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 w-full max-w-3xl">
        {SUGGESTIONS.map((s) => {
          const Icon = s.icon;
          return (
            <button
              key={s.id}
              onClick={() => onSuggestionClick(s.query)}
              className="flex flex-col items-center gap-2 p-4 rounded-xl border border-slate-200 bg-white hover:bg-green-50 hover:border-green-300 transition-all duration-300 group shadow-sm hover:shadow-md"
            >
              <div className="p-2 bg-slate-50 rounded-lg group-hover:bg-white group-hover:text-green-600 transition-colors">
                <Icon className="w-5 h-5 text-slate-500 group-hover:text-green-600 transition-colors" />
              </div>
              <span className="text-xs font-semibold text-slate-700 group-hover:text-green-700">{s.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
