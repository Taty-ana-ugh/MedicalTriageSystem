import { useEffect, useState } from 'react';
import { admitNextPatient, fetchDepartments, routePatient } from '../lib/api';

const TIER_BADGES = {
  EMERGENCY: "bg-red-100 text-red-800 border-red-200",
  URGENT: "bg-amber-100 text-amber-800 border-amber-200",
  NORMAL: "bg-green-100 text-green-800 border-green-200"
};

const QueueDashboard = ({ departmentsData, onPopPatient, onRoutePatient }) => {
  const [activeDept, setActiveDept] = useState('ER');
  const [liveData, setLiveData] = useState(departmentsData || { ER: [], Pediatrics: [], Radiology: [], General: [] });
  const [loading, setLoading] = useState(false);

  const departments = Object.keys(liveData || { ER: [], Pediatrics: [], Radiology: [], General: [] });
  const currentQueue = liveData?.[activeDept] || [];

  const refreshData = async () => {
    try {
      const data = await fetchDepartments();
      setLiveData(data);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    if (departmentsData) {
      setLiveData(departmentsData);
      return;
    }
    refreshData();
  }, [departmentsData]);

  const formatWaitTime = (seconds) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="max-w-6xl mx-auto mt-10 p-6 bg-white rounded-2xl shadow-md border border-gray-200 text-slate-800">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-gray-200 pb-4 mb-6 gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">Patient Queue Dashboard</h2>
        </div>
        
        <button
          onClick={async () => {
            setLoading(true);
            try {
              await admitNextPatient(activeDept);
              if (onPopPatient) {
                onPopPatient(activeDept);
              }
              await refreshData();
            } finally {
              setLoading(false);
            }
          }}
          disabled={currentQueue.length === 0 || loading}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-500  text-slate-800 text-white font-semibold py-2 px-4 rounded-lg shadow transition text-sm flex items-center gap-2"
        >
          <span>{loading ? 'Serving...' : 'Serve Next Critical Patient'}</span>
          <span className="bg-blue-800 px-1.5 py-0.5 rounded text-xs">{currentQueue.length}</span>
        </button>
      </div>

      {/* Navigation Department Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {departments.map(dept => {
          const count = departmentsData?.[dept]?.length || 0;
          return (
            <button
              key={dept}
              onClick={() => setActiveDept(dept)}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition flex items-center gap-2 border ${
                activeDept === dept 
                  ? 'bg-blue-600 border-blue-600 text-white shadow-lg' 
                  : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span>{dept}</span>
              <span className={`px-1.5 py-0.5 rounded text-xs ${activeDept === dept ? 'bg-blue-800 text-white' : 'bg-gray-100 text-gray-500'}`}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Main Priority Queue Output Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {currentQueue.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            No patients currently queued inside the {activeDept} block.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-gray-600 text-xs font-semibold uppercase tracking-wider">
                  <th className="p-4">Rank Priority Score</th>
                  <th className="p-4">Patient Identifier</th>
                  <th className="p-4">Urgency Level Band</th>
                  <th className="p-4">Active Wait Time</th>
                  <th className="p-4 text-right">Inter-Department Routing</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 text-sm">
                {currentQueue.map((patient, index) => (
                  <tr key={patient.patient_id} className="hover:bg-gray-50 transition">
                    <td className="p-4 font-mono font-bold text-blue-400">
                      #{index + 1} &rarr; <span className="text-slate-800">{patient.priority.toFixed(2)}</span>
                    </td>
                    <td className="p-4">
                      <div className="font-semibold text-slate-800">{patient.name || "Anonymous Case"}</div>
                      <div className="text-xs text-gray-500 font-mono">{patient.patient_id}</div>
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${TIER_BADGES[patient.urgency_level] || TIER_BADGES.NORMAL}`}>
                        {patient.urgency_level}
                      </span>
                    </td>
                    <td className="p-4 text-slate-700 font-mono">
                      {formatWaitTime(patient.waited_seconds)}
                    </td>
                    <td className="p-4 text-right">
                      <select
                        value={activeDept}
                        onChange={async (e) => {
                          try {
                            await routePatient(patient.patient_id, e.target.value);
                            if (onRoutePatient) {
                              onRoutePatient(patient.patient_id, activeDept, e.target.value);
                            }
                            await refreshData();
                          } catch (error) {
                            console.error(error);
                          }
                        }}
                        className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs font-medium text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
                      >
                        {departments.map(d => (
                          <option key={d} value={d}>{d}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default QueueDashboard;