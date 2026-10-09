// Acesso à API do sistema rodando e dados da conta de demonstração.
import fs from 'fs';

export const API = (process.env.HELP_API || 'http://127.0.0.1:8000/api/v1').replace(/\/+$/, '');
export const APP = (process.env.HELP_APP || 'http://127.0.0.1:5173').replace(/\/+$/, '');

/** Conta da agência de demonstração (só existe no banco local). */
export const DEMO = { name: 'Marina Souza', email: 'marina@rotasulviagens.com.br', password: 'RotaSul#2026' };

/** Chromium já instalado (PW_CHROMIUM) ou o do Playwright. */
export const chromiumPath = () =>
  process.env.PW_CHROMIUM || (fs.existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined);

export async function login(email, password) {
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(`${API}/auth/login`, { method: 'POST', body });
  if (!res.ok) throw new Error(`login ${email}: ${res.status} ${await res.text()}`);
  return (await res.json()).access_token;
}

export async function req(token, method, path, body) {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(body ? { 'Content-Type': 'application/json' } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${method} ${path}: ${res.status} ${(await res.text()).slice(0, 300)}`);
  return res.status === 204 ? null : res.json().catch(() => null);
}
