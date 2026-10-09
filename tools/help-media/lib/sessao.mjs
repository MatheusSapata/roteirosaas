// Abre o painel já logado na conta de demonstração, no tema pedido, com as fontes
// locais e sem o botão de suporte (que cobriria os cantos das telas).
import fs from 'fs';
import { chromium } from 'playwright';
import { APP, DEMO, chromiumPath } from './api.mjs';

export const TELA = { largura: 1440, altura: 900 };

// Fontes do painel servidas do node_modules (pacotes @fontsource), sem depender da rede.
const FONTES = new URL('../node_modules/', import.meta.url);
let FONTCSS = '';
for (const [fam, pacote, k, ws] of [
  ['Inter', '@fontsource/inter', 'inter', [400, 500, 600, 700]],
  ['Sora', '@fontsource/sora', 'sora', [500, 600, 700, 800]],
  ['Figtree', '@fontsource/figtree', 'figtree', [400, 500, 600, 700]],
])
  for (const w of ws)
    for (const sub of ['latin', 'latin-ext'])
      FONTCSS += `@font-face{font-family:'${fam}';font-weight:${w};font-display:block;src:url(https://fonts.local/${pacote}/files/${k}-${sub}-${w}-normal.woff2) format('woff2');}\n`;
for (const sub of ['latin', 'latin-ext'])
  FONTCSS += `@font-face{font-family:'Bricolage Grotesque';font-weight:200 800;font-display:block;src:url(https://fonts.local/@fontsource-variable/bricolage-grotesque/files/bricolage-grotesque-${sub}-opsz-normal.woff2) format('woff2');}\n`;

/** CSS aplicado em todas as capturas. */
const LIMPEZA = `
  a[href^="https://wa.me/5553991800903"] { display: none !important; }
  html { scrollbar-width: none; }
  html::-webkit-scrollbar { display: none; }
`;

export const abrirNavegador = () => chromium.launch({ executablePath: chromiumPath(), args: ['--lang=pt-BR'] });

/**
 * @param {import('playwright').Browser} browser
 * @param {{ tema?: 'light' | 'dark', video?: string }} opts  video: pasta para gravar
 */
export async function abrirPainel(browser, { tema = 'light', video } = {}) {
  const ctx = await browser.newContext({
    viewport: { width: TELA.largura, height: TELA.altura },
    deviceScaleFactor: 1,
    locale: 'pt-BR',
    timezoneId: 'America/Sao_Paulo',
    ...(video ? { recordVideo: { dir: video, size: { width: TELA.largura, height: TELA.altura } } } : {}),
  });
  if (fs.existsSync(new URL('@fontsource/inter/', FONTES))) {
    await ctx.route(/fonts\.googleapis\.com/, r => r.fulfill({ status: 200, contentType: 'text/css', headers: { 'access-control-allow-origin': '*' }, body: FONTCSS }));
    await ctx.route(/fonts\.local\//, r => {
      const arquivo = new URL(new URL(r.request().url()).pathname.slice(1), FONTES);
      return fs.existsSync(arquivo)
        ? r.fulfill({ status: 200, contentType: 'font/woff2', headers: { 'access-control-allow-origin': '*' }, body: fs.readFileSync(arquivo) })
        : r.fulfill({ status: 404, body: '' });
    });
  }
  // Serviços de fora (chat, analytics) não carregam nas capturas.
  await ctx.route(/^https?:\/\/[^/]*(viajechat|googletagmanager|google-analytics|facebook\.net|doubleclick)/, r => r.fulfill({ status: 204, body: '' }));
  await ctx.addInitScript(([t, css]) => {
    localStorage.setItem('global_cookie_consent', 'accepted');
    localStorage.setItem('admin-theme', t);
    localStorage.setItem('admin_sidebar_collapsed', '0');
    document.addEventListener('DOMContentLoaded', () => {
      const s = document.createElement('style');
      s.textContent = css;
      document.head.appendChild(s);
    });
  }, [tema, LIMPEZA]);
  const page = await ctx.newPage();
  await page.goto(`${APP}/login`, { waitUntil: 'networkidle' });
  await page.fill('input[type=email]', DEMO.email);
  await page.fill('input[type=password]', DEMO.password);
  await page.keyboard.press('Enter');
  await page.waitForURL('**/admin/**', { timeout: 30000 });
  await page.waitForTimeout(800);
  return { ctx, page };
}
