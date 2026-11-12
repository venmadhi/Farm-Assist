import React, { useState, useEffect } from 'react';
import { 
  FlaskConical, 
  HelpCircle, 
  Leaf, 
  CheckCircle2, 
  AlertTriangle, 
  Sparkles 
} from 'lucide-react';
import { fertilizerAPI, twinAPI } from '../utils/api';

export default function FertilizerOptimizer() {
  const [formData, setFormData] = useState({
    crop_name: 'banana',
    nitrogen: 65,
    phosphorus: 40,
    potassium: 50,
    ph: 5.4,
  });

  const [farmId, setFarmId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    twinAPI.getSummary().then(data => {
      if (data.farmer_profile.farm) {
        setFarmId(data.farmer_profile.farm.id);
      }
    }).catch(err => {
      console.error(err);
      setFarmId(1);
    });
  }, []);

  // Default optimal crop values map to help farmers pre-fill values during demonstrations
  const cropDefaults = {
    paddy: { n: 60, p: 35, k: 30, ph: 6.2 },
    coconut: { n: 40, p: 20, k: 80, ph: 6.5 },
    banana: { n: 80, p: 40, k: 100, ph: 6.8 },
    pepper: { n: 45, p: 30, k: 50, ph: 5.8 },
    rubber: { n: 30, p: 15, k: 35, ph: 5.2 },
    cardamom: { n: 50, p: 30, k: 60, ph: 5.6 },
  };

  const handleCropChange = (e) => {
    const crop = e.target.value;
    const defaults = cropDefaults[crop] || { n: 50, p: 30, k: 50, ph: 6.0 };
    setFormData({
      crop_name: crop,
      nitrogen: defaults.n,
      phosphorus: defaults.p,
      potassium: defaults.k,
      ph: defaults.ph,
    });
    setResult(null); // Reset result on crop change
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: parseFloat(value) || value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const activeFarmId = farmId || 1;
      const data = await fertilizerAPI.calculate(
        activeFarmId,
        formData.crop_name,
        formData.nitrogen,
        formData.phosphorus,
        formData.potassium,
        formData.ph
      );
      setResult(data);
    } catch (err) {
      console.error(err);
      setError('Failed to compute fertilizer recommendation. Make sure backend is active.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const s = status.toLowerCase();
    if (s.includes('deficient')) return 'text-amber-700 bg-amber-50 border-amber-250';
    if (s.includes('excess')) return 'text-rose-700 bg-rose-50 border-rose-200';
    return 'text-green-700 bg-green-50 border-green-200';
  };

  return (
    <div className="p-8 space-y-6 overflow-y-auto h-[calc(100vh-64px)] bg-slate-50/50">
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Fertilizer Input Form */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-6 h-fit shadow-sm">
          <div className="space-y-1">
            <h3 className="font-bold text-slate-800 text-sm">Soil Nutrient Matrix</h3>
            <p className="text-xs text-slate-500">Calculate precision organic and inorganic NPK inputs</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Target Crop</label>
              <select
                value={formData.crop_name}
                onChange={handleCropChange}
                className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
              >
                <option value="paddy">Nel (Paddy)</option>
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
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Soil Nitrogen (N) ppm</label>
              <input
                type="number"
                name="nitrogen"
                required
                value={formData.nitrogen}
                onChange={handleInputChange}
                className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Phosphorus (P) ppm</label>
                <input
                  type="number"
                  name="phosphorus"
                  required
                  value={formData.phosphorus}
                  onChange={handleInputChange}
                  className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Potassium (K) ppm</label>
                <input
                  type="number"
                  name="potassium"
                  required
                  value={formData.potassium}
                  onChange={handleInputChange}
                  className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Soil pH (Acidic/Alkaline)</label>
              <input
                type="number"
                name="ph"
                step="0.1"
                required
                value={formData.ph}
                onChange={handleInputChange}
                className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-green-600 focus:border-green-600"
              />
            </div>

            {error && (
              <p className="text-xs text-rose-600 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" />
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green-600 hover:bg-green-700 active:bg-green-800 text-white font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 text-xs shadow-sm"
            >
              {loading ? 'Calculating Dosage...' : 'Calculate Fertilizer Program'}
            </button>
          </form>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2 space-y-6">
          {result ? (
            <div className="space-y-6">
              
              {/* NPK Status Badges */}
              <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-sm">
                <div className="flex justify-between items-center">
                  <h4 className="font-bold text-slate-800 text-xs">Soil Nutrient Levels vs Crop Needs</h4>
                  {result.estimated_cost > 0 && (
                    <span className="text-[10px] font-bold text-green-700 bg-green-50 px-2.5 py-0.5 rounded border border-green-150">
                      Est. Cost: ₹{result.estimated_cost}
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className={`p-3 rounded-lg border flex flex-col items-center justify-center gap-0.5 text-center ${getStatusColor(result.n_status)}`}>
                    <span className="text-[9px] uppercase font-bold tracking-wider opacity-85">Nitrogen (N)</span>
                    <strong className="text-sm font-bold">{result.n_status}</strong>
                  </div>
                  <div className={`p-3 rounded-lg border flex flex-col items-center justify-center gap-0.5 text-center ${getStatusColor(result.p_status)}`}>
                    <span className="text-[9px] uppercase font-bold tracking-wider opacity-85">Phosphorus (P)</span>
                    <strong className="text-sm font-bold">{result.p_status}</strong>
                  </div>
                  <div className={`p-3 rounded-lg border flex flex-col items-center justify-center gap-0.5 text-center ${getStatusColor(result.k_status)}`}>
                    <span className="text-[9px] uppercase font-bold tracking-wider opacity-85">Potassium (K)</span>
                    <strong className="text-sm font-bold">{result.k_status}</strong>
                  </div>
                </div>
              </div>

              {/* Fertilizer Schedule */}
              <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-sm">
                <div>
                  <h4 className="font-bold text-slate-800 text-xs">Precision Fertilizer Application Schedule</h4>
                  <p className="text-xs text-slate-500">Chronological application calendar for {result.crop_name}</p>
                </div>

                <div className="space-y-4">
                  {result.fertilizer_schedule.map((item, idx) => (
                    <div key={idx} className="bg-slate-50 border border-slate-200 rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="space-y-1">
                        <span className="text-[9px] font-bold text-green-700 bg-green-50 px-2 py-0.5 rounded-full border border-green-150">
                          {item.stage}
                        </span>
                        <h5 className="font-bold text-slate-850 text-xs mt-1">{item.fertilizer_name}</h5>
                        <p className="text-gray-700">
                          Recommended dosage: <strong>{item.amount_grams_per_sqm} g/m²</strong> (approx. {round(item.amount_grams_per_sqm * 4.047, 1)} kg per acre)
                        </p>
                      </div>

                      {/* Organic alternative box */}
                      <div className="p-3 bg-white border border-slate-200 rounded-lg min-w-[200px] sm:max-w-xs">
                        <span className="text-[9px] font-bold text-green-700 flex items-center gap-1 uppercase tracking-wider mb-1">
                          <Leaf className="w-3 h-3 text-green-600" />
                          Jaiva (Organic) Substitutes
                        </span>
                        <ul className="text-[10px] text-slate-600 list-disc list-inside space-y-0.5">
                          {item.organic_alternatives.map((alt, i) => (
                            <li key={i}>{alt}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sustainability Tips */}
              <div className="bg-green-50 border border-green-200 rounded-xl p-6 space-y-3">
                <h5 className="text-xs font-bold text-green-700 flex items-center gap-1.5 uppercase tracking-wider">
                  <Sparkles className="w-3.5 h-3.5" />
                  Eco-friendly Farming & Soil Correction
                </h5>
                <ul className="text-xs text-slate-700 space-y-2 list-none">
                  {result.sustainability_tips.map((tip, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-green-600 shrink-0 mt-0.5" />
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>

            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center border border-dashed border-slate-200 rounded-xl bg-white p-8 text-center text-slate-500 min-h-[350px] shadow-sm">
              <FlaskConical className="w-10 h-10 text-slate-350 mb-3" />
              <h4 className="font-bold text-slate-700 text-sm">Nutrient Calendars Awaiting</h4>
              <p className="text-xs text-slate-500 max-w-[280px] mt-1">
                Enter your soil NPK indexes and click "Calculate Fertilizer Program" to generate precision schedules.
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

// Utility helper
function round(value, precision) {
  var multiplier = Math.pow(10, precision || 0);
  return Math.round(value * multiplier) / multiplier;
}
