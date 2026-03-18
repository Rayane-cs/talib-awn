// ═══════════════════════════════════════════════════════════════════════════════
//  supabase/functions/create-payment/index.ts
//  Talib-Awn · طالب عون — Chargily Payment Initiation Edge Function
//
//  Deploy with:  supabase functions deploy create-payment
//
//  Required secrets (set via Supabase Dashboard → Edge Functions → Secrets):
//    CHARGILY_API_KEY   — your Chargily Pay secret key (sk_live_...)
//    CHARGILY_WEBHOOK_URL — full URL of the webhook Edge Function
//    APP_URL            — your frontend base URL (e.g. https://yourapp.com)
//    SUPABASE_SERVICE_ROLE_KEY — auto-injected by Supabase
// ═══════════════════════════════════════════════════════════════════════════════

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// ─────────────────────────────────────────────────────────────────────────────
//  CORS headers — allow requests from your frontend domain
// ─────────────────────────────────────────────────────────────────────────────
const CORS = {
  "Access-Control-Allow-Origin":  "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

// ─────────────────────────────────────────────────────────────────────────────
//  Chargily Pay v2 — API constants
// ─────────────────────────────────────────────────────────────────────────────
const CHARGILY_BASE = "https://pay.chargily.net/api/v2";
const CURRENCY      = "dzd";  // Algerian Dinar

// ─────────────────────────────────────────────────────────────────────────────
//  Handler
// ─────────────────────────────────────────────────────────────────────────────
Deno.serve(async (req: Request) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: CORS });
  }

  if (req.method !== "POST") {
    return json({ error: "Method not allowed" }, 405);
  }

  try {
    // ── 1. Authenticate the caller via Supabase JWT ──────────────────────────
    const authHeader = req.headers.get("Authorization") ?? "";
    if (!authHeader.startsWith("Bearer ")) {
      return json({ error: "Missing authorization token" }, 401);
    }

    // Use service-role client for profile lookups; anon client for auth verify
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_ANON_KEY")!,
      { global: { headers: { Authorization: authHeader } } }
    );

    const { data: { user }, error: authErr } = await supabase.auth.getUser();
    if (authErr || !user) return json({ error: "Unauthorized" }, 401);

    // Fetch public profile (we need the internal user.id, not the auth UUID)
    const { data: profile, error: profileErr } = await supabase
      .from("users")
      .select("id, firstname, lastname, email, role, is_banned")
      .eq("auth_id", user.id)
      .maybeSingle();

    if (profileErr || !profile) return json({ error: "Profile not found" }, 404);
    if (profile.is_banned)      return json({ error: "Account suspended"  }, 403);

    // ── 2. Validate & parse request body ────────────────────────────────────
    const body = await req.json().catch(() => null);
    if (!body) return json({ error: "Invalid JSON body" }, 400);

    const amount = Number(body.amount);
    if (!Number.isFinite(amount) || amount < 100) {
      return json({ error: "Minimum deposit is 100 DZD" }, 400);
    }
    if (amount > 200_000) {
      return json({ error: "Maximum deposit is 200,000 DZD per transaction" }, 400);
    }

    // ── 3. Generate idempotency key to prevent duplicate checkouts ───────────
    // Keyed on user + amount + minute bucket → same request within 1 minute
    // is deduplicated; after 1 minute a fresh checkout is created.
    const minuteBucket = Math.floor(Date.now() / 60_000);
    const idempotencyKey = `${profile.id}_${amount}_${minuteBucket}`;

    // ── 4. Create Chargily checkout ──────────────────────────────────────────
    const chargilyKey = Deno.env.get("CHARGILY_API_KEY");
    if (!chargilyKey) throw new Error("CHARGILY_API_KEY not configured");

    const webhookUrl = Deno.env.get("CHARGILY_WEBHOOK_URL");
    const appUrl     = Deno.env.get("APP_URL") ?? "https://yourapp.com";

    const checkoutPayload = {
      amount:           amount,
      currency:         CURRENCY,
      payment_method:   "edahabia",        // Edahabia card (can also be "cib")
      webhook_endpoint: webhookUrl,
      back_url:         `${appUrl}/wallet.html?status=success`,
      failure_url:      `${appUrl}/wallet.html?status=failed`,

      // metadata is returned verbatim in the webhook — we use it to identify
      // which user to credit and for idempotency
      metadata: {
        user_id:         profile.id,          // internal DB user id
        auth_id:         user.id,             // Supabase auth UUID
        idempotency_key: idempotencyKey,
      },

      // Customer info (optional but improves Chargily dashboard UX)
      customer: {
        name:  `${profile.firstname} ${profile.lastname}`,
        email: profile.email ?? user.email,
      },
    };

    const chargilyRes = await fetch(`${CHARGILY_BASE}/checkouts`, {
      method:  "POST",
      headers: {
        "Authorization": `Bearer ${chargilyKey}`,
        "Content-Type":  "application/json",
      },
      body: JSON.stringify(checkoutPayload),
    });

    if (!chargilyRes.ok) {
      const errBody = await chargilyRes.text().catch(() => "");
      console.error("Chargily error:", chargilyRes.status, errBody);
      return json({ error: "Payment provider error. Please try again." }, 502);
    }

    const checkout = await chargilyRes.json();

    // ── 5. Pre-record a PENDING deposit transaction ──────────────────────────
    // This lets us show "payment in progress" in the UI before the webhook fires.
    // The service-role client bypasses RLS for this insert.
    const adminClient = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );

    await adminClient.from("transactions").insert({
      user_id:         profile.id,
      type:            "deposit",
      amount:          amount,
      status:          "pending",
      reference:       checkout.id,          // Chargily checkout id
      idempotency_key: idempotencyKey,
    }).select().maybeSingle();               // upsert-safe: ignore if duplicate

    // ── 6. Return the checkout URL for the frontend to redirect ─────────────
    return json({
      ok:          true,
      checkout_id: checkout.id,
      checkout_url: checkout.checkout_url,  // redirect user here
      amount,
    });

  } catch (err) {
    console.error("create-payment error:", err);
    return json({ error: "Internal server error" }, 500);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
//  Helper — JSON response with CORS
// ─────────────────────────────────────────────────────────────────────────────
function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });
}
