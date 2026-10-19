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
import { garantirCamada, legenda, marcarClique, moverCursor } from './lib/gravacao.mjs';

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
