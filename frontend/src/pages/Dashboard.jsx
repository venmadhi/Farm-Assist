import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Calendar, 
  Coins, 
  AlertTriangle, 
  CheckCircle2, 
  Plus, 
  CloudSun,
  ShieldAlert,
  ArrowRight,
  TrendingUp,
  MapPin,
  Map,
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
  
  // Crop History Form States
  const [cropForm, setCropForm] = useState({
    crop_name: 'rice',
    yield_kg: '',
    season: 'Kharif',
    year: new Date().getFullYear(),
    revenue: '',
    weather_summary: 'Good Rain',
    disease_incidence: 'None',
    fertilizer_used: 'Organic Ash',
    market_price: ''
  });
  const [formSuccess, setFormSuccess] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  // Active Cycle Harvest Form States
  const [harvestForm, setHarvestForm] = useState({
    actual_yield: '',
    actual_selling_price: '',
    cultivation_cost: '',
    fertilizer_used: '',
    disease_incidence: ''
  });
  const [harvestLoading, setHarvestLoading] = useState(false);

  useEffect(() => {
    fetchTwinData();
    fetchWeatherData();
  }, []);

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
      // Geolocate user coordinates if allowed
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

  const handleHistorySubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormSuccess('');
    try {
      await twinAPI.addCropHistory(
        cropForm.crop_name,
        cropForm.yield_kg,
        cropForm.season,
        cropForm.year,
        cropForm.revenue,
        cropForm.weather_summary,
        cropForm.disease_incidence,
        cropForm.fertilizer_used,
        cropForm.market_price
      );
      setFormSuccess('Harvest logged to Digital Twin history buffer.');
      setCropForm({
        crop_name: 'rice',
        yield_kg: '',
        season: 'Kharif',
        year: new Date().getFullYear(),
        revenue: '',
        weather_summary: 'Good Rain',
        disease_incidence: 'None',
        fertilizer_used: 'Organic Ash',
        market_price: ''
      });
      fetchTwinData(); // Refresh metrics
    } catch (err) {
      console.error(err);
      setError('Failed to log harvest record.');
    } finally {
      setFormLoading(false);
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
    setHarvestLoading(true);
    setError('');
    const activeCycleId = twinData.active_cycles[0].id;
    try {
      await twinAPI.harvestCropCycle(
        activeCycleId,
        harvestForm.actual_yield,
        harvestForm.actual_selling_price,
        harvestForm.cultivation_cost,
        harvestForm.fertilizer_used,
        harvestForm.disease_incidence
      );
      setHarvestForm({
        actual_yield: '',
        actual_selling_price: '',
        cultivation_cost: '',
        fertilizer_used: '',
        disease_incidence: ''
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

  const chartData = twinData?.soil_history 
    ? [...twinData.soil_history].reverse()
    : [];

  const metrics = twinData?.digital_twin_metrics || {
    health_score: 75.0,
    expected_yield_kg: 0.0,
    expected_profit_inr: 0.0,
    risk_score: 15.0,
    risk_reasons: ["No active farming data"],
    latest_crop: "None"
  };

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

      {/* AI metrics cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <StatCard 
          title="Farm Health Score" 
          value={`${metrics.health_score}%`}
          description={`Soil & crop health standard`}
          icon={Activity}
          trend={metrics.health_score >= 80 ? "Optimal Health" : "Alert warnings"}
          trendColor={metrics.health_score >= 80 ? "green" : "red"}
        />
        <StatCard 
          title="Expected Yield (ML)" 
          value={`${metrics.expected_yield_kg.toLocaleString()} kg`}
          description={`Forecasted for next harvest`}
          icon={Calendar}
          trend={`Crop: ${metrics.latest_crop}`}
          trendColor="green"
        />
        <StatCard 
          title="Seasonal Profit" 
          value={`₹${metrics.expected_profit_inr.toLocaleString()}`}
          description="Predicted crop revenue yields"
          icon={Coins}
          trend="Forecast"
          trendColor="green"
        />
        <StatCard 
          title="Overall Risk Score" 
          value={`${metrics.risk_score}%`}
          description="Climate, disease, volatility risk"
          icon={ShieldAlert}
          trend={metrics.risk_score > 35 ? "High Hazard" : "Low Risk"}
          trendColor={metrics.risk_score > 35 ? "red" : "green"}
        />
      </div>

      {/* Active Crop Cycle Tracker */}
      {twinData?.active_cycles && twinData.active_cycles.length > 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-sm">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <div>
              <span className="text-[9px] font-bold text-green-700 bg-green-50 px-2.5 py-0.5 rounded-full border border-green-200 uppercase tracking-wider">
                Active Crop Cycle
              </span>
              <h3 className="font-extrabold text-slate-800 text-sm mt-1.5">
                Monitoring {twinData.active_cycles[0].crop.toUpperCase()} Cultivation
              </h3>
            </div>
            <div className="text-right text-xs text-slate-500 font-medium">
              Started: <strong className="text-slate-700">{twinData.active_cycles[0].start_date}</strong>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
            <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Land Area</span>
              <strong className="text-slate-850 text-sm">{twinData.active_cycles[0].area_acres} Acres</strong>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Expected Yield</span>
              <strong className="text-slate-850 text-sm">{twinData.active_cycles[0].expected_yield.toLocaleString()} kg</strong>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Expected Revenue</span>
              <strong className="text-slate-850 text-sm">₹{twinData.active_cycles[0].expected_revenue.toLocaleString()}</strong>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Expected Profit</span>
              <strong className="text-slate-850 text-sm">₹{twinData.active_cycles[0].expected_profit.toLocaleString()}</strong>
            </div>
          </div>

          {/* Harvest Outcome Form (inline expandable) */}
          <div className="bg-slate-50 border border-slate-100 rounded-lg p-5 mt-4 space-y-4">
            <div>
              <h4 className="font-bold text-slate-805 text-xs">Log Harvest & Close Cycle</h4>
              <p className="text-[10px] text-slate-500">Record actual farm performance metrics at harvest to evaluate accuracy and update agent personalization.</p>
            </div>
            
            <form onSubmit={handleHarvestSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div>
                <label className="block font-bold text-slate-500 uppercase tracking-wider mb-1.5">Actual Yield (kg)</label>
                <input 
                  type="number" 
                  name="actual_yield"
                  required 
                  value={harvestForm.actual_yield}
                  onChange={handleHarvestChange}
                  placeholder="e.g. 1450"
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none"
                />
              </div>
              <div>
                <label className="block font-bold text-slate-500 uppercase tracking-wider mb-1.5">Actual Selling Price (₹/kg)</label>
                <input 
                  type="number" 
                  name="actual_selling_price"
                  required 
                  value={harvestForm.actual_selling_price}
                  onChange={handleHarvestChange}
                  placeholder="e.g. 42"
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none"
                />
              </div>
              <div>
                <label className="block font-bold text-slate-500 uppercase tracking-wider mb-1.5">Actual Cultivation Cost (₹)</label>
                <input 
                  type="number" 
                  name="cultivation_cost"
                  required 
                  value={harvestForm.cultivation_cost}
                  onChange={handleHarvestChange}
                  placeholder="e.g. 15000"
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none"
                />
              </div>
              <div>
                <label className="block font-bold text-slate-500 uppercase tracking-wider mb-1.5">Fertilizers Applied</label>
                <input 
                  type="text" 
                  name="fertilizer_used"
                  value={harvestForm.fertilizer_used}
                  onChange={handleHarvestChange}
                  placeholder="e.g. Compost, Urea"
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none"
                />
              </div>
              <div>
                <label className="block font-bold text-slate-500 uppercase tracking-wider mb-1.5">Disease Incidence Noticed</label>
                <input 
                  type="text" 
                  name="disease_incidence"
                  value={harvestForm.disease_incidence}
                  onChange={handleHarvestChange}
                  placeholder="e.g. None, Leaf spot"
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none"
                />
              </div>
              <div className="flex items-end">
                <button
                  type="submit"
                  disabled={harvestLoading}
                  className="w-full bg-green-600 hover:bg-green-700 active:bg-green-800 text-white font-bold py-2 rounded-lg transition-colors flex items-center justify-center gap-2 text-xs"
                >
                  {harvestLoading ? 'Completing Cycle...' : 'Submit Harvest & Log Feedback'}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}

      {/* Warnings & Alerts Banner */}
      {twinData?.soil_warnings.length > 0 && (
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

      {/* Main Grid: Soil Telemetry & Cultivation Logger */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Soil health history chart */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-sm">
          <div>
            <h3 className="font-bold text-slate-800 text-sm">Soil Chemistry Telemetry</h3>
            <p className="text-xs text-slate-500">Historical NPK values logged under primary farm digital twin</p>
          </div>
          
          <div className="h-80 w-full text-xs">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorN" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22c55e" stopOpacity={0.1}/>
                      <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorP" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorK" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#a855f7" stopOpacity={0.1}/>
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
              <div className="h-full flex items-center justify-center border border-dashed border-slate-200 rounded-lg bg-slate-50 text-xs text-slate-500">
                No NPK telemetry records found. Perform crop suitabilities to generate soil tests.
              </div>
            )}
          </div>
        </div>

        {/* Cultivation Log Form */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-6 shadow-sm">
          <div>
            <h3 className="font-bold text-slate-800 text-sm">Log Harvest & Yield</h3>
            <p className="text-xs text-slate-500">Record actual crop performance metrics to improve ML training accuracy</p>
          </div>

          <form onSubmit={handleHistorySubmit} className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-500 uppercase tracking-wider mb-2">Crop Species</label>
              <select 
                value={cropForm.crop_name}
                onChange={(e) => setCropForm({...cropForm, crop_name: e.target.value})}
                className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2 text-xs text-slate-800 focus:outline-none"
              >
                <option value="rice">Rice (Paddy)</option>
                <option value="banana">Banana</option>
                <option value="coconut">Coconut</option>
                <option value="pepper">Black Pepper</option>
                <option value="cardamom">Cardamom</option>
                <option value="coffee">Coffee</option>
                <option value="tea">Tea</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-slate-500 uppercase tracking-wider mb-2">Yield (kg)</label>
                <input 
                  type="number"
                  required
                  value={cropForm.yield_kg}
                  onChange={(e) => setCropForm({...cropForm, yield_kg: e.target.value})}
                  className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2 text-xs text-slate-800 focus:outline-none"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-500 uppercase tracking-wider mb-2">Revenue (₹)</label>
                <input 
                  type="number"
                  value={cropForm.revenue}
                  onChange={(e) => setCropForm({...cropForm, revenue: e.target.value})}
                  className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2 text-xs text-slate-800 focus:outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-slate-500 uppercase tracking-wider mb-2">Season</label>
                <select 
                  value={cropForm.season}
                  onChange={(e) => setCropForm({...cropForm, season: e.target.value})}
                  className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2 text-xs text-slate-800 focus:outline-none"
                >
                  <option value="Kharif">Kharif / Monsoon</option>
                  <option value="Rabi">Rabi / Winter</option>
                  <option value="Summer">Summer / Zaid</option>
                </select>
              </div>
              <div>
                <label className="block font-semibold text-slate-500 uppercase tracking-wider mb-2">Harvest Year</label>
                <input 
                  type="number"
                  required
                  value={cropForm.year}
                  onChange={(e) => setCropForm({...cropForm, year: e.target.value})}
                  className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2 text-xs text-slate-800 focus:outline-none"
                />
              </div>
            </div>

            {formSuccess && (
              <p className="text-xs text-green-600 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                {formSuccess}
              </p>
            )}

            <button
              type="submit"
              disabled={formLoading}
              className="w-full bg-green-600 hover:bg-green-700 active:bg-green-800 text-white font-semibold py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {formLoading ? 'Logging...' : 'Log Crop Harvest'}
              <Plus className="w-3.5 h-3.5" />
            </button>
          </form>
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
                <th className="py-3 px-4 text-right">Confidence score</th>
                <th className="py-3 px-4 text-right">Yield index</th>
                <th className="py-3 px-4 text-right">Estimated Profit</th>
              </tr>
            </thead>
            <tbody>
              {twinData?.recent_recommendations.length > 0 ? (
                twinData.recent_recommendations.map((rec) => (
                  <tr key={rec.id} className="border-b border-slate-100 hover:bg-slate-50/50 text-xs transition-colors">
                    <td className="py-3 px-4 text-slate-500 font-medium">{rec.date}</td>
                    <td className="py-3 px-4 font-bold text-slate-850 capitalize">{rec.crop}</td>
                    <td className="py-3 px-4 text-right text-slate-700">{(rec.confidence * 100).toFixed(0)}%</td>
                    <td className="py-3 px-4 text-right text-green-650 font-bold">{rec.yield} kg/ac</td>
                    <td className="py-3 px-4 text-right text-slate-650 font-semibold">₹{rec.profit.toLocaleString()}</td>
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
            <p className="text-xs text-slate-500">Actual harvest outcomes vs model-predicted estimates</p>
          </div>
          
          {/* Manual retraining trigger */}
          <button
            onClick={async () => {
              try {
                const resp = await twinAPI.triggerRetraining();
                alert(resp.message);
                fetchTwinData();
              } catch (err) {
                console.error(err);
                alert("Failed to trigger retraining check.");
              }
            }}
            className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold px-3 py-1.5 rounded-lg text-[10px] transition-colors"
          >
            Trigger Retraining Check
          </button>
        </div>

        <div className="overflow-x-auto text-xs">
          {twinData?.crop_history && twinData.crop_history.length > 0 ? (
            <table className="w-full text-left border-collapse font-sans">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 text-[10px] font-bold uppercase tracking-wider">
                  <th className="py-2.5 px-3">Completed Date</th>
                  <th className="py-2.5 px-3">Crop Name</th>
                  <th className="py-2.5 px-3 text-right">Expected Yield</th>
                  <th className="py-2.5 px-3 text-right">Actual Yield</th>
                  <th className="py-2.5 px-3 text-right">Absolute Error</th>
                  <th className="py-2.5 px-3 text-right">Percentage Error</th>
                  <th className="py-2.5 px-3 text-right">Actual Profit</th>
                </tr>
              </thead>
              <tbody>
                {twinData.crop_history.map((c) => {
                  const absErr = Math.abs(c.expected_yield - c.yield);
                  const pctErr = c.yield ? (absErr / c.yield * 100).toFixed(1) : "0.0";
                  return (
                    <tr key={c.id} className="border-b border-slate-105 hover:bg-slate-50/50 transition-colors text-slate-700">
                      <td className="py-3 px-3 text-slate-500">{c.harvest_date || 'N/A'}</td>
                      <td className="py-3 px-3 font-bold text-slate-800 capitalize">{c.crop}</td>
                      <td className="py-3 px-3 text-right">{c.expected_yield.toLocaleString()} kg</td>
                      <td className="py-3 px-3 text-right font-semibold text-green-700">{c.yield.toLocaleString()} kg</td>
                      <td className="py-3 px-3 text-right">{absErr.toFixed(1)} kg</td>
                      <td className={`py-3 px-3 text-right font-bold ${absErr / c.yield > 0.2 ? 'text-amber-600' : 'text-green-600'}`}>
                        {pctErr}%
                      </td>
                      <td className="py-3 px-3 text-right font-bold text-slate-900">₹{(c.revenue - c.cultivation_cost).toLocaleString()}</td>
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
