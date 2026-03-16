const API_BASE = '/api/v1';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export const api = {
  analyzeEmail: (data) => request('/analyze/email', { method: 'POST', body: JSON.stringify(data) }),
  analyzeUrl: (data) => request('/analyze/url', { method: 'POST', body: JSON.stringify(data) }),
  analyzeMessage: (data) => request('/analyze/message', { method: 'POST', body: JSON.stringify(data) }),
  getThreats: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/threats${query ? '?' + query : ''}`);
  },
  getThreat: (id) => request(`/threats/${id}`),
  updateThreat: (id, data) => request(`/threats/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  getDashboardStats: () => request('/dashboard/stats'),
  getTimeline: (days = 30) => request(`/dashboard/timeline?days=${days}`),
};
