import fs from 'fs';
import { chromium } from './lib.mjs';
const HM = '/home/user/roteirosaas/tools/help-media';
const { DEMO, login, req, APP, chromiumPath } = await import(`${HM}/lib/api.mjs`);
const { prepararContexto } = await import(`${HM}/lib/sessao.mjs`);
const st = JSON.parse(fs.readFileSync('film-state.json'));
const token = await login(DEMO.email, DEMO.password);
await req(token, 'POST', `/pages/${st.pageId}/publish`, { publish: true });
const browser = await chromium.launch({ executablePath: chromiumPath() });
const out = 'real';
for (const layout of ['cartao', 'imersivo']) {
  if (layout === 'imersivo') {
    const full = await req(token, 'GET', `/pages/${st.pageId}`); const cfg = full.config_json || full.config;
    cfg.sections[0].layout = 'immersive';
    await req(token, 'PUT', `/pages/${st.pageId}`, { title: full.title, slug: full.slug, config_json: cfg });
  }
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true, locale: 'pt-BR',
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1' });
  await prepararContexto(ctx);
  await ctx.addInitScript(() => localStorage.setItem('global_cookie_consent', 'accepted'));
  const page = await ctx.newPage();
  await page.goto(`${APP}/${st.agencySlug}/gramado-e-canela`, { waitUntil: 'networkidle' });
  const H = await page.evaluate(() => document.documentElement.scrollHeight);
  for (let y = 0; y < H; y += 500) { await page.evaluate(y => window.scrollTo(0, y), y); await page.waitForTimeout(200); }
  await page.evaluate(() => window.scrollTo(0, 0)); await page.waitForTimeout(2500);
  await page.screenshot({ path: `${out}/gramado-${layout}-top.png` });
  await page.screenshot({ path: `${out}/gramado-${layout}-long.png`, fullPage: true, clip: { x: 0, y: 0, width: 390, height: Math.min(H, 844 * 4) } });
  console.log(layout, H);
  await ctx.close();
}
// leave the page as the film ends it (Cartão)
const full = await req(token, 'GET', `/pages/${st.pageId}`); const cfg = full.config_json || full.config; cfg.sections[0].layout = 'card';
await req(token, 'PUT', `/pages/${st.pageId}`, { title: full.title, slug: full.slug, config_json: cfg });
await browser.close();
