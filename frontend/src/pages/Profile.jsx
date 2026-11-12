import React, { useState, useEffect } from 'react';
import { User, Layers, Save, CheckCircle2, History, Sprout, TrendingUp, Calendar, AlertCircle, Loader2, MessageSquareCode, ThumbsUp, ThumbsDown } from 'lucide-react';
import { twinAPI, chatbotAPI } from '../utils/api';

const getCropEmoji = (crop) => {
  if (!crop) return '🌱';
  const c = crop.toLowerCase();
  if (c.includes('rice') || c.includes('paddy')) return '🌾';
  if (c.includes('coconut')) return '🥥';
  if (c.includes('banana')) return '🍌';
  if (c.includes('pepper')) return '🌶️';
  if (c.includes('rubber')) return '🌳';
  if (c.includes('cardamom')) return '🌱';
  if (c.includes('coffee')) return '☕';
  if (c.includes('tea')) return '🍵';
  if (c.includes('tomato')) return '🍅';
  if (c.includes('mango')) return '🥭';
  return '🌱';
};

const StatusBadge = ({ status }) => {
  const s = (status || '').toUpperCase();
  if (s === 'ACTIVE') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold bg-green-50 text-green-700 border border-green-200 uppercase tracking-wide">
        <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse inline-block" />
        Active
      </span>
    );
  }
  if (s === 'HARVESTED') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold bg-blue-50 text-blue-700 border border-blue-200 uppercase tracking-wide">
        ✓ Harvested
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-bold bg-slate-50 text-slate-600 border border-slate-200 uppercase tracking-wide">
      {status}
    </span>
  );
};

const formatDate = (dateStr) => {
  if (!dateStr) return 'Not recorded';
  try {
    return new Date(dateStr).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  } catch {
    return dateStr;
  }
};

