import { useState } from 'react';

const RED_FLAG_SYMPTOMS = [
  { key: "chest_pain", label: "Chest Pain" },
  { key: "severe_bleeding", label: "Severe Bleeding" },
  { key: "stroke_signs", label: "Stroke Signs (FAST)" },
  { key: "not_breathing", label: "Not Breathing / Severe Apnea" },
  { key: "unresponsive", label: "Unresponsive / Altered Mental State" },
  { key: "anaphylaxis", label: "Anaphylaxis / Severe Allergic Reaction" },
  { key: "seizure_active", label: "Active Seizure" },
  { key: "severe_burn", label: "Severe Burn" }
];

const URGENT_SYMPTOMS = [
  { key: "high_fever", label: "High Fever" },
  { key: "fracture", label: "Suspected Fracture" },
  { key: "moderate_bleeding", label: "Moderate Bleeding" },
  { key: "persistent_vomiting", label: "Persistent Vomiting" },
  { key: "dehydration", label: "Severe Dehydration" },
  { key: "abdominal_pain_severe", label: "Severe Abdominal Pain" },
  { key: "breathing_difficulty", label: "Difficulty Breathing" }
];

const MINOR_SYMPTOMS = [
  { key: "sprained_ankle", label: "Sprained Ankle / Minor Trauma" },
  { key: "minor_cut", label: "Minor Cut / Laceration" },
  { key: "mild_cough", label: "Mild Cough / Cold Symptoms" },
  { key: "skin_rash", label: "Skin Rash / Mild Irritation" },
  { key: "sore_throat", label: "Sore Throat" },
  { key: "earache", label: "Earache / Minor Discomfort" }
];

