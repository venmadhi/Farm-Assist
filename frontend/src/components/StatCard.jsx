import React from 'react';

export default function StatCard({ title, value, icon: Icon, description, trend, trendColor }) {
  // Translate trend properties to clean, modern style
  const getTrendStyle = () => {
    if (trendColor === 'green') return 'text-green-600';
    if (trendColor === 'red') return 'text-rose-600';
    return 'text-slate-500';
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col gap-4 shadow-sm h-full">
      <div className="flex items-start gap-4">
        <div className="p-2.5 bg-slate-50 border border-slate-100 rounded-lg text-slate-500 shrink-0">
          <Icon className="w-5 h-5 text-green-600" />
        </div>
        
        <div className="space-y-1 min-w-0 flex-1">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</p>
          <h3 className="text-2xl sm:text-2xl md:text-xl lg:text-2xl font-bold text-slate-900 tracking-tight leading-none pt-0.5 truncate" title={value}>{value}</h3>
          {description && <p className="text-xs text-slate-500 font-medium truncate" title={description}>{description}</p>}
        </div>
      </div>
      
      <div className="mt-auto">
        {trend && (
          <p className={`text-xs font-bold flex items-center gap-1 ${getTrendStyle()}`}>
            {trend.startsWith('+') || trend.includes('Up') || trend.includes('Stable') || trend.includes('Good') || trend.includes('Improved') ? '↑' : '↓'} {trend}
          </p>
        )}
      </div>
    </div>
  );
}
