// ─────────────────────────────────────────────────────────────────────────────
//  supabase.js  —  Talib-Awn · طالب عون
//  Import this with:  import { ... } from './supabase.js';
//  Every HTML file must use <script type="module"> for its own script.
// ─────────────────────────────────────────────────────────────────────────────

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';

const SUPABASE_URL  = 'https://lzvopmmasfvwtepcrpkw.supabase.co';
const SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx6dm9wbW1hc2Z2d3RlcGNycGt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4MDEwNTUsImV4cCI6MjA4OTM3NzA1NX0.74JQHZ-hM-GwQhoqLYy0Zr-QpNXLOdfzUs71rPmbja0';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON, {
  auth: {
    autoRefreshToken:   true,
    persistSession:     true,
    detectSessionInUrl: true,
  },
});

// ─────────────────────────────────────────────────────────────────────────────
//  AUTH HELPERS
// ─────────────────────────────────────────────────────────────────────────────

/** Get the current Supabase Auth user, or null */
export async function getAuthUser() {
  const { data: { user } } = await supabase.auth.getUser();
  return user ?? null;
}

/**
 * Get the public.users profile for the logged-in user.
 * Redirects to login.html if not authenticated.
 * Waits up to 3 seconds for the DB trigger to create the row.
 */
export async function requireProfile() {
  const user = await getAuthUser();
  if (!user) { window.location.href = 'login.html'; return null; }

  // Retry up to 6 times (3s total) — trigger may be slightly delayed
  for (let i = 0; i < 6; i++) {
    const { data, error } = await supabase
      .from('users')
      .select('*')
      .eq('auth_id', user.id)
      .maybeSingle();                  // maybeSingle never throws on 0 rows

    if (data) return data;
    if (error) { console.error('requireProfile error:', error); break; }
    await new Promise(r => setTimeout(r, 500));
  }

  // Profile not found — sign out and redirect
  await supabase.auth.signOut();
  window.location.href = 'login.html';
  return null;
}

/** Redirect already-logged-in users away from auth pages */
export async function redirectIfLoggedIn() {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return;
  const { data } = await supabase
    .from('users').select('role').eq('auth_id', session.user.id).maybeSingle();
  if (data) redirectByRole(data.role);
}

/** Redirect to the correct dashboard based on role */
export function redirectByRole(role) {
  const r = (role || '').toLowerCase();
  if (r === 'admin')    window.location.href = 'admin-panel.html';
  else                  window.location.href = 'student-dashboard.html';
}

/** Sign out and go to login */
export async function signOut() {
  await supabase.auth.signOut();
  window.location.href = 'login.html';
}

// ─────────────────────────────────────────────────────────────────────────────
//  REGISTRATION  (Supabase Auth OTP flow)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Step 1 — sign up. Supabase sends an 8-digit OTP to email.
 * metadata is stored in auth.users.raw_user_meta_data and copied
 * to public.users by the handle_new_user trigger.
 */
export async function signUpWithOtp({ email, password, metadata }) {
  return supabase.auth.signUp({
    email,
    password,
    options: { data: metadata },
  });
}

/** Step 2 — verify the 8-digit OTP from the confirmation email */
export async function verifyEmailOtp({ email, token }) {
  return supabase.auth.verifyOtp({ email, token, type: 'email' });
}

/** Sign in with email + password */
export async function signIn({ email, password }) {
  return supabase.auth.signInWithPassword({ email, password });
}

/** Password reset step 1 — send recovery OTP */
export async function sendPasswordResetOtp(email) {
  return supabase.auth.resetPasswordForEmail(email, { redirectTo: null });
}

/** Password reset step 2 — verify recovery OTP */
export async function verifyPasswordResetOtp({ email, token }) {
  return supabase.auth.verifyOtp({ email, token, type: 'recovery' });
}

/** Password reset step 3 — set new password (requires active session) */
export async function updatePassword(newPassword) {
  return supabase.auth.updateUser({ password: newPassword });
}

// ─────────────────────────────────────────────────────────────────────────────
//  PROFILE
// ─────────────────────────────────────────────────────────────────────────────

export async function updateProfile(authId, fields) {
  const { data, error } = await supabase
    .from('users')
    .update(fields)
    .eq('auth_id', authId)
    .select()
    .single();
  return { data, error };
}

// ─────────────────────────────────────────────────────────────────────────────
//  PROJECTS  (with aggregated like_count, comment_count, is_liked)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Fetch all visible projects with owner info and aggregated counts.
 * Also marks which ones the current user has liked (requires active session).
 */
