import React from 'react';
import { 
  User, 
  Sprout, 
  Bug, 
  FlaskConical, 
  TrendingUp, 
  MessageSquareCode, 
  LogOut,
  Sparkles,
  Settings,
  Layers
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, farmerName, locationDistrict, onLogout }) {
  const menuItems = [
    { id: 'dashboard', label: 'Farmer Digital Twin', icon: Layers },
    { id: 'crop', label: 'Crop Intelligence', icon: Sprout },
    { id: 'disease', label: 'Disease Leaf Scanner', icon: Bug },
    { id: 'fertilizer', label: 'Smart Fertilizer', icon: FlaskConical },
    { id: 'market', label: 'Market Price Forecast', icon: TrendingUp },
    { id: 'chatbot', label: 'AI Farm Consultant', icon: MessageSquareCode },
    { id: 'profile', label: 'Profile Configurations', icon: Settings },
  ];

  return (
    <aside className="w-72 bg-white border-r border-slate-200 flex flex-col h-screen sticky top-0 shadow-sm">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-100 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-green-600 flex items-center justify-center">
          <Sprout className="w-4 h-4 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-base text-slate-900 tracking-tight">
            FarmAssist
          </h1>
          <p className="text-[10px] text-slate-505 font-medium tracking-wide">
            Kerala Farming Platform
          </p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-6 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left text-sm font-medium transition-colors group ${
                isActive 
                  ? 'bg-green-50 text-green-700 font-semibold' 
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <div className="flex-shrink-0 w-5 flex justify-center items-center">
                <Icon className={`w-4 h-4 ${
                  isActive ? 'text-green-600' : 'text-slate-400 group-hover:text-slate-500'
                }`} />
              </div>
              <span className="truncate">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* User Profile Block */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50 flex flex-col gap-3">
        <div className="flex items-center gap-3 px-2">
          <div className="w-9 h-9 rounded-full bg-green-100 flex items-center justify-center">
            <span className="font-semibold text-sm text-green-700">
              {(farmerName || 'Jhanandhan').charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="font-semibold text-slate-800 text-xs truncate">
              {farmerName || 'Jhanandhan'}
            </h2>
            <p className="text-[10px] text-slate-500 truncate">
              {locationDistrict ? `${locationDistrict}, Kerala` : 'Idukki, Kerala'}
            </p>
          </div>
        </div>
        <button
          onClick={onLogout}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-xs font-semibold text-slate-600 hover:bg-rose-50 hover:text-rose-600 transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          Log Out
        </button>
      </div>
    </aside>
  );
}
