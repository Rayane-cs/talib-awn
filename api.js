// ══════════════════════════════════════════════════════════════════════════════
//  api.js  —  Talib-Awn · طالب عون
//  Replaces supabase.js completely.
//  All calls go to your local Flask API.
//
//  Usage (identical import pattern to old supabase.js):
//    import { signIn, requireProfile, redirectByRole, ... } from './api.js';
//
//  Set API_BASE to your Flask server URL (with no trailing slash).
// ══════════════════════════════════════════════════════════════════════════════

export const API_BASE = "http://127.0.0.1:5000/api";

// ─────────────────────────────────────────────────────────────────────────────
//  TOKEN STORAGE  (localStorage — no Supabase session needed)
// ─────────────────────────────────────────────────────────────────────────────

function _setTokens(access, refresh) {
  localStorage.setItem('ta_access',  access);
  localStorage.setItem('ta_refresh', refresh);
}
function _getAccess()  { return localStorage.getItem('ta_access');  }
function _getRefresh() { return localStorage.getItem('ta_refresh'); }
function _clearTokens() {
  localStorage.removeItem('ta_access');
  localStorage.removeItem('ta_refresh');
  localStorage.removeItem('ta_profile');
}

function _cacheProfile(profile) {
  localStorage.setItem('ta_profile', JSON.stringify(profile));
}
function _getCachedProfile() {
  try { return JSON.parse(localStorage.getItem('ta_profile')); }
  catch { return null; }
}


// ─────────────────────────────────────────────────────────────────────────────
//  CORE HTTP  (auto-refresh on 401)
// ─────────────────────────────────────────────────────────────────────────────

export async function apiCall(method, path, body = null, retry = true) {
  const token = _getAccess();
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  let res = await fetch(`${API_BASE}${path}`, opts);

  // Auto-refresh on 401
  if (res.status === 401 && retry) {
    const refreshed = await _doRefresh();
    if (refreshed) return apiCall(method, path, body, false);
    _clearTokens();
    window.location.href = 'login.html';
    return { ok: false, error: 'Session expired.' };
  }

  const json = await res.json().catch(() => ({ ok: false, error: 'Invalid server response.' }));
  return json;
}

async function _doRefresh() {
  const refresh = _getRefresh();
  if (!refresh) return false;
  try {
    const res  = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${refresh}`, 'Content-Type': 'application/json' },
    });
    const json = await res.json();
    if (json.ok && json.data?.access_token) {
      localStorage.setItem('ta_access', json.data.access_token);
      return true;
    }
  } catch {}
  return false;
}


// ─────────────────────────────────────────────────────────────────────────────
//  AUTH — PROFILE / SESSION
// ─────────────────────────────────────────────────────────────────────────────

/** Returns the current user profile, or null if not logged in. */
export async function getAuthUser() {
  if (!_getAccess()) return null;
  const r = await apiCall('GET', '/auth/me');
  if (!r.ok) return null;
  _cacheProfile(r.data);
  return r.data;
}

/**
 * Returns the profile or redirects to login.html.
 * Drop-in replacement for Supabase requireProfile().
 */
export async function requireProfile() {
  const cached = _getCachedProfile();
  if (cached && _getAccess()) {
    // Refresh in background
    getAuthUser().then(p => { if (p) _cacheProfile(p); });
    return cached;
  }
  const profile = await getAuthUser();
  if (!profile) { window.location.href = 'login.html'; return null; }
  return profile;
}

/** Redirect already-authenticated users from auth pages. */
export async function redirectIfLoggedIn() {
  const profile = await getAuthUser();
  if (profile) redirectByRole(profile);
}

/** Redirect to the right dashboard based on role + grade. */
export function redirectByRole(profile) {
  const role  = (profile?.role  ?? '').toLowerCase();
  const grade = (profile?.grade ?? '').toLowerCase();
  if (role === 'admin')
    { window.location.href = 'admin-panel.html'; return; }
  if (grade.includes('company') || grade.includes('manager') || grade.includes('employer'))
    { window.location.href = 'employer.html'; return; }
  window.location.href = 'student.html';
}

/** Sign out: clear tokens and redirect. */
export async function signOut() {
  _clearTokens();
  window.location.href = 'login.html';
}


// ─────────────────────────────────────────────────────────────────────────────
//  AUTH — REGISTER (2-step OTP)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Step 1 — send OTP.
 */
export async function signUpWithOtp({ email, password, metadata = {} }) {
  const r = await apiCall('POST', '/auth/register/send-otp', {
    email, password, ...metadata,
  });
  return r.ok ? { error: null } : { error: { message: r.error } };
}

/** Step 2 — verify OTP, receive JWT. */
export async function verifyEmailOtp({ email, token }) {
  const r = await apiCall('POST', '/auth/register/verify-otp', { email, otp: token });
  if (!r.ok) return { error: { message: r.error } };
  _setTokens(r.data.access_token, r.data.refresh_token);
  _cacheProfile(r.data.user);
  return { data: { user: r.data.user }, error: null };
}


// ─────────────────────────────────────────────────────────────────────────────
//  AUTH — LOGIN
// ─────────────────────────────────────────────────────────────────────────────

export async function signIn({ email, password }) {
  const r = await apiCall('POST', '/auth/login', { email, password });
  if (!r.ok) return { data: null, error: { message: r.error } };
  _setTokens(r.data.access_token, r.data.refresh_token);
  _cacheProfile(r.data.user);
  return { data: { user: r.data.user }, error: null };
}

// ... (continues exactly same as your original)

// ─────────────────────────────────────────────────────────────────────────────
//  UI HELPERS
// ─────────────────────────────────────────────────────────────────────────────

export function showAlert(boxId, msg) {
  const a = document.getElementById(boxId);
  if (!a) return;
  if (!msg) {
    a.className = 'alert';
    a.style.display = 'none';
  } else {
    a.className = 'alert show';
    a.textContent = msg;
    a.style.display = 'block';
  }
}

export function setLoading(btnId, isLoading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  if (isLoading) {
    btn.disabled = true;
    btn.classList.add('loading');
  } else {
    btn.disabled = false;
    btn.classList.remove('loading');
  }
}
