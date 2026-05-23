/**
 * MCP OAuth 2.1 authorization server.
 *
 * Wraps Supabase email/password auth in the OAuth 2.1 + PKCE flow
 * that Claude.ai expects when connecting to a remote MCP server.
 *
 * Flow:
 *   1. Claude discovers /.well-known/oauth-authorization-server
 *   2. Opens browser → GET /authorize → redirects to GET /login (HTML form)
 *   3. Parent submits credentials → POST /login calls Supabase, stores code
 *   4. Browser redirects to Claude with ?code=...
 *   5. Claude calls POST /token with code + PKCE verifier → gets Supabase JWT
 *   6. All /mcp requests carry Authorization: Bearer <jwt>
 *   7. requireAuth middleware validates JWT and attaches parentId to the request
 */

import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { createHash, randomBytes } from "crypto";
import type { Request, Response, NextFunction } from "express";

const MCP_BASE_URL = (process.env.MCP_BASE_URL ?? `http://localhost:${process.env.PORT ?? 3001}`).replace(/\/+$/, "");

// Lazily initialised so missing env vars produce a clear error at first use,
// not a cryptic Supabase internal error at module load time.
let _supabase: SupabaseClient | null = null;

function getSupabase(): SupabaseClient {
  if (_supabase) return _supabase;
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_KEY;
  if (!url || !key) {
    throw new Error(
      "Missing env vars: SUPABASE_URL and SUPABASE_KEY must be set on the MCP App service in Render."
    );
  }
  _supabase = createClient(url, key);
  return _supabase;
}

// ── Augmented request type ────────────────────────────────────────────

export interface AuthenticatedRequest extends Request {
  parentId: string;
  userToken: string;
}

// ── In-memory code store (5-min TTL) ─────────────────────────────────

interface PendingCode {
  jwt: string;
  codeChallenge: string;
  expiresAt: number;
}

const pendingCodes = new Map<string, PendingCode>();

setInterval(() => {
  const now = Date.now();
  for (const [k, v] of pendingCodes) {
    if (v.expiresAt < now) pendingCodes.delete(k);
  }
}, 60_000);

// ── PKCE ─────────────────────────────────────────────────────────────

function verifyPkce(verifier: string, challenge: string): boolean {
  const computed = createHash("sha256").update(verifier).digest("base64url");
  return computed === challenge;
}

// ── XSS prevention for inline HTML ───────────────────────────────────