const UpdatedTriageForm = ({ onSubmitPatient }) => {
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    department: 'ER',
    heart_rate: '',
    systolic_bp: '',
    diastolic_bp: '',
    respiratory_rate: '',
    oxygen_saturation: '',
    temperature_c: '',
    pain_score: 5,
    consciousness: 'alert'
  });

  const [selectedSymptoms, setSelectedSymptoms] = useState([]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSymptomToggle = (key) => {
    setSelectedSymptoms(prev => 
      prev.includes(key) ? prev.filter(s => s !== key) : [...prev, key]
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Reconstruct into the exact payload Elvis's POST /patient route expects
    const payload = {
      department: formData.department,
      patient_id: `PT-${Math.floor(1000 + Math.random() * 9000)}`, // temporary ID generator
      intake: {
        age: formData.age ? parseInt(formData.age, 10) : null,
        symptom_tags: selectedSymptoms,
        vitals: {
          heart_rate: formData.heart_rate ? parseFloat(formData.heart_rate) : null,
          systolic_bp: formData.systolic_bp ? parseFloat(formData.systolic_bp) : null,
          diastolic_bp: formData.diastolic_bp ? parseFloat(formData.diastolic_bp) : null,
          respiratory_rate: formData.respiratory_rate ? parseFloat(formData.respiratory_rate) : null,
          oxygen_saturation: formData.oxygen_saturation ? parseFloat(formData.oxygen_saturation) : null,
          temperature_c: formData.temperature_c ? parseFloat(formData.temperature_c) : null,
          pain_score: parseInt(formData.pain_score, 10),
          consciousness: formData.consciousness
        }
      },
      data: {
        name: formData.name
      }
    };

    if (onSubmitPatient) {
      onSubmitPatient(payload);
    } else {
      console.log("Structured Triage Payload Prepared:", payload);
    }
  };

  return (
    <div className="max-w-4xl mx-auto mt-10 p-8 bg-white rounded-xl shadow-lg border border-gray-200">
      <h2 className="text-2xl font-bold text-slate-800 mb-6 border-b pb-3 flex items-center justify-between">
        <span>Clinical Patient Intake Form</span>
        
      </h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Core Administrative Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-gray-700 font-medium mb-1">Full Name</label>
            <input 
              type="text" name="name" value={formData.name} onChange={handleChange}
              className="w-full border border-gray-300 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="Amanda Kimani" required
            />
          </div>
          <div>
            <label className="block text-gray-700 font-medium mb-1">Age</label>
            <input 
              type="number" name="age" value={formData.age} onChange={handleChange}
              className="w-full border border-gray-300 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="e.g. 45" required
            />
          </div>
          <div>
            <label className="block text-gray-700 font-medium mb-1">Target Department</label>
            <select 
              name="department" value={formData.department} onChange={handleChange}
              className="w-full border border-gray-300 rounded p-2 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              <option value="ER">Emergency Room (ER)</option>
              <option value="Pediatrics">Pediatrics</option>
              <option value="Radiology">Radiology</option>
              <option value="General">General Outpatient</option>
            </select>
          </div>
        </div>

        <hr className="border-gray-200" />

        {/* Vital Signs Grid */}
        <div>
          <h3 className="text-lg font-semibold text-blue-600 mb-3">Physiological Vital Signs</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-gray-600 font-medium mb-1">SpO2 (%)</label>
              <input type="number" name="oxygen_saturation" value={formData.oxygen_saturation} onChange={handleChange} placeholder="e.g. 98" className="w-full border border-gray-300 rounded p-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 font-medium mb-1">Heart Rate (BPM)</label>
              <input type="number" name="heart_rate" value={formData.heart_rate} onChange={handleChange} placeholder="e.g. 72" className="w-full border border-gray-300 rounded p-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 font-medium mb-1">Systolic BP (mmHg)</label>
              <input type="number" name="systolic_bp" value={formData.systolic_bp} onChange={handleChange} placeholder="e.g. 120" className="w-full border border-gray-300 rounded p-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 font-medium mb-1">Diastolic BP (mmHg)</label>
              <input type="number" name="diastolic_bp" value={formData.diastolic_bp} onChange={handleChange} placeholder="e.g. 80" className="w-full border border-gray-300 rounded p-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 font-medium mb-1">Resp Rate (breaths/m)</label>
              <input type="number" name="respiratory_rate" value={formData.respiratory_rate} onChange={handleChange} placeholder="e.g. 16" className="w-full border border-gray-300 rounded p-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 font-medium mb-1">Temperature (°C)</label>
              <input type="number" step="0.1" name="temperature_c" value={formData.temperature_c} onChange={handleChange} placeholder="e.g. 36.8" className="w-full border border-gray-300 rounded p-2 text-sm" />
            </div>
            <div className="col-span-2">
              <label className="block text-xs text-gray-600 font-medium mb-1">Consciousness Level</label>
              <select name="consciousness" value={formData.consciousness} onChange={handleChange} className="w-full border border-gray-300 rounded p-2 text-sm bg-white">
                <option value="alert">Alert (Fully conscious)</option>
                <option value="verbal">Verbal (Responds to voice)</option>
                <option value="pain">Pain (Responds only to pain)</option>
                <option value="unresponsive">Unresponsive</option>
              </select>
            </div>
          </div>
        </div>

        {/* Pain Scale Slider */}
        <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
          <label className="block text-gray-700 font-medium mb-1 flex justify-between">
            <span>Self-Reported Pain Score:</span>
            <span className={`font-bold text-lg ${formData.pain_score >= 7 ? 'text-red-600' : 'text-blue-600'}`}>{formData.pain_score} / 10</span>
          </label>
          <input 
            type="range" name="pain_score" min="0" max="10" value={formData.pain_score} onChange={handleChange}
            className="w-full cursor-pointer accent-blue-600"
          />
        </div>

        <hr className="border-gray-200" />

        {/* Structured Symptom Checkboxes */}
        <div>
          <h3 className="text-lg font-semibold text-red-600 mb-2">Symptom Assessment / Red Flags</h3>
          
          <h4 className="text-xs font-bold uppercase tracking-wider text-red-500 mb-2">Category 1: Emergency Triggers</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            {RED_FLAG_SYMPTOMS.map(sym => (
              <label key={sym.key} className={`flex items-start p-2 border rounded cursor-pointer transition text-xs ${selectedSymptoms.includes(sym.key) ? 'border-red-500 bg-red-50 text-red-900 font-medium' : 'border-gray-200 hover:bg-gray-50'}`}>
                <input type="checkbox" checked={selectedSymptoms.includes(sym.key)} onChange={() => handleSymptomToggle(sym.key)} className="mt-0.5 mr-2 accent-red-600" />
                <span>{sym.label}</span>
              </label>
            ))}
          </div>

          <h4 className="text-xs font-bold uppercase tracking-wider text-amber-600 mb-2">Category 2: Urgent Indicators</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            {URGENT_SYMPTOMS.map(sym => (
              <label key={sym.key} className={`flex items-start p-2 border rounded cursor-pointer transition text-xs ${selectedSymptoms.includes(sym.key) ? 'border-amber-500 bg-amber-50 text-amber-900 font-medium' : 'border-gray-200 hover:bg-gray-50'}`}>
                <input type="checkbox" checked={selectedSymptoms.includes(sym.key)} onChange={() => handleSymptomToggle(sym.key)} className="mt-0.5 mr-2 accent-amber-600" />
                <span>{sym.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Category 3 */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-green-600 mb-2">Category 3: Non-Urgent / Minor Complaints (Routine Management)</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              {MINOR_SYMPTOMS.map(sym => (
                <label key={sym.key} className={`flex items-start p-2 border rounded cursor-pointer transition text-xs ${selectedSymptoms.includes(sym.key) ? 'border-green-500 bg-green-5- bg-green-50 text-green-900 font-medium' : 'border-gray-200 hover:bg-gray-50'}`}>
                  <input type="checkbox" checked={selectedSymptoms.includes(sym.key)} onChange={() => handleSymptomToggle(sym.key)} className="mt-0.5 mr-2 accent-green-600" />
                  <span>{sym.label}</span>
                </label>
              ))}
            </div>
          </div>
        
       

        {/* Submit Action */}
        <button 
          type="submit" 
          className="w-full bg-blue-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 shadow-md transition duration-200 text-base"
        >
          Submit Patient Form
        </button>
      </form>
    </div>
  );
};

export default UpdatedTriageForm;