export async function getProjects(category = null) {
  let q = supabase
    .from('projects')
    .select(`
      id, title, description, image, category, status, owner_id, created_at,
      owner:users!owner_id(id, firstname, lastname, image, grade, domain),
      likes:project_likes(count),
      comments:project_comments(count)
    `)
    .eq('is_visible', true)
    .order('created_at', { ascending: false });

  if (category && category !== 'all') q = q.eq('category', category);

  const { data, error } = await q;
  if (error) return { data: null, error };

  // Get current user's likes to mark is_liked
  const { data: { user } } = await supabase.auth.getUser();
  let myLikes = new Set();
  if (user) {
    const { data: profile } = await supabase
      .from('users').select('id').eq('auth_id', user.id).maybeSingle();
    if (profile) {
      const { data: likes } = await supabase
        .from('project_likes').select('project_id').eq('user_id', profile.id);
      myLikes = new Set((likes || []).map(l => l.project_id));
    }
  }

  const enriched = (data || []).map(p => ({
    ...p,
    like_count:    p.likes?.[0]?.count    ?? 0,
    comment_count: p.comments?.[0]?.count ?? 0,
    is_liked:      myLikes.has(p.id),
  }));

  return { data: enriched, error: null };
}

export async function createProject(fields) {
  const profile = await requireProfile();
  if (!profile) return { error: { message: 'Not authenticated' } };
  const { data, error } = await supabase
    .from('projects')
    .insert({ ...fields, owner_id: profile.id, is_visible: true })
    .select()
    .single();
  return { data, error };
}

export async function updateProject(id, fields) {
  const { data, error } = await supabase
    .from('projects').update(fields).eq('id', id).select().single();
  return { data, error };
}

export async function deleteProject(id) {
  const { error } = await supabase.from('projects').delete().eq('id', id);
  return { error };
}

export async function toggleLike(projectId) {
  const profile = await requireProfile();
  if (!profile) return { error: { message: 'Not authenticated' } };

  const { data: existing } = await supabase
    .from('project_likes').select('id')
    .eq('project_id', projectId).eq('user_id', profile.id)
    .maybeSingle();

  if (existing) {
    const { error } = await supabase.from('project_likes').delete().eq('id', existing.id);
    return { liked: false, error };
  }
  const { error } = await supabase
    .from('project_likes').insert({ project_id: projectId, user_id: profile.id });
  return { liked: true, error };
}

export async function getComments(projectId) {
  const { data, error } = await supabase
    .from('project_comments')
    .select(`id, content, created_at, user_id, user:users!user_id(id, firstname, lastname, image)`)
    .eq('project_id', projectId)
    .order('created_at', { ascending: true });
  return { data, error };
}

export async function addComment(projectId, content) {
  const profile = await requireProfile();
  if (!profile) return { error: { message: 'Not authenticated' } };
  const { data, error } = await supabase
    .from('project_comments')
    .insert({ project_id: projectId, user_id: profile.id, content })
    .select(`id, content, created_at, user_id, user:users!user_id(id, firstname, lastname, image)`)
    .single();
  return { data, error };
}

export async function deleteComment(commentId) {
  const { error } = await supabase.from('project_comments').delete().eq('id', commentId);
  return { error };
}

// ─────────────────────────────────────────────────────────────────────────────
//  EVENTS
// ─────────────────────────────────────────────────────────────────────────────

export async function getEvents() {
  const { data, error } = await supabase
    .from('events')
    .select(`*, registrations:event_registrations(count)`)
    .eq('is_visible', true)
    .order('start_at', { ascending: true });
  return { data, error };
}

export async function joinEvent(eventId) {
  const profile = await requireProfile();
  if (!profile) return { error: { message: 'Not authenticated' } };
  const { error } = await supabase
    .from('event_registrations')
    .insert({ event_id: eventId, user_id: profile.id });
  return { error };
}

export async function quitEvent(eventId) {
  const profile = await requireProfile();
  if (!profile) return { error: { message: 'Not authenticated' } };
  const { error } = await supabase
    .from('event_registrations')
    .delete()
    .eq('event_id', eventId)
    .eq('user_id', profile.id);
  return { error };
}

// ─────────────────────────────────────────────────────────────────────────────
//  ANNOUNCEMENTS
// ─────────────────────────────────────────────────────────────────────────────

export async function getAnnouncements() {
  const { data, error } = await supabase
    .from('announcements')
    .select(`*, author:users!author_id(firstname, lastname, image)`)
    .eq('is_visible', true)
    .order('is_pinned', { ascending: false })
    .order('created_at', { ascending: false });
  return { data, error };
}

// ─────────────────────────────────────────────────────────────────────────────
//  SOCIAL
// ─────────────────────────────────────────────────────────────────────────────

