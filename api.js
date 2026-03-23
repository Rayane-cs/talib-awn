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
 * metadata shape: { firstname, lastname, grade, domain, phone?,
 *                  institution?, field_of_study?, student_id_number?,
 *                  company_name? }
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


// ─────────────────────────────────────────────────────────────────────────────
//  AUTH — PASSWORD RESET (3-step)
// ─────────────────────────────────────────────────────────────────────────────

export async function sendPasswordResetOtp(email) {
  const r = await apiCall('POST', '/auth/reset/send-otp', { email });
  return r.ok ? { error: null } : { error: { message: r.error } };
}

export async function verifyPasswordResetOtp({ email, token }) {
  const r = await apiCall('POST', '/auth/reset/verify-otp', { email, otp: token });
  return r.ok ? { error: null } : { error: { message: r.error } };
}

export async function updatePassword(newPassword) {
  // After OTP verified, we need email stored — caller must pass it
  // The HTML pages already have the email in scope — they call this with just password.
  // We delegate to the page storing email; see note in forgot-password.html.
  const r = await apiCall('POST', '/auth/reset/set-password', {
    email:        window._resetEmail ?? '',   // set by the page
    otp:          window._resetOtp   ?? '',   // set by the page
    new_password: newPassword,
  });
  return r.ok ? { error: null } : { error: { message: r.error } };
}


// ─────────────────────────────────────────────────────────────────────────────
//  PROFILE
// ─────────────────────────────────────────────────────────────────────────────

export async function updateProfile(_ignored, fields) {
  const r = await apiCall('PATCH', '/users/me', fields);
  if (!r.ok) return { data: null, error: { message: r.error } };
  _cacheProfile(r.data);
  return { data: r.data, error: null };
}

export async function getUserInfo(userId) {
  const r = await apiCall('GET', `/users/${userId}`);
  if (!r.ok) return { user: null, projects: [], error: { message: r.error } };
  return { user: r.data.user, projects: r.data.projects, error: null };
}

export async function searchUsers(name) {
  const r = await apiCall('GET', `/users/search?q=${encodeURIComponent(name)}`);
  return { data: r.ok ? r.data : [], error: r.ok ? null : { message: r.error } };
}


// ─────────────────────────────────────────────────────────────────────────────
//  PROJECTS
// ─────────────────────────────────────────────────────────────────────────────

export async function getProjects(category = null) {
  const qs = category && category !== 'all' ? `?category=${encodeURIComponent(category)}` : '';
  const r  = await apiCall('GET', `/projects${qs}`);
  return { data: r.ok ? r.data : null, error: r.ok ? null : { message: r.error } };
}

export async function createProject(fields) {
  const r = await apiCall('POST', '/projects', fields);
  return { data: r.ok ? r.data : null, error: r.ok ? null : { message: r.error } };
}

export async function updateProject(id, fields) {
  const r = await apiCall('PATCH', `/projects/${id}`, fields);
  return { data: r.ok ? r.data : null, error: r.ok ? null : { message: r.error } };
}

export async function deleteProject(id) {
  const r = await apiCall('DELETE', `/projects/${id}`);
  return { error: r.ok ? null : { message: r.error } };
}

export async function toggleLike(projectId) {
  const r = await apiCall('POST', `/projects/${projectId}/like`);
  return { liked: r.data?.liked ?? false, error: r.ok ? null : { message: r.error } };
}

export async function getComments(projectId) {
  const r = await apiCall('GET', `/projects/${projectId}/comments`);
  return { data: r.ok ? r.data : [], error: r.ok ? null : { message: r.error } };
}

export async function addComment(projectId, content) {
  const r = await apiCall('POST', `/projects/${projectId}/comments`, { content });
  return { data: r.ok ? r.data : null, error: r.ok ? null : { message: r.error } };
}

export async function deleteComment(commentId) {
  const r = await apiCall('DELETE', `/comments/${commentId}`);
  return { error: r.ok ? null : { message: r.error } };
}


