import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Globe, Moon, Sun, Bell, Shield, Smartphone, Save, CheckCircle2 } from 'lucide-react';
import { twinAPI } from '../utils/api';

export default function Settings() {
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState('');
  const [farmerProfile, setFarmerProfile] = useState(null);

  // App-level settings (stored in localStorage, no backend required)
  const [appSettings, setAppSettings] = useState({
    language: localStorage.getItem('fa_language') || 'english',
    notifications: localStorage.getItem('fa_notifications') !== 'false',
    darkMode: localStorage.getItem('fa_darkMode') === 'true',
    units: localStorage.getItem('fa_units') || 'metric',
  });

  useEffect(() => {
    twinAPI.getSummary()
      .then(data => setFarmerProfile(data?.farmer_profile))
      .catch(() => {});
  }, []);

  const handleToggle = (key) => {
    const updated = { ...appSettings, [key]: !appSettings[key] };
    setAppSettings(updated);
    localStorage.setItem(`fa_${key}`, String(updated[key]));
  };

  const handleSelect = (key, value) => {
    const updated = { ...appSettings, [key]: value };
    setAppSettings(updated);
    localStorage.setItem(`fa_${key}`, value);
  };

  const handleSave = () => {
    setSaving(true);
    setTimeout(() => {
      setSaving(false);
      setSuccess('Settings saved successfully.');
      setTimeout(() => setSuccess(''), 3000);
    }, 600);
  };

  return (
    <div className="p-8 space-y-6 overflow-y-auto h-[calc(100vh-64px)] bg-slate-50/50">
      <div className="max-w-3xl mx-auto space-y-6">

        {/* Header */}
        <div>
          <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <SettingsIcon className="w-4 h-4 text-green-600" />
            Application Settings
          </h2>
          <p className="text-xs text-slate-500 mt-1">Configure your FarmAssist experience preferences.</p>
        </div>

        {/* Account Info Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-3">Account Information</h3>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="font-bold text-slate-400 uppercase tracking-wider text-[9px] block mb-1">Farmer Name</span>
              <p className="font-semibold text-slate-800">{farmerProfile?.full_name || 'Jhanandhan'}</p>
            </div>
            <div>
              <span className="font-bold text-slate-400 uppercase tracking-wider text-[9px] block mb-1">Phone Number</span>
              <p className="font-semibold text-slate-800">{farmerProfile?.phone_number || '—'}</p>
            </div>
            <div>
              <span className="font-bold text-slate-400 uppercase tracking-wider text-[9px] block mb-1">Location</span>
              <p className="font-semibold text-slate-800">{farmerProfile?.location_district || 'Idukki'}, Kerala</p>
            </div>
            <div>
              <span className="font-bold text-slate-400 uppercase tracking-wider text-[9px] block mb-1">Member Since</span>
              <p className="font-semibold text-slate-800">
                {farmerProfile?.created_at
                  ? new Date(farmerProfile.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long' })
                  : '—'}
              </p>
            </div>
          </div>
        </div>

        {/* Display & Language */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center gap-2">
            <Globe className="w-3.5 h-3.5 text-slate-400" />
            Language & Display
          </h3>

          <div className="space-y-4 text-xs">
            {/* Interface Language */}
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-slate-700">Interface Language</p>
                <p className="text-slate-500 mt-0.5">Select the language for the FarmAssist dashboard</p>
              </div>
              <select
                value={appSettings.language}
                onChange={(e) => handleSelect('language', e.target.value)}
                className="bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
              >
                <option value="english">English</option>
                <option value="malayalam">Malayalam</option>
                <option value="tamil">Tamil</option>
                <option value="hindi">Hindi</option>
              </select>
            </div>

            {/* Measurement Units */}
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-slate-700">Measurement Units</p>
                <p className="text-slate-500 mt-0.5">Units used for land area, yield, and weather</p>
              </div>
              <select
                value={appSettings.units}
                onChange={(e) => handleSelect('units', e.target.value)}
                className="bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
              >
                <option value="metric">Metric (kg, hectares, °C)</option>
                <option value="imperial">Imperial (lbs, acres, °F)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Appearance */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center gap-2">
            <Sun className="w-3.5 h-3.5 text-slate-400" />
            Appearance
          </h3>
          <div className="flex items-center justify-between text-xs">
            <div>
              <p className="font-semibold text-slate-700">Dark Mode</p>
              <p className="text-slate-500 mt-0.5">Switch between light and dark interface themes</p>
            </div>
            <button
              onClick={() => handleToggle('darkMode')}
              className={`relative w-10 h-5 rounded-full transition-colors focus:outline-none ${
                appSettings.darkMode ? 'bg-green-600' : 'bg-slate-200'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                  appSettings.darkMode ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center gap-2">
            <Bell className="w-3.5 h-3.5 text-slate-400" />
            Notifications & Alerts
          </h3>
          <div className="flex items-center justify-between text-xs">
            <div>
              <p className="font-semibold text-slate-700">Push Notifications</p>
              <p className="text-slate-500 mt-0.5">Receive weather alerts, crop advisories, and disease warnings</p>
            </div>
            <button
              onClick={() => handleToggle('notifications')}
              className={`relative w-10 h-5 rounded-full transition-colors focus:outline-none ${
                appSettings.notifications ? 'bg-green-600' : 'bg-slate-200'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                  appSettings.notifications ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>

        {/* About */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center gap-2">
            <Shield className="w-3.5 h-3.5 text-slate-400" />
            About FarmAssist
          </h3>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="font-bold text-slate-400 uppercase tracking-wider text-[9px] block mb-1">Application</span>
              <p className="font-semibold text-slate-700">FarmAssist — AgriGenie AI</p>
            </div>
            <div>
              <span className="font-bold text-slate-400 uppercase tracking-wider text-[9px] block mb-1">Version</span>
              <p className="font-semibold text-slate-700">v1.0.0</p>
            </div>
            <div>
              <span className="font-bold text-slate-400 uppercase tracking-wider text-[9px] block mb-1">Model</span>
              <p className="font-semibold text-slate-700">ConvGeM-NeXt Disease Classifier</p>
            </div>
            <div>
              <span className="font-bold text-slate-400 uppercase tracking-wider text-[9px] block mb-1">Region</span>
              <p className="font-semibold text-slate-700">Kerala, India</p>
            </div>
          </div>
        </div>

        {/* Save */}
        <div className="flex items-center gap-4">
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-green-600 hover:bg-green-700 active:bg-green-800 text-white font-semibold py-2 px-5 rounded-lg text-xs transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <Save className="w-3.5 h-3.5" />
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
          {success && (
            <div className="flex items-center gap-1.5 text-xs text-green-700 font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              {success}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
