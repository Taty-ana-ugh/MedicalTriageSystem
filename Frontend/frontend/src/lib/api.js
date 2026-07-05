const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request(path, { method = 'GET', body, headers } = {}) {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(headers || {})
    }
  };

  if (body !== undefined) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || 'Request failed');
  }

  return data;
}

export async function submitPatient(payload) {
  return request('/patient', { method: 'POST', body: payload });
}

export async function fetchQueue() {
  return request('/queue');
}

export async function fetchDepartments() {
  return request('/departments');
}

export async function admitNextPatient(department) {
  return request('/queue/admit-next', {
    method: 'POST',
    body: department ? { department } : {}
  });
}

export async function removePatient(patientId) {
  return request('/queue/remove', {
    method: 'POST',
    body: { patient_id: patientId }
  });
}

export async function routePatient(patientId, department) {
  return request(`/patient/${patientId}/route`, {
    method: 'PUT',
    body: { department }
  });
}