function CycleCard({ cycle }) {
  const isActive = cycle.status === 'ACTIVE';
  return (
    <div className={`border rounded-lg p-4 space-y-3 transition-colors ${isActive ? 'border-green-200 bg-green-50/40' : 'border-slate-100 bg-slate-50/30'}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xl">{getCropEmoji(cycle.crop_name)}</span>
          <div>
            <p className="font-bold text-slate-800 text-xs capitalize">{cycle.crop_name}</p>
            <p className="text-[10px] text-slate-500">{cycle.season} · {cycle.year}</p>
          </div>
        </div>
        <StatusBadge status={cycle.status} />
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px]">
        <div className="flex items-center gap-1 text-slate-500">
          <Calendar className="w-3 h-3" />
          <span>Started: <span className="text-slate-700 font-semibold">{formatDate(cycle.start_date)}</span></span>
        </div>
        <div className="flex items-center gap-1 text-slate-500">
          <Layers className="w-3 h-3" />
          <span>Area: <span className="text-slate-700 font-semibold">{cycle.area_acres} acre{cycle.area_acres !== 1 ? 's' : ''}</span></span>
        </div>
        {cycle.harvest_date && (
          <div className="flex items-center gap-1 text-slate-500">
            <CheckCircle2 className="w-3 h-3 text-blue-500" />
            <span>Harvested: <span className="text-slate-700 font-semibold">{formatDate(cycle.harvest_date)}</span></span>
          </div>
        )}
        <div className="flex items-center gap-1 text-slate-500">
          <Sprout className="w-3 h-3" />
          <span>Yield: <span className="text-slate-700 font-semibold">
            {cycle.actual_yield != null ? `${cycle.actual_yield.toLocaleString()} kg` : cycle.expected_yield != null ? `~${cycle.expected_yield.toLocaleString()} kg (est.)` : 'Not recorded'}
          </span></span>
        </div>
        <div className="flex items-center gap-1 text-slate-500">
          <TrendingUp className="w-3 h-3" />
          <span>Profit: <span className="text-slate-700 font-semibold">
            {cycle.actual_profit != null ? `₹${cycle.actual_profit.toLocaleString()}` : cycle.expected_profit != null ? `~₹${cycle.expected_profit.toLocaleString()} (est.)` : 'Not recorded'}
          </span></span>
        </div>
        {cycle.fertilizer_used && cycle.fertilizer_used !== 'None' && (
          <div className="col-span-2 text-slate-500">Fertilizer: <span className="text-slate-700 font-semibold">{cycle.fertilizer_used}</span></div>
        )}
      </div>
    </div>
  );
}

export default function Profile() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [profileData, setProfileData] = useState(null);

  // Separate state for persistent cultivation history from /profile/crop-cycles
  const [cyclesLoading, setCyclesLoading] = useState(true);
  const [cyclesError, setCyclesError] = useState('');
  const [allCycles, setAllCycles] = useState([]);

  const [feedbackLoading, setFeedbackLoading] = useState(true);
  const [feedbackError, setFeedbackError] = useState('');
  const [feedbackHistory, setFeedbackHistory] = useState([]);
  
  const [formData, setFormData] = useState({
    farm_name: 'Primary Farm',
    location_district: 'Idukki',
    latitude: 9.8497,
    longitude: 76.9804,
    soil_type: 'Laterite',
    land_area_acres: 1.5,
    water_availability: 'medium',
    irrigation_type: 'manual'
  });

  useEffect(() => {
    fetchProfileDetails();
    fetchCultivationHistory();
    fetchFeedbackHistory();
  }, []);

  const fetchProfileDetails = async () => {
    try {
      setLoading(true);
      const data = await twinAPI.getSummary();
      setProfileData(data);
      if (data.farmer_profile.farm) {
        setFormData(data.farmer_profile.farm);
      }
    } catch (err) {
      console.error(err);
      setError('Failed to fetch profile settings.');
    } finally {
      setLoading(false);
    }
  };

  // Fetch ALL crop cycles (ACTIVE + HARVESTED) from the persistent database
  // Uses GET /api/v1/profile/crop-cycles — authenticated, user-scoped
  const fetchCultivationHistory = async () => {
    try {
      setCyclesLoading(true);
      setCyclesError('');
      const cycles = await twinAPI.getCropCycles();
      setAllCycles(Array.isArray(cycles) ? cycles : []);
    } catch (err) {
      console.error('Failed to load cultivation history:', err);
      if (err.response?.status === 401 || err.response?.status === 403) {
        setCyclesError('Authentication error. Please log in again.');
      } else if (err.response?.status === 404) {
        // No farm yet — genuinely empty, not an error
        setAllCycles([]);
      } else {
        setCyclesError('Unable to load cultivation history. Please try again.');
      }
    } finally {
      setCyclesLoading(false);
    }
  };

  const fetchFeedbackHistory = async () => {
    try {
      setFeedbackLoading(true);
      setFeedbackError('');
      // Need to import chatbotAPI from api.js if not already imported, but let's assume it or we can import it.
      // Wait, api.js exports chatbotAPI. Let's check imports at the top of Profile.jsx.
      // Assuming we need to import it, I'll add the import first. Actually, I can use a direct call if imported.
      const history = await chatbotAPI.getFeedbackHistory();
      setFeedbackHistory(Array.isArray(history) ? history : []);
    } catch (err) {
      console.error('Failed to load feedback history:', err);
      setFeedbackError('Unable to load chatbot feedback history.');
    } finally {
      setFeedbackLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: name === 'land_area_acres' || name === 'latitude' || name === 'longitude' ? parseFloat(value) || value : value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      // Simulate/call farm update endpoint
      const response = await twinAPI.updateFarm(
        formData.farm_name,
        formData.location_district,
        formData.latitude,
        formData.longitude,
        formData.soil_type,
        formData.land_area_acres,
        formData.water_availability,
        formData.irrigation_type
      );
      setSuccess('Farm specifications updated successfully.');
      fetchProfileDetails();
    } catch (err) {
      console.error(err);
      setError('Failed to update farm details.');
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-500">
        Loading Profile Settings...
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 overflow-y-auto h-[calc(100vh-64px)] bg-slate-50/50">
      <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Left Card: Farmer Profile details */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-6 shadow-sm h-fit">
          <div className="text-center space-y-3">
            <div className="w-16 h-16 rounded-full bg-green-150 mx-auto flex items-center justify-center border border-green-200">
              <User className="w-8 h-8 text-green-700" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800 text-sm">{profileData?.farmer_profile?.full_name || 'Jhanandhan'}</h3>
              <p className="text-xs text-slate-500">{profileData?.farmer_profile?.phone_number || '0987654321'}</p>
            </div>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-green-50 text-green-700 border border-green-100 uppercase tracking-wide">
              Farmer Partner
            </span>
          </div>

          <div className="border-t border-slate-100 pt-4 space-y-3 text-xs">
            <div>
              <span className="font-bold text-slate-400 uppercase tracking-wider text-[9px]">Interface Language</span>
              <p className="font-semibold text-slate-700 capitalize mt-0.5">{profileData?.farmer_profile?.preferred_language || 'English'}</p>
            </div>
            <div>
              <span className="font-bold text-slate-400 uppercase tracking-wider text-[9px]">Member Since</span>
              <p className="font-semibold text-slate-700 mt-0.5">
                {new Date(profileData?.farmer_profile?.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long' })}
              </p>
            </div>
          </div>
        </div>

        {/* Right Columns: Farm specifications */}
        <div className="md:col-span-2 space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-6 shadow-sm">
            <div>
              <h3 className="font-bold text-slate-800 text-sm">Farm Digital Twin Specifications</h3>
              <p className="text-xs text-slate-500">Configure land parameters used for dynamic ML recommendations</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1.5">Farm Identification Name</label>
                  <input 
                    type="text"
                    name="farm_name"
                    value={formData.farm_name}
                    onChange={handleInputChange}
                    className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600" 
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1.5">Location District</label>
                  <select 
                    name="location_district"
                    value={formData.location_district}
                    onChange={handleInputChange}
                    className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600" 
                  >
                    <option value="Palakkad">Palakkad</option>
                    <option value="Idukki">Idukki</option>
                    <option value="Wayanad">Wayanad</option>
                    <option value="Thrissur">Thrissur</option>
                    <option value="Kollam">Kollam</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1.5">Soil Classification Type</label>
                  <select 
                    name="soil_type"
                    value={formData.soil_type}
                    onChange={handleInputChange}
                    className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600" 
                  >
                    <option value="Laterite">Laterite Soil</option>
                    <option value="Clayey">Kuttanad Clayey Soil</option>
                    <option value="Sandy Loam">Coastal Sandy Loam</option>
                    <option value="Acidic Forest Loam">Munnar Acidic Forest Loam</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1.5">Land Area (Acres)</label>
                  <input 
                    type="number" 
                    name="land_area_acres"
                    step="0.1"
                    value={formData.land_area_acres}
                    onChange={handleInputChange}
                    className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600" 
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1.5">Water Availability</label>
                  <select 
                    name="water_availability"
                    value={formData.water_availability}
                    onChange={handleInputChange}
                    className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600" 
                  >
                    <option value="high">Abundant Water (River/Well fed)</option>
                    <option value="medium">Moderate Water</option>
                    <option value="low">Water Deficient / Drylands</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1.5">Irrigation Setup</label>
                  <select 
                    name="irrigation_type"
                    value={formData.irrigation_type}
                    onChange={handleInputChange}
                    className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600" 
                  >
                    <option value="manual">Manual / Flooding</option>
                    <option value="drip">Precision Drip Irrigation</option>
                    <option value="sprinkler">Sprinkler System</option>
                    <option value="rainfed">Rainfed Only</option>
                  </select>
                </div>
              </div>

              {error && <div className="text-xs text-rose-600 font-semibold">{error}</div>}
              {success && (
                <div className="bg-green-50 border border-green-200 text-green-700 text-xs px-4 py-3 rounded-lg flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  {success}
                </div>
              )}

              <button
                type="submit"
                className="bg-green-600 hover:bg-green-700 active:bg-green-800 text-white font-semibold py-2 px-4 rounded-lg text-xs transition-colors flex items-center gap-1.5"
              >
                <Save className="w-3.5 h-3.5" />
                Save Specifications
              </button>
            </form>
          </div>

          {/* ============================================================
              CULTIVATION HISTORY
              Source: GET /api/v1/profile/crop-cycles (persistent database)
              Shows ALL cycles: ACTIVE first, then HARVESTED, sorted by start_date desc.
              Previous crops are NEVER overwritten — each cycle is a separate DB record.
              ============================================================ */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-sm">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-slate-800 text-sm flex items-center gap-1.5">
                <History className="w-4 h-4 text-slate-400" />
                Cultivation History
              </h4>
              {!cyclesLoading && !cyclesError && (
                <button
                  type="button"
                  onClick={fetchCultivationHistory}
                  className="text-[10px] text-slate-400 hover:text-green-600 font-semibold transition-colors"
                >
                  Refresh
                </button>
              )}
            </div>

            {/* Loading state — shown while fetching from backend */}
            {cyclesLoading && (
              <div className="flex items-center gap-2 text-xs text-slate-500 py-4">
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading cultivation history...
              </div>
            )}

            {/* Error state — clearly distinct from empty history */}
            {!cyclesLoading && cyclesError && (
              <div className="flex items-start gap-2 bg-rose-50 border border-rose-200 text-rose-700 text-xs px-4 py-3 rounded-lg">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Error loading history</p>
                  <p className="text-rose-600 mt-0.5">{cyclesError}</p>
                  <button
                    type="button"
                    onClick={fetchCultivationHistory}
                    className="mt-2 text-rose-700 font-bold underline underline-offset-2"
                  >
                    Try again
                  </button>
                </div>
              </div>
            )}

            {/* Empty state — only shown after a successful fetch with zero records */}
            {!cyclesLoading && !cyclesError && allCycles.length === 0 && (
              <div className="text-center py-8 space-y-2">
                <Sprout className="w-8 h-8 text-slate-300 mx-auto" />
                <p className="text-xs text-slate-500 font-medium">No cultivation history yet.</p>
                <p className="text-[10px] text-slate-400">
                  Start a farming cycle from the Crop Intelligence page to begin logging history.
                </p>
              </div>
            )}

            {/* Active cycles — shown prominently at top */}
            {!cyclesLoading && !cyclesError && allCycles.filter(c => c.status === 'ACTIVE').length > 0 && (
              <div className="space-y-2">
                <p className="text-[10px] font-bold text-green-700 uppercase tracking-wider">
                  Current Active Cycle{allCycles.filter(c => c.status === 'ACTIVE').length > 1 ? 's' : ''}
                </p>
                {allCycles
                  .filter(c => c.status === 'ACTIVE')
                  .sort((a, b) => new Date(b.start_date) - new Date(a.start_date))
                  .map(cycle => <CycleCard key={cycle.id} cycle={cycle} />)
                }
              </div>
            )}

            {/* All previously completed / harvested cycles */}
            {!cyclesLoading && !cyclesError && allCycles.filter(c => c.status !== 'ACTIVE').length > 0 && (
              <div className="space-y-2">
                {allCycles.filter(c => c.status === 'ACTIVE').length > 0 && (
                  <div className="border-t border-slate-100 pt-3">
                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Previous Cultivation Cycles</p>
                  </div>
                )}
                {allCycles
                  .filter(c => c.status !== 'ACTIVE')
                  .sort((a, b) => new Date(b.start_date) - new Date(a.start_date))
                  .map(cycle => <CycleCard key={cycle.id} cycle={cycle} />)
                }
              </div>
            )}
          </div>

          {/* Chatbot Feedback History */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-sm">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-slate-800 text-sm flex items-center gap-1.5">
                <MessageSquareCode className="w-4 h-4 text-slate-400" />
                Chatbot Feedback History
              </h4>
              {!feedbackLoading && !feedbackError && (
                <button
                  type="button"
                  onClick={fetchFeedbackHistory}
                  className="text-[10px] text-slate-400 hover:text-green-600 font-semibold transition-colors"
                >
                  Refresh
                </button>
              )}
            </div>

            {feedbackLoading && (
              <div className="flex items-center gap-2 text-xs text-slate-500 py-4">
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading feedback history...
              </div>
            )}

            {!feedbackLoading && feedbackError && (
              <div className="flex items-start gap-2 bg-rose-50 border border-rose-200 text-rose-700 text-xs px-4 py-3 rounded-lg">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Error loading feedback</p>
                  <p className="text-rose-600 mt-0.5">{feedbackError}</p>
                  <button
                    type="button"
                    onClick={fetchFeedbackHistory}
                    className="mt-2 text-rose-700 font-bold underline underline-offset-2"
                  >
                    Try again
                  </button>
                </div>
              </div>
            )}

            {!feedbackLoading && !feedbackError && feedbackHistory.length === 0 && (
              <div className="text-center py-8 space-y-2">
                <MessageSquareCode className="w-8 h-8 text-slate-300 mx-auto" />
                <p className="text-xs text-slate-500 font-medium">No feedback provided yet.</p>
                <p className="text-[10px] text-slate-400">
                  Provide feedback to the AI assistant to help it improve.
                </p>
              </div>
            )}

            {!feedbackLoading && !feedbackError && feedbackHistory.length > 0 && (
              <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                {feedbackHistory.map(feedback => (
                  <div key={feedback.id} className="border border-slate-100 bg-slate-50 rounded-lg p-4 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-bold text-slate-800 line-clamp-2">Q: {feedback.query}</p>
                      {feedback.rating === 1 ? (
                        <ThumbsUp className="w-4 h-4 text-green-600 shrink-0" />
                      ) : (
                        <ThumbsDown className="w-4 h-4 text-rose-600 shrink-0" />
                      )}
                    </div>
                    <p className="text-[10px] text-slate-600 line-clamp-3">A: {feedback.response}</p>
                    <div className="flex items-center gap-3 text-[9px] text-slate-400 font-semibold pt-2 border-t border-slate-200 mt-2">
                      <span>{new Date(feedback.created_at).toLocaleDateString()}</span>
                      {feedback.intent && <span>Intent: {feedback.intent}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
