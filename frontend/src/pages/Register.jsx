import React, { useState } from 'react';
import { Sprout, Phone, Lock, User, AlertCircle, ArrowRight } from 'lucide-react';
import { authAPI } from '../utils/api';

export default function Register({ onRegisterSuccess, switchToLogin }) {
  const [fullName, setFullName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [password, setPassword] = useState('');
  const [district, setDistrict] = useState('Palakkad');
  const [soilType, setSoilType] = useState('Laterite');
  const [landArea, setLandArea] = useState('1.0');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const districts = ['Palakkad', 'Idukki', 'Wayanad', 'Kottayam', 'Thrissur', 'Kollam', 'Alappuzha', 'Kasaragod', 'Kannur', 'Malappuram', 'Kozhikode', 'Pathanamthitta', 'Ernakulam', 'Trivandrum'];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = await authAPI.register(
        fullName,
        phoneNumber,
        password,
        district,
        soilType,
        landArea
      );
      localStorage.setItem('agrigenie_token', data.access_token);
      onRegisterSuccess();
    } catch (err) {
      console.error(err);
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Registration failed. Ensure phone is unique and server is active.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6 relative overflow-hidden select-none">
      <div className="w-full max-w-md bg-white border border-slate-200 rounded-xl p-8 space-y-6 relative z-10 shadow-sm">
        
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-10 h-10 rounded-lg bg-green-600 flex items-center justify-center mx-auto">
            <Sprout className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-slate-900 tracking-tight">
              Register Land Profile
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Initialize your farm profile to trigger adaptive learning predictions
            </p>
          </div>
        </div>

        {/* Register form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                <input 
                  type="text" 
                  required
                  placeholder="e.g. Madhavan"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-lg pl-12 pr-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">Phone Number</label>
              <div className="relative">
                <Phone className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                <input 
                  type="text" 
                  required
                  placeholder="e.g. 9876543210"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-lg pl-12 pr-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
                />
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">Password (Min 6 chars)</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
              <input 
                type="password" 
                required
                placeholder="••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white border border-slate-200 rounded-lg pl-12 pr-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 border-t border-slate-100 pt-4">
            <div className="space-y-1.5">
              <label className="block text-[9px] font-bold text-slate-500 uppercase tracking-wider">District</label>
              <select
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                className="w-full bg-white border border-slate-200 rounded-lg px-2 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
              >
                {districts.map((d, i) => (
                  <option key={i} value={d}>{d}</option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-[9px] font-bold text-slate-500 uppercase tracking-wider">Soil Type</label>
              <select
                value={soilType}
                onChange={(e) => setSoilType(e.target.value)}
                className="w-full bg-white border border-slate-200 rounded-lg px-2 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
              >
                <option value="Laterite">Laterite Soil</option>
                <option value="Clayey">Clayey Soil</option>
                <option value="Alluvial">Alluvial Soil</option>
                <option value="Forest Humus">Forest Humus</option>
                <option value="Sandy Loam">Sandy Loam</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-[9px] font-bold text-slate-500 uppercase tracking-wider">Acres</label>
              <input 
                type="number" 
                step="0.1"
                required
                value={landArea}
                onChange={(e) => setLandArea(e.target.value)}
                className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
              />
            </div>
          </div>

          {error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-600 text-xs px-4 py-2.5 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 hover:bg-green-700 active:bg-green-800 text-white font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 text-xs shadow-xs"
          >
            {loading ? 'Initializing Twin...' : 'Register Profile'}
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Footer link */}
        <div className="text-center pt-4 border-t border-slate-105">
          <p className="text-xs text-slate-550">
            Already have a profile?{' '}
            <button
              onClick={switchToLogin}
              className="text-green-600 font-semibold hover:underline"
            >
              Sign In here
            </button>
          </p>
        </div>

      </div>
    </div>
  );
}
