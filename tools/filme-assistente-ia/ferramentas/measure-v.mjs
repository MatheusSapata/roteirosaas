const { chromium } = await import('/home/user/roteirosaas/tools/help-media/node_modules/playwright/index.mjs');
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--allow-file-access-from-files', '--no-sandbox'] });
const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
const errs = []; p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.text()); }); p.on('pageerror', e => errs.push('PAGEERR ' + e.message));
await p.goto('file://' + process.argv[2]);
await p.evaluate(() => document.fonts.ready);
await p.waitForTimeout(500);
const r = await p.evaluate(() => ({ m: window.__measure(), ev0: window.__typeEv[0], evEnd: window.__typeEv[window.__typeEv.length - 1], n: window.__typeEv.length,
  hB1: document.querySelector('#hB1').scrollWidth, w: [...document.querySelectorAll('.hl, #claim .ln')].map(e => { const r = document.createRange(); r.selectNodeContents(e); const bb = r.getBoundingClientRect(); return e.id + ':' + Math.round(bb.width); }),
  cta: (() => { const bb = document.querySelector('#cta').getBoundingClientRect(); return [bb.x, bb.width]; })() }));
console.log(JSON.stringify(r)); console.log(errs.slice(0, 10).join('\n'));
await b.close();
