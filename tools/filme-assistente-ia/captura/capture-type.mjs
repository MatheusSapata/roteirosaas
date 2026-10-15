// Re-capture the typing states: blank page, AI open, textarea resized to 3 lines (its own resize handle), no spellcheck.
import fs from 'fs';
import { launch, panel, APP } from './lib.mjs';
const HM = '/home/user/roteirosaas/tools/help-media';
const { DEMO, login, req } = await import(`${HM}/lib/api.mjs`);
const st = JSON.parse(fs.readFileSync('film-state.json'));
const PROMPT = 'Gramado e Canela, 4 dias, saída 10/07. Hotel com café, city tour e Snowland. R$ 1.290 em até 10x.';
const token = await login(DEMO.email, DEMO.password);
const full = await req(token, 'GET', `/pages/${st.pageId}`);
fs.writeFileSync('page-final.json', JSON.stringify(full, null, 1));
const cfg = full.config_json || full.config;
await req(token, 'PUT', `/pages/${st.pageId}`, { title: full.title, slug: full.slug, config_json: { sections: [] } });
fs.rmSync('main/type2', { recursive: true, force: true }); fs.mkdirSync('main/type2', { recursive: true });
const b = await launch();
const { page } = await panel(b, { dpr: 3 });
await page.route('**/ai-assistant/pages/*/history', r => r.fulfill({ json: [] }));
await page.goto(`${APP}/admin/pages/${st.pageId}/edit`, { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);
await page.locator('.ed-btn-ai').click();
await page.waitForTimeout(1500);
const ta = page.locator('.editor-ai-sidebar textarea');
await ta.evaluate(el => { el.spellcheck = false; el.setAttribute('spellcheck', 'false'); el.style.height = '82px'; });
await page.waitForTimeout(400);
await page.screenshot({ path: 'main/a01b-blank-ai-tall.png' });
const geo = { textarea: await ta.boundingBox(), send: await page.locator('.editor-ai-sidebar-send').boundingBox(), caret: [] };
const clip = { x: 1004, y: 600, width: 428, height: 300 }; geo.clip = clip;
await ta.click();
const chars = [...PROMPT];
for (let k = 0; k <= chars.length; k++) {
  await ta.fill(chars.slice(0, k).join(''));
  await page.waitForTimeout(k === 0 ? 300 : 50);
  geo.caret.push(await ta.evaluate(el => {
    const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
    const m = document.createElement('div');
    for (const p of ['fontFamily', 'fontSize', 'fontWeight', 'lineHeight', 'letterSpacing', 'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft', 'borderTopWidth', 'borderLeftWidth', 'borderRightWidth', 'borderBottomWidth', 'boxSizing']) m.style[p] = cs[p];
    m.style.position = 'fixed'; m.style.left = r.left + 'px'; m.style.top = r.top + 'px'; m.style.width = r.width + 'px';
    m.style.whiteSpace = 'pre-wrap'; m.style.overflowWrap = 'break-word'; m.style.visibility = 'hidden'; m.style.borderStyle = 'solid'; m.style.borderColor = 'transparent';
    m.textContent = el.value; const s = document.createElement('span'); s.textContent = '​'; m.appendChild(s); document.body.appendChild(m);
    const sr = s.getBoundingClientRect(); m.remove();
    return { x: sr.left, y: sr.top - el.scrollTop, h: parseFloat(cs.lineHeight), scrollTop: el.scrollTop };
  }));
  await page.screenshot({ path: `main/type2/t${String(k).padStart(3, '0')}.png`, clip });
}
geo.sendActive = await page.locator('.editor-ai-sidebar-send').boundingBox();
await page.screenshot({ path: 'main/a02b-typed-tall.png' });
fs.writeFileSync('main/geo-type.json', JSON.stringify(geo, null, 1));
await b.close();
await req(token, 'PUT', `/pages/${st.pageId}`, { title: full.title, slug: full.slug, config_json: cfg });
console.log('typing states', chars.length + 1, 'restored sections', (cfg.sections || []).length);
