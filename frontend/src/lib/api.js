/**
 * NirnayX API Client
 * Centralized API communication layer
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'API request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

// ─── Cases ─────────────────────────────────────
export async function getCases(params = {}) {
  const query = new URLSearchParams(params).toString();
  return fetchAPI(`/api/v1/cases?${query}`);
}

export async function getCase(caseId) {
  return fetchAPI(`/api/v1/cases/${caseId}`);
}

export async function createCase(data) {
  return fetchAPI('/api/v1/cases', { method: 'POST', body: JSON.stringify(data) });
}

export async function submitCase(caseId, config = {}) {
  return fetchAPI(`/api/v1/cases/${caseId}/submit`, {
    method: 'POST',
    body: JSON.stringify(config),
  });
}

export async function getCaseEvaluations(caseId) {
  return fetchAPI(`/api/v1/cases/${caseId}/evaluations`);
}

export async function getCaseReport(caseId) {
  return fetchAPI(`/api/v1/cases/${caseId}/report`);
}

export async function cloneCase(caseId) {
  return fetchAPI(`/api/v1/cases/${caseId}/clone`, { method: 'POST' });
}

// ─── Verdicts ──────────────────────────────────
export async function getVerdicts() {
  return fetchAPI('/api/v1/verdicts');
}

export async function getVerdict(caseId) {
  return fetchAPI(`/api/v1/verdicts/${caseId}`);
}

export async function overrideVerdict(caseId, data) {
  return fetchAPI(`/api/v1/verdicts/${caseId}/override`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ─── Feedback ──────────────────────────────────
export async function submitFeedback(data) {
  return fetchAPI('/api/v1/feedback', { method: 'POST', body: JSON.stringify(data) });
}

export async function getFeedback() {
  return fetchAPI('/api/v1/feedback');
}

// ─── Agents ────────────────────────────────────
export async function getAgents() {
  return fetchAPI('/api/v1/agents');
}

export async function getRLTelemetry() {
  return fetchAPI('/api/v1/agents/rl/telemetry');
}

export async function getBiasReport() {
  return fetchAPI('/api/v1/agents/rl/bias-report');
}

// ─── Dashboard ─────────────────────────────────
export async function getDashboardStats() {
  return fetchAPI('/api/v1/dashboard/stats');
}

export async function getAuditLogs(params = {}) {
  const query = new URLSearchParams(params).toString();
  return fetchAPI(`/api/v1/dashboard/audit-logs?${query}`);
}

// ─── Domains ───────────────────────────────────
export async function getDomains() {
  return fetchAPI('/api/v1/domains');
}

export async function getDomain(domainKey) {
  return fetchAPI(`/api/v1/domains/${domainKey}`);
}

// ─── Auth ──────────────────────────────────────
export async function login(email, password) {
  return fetchAPI('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function register(data) {
  return fetchAPI('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
