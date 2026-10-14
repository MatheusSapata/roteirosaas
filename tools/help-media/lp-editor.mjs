// Animação do editor para a página de vendas (/lp, seção "Mais fácil que editar no Canva"):
// grava o editor de verdade na agência de demonstração, com cursor, marca do clique e
// legendas grandes (a LP mostra o vídeo com uns 600 px de largura). Sai em
// frontend/src/assets/lp/editor.{mp4,webm} e editor-poster.webp.
//
//   node lp-editor.mjs
//
// Precisa do mesmo ambiente do gerar.mjs (sistema rodando e seed.mjs feito). A página
// "Bonito em família" volta ao estado da demonstração antes e depois de gravar.
import fs from 'fs';
import { execFileSync } from 'child_process';
import { abrirNavegador, abrirPainel } from './lib/sessao.mjs';
import { abrirRoteiro, agir, localizar } from './lib/tour.mjs';
import { pagina, restaurarPagina } from './lib/demo.mjs';

const TELA = { largura: 1280, altura: 800 };
const LARGURA_FINAL = 1120;
const SAIDA = new URL('../../frontend/src/assets/lp/', import.meta.url).pathname;
const TMP = new URL('./out/video-tmp/lp-editor/', import.meta.url).pathname;

const roteiro = {
  rota: () => `/admin/pages/${pagina('bonito-em-familia')}/edit`,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  // n: número da legenda; passos seguidos com o mesmo n mantêm a legenda.
  passos: [
    { n: 1, legenda: 'Escolha uma seção pronta', alvo: '.ed-layers-add', esperar: 1050 },
    { n: 1, legenda: 'Escolha uma seção pronta', alvo: '.spk-chip:has-text("Detalhamento")', esperar: 550 },
    { n: 1, legenda: 'Escolha uma seção pronta', alvo: '.spk-card:has-text("Roteiro dia a dia")', esperar: 1750 },
    { n: 2, legenda: 'Clique numa seção para editar', alvo: '.ed-section-main:has-text("Banner Inicial")', esperar: 950 },
    { n: 2, legenda: 'Clique numa seção para editar', alvo: '.ved-group-head:has-text("Texto")', esperar: 550 },
    { n: 3, legenda: 'Digite: a prévia muda na hora', alvo: page => page.locator('.ed-section-panel input').first(), acao: 'digitar', texto: 'Bonito com as crianças', esperar: 1200 },
    { n: 4, legenda: 'Troque o visual com um clique', alvo: '.ved-tab:has-text("Aparência")', esperar: 550 },
    { n: 4, legenda: 'Troque o visual com um clique', alvo: page => page.locator('.ed-section-panel button', { hasText: 'Imersivo' }).first(), esperar: 1500 },
    { n: 4, legenda: 'Troque o visual com um clique', alvo: page => page.locator('.ed-section-panel button', { hasText: 'Salvar seção' }).first(), esperar: 1050 },
    { n: 5, legenda: 'Veja como fica no celular', alvo: page => page.locator('button', { hasText: 'Celular' }).first(), esperar: 2100 },
    { n: 6, legenda: 'Ou peça ao Assistente IA', alvo: '.ed-btn-ai', esperar: 1050 },
    { n: 6, legenda: 'Ou peça ao Assistente IA', alvo: '.editor-ai-sidebar textarea', acao: 'digitar', texto: 'Crie perguntas frequentes sobre Bonito com crianças', esperar: 1100 },
    { n: 7, legenda: 'Publique e mande o link', alvo: page => page.locator('.ed-actions button', { hasText: 'Publicar' }).first(), esperar: 2250 },
  ],
};

// Camada da gravação: a mesma do vídeo da Central de Ajuda, com cursor e legenda maiores.
const CAMADA = `
<style>
  #hm-layer{position:fixed;inset:0;pointer-events:none;z-index:2147483647;font-family:Inter,system-ui,sans-serif}
  #hm-cursor{position:absolute;left:640px;top:420px;width:42px;height:42px;transition:left .65s cubic-bezier(.4,0,.2,1),top .65s cubic-bezier(.4,0,.2,1);filter:drop-shadow(0 3px 6px rgba(0,0,0,.35))}
  #hm-click{position:absolute;width:96px;height:96px;margin:-48px 0 0 -48px;border-radius:50%;border:5px solid #0b7a5b;background:rgba(18,185,129,.2);opacity:0;transform:scale(.4)}
  #hm-click.on{animation:hm-rip .9s ease-out forwards}
  @keyframes hm-rip{0%{opacity:1;transform:scale(.4)}45%{opacity:1;transform:scale(1)}100%{opacity:0;transform:scale(1.15)}}
  #hm-cap{position:absolute;left:50%;bottom:30px;max-width:88%;transform:translate(-50%,18px);opacity:0;transition:all .4s ease;background:rgba(12,16,14,.92);color:#fff;padding:14px 30px 14px 14px;border-radius:999px;font-size:34px;font-weight:700;letter-spacing:-.015em;display:flex;gap:16px;align-items:center;white-space:nowrap;box-shadow:0 14px 36px -10px rgba(0,0,0,.5)}
  #hm-cap.on{opacity:1;transform:translate(-50%,0)}
  #hm-cap b{flex:none;background:#1de9a0;color:#071613;border-radius:999px;width:50px;height:50px;display:grid;place-items:center;font-size:26px}
</style>
<svg id="hm-cursor" viewBox="0 0 24 24"><path d="M4 2l16 10.5-7.2 1.4L9.6 21z" fill="#0f1713" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>
<div id="hm-click"></div>
<div id="hm-cap"><b></b><span></span></div>`;