// ─────────────────────────────────────────────────────────────────────────────
//  EVENTS
// ─────────────────────────────────────────────────────────────────────────────

export async function getEvents() {
  const r = await apiCall('GET', '/events');
  return { data: r.ok ? r.data : [], error: r.ok ? null : { message: r.error } };
}

export async function joinEvent(eventId) {
  const r = await apiCall('POST', `/events/${eventId}/register`);
  return { error: r.ok ? null : { message: r.error } };
}

export async function quitEvent(eventId) {
  const r = await apiCall('DELETE', `/events/${eventId}/register`);
  return { error: r.ok ? null : { message: r.error } };
}


// ─────────────────────────────────────────────────────────────────────────────
//  ANNOUNCEMENTS
// ─────────────────────────────────────────────────────────────────────────────

export async function getAnnouncements() {
  const r = await apiCall('GET', '/announcements');
  return { data: r.ok ? r.data : [], error: r.ok ? null : { message: r.error } };
}


// ─────────────────────────────────────────────────────────────────────────────
//  SOCIAL
// ─────────────────────────────────────────────────────────────────────────────

export async function toggleFollow(targetUserId) {
  const r = await apiCall('POST', `/users/${targetUserId}/follow`);
  return { following: r.data?.following ?? false, error: r.ok ? null : { message: r.error } };
}


// ─────────────────────────────────────────────────────────────────────────────
//  STATS
// ─────────────────────────────────────────────────────────────────────────────

export async function getStats() {
  const r = await apiCall('GET', '/stats');
  return r.ok ? r.data : { projects: 0, events: 0, users: 0 };
}


// ─────────────────────────────────────────────────────────────────────────────
//  ADMIN — USERS
// ─────────────────────────────────────────────────────────────────────────────

export async function adminGetAllUsers() {
  const r = await apiCall('GET', '/admin/users');
  return { data: r.ok ? r.data : [], error: r.ok ? null : { message: r.error } };
}

export async function adminBanUser(userId, reason) {
  const r = await apiCall('POST', `/admin/users/${userId}/ban`, { reason });
  return { data: r.ok ? r.data : null, error: r.ok ? null : { message: r.error } };
}

export async function adminUnbanUser(userId) {
  const r = await apiCall('POST', `/admin/users/${userId}/unban`);
  return { data: r.ok ? r.data : null, error: r.ok ? null : { message: r.error } };
}

export async function adminWarnUser(userId) {
  const r = await apiCall('POST', `/admin/users/${userId}/warn`);
  return {
    data: r.ok ? r.data : null,
    error: r.ok ? null : { message: r.error },
    auto_banned: r.data?.auto_banned ?? false,
  };
}

export async function adminGetWithdrawals() {
  const r = await apiCall('GET', '/admin/withdrawals');
  return { data: r.ok ? r.data : [], error: r.ok ? null : { message: r.error } };
}

export async function adminApproveWithdrawal(id, note = null) {
  const r = await apiCall('POST', `/admin/withdrawals/${id}/approve`, { note });
  return { error: r.ok ? null : { message: r.error } };
}

export async function adminRejectWithdrawal(id, note = null) {
  const r = await apiCall('POST', `/admin/withdrawals/${id}/reject`, { note });
  return { error: r.ok ? null : { message: r.error } };
}


// ─────────────────────────────────────────────────────────────────────────────
//  WALLET
// ─────────────────────────────────────────────────────────────────────────────

export async function getWallet() {
  const r = await apiCall('GET', '/wallet');
  return { data: r.ok ? r.data : null, error: r.ok ? null : { message: r.error } };
}

export async function getWalletBalance() {
  const r = await apiCall('GET', '/wallet');
  return { balance: r.ok ? parseFloat(r.data.balance) : 0,
           error:   r.ok ? null : { message: r.error } };
}

export async function getTransactions(limit = 50) {
  const r = await apiCall('GET', `/wallet/transactions?limit=${limit}`);
  return { data: r.ok ? r.data : [], error: r.ok ? null : { message: r.error } };
}

