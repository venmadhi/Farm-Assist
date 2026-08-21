import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Coins, 
  Calendar,
  AlertCircle,
  Clock,
  Sparkles
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { marketAPI } from '../utils/api';

export default function MarketAnalysis() {
  const [selectedCrop, setSelectedCrop] = useState('banana');
  const [selectedDistrict, setSelectedDistrict] = useState('Palakkad');
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  const districts = ['Palakkad', 'Idukki', 'Wayanad', 'Thrissur', 'Kollam'];

  useEffect(() => {
    fetchMarketTrends();
  }, [selectedCrop, selectedDistrict]);

  const fetchMarketTrends = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await marketAPI.getTrends(selectedCrop, selectedDistrict);
      setData(response);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch market trends. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-64px)]">
        <div className="relative w-10 h-10">
          <div className="absolute inset-0 rounded-full border-4 border-slate-200 border-t-green-600 animate-spin"></div>
        </div>
      </div>
    );
  }

  // Preprocess chart data for Recharts by adding forecast dates
  const getExtendedChartData = () => {
    if (!data || !data.historical_prices) return [];
    
    // Add 7-day and 30-day forecast points to show forecast curve
    const history = [...data.historical_prices];
    history.push({ month: "7-Day Forecast (ML)", price: data.price_forecast_7d });
    history.push({ month: "30-Day Forecast (ML)", price: data.price_forecast_30d });
    return history;
  };

  return (
    <div className="p-8 space-y-6 overflow-y-auto h-[calc(100vh-64px)] bg-slate-50/50 text-xs">
      
      {/* Query Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 flex flex-wrap items-center justify-between gap-6 shadow-sm">
        <div className="space-y-1">
          <h3 className="font-bold text-slate-800 text-sm">Agmarknet Price Forecasting</h3>
          <p className="text-xs text-slate-500 font-sans">Analyze commodity prices and forecast margins per acre using XGBoost models</p>
        </div>
        
        <div className="flex gap-4">
          <div>
            <label className="block text-[9px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Crop Selection</label>
            <select
              value={selectedCrop}
              onChange={(e) => setSelectedCrop(e.target.value)}
              className="bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
            >
              <option value="rice">Nel (Rice/Paddy)</option>
              <option value="coconut">Thengu (Coconut)</option>
              <option value="banana">Vazha (Banana)</option>
              <option value="pepper">Kurumulaku (Black Pepper)</option>
              <option value="rubber">Rubber</option>
              <option value="cardamom">Elam (Cardamom)</option>
              <option value="coffee">Kappi (Coffee)</option>
              <option value="tea">Teyila (Tea)</option>
            </select>
          </div>
          <div>
            <label className="block text-[9px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">District (Kerala)</label>
            <select
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              className="bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none"
            >
              {districts.map((d, i) => (
                <option key={i} value={d}>{d}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-600 text-xs px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          <div className="lg:col-span-8 space-y-6">
            
            {/* Commodity Pricing Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-2 shadow-sm">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Today's Price</p>
                <h4 className="text-xl font-bold text-slate-900">₹{data.price_today} <span className="text-[10px] text-slate-500">/ kg</span></h4>
                <div className="flex items-center gap-1 border-t border-slate-50 pt-1.5 mt-1.5">
                  <span className={`inline-flex items-center gap-0.5 px-1.5 py-0.2 rounded-full text-[9px] font-bold ${
                    data.demand_trend === 'Upward' ? 'bg-green-50 text-green-700' :
                    data.demand_trend === 'Downward' ? 'bg-rose-50 text-rose-700' :
                    'bg-slate-50 text-slate-600'
                  }`}>
                    {data.demand_trend === 'Upward' ? <TrendingUp className="w-2.5 h-2.5" /> : <TrendingDown className="w-2.5 h-2.5" />}
                    {data.demand_trend}
                  </span>
                </div>
              </div>

              <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-2 shadow-sm">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">7-Day Forecast</p>
                <h4 className="text-xl font-bold text-slate-900">₹{data.price_forecast_7d} <span className="text-[10px] text-slate-500">/ kg</span></h4>
                <span className="text-[9px] text-slate-550 font-medium block border-t border-slate-50 pt-1.5 mt-1.5">Short-term drift</span>
              </div>

              <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-2 shadow-sm">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">30-Day Forecast</p>
                <h4 className="text-xl font-bold text-slate-900">₹{data.price_forecast_30d} <span className="text-[10px] text-slate-500">/ kg</span></h4>
                <span className="text-[9px] text-slate-550 font-medium block border-t border-slate-50 pt-1.5 mt-1.5">XGBoost model run</span>
              </div>

              <div className="bg-green-600 text-white rounded-xl p-4 space-y-2 shadow-sm">
                <p className="text-[10px] font-bold text-white/80 uppercase tracking-wider">Expected Net Profit</p>
                <h4 className="text-xl font-bold">₹{data.projected_profit.toLocaleString()} <span className="text-[10px] text-white/70">/ ac</span></h4>
                <p className="text-[9px] text-white/90 flex items-center gap-1 border-t border-green-500/50 pt-1.5 mt-1.5">
                  <Coins className="w-3 h-3" />
                  Cultivation Cost: ₹{data.investment_cost.toLocaleString()}
                </p>
              </div>
            </div>

            {/* Price Chart with Forecast Curve */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-sm">
              <div>
                <h4 className="font-bold text-slate-800 text-xs">Commodity Price Curve & Forecast (Agmarknet)</h4>
                <p className="text-xs text-slate-500 font-sans">Historical values matched with ML 7-day and 30-day projection coordinates</p>
              </div>

              <div className="h-64 w-full text-xs">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={getExtendedChartData()} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#16a34a" stopOpacity={0.1}/>
                        <stop offset="95%" stopColor="#16a34a" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="month" stroke="#64748b" fontSize={10} />
                    <YAxis stroke="#64748b" fontSize={10} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px', fontSize: '11px' }}
                    />
                    <Area name="Sales Price (₹/kg)" type="monotone" dataKey="price" stroke="#16a34a" strokeWidth={2.5} fillOpacity={1} fill="url(#colorPrice)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>

          {/* Budget cost calculator and best harvest window */}
          <div className="lg:col-span-4 space-y-6">
            <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-6 shadow-sm">
              <div>
                <h4 className="font-bold text-slate-800 text-xs">Harvest Marketing Window</h4>
                <p className="text-xs text-slate-500">ML-derived peak sales window matching seasonal price waves</p>
              </div>

              <div className="bg-amber-50 border border-amber-100 rounded-lg p-4 flex gap-3 text-amber-900">
                <Clock className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <strong className="block text-[10px] font-bold uppercase tracking-wider text-amber-700">Optimal Sell Window</strong>
                  <p className="font-semibold text-xs leading-tight">{data.best_selling_month}</p>
                  <p className="text-[10px] text-amber-800 mt-1">Historically, Onam and wedding season exports cause demand spikes. Consider crop scheduling offsets.</p>
                </div>
              </div>

              <div className="space-y-2 border-t border-slate-100 pt-4">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2">Detailed Cultivation Costs per acre</span>
                <div className="space-y-2.5">
                  <div className="space-y-1">
                    <div className="flex justify-between font-semibold">
                      <span className="text-slate-500">Seeds & Saplings</span>
                      <span className="text-slate-800">₹{round(data.investment_cost * 0.2, 0).toLocaleString()}</span>
                    </div>
                    <div className="w-full h-1 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-green-600" style={{ width: '20%' }}></div>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between font-semibold">
                      <span className="text-slate-500">Soil tilling & labor</span>
                      <span className="text-slate-800">₹{round(data.investment_cost * 0.15, 0).toLocaleString()}</span>
                    </div>
                    <div className="w-full h-1 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-green-600" style={{ width: '15%' }}></div>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between font-semibold">
                      <span className="text-slate-500">NPK & organic compost</span>
                      <span className="text-slate-800">₹{round(data.investment_cost * 0.25, 0).toLocaleString()}</span>
                    </div>
                    <div className="w-full h-1 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-green-600" style={{ width: '25%' }}></div>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between font-semibold">
                      <span className="text-slate-500">Harvesting manpower</span>
                      <span className="text-slate-800">₹{round(data.investment_cost * 0.4, 0).toLocaleString()}</span>
                    </div>
                    <div className="w-full h-1 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-green-600" style={{ width: '40%' }}></div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 space-y-2">
                <div className="flex items-center gap-1.5 font-bold text-slate-700">
                  <Calendar className="w-4 h-4 text-green-600" />
                  Growth Cycle Details
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed font-sans">
                  Average growth duration is <strong>{data.harvest_cycle_months} months</strong> from sowing to market readiness. Ensure price-hedging calculations are aligned to harvest calendars.
                </p>
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  );
}

// Helper utility
function round(value, precision) {
  var multiplier = Math.pow(10, precision || 0);
  return Math.round(value * multiplier) / multiplier;
}