const garantirCamada = page =>
  page.evaluate(html => {
    if (document.getElementById('hm-layer')) return;
    const el = document.createElement('div');
    el.id = 'hm-layer';
    el.innerHTML = html;
    document.body.appendChild(el);
  }, CAMADA);

const legenda = (page, n, texto) =>
  page.evaluate(([n, texto]) => {
    const cap = document.getElementById('hm-cap');
    cap.classList.remove('on');
    setTimeout(() => {
      cap.querySelector('b').textContent = n;
      cap.querySelector('span').textContent = texto;
      cap.classList.add('on');
    }, 160);
  }, [String(n), texto]);

const moverCursor = (page, x, y) =>
  page.evaluate(([x, y]) => Object.assign(document.getElementById('hm-cursor').style, { left: `${x}px`, top: `${y}px` }), [x, y]);

const marcarClique = (page, x, y) =>
  page.evaluate(([x, y]) => {
    const m = document.getElementById('hm-click');
    Object.assign(m.style, { left: `${x}px`, top: `${y}px` });
    m.classList.remove('on');
    void m.offsetWidth;
    m.classList.add('on');
  }, [x, y]);

async function gravar(browser) {
  fs.rmSync(TMP, { recursive: true, force: true });
  fs.mkdirSync(TMP, { recursive: true });
  const t0 = Date.now();
  const { ctx, page } = await abrirPainel(browser, { tema: 'light', video: TMP, tela: TELA });
  let inicio = 0;
  let poster = 0;
  try {
    await abrirRoteiro(page, roteiro);
    await garantirCamada(page);
    inicio = (Date.now() - t0) / 1000;
    await page.waitForTimeout(600);
    let atual = 0;
    for (const passo of roteiro.passos) {
      await garantirCamada(page);
      if (passo.n !== atual) {
        await legenda(page, passo.n, passo.legenda);
        atual = passo.n;
        await page.waitForTimeout(350);
      }
      const alvo = localizar(page, passo.alvo);
      await alvo.waitFor({ state: 'visible', timeout: 15000 });
      await alvo.scrollIntoViewIfNeeded().catch(() => {});
      const box = await alvo.boundingBox();
      if (box) {
        const x = box.x + Math.min(box.width / 2, 60);
        const y = box.y + box.height / 2;
        await moverCursor(page, x, y);
        await page.waitForTimeout(700);
        await marcarClique(page, x, y);
        await page.waitForTimeout(280);
      }
      await agir(page, passo, alvo, { devagar: true });
      // Quadro de capa: a prévia já com o banner editado e o layout novo.
      if (passo.n === 4 && !poster) poster = (Date.now() - t0) / 1000 - inicio;
    }
    await page.waitForTimeout(1000);
  } finally {
    await page.close();
    await ctx.close();
  }
  const webm = fs.readdirSync(TMP).filter(f => f.endsWith('.webm')).map(f => `${TMP}${f}`)[0];
  return { webm, inicio, poster };
}

const ffmpeg = args => execFileSync('ffmpeg', ['-loglevel', 'error', '-y', ...args]);

const browser = await abrirNavegador();
await restaurarPagina('bonito-em-familia');
let resultado;
try {
  resultado = await gravar(browser);
} finally {
  await browser.close();
  await restaurarPagina('bonito-em-familia');
}
const { webm, inicio, poster } = resultado;
const corte = ['-ss', String(Math.max(0, inicio - 0.1)), '-i', webm];
const escala = `scale=${LARGURA_FINAL}:-2,fps=30`;
ffmpeg([...corte, '-vf', escala, '-c:v', 'libx264', '-preset', 'slow', '-crf', '27', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', `${SAIDA}editor.mp4`]);
ffmpeg([...corte, '-vf', escala, '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '46', '-row-mt', '1', '-an', `${SAIDA}editor.webm`]);
ffmpeg(['-ss', String(Math.max(0, inicio + poster + 0.6)), '-i', webm, '-frames:v', '1', '-vf', `scale=${LARGURA_FINAL}:-2`, '-c:v', 'libwebp', '-quality', '80', `${SAIDA}editor-poster.webp`]);
fs.rmSync(TMP, { recursive: true, force: true });
for (const f of ['editor.mp4', 'editor.webm', 'editor-poster.webp']) console.log(f, Math.round(fs.statSync(`${SAIDA}${f}`).size / 1024), 'KB');
