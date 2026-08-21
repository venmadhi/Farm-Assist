import React, { useState } from 'react';
import { Sprout, Phone, Lock, AlertCircle, ArrowRight } from 'lucide-react';
import { authAPI } from '../utils/api';

export default function Login({ onLoginSuccess, switchToRegister }) {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = await authAPI.login(phoneNumber, password);
      localStorage.setItem('agrigenie_token', data.access_token);
      onLoginSuccess();
    } catch (err) {
      console.error(err);
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Incorrect phone number or password. Check backend server.');
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
              Welcome to FarmAssist
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Personalized Decision Intelligence for Kerala Farmers
            </p>
          </div>
        </div>

        {/* Login form */}
        <form onSubmit={handleSubmit} className="space-y-4">
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

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
              <input 
                type="password" 
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white border border-slate-200 rounded-lg pl-12 pr-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
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
            {loading ? 'Authenticating...' : 'Sign In'}
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Footer toggles */}
        <div className="text-center pt-4 border-t border-slate-105">
          <p className="text-xs text-slate-550">
            Don't have a land profile yet?{' '}
            <button
              onClick={switchToRegister}
              className="text-green-600 font-semibold hover:underline"
            >
              Register Land Profile
            </button>
          </p>
        </div>

      </div>
    </div>
  );
}
