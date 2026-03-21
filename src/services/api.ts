/**
 * API service — connects the React frontend to the FastAPI backend.
 * Handles JWT token storage, auto-refresh, and all API calls.
 */

const API_BASE = 'http://localhost:8000/api';

// ─── Token Management ───

let accessToken: string | null = localStorage.getItem('vitalid_access_token');
let refreshToken: string | null = localStorage.getItem('vitalid_refresh_token');

export function setTokens(access: string, refresh: string) {
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem('vitalid_access_token', access);
  localStorage.setItem('vitalid_refresh_token', refresh);
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem('vitalid_access_token');
  localStorage.removeItem('vitalid_refresh_token');
}

export function getAccessToken() {
  return accessToken;
}

export function isLoggedIn() {
  return !!accessToken;
}

// ─── Fetch Wrapper ───

async function apiFetch(endpoint: string, options: RequestInit = {}): Promise<any> {
  const url = `${API_BASE}${endpoint}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const response = await fetch(url, { ...options, headers });

  if (response.status === 401 && refreshToken) {
    // Try to refresh the token
    const refreshResp = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${refreshToken}`,
      },
    });

    if (refreshResp.ok) {
      const data = await refreshResp.json();
      setTokens(data.access_token, data.refresh_token);
      headers['Authorization'] = `Bearer ${data.access_token}`;
      const retryResp = await fetch(url, { ...options, headers });
      if (!retryResp.ok) {
        const err = await retryResp.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(err.detail || 'Request failed');
      }
      return retryResp.json();
    } else {
      clearTokens();
      throw new Error('Session expired. Please login again.');
    }
  }

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ─── Auth API ───

export const authAPI = {
  register: (data: { full_name: string; phone_number: string; password: string; date_of_birth?: string; gender?: string }) =>
    apiFetch('/auth/register', { method: 'POST', body: JSON.stringify(data) }),

  verifyOTP: (phone_number: string, otp: string) =>
    apiFetch('/auth/verify-otp', { method: 'POST', body: JSON.stringify({ phone_number, otp }) }),

  aadhaarVerify: (aadhaar_number: string, tempToken: string) =>
    fetch(`${API_BASE}/auth/aadhaar-verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tempToken}` },
      body: JSON.stringify({ aadhaar_number }),
    }).then(r => { if (!r.ok) throw r; return r.json(); }),

  login: (phone_number: string, password: string) =>
    apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ phone_number, password }) }),

  getMe: () => apiFetch('/auth/me'),
};

// ─── Dashboard API ───

export const dashboardAPI = {
  getSummary: () => apiFetch('/dashboard/summary'),
};

// ─── Vitals API ───

export const vitalsAPI = {
  logBP: (systolic: number, diastolic: number, pulse?: number) =>
    apiFetch('/vitals/bp', { method: 'POST', body: JSON.stringify({ systolic, diastolic, pulse }) }),

  logGlucose: (fasting_glucose: number) =>
    apiFetch('/vitals/glucose', { method: 'POST', body: JSON.stringify({ fasting_glucose }) }),

  logBMI: (weight_kg: number, height_cm: number, waist_cm?: number) =>
    apiFetch('/vitals/bmi', { method: 'POST', body: JSON.stringify({ weight_kg, height_cm, waist_cm }) }),

  getHistory: (limit = 20) => apiFetch(`/vitals/history?limit=${limit}`),
  getLatestBMI: () => apiFetch('/vitals/bmi/latest'),
};

// ─── Tasks API ───

export const tasksAPI = {
  getToday: () => apiFetch('/tasks/today'),
  completeTask: (taskId: string, verificationData?: any) =>
    apiFetch(`/tasks/${taskId}/complete`, {
      method: 'POST',
      body: JSON.stringify({ verification_data: verificationData }),
    }),
  getStreak: () => apiFetch('/tasks/streak'),
  getHistory: (page = 1) => apiFetch(`/tasks/history?page=${page}`),
};

// ─── Coins API ───

export const coinsAPI = {
  getBalance: () => apiFetch('/coins/balance'),
  getOffers: () => apiFetch('/coins/offers'),
  redeem: (offerId: string) =>
    apiFetch('/coins/redeem', { method: 'POST', body: JSON.stringify({ offer_id: offerId }) }),
};

// ─── Profile API ───

export const profileAPI = {
  get: () => apiFetch('/profile/'),
  update: (data: { full_name?: string; gender?: string; date_of_birth?: string }) =>
    apiFetch('/profile/update', { method: 'PUT', body: JSON.stringify(data) }),
  changePassword: (old_password: string, new_password: string) =>
    apiFetch('/profile/change-password', { method: 'POST', body: JSON.stringify({ old_password, new_password }) }),
  getActivity: () => apiFetch('/profile/activity'),
};
