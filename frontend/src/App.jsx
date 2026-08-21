import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';

// Page components
import Dashboard from './pages/Dashboard';
import CropRecommendation from './pages/CropRecommendation';
import DiseaseScanner from './pages/DiseaseScanner';
import FertilizerOptimizer from './pages/FertilizerOptimizer';
import MarketAnalysis from './pages/MarketAnalysis';
import AICompanion from './pages/AICompanion';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import Settings from './pages/Settings';

import { twinAPI } from './utils/api';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('agrigenie_token'));
  const [authView, setAuthView] = useState('login'); // 'login' or 'register'
  const [activeTab, setActiveTab] = useState('dashboard');
  const [farmerProfile, setFarmerProfile] = useState(null);

  useEffect(() => {
    if (isAuthenticated) {
      fetchFarmerProfile();
    }
  }, [isAuthenticated]);

  const fetchFarmerProfile = async () => {
    try {
      const summary = await twinAPI.getSummary();
      setFarmerProfile(summary.farmer_profile);
    } catch (err) {
      console.error('Error fetching farmer profile:', err);
      // If token expired or invalid, trigger logout
      if (err.response && err.response.status === 401) {
        handleLogout();
      }
    }
  };

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('agrigenie_token');
    setIsAuthenticated(false);
    setFarmerProfile(null);
    setActiveTab('dashboard');
  };

  // Render auth screens if not logged in
  if (!isAuthenticated) {
    return authView === 'login' ? (
      <Login 
        onLoginSuccess={handleLoginSuccess} 
        switchToRegister={() => setAuthView('register')} 
      />
    ) : (
      <Register 
        onRegisterSuccess={handleLoginSuccess} 
        switchToLogin={() => setAuthView('login')} 
      />
    );
  }

  // Master workspace page switcher
  const renderPage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'crop':
        return <CropRecommendation />;
      case 'disease':
        return <DiseaseScanner />;
      case 'fertilizer':
        return <FertilizerOptimizer />;
      case 'market':
        return <MarketAnalysis />;
      case 'chatbot':
        return <AICompanion />;
      case 'profile':
        return <Profile />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex bg-slate-50 min-h-screen text-slate-900 font-sans">
      {/* Sidebar - Navigation */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab}
        farmerName={farmerProfile?.full_name}
        locationDistrict={farmerProfile?.location_district || farmerProfile?.farm?.location_district}
        onLogout={handleLogout}
      />

      {/* Main Workspace Frame */}
      <div className="flex-1 flex flex-col min-h-screen overflow-hidden">
        {/* Top Header */}
        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          farmerProfile={farmerProfile}
          onLogout={handleLogout}
        />

        {/* Viewport content */}
        <main className="flex-1 overflow-hidden bg-slate-50/30">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}
