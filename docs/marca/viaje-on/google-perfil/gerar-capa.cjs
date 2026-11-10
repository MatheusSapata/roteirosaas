// Capa do Perfil da Empresa no Google da Viaje On (1920x1080), feita com telas reais do
// Sistema Viaje On (repositório oi-charm-glow, public/apresentacao/telas, agência fictícia
// "Serra Turismo") e o logo oficial (public/brand/viajeon-logo-dark.png). Os recortes ficam em real/.
//
//   node gerar-capa.cjs   →   capa-viaje-on.jpg
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const R = n => 'file://' + path.join(__dirname, 'real', n);

const html = `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fraunces:ital,opsz,wght@1,9..144,600&display=block" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{width:1920px;height:1080px;overflow:hidden;font-family:Inter,sans-serif;-webkit-font-smoothing:antialiased;color:#fff;
  background:radial-gradient(ellipse 55% 60% at 78% 45%,rgba(37,230,160,.16),transparent 70%),radial-gradient(ellipse 45% 55% at 0% 100%,rgba(21,145,92,.28),transparent 70%),#0A110E}
body::before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(144,238,143,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(144,238,143,.05) 1px,transparent 1px);background-size:56px 56px;mask-image:radial-gradient(ellipse 70% 70% at 40% 50%,#000,transparent)}
.abs{position:absolute}
h1{font-size:80px;font-weight:800;letter-spacing:-.04em;line-height:1.02}
h1 em{font-family:Fraunces,serif;font-weight:600;letter-spacing:-.02em;color:#90EE8F}
.sub{font-size:28px;line-height:1.45;color:rgba(255,255,255,.72);font-weight:450}
.tags{display:flex;gap:12px;flex-wrap:wrap}
.tag{padding:10px 16px;border-radius:999px;font-size:17px;font-weight:650;background:rgba(144,238,143,.10);border:1px solid rgba(144,238,143,.28);color:#C9F7C8}
.laptop .tela{background:#050806;border-radius:22px 22px 6px 6px;padding:14px 14px 18px;box-shadow:0 0 0 2px #262d29 inset,0 50px 100px -30px rgba(0,0,0,.8)}
.laptop img{display:block;width:100%;border-radius:6px}
.laptop .base{height:22px;margin:0 -6%;background:linear-gradient(#cfd6d2,#8f9893);border-radius:0 0 24px 24px;position:relative}
.laptop .base::before{content:"";position:absolute;left:50%;top:0;width:15%;height:8px;transform:translateX(-50%);background:#aeb6b1;border-radius:0 0 10px 10px}
.flut{border-radius:22px;overflow:hidden;box-shadow:0 0 0 1px rgba(144,238,143,.22),0 40px 80px -20px rgba(0,0,0,.85)}
.flut img{display:block;width:100%}
</style></head><body>
  <div class="abs" style="left:110px;top:104px"><img src="${R('viajeon-logo-dark.png')}" style="height:70px"></div>
  <div class="abs" style="left:110px;top:280px;width:800px">
    <h1>A operação da sua agência <em>em um só lugar</em></h1>
    <p class="sub" style="margin-top:30px;width:700px">Vendas online, poltronas, contratos, rooming list e financeiro de cada viagem, no mesmo sistema.</p>
    <div class="tags" style="margin-top:40px"><span class="tag">Venda por link</span><span class="tag">Mapa de poltronas</span><span class="tag">Contrato automático</span><span class="tag">Financeiro</span></div>
  </div>
  <div class="abs" style="left:110px;bottom:88px;font-size:24px;font-weight:600;color:rgba(255,255,255,.6)">viajeon.com</div>

  <div class="abs laptop" style="left:930px;top:120px;width:900px"><div class="tela"><img src="${R('painel.jpg')}"></div><div class="base"></div></div>
  <div class="abs flut" style="left:1520px;top:70px;width:320px">${'<img src="' + R('kpi-valor-vendido.png') + '">'}</div>
  <div class="abs flut" style="left:860px;top:800px;width:820px">${'<img src="' + R('card-operacao.png') + '">'}</div>
</body></html>`;

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const tmp = path.join(__dirname, '.capa.html');
  fs.writeFileSync(tmp, html);
  await p.goto('file://' + tmp, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.screenshot({ path: path.join(__dirname, 'capa-viaje-on.jpg'), type: 'jpeg', quality: 92 });
  fs.rmSync(tmp);
  await b.close();
  console.log('✓ capa-viaje-on.jpg');
})();
