// ─────────────────────────────────────────────────────────────────────────────
//  wallet.js  —  Talib-Awn · طالب عون
//  Client-side wallet & payment helpers.
//  Import alongside supabase.js:  import { ... } from './wallet.js';
// ─────────────────────────────────────────────────────────────────────────────

import { supabase, requireProfile } from './supabase.js';

// ─────────────────────────────────────────────────────────────────────────────
//  CONFIG — update the Edge Function URLs after deploying
// ─────────────────────────────────────────────────────────────────────────────
const SUPABASE_URL        = 'https://lzvopmmasfvwtepcrpkw.supabase.co';
const CREATE_PAYMENT_URL  = `${SUPABASE_URL}/functions/v1/create-payment`;


// ═════════════════════════════════════════════════════════════════════════════
//  WALLET
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Fetch the current user's wallet balance.
 * Returns { balance: number } or { error }
 */
export async function getWalletBalance() {
  const profile = await requireProfile();
  if (!profile) return { balance: 0, error: { message: 'Not authenticated' } };

  const { data, error } = await supabase
    .from('wallets')
    .select('balance')
    .eq('user_id', profile.id)
    .maybeSingle();

  return { balance: data?.balance ?? 0, error };
}

/**
 * Fetch full wallet row (balance + timestamps).
 */
export async function getWallet() {
  const profile = await requireProfile();
  if (!profile) return { data: null, error: { message: 'Not authenticated' } };

  const { data, error } = await supabase
    .from('wallets')
    .select('*')
    .eq('user_id', profile.id)
    .maybeSingle();

  return { data, error };
}


// ═════════════════════════════════════════════════════════════════════════════
//  TRANSACTIONS
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Fetch the current user's transaction history, newest first.
 * @param {number} limit  — max rows to return (default 50)
 */
export async function getTransactions(limit = 50) {
  const profile = await requireProfile();
  if (!profile) return { data: [], error: { message: 'Not authenticated' } };

  const { data, error } = await supabase
    .from('transactions')
    .select('*')
    .eq('user_id', profile.id)
    .order('created_at', { ascending: false })
    .limit(limit);

  return { data: data ?? [], error };
}


// ═════════════════════════════════════════════════════════════════════════════
//  DEPOSITS  (via Chargily)
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Initiate a Chargily deposit.
 * Calls the create-payment Edge Function (server-side, API key protected).
 * On success, redirects the browser to the Chargily checkout page.
 *
 * @param {number} amount  — amount in DZD (minimum 100)
 * @returns {{ error: string } | never}  — only returns on error; on success it redirects
 */
export async function initiateDeposit(amount) {
  // Get the current auth session token to send to the Edge Function
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return { error: 'Not authenticated. Please log in.' };

  // Validate amount before hitting the server
  const n = Number(amount);
  if (!Number.isFinite(n) || n < 100) return { error: 'Minimum deposit is 100 DZD.' };
  if (n > 200_000)                    return { error: 'Maximum deposit is 200,000 DZD.' };

  const res = await fetch(CREATE_PAYMENT_URL, {
    method:  'POST',
    headers: {
      'Content-Type':  'application/json',
      'Authorization': `Bearer ${session.access_token}`,
    },
    body: JSON.stringify({ amount: n }),
  });

  const payload = await res.json().catch(() => ({ error: 'Server returned invalid response.' }));

  if (!res.ok || !payload.ok) {
    return { error: payload.error ?? 'Payment initiation failed. Try again.' };
  }

  // Redirect to Chargily checkout (user pays there, then Chargily calls our webhook)
  window.location.href = payload.checkout_url;
  // Never reaches here on success
  return {};
}


// ═════════════════════════════════════════════════════════════════════════════
//  ESCROW
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Employer: lock funds for a hire.
 * @param {object} params
 * @param {number} params.studentId  — DB user id of the student
 * @param {number} params.amount     — amount in DZD
 * @param {number} [params.jobId]    — optional job/contract id
 * @param {string} [params.note]     — optional note
 */
export async function createEscrow({ studentId, amount, jobId = null, note = null }) {
  const profile = await requireProfile();
  if (!profile) return { data: null, error: { message: 'Not authenticated' } };

  const { data, error } = await supabase.rpc('wallet_create_escrow', {
    p_employer_id: profile.id,
    p_student_id:  studentId,
    p_amount:      amount,
    p_job_id:      jobId,
    p_note:        note,
  });

  return { data, error };
}

/**
 * Release escrow to student (job completed).
 * @param {number} escrowId
 */
export async function releaseEscrow(escrowId) {
  const { data, error } = await supabase.rpc('wallet_release_escrow', {
    p_escrow_id: escrowId,
  });
  return { data, error };
}

/**
 * Cancel escrow — refunds employer.
 * @param {number} escrowId
 */
