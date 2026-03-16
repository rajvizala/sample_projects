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
  listAgents: () => request('/agents'),
  getAgent: (name) => request(`/agents/${name}`),
  executeAgent: (name, data) => request(`/agents/${name}/execute`, { method: 'POST', body: JSON.stringify(data) }),
  listWorkflows: () => request('/workflows'),
  createWorkflow: (data) => request('/workflows', { method: 'POST', body: JSON.stringify(data) }),
  getWorkflow: (id) => request(`/workflows/${id}`),
  executeWorkflow: (id) => request(`/workflows/${id}/execute`, { method: 'POST' }),
  listPrebuilt: () => request('/workflows/prebuilt/list'),
  listExecutions: () => request('/executions'),
  getExecution: (id) => request(`/executions/${id}`),
  listTools: () => request('/tools'),
};
