/**
 * VitalID API Service — JWT auth, auto-refresh, all endpoints.
 */

const API_BASE = 'http://localhost:8000/api';

let accessToken: string | null = localStorage.getItem('vitalid_access_token');
let refreshToken: string | null = localStorage.getItem('vitalid_refresh_token');

export function setTokens(access: string, refresh: string) {
  accessToken = access; refreshToken = refresh;
  localStorage.setItem('vitalid_access_token', access);
  localStorage.setItem('vitalid_refresh_token', refresh);
}
export function clearTokens() {
  accessToken = null; refreshToken = null;
  localStorage.removeItem('vitalid_access_token');
  localStorage.removeItem('vitalid_refresh_token');
}
export function getAccessToken() { return accessToken; }
export function isLoggedIn() { return !!accessToken; }

async function apiFetch(endpoint: string, options: RequestInit = {}): Promise<any> {
  const url = `${API_BASE}${endpoint}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;

  let response = await fetch(url, { ...options, headers });

  if (response.status === 401 && refreshToken) {
    const refreshResp = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${refreshToken}` },
    });
    if (refreshResp.ok) {
      const data = await refreshResp.json();
      setTokens(data.access_token, data.refresh_token);
      headers['Authorization'] = `Bearer ${data.access_token}`;
      response = await fetch(url, { ...options, headers });
    } else {
      clearTokens();
      const err: any = new Error('Session expired. Please login again.');
      err.status = 401;
      throw err;
    }
  }

  if (!response.ok) {
    const err: any = await response.json().catch(() => ({ detail: 'Request failed' }));
    const error: any = new Error(err.detail || `HTTP ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

// ─── Auth ───
export const authAPI = {
  register: (data: Record<string, any>) =>
    apiFetch('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  verifyOTP: (phone_number: string, otp: string) =>
    apiFetch('/auth/verify-otp', { method: 'POST', body: JSON.stringify({ phone_number, otp }) }),
  aadhaarVerify: (aadhaar_number: string, tempToken: string) =>
    fetch(`${API_BASE}/auth/aadhaar-submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tempToken}` },
      body: JSON.stringify({ aadhaar_number }),
    }).then(async r => { if (!r.ok) { const e = await r.json(); throw new Error(e.detail || 'Failed'); } return r.json(); }),
  login: (phone_number: string, password: string) =>
    apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ phone_number, password }) }),
  getMe: () => apiFetch('/auth/me'),
};

// ─── Dashboard ───
export const dashboardAPI = {
  getSummary: () => apiFetch('/dashboard/summary'),
};

// ─── Vitals ───
export const vitalsAPI = {
  logBP: (systolic: number, diastolic: number, pulse?: number) =>
    apiFetch('/vitals/bp', { method: 'POST', body: JSON.stringify({ systolic, diastolic, pulse }) }),
  logGlucose: (fasting_glucose: number) =>
    apiFetch('/vitals/sugar', { method: 'POST', body: JSON.stringify({ fasting_glucose }) }),
  logBMI: (weight_kg: number, height_cm: number, waist_cm?: number) =>
    apiFetch('/vitals/bmi', { method: 'POST', body: JSON.stringify({ weight_kg, height_cm, waist_cm }) }),
  getHistory: () => apiFetch('/vitals/history'),
  getLatestBMI: () => apiFetch('/vitals/bmi/latest'),
};

// ─── Tasks ───
export const tasksAPI = {
  getToday: () => apiFetch('/tasks/today'),
  completeTask: (taskId: string) =>
    apiFetch(`/tasks/${taskId}/complete`, { method: 'POST', body: JSON.stringify({}) }),
  getHistory: () => apiFetch('/tasks/history'),
  getMonthlyStatus: () => apiFetch('/tasks/monthly-status'),
  getStepGoal: () => apiFetch('/tasks/step-goal'),
  updateStepGoal: (step_goal: number) =>
    apiFetch('/tasks/step-goal', { method: 'POST', body: JSON.stringify({ step_goal }) }),
};

// ─── Reports ───
export const reportsAPI = {
  list: () => apiFetch('/reports/'),
  analyze: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const token = getAccessToken();
    const headers: any = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const response = await fetch(`${API_BASE}/reports/analyze`, { method: 'POST', headers, body: formData });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || `Upload failed (HTTP ${response.status})`);
    }
    return response.json();
  },
};

// ─── ML (legacy alias — same as reports/analyze) ───
export const mlAPI = {
  analyzeReport: (file: File) => reportsAPI.analyze(file),
};

// ─── Coins ───
export const coinsAPI = {
  getBalance: () => apiFetch('/coins/balance'),
  getOffers: () => apiFetch('/coins/offers'),
  redeem: (offerId: string) =>
    apiFetch('/coins/redeem', { method: 'POST', body: JSON.stringify({ offer_id: offerId }) }),
};

// ─── Profile ───
export const profileAPI = {
  get: () => apiFetch('/profile/'),
  update: (data: Record<string, any>) =>
    apiFetch('/profile/update', { method: 'PUT', body: JSON.stringify(data) }),
  changePassword: (old_password: string, new_password: string) =>
    apiFetch('/profile/change-password', { method: 'POST', body: JSON.stringify({ old_password, new_password }) }),
  downloadReport: () => apiFetch('/profile/download-report'),
  getActivity: () => apiFetch('/profile/activity'),
  uploadPhoto: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const token = getAccessToken();
    const headers: any = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const response = await fetch(`${API_BASE}/profile/upload-photo`, { method: 'POST', headers, body: formData });
    if (!response.ok) { const err = await response.json().catch(() => ({ detail: 'Upload failed' })); throw new Error(err.detail || 'Upload failed'); }
    return response.json();
  },
};

// ─── Settings ───
export const settingsAPI = {
  get: () => apiFetch('/settings/'),
  update: (data: Record<string, any>) =>
    apiFetch('/settings/', { method: 'PUT', body: JSON.stringify(data) }),
};

// ─── Notifications ───
export const notificationsAPI = {
  list: () => apiFetch('/notifications/'),
  create: (data: Record<string, any>) =>
    apiFetch('/notifications/', { method: 'POST', body: JSON.stringify(data) }),
  delete: (id: string) => apiFetch(`/notifications/${id}`, { method: 'DELETE' }),
  check: () => apiFetch('/notifications/check'),
  initWaterReminders: () => apiFetch('/notifications/init-water-reminders', { method: 'POST' }),
};

// ─── Clinics ───
export const clinicsAPI = {
  nearest: (lat: number, lng: number) => apiFetch(`/clinics/nearest?lat=${lat}&lng=${lng}`),
};

// ─── Health ID ───
export const healthIdAPI = {
  getCardData: () => apiFetch('/health-id/card-data'),
  getQRCode: () => `${API_BASE}/health-id/qr-code?token=${getAccessToken()}`,
  downloadCard: () => `${API_BASE}/health-id/download-card?token=${getAccessToken()}`,
};

// ─── Trends ───
export const trendsAPI = {
  getBP: (days: number = 30) => apiFetch(`/trends/bp?days=${days}`),
  getSugar: (days: number = 30) => apiFetch(`/trends/sugar?days=${days}`),
  getWeight: (days: number = 90) => apiFetch(`/trends/weight?days=${days}`),
  getSummary: () => apiFetch('/trends/summary'),
  getHistory: () => apiFetch('/trends/history'),
};

// ─── Share ───
export const shareAPI = {
  getHealthSummary: () => apiFetch('/share/health-summary'),
  getWhatsAppLink: () => apiFetch('/share/whatsapp-link'),
};

// ─── Blockchain ───
export const blockchainAPI = {
  getHistory: () => apiFetch('/blockchain/history'),
};
