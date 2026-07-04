import { useState } from 'react';

const TriageForm = () => {
  // This is React 'State' - it holds the data as the user types
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    symptoms: '',
    painLevel: '1'
  });

  // This function updates the state whenever an input changes
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // This function runs when the user clicks Submit
  const handleSubmit = (e) => {
    e.preventDefault(); // Prevents the page from refreshing
    console.log("Patient Data Submitted:", formData);
    alert("Patient intake saved! Check the developer console.");
  };

  return (
    <div className="max-w-2xl mx-auto mt-10 p-6 bg-white rounded-lg shadow-md border border-gray-200">
      <h2 className="text-2xl font-bold text-blue-600 mb-6 border-b pb-2">Patient Intake Form</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Name Input */}
        <div>
          <label className="block text-gray-700 font-medium mb-1">Full Name</label>
          <input 
            type="text" 
            name="name"
            value={formData.name}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded p-2 focus:outline-none focus:border-blue-500"
            placeholder="e.g. Jane Doe"
            required
          />
        </div>

        {/* Age Input */}
        <div>
          <label className="block text-gray-700 font-medium mb-1">Age</label>
          <input 
            type="number" 
            name="age"
            value={formData.age}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded p-2 focus:outline-none focus:border-blue-500"
            placeholder="e.g. 45"
            required
          />
        </div>

        {/* Symptoms Textarea */}
        <div>
          <label className="block text-gray-700 font-medium mb-1">Primary Symptoms</label>
          <textarea 
            name="symptoms"
            value={formData.symptoms}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded p-2 focus:outline-none focus:border-blue-500"
            rows="3"
            placeholder="Describe the symptoms..."
            required
          ></textarea>
        </div>

        {/* Pain Level Slider */}
        <div>
          <label className="block text-gray-700 font-medium mb-1">
            Pain Level: <span className="font-bold text-red-500">{formData.painLevel}</span> / 10
          </label>
          <input 
            type="range" 
            name="painLevel"
            min="1" 
            max="10" 
            value={formData.painLevel}
            onChange={handleChange}
            className="w-full cursor-pointer"
          />
        </div>

        {/* Submit Button */}
        <button 
          type="submit" 
          className="w-full bg-blue-600 text-white font-bold py-2 px-4 rounded hover:bg-blue-700 transition duration-300"
        >
          Submit Triage
        </button>
      </form>
    </div>
  );
};

export default TriageForm;