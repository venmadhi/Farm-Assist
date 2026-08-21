import React, { useState, useEffect, useRef } from 'react';
import { Bell, CloudSun, User, LogOut, Settings, MapPin } from 'lucide-react';
import { twinAPI, notificationsAPI } from '../utils/api';

export default function Navbar({ activeTab, setActiveTab, farmerProfile, onLogout }) {
  const [weather, setWeather] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showDrawer, setShowDrawer] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [notifications, setNotifications] = useState([]);
  
  const drawerRef = useRef(null);
  const profileRef = useRef(null);

  const userName = farmerProfile?.full_name || 'Jhanandhan';
  const userDistrict = farmerProfile?.location_district || farmerProfile?.farm?.location_district || 'Idukki';
  const avatarInitial = userName.charAt(0).toUpperCase();

  useEffect(() => {
    // Load weather summary
    twinAPI.getWeather().then(data => {
      setWeather(data);
    }).catch(err => console.error("Error loading weather header:", err));

    // Load unread notification counts
    loadNotifications();
  }, [activeTab]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (drawerRef.current && !drawerRef.current.contains(event.target)) {
        setShowDrawer(false);
      }
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setShowProfileMenu(false);
      }
    };
    
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const loadNotifications = () => {
    notificationsAPI.getNotifications().then(data => {
      setNotifications(data);
      const unreads = data.filter(n => !n.is_read).length;
      setUnreadCount(unreads);
    }).catch(err => console.error("Error loading notifications list:", err));
  };

  const handleMarkAsRead = async (id) => {
    try {
      await notificationsAPI.markAsRead(id);
      loadNotifications();
    } catch (err) {
      console.error(err);
    }
  };

  const handleProfileClick = () => {
    setShowProfileMenu(false);
    if (setActiveTab) setActiveTab('profile');
  };

  const handleSettingsClick = () => {
    setShowProfileMenu(false);
    if (setActiveTab) setActiveTab('settings');
  };

  const handleLogoutClick = () => {
    setShowProfileMenu(false);
    if (onLogout) onLogout();
  };

  const getHeaderTitle = () => {
    switch (activeTab) {
      case 'dashboard': return 'Farmer Digital Twin';
      case 'crop': return 'Crop Suitability Recommendation';
      case 'disease': return 'Leaf Disease Scanner';
      case 'fertilizer': return 'Precision Fertilizer Optimizer';
      case 'market': return 'Market Price Analytics';
      case 'chatbot': return 'Farm Companion AI';
      case 'profile': return 'Profile Configurations';
      case 'settings': return 'Settings';
      default: return 'Dashboard';
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-10">
      <div>
        <h1 className="text-lg font-bold text-slate-900 leading-none">{getHeaderTitle()}</h1>
        <p className="text-xs text-slate-500 mt-1">Welcome back to AgriGenie AI</p>
      </div>

      {/* Navigation utilities */}
      <div className="flex items-center gap-6">
        
        {/* Dynamic Weather & Season Summary */}
        {weather && (
          <div className="hidden md:flex items-center gap-4 text-xs font-semibold text-slate-600 bg-slate-50 border border-slate-100 rounded-lg px-3 py-1.5 shadow-sm">
            <div className="flex items-center gap-1.5 border-r border-slate-200 pr-3">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
              {weather.season ? weather.season.split(' ')[0] : 'Kharif'} Season
            </div>
            <div className="flex items-center gap-1.5 text-slate-500">
              <CloudSun className="w-3.5 h-3.5 text-slate-400" />
              {weather.district || userDistrict}: {weather.temperature}°C • Rain {weather.rainfall}mm
            </div>
          </div>
        )}

        {/* Notifications and Profile */}
        <div className="flex items-center gap-4">
          <div className="relative" ref={drawerRef}>
            <button 
              onClick={() => {
                setShowDrawer(!showDrawer);
                if (!showDrawer) loadNotifications();
              }}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg transition-colors relative flex items-center justify-center"
              aria-label="Alerts & Notifications"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-white"></span>
              )}
            </button>
  
            {/* Collapsible Notifications list drawer */}
            {showDrawer && (
              <div className="absolute right-0 top-full mt-2 w-80 bg-white border border-slate-200 rounded-xl shadow-lg p-4 z-20 space-y-3 animate-fadeIn text-xs">
                <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                  <span className="font-bold text-slate-800">Alerts & Notifications {unreadCount > 0 && `(${unreadCount})`}</span>
                </div>
                <div className="max-h-60 overflow-y-auto space-y-2.5 pr-1 custom-scrollbar">
                  {notifications.length > 0 ? (
                    notifications.map((n) => (
                      <div 
                        key={n.id} 
                        onClick={() => handleMarkAsRead(n.id)}
                        className={`p-2.5 rounded-lg border cursor-pointer hover:bg-slate-50 transition-colors ${
                          n.is_read ? 'bg-white border-slate-100 text-slate-500' : 'bg-green-50/30 border-green-100 text-slate-750 font-medium'
                        }`}
                      >
                        <div className="flex justify-between font-semibold">
                          <span className="capitalize">{n.title}</span>
                          {!n.is_read && <span className="w-1.5 h-1.5 bg-green-500 rounded-full mt-1 shrink-0"></span>}
                        </div>
                        <p className="text-[10px] text-slate-550 mt-1 leading-normal">{n.message}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-center text-slate-400 py-6">No recent alerts found.</p>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="relative" ref={profileRef}>
            <button 
              onClick={() => setShowProfileMenu(!showProfileMenu)}
              className="w-9 h-9 rounded-full border-2 border-slate-200 bg-green-50 text-green-700 font-semibold text-sm flex items-center justify-center overflow-hidden hover:border-green-300 transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1"
              aria-label="User Profile"
            >
              {avatarInitial}
            </button>
            
            {showProfileMenu && (
              <div className="absolute right-0 top-full mt-2 w-56 bg-white border border-slate-200 rounded-xl shadow-lg py-2 z-20 animate-fadeIn text-sm">
                <div className="px-4 py-2 border-b border-slate-100 mb-1">
                  <p className="font-bold text-slate-800 truncate">{userName}</p>
                  <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5 truncate">
                    <MapPin className="w-3 h-3 shrink-0 text-slate-400" />
                    {userDistrict}, Kerala
                  </p>
                </div>
                <button 
                  onClick={handleProfileClick}
                  className="w-full text-left px-4 py-2 text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors flex items-center gap-2"
                >
                  <User className="w-4 h-4" />
                  Profile
                </button>
                <button 
                  onClick={handleSettingsClick}
                  className="w-full text-left px-4 py-2 text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors flex items-center gap-2"
                >
                  <Settings className="w-4 h-4" />
                  Settings
                </button>
                <div className="h-px bg-slate-100 my-1"></div>
                <button 
                  onClick={handleLogoutClick}
                  className="w-full text-left px-4 py-2 text-rose-600 hover:bg-rose-50 transition-colors flex items-center gap-2 font-medium"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            )}
          </div>

        </div>
      </div>
    </header>
  );
}
