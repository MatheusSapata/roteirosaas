// Main capture of the real editor (local stack) for the film. DPR 3, 1440x900, light theme.
import fs from 'fs';
import { launch, panel, APP } from './lib.mjs';
const HM = '/home/user/roteirosaas/tools/help-media';
const { DEMO, login, req } = await import(`${HM}/lib/api.mjs`);
const st = JSON.parse(fs.readFileSync('film-state.json'));
const PROMPT = 'Gramado e Canela, 4 dias, saída 10/07. Hotel com café, city tour e Snowland. R$ 1.290 em até 10x.';
const OUT = 'main'; fs.rmSync(OUT, { recursive: true, force: true }); fs.mkdirSync(`${OUT}/type`, { recursive: true }); fs.mkdirSync(`${OUT}/stream`, { recursive: true });
const geo = {};
const token = await login(DEMO.email, DEMO.password);
await req(token, 'PUT', `/pages/${st.pageId}`, { title: 'Gramado e Canela', slug: 'gramado-e-canela', config_json: { sections: [] } });
const b = await launch();
const { page } = await panel(b, { dpr: 3 });
const box = async (loc, name) => { const r = await loc.boundingBox(); geo[name] = r; return r; };
const shot = (name, opts = {}) => page.screenshot({ path: `${OUT}/${name}.png`, ...opts });
await page.addStyleTag({ content: '' }).catch(() => {});
await page.route('**/ai-assistant/pages/*/history', r => r.fulfill({ json: [] }));
await page.route('**/ai-assistant/preview-page-base', async route => {
  const res = await route.fetch(); const d = await res.json();
  const s0 = d.sections[0]; s0.backgroundImage = st.fotos.catedral; s0.mobileBackgroundImage = st.fotos.catedral;
  const days = d.sections.find(s => s.type === 'itinerary')?.days || [];
  ['ruacoberta', 'cascata', 'snowland', 'chocolate'].forEach((n, i) => { if (days[i]) days[i].image = st.fotos[n]; });
  await route.fulfill({ response: res, json: d });
});
await page.goto(`${APP}/admin/pages/${st.pageId}/edit`, { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);
await page.addStyleTag({ content: '.editor-ai-sidebar textarea{max-height:none!important;overflow:hidden!important}' });
await shot('a00-blank');
await page.locator('.ed-btn-ai').click();
await page.waitForTimeout(1500);
await shot('a01-blank-ai');
const ta = page.locator('.editor-ai-sidebar textarea');
await box(ta, 'textarea'); await box(page.locator('.editor-ai-sidebar-send'), 'send0');
await box(page.locator('.editor-ai-sidebar'), 'sidebar'); await box(page.locator('.ed-btn-ai'), 'btnAI');
// typing states: every grapheme count; crop the sidebar column
const SB = geo.sidebar; const clipSB = { x: Math.floor(SB.x) - 4, y: 0, width: Math.ceil(SB.width) + 8, height: 900 }; geo.clipSB = clipSB;
await ta.click();
const chars = [...PROMPT]; geo.caret = []; geo.taH = [];
for (let k = 0; k <= chars.length; k++) {
  await ta.fill(chars.slice(0, k).join(''));
  await page.waitForTimeout(k === 0 ? 300 : 60);
  const c = await ta.evaluate(el => {
    const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
    const m = document.createElement('div');
    for (const p of ['fontFamily', 'fontSize', 'fontWeight', 'lineHeight', 'letterSpacing', 'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft', 'borderTopWidth', 'borderLeftWidth', 'borderRightWidth', 'boxSizing', 'wordBreak', 'overflowWrap', 'whiteSpace', 'tabSize']) m.style[p] = cs[p];
    m.style.position = 'fixed'; m.style.left = r.left + 'px'; m.style.top = r.top + 'px'; m.style.width = r.width + 'px'; m.style.whiteSpace = 'pre-wrap'; m.style.wordWrap = 'break-word'; m.style.visibility = 'hidden'; m.style.borderStyle = 'solid'; m.style.borderColor = 'transparent';
    m.textContent = el.value; const s = document.createElement('span'); s.textContent = '​'; m.appendChild(s); document.body.appendChild(m);
    const sr = s.getBoundingClientRect(); m.remove();
    return { x: sr.left, y: sr.top, h: parseFloat(cs.lineHeight), taTop: r.top, taH: r.height, scrollTop: el.scrollTop };
  });
  geo.caret.push(c);
  await shot(`type/t${String(k).padStart(3, '0')}`, { clip: clipSB });
}
await box(page.locator('.editor-ai-sidebar-send'), 'send1');
await shot('a02-typed');
// send + stream
await page.locator('.editor-ai-sidebar-send').click();
const t0 = Date.now(); let i = 0; geo.stream = [];
while (Date.now() - t0 < 60000) {
  await shot(`stream/s${String(i).padStart(3, '0')}`, { clip: clipSB }); geo.stream.push(Date.now() - t0); i++;
  if (await page.locator('.editor-ai-sidebar button', { hasText: 'Inserir no fim' }).count()) break;
  await page.waitForTimeout(40);
}
await page.waitForTimeout(900);
await shot(`stream/s${String(i).padStart(3, '0')}`, { clip: clipSB }); geo.stream.push(Date.now() - t0);
const ins = page.locator('.editor-ai-sidebar button', { hasText: 'Inserir no fim' }).last();
await box(ins, 'btnInserir');
await shot('a03-structure');
await ins.hover(); await page.waitForTimeout(400); await shot('a04-structure-hover');
await ins.click();
await page.waitForTimeout(150); await shot('a05-applied-t0');
await page.evaluate(() => Promise.race([Promise.all([...document.images].filter(i => i.loading !== 'lazy').map(i => i.complete || new Promise(r => { i.onload = i.onerror = r; }))), new Promise(r => setTimeout(r, 6000))]));
await page.waitForTimeout(1500); await shot('a06-applied');
await box(page.locator('.ed-screen').first(), 'screen');
await page.locator('.ed-actions button', { hasText: 'Salvar' }).first().click();
await page.waitForTimeout(2500); await shot('a07-saved');
// scroll states of the preview (for the scroll beat)
geo.scroll = [];
const scr = page.locator('.ed-screen').first();
const H = await scr.evaluate(el => el.scrollHeight - el.clientHeight); geo.scrollMax = H;
for (let k = 0, y = 0; y <= H + 1; k++, y += 220) {
  await scr.evaluate((el, y) => { el.scrollTop = y; }, Math.min(y, H)); await page.waitForTimeout(350);
  await shot(`scroll-${String(k).padStart(2, '0')}`, { clip: { x: geo.screen.x, y: geo.screen.y, width: geo.screen.width, height: geo.screen.height } });
  geo.scroll.push(Math.min(y, H));
}
await scr.evaluate(el => { el.scrollTop = 0; });
// close AI sidebar
await page.locator('.editor-ai-sidebar button[aria-label="Fechar"], .editor-ai-sidebar-close').first().click().catch(() => {});
await page.waitForTimeout(800); await shot('a08-layers');
// price edit
await page.locator('.ed-section-main:has-text("Preços")').first().click();
await page.waitForTimeout(1500); await shot('b00-price-panel');
await page.locator('.ved-group-head:has-text("Ofertas")').first().click();
await page.waitForTimeout(1200); await shot('b01-ofertas');
const price = page.locator('.ed-section-panel input[type=number]').first();
await box(price, 'priceInput');
await price.click(); await page.waitForTimeout(300); await price.selectText(); await page.waitForTimeout(400); await shot('b02-price-selected');
let v = '';
for (const ch of '1190') { v += ch; await price.fill(v); await page.waitForTimeout(700); await shot(`b03-price-${v}`); }
await box(page.locator('.ed-screen').first(), 'screenPanel');
await page.locator('.ed-section-panel button', { hasText: 'Salvar seção' }).first().click(); await page.waitForTimeout(1200);
await shot('b04-price-saved');
// banner layout
await page.locator('.ed-section-main:has-text("Banner")').first().click(); await page.waitForTimeout(1500);
await page.locator('.ved-tab:has-text("Aparência")').click(); await page.waitForTimeout(1200);
await shot('c00-banner-aparencia');
for (const name of ['Cartão', 'Dividido', 'Clássico']) {
  const btn = page.locator('.ed-section-panel button', { hasText: name }).first();
  await box(btn, `layout-${name}`);
  await btn.hover(); await page.waitForTimeout(300); await shot(`c01-hover-${name}`);
  await btn.click(); await page.waitForTimeout(1500); await shot(`c02-layout-${name}`);
}
const imm = page.locator('.ed-section-panel button', { hasText: 'Imersivo' }).first(); await box(imm, 'layout-Imersivo');
await page.locator('.ed-section-panel button', { hasText: 'Cartão' }).first().click(); await page.waitForTimeout(1500);
await page.locator('.ed-section-panel button', { hasText: 'Salvar seção' }).first().click(); await page.waitForTimeout(1200);
await shot('c03-cartao-saved');
// phone toggle
const cel = page.locator('button', { hasText: 'Celular' }).first(); await box(cel, 'btnCelular');
await cel.hover(); await page.waitForTimeout(300); await shot('d00-celular-hover');
await cel.click(); await page.waitForTimeout(2000); await shot('d01-celular');
await box(page.locator('.ed-screen').first(), 'screenPhone');
await page.locator('.ed-actions button', { hasText: 'Salvar' }).first().click().catch(() => {}); await page.waitForTimeout(1500);
fs.writeFileSync(`${OUT}/geo.json`, JSON.stringify(geo, null, 1));
await b.close();
console.log('done; stream states', geo.stream.length, 'scroll states', geo.scroll.length);
