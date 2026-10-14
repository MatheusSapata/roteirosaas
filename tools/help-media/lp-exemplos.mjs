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
  // Atrás de um proxy (ambiente de nuvem), o Chromium abre conexões demais em paralelo e o
  // proxy recusa parte delas (ERR_TOO_MANY_RETRIES): os pedidos da página passam pelo Node.
  if (proxy)
    await ctx.route(/^https:\/\/(?!fonts\.)/, async r => {
      try {
        await r.fulfill({ response: await r.fetch({ maxRetries: 2, timeout: 20000 }) });
      } catch {
        await r.abort().catch(() => {});
      }
    });
  await ctx.addInitScript(() => localStorage.setItem('global_cookie_consent', 'accepted'));
  const page = await ctx.newPage();
  try {
    // Página fora do ar (assinatura vencida, limite do plano) não vira miniatura: fica a antiga.
    const [agencia, slug] = new URL(url).pathname.split('/').filter(Boolean);
    const api = await page.request.get(`${new URL(url).origin}/api/v1/public/pages/by-slug/${agencia}/${slug}`);
    if (!api.ok()) throw new Error(`página indisponível (${api.status()} ${(await api.text()).slice(0, 80)})`);
    // "load" e não "networkidle": a página publicada mantém conexões abertas (rastreamento).
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForLoadState('load', { timeout: 30000 }).catch(() => {});
    // Espera as fotos e a animação de entrada do banner.
    await page.evaluate(() => Promise.race([
      Promise.all([...document.images].map(img => img.complete || new Promise(r => { img.onload = img.onerror = r; }))),
      new Promise(r => setTimeout(r, 20000)),
    ]));
    await page.waitForTimeout(3500);
    // Só o banner do topo (sem a faixa da seção seguinte), no máximo a altura da janela.
    const banner = await page.locator('section, [class*="hero"]').first().boundingBox();
    const altura = Math.round(Math.min(TELA.height, banner && banner.height > 300 ? banner.height : TELA.height));
    const png = `${SAIDA}exemplo-${id}.png`;
    await page.screenshot({ path: png, clip: { x: 0, y: 0, width: TELA.width, height: altura } });
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
