const API = 'https://web-production-569c.up.railway.app/';

function getTokens() {
    return {
        access:  localStorage.getItem('access_token'),
        refresh: localStorage.getItem('refresh_token'),
    };
}

function saveTokens(access, refresh) {
    if (access)  localStorage.setItem('access_token',  access);
    if (refresh) localStorage.setItem('refresh_token', refresh);
}

function clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_role');
}

async function apiFetch(endpoint, options = {}) {
    const { access } = getTokens();
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    if (access) headers['Authorization'] = `Bearer ${access}`;
    const res = await fetch(`${API}${endpoint}`, { ...options, headers });
    let data;
    try { data = await res.json(); } catch { data = {}; }
    return { ok: res.ok, status: res.status, data };
}

function showAlert(elId, msg, type = 'error') {
    const el = document.getElementById(elId);
    if (!el) return;
    el.className = `alert ${type} show`;
    el.innerHTML = `<span>${type === 'error' ? '⚠️' : type === 'success' ? '✅' : 'ℹ️'}</span><span>${msg}</span>`;
}

function hideAlert(elId) {
    const el = document.getElementById(elId);
    if (el) el.classList.remove('show');
}

function setLoading(btnId, loading) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    btn.disabled = loading;
    btn.classList.toggle('loading', loading);
}

function redirectByRole(role) {
    if (role === 'Admin') window.location.href = 'admin-dashboard.html';
    else window.location.href = 'dashboard.html';
}

function requireAuth() {
    const { access } = getTokens();
    if (!access) window.location.href = 'login.html';
}

async function fetchMe() {
    const { ok, data, status } = await apiFetch('/me');
    if (!ok) {
        if (status === 401 || status === 403) {
            clearTokens();
            window.location.href = 'login.html';
        }
        return null;
    }
    return data;
}
