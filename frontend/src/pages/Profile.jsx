import React, { useState, useEffect } from 'react';
import { User, MapPin, Layers, Droplet, Wind, Sparkles, Save, CheckCircle2, History } from 'lucide-react';
import { twinAPI } from '../utils/api';

export default function Profile() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [profileData, setProfileData] = useState(null);
  
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

          {/* Historical Crops logged */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-sm">
            <h4 className="font-bold text-slate-800 text-sm flex items-center gap-1.5">
              <History className="w-4 h-4 text-slate-400" />
              Historical Harvest Logs
            </h4>
            
            {profileData?.crop_history?.length === 0 ? (
              <p className="text-xs text-slate-500">No historical crops logged yet.</p>
            ) : (
              <div className="border border-slate-100 rounded-lg overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-500 font-bold uppercase tracking-wider border-b border-slate-100">
                    <tr>
                      <th className="px-4 py-2">Crop</th>
                      <th className="px-4 py-2">Yield</th>
                      <th className="px-4 py-2">Revenue</th>
                      <th className="px-4 py-2">Season</th>
                      <th className="px-4 py-2">Year</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {profileData?.crop_history?.map((h, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/50">
                        <td className="px-4 py-2 font-semibold capitalize">{h.crop}</td>
                        <td className="px-4 py-2">{h.yield.toLocaleString()} kg</td>
                        <td className="px-4 py-2 text-green-650 font-medium">₹{h.revenue ? h.revenue.toLocaleString() : 'N/A'}</td>
                        <td className="px-4 py-2">{h.season}</td>
                        <td className="px-4 py-2">{h.year}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
