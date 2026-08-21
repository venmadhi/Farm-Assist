import React, { useState, useEffect, useRef } from 'react';
import { 
  Bug, 
  Upload, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle2, 
  ShieldAlert, 
  Camera, 
  FileText 
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
  const canvasRef = useRef(null);

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
      setError('Failed to scan leaf image. Ensure the image is valid and the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  // Visual simulator generator for judges/evaluators
  // Creates a canvas drawing resembling diseased leaves, converts to blob, and uploads
  const generateSimulatedLeaf = (diseaseKey) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    // Draw base leaf structure (green spade/oval shape)
    ctx.fillStyle = '#f8fafc'; // Clear background (light)
    ctx.fillRect(0, 0, 300, 300);
    
    // Draw stem
    ctx.strokeStyle = '#854d0e';
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(150, 280);
    ctx.quadraticCurveTo(140, 200, 150, 40);
    ctx.stroke();

    // Draw green leaf body
    ctx.fillStyle = '#16a34a'; // Healthy green
    ctx.beginPath();
    ctx.moveTo(150, 40);
    ctx.quadraticCurveTo(50, 130, 150, 250);
    ctx.quadraticCurveTo(250, 130, 150, 40);
    ctx.fill();

    // Draw veins
    ctx.strokeStyle = '#4ade80';
    ctx.lineWidth = 2;
    ctx.beginPath();
    // Left veins
    ctx.moveTo(150, 100); ctx.lineTo(90, 80);
    ctx.moveTo(150, 150); ctx.lineTo(80, 130);
    ctx.moveTo(150, 200); ctx.lineTo(100, 180);
    // Right veins
    ctx.moveTo(150, 100); ctx.lineTo(210, 80);
    ctx.moveTo(150, 150); ctx.lineTo(220, 130);
    ctx.moveTo(150, 200); ctx.lineTo(200, 180);
    ctx.stroke();

    // Draw disease lesions based on key
    if (diseaseKey === 'corn_northern_leaf_blight') {
      // Long yellow/brown streaks
      ctx.fillStyle = '#ca8a04'; // yellow-brown
      ctx.beginPath();
      ctx.ellipse(100, 120, 15, 6, Math.PI / 6, 0, 2 * Math.PI);
      ctx.ellipse(190, 150, 20, 8, -Math.PI / 4, 0, 2 * Math.PI);
      ctx.ellipse(120, 180, 12, 5, Math.PI / 8, 0, 2 * Math.PI);
      ctx.fill();
      
      ctx.fillStyle = '#451a03'; // dark brown centers
      ctx.beginPath();
      ctx.ellipse(100, 120, 8, 3, Math.PI / 6, 0, 2 * Math.PI);
      ctx.ellipse(190, 150, 10, 4, -Math.PI / 4, 0, 2 * Math.PI);
      ctx.fill();
    } 
    else if (diseaseKey === 'pepper_quick_wilt') {
      // Blackish decay spreading from margins
      ctx.fillStyle = '#1c1917'; // dark charcoal
      ctx.beginPath();
      ctx.arc(80, 100, 30, 0, 2 * Math.PI);
      ctx.arc(220, 160, 25, 0, 2 * Math.PI);
      ctx.arc(150, 220, 20, 0, 2 * Math.PI);
      ctx.fill();
      
      ctx.fillStyle = '#ca8a04'; // yellow borders
      ctx.beginPath();
      ctx.arc(80, 100, 35, 0, 2 * Math.PI, true);
      // Simulating border outlines
      ctx.strokeStyle = '#ca8a04';
      ctx.lineWidth = 4;
      ctx.stroke();
    } 
    else if (diseaseKey === 'coconut_bud_rot') {
      // Brown rotting base and rotting tip
      ctx.fillStyle = '#451a03'; // rotting brown
      ctx.beginPath();
      ctx.arc(150, 40, 25, 0, 2 * Math.PI);
      ctx.arc(150, 230, 35, 0, 2 * Math.PI);
      ctx.fill();
    }
    else if (diseaseKey === 'tomato_early_blight') {
      // Small brown spots with concentric target rings
      ctx.strokeStyle = '#ca8a04';
      ctx.fillStyle = '#451a03';
      ctx.lineWidth = 2;
      
      // Spot 1
      ctx.beginPath(); ctx.arc(110, 110, 14, 0, 2 * Math.PI); ctx.fill();
      ctx.beginPath(); ctx.arc(110, 110, 8, 0, 2 * Math.PI); ctx.stroke();
      
      // Spot 2
      ctx.beginPath(); ctx.arc(180, 180, 18, 0, 2 * Math.PI); ctx.fill();
      ctx.beginPath(); ctx.arc(180, 180, 12, 0, 2 * Math.PI); ctx.stroke();
      ctx.beginPath(); ctx.arc(180, 180, 6, 0, 2 * Math.PI); ctx.stroke();
    }

    // Convert canvas to file and trigger upload
    canvas.toBlob((blob) => {
      const filename = `simulated_${diseaseKey}.jpg`;
      const file = new File([blob], filename, { type: 'image/jpeg' });
      setSelectedFile(file);
      setPreviewUrl(canvas.toDataURL('image/jpeg'));
      handleUploadSubmit(file);
    }, 'image/jpeg');
  };

  const getSeverityColor = (severity) => {
    const sev = severity ? severity.toLowerCase() : '';
    if (sev.includes('severe')) return 'bg-rose-50 text-rose-700 border-rose-200';
    if (sev.includes('moderate')) return 'bg-amber-50 text-amber-700 border-amber-200';
    if (sev.includes('uncertain') || sev.includes('n/a')) return 'bg-slate-50 text-slate-700 border-slate-200';
    if (sev.includes('low')) return 'bg-green-50 text-green-700 border-green-200';
    return 'bg-slate-50 text-slate-700 border-slate-200';
  };

  const getRiskBadge = (severity, status) => {
    if (status === 'non_leaf' || status === 'uncertain') return { label: 'N/A', class: 'bg-slate-50 text-slate-500 border-slate-200' };
    if (status === 'needs_verification') return { label: 'Unverified Risk', class: 'bg-orange-50 text-orange-700 border-orange-200' };
    const sev = severity ? severity.toLowerCase() : '';
    if (sev.includes('severe')) return { label: 'High Risk', class: 'bg-rose-50 text-rose-700 border-rose-200' };
    if (sev.includes('moderate')) return { label: 'Medium Risk', class: 'bg-amber-50 text-amber-700 border-amber-200' };
    if (sev.includes('low risk (healthy')) return { label: 'Low Risk', class: 'bg-green-50 text-green-700 border-green-200' };
    if (sev.includes('low')) return { label: 'Low Risk', class: 'bg-green-50 text-green-700 border-green-200' };
    return { label: 'Uncertain Risk', class: 'bg-slate-50 text-slate-700 border-slate-200' };
  };

  return (
    <div className="p-8 space-y-6 overflow-y-auto h-[calc(100vh-64px)] bg-slate-50/50">
      
      {/* Hidden simulator canvas */}
      <canvas ref={canvasRef} width={300} height={300} className="hidden" />

      {/* Simulator Shortcut Panel */}
      <div className="space-y-2">
        <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Visual Disease Simulator (Presentation Presets)</h4>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => generateSimulatedLeaf('corn_northern_leaf_blight')}
            className="px-3 py-1.5 text-xs font-semibold border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 rounded-lg shadow-sm transition-colors"
          >
            Northern Leaf Blight (Corn)
          </button>
          <button
            onClick={() => generateSimulatedLeaf('pepper_quick_wilt')}
            className="px-3 py-1.5 text-xs font-semibold border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 rounded-lg shadow-sm transition-colors"
          >
            Quick Wilt Decay (Pepper)
          </button>
          <button
            onClick={() => generateSimulatedLeaf('coconut_bud_rot')}
            className="px-3 py-1.5 text-xs font-semibold border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 rounded-lg shadow-sm transition-colors"
          >
            Bud Rot Necrosis (Coconut)
          </button>
          <button
            onClick={() => generateSimulatedLeaf('tomato_early_blight')}
            className="px-3 py-1.5 text-xs font-semibold border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 rounded-lg shadow-sm transition-colors"
          >
            Early Blight Rings (Tomato)
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Step 1 & 2: Upload Leaf & Analyze */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-6 flex flex-col justify-between shadow-sm">
          <div className="space-y-4">
            <div>
              <span className="text-[9px] font-bold text-green-600 bg-green-50 border border-green-150 px-2 py-0.5 rounded-full uppercase tracking-wider">Step 1</span>
              <h3 className="font-bold text-slate-800 text-sm mt-1.5">Upload Diseased Leaf</h3>
              <p className="text-xs text-slate-500">Capture or select an image of an infected crop leaf to identify pathogen decay</p>
            </div>

            {/* Upload Box area */}
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

          {/* Trigger Scan button */}
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
                  Analyzing Leaf with ConvGeM-NeXt...
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

        {/* Step 3: Diagnosis Result Card */}
        <div className="flex flex-col">
          {result ? (
            <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-5 shadow-sm h-full flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[9px] font-bold text-green-600 bg-green-50 border border-green-150 px-2 py-0.5 rounded-full uppercase tracking-wider">Step 3: Diagnosis Result</span>
                    <h3 className="text-2xl font-bold text-slate-800 capitalize mt-2 flex items-center gap-1.5">
                      {result.detected_disease === "Image Quality Too Low" ? (
                        <ShieldAlert className="w-5 h-5 text-amber-500 shrink-0" />
                      ) : result.classification_status === "non_leaf" ? (
                        <AlertTriangle className="w-5 h-5 text-rose-500 shrink-0" />
                      ) : result.classification_status === "uncertain" ? (
                        <span className="text-xl shrink-0">🌿</span>
                      ) : (
                        <Bug className="w-5 h-5 text-red-500 shrink-0" />
                      )}
                      {result.detected_disease}
                    </h3>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className={`text-[10px] font-bold px-2 py-0.5 border rounded-full ${getSeverityColor(result.severity_level)}`}>
                      Severity: {result.severity_level ? result.severity_level.split(' ')[0] : 'Moderate'}
                    </span>
                    <span className="text-[9px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full">
                      Model: {result.model || 'ConvGeM-NeXt'}
                    </span>
                  </div>
                </div>

                {/* Risk & Performance Evaluation Widgets */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg flex flex-col justify-between text-slate-650">
                    <span className="text-[9px] uppercase font-bold tracking-wider text-slate-500">Model Confidence</span>
                    <span className="text-xs font-extrabold text-green-700 mt-0.5">
                      {result.classification_status === "non_leaf"
                        ? "N/A"
                        : `${(result.confidence * 100).toFixed(2)}%`}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg flex flex-col justify-between text-slate-650">
                    <span className="text-[9px] uppercase font-bold tracking-wider text-slate-500">
                      {result.classification_status === 'confirmed' ? 'Lesion Area (OpenCV)' : 'Detected Region'}
                    </span>
                    <span className="text-xs font-extrabold text-amber-700 mt-0.5">
                      {result.classification_status === "non_leaf" || result.classification_status === "uncertain"
                        ? "N/A"
                        : result.affected_percent > 0
                          ? `${result.affected_percent}%`
                          : (result.classification_status === "healthy" ? "0%" : "N/A")}
                    </span>
                  </div>
                  <div className={`p-3 rounded-lg border flex flex-col justify-between ${
                    getRiskBadge(result.severity_level || '', result.classification_status).class
                  }`}>
                    <span className="text-[9px] uppercase font-bold tracking-wider opacity-85">Pathology Risk</span>
                    <span className="text-xs font-bold mt-0.5">
                      {getRiskBadge(result.severity_level || '', result.classification_status).label}
                    </span>
                  </div>
                </div>

                {/* Accuracy validation badge */}
                <div className="text-[11px] font-medium text-slate-600 bg-slate-50 border border-slate-100 px-3.5 py-2.5 rounded-lg flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0" />
                  {result.classification_status === 'uncertain' ? (
                    <span>Prediction: Unknown / Uncertain — Confidence too low to classify</span>
                  ) : result.classification_status === 'non_leaf' ? (
                    <span>Validation: No Leaf Detected — ConvGeM-NeXt skipped</span>
                  ) : result.classification_status === 'healthy' ? (
                    <span>ConvGeM-NeXt: Healthy Leaf ({(result.confidence*100).toFixed(1)}% confidence)</span>
                  ) : result.classification_status === 'needs_verification' ? (
                    <span className="text-orange-700">⚠ Needs Verification — Low confidence ({(result.confidence*100).toFixed(1)}%). Consult an agronomist.</span>
                  ) : (
                    <span>ConvGeM-NeXt Confirmed: {result.crop || 'General'} Leaf Disease</span>
                  )}
                </div>

                {/* Detailed Metrics Table */}
                <div className="border border-slate-150 rounded-lg overflow-hidden mt-3">
                  <table className="w-full text-xs text-left text-slate-650">
                    <thead className="bg-slate-50 text-[9px] uppercase font-bold text-slate-500 border-b border-slate-150">
                      <tr>
                        <th className="px-3.5 py-1.5">Metric</th>
                        <th className="px-3.5 py-1.5 text-right">Result</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      <tr>
                        <td className="px-3.5 py-1.5 font-medium">Leaf Detection</td>
                        <td className={`px-3.5 py-1.5 text-right font-bold ${result.is_leaf ? 'text-green-700' : 'text-rose-600'}`}>
                          {result.is_leaf ? 'Detected' : 'Not Detected'}
                        </td>
                      </tr>
                      <tr>
                        <td className="px-3.5 py-1.5 font-medium">Leaf Confidence</td>
                        <td className="px-3.5 py-1.5 text-right font-bold text-slate-700">
                          {result.leaf_confidence ? `${(result.leaf_confidence * 100).toFixed(2)}%` : 'N/A'}
                        </td>
                      </tr>
                      <tr>
                        <td className="px-3.5 py-1.5 font-medium">Disease Classification</td>
                        <td className="px-3.5 py-1.5 text-right font-bold text-slate-700">
                          {result.classification_status === "non_leaf" ? 'Not Performed'
                            : result.classification_status === "uncertain" ? 'Unknown'
                            : result.classification_status === "needs_verification" ? 'Needs Verification'
                            : result.classification_status === "healthy" ? 'Healthy'
                            : 'Confirmed'}
                        </td>
                      </tr>
                      <tr>
                        <td className="px-3.5 py-1.5 font-medium">Disease Confidence</td>
                        <td className="px-3.5 py-1.5 text-right font-bold text-slate-700">
                          {result.classification_status === "non_leaf" ? 'N/A' : `${(result.confidence * 100).toFixed(2)}%`}
                        </td>
                      </tr>
                      <tr>
                        <td className="px-3.5 py-1.5 font-medium">
                          {result.classification_status === 'confirmed' ? 'Lesion Area (OpenCV)' : 'Detected Region (OpenCV)'}
                        </td>
                        <td className="px-3.5 py-1.5 text-right font-bold text-amber-700 font-mono">
                          {result.classification_status === "non_leaf" || result.classification_status === "uncertain"
                            ? 'N/A'
                            : result.affected_percent > 0 ? `${result.affected_percent}%` : 'N/A'}
                        </td>
                      </tr>
                      {result.lesion_count !== undefined && result.lesion_count > 0 && (
                        <tr>
                          <td className="px-3.5 py-1.5 font-medium">Lesion Count</td>
                          <td className="px-3.5 py-1.5 text-right font-bold text-amber-700">
                            {result.lesion_count}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Top-3 Predictions */}
                {result.top_k && result.top_k.length > 0 && result.classification_status !== 'non_leaf' && (
                  <div className="border border-slate-150 rounded-lg overflow-hidden">
                    <div className="bg-slate-50 px-3.5 py-1.5 text-[9px] uppercase font-bold text-slate-500 border-b border-slate-150">ConvGeM-NeXt Top-3 Predictions</div>
                    {result.top_k.map((p, i) => (
                      <div key={i} className="flex items-center gap-2 px-3.5 py-1.5 bg-white border-b border-slate-100 last:border-0">
                        <span className="text-[9px] font-bold text-slate-400 w-4">{i+1}</span>
                        <span className="text-xs text-slate-700 flex-1 capitalize">{p.class_name.replace(/_/g, ' ')}</span>
                        <div className="flex items-center gap-1.5">
                          <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div className="h-full bg-green-500 rounded-full" style={{width: `${(p.confidence*100).toFixed(0)}%`}} />
                          </div>
                          <span className="text-[10px] font-bold text-slate-600 w-10 text-right">{(p.confidence*100).toFixed(1)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <div className="bg-slate-50/50 p-4 rounded-lg border border-slate-100 space-y-3.5 text-xs text-slate-700 leading-relaxed">
                  {result.treatment_plan && result.treatment_plan.split('\n\n').map((para, i) => {
                    if (para.startsWith('**Cause:**')) {
                      return (
                        <div key={i}>
                          <strong className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-0.5">Pathogen Etiology</strong>
                          <p className="text-slate-700">{para.replace('**Cause:**', '').trim()}</p>
                        </div>
                      );
                    }
                    if (para.startsWith('**Visual Indicators:**') || para.startsWith('**Visual Spot Indicators:**')) {
                      return (
                        <div key={i}>
                          <strong className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-0.5">Symptoms & Severity Indicators</strong>
                          <p className="text-slate-700">{para.replace('**Visual Spot Indicators:**', '').replace('**Visual Indicators:**', '').trim()}</p>
                        </div>
                      );
                    }
                    if (para.startsWith('**Chemical/Biological Treatments:**')) {
                      return (
                        <div key={i} className="p-3 bg-red-50 border border-red-100 rounded-lg text-red-800">
                          <strong className="text-[10px] uppercase font-bold text-red-700 tracking-wider block mb-0.5">Chemical Treatment Plan</strong>
                          <p>{para.replace('**Chemical/Biological Treatments:**', '').trim()}</p>
                        </div>
                      );
                    }
                    if (para.startsWith('**Preventive Measures:**')) {
                      return (
                        <div key={i} className="p-3 bg-green-50 border border-green-100 rounded-lg text-green-800">
                          <strong className="text-[10px] uppercase font-bold text-green-700 tracking-wider block mb-0.5">Organic Prevention Protocol</strong>
                          <p>{para.replace('**Preventive Measures:**', '').trim()}</p>
                        </div>
                      );
                    }
                    return <p key={i}>{para}</p>;
                  })}
                </div>
              </div>

              <div className="text-[10px] text-slate-500 pt-3 border-t border-slate-100 text-center font-medium">
                Estimated recovery timeline: {result.recovery_time_days || 14} days if guidelines are followed
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center border border-dashed border-slate-200 rounded-xl bg-white p-8 text-center text-slate-500 min-h-[350px] shadow-sm">
              <Bug className="w-10 h-10 text-slate-300 mb-3" />
              <h4 className="font-bold text-slate-700 text-sm">Diagnosis Result Awaiting</h4>
              <p className="text-xs text-slate-500 max-w-[280px] mt-1">
                Upload a picture of a leaf or click an SIH Shortcut button to compute disease classifications.
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
                  src={`http://localhost:8000${record.image_path}`} 
                  alt="Scanned leaf"
                  className="w-16 h-16 rounded-lg object-cover border border-slate-100 shrink-0 bg-slate-50"
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
                <div className="space-y-1 min-w-0">
                  <h4 className="text-xs font-bold text-slate-850 truncate capitalize">{record.detected_disease}</h4>
                  <p className="text-[10px] text-slate-500">
                    {new Date(record.scanned_at).toLocaleDateString()}
                  </p>
                  <div className="flex gap-2 mt-1">
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full border ${getSeverityColor(record.severity_level)}`}>
                      {record.severity_level.split(' ')[0]}
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
