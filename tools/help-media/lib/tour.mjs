// Demonstração interativa: percorre o roteiro tirando uma tela por passo e anotando
// onde fica o ponto de clique (em % da tela). A Central de Ajuda mostra as telas em
// sequência e a pessoa clica no ponto destacado para avançar.
import fs from 'fs';
import { execFileSync } from 'child_process';
import { APP } from './api.mjs';
import { TELA, abrirPainel } from './sessao.mjs';

/** Localiza o alvo do passo: texto de seletor do Playwright ou função (page) => Locator. */
export const localizar = (page, alvo) => (typeof alvo === 'function' ? alvo(page) : page.locator(alvo).first());

/** Abre a rota do roteiro e espera a tela ficar pronta. */
export async function abrirRoteiro(page, roteiro) {
  const rota = typeof roteiro.rota === 'function' ? roteiro.rota() : roteiro.rota;
  await page.goto(APP + rota, { waitUntil: 'networkidle' }).catch(() => {});
  if (roteiro.pronto) await roteiro.pronto(page);
  await page.waitForTimeout(roteiro.espera ?? 1200);
}

/** Executa a ação do passo depois da captura. */
export async function agir(page, passo, alvo, { devagar = false } = {}) {
  if (passo.acao === 'digitar') {
    await alvo.click();
    await alvo.fill('');
    await alvo.pressSequentially(passo.texto, { delay: devagar ? 55 : 0 });
  } else if (passo.acao === 'selecionar') {
    await alvo.selectOption(passo.valor);
  } else if (passo.acao === 'passar') {
    await alvo.hover();
  } else if (passo.acao !== 'nenhuma') {
    await alvo.click();
  }
  if (passo.depois) await passo.depois(page);
  await page.waitForTimeout(passo.esperar ?? 1100);
}

const pct = (valor, total) => Math.round((valor / total) * 10000) / 100;

/**
 * @returns {Promise<Array<{ legenda: string, ponto: null | { x: number, y: number, w: number, h: number } }>>}
 */
export async function capturarTour(browser, roteiro, tema, pasta) {
  const { ctx, page } = await abrirPainel(browser, { tema });
  const passos = [];
  try {
    await abrirRoteiro(page, roteiro);
    for (const [i, passo] of roteiro.passos.entries()) {
      if (passo.antes) await passo.antes(page);
      let ponto = null;
      let alvo = null;
      if (passo.alvo) {
        alvo = localizar(page, passo.alvo);
        await alvo.waitFor({ state: 'visible', timeout: 15000 }).catch(e => {
          throw new Error(`passo ${i + 1} (${passo.legenda}): ${e.message.split('\n')[0]}`);
        });
        await alvo.scrollIntoViewIfNeeded().catch(() => {});
        await page.waitForTimeout(350);
        const box = await alvo.boundingBox();
        if (box) {
          const folga = 6;
          ponto = {
            x: pct(Math.max(0, box.x - folga), TELA.largura),
            y: pct(Math.max(0, box.y - folga), TELA.altura),
            w: pct(box.width + folga * 2, TELA.largura),
            h: pct(box.height + folga * 2, TELA.altura),
          };
        }
      }
      const png = `${pasta}/tmp-${tema}-${i}.png`;
      await page.screenshot({ path: png });
      execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', png, '-c:v', 'libwebp', '-quality', '82', `${pasta}/passo-${String(i + 1).padStart(2, '0')}-${tema}.webp`]);
      fs.unlinkSync(png);
      passos.push({ legenda: passo.legenda, ...(passo.detalhe ? { detalhe: passo.detalhe } : {}), ponto });
      if (alvo && passo.acao !== 'nenhuma') await agir(page, passo, alvo);
      else if (passo.depois) await passo.depois(page);
    }
  } finally {
    await ctx.close();
  }
  return passos;
}
