import React, { useState, useEffect, useRef } from 'react';
import { 
  Bug, 
  Upload, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle2, 
  ShieldAlert, 
  Camera, 
  Leaf,
  Activity
} from 'lucide-react';
import { diseaseAPI } from '../utils/api';

export default function DiseaseScanner() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const data = await diseaseAPI.getHistory();
      setHistory(data);
    } catch (err) {
      console.error('Failed to retrieve disease logs:', err);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setError('');
    }
  };

  const handleUploadSubmit = async (fileToUpload) => {
    const file = fileToUpload || selectedFile;
    if (!file) {
      setError('Please select or generate a leaf image first.');
      return;
    }
    
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const data = await diseaseAPI.scanLeaf(file);
      setResult(data);
      fetchHistory(); // Refresh scan logs
    } catch (err) {
      console.error(err);
      if (!err.response) {
        setError('Cannot connect to disease detection server. Is the backend running?');
      } else if (err.response.status === 404) {
        setError('Disease detection endpoint was not found.');
      } else {
        setError(err.response?.data?.detail || 'Disease detection server encountered an error.');
      }
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    const sev = severity ? severity.toLowerCase() : '';
    if (sev.includes('severe')) return 'bg-rose-50 text-rose-700 border-rose-200';
    if (sev.includes('moderate')) return 'bg-amber-50 text-amber-700 border-amber-200';
    if (sev.includes('low')) return 'bg-green-50 text-green-700 border-green-200';
    if (sev.includes('none')) return 'bg-green-50 text-green-700 border-green-200';
    return 'bg-slate-50 text-slate-700 border-slate-200';
  };

  const getRiskBadge = (severity, status) => {
    if (status === 'non_leaf' || status === 'uncertain') return { label: 'N/A', class: 'bg-slate-50 text-slate-500 border-slate-200' };
    const sev = severity ? severity.toLowerCase() : '';
    if (sev.includes('severe')) return { label: 'High Risk', class: 'bg-rose-50 text-rose-700 border-rose-200' };
    if (sev.includes('moderate')) return { label: 'Medium Risk', class: 'bg-amber-50 text-amber-700 border-amber-200' };
    if (sev.includes('low')) return { label: 'Low Risk', class: 'bg-green-50 text-green-700 border-green-200' };
    if (sev.includes('none')) return { label: 'No Risk', class: 'bg-green-50 text-green-700 border-green-200' };
    return { label: 'Uncertain Risk', class: 'bg-slate-50 text-slate-700 border-slate-200' };
  };

  return (
    <div className="p-8 space-y-6 overflow-y-auto h-[calc(100vh-64px)] bg-slate-50/50">
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Upload Leaf & Analyze */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-6 flex flex-col justify-between shadow-sm">
          <div className="space-y-4">
            <div>
              <span className="text-[9px] font-bold text-green-600 bg-green-50 border border-green-150 px-2 py-0.5 rounded-full uppercase tracking-wider">Step 1</span>
              <h3 className="font-bold text-slate-800 text-sm mt-1.5">Upload Diseased Leaf</h3>
              <p className="text-xs text-slate-500">Capture or select an image of an infected crop leaf to identify pathogen decay</p>
            </div>

            <div 
              onClick={() => fileInputRef.current.click()}
              className="border-2 border-dashed border-slate-200 hover:border-green-500/50 rounded-xl p-6 flex flex-col items-center justify-center gap-4 bg-slate-50/50 hover:bg-slate-50 cursor-pointer transition-colors min-h-[220px]"
            >
              <input 
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="image/*"
                className="hidden"
              />
              {previewUrl ? (
                <img 
                  src={previewUrl} 
                  alt="Leaf Preview" 
                  className="max-h-40 rounded-lg object-contain border border-slate-100"
                />
              ) : (
                <>
                  <div className="p-3 bg-white border border-slate-200 rounded-xl shadow-xs">
                    <Upload className="w-6 h-6 text-slate-400" />
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-semibold text-slate-750">Click to upload leaf photo</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">Supports PNG, JPG, JPEG up to 10MB</p>
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="space-y-3 pt-4 border-t border-slate-100">
            <div>
              <span className="text-[9px] font-bold text-green-600 bg-green-50 border border-green-150 px-2 py-0.5 rounded-full uppercase tracking-wider">Step 2</span>
              <p className="text-[11px] text-slate-500 mt-1.5">Run computer vision diagnostic algorithms on the leaf sample</p>
            </div>
            {error && (
              <p className="text-xs text-rose-600 flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                {error}
              </p>
            )}
            
            <button
              onClick={() => handleUploadSubmit()}
              disabled={loading || !selectedFile}
              className={`w-full font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 text-xs ${
                selectedFile 
                  ? 'bg-green-600 hover:bg-green-700 text-white shadow-sm' 
                  : 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200'
              }`}
            >
              {loading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Analyzing Leaf Image...
                </>
              ) : (
                <>
                  <Camera className="w-3.5 h-3.5" />
                  Analyze Leaf Image
                </>
              )}
            </button>
          </div>
        </div>

        {/* Diagnosis Result Card */}
        <div className="flex flex-col">
          {result ? (
            <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-5 shadow-sm h-full flex flex-col justify-between">
              
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[9px] font-bold text-green-600 bg-green-50 border border-green-150 px-2 py-0.5 rounded-full uppercase tracking-wider">Step 3: Diagnosis Result</span>
                  <h3 className="text-2xl font-bold text-slate-800 capitalize mt-2 flex items-center gap-1.5">
                    {result.disease_detection?.status === 'skipped' || result.disease_detection?.disease === 'None' ? (
                      <>
                        <ShieldAlert className="w-6 h-6 text-amber-500 shrink-0" />
                        <span className="text-slate-700">No Disease Prediction</span>
                      </>
                    ) : result.validation?.prediction_status === "uncertain" ? (
                      <>
                        <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0" />
                        <span>{result.disease_detection.disease.replace(/_/g, ' ')}</span>
                      </>
                    ) : (
                      <>
                        <Bug className="w-5 h-5 text-red-500 shrink-0" />
                        <span>{result.disease_detection.disease.replace(/_/g, ' ')}</span>
                      </>
                    )}
                  </h3>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span className={`text-[10px] font-bold px-2 py-0.5 border rounded-full ${
                    result.disease_detection?.status === 'skipped' || result.disease_detection?.disease === 'None'
                      ? 'bg-slate-50 text-slate-600 border-slate-200'
                      : getSeverityColor(result.disease_detection.severity)
                  }`}>
                    {result.disease_detection?.status === 'skipped' || result.disease_detection?.disease === 'None'
                      ? 'Status: Skipped'
                      : `Severity: ${result.disease_detection.severity ? result.disease_detection.severity.split(' ')[0] : 'None'}`}
                  </span>
                </div>
              </div>

              {/* 1. Image Validation */}
              <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm">
                <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 flex justify-between items-center">
                  <h4 className="text-[10px] font-bold text-slate-700 uppercase tracking-wider">1. Image Validation</h4>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full border ${
                    result.validation.crop_disease_status === 'unsupported_image'
                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                      : result.validation.crop_disease_status === 'crop_uncertain'
                      ? 'bg-amber-50 text-amber-700 border-amber-200'
                      : 'bg-green-50 text-green-700 border-green-200'
                  }`}>
                    {result.validation.crop_disease_status === 'unsupported_image'
                      ? 'Unsupported Image'
                      : result.validation.crop_disease_status === 'crop_uncertain'
                      ? 'Low Confidence Crop'
                      : 'Valid Crop Image'}
                  </span>
                </div>
                <div className="p-4 flex flex-col gap-2">
                  <div className={`text-[11px] font-medium px-3.5 py-2.5 rounded-lg flex items-start gap-2 ${
                    result.validation.crop_disease_status === 'unsupported_image'
                      ? 'text-rose-700 bg-rose-50 border border-rose-200'
                      : result.validation.crop_disease_status === 'crop_uncertain'
                      ? 'text-amber-700 bg-amber-50 border border-amber-200'
                      : 'text-green-700 bg-green-50 border border-green-200'
                  }`}>
                    {result.validation.crop_disease_status === 'unsupported_image' ? (
                      <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
                    ) : result.validation.crop_disease_status === 'crop_uncertain' ? (
                      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-600" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0" />
                    )}
                    <span>
                      {result.validation.validation_message || (result.validation.crop_disease_status === "consistent"
                        ? "Crop and Disease Compatibility: Verified"
                        : result.validation.crop_disease_status === "crop_uncertain"
                        ? "Crop identification confidence is low; disease diagnosis was skipped."
                        : "The uploaded image does not appear to contain a supported crop or plant leaf.")}
                    </span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* 2. Crop Identification */}
                <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm">
                  <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 flex justify-between items-center">
                    <h4 className="text-[10px] font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1"><Leaf className="w-3 h-3"/> 2. Crop Identification</h4>
                  </div>
                  <div className="p-4 flex flex-col gap-2">
                    {result.crop_identification?.status === 'model_unavailable' || result.crop_identification?.crop === 'Unavailable' ? (
                      <div className="text-[11px] font-medium px-3.5 py-2.5 rounded-lg flex items-start gap-2 text-rose-700 bg-rose-50 border border-rose-200">
                        <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
                        <span>Crop identification model is unavailable.</span>
                      </div>
                    ) : (
                      <>
                        <div>
                          <span className="block text-[10px] uppercase font-bold text-slate-400 mb-0.5">Crop</span>
                          <span className={`font-semibold text-sm capitalize ${result.crop_identification.crop === 'Unknown' ? 'text-amber-700' : 'text-slate-800'}`}>
                            {result.crop_identification.crop}
                          </span>
                        </div>
                        <div>
                          <span className="block text-[10px] uppercase font-bold text-slate-400 mb-0.5">Model</span>
                          <span className="text-xs text-slate-600">{result.crop_identification.model}</span>
                        </div>
                        <div>
                          <span className="block text-[10px] uppercase font-bold text-slate-400 mb-0.5">Confidence</span>
                          <span className={`font-semibold text-sm ${
                            result.crop_identification.confidence >= 0.70 ? 'text-green-600' : 'text-amber-600'
                          }`}>
                            {result.crop_identification.confidence > 0 
                              ? `${(result.crop_identification.confidence * 100).toFixed(1)}%` 
                              : '—'}
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* 3. Disease Detection */}
                <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm">
                  <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 flex justify-between items-center">
                    <h4 className="text-[10px] font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1"><Bug className="w-3 h-3"/> 3. Disease Detection</h4>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${
                      result.disease_detection?.status === 'skipped' || result.disease_detection?.disease === 'None'
                        ? 'bg-slate-100 text-slate-600'
                        : 'bg-green-100 text-green-700'
                    }`}>
                      {result.disease_detection?.status === 'skipped' || result.disease_detection?.disease === 'None'
                        ? 'Not Performed'
                        : 'Executed'}
                    </span>
                  </div>
                  <div className="p-4 flex flex-col gap-2">
                    {result.disease_detection?.status === 'skipped' || result.disease_detection?.disease === 'None' ? (
                      <>
                        <div>
                          <span className="block text-[10px] uppercase font-bold text-slate-400 mb-0.5">Disease</span>
                          <span className="font-semibold text-slate-500 text-sm">—</span>
                        </div>
                        <div>
                          <span className="block text-[10px] uppercase font-bold text-slate-400 mb-0.5">Model</span>
                          <span className="text-xs text-slate-500">YOLO11 (Skipped)</span>
                        </div>
                        <div>
                          <span className="block text-[10px] uppercase font-bold text-slate-400 mb-0.5">Confidence</span>
                          <span className="font-semibold text-slate-500 text-sm">—</span>
                        </div>
                      </>
                    ) : (
                      <>
                        <div>
                          <span className="block text-[10px] uppercase font-bold text-slate-400 mb-0.5">Disease</span>
                          <span className="font-semibold text-slate-800 text-sm capitalize">{result.disease_detection.disease.replace(/_/g, ' ')}</span>
                        </div>
                        <div>
                          <span className="block text-[10px] uppercase font-bold text-slate-400 mb-0.5">Model</span>
                          <span className="text-xs text-slate-600">{result.disease_detection.model}</span>
                        </div>
                        <div>
                          <span className="block text-[10px] uppercase font-bold text-slate-400 mb-0.5">Confidence</span>
                          <span className={`font-semibold text-sm ${result.disease_detection.confidence > 0.8 ? 'text-green-600' : 'text-amber-600'}`}>
                            {(result.disease_detection.confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Top-5 Predictions Breakdown if available */}
              {result.disease_detection?.status !== 'skipped' && result.disease_detection?.top5 && result.disease_detection.top5.length > 1 && (
                <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm">
                  <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 flex justify-between items-center">
                    <h4 className="text-[10px] font-bold text-slate-700 uppercase tracking-wider">Top Probable Disease Matches</h4>
                    <span className="text-[9px] text-slate-500 font-bold">Top-5 Ranking</span>
                  </div>
                  <div className="p-3 space-y-2">
                    {result.disease_detection.top5.map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs">
                        <span className="font-medium text-slate-700 truncate max-w-[70%]">{idx + 1}. {item.disease}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-20 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                            <div className="bg-green-600 h-full rounded-full" style={{ width: `${Math.min(100, item.confidence * 100)}%` }}></div>
                          </div>
                          <span className="font-bold text-slate-600 text-[11px] w-10 text-right">{(item.confidence * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Disease Model Performance Metrics */}
              {result.model_performance && result.model_performance.disease && (
                <div className="border border-indigo-200 rounded-lg overflow-hidden bg-white shadow-sm">
                  <div className="bg-indigo-50 px-4 py-2 border-b border-indigo-100 flex justify-between items-center">
                    <h4 className="text-[10px] font-bold text-indigo-800 uppercase tracking-wider flex items-center gap-1"><Activity className="w-3 h-3"/> YOLO11 Validation Metrics</h4>
                    <span className="text-[9px] text-indigo-500 font-bold px-1.5 py-0.5 bg-indigo-100 rounded-full">{result.model_performance.disease.training_epochs || 50} Epochs</span>
                  </div>
                  <div className="p-4 grid grid-cols-4 gap-2">
                    <div className="text-center">
                      <span className="block text-[9px] uppercase font-bold text-slate-400 mb-1">Top-1 Acc</span>
                      <span className="font-semibold text-slate-700 text-xs">{((result.model_performance.disease.top1_accuracy ?? result.model_performance.disease.precision) * 100).toFixed(2)}%</span>
                    </div>
                    <div className="text-center">
                      <span className="block text-[9px] uppercase font-bold text-slate-400 mb-1">Top-5 Acc</span>
                      <span className="font-semibold text-slate-700 text-xs">{((result.model_performance.disease.top5_accuracy ?? result.model_performance.disease.recall) * 100).toFixed(2)}%</span>
                    </div>
                    <div className="text-center">
                      <span className="block text-[9px] uppercase font-bold text-slate-400 mb-1">Classes</span>
                      <span className="font-semibold text-slate-700 text-xs">{result.model_performance.disease.num_classes || 86}</span>
                    </div>
                    <div className="text-center">
                      <span className="block text-[9px] uppercase font-bold text-slate-400 mb-1">Architecture</span>
                      <span className="font-semibold text-slate-700 text-xs">YOLO11</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Crop Model Performance Metrics */}
              {result.model_performance && result.model_performance.crop && result.model_performance.crop.available !== false && (
                <div className="border border-green-200 rounded-lg overflow-hidden bg-white shadow-sm mt-4">
                  <div className="bg-green-50 px-4 py-2 border-b border-green-100 flex justify-between items-center">
                    <h4 className="text-[10px] font-bold text-green-800 uppercase tracking-wider flex items-center gap-1"><Activity className="w-3 h-3"/> Crop Model Metrics</h4>
                    <span className="text-[9px] text-green-600 font-bold px-1.5 py-0.5 bg-green-100 rounded-full">{result.model_performance.crop.num_classes || 19} Classes</span>
                  </div>
                  <div className="p-4 grid grid-cols-4 gap-2">
                    <div className="text-center">
                      <span className="block text-[9px] uppercase font-bold text-slate-400 mb-1">Accuracy</span>
                      <span className="font-semibold text-slate-700 text-xs">{(result.model_performance.crop.accuracy * 100).toFixed(2)}%</span>
                    </div>
                    <div className="text-center">
                      <span className="block text-[9px] uppercase font-bold text-slate-400 mb-1">Precision</span>
                      <span className="font-semibold text-slate-700 text-xs">{(result.model_performance.crop.precision * 100).toFixed(2)}%</span>
                    </div>
                    <div className="text-center">
                      <span className="block text-[9px] uppercase font-bold text-slate-400 mb-1">Recall</span>
                      <span className="font-semibold text-slate-700 text-xs">{(result.model_performance.crop.recall * 100).toFixed(2)}%</span>
                    </div>
                    <div className="text-center">
                      <span className="block text-[9px] uppercase font-bold text-slate-400 mb-1">F1-Score</span>
                      <span className="font-semibold text-slate-700 text-xs">{(result.model_performance.crop.f1 * 100).toFixed(2)}%</span>
                    </div>
                  </div>
                </div>
              )}

              {/* DISEASE MANAGEMENT */}
              {result.disease_management && result.disease_management.available ? (
                <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm">
                  <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 flex justify-between items-center">
                    <h4 className="text-[10px] font-bold text-slate-700 uppercase tracking-wider">Disease Management</h4>
                  </div>
                  <div className="p-4 space-y-4 max-h-48 overflow-y-auto">
                    {result.disease_management.immediate_actions?.length > 0 && (
                      <div>
                        <h5 className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1.5">Immediate Actions</h5>
                        <ul className="list-disc pl-4 text-xs text-slate-700 space-y-1">
                          {result.disease_management.immediate_actions.map((item, idx) => <li key={idx}>{item}</li>)}
                        </ul>
                      </div>
                    )}
                    {result.disease_management.cultural_management?.length > 0 && (
                      <div>
                        <h5 className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1.5">Cultural Management</h5>
                        <ul className="list-disc pl-4 text-xs text-slate-700 space-y-1">
                          {result.disease_management.cultural_management.map((item, idx) => <li key={idx}>{item}</li>)}
                        </ul>
                      </div>
                    )}
                    {result.disease_management.biological_management?.length > 0 && (
                      <div className="bg-emerald-50 border border-emerald-100 rounded-lg p-3">
                        <h5 className="text-[10px] uppercase font-bold text-emerald-700 tracking-wider mb-1.5">Biological Management</h5>
                        <ul className="list-disc pl-4 text-xs text-emerald-900 space-y-1">
                          {result.disease_management.biological_management.map((item, idx) => <li key={idx}>{item}</li>)}
                        </ul>
                      </div>
                    )}
                    {result.disease_management.chemical_management?.length > 0 && (
                      <div className="bg-red-50 border border-red-100 rounded-lg p-3">
                        <h5 className="text-[10px] uppercase font-bold text-red-700 tracking-wider mb-1.5">Chemical Management</h5>
                        <ul className="list-disc pl-4 text-xs text-red-900 space-y-1">
                          {result.disease_management.chemical_management.map((item, idx) => <li key={idx}>{item}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ) : result.disease_management && !result.disease_management.available ? (
                <div className="border border-slate-200 rounded-lg overflow-hidden bg-slate-50 shadow-sm p-5 text-center flex flex-col items-center justify-center">
                  <ShieldAlert className="w-8 h-8 text-slate-400 mb-2" />
                  <h4 className="font-bold text-slate-700 text-sm">Treatment Recommendations Disabled</h4>
                  <p className="text-xs text-slate-500 mt-1 max-w-[90%] mx-auto">
                    {result.validation?.crop_disease_status === "mismatch" 
                      ? "The detected disease does not match the identified crop. We cannot safely provide treatment options." 
                      : "Crop could not be confidently identified, so crop-disease compatibility validation was skipped."}
                  </p>
                </div>
              ) : null}

            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center border border-dashed border-slate-200 rounded-xl bg-white p-8 text-center text-slate-500 min-h-[350px] shadow-sm">
              <Bug className="w-10 h-10 text-slate-300 mb-3" />
              <h4 className="font-bold text-slate-700 text-sm">Diagnosis Result Awaiting</h4>
              <p className="text-xs text-slate-500 max-w-[280px] mt-1">
                Upload a picture of a leaf to compute disease classifications.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* History Log table */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-sm">
        <div>
          <h3 className="font-bold text-slate-800 text-sm">Scan Diagnosis History Log</h3>
          <p className="text-xs text-slate-500">Archived plant disease scans stored under your Digital Twin</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pt-2">
          {history.length > 0 ? (
            history.map((record) => (
              <div key={record.id} className="bg-white border border-slate-200 rounded-xl p-4 flex gap-4 hover:border-slate-300 transition-colors shadow-xs">
                <img 
                  src={`http://localhost:8001${record.image_path}`} 
                  alt="Scanned leaf"
                  className="w-16 h-16 rounded-lg object-cover border border-slate-100 shrink-0 bg-slate-50"
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
                <div className="space-y-1 min-w-0">
                  <h4 className="text-xs font-bold text-slate-850 truncate capitalize">{record.disease_detection?.disease || 'Unknown'}</h4>
                  <p className="text-[10px] text-slate-500">
                    {new Date(record.scanned_at).toLocaleDateString()}
                  </p>
                  <div className="flex gap-2 mt-1">
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full border ${getSeverityColor(record.disease_detection?.severity)}`}>
                      {record.disease_detection?.severity ? record.disease_detection.severity.split(' ')[0] : 'Unknown'}
                    </span>
                    <span className="text-[9px] font-semibold px-1.5 py-0.5 bg-slate-50 border border-slate-200 text-slate-600 rounded-full">
                      Verified
                    </span>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full py-6 text-center text-slate-500 text-xs">
              No historical diagnosis scans logged. Make your first scan to populate this board.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