/** Request a manual deposit (creates pending TX for admin to confirm). */
export async function initiateDeposit(amount) {
  const r = await apiCall('POST', '/wallet/deposit', { amount });
  if (!r.ok) return { error: r.error };
  // No redirect for manual deposits — show success message
  return { data: r.data, error: null };
}

export async function requestWithdrawal({ amount, payoutMethod, accountNumber }) {
  const r = await apiCall('POST', '/wallet/withdraw', {
    amount, payout_method: payoutMethod, account_number: accountNumber,
  });
  return { data: r.ok ? r.data : null, error: r.ok ? null : { message: r.error } };
}

export async function getWithdrawals() {
  const r = await apiCall('GET', '/wallet/withdrawals');
  return { data: r.ok ? r.data : [], error: r.ok ? null : { message: r.error } };
}

export async function createEscrow({ studentId, amount, jobId = null, note = null }) {
  const r = await apiCall('POST', '/escrow', {
    student_id: studentId, amount, job_id: jobId, note,
  });
  return { data: r.ok ? r.data : null, error: r.ok ? null : { message: r.error } };
}

export async function releaseEscrow(escrowId) {
  const r = await apiCall('POST', `/escrow/${escrowId}/release`);
  return { error: r.ok ? null : { message: r.error } };
}

export async function cancelEscrow(escrowId) {
  const r = await apiCall('POST', `/escrow/${escrowId}/cancel`);
  return { error: r.ok ? null : { message: r.error } };
}

export async function getMyEscrowsAsEmployer() {
  const r = await apiCall('GET', '/escrow/as-employer');
  return { data: r.ok ? r.data : [], error: r.ok ? null : { message: r.error } };
}

export async function getMyEscrowsAsStudent() {
  const r = await apiCall('GET', '/escrow/as-student');
  return { data: r.ok ? r.data : [], error: r.ok ? null : { message: r.error } };
}


// ─────────────────────────────────────────────────────────────────────────────
//  FORMATTING HELPERS  (kept identical to wallet.js)
// ─────────────────────────────────────────────────────────────────────────────

export function formatDZD(amount) {
  return new Intl.NumberFormat('en-DZ', {
    minimumFractionDigits: 2, maximumFractionDigits: 2,
  }).format(amount) + ' DZD';
}

export function txMeta(type) {
  const map = {
    deposit:  { label: 'Deposit',     color: 'green', icon: '↓' },
    escrow:   { label: 'Escrow Hold', color: 'amber', icon: '⏸' },
    release:  { label: 'Job Payment', color: 'green', icon: '↓' },
    refund:   { label: 'Refund',      color: 'blue',  icon: '↩' },
    withdraw: { label: 'Withdrawal',  color: 'red',   icon: '↑' },
  };
  return map[type] ?? { label: type, color: 'gray', icon: '·' };
}

export function txStatusLabel(status) {
  return { pending: 'Pending', completed: 'Completed', failed: 'Failed' }[status] ?? status;
}


// ─────────────────────────────────────────────────────────────────────────────
//  UI HELPERS  (identical to old supabase.js)
// ─────────────────────────────────────────────────────────────────────────────

export function showAlert(elId, msg, type = 'error') {
  const el = document.getElementById(elId);
  if (!el) return;
  el.className = `alert ${type} show`;
  el.textContent = msg;
  el.style.display = 'flex';
}

export function hideAlert(elId) {
  const el = document.getElementById(elId);
  if (el) { el.classList.remove('show'); el.style.display = 'none'; }
}

export function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = loading;
  btn.classList.toggle('loading', loading);
}

export function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
  });
}

export function esc(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

// ─────────────────────────────────────────────────────────────────────────────
//  BACKWARDS COMPAT  — so old code that does `import {supabase}` doesn't crash
// ─────────────────────────────────────────────────────────────────────────────
export const supabase = {
  auth: {
    signOut: async () => { _clearTokens(); window.location.href = 'login.html'; },
  },
};
