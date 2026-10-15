// Real published Roteiro Online pages (the same three shown on the sales LP) at phone size, 3x.
import fs from 'fs';
import { chromium } from './lib.mjs';
const HM = '/home/user/roteirosaas/tools/help-media';
const { prepararContexto } = await import(`${HM}/lib/sessao.mjs`);
const { chromiumPath } = await import(`${HM}/lib/api.mjs`);
const PAGES = [
  { id: 'foz', url: 'https://roteiroonline.com/status/foz-do-iguacu' },
  { id: 'italia', url: 'https://roteiroonline.com/beth-tur/itaia-magnifica' },
  { id: 'abrolhos', url: 'https://roteiroonline.com/ecoar-ecoturismo/abrolhos' },
];
fs.mkdirSync('real', { recursive: true });
const proxy = process.env.HTTPS_PROXY;
const browser = await chromium.launch({ executablePath: chromiumPath(), ...(proxy ? { proxy: { server: proxy } } : {}) });
for (const { id, url } of PAGES) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true, locale: 'pt-BR', ignoreHTTPSErrors: !!proxy,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1' });
  await prepararContexto(ctx);
  if (proxy) await ctx.route(/^https:\/\/(?!fonts\.)/, async r => { try { await r.fulfill({ response: await r.fetch({ maxRetries: 2, timeout: 30000 }) }); } catch { await r.abort().catch(() => {}); } });
  // read-only: block any tracking beacons / POSTs to the production API
  await ctx.route(/roteiroonline\.com\/api\/.*(stats|track|event|visit)/i, r => r.fulfill({ status: 204, body: '' }));
  await ctx.addInitScript(() => localStorage.setItem('global_cookie_consent', 'accepted'));
  const page = await ctx.newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForLoadState('load', { timeout: 30000 }).catch(() => {});
  // scroll through once so lazy images load
  const H = await page.evaluate(() => document.documentElement.scrollHeight);
  for (let y = 0; y < Math.min(H, 9000); y += 600) { await page.evaluate(y => window.scrollTo(0, y), y); await page.waitForTimeout(250); }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.evaluate(() => Promise.race([Promise.all([...document.images].map(i => i.complete || new Promise(r => { i.onload = i.onerror = r; }))), new Promise(r => setTimeout(r, 15000))]));
  await page.waitForTimeout(3000);
  await page.screenshot({ path: `real/${id}-top.png` });
  const h = Math.min(H, 844 * 4);
  await page.screenshot({ path: `real/${id}-long.png`, fullPage: true, clip: { x: 0, y: 0, width: 390, height: h } });
  console.log(id, 'height', H);
  await ctx.close();
}
await browser.close();
