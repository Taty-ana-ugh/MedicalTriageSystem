import { useEffect, useMemo, useState } from 'react';
import { fetchDepartments, routePatient } from '../lib/api';

const DEFAULT_DEPARTMENTS = ['ER', 'Pediatrics', 'Radiology', 'General'];

const DepartmentRegistry = ({ departmentsData = {}, onMovePatient, onAddDepartment }) => {
  const [activeDepartment, setActiveDepartment] = useState(DEFAULT_DEPARTMENTS[0]);
  const [newDepartment, setNewDepartment] = useState('');
  const [liveDepartmentsData, setLiveDepartmentsData] = useState(departmentsData || {});

  const departments = useMemo(() => {
    const names = new Set([...DEFAULT_DEPARTMENTS, ...Object.keys(liveDepartmentsData || {})]);
    return Array.from(names);
  }, [liveDepartmentsData]);

  const currentQueue = liveDepartmentsData?.[activeDepartment] || [];

  useEffect(() => {
    const loadDepartments = async () => {
      try {
        const data = await fetchDepartments();
        setLiveDepartmentsData(data);
      } catch (error) {
        console.error(error);
      }
    };

    if (departmentsData && Object.keys(departmentsData).length > 0) {
      setLiveDepartmentsData(departmentsData);
    } else {
      loadDepartments();
    }
  }, [departmentsData]);

  const handleAddDepartment = () => {
    const name = newDepartment.trim();
    if (!name) return;

    if (onAddDepartment) {
      onAddDepartment(name);
    }

    setActiveDepartment(name);
    setNewDepartment('');
  };

  return (
    <div className="max-w-6xl mx-auto mt-10 p-6 bg-white rounded-2xl shadow-md border border-gray-200 text-slate-800">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-gray-200 pb-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">Department Registry</h2>
          <p className="text-sm text-slate-500 mt-1">
            This view mirrors the Python registry by keeping each specialty as its own queue.
          </p>
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <input
            type="text"
            value={newDepartment}
            onChange={(event) => setNewDepartment(event.target.value)}
            placeholder="New department"
            className="flex-1 md:w-48 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleAddDepartment}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg shadow transition text-sm"
          >
            Add Department
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-6">
        {departments.map((department) => {
          const count = departmentsData?.[department]?.length || 0;
          return (
            <button
              key={department}
              onClick={() => setActiveDepartment(department)}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition flex items-center gap-2 border ${
                activeDepartment === department
                  ? 'bg-blue-600 border-blue-600 text-white shadow-lg'
                  : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span>{department}</span>
              <span className={`px-1.5 py-0.5 rounded text-xs ${activeDepartment === department ? 'bg-blue-800 text-white' : 'bg-gray-100 text-gray-500'}`}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-xl border border-gray-200 overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
            <h3 className="font-semibold text-slate-700">{activeDepartment} queue</h3>
          </div>

          {currentQueue.length === 0 ? (
            <div className="p-6 text-sm text-slate-500">No patients are currently assigned to this department.</div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {currentQueue.map((patient) => (
                <li key={patient.patient_id} className="p-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-semibold text-slate-800">{patient.name || 'Anonymous patient'}</p>
                    <p className="text-sm text-slate-500 font-mono">{patient.patient_id}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold px-2 py-1 rounded-full bg-blue-100 text-blue-700">
                      {patient.urgency_level || 'NORMAL'}
                    </span>
                    <select
                      value={activeDepartment}
                      onChange={async (event) => {
                        try {
                          await routePatient(patient.patient_id, event.target.value);
                          if (onMovePatient) {
                            onMovePatient(patient.patient_id, activeDepartment, event.target.value);
                          }
                          const data = await fetchDepartments();
                          setLiveDepartmentsData(data);
                        } catch (error) {
                          console.error(error);
                        }
                      }}
                      className="border border-gray-300 rounded px-2 py-1 text-sm"
                    >
                      {departments.map((department) => (
                        <option key={department} value={department}>
                          {department}
                        </option>
                      ))}
                    </select>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="rounded-xl border border-gray-200 p-4 bg-slate-50">
          <h3 className="font-semibold text-slate-700 mb-3">Registry summary</h3>
          <ul className="space-y-2 text-sm text-slate-600">
            {departments.map((department) => (
              <li key={department} className="flex justify-between items-center">
                <span>{department}</span>
                <span className="font-semibold text-slate-800">{liveDepartmentsData?.[department]?.length || 0} patients</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default DepartmentRegistry;