export async function toggleFollow(targetUserId) {
  const profile = await requireProfile();
  if (!profile) return { error: { message: 'Not authenticated' } };
  if (profile.id === targetUserId) return { error: { message: 'Cannot follow yourself' } };

  const { data: existing } = await supabase
    .from('user_follows').select('id')
    .eq('follower_id', profile.id).eq('following_id', targetUserId)
    .maybeSingle();

  if (existing) {
    const { error } = await supabase.from('user_follows').delete().eq('id', existing.id);
    return { following: false, error };
  }
  const { error } = await supabase
    .from('user_follows').insert({ follower_id: profile.id, following_id: targetUserId });
  return { following: true, error };
}

export async function searchUsers(name) {
  const { data, error } = await supabase
    .from('users')
    .select('id, firstname, lastname, image, grade, domain, role')
    .or(`firstname.ilike.%${name}%,lastname.ilike.%${name}%`)
    .limit(20);
  return { data, error };
}

export async function getUserInfo(userId) {
  const { data: user, error } = await supabase
    .from('users').select('*').eq('id', userId).maybeSingle();
  if (error || !user) return { user: null, projects: [], error };

  const [{ data: projects }, followersRes, followingRes, isFollowingRes] = await Promise.all([
    supabase.from('projects').select('id,title,description,category,status')
      .eq('owner_id', userId).eq('is_visible', true),
    supabase.from('user_follows').select('*', { count: 'exact', head: true }).eq('following_id', userId),
    supabase.from('user_follows').select('*', { count: 'exact', head: true }).eq('follower_id', userId),
    (async () => {
      const { data: { user: authUser } } = await supabase.auth.getUser();
      if (!authUser) return { data: null };
      const { data: me } = await supabase.from('users').select('id').eq('auth_id', authUser.id).maybeSingle();
      if (!me) return { data: null };
      return supabase.from('user_follows').select('id')
        .eq('follower_id', me.id).eq('following_id', userId).maybeSingle();
    })(),
  ]);

  return {
    user: {
      ...user,
      followers_count: followersRes.count ?? 0,
      following_count: followingRes.count ?? 0,
      is_following:    !!isFollowingRes.data,
    },
    projects: projects ?? [],
  };
}

// ─────────────────────────────────────────────────────────────────────────────
//  STATS
// ─────────────────────────────────────────────────────────────────────────────

export async function getStats() {
  const [{ count: projects }, { count: events }, { count: users }] = await Promise.all([
    supabase.from('projects').select('*', { count: 'exact', head: true }).eq('is_visible', true),
    supabase.from('events').select('*', { count: 'exact', head: true }).eq('is_visible', true),
    supabase.from('users').select('*', { count: 'exact', head: true }).neq('role', 'Admin'),
  ]);
  return { projects: projects ?? 0, events: events ?? 0, users: users ?? 0 };
}

// ─────────────────────────────────────────────────────────────────────────────
//  ADMIN
// ─────────────────────────────────────────────────────────────────────────────

export async function adminGetAllUsers() {
  const { data, error } = await supabase
    .from('users').select('*').neq('role', 'Admin')
    .order('created_at', { ascending: false });
  return { data, error };
}

export async function adminBanUser(userId, reason) {
  const { data, error } = await supabase
    .from('users')
    .update({ is_banned: true, ban_reason: reason })
    .eq('id', userId).select().single();
  return { data, error };
}

export async function adminUnbanUser(userId) {
  const { data, error } = await supabase
    .from('users')
    .update({ is_banned: false, ban_reason: null })
    .eq('id', userId).select().single();
  return { data, error };
}

export async function adminWarnUser(userId) {
  const { data: u } = await supabase
    .from('users').select('warnings').eq('id', userId).single();
  const newWarnings = (u?.warnings ?? 0) + 1;
  const update = { warnings: newWarnings };
  if (newWarnings >= 3) {
    update.is_banned  = true;
    update.ban_reason = 'Automatically banned after 3 warnings.';
  }
  const { data, error } = await supabase
    .from('users').update(update).eq('id', userId).select().single();
  return { data, error, auto_banned: newWarnings >= 3 };
}

export async function adminGetWithdrawals() {
  const { data, error } = await supabase
    .from('withdrawals')
    .select(`*, user:users!user_id(firstname, lastname, image)`)
    .order('created_at', { ascending: false });
  return { data, error };
}

export async function adminUpdateWithdrawal(id, status) {
  const { data, error } = await supabase
    .from('withdrawals')
    .update({ status })
    .eq('id', id)
    .select()
    .single();
  return { data, error };
}

// ─────────────────────────────────────────────────────────────────────────────
//  UI HELPERS
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

/** Format ISO date string as "12 Jan 2025" */
export function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
  });
}

/** Escape HTML to prevent XSS */
export function esc(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
