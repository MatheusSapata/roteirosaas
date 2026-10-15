// selftest.mjs film.html : open with ?selftest in Chromium, print window.__seekcheck and console warnings
const { chromium } = await import('/home/user/roteirosaas/tools/help-media/node_modules/playwright/index.mjs');
const file = process.argv[2];
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--allow-file-access-from-files', '--no-sandbox'] });
const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
const logs = [];
p.on('console', m => { if (m.type() === 'warning' || m.type() === 'error') logs.push(m.type() + ': ' + m.text()); });
await p.goto('file://' + file + '?selftest');
const r = await p.waitForFunction(() => window.__seekcheck, null, { timeout: 600000 }).then(h => h.jsonValue());
console.log(JSON.stringify({ ok: r.ok, samples: r.samples, elements: r.elements, n: (r.mismatches || []).length, mismatches: (r.mismatches || []).slice(0, 3) }, null, 1));
console.log([...new Set(logs)].filter(l => !/image failed/.test(l)).slice(0, 20).join('\n'));
await b.close();
