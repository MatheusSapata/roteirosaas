// Capture helpers: real Roteiro Online panel (local stack) at high DPR.
import fs from 'fs';
const HM = '/home/user/roteirosaas/tools/help-media';
const { chromium } = await import(`${HM}/node_modules/playwright/index.mjs`);
const { prepararContexto } = await import(`${HM}/lib/sessao.mjs`);
const { APP, DEMO, chromiumPath } = await import(`${HM}/lib/api.mjs`);
export { APP, DEMO, chromium };
export const launch = () => chromium.launch({ executablePath: chromiumPath(), args: ['--lang=pt-BR', '--font-render-hinting=none'] });
const CLEAN = `a[href^="https://wa.me/5553991800903"]{display:none!important} html{scrollbar-width:none} html::-webkit-scrollbar{display:none} *::-webkit-scrollbar{display:none!important}`;
export async function panel(browser, { w = 1440, h = 900, dpr = 2, theme = 'light', collapsed = true } = {}) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: dpr, locale: 'pt-BR', timezoneId: 'America/Sao_Paulo' });
  await prepararContexto(ctx);
  await ctx.addInitScript(([t, css, c]) => {
    localStorage.setItem('global_cookie_consent', 'accepted');
    localStorage.setItem('admin-theme', t);
    localStorage.setItem('admin_sidebar_collapsed', c ? '1' : '0');
    document.addEventListener('DOMContentLoaded', () => { const s = document.createElement('style'); s.textContent = css; document.head.appendChild(s); });
  }, [theme, CLEAN, collapsed]);
  const page = await ctx.newPage();
  await page.goto(`${APP}/login`, { waitUntil: 'networkidle' });
  await page.fill('input[type=email]', DEMO.email);
  await page.fill('input[type=password]', DEMO.password);
  await page.keyboard.press('Enter');
  await page.waitForURL('**/admin/**', { timeout: 30000 });
  await page.waitForTimeout(600);
  return { ctx, page };
}
