import React from 'react';
import { HelpCircle, ChevronRight } from 'lucide-react';

export default function SHAPChart({ data }) {
  if (!data) return null;

  const features = [
    { 
      key: 'nitrogen', 
      label: 'Nitrogen (N) Impact', 
      value: data.nitrogen, 
      color: 'bg-green-600',
      description: 'Influences vegetative foliage growth and leaf greenness.'
    },
    { 
      key: 'phosphorus', 
      label: 'Phosphorus (P) Impact', 
      value: data.phosphorus, 
      color: 'bg-blue-600', 
      description: 'Supports root development, seedling vigor, and flowering.'
    },
    { 
      key: 'potassium', 
      label: 'Potassium (K) Impact', 
      value: data.potassium, 
      color: 'bg-purple-600', 
      description: 'Regulates water intake, crop quality, and pathogen resistance.'
    },
    { 
      key: 'weather', 
      label: 'Climate & Water Suitability', 
      value: data.weather, 
      color: 'bg-amber-600', 
      description: 'Integrates temperature, rainfall, and moisture parameters.'
    },
  ];

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-bold text-sm text-slate-800">Advanced AI Diagnostics</h4>
          <p className="text-[11px] text-slate-500">Relative Shapley value weight distribution for this decision model</p>
        </div>
        <div className="text-[10px] font-bold px-2 py-0.5 bg-green-50 border border-green-200 text-green-700 rounded-full">
          SHAP Engine Active
        </div>
      </div>

      <div className="space-y-3.5">
        {features.map((item) => {
          const val = item.value;
          const absVal = Math.abs(val);
          // Scale it for visual representation (normalized against sum of absolute values)
          const totalAbs = features.reduce((acc, f) => acc + Math.abs(f.value), 0) || 100;
          const percentage = ((absVal / totalAbs) * 100).toFixed(0);

          return (
            <div key={item.key} className="space-y-1 group relative">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="text-slate-600 flex items-center gap-1">
                  {item.label}
                  <div className="relative cursor-help text-slate-400 hover:text-slate-600">
                    <HelpCircle className="w-3.5 h-3.5" />
                    <div className="absolute left-0 bottom-full mb-1.5 hidden group-hover:block w-48 p-2 bg-slate-900 text-[10px] text-white rounded shadow-xl z-20">
                      {item.description}
                    </div>
                  </div>
                </span>
                <span className={val >= 0 ? 'text-green-700' : 'text-amber-700'}>
                  {val >= 0 ? '+' : ''}{val}%
                </span>
              </div>
              
              {/* Custom SVG/HTML Bar */}
              <div className="w-full h-2.5 bg-slate-200/70 rounded-full overflow-hidden border border-slate-200 relative">
                <div 
                  className={`h-full ${item.color} rounded-full transition-all duration-1000 ease-out`}
                  style={{ width: `${percentage}%` }}
                ></div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Decision Summary Info */}
      <div className="border-t border-slate-200 pt-3 text-[11px] text-slate-500 flex items-start gap-1.5 bg-white p-2.5 rounded-lg border border-slate-200/60">
        <ChevronRight className="w-3.5 h-3.5 text-green-600 shrink-0 mt-0.5" />
        <p>
          <strong>Interpretation:</strong> Factors with higher percentages represent dominant decision drivers. A high <strong>Potassium (K)</strong> contribution signifies that your crop choice was heavily determined by K concentration levels in your soil.
        </p>
      </div>
    </div>
  );
}
