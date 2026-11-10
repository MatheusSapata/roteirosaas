// Mockups brancos (notebook + destaques flutuantes) do Roteiro Online e do Viaje On.
// Tudo vem de telas reais no tema claro (pasta recortes/):
//   - Viaje On: repositório do sistema (oi-charm-glow), public/lp-black/assets/tela-painel.webp
//     e public/help/shots/*-light.webp (agência fictícia "Serra Turismo").
//   - Roteiro Online: frontend/src/help/media (agência de demonstração "Rota Sul Viagens")
//     e uma página publicada no celular.
//
//   node gerar-mockups.cjs   →   mockup-viaje-on.jpg e mockup-roteiro-online.jpg (2400x1800)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const R = n => 'file://' + path.join(__dirname, 'recortes', n);

const CSS = `
*{box-sizing:border-box;margin:0;padding:0}
body{width:1200px;height:900px;overflow:hidden;font-family:Inter,sans-serif;
  background:radial-gradient(ellipse 60% 55% at 50% 45%,#ffffff 0%,#F3F5F3 70%,#ECEFEC 100%)}
.abs{position:absolute}
/* notebook */
.nb{position:absolute;left:50%;transform:translateX(-50%)}
.nb .tampa{position:relative;background:#0E0F10;border-radius:26px 26px 8px 8px;padding:14px 14px 20px;
  box-shadow:0 0 0 1.5px #3a3c3f inset,0 0 0 3px #c9ccce,0 50px 90px -40px rgba(20,30,25,.45)}
.nb .tampa::before{content:"";position:absolute;top:0;left:50%;transform:translateX(-50%);width:96px;height:16px;background:#0E0F10;border-radius:0 0 10px 10px;z-index:2}
.nb .tela{border-radius:6px;overflow:hidden;background:#fff}
.nb .tela img{display:block;width:100%}
.nb .base{position:relative;height:20px;margin:0 -9%;border-radius:2px 2px 22px 22px;
  background:linear-gradient(#e9ebec 0%,#d3d6d8 45%,#a9adb0 100%);box-shadow:0 26px 40px -16px rgba(20,30,25,.45)}
.nb .base::before{content:"";position:absolute;left:50%;top:0;width:17%;height:9px;transform:translateX(-50%);background:linear-gradient(#bfc3c6,#d9dcde);border-radius:0 0 12px 12px}
.nb .sombra{position:absolute;left:-6%;right:-6%;bottom:-38px;height:40px;background:radial-gradient(ellipse at center,rgba(0,0,0,.22),transparent 70%);filter:blur(6px)}
/* destaques flutuantes */
.flut{position:absolute;border-radius:18px;overflow:hidden;background:#fff;
  box-shadow:0 0 0 1px rgba(15,40,30,.06),0 30px 60px -18px rgba(15,40,30,.28),0 10px 20px -10px rgba(15,40,30,.12)}
.flut img{display:block;width:100%}
.celular{position:absolute;background:#0E0F10;border-radius:42px;padding:9px;
  box-shadow:0 0 0 2px #c9ccce,0 40px 70px -20px rgba(15,40,30,.4)}
.celular .t{position:relative;border-radius:34px;overflow:hidden}
.celular img{display:block;width:100%}
.celular .ilha{position:absolute;top:10px;left:50%;transform:translateX(-50%);width:34%;height:22px;background:#000;border-radius:20px}
`;

const pagina = corpo => `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700&display=block" rel="stylesheet">
<style>${CSS}</style></head><body>${corpo}</body></html>`;

const notebook = (img, w, top) => `<div class="nb" style="width:${w}px;top:${top}px"><div class="tampa"><div class="tela"><img src="${R(img)}"></div></div><div class="base"></div><div class="sombra"></div></div>`;
const flut = (img, w, pos, raio = 18) => `<div class="flut" style="width:${w}px;${pos};border-radius:${raio}px"><img src="${R(img)}"></div>`;

const MOCKUPS = {
  'mockup-viaje-on': pagina(`
    ${notebook('vo-painel.png', 760, 190)}
    ${flut('vo-ocupacao.png', 290, 'left:46px;top:610px', 20)}
    ${flut('vo-poltronas.png', 180, 'left:92px;top:330px', 18)}
    ${flut('vo-saldo.png', 270, 'right:44px;top:140px', 16)}
    ${flut('vo-pacote.png', 300, 'right:56px;top:640px', 14)}
  `),
  'mockup-roteiro-online': pagina(`
    ${notebook('ro-painel.png', 760, 190)}
    ${flut('ro-visitas.png', 250, 'left:46px;top:330px', 18)}
    ${flut('ro-conversao.png', 260, 'left:80px;top:560px', 18)}
    ${flut('ro-lead-linha.png', 400, 'right:120px;top:130px', 14)}
    <div class="celular" style="width:210px;right:50px;top:330px"><div class="t"><img src="${R('ro-celular.jpg')}"><div class="ilha"></div></div></div>
  `)
};

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: 2 });
  for (const [nome, html] of Object.entries(MOCKUPS)) {
    const tmp = path.join(__dirname, '.tmp.html');
    fs.writeFileSync(tmp, html);
    await p.goto('file://' + tmp, { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: path.join(__dirname, nome + '.jpg'), type: 'jpeg', quality: 92 });
    fs.rmSync(tmp);
    console.log('✓', nome);
  }
  await b.close();
})();
