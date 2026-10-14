// Miniaturas dos "Exemplos reais" da página de vendas (/lp): abre cada página publicada e
// guarda o topo dela em frontend/src/assets/lp/exemplo-<id>.webp (760 px de largura, o
// tamanho que o cartão usa). Rode de novo sempre que as páginas mudarem de visual.
//
//   node lp-exemplos.mjs
//
// Precisa de acesso a roteiroonline.com (no ambiente de nuvem, liberado em Network access).
import { execFileSync } from 'child_process';
import fs from 'fs';
import { chromium } from 'playwright';
import { chromiumPath } from './lib/api.mjs';
import { prepararContexto } from './lib/sessao.mjs';

// Os mesmos links dos cartões em SalesLandingView.vue (EXAMPLES).
const EXEMPLOS = [
  { id: 'abrolhos', url: 'https://roteiroonline.com/ecoar-ecoturismo/abrolhos' },
  { id: 'foz', url: 'https://roteiroonline.com/status/foz-do-iguacu' },
  { id: 'italia', url: 'https://roteiroonline.com/beth-tur/itaia-magnifica' },
];
const SAIDA = new URL('../../frontend/src/assets/lp/', import.meta.url).pathname;
const TELA = { width: 1440, height: 810 };

const proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
const browser = await chromium.launch({ executablePath: chromiumPath(), ...(proxy ? { proxy: { server: proxy } } : {}) });
let falhas = 0;
for (const { id, url } of EXEMPLOS) {
  const ctx = await browser.newContext({ viewport: TELA, deviceScaleFactor: 1, locale: 'pt-BR', ignoreHTTPSErrors: !!proxy });
  await prepararContexto(ctx);
  await ctx.addInitScript(() => localStorage.setItem('global_cookie_consent', 'accepted'));
  const page = await ctx.newPage();
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 });
    // Espera as fotos e a animação de entrada do banner.
    await page.evaluate(() => Promise.all([...document.images].map(img => img.complete || new Promise(r => { img.onload = img.onerror = r; }))));
    await page.waitForTimeout(2500);
    const png = `${SAIDA}exemplo-${id}.png`;
    await page.screenshot({ path: png });
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', png, '-vf', 'scale=760:-2', '-c:v', 'libwebp', '-quality', '80', `${SAIDA}exemplo-${id}.webp`]);
    fs.unlinkSync(png);
    console.log(`✓ ${id}`, Math.round(fs.statSync(`${SAIDA}exemplo-${id}.webp`).size / 1024), 'KB');
  } catch (e) {
    falhas++;
    console.log(`✗ ${id}: ${e.message.split('\n')[0]}`);
  } finally {
    await ctx.close();
  }
}
await browser.close();
process.exit(falhas ? 1 : 0);
