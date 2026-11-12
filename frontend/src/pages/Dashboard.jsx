import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Calendar, 
  Coins, 
  AlertTriangle, 
  CheckCircle2, 
  CloudSun,
  ShieldAlert,
  Sprout
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts';
import { twinAPI } from '../utils/api';
import StatCard from '../components/StatCard';

export default function Dashboard() {
  const [twinData, setTwinData] = useState(null);
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [error, setError] = useState('');

  // Active Cycle Harvest Form States (Source of Truth for Harvest)
  const [harvestForm, setHarvestForm] = useState({
    actual_yield: '',
    actual_selling_price: '',
    cultivation_cost: '',
    fertilizer_used: '',
    disease_incidence: '',
    start_date: '',
    harvest_date: new Date().toISOString().split('T')[0]
  });
  const [harvestLoading, setHarvestLoading] = useState(false);

  useEffect(() => {
    fetchTwinData();
    fetchWeatherData();
  }, []);

  useEffect(() => {
    if (twinData?.active_cycles && twinData.active_cycles.length > 0) {
      setHarvestForm(prev => ({
        ...prev,
        start_date: prev.start_date || twinData.active_cycles[0].start_date || new Date().toISOString().split('T')[0]
      }));
    }
  }, [twinData]);

  const fetchTwinData = async () => {
    setLoading(true);
    try {
      const data = await twinAPI.getSummary();
      setTwinData(data);
    } catch (err) {
      console.error(err);
      setError('Failed to load Digital Twin data.');
    } finally {
      setLoading(false);
    }
  };

  const fetchWeatherData = async () => {
    setWeatherLoading(true);
    try {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords;
          const w = await twinAPI.getWeather(latitude, longitude);
          setWeatherData(w);
          setWeatherLoading(false);
        },
        async (err) => {
          console.warn("Geolocation denied/failed. Fetching default weather details:", err);
          const w = await twinAPI.getWeather();
          setWeatherData(w);
          setWeatherLoading(false);
        }
      );
    } catch (err) {
      console.error("Error fetching weather API:", err);
      setWeatherLoading(false);
    }
  };

  const handleHarvestChange = (e) => {
    setHarvestForm({
      ...harvestForm,
      [e.target.name]: e.target.value
    });
  };

  const handleHarvestSubmit = async (e) => {
    e.preventDefault();
    if (!twinData?.active_cycles || twinData.active_cycles.length === 0) return;

    const yieldVal = parseFloat(harvestForm.actual_yield);
    const priceVal = parseFloat(harvestForm.actual_selling_price);
    const costVal = parseFloat(harvestForm.cultivation_cost);

    if (isNaN(yieldVal) || yieldVal <= 0) {
      setError("Actual Yield must be greater than 0 kg.");
      return;
    }
    if (isNaN(priceVal) || priceVal < 0) {
      setError("Actual Selling Price must be non-negative.");
      return;
    }
    if (isNaN(costVal) || costVal < 0) {
      setError("Actual Cultivation Cost must be non-negative.");
      return;
    }
    if (harvestForm.start_date && harvestForm.harvest_date && harvestForm.harvest_date < harvestForm.start_date) {
      setError("Harvest/End Date cannot be earlier than Start Date.");
      return;
    }

    setHarvestLoading(true);
    setError('');
    const activeCycleId = twinData.active_cycles[0].id;

    try {
      await twinAPI.harvestCropCycle(
        activeCycleId,
        yieldVal,
        priceVal,
        costVal,
        harvestForm.fertilizer_used,
        harvestForm.disease_incidence,
        harvestForm.start_date,
        harvestForm.harvest_date
      );
      setHarvestForm({
        actual_yield: '',
        actual_selling_price: '',
        cultivation_cost: '',
        fertilizer_used: '',
        disease_incidence: '',
        start_date: '',
        harvest_date: new Date().toISOString().split('T')[0]
      });
      fetchTwinData();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to complete harvest logging.');
    } finally {
      setHarvestLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-64px)]">
        <div className="relative w-10 h-10">
          <div className="absolute inset-0 rounded-full border-4 border-slate-200 border-t-green-600 animate-spin"></div>
        </div>
      </div>
    );
  }

  const chartData = twinData?.soil_history || [];

  const metrics = twinData?.digital_twin_metrics || {
    health_score: 75.0,
    expected_yield_kg: 0.0,
    expected_profit_inr: 0.0,
    risk_score: 15.0,
    risk_reasons: ["No active farming data"],
    latest_crop: "None"
  };

  // Calculate Deltas for the dashboard arrows
  const prevCycle = twinData?.crop_history && twinData.crop_history.length > 0 ? twinData.crop_history[0] : null;
  const healthScoreBaseline = 75.0;
  const riskScoreBaseline = 15.0;

  const healthDir = metrics.health_score > healthScoreBaseline ? 'up' : (metrics.health_score < healthScoreBaseline ? 'down' : 'neutral');
  const riskDir = metrics.risk_score > riskScoreBaseline ? 'up' : (metrics.risk_score < riskScoreBaseline ? 'down' : 'neutral');
  
  let yieldDir = 'neutral';
  let profitDir = 'neutral';
  if (prevCycle) {
    if (metrics.expected_yield_kg > prevCycle.yield) yieldDir = 'up';
    else if (metrics.expected_yield_kg < prevCycle.yield) yieldDir = 'down';

    const prevProfit = prevCycle.actual_profit !== null && prevCycle.actual_profit !== undefined 
      ? prevCycle.actual_profit 
      : (prevCycle.revenue - prevCycle.cultivation_cost);
    if (metrics.expected_profit_inr > prevProfit) profitDir = 'up';
    else if (metrics.expected_profit_inr < prevProfit) profitDir = 'down';
  } else {
     if (metrics.expected_yield_kg > 0) yieldDir = 'up';
     if (metrics.expected_profit_inr > 0) profitDir = 'up';
  }

  return (
    <div className="p-8 space-y-6 overflow-y-auto h-[calc(100vh-64px)] bg-slate-50/50">
      
      {/* Geolocation Live Weather widget row */}
      {weatherData && (
        <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-xl p-5 text-white shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1.5">
            <span className="text-[10px] font-bold tracking-wider uppercase bg-white/20 px-2 py-0.5 rounded">Live Agro-Weather Station</span>
            <div className="flex items-center gap-2">
              <CloudSun className="w-6 h-6 text-amber-200 shrink-0" />
              <h3 className="text-lg font-bold">{weatherData.district} District Weather</h3>
            </div>
            <p className="text-xs text-white/85">
              Lat: {weatherData.latitude.toFixed(4)} • Lon: {weatherData.longitude.toFixed(4)}
            </p>
          </div>
          <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs font-semibold">
            <div className="border-r border-white/20 pr-4">
              <span className="text-white/70 block text-[9px] uppercase">Temperature</span>
              <span className="text-sm font-extrabold">{weatherData.temperature}°C</span>
            </div>
            <div className="border-r border-white/20 pr-4">
              <span className="text-white/70 block text-[9px] uppercase">Humidity</span>
              <span className="text-sm font-extrabold">{weatherData.humidity}%</span>
            </div>
            <div className="border-r border-white/20 pr-4">
              <span className="text-white/70 block text-[9px] uppercase">Rainfall</span>
              <span className="text-sm font-extrabold">{weatherData.rainfall} mm</span>
            </div>
            <div className="border-r border-white/20 pr-4">
              <span className="text-white/70 block text-[9px] uppercase">Wind</span>
              <span className="text-sm font-extrabold">{weatherData.wind_speed} km/h</span>
            </div>
            <div>
              <span className="text-white/70 block text-[9px] uppercase">Active Season</span>
              <span className="text-sm font-extrabold block max-w-[120px] truncate">{weatherData.season}</span>
            </div>
          </div>
        </div>
      )}

      {/* Error alert if any */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-xl p-4 flex items-center justify-between shadow-sm text-xs">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError('')} className="text-rose-600 font-bold hover:underline">Dismiss</button>
        </div>
      )}

      {/* AI metrics cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <StatCard 
          title="Farm Health Score" 
          value={`${metrics?.health_score ?? 0}%`}
          description="Soil & crop health standard"
          icon={Activity}
          trend={(metrics?.health_score ?? 0) >= 80 ? "Optimal Health" : "Alert warnings"}
          trendColor={(metrics?.health_score ?? 0) >= 80 ? "green" : "red"}
          trendDirection={healthDir}
        />
        <StatCard 
          title="Expected Yield (ML)" 
          value={`${(metrics?.expected_yield_kg ?? 0).toLocaleString()} kg`}
          description="Forecasted for next harvest"
          icon={Calendar}
          trend={`Crop: ${metrics?.latest_crop || 'None'}`}
          trendColor="green"
          trendDirection={yieldDir}
        />
        <StatCard 
          title="Seasonal Profit" 
          value={`₹${(metrics?.expected_profit_inr ?? 0).toLocaleString()}`}
          description="Predicted crop net profits"
          icon={Coins}
          trend="Forecast"
          trendColor="green"
          trendDirection={profitDir}
        />
        <StatCard 
          title="Overall Risk Score" 
          value={`${metrics?.risk_score ?? 0}%`}
          description="Climate, disease, volatility risk"
          icon={ShieldAlert}
          trend={(metrics?.risk_score ?? 0) > 35 ? "High Hazard" : "Low Risk"}
          trendColor={(metrics?.risk_score ?? 0) > 35 ? "red" : "green"}
          trendDirection={riskDir}
        />
      </div>

      {/* Active Crop Cycle Tracker & Authoritative Harvest Logger */}
      {twinData?.active_cycles && twinData.active_cycles.length > 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-sm">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <div>
              <span className="text-[9px] font-bold text-green-700 bg-green-50 px-2.5 py-0.5 rounded-full border border-green-200 uppercase tracking-wider">
                Active Crop Cycle
              </span>
              <h3 className="font-extrabold text-slate-800 text-sm mt-1.5">
                Monitoring {String(twinData.active_cycles[0]?.crop_name || twinData.active_cycles[0]?.crop || 'Active Crop').toUpperCase()} Cultivation
              </h3>
            </div>
            <div className="text-right text-xs text-slate-500 font-medium">
              Started: <strong className="text-slate-700">{twinData.active_cycles[0]?.start_date || 'N/A'}</strong>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
            <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Land Area</span>
              <strong className="text-slate-800 text-sm">{twinData.active_cycles[0]?.area_acres ?? 0} Acres</strong>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Expected Yield (Predicted)</span>
              <strong className="text-slate-800 text-sm">{(twinData.active_cycles[0]?.expected_yield ?? 0).toLocaleString()} kg</strong>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Expected Revenue</span>
              <strong className="text-slate-800 text-sm">₹{(twinData.active_cycles[0]?.expected_revenue ?? 0).toLocaleString()}</strong>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Expected Profit</span>
              <strong className="text-slate-800 text-sm">₹{(twinData.active_cycles[0]?.expected_profit ?? 0).toLocaleString()}</strong>
            </div>
          </div>

          {/* Authoritative Harvest Outcome Form */}
          <div className="bg-slate-50 border border-slate-100 rounded-lg p-5 mt-4 space-y-4">
            <div>
              <h4 className="font-bold text-slate-800 text-xs">Log Harvest & Close Cycle</h4>
              <p className="text-[10px] text-slate-500">
                Record actual farm performance metrics at harvest to evaluate accuracy and update agent personalization.
              </p>
            </div>
            
            <form onSubmit={handleHarvestSubmit} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                    Actual Yield (kg) *
                  </label>
                  <input 
                    type="number" 
                    step="any"
                    name="actual_yield"
                    required 
                    value={harvestForm.actual_yield}
                    onChange={handleHarvestChange}
                    placeholder="e.g. 1466"
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                    Actual Selling Price (₹/kg) *
                  </label>
                  <input 
                    type="number" 
                    step="any"
                    name="actual_selling_price"
                    required 
                    value={harvestForm.actual_selling_price}
                    onChange={handleHarvestChange}
                    placeholder="e.g. 42"
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                    Actual Cultivation Cost (₹) *
                  </label>
                  <input 
                    type="number" 
                    step="any"
                    name="cultivation_cost"
                    required 
                    value={harvestForm.cultivation_cost}
                    onChange={handleHarvestChange}
                    placeholder="e.g. 15000"
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
                  />
                  <p className="text-[10px] text-slate-400 mt-1">
                    Enter total cultivation cost including irrigation, fertilizers, pesticides, labour, transportation, storage, etc.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                    Cultivation Start Date *
                  </label>
                  <input 
                    type="date" 
                    name="start_date"
                    required 
                    value={harvestForm.start_date}
                    onChange={handleHarvestChange}
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                    Harvest / End Date *
                  </label>
                  <input 
                    type="date" 
                    name="harvest_date"
                    required 
                    value={harvestForm.harvest_date}
                    onChange={handleHarvestChange}
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                    Fertilizers Applied
                  </label>
                  <input 
                    type="text" 
                    name="fertilizer_used"
                    value={harvestForm.fertilizer_used}
                    onChange={handleHarvestChange}
                    placeholder="e.g. FYM, Wood Ash"
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                    Disease Incidence Noticed
                  </label>
                  <input 
                    type="text" 
                    name="disease_incidence"
                    value={harvestForm.disease_incidence}
                    onChange={handleHarvestChange}
                    placeholder="e.g. Leaf spot, None"
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={harvestLoading}
                  className="bg-green-600 hover:bg-green-700 active:bg-green-800 text-white font-bold px-6 py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 text-xs shadow-sm"
                >
                  {harvestLoading ? 'Completing Cycle...' : 'Submit Harvest & Log Feedback'}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}

      {/* Warnings & Alerts Banner */}
      {twinData?.soil_warnings && twinData.soil_warnings.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 flex items-start gap-4 shadow-sm">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-bold text-sm text-amber-900">Explainable Soil Warnings</h4>
            <ul className="text-xs text-amber-800 list-disc list-inside space-y-0.5">
              {twinData.soil_warnings.map((warn, i) => (
                <li key={i}>{warn}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Soil Telemetry Chart (Real Farmer NPK Measurements Only) */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-sm">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-bold text-slate-800 text-sm">Soil Chemistry Telemetry</h3>
            <p className="text-xs text-slate-500">Historical NPK values logged under primary farm digital twin</p>
          </div>
          {chartData.length > 0 && (
            <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
              {chartData.length} Real Observation{chartData.length > 1 ? 's' : ''}
            </span>
          )}
        </div>
        
        <div className="h-80 w-full text-xs">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorN" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.15}/>
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorP" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorK" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.15}/>
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="measured_at" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px', fontSize: '12px' }}
                  labelStyle={{ color: '#64748b', fontWeight: 'bold' }}
                />
                <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: '11px', fontWeight: 550 }} />
                <Area name="Nitrogen (N) ppm" type="monotone" dataKey="n" stroke="#22c55e" strokeWidth={2} fillOpacity={1} fill="url(#colorN)" />
                <Area name="Phosphorus (P) ppm" type="monotone" dataKey="p" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorP)" />
                <Area name="Potassium (K) ppm" type="monotone" dataKey="k" stroke="#a855f7" strokeWidth={2} fillOpacity={1} fill="url(#colorK)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex flex-col items-center justify-center border border-dashed border-slate-200 rounded-lg bg-slate-50 text-xs text-slate-500 p-6 text-center space-y-2">
              <Sprout className="w-8 h-8 text-slate-300" />
              <p className="font-semibold text-slate-600">No NPK telemetry records found</p>
              <p className="text-[11px] text-slate-400 max-w-sm">
                Provide lab-tested soil metrics in Crop Suitability or Fertilizer Optimizer to log actual telemetry measurements.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Layout: Recommendation History */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-sm">
        <div>
          <h3 className="font-bold text-slate-800 text-sm">Recent AgriGenie Crop Predictions</h3>
          <p className="text-xs text-slate-500">Historical advisor runs stored in the digital twin memory logs</p>
        </div>

        <div className="overflow-x-auto text-xs">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Predicted Date</th>
                <th className="py-3 px-4">Crop</th>
                <th className="py-3 px-4 text-right">Suitability score</th>
                <th className="py-3 px-4 text-right">Yield index</th>
                <th className="py-3 px-4 text-right">Estimated Profit</th>
              </tr>
            </thead>
            <tbody>
              {twinData?.recent_recommendations && twinData.recent_recommendations.length > 0 ? (
                twinData.recent_recommendations.map((rec) => (
                  <tr key={rec.id} className="border-b border-slate-100 hover:bg-slate-50/50 text-xs transition-colors">
                    <td className="py-3 px-4 text-slate-500 font-medium">{rec.date}</td>
                    <td className="py-3 px-4 font-bold text-slate-800 capitalize">{rec.crop}</td>
                    <td className="py-3 px-4 text-right text-slate-700">{(rec.confidence * 100).toFixed(0)}%</td>
                    <td className="py-3 px-4 text-right text-green-700 font-bold">{rec.yield} kg/ac</td>
                    <td className="py-3 px-4 text-right text-slate-700 font-semibold">₹{rec.profit.toLocaleString()}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-500 text-xs">
                    No recommendations processed yet. Navigate to Crop Suitability to run your first evaluation.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Farm History & Completed Crop Cycles Section */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-sm">
        <div className="flex justify-between items-center border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-extrabold text-slate-800 text-sm">Farmer Yield History & Decision Feedback</h3>
            <p className="text-xs text-slate-500">Real harvest outcomes vs original model-predicted estimates</p>
          </div>
          
          {/* Retraining Evaluation trigger */}
          <button
            onClick={async () => {
              try {
                const resp = await twinAPI.triggerRetraining();
                alert(resp.message);
                fetchTwinData();
              } catch (err) {
                console.error(err);
                alert("Failed to evaluate retraining status.");
              }
            }}
            className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold px-3 py-1.5 rounded-lg text-[10px] transition-colors"
          >
            Evaluate Retraining Status
          </button>
        </div>

        <div className="overflow-x-auto text-xs">
          {twinData?.crop_history && twinData.crop_history.length > 0 ? (
            <table className="w-full text-left border-collapse font-sans">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 text-[10px] font-bold uppercase tracking-wider">
                  <th className="py-2.5 px-3">Harvest Date</th>
                  <th className="py-2.5 px-3">Start Date</th>
                  <th className="py-2.5 px-3">Crop Name</th>
                  <th className="py-2.5 px-3 text-right">Expected Yield</th>
                  <th className="py-2.5 px-3 text-right">Actual Yield</th>
                  <th className="py-2.5 px-3 text-right">Absolute Error</th>
                  <th className="py-2.5 px-3 text-right">Prediction Error</th>
                  <th className="py-2.5 px-3 text-right">Actual Revenue</th>
                  <th className="py-2.5 px-3 text-right">Cultivation Cost</th>
                  <th className="py-2.5 px-3 text-right">Actual Net Profit</th>
                  <th className="py-2.5 px-3">Disease / Notes</th>
                </tr>
              </thead>
              <tbody>
                {twinData.crop_history.map((c) => {
                  const hasActualYield = c.yield !== null && c.yield !== undefined;
                  const expYield = c.expected_yield !== null && c.expected_yield !== undefined ? c.expected_yield : null;
                  const actYield = c.yield;
                  const absErr = (expYield !== null && hasActualYield) ? Math.abs(expYield - actYield) : null;
                  const pctErr = (absErr !== null && actYield > 0) ? ((absErr / actYield) * 100).toFixed(1) : "0.0";
                  
                  const revenue = c.revenue !== null && c.revenue !== undefined ? c.revenue : null;
                  const cost = c.cultivation_cost !== null && c.cultivation_cost !== undefined ? c.cultivation_cost : null;
                  const profit = c.actual_profit !== null && c.actual_profit !== undefined 
                    ? c.actual_profit 
                    : ((revenue !== null && cost !== null) ? (revenue - cost) : null);

                  return (
                    <tr key={c.id} className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors text-slate-700">
                      <td className="py-3 px-3 text-slate-500 font-medium">{c.harvest_date || 'N/A'}</td>
                      <td className="py-3 px-3 text-slate-500">{c.start_date || 'N/A'}</td>
                      <td className="py-3 px-3 font-bold text-slate-800 capitalize">{c.crop}</td>
                      <td className="py-3 px-3 text-right">
                        {expYield !== null ? `${expYield.toLocaleString()} kg` : 'N/A'}
                      </td>
                      <td className="py-3 px-3 text-right font-semibold text-green-700">
                        {hasActualYield ? `${actYield.toLocaleString()} kg` : <span className="text-slate-400 italic">Actual harvest not recorded</span>}
                      </td>
                      <td className="py-3 px-3 text-right">
                        {absErr !== null ? `${absErr.toFixed(1)} kg` : 'N/A'}
                      </td>
                      <td className="py-3 px-3 text-right font-bold text-slate-700">
                        {hasActualYield && absErr !== null ? `${pctErr}%` : 'N/A'}
                      </td>
                      <td className="py-3 px-3 text-right font-semibold text-slate-800">
                        {revenue !== null ? `₹${revenue.toLocaleString()}` : 'N/A'}
                      </td>
                      <td className="py-3 px-3 text-right text-slate-600">
                        {cost !== null ? `₹${cost.toLocaleString()}` : 'N/A'}
                      </td>
                      <td className={`py-3 px-3 text-right font-bold ${profit !== null ? (profit >= 0 ? 'text-green-700' : 'text-rose-600') : 'text-slate-700'}`}>
                        {profit !== null ? `₹${profit.toLocaleString()}` : 'N/A'}
                      </td>
                      <td className="py-3 px-3 text-slate-500 text-[11px]">
                        {c.disease && c.disease !== 'None' ? (
                          <span className="text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-medium">
                            {c.disease}
                          </span>
                        ) : (
                          <span className="text-slate-400">None</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div className="py-8 text-center text-slate-500 space-y-4">
              <Sprout className="w-8 h-8 mx-auto text-slate-350" />
              <div className="space-y-1">
                <p className="font-bold text-slate-700 text-xs">No Farming History Available</p>
                <p className="text-[11px] text-slate-400">Personalized insights will become available after your first farming cycle.</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-lg mx-auto pt-2 text-[10px] uppercase font-bold text-slate-450 tracking-wider">
                <div className="p-3 border border-slate-150 rounded bg-slate-50/30">
                  Farm History: <span className="text-slate-500 font-bold block mt-1">No farming history yet</span>
                </div>
                <div className="p-3 border border-slate-150 rounded bg-slate-50/30">
                  Profit History: <span className="text-slate-500 font-bold block mt-1">No completed crop cycles</span>
                </div>
                <div className="p-3 border border-slate-150 rounded bg-slate-50/30">
                  Yield History: <span className="text-slate-500 font-bold block mt-1">No actual yield records</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
