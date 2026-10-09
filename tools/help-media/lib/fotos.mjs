// Fotos ilustrativas da agência de demonstração, desenhadas no navegador (sem banco de
// imagens): praia, dunas, vinhedo, serra, cidade e rio. Saem em JPEG, 1600x1000.
import fs from 'fs';

const CENAS = {
  praia: `
    sky('#7cc8ef', '#e9f6fb', .55); sun(1180, 230, 80, 'rgba(255,255,255,.9)');
    sea('#2b9fc4', '#167a9c', 560, 760); sand('#f3dcae', '#e7c88c', 720);
    palm(260, 760, 1); palm(380, 790, .8);`,
  dunas: `
    sky('#f7b46b', '#fde6c4', .6); sun(1140, 300, 110, 'rgba(255,240,210,.95)');
    dune('#e89a4c', 620, 220, 1.0); dune('#d9823a', 720, 180, 1.7); dune('#c46d2c', 820, 140, 2.4);
    water('#3fb0c9', 840, 120);`,
  vinhedo: `
    sky('#9fd4ee', '#fdf2dc', .55); sun(320, 260, 90, 'rgba(255,248,220,.9)');
    hills('#8aa76a', 560, 120); hills('#6f8f50', 640, 90);
    rows('#4c6b35', '#7a9a52', 680);`,
  serra: `
    sky('#86c5f0', '#f4e8d0', .6); sun(1150, 240, 80, 'rgba(255,255,255,.88)');
    mountain('#5b7d9b', 600, 320); mountain('#2f6b4f', 760, 220); mountain('#1d4634', 860, 140);`,
  cidade: `
    sky('#f39a7a', '#ffe0c2', .7); sun(800, 640, 140, 'rgba(255,230,190,.95)');
    skyline('#3c3550', 700); skyline('#2a2438', 820, 1.3);`,
  rio: `
    sky('#9ed8e8', '#eaf7f4', .5);
    hills('#3f8f5a', 520, 140); hills('#2e7246', 600, 110);
    river('#4fc3c9', '#2d9fae'); trees('#1f5c38', 640);`,
};

const LIB = `
  const c = document.createElement('canvas'); c.width = 1600; c.height = 1000; const x = c.getContext('2d');
  const sky = (a, b, stop) => { const g = x.createLinearGradient(0, 0, 0, 1000); g.addColorStop(0, a); g.addColorStop(stop, b); g.addColorStop(1, b); x.fillStyle = g; x.fillRect(0, 0, 1600, 1000); };
  const sun = (cx, cy, r, col) => { const g = x.createRadialGradient(cx, cy, r * .2, cx, cy, r * 2.2); g.addColorStop(0, col); g.addColorStop(.45, col.replace(/[\\d.]+\\)$/, '.35)')); g.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = g; x.fillRect(0, 0, 1600, 1000); x.fillStyle = col; x.beginPath(); x.arc(cx, cy, r, 0, 7); x.fill(); };
  const wave = (base, amp, freq, phase) => i => base - Math.sin(i / freq + phase) * amp;
  const fillPath = (col, f, bottom = 1000) => { x.fillStyle = col; x.beginPath(); x.moveTo(0, bottom); for (let i = 0; i <= 1600; i += 20) x.lineTo(i, f(i)); x.lineTo(1600, bottom); x.fill(); };
  const sea = (a, b, top, bottom) => { const g = x.createLinearGradient(0, top, 0, bottom); g.addColorStop(0, a); g.addColorStop(1, b); fillPath(g, wave(top, 6, 60, 0)); x.strokeStyle = 'rgba(255,255,255,.35)'; x.lineWidth = 3; for (let k = 0; k < 6; k++) { x.beginPath(); for (let i = 0; i <= 1600; i += 20) x.lineTo(i, top + 30 + k * 28 + Math.sin(i / 50 + k) * 4); x.stroke(); } };
  const sand = (a, b, top) => { const g = x.createLinearGradient(0, top, 0, 1000); g.addColorStop(0, a); g.addColorStop(1, b); fillPath(g, wave(top, 18, 240, 1)); };
  const palm = (px, py, s) => { x.strokeStyle = '#5a3d22'; x.lineWidth = 18 * s; x.beginPath(); x.moveTo(px, py); x.quadraticCurveTo(px + 40 * s, py - 200 * s, px + 20 * s, py - 380 * s); x.stroke(); x.fillStyle = '#2f7d4a'; for (let k = 0; k < 7; k++) { const a = k / 7 * Math.PI * 2; x.beginPath(); x.ellipse(px + 20 * s + Math.cos(a) * 80 * s, py - 380 * s + Math.sin(a) * 30 * s, 110 * s, 22 * s, a, 0, 7); x.fill(); } };
  const dune = (col, base, amp, ph) => fillPath(col, i => base - Math.abs(Math.sin(i / 380 + ph)) * amp);
  const water = (col, top, h) => { x.fillStyle = col; x.beginPath(); x.ellipse(1100, top + h / 2, 420, h / 2, 0, 0, 7); x.fill(); };
  const hills = (col, base, amp) => fillPath(col, i => base - Math.sin(i / 300 + base) * amp);
  const rows = (dark, light, top) => { x.fillStyle = light; x.fillRect(0, top, 1600, 1000 - top); x.strokeStyle = dark; for (let k = 0; k < 16; k++) { x.lineWidth = 6 + k * 2.4; x.beginPath(); x.moveTo(800 + (k - 8) * 18, top); x.lineTo(800 + (k - 8) * 260, 1000); x.stroke(); } };
  const mountain = (col, base, amp) => fillPath(col, i => base - Math.abs(Math.sin(i / 230 + base)) * amp);
  const skyline = (col, base, s = 1) => { x.fillStyle = col; let i = 0; while (i < 1600) { const w = (40 + (i * 7) % 70) * s, h = (80 + (i * 13) % 260) * s; x.fillRect(i, base - h, w, 1000); i += w + 6; } };
  const river = (a, b) => { const g = x.createLinearGradient(0, 600, 0, 1000); g.addColorStop(0, a); g.addColorStop(1, b); x.fillStyle = g; x.beginPath(); x.moveTo(700, 600); x.bezierCurveTo(900, 720, 400, 820, 600, 1000); x.lineTo(1200, 1000); x.bezierCurveTo(900, 840, 1150, 720, 820, 600); x.fill(); };
  const trees = (col, base) => { x.fillStyle = col; for (let i = 0; i < 1600; i += 34) { const h = 60 + (i * 11) % 70; x.beginPath(); x.moveTo(i, base + 40); x.lineTo(i + 17, base - h); x.lineTo(i + 34, base + 40); x.fill(); } };
`;

/** Gera os arquivos <nome>.jpg em `pasta` com o navegador já aberto do Playwright. */
export async function gerarFotos(browser, pasta) {
  fs.mkdirSync(pasta, { recursive: true });
  const page = await browser.newPage();
  const arquivos = {};
  for (const [nome, cena] of Object.entries(CENAS)) {
    const data = await page.evaluate(`(() => { ${LIB} ${cena} return c.toDataURL('image/jpeg', .86); })()`);
    const arquivo = `${pasta}/${nome}.jpg`;
    fs.writeFileSync(arquivo, Buffer.from(data.split(',')[1], 'base64'));
    arquivos[nome] = arquivo;
  }
  await page.close();
  return arquivos;
}
