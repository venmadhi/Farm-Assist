import React from 'react';
import { MapPin, Sprout, Droplets, Map, Thermometer, X } from 'lucide-react';

export default function ChatContextPanel({ farmerProfile }) {
  if (!farmerProfile) return null;
  
  const farm = farmerProfile.farm || {};
  const district = farm.location_district || farmerProfile.location_district || 'Unknown Location';
  const soilType = farm.soil_type || farmerProfile.soil_type || 'Unknown Soil';
  
  return (
    <div className="w-full lg:w-64 bg-white border-l border-slate-200 p-4 flex flex-col gap-4 overflow-y-auto hidden lg:flex">
      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Farm Context</h3>
      
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 p-2 rounded-lg bg-slate-50 border border-slate-100">
          <MapPin className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-medium text-slate-700 truncate">{district}</span>
        </div>
        
        <div className="flex items-center gap-2 p-2 rounded-lg bg-slate-50 border border-slate-100">
          <Map className="w-4 h-4 text-orange-400" />
          <span className="text-xs font-medium text-slate-700 truncate">{soilType} Soil</span>
        </div>

        {farm.land_area_acres && (
          <div className="flex items-center gap-2 p-2 rounded-lg bg-slate-50 border border-slate-100">
            <Sprout className="w-4 h-4 text-green-500" />
            <span className="text-xs font-medium text-slate-700 truncate">{farm.land_area_acres} Acres</span>
          </div>
        )}
        
        {farm.irrigation_type && (
          <div className="flex items-center gap-2 p-2 rounded-lg bg-slate-50 border border-slate-100">
            <Droplets className="w-4 h-4 text-blue-500" />
            <span className="text-xs font-medium text-slate-700 truncate capitalize">{farm.irrigation_type.replace('_', ' ')}</span>
          </div>
        )}
      </div>

      <div className="mt-4 p-3 bg-green-50 rounded-xl border border-green-100">
        <p className="text-[10px] text-green-800 leading-relaxed">
          FarmAssist uses this context automatically to personalize recommendations. You don't need to repeat this information in your chats!
        </p>
      </div>
    </div>
  );
}