function esc(s: string | undefined): string {
  return (s ?? "").replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ── OAuth discovery ───────────────────────────────────────────────────

export function oauthMetadata(_req: Request, res: Response): void {
  res.json({
    issuer: MCP_BASE_URL,
    authorization_endpoint: `${MCP_BASE_URL}/authorize`,
    token_endpoint: `${MCP_BASE_URL}/token`,
    registration_endpoint: `${MCP_BASE_URL}/register`,
    response_types_supported: ["code"],
    grant_types_supported: ["authorization_code"],
    code_challenge_methods_supported: ["S256"],
    token_endpoint_auth_methods_supported: ["none"],
  });
}

export function protectedResourceMetadata(_req: Request, res: Response): void {
  res.json({
    resource: MCP_BASE_URL,
    authorization_servers: [MCP_BASE_URL],
  });
}

// ── POST /register — Dynamic Client Registration (RFC 7591) ─────────────
// claude.ai and other MCP clients don't have pre-shared client IDs, so they
// register themselves on first connect. We don't enforce a per-client secret
// because PKCE + Supabase-bound auth codes already prevent token theft. We
// echo back a constant client_id; tracking individual MCP clients adds DB
// surface without any real security benefit at this scale.
export function dynamicRegister(req: Request, res: Response): void {
  const body = (req.body ?? {}) as { redirect_uris?: string[]; client_name?: string };
  res.status(201).json({
    client_id: "marathi-mitra-mcp-public",
    client_id_issued_at: Math.floor(Date.now() / 1000),
    redirect_uris: body.redirect_uris ?? [],
    client_name: body.client_name ?? "MCP Client",
    token_endpoint_auth_method: "none",
    grant_types: ["authorization_code"],
    response_types: ["code"],
  });
}

// ── GET /authorize ────────────────────────────────────────────────────

export function authorize(req: Request, res: Response): void {
  const { redirect_uri, state, code_challenge, client_id } = req.query as Record<string, string>;
  if (!redirect_uri || !code_challenge) {
    res.status(400).send("Missing redirect_uri or code_challenge");
    return;
  }
  const params = new URLSearchParams({
    redirect_uri,
    state: state ?? "",
    code_challenge,
    client_id: client_id ?? "",
  });
  res.redirect(`/login?${params}`);
}

// ── GET /login — login form ───────────────────────────────────────────

export function loginPage(req: Request, res: Response): void {
  const q = req.query as Record<string, string>;
  const errorHtml = q.error ? `<div class="error">${esc(q.error)}</div>` : "";

  res.setHeader("Content-Type", "text/html; charset=utf-8");
  res.send(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>MarathiMitra — Sign In</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:system-ui,sans-serif;background:#f5f0eb;display:flex;align-items:center;justify-content:center;min-height:100vh}
    .card{background:#fff;border-radius:12px;padding:2rem;width:100%;max-width:380px;box-shadow:0 2px 16px rgba(0,0,0,.1)}
    .logo{text-align:center;font-size:2.5rem;margin-bottom:.5rem}
    h1{text-align:center;font-size:1.25rem;color:#1a1a1a;margin-bottom:.25rem}
    .sub{text-align:center;color:#666;font-size:.875rem;margin-bottom:1.5rem}
    label{display:block;font-size:.875rem;font-weight:500;color:#333;margin-bottom:.375rem}
    input[type=email],input[type=password]{display:block;width:100%;padding:.625rem .75rem;border:1px solid #ddd;border-radius:8px;font-size:1rem;margin-bottom:1rem;outline:none}
    input:focus{border-color:#f97316;box-shadow:0 0 0 3px rgba(249,115,22,.1)}
    button{width:100%;padding:.75rem;background:#f97316;color:#fff;border:none;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer}
    button:hover{background:#ea6c0a}
    .error{color:#dc2626;font-size:.875rem;margin-bottom:1rem;padding:.5rem .75rem;background:#fef2f2;border-radius:6px}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">🇮🇳</div>
    <h1>MarathiMitra</h1>
    <p class="sub">Sign in to connect your account to Claude</p>
    ${errorHtml}
    <form method="POST" action="/login">
      <input type="hidden" name="redirect_uri" value="${esc(q.redirect_uri)}">
      <input type="hidden" name="state" value="${esc(q.state)}">
      <input type="hidden" name="code_challenge" value="${esc(q.code_challenge)}">
      <input type="hidden" name="client_id" value="${esc(q.client_id)}">
      <label for="email">Email</label>
      <input type="email" id="email" name="email" required autocomplete="email">
      <label for="password">Password</label>
      <input type="password" id="password" name="password" required autocomplete="current-password">
      <button type="submit">Sign In</button>
    </form>
  </div>
</body>
</html>`);
}

// ── POST /login — validate credentials, issue code ───────────────────

export async function loginSubmit(req: Request, res: Response): Promise<void> {
  const { email, password, redirect_uri, state, code_challenge, client_id } =
    req.body as Record<string, string>;

  if (!email || !password || !redirect_uri || !code_challenge) {
    res.status(400).send("Bad request");
    return;
  }

  const { data, error } = await getSupabase().auth.signInWithPassword({ email, password });

  if (error || !data.session) {
    const params = new URLSearchParams({
      redirect_uri,
      state: state ?? "",
      code_challenge,
      client_id: client_id ?? "",
      error: "Invalid email or password",
    });
    res.redirect(`/login?${params}`);
    return;
  }

  const code = randomBytes(32).toString("hex");
  pendingCodes.set(code, {
    jwt: data.session.access_token,
    codeChallenge: code_challenge,
    expiresAt: Date.now() + 5 * 60 * 1000,
  });

  const callbackUrl = new URL(redirect_uri);
  callbackUrl.searchParams.set("code", code);
  if (state) callbackUrl.searchParams.set("state", state);
  res.redirect(callbackUrl.toString());
}

// ── POST /token — PKCE exchange ───────────────────────────────────────

export function tokenExchange(req: Request, res: Response): void {
  const { grant_type, code, code_verifier } = req.body as Record<string, string>;

  if (grant_type !== "authorization_code") {
    res.status(400).json({ error: "unsupported_grant_type" });
    return;
  }
  if (!code || !code_verifier) {
    res.status(400).json({ error: "invalid_request" });
    return;
  }

  const entry = pendingCodes.get(code);
  if (!entry || entry.expiresAt < Date.now()) {
    res.status(400).json({ error: "invalid_grant", error_description: "Code expired or not found" });
    return;
  }
  if (!verifyPkce(code_verifier, entry.codeChallenge)) {
    res.status(400).json({ error: "invalid_grant", error_description: "PKCE verification failed" });
    return;
  }

  pendingCodes.delete(code);
  res.json({ access_token: entry.jwt, token_type: "bearer" });
}

// ── Middleware: validate Bearer token on /mcp ─────────────────────────

// Per MCP authorization spec, 401 responses MUST advertise the
// protected-resource metadata URL via WWW-Authenticate so clients
// (claude.ai, Claude Desktop) can discover the OAuth flow. Without
// this header the client gives up with "Couldn't reach the MCP server."
const WWW_AUTHENTICATE_HEADER =
  `Bearer resource_metadata="${MCP_BASE_URL}/.well-known/oauth-protected-resource"`;

export async function requireAuth(req: Request, res: Response, next: NextFunction): Promise<void> {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith("Bearer ")) {
    res.set("WWW-Authenticate", WWW_AUTHENTICATE_HEADER);
    res.status(401).json({ error: "unauthorized", error_description: "Missing Bearer token" });
    return;
  }

  const token = authHeader.slice(7);
  const { data, error } = await getSupabase().auth.getUser(token);

  if (error || !data.user) {
    res.set("WWW-Authenticate", WWW_AUTHENTICATE_HEADER);
    res.status(401).json({ error: "unauthorized", error_description: "Invalid or expired token" });
    return;
  }

  (req as AuthenticatedRequest).parentId = data.user.id;
  (req as AuthenticatedRequest).userToken = token;
  next();
}