export async function cancelEscrow(escrowId) {
  const { data, error } = await supabase.rpc('wallet_cancel_escrow', {
    p_escrow_id: escrowId,
  });
  return { data, error };
}

/**
 * Fetch escrows where the current user is the employer.
 */
export async function getMyEscrowsAsEmployer() {
  const profile = await requireProfile();
  if (!profile) return { data: [], error: { message: 'Not authenticated' } };

  const { data, error } = await supabase
    .from('escrows')
    .select(`
      *,
      student:users!student_id(id, firstname, lastname, image)
    `)
    .eq('employer_id', profile.id)
    .order('created_at', { ascending: false });

  return { data: data ?? [], error };
}

/**
 * Fetch escrows where the current user is the student.
 */
export async function getMyEscrowsAsStudent() {
  const profile = await requireProfile();
  if (!profile) return { data: [], error: { message: 'Not authenticated' } };

  const { data, error } = await supabase
    .from('escrows')
    .select(`
      *,
      employer:users!employer_id(id, firstname, lastname, image)
    `)
    .eq('student_id', profile.id)
    .order('created_at', { ascending: false });

  return { data: data ?? [], error };
}


// ═════════════════════════════════════════════════════════════════════════════
//  WITHDRAWALS
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Student: request a manual withdrawal.
 * @param {object} params
 * @param {number} params.amount          — amount in DZD (min 500)
 * @param {string} params.payoutMethod    — 'ccp' | 'edahabia' | 'baridimob'
 * @param {string} params.accountNumber   — CCP/card number (stored encrypted)
 */
export async function requestWithdrawal({ amount, payoutMethod, accountNumber }) {
  const { data, error } = await supabase.rpc('wallet_request_withdrawal', {
    p_amount:          amount,
    p_payout_method:   payoutMethod,
    p_account_number:  accountNumber,
  });
  return { data, error };
}

/**
 * Fetch current user's withdrawal history.
 */
export async function getWithdrawals() {
  const profile = await requireProfile();
  if (!profile) return { data: [], error: { message: 'Not authenticated' } };

  const { data, error } = await supabase
    .from('withdrawals')
    .select('*')
    .eq('user_id', profile.id)
    .order('created_at', { ascending: false });

  return { data: data ?? [], error };
}


// ═════════════════════════════════════════════════════════════════════════════
//  ADMIN
// ═════════════════════════════════════════════════════════════════════════════

/** Admin: fetch all pending withdrawal requests */
export async function adminGetPendingWithdrawals() {
  const { data, error } = await supabase
    .from('withdrawals')
    .select(`*, user:users!user_id(id, firstname, lastname, email, image)`)
    .eq('status', 'pending')
    .order('created_at', { ascending: true });   // oldest first for fairness
  return { data: data ?? [], error };
}

/** Admin: approve withdrawal */
export async function adminApproveWithdrawal(withdrawalId, note = null) {
  const { data, error } = await supabase.rpc('admin_approve_withdrawal', {
    p_wd_id: withdrawalId,
    p_note:  note,
  });
  return { data, error };
}

/** Admin: reject withdrawal */
export async function adminRejectWithdrawal(withdrawalId, note = null) {
  const { data, error } = await supabase.rpc('admin_reject_withdrawal', {
    p_wd_id: withdrawalId,
    p_note:  note,
  });
  return { data, error };
}

/** Admin: fetch all wallets with user info */
export async function adminGetAllWallets() {
  const { data, error } = await supabase
    .from('wallets')
    .select(`*, user:users!user_id(id, firstname, lastname, email, role, image)`)
    .order('balance', { ascending: false });
  return { data: data ?? [], error };
}


// ═════════════════════════════════════════════════════════════════════════════
//  FORMATTING HELPERS
// ═════════════════════════════════════════════════════════════════════════════

/** Format DZD amount: "12,500.00 DZD" */
export function formatDZD(amount) {
  return new Intl.NumberFormat('en-DZ', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount) + ' DZD';
}

/** Transaction type → { label, colorClass, icon } */
export function txMeta(type) {
  const map = {
    deposit:  { label: 'Deposit',       color: 'green',  icon: '↓' },
    escrow:   { label: 'Escrow Hold',   color: 'amber',  icon: '⏸' },
    release:  { label: 'Job Payment',   color: 'green',  icon: '↓' },
    refund:   { label: 'Refund',        color: 'blue',   icon: '↩' },
    withdraw: { label: 'Withdrawal',    color: 'red',    icon: '↑' },
  };
  return map[type] ?? { label: type, color: 'gray', icon: '·' };
}

/** Transaction status → badge label */
export function txStatusLabel(status) {
  return { pending: 'Pending', completed: 'Completed', failed: 'Failed' }[status] ?? status;
}
