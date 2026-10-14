// Animação do Assistente IA para a página de vendas (/lp, seção "Descreva a viagem. A IA monta a
// página."): grava o editor de verdade na agência de demonstração, pedindo uma página ao assistente,
// aplicando a estrutura e passeando pela prévia. Sai em frontend/src/assets/lp/assistente.{mp4,webm}
// e assistente-poster.webp.
//
//   python3 ia-falsa.py &      (IA de mentira: a resposta sai igual toda vez e não gasta crédito)
//   API com GPT_KEY=falsa OPENAI_BASE_URL=http://127.0.0.1:8765/v1
//   node lp-assistente.mjs
//
// Precisa do mesmo ambiente do gerar.mjs (sistema rodando e seed.mjs feito). A página
// "Bonito em família" volta ao estado da demonstração antes e depois de gravar.
import fs from 'fs';
import { execFileSync } from 'child_process';
import { abrirNavegador, abrirPainel } from './lib/sessao.mjs';
import { abrirRoteiro, agir, localizar } from './lib/tour.mjs';
import { demo, pagina, restaurarPagina } from './lib/demo.mjs';
import { garantirCamada, legenda, marcarClique, moverCursor } from './lib/gravacao.mjs';

const TELA = { largura: 1280, altura: 800 };
const LARGURA_FINAL = 1120;
const SAIDA = new URL('../../frontend/src/assets/lp/', import.meta.url).pathname;
const TMP = new URL('./out/video-tmp/lp-assistente/', import.meta.url).pathname;
const PEDIDO = 'Gramado e Canela, 4 dias, saída 10/07. Hotel com café, city tour e Snowland. R$ 1.290 em até 10x.';

/** Rola a prévia da página até a fração `parte` da altura, devagar. */
const rolarPrevia = (page, parte) =>
  page.evaluate(parte => {
    const tela = document.querySelector('.ed-screen');
    if (tela) tela.scrollTo({ top: Math.round((tela.scrollHeight - tela.clientHeight) * parte), behavior: 'smooth' });
  }, parte);

/**
 * Só na gravação: o chat começa vazio (sem conversas de gravações anteriores) e, como o ambiente
 * local não tem chave de banco de fotos, os espaços de foto da estrutura recebem as fotos da
 * agência de demonstração.
 */
async function prepararGravacao(page) {
  await page.route('**/ai-assistant/pages/*/history', route => route.fulfill({ json: [] }));
  const { fotos } = demo();
  const ordem = ['serra', 'cidade', 'vinhedo', 'rio', 'dunas', 'praia'].map(nome => fotos[nome]).filter(Boolean);
  await page.route('**/ai-assistant/preview-page-base', async route => {
    const resposta = await route.fetch();
    const dados = await resposta.json();
    let i = 0;
    const trocar = valor => {
      if (Array.isArray(valor)) return valor.map(trocar);
      if (valor && typeof valor === 'object') {
        for (const [chave, item] of Object.entries(valor)) {
          if (typeof item === 'string' && /image|photo/i.test(chave) && item.startsWith('data:image/svg+xml')) valor[chave] = ordem[i++ % ordem.length];
          else valor[chave] = trocar(item);
        }
      }
      return valor;
    };
    await route.fulfill({ response: resposta, json: trocar(dados) });
  });
}

const roteiro = {
  rota: () => `/admin/pages/${pagina('bonito-em-familia')}/edit`,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  // n: número da legenda; passos seguidos com o mesmo n mantêm a legenda.
  passos: [
    { n: 1, legenda: 'Abra o Assistente IA', alvo: '.ed-btn-ai', esperar: 1100 },
    { n: 2, legenda: 'Conte a viagem do seu jeito', alvo: '.editor-ai-sidebar textarea', acao: 'digitar', texto: PEDIDO, atraso: 32, esperar: 500 },
    {
      n: 3,
      legenda: 'A IA monta a página inteira',
      alvo: '.editor-ai-sidebar-send',
      depois: page => page.locator('.editor-ai-sidebar button', { hasText: 'Substituir tudo' }).last().waitFor({ timeout: 30000 }),
      esperar: 1400,
    },
    { n: 4, legenda: 'Aplique com um clique', alvo: page => page.locator('.editor-ai-sidebar button', { hasText: 'Substituir tudo' }).last(), esperar: 2200, capa: true },
    {
      n: 5,
      legenda: 'Pronto: revise e publique',
      depois: async page => {
        for (const parte of [0.24, 0.48, 0.72, 0.95]) {
          await rolarPrevia(page, parte);
          await page.waitForTimeout(1250);
        }
        await rolarPrevia(page, 0);
        await page.waitForTimeout(900);
      },
    },
    { n: 5, legenda: 'Pronto: revise e publique', alvo: page => page.locator('.ed-actions button', { hasText: 'Publicar' }).first(), acao: 'nenhuma', esperar: 1800 },
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
    await prepararGravacao(page);
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
      if (!passo.alvo) {
        if (passo.depois) await passo.depois(page);
        continue;
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
      if (passo.acao === 'digitar') {
        await alvo.click();
        await alvo.fill('');
        await alvo.pressSequentially(passo.texto, { delay: passo.atraso ?? 55 });
        await page.waitForTimeout(passo.esperar ?? 1100);
      } else {
        await agir(page, passo, alvo, { devagar: true });
      }
      // Quadro de capa: a página nova já aplicada na prévia.
      if (passo.capa && !poster) poster = (Date.now() - t0) / 1000 - inicio;
    }
    await page.waitForTimeout(800);
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
ffmpeg([...corte, '-vf', escala, '-c:v', 'libx264', '-preset', 'slow', '-crf', '27', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', `${SAIDA}assistente.mp4`]);
ffmpeg([...corte, '-vf', escala, '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '46', '-row-mt', '1', '-an', `${SAIDA}assistente.webm`]);
ffmpeg(['-ss', String(Math.max(0, inicio + poster + 0.4)), '-i', webm, '-frames:v', '1', '-vf', `scale=${LARGURA_FINAL}:-2`, '-c:v', 'libwebp', '-quality', '80', `${SAIDA}assistente-poster.webp`]);
fs.rmSync(TMP, { recursive: true, force: true });
for (const f of ['assistente.mp4', 'assistente.webm', 'assistente-poster.webp']) console.log(f, Math.round(fs.statSync(`${SAIDA}${f}`).size / 1024), 'KB');
