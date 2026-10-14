// Camada das animações da página de vendas (lp-editor.mjs, lp-assistente.mjs): cursor, marca do
// clique e legenda grande por cima da tela gravada (a LP mostra o vídeo com uns 600 px de largura).

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

export const garantirCamada = page =>
  page.evaluate(html => {
    if (document.getElementById('hm-layer')) return;
    const el = document.createElement('div');
    el.id = 'hm-layer';
    el.innerHTML = html;
    document.body.appendChild(el);
  }, CAMADA);

export const legenda = (page, n, texto) =>
  page.evaluate(([n, texto]) => {
    const cap = document.getElementById('hm-cap');
    cap.classList.remove('on');
    setTimeout(() => {
      cap.querySelector('b').textContent = n;
      cap.querySelector('span').textContent = texto;
      cap.classList.add('on');
    }, 160);
  }, [String(n), texto]);

export const moverCursor = (page, x, y) =>
  page.evaluate(([x, y]) => Object.assign(document.getElementById('hm-cursor').style, { left: `${x}px`, top: `${y}px` }), [x, y]);

export const marcarClique = (page, x, y) =>
  page.evaluate(([x, y]) => {
    const m = document.getElementById('hm-click');
    Object.assign(m.style, { left: `${x}px`, top: `${y}px` });
    m.classList.remove('on');
    void m.offsetWidth;
    m.classList.add('on');
  }, [x, y]);
