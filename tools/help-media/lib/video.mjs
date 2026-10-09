// Vídeo curto (MP4, sem som, em repetição na Central de Ajuda): o mesmo roteiro da
// demonstração, com um cursor que desliza até cada alvo, a marca do clique e a
// legenda do passo embaixo. Grava no tema claro.
import fs from 'fs';
import { execFileSync } from 'child_process';
import { TELA, abrirPainel } from './sessao.mjs';
import { abrirRoteiro, agir, localizar } from './tour.mjs';

const CAMADA = `
<style>
  #hm-layer{position:fixed;inset:0;pointer-events:none;z-index:2147483647;font-family:Inter,system-ui,sans-serif}
  #hm-cursor{position:absolute;left:720px;top:470px;width:28px;height:28px;transition:left .85s cubic-bezier(.4,0,.2,1),top .85s cubic-bezier(.4,0,.2,1);filter:drop-shadow(0 2px 4px rgba(0,0,0,.35))}
  #hm-click{position:absolute;width:70px;height:70px;margin:-35px 0 0 -35px;border-radius:50%;border:4px solid #0b8059;background:rgba(11,128,89,.18);opacity:0;transform:scale(.4)}
  #hm-click.on{animation:hm-rip .9s ease-out forwards}
  @keyframes hm-rip{0%{opacity:1;transform:scale(.4)}45%{opacity:1;transform:scale(1)}100%{opacity:0;transform:scale(1.15)}}
  #hm-cap{position:absolute;left:50%;bottom:28px;max-width:80%;transform:translate(-50%,16px);opacity:0;transition:all .4s ease;background:rgba(10,20,16,.9);color:#fff;padding:12px 22px 12px 12px;border-radius:999px;font-size:19px;font-weight:600;letter-spacing:-.01em;display:flex;gap:12px;align-items:center;box-shadow:0 10px 30px -8px rgba(0,0,0,.45)}
  #hm-cap.on{opacity:1;transform:translate(-50%,0)}
  #hm-cap b{flex:none;background:#12b981;color:#06140e;border-radius:999px;width:30px;height:30px;display:grid;place-items:center;font-size:15px}
</style>
<svg id="hm-cursor" viewBox="0 0 24 24"><path d="M4 2l16 10.5-7.2 1.4L9.6 21z" fill="#0f1713" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>
<div id="hm-click"></div>
<div id="hm-cap"><b></b><span></span></div>`;

async function garantirCamada(page) {
  await page.evaluate(html => {
    if (document.getElementById('hm-layer')) return;
    const el = document.createElement('div');
    el.id = 'hm-layer';
    el.innerHTML = html;
    document.body.appendChild(el);
  }, CAMADA);
}

const legenda = (page, n, texto) =>
  page.evaluate(([n, texto]) => {
    const cap = document.getElementById('hm-cap');
    cap.classList.remove('on');
    setTimeout(() => {
      cap.querySelector('b').textContent = n;
      cap.querySelector('span').textContent = texto;
      cap.classList.add('on');
    }, 120);
  }, [n, texto]);

const moverCursor = (page, x, y) =>
  page.evaluate(([x, y]) => {
    const c = document.getElementById('hm-cursor');
    c.style.left = `${x}px`;
    c.style.top = `${y}px`;
  }, [x, y]);

const marcarClique = (page, x, y) =>
  page.evaluate(([x, y]) => {
    const m = document.getElementById('hm-click');
    m.style.left = `${x}px`;
    m.style.top = `${y}px`;
    m.classList.remove('on');
    void m.offsetWidth;
    m.classList.add('on');
  }, [x, y]);

export async function gravarVideo(browser, roteiro, destino, pastaTmp) {
  fs.mkdirSync(pastaTmp, { recursive: true });
  const t0 = Date.now();
  const { ctx, page } = await abrirPainel(browser, { tema: 'light', video: pastaTmp });
  let inicio = 0;
  try {
    await abrirRoteiro(page, roteiro);
    await garantirCamada(page);
    inicio = (Date.now() - t0) / 1000;
    await page.waitForTimeout(700);
    for (const [i, passo] of roteiro.passos.entries()) {
      if (passo.antes) await passo.antes(page);
      await garantirCamada(page);
      await legenda(page, i + 1, passo.legenda);
      if (passo.alvo) {
        const alvo = localizar(page, passo.alvo);
        await alvo.waitFor({ state: 'visible', timeout: 15000 });
        await alvo.scrollIntoViewIfNeeded().catch(() => {});
        const box = await alvo.boundingBox();
        if (box) {
          const x = box.x + Math.min(box.width / 2, 60);
          const y = box.y + box.height / 2;
          await moverCursor(page, x, y);
          await page.waitForTimeout(1000);
          if (passo.acao !== 'nenhuma' && passo.acao !== 'passar') await marcarClique(page, x, y);
          await page.waitForTimeout(passo.acao === 'nenhuma' ? 1600 : 450);
        }
        if (passo.acao !== 'nenhuma') await agir(page, passo, alvo, { devagar: true });
        else if (passo.depois) await passo.depois(page);
      } else {
        await page.waitForTimeout(2200);
      }
    }
    await page.waitForTimeout(1200);
  } finally {
    await page.close();
    await ctx.close();
  }
  const webm = fs.readdirSync(pastaTmp).filter(f => f.endsWith('.webm')).map(f => `${pastaTmp}/${f}`).sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs)[0];
  execFileSync('ffmpeg', [
    '-loglevel', 'error', '-y', '-ss', String(Math.max(0, inicio - 0.2)), '-i', webm,
    '-vf', `scale=${Math.round(TELA.largura * 0.889)}:-2,fps=30`,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '28', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', destino,
  ]);
  fs.rmSync(pastaTmp, { recursive: true, force: true });
}
