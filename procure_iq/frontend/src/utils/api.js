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
  parseDocument: (data) => request('/documents/parse', { method: 'POST', body: JSON.stringify(data) }),
  getSuppliers: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/suppliers${query ? '?' + query : ''}`);
  },
  getSupplier: (id) => request(`/suppliers/${id}`),
  getSupplierRisk: (id) => request(`/suppliers/${id}/risk`),
  generateForecast: (data) => request('/forecast/generate', { method: 'POST', body: JSON.stringify(data) }),
  getSpendAnalytics: (days = 365) => request(`/analytics/spend?days=${days}`),
  getAnomalies: (days = 365) => request(`/analytics/anomalies?days=${days}`),
  getSavings: () => request('/analytics/savings'),
  getDashboard: () => request('/dashboard/overview'),
};
