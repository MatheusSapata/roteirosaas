// Gera as imagens do Perfil da Empresa no Google (catálogo de produtos, fotos, capa e destaques).
// Usa as telas reais do sistema (agência de demonstração "Rota Sul Viagens", em
// frontend/src/help/media) e páginas publicadas capturadas no celular (pasta celular/).
//
//   node gerar.cjs            todas as peças
//   node gerar.cjs p01 f03    só as pedidas (pelo prefixo do nome)
//
// Saída: produtos/, fotos/ e destaques/ ao lado deste arquivo, em JPG.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const AQUI = __dirname;
const RAIZ = path.resolve(AQUI, '../../../..');
const TELA = n => 'file://' + path.join(RAIZ, 'frontend/src/help/media', n);
const CEL = n => 'file://' + path.join(AQUI, 'celular', n + '.jpg');
const LOGO = n => 'file://' + path.join(RAIZ, 'docs/marca/roteiro-online/svg', `roteiro-online-${n}.svg`);

// ---------- peças reutilizáveis ----------
const ico = (nome, cls = '') => `<i data-lucide="${nome}" class="${cls}"></i>`;
const laptop = (src, w) => `
  <div class="laptop" style="width:${w}px">
    <div class="lp-screen"><img src="${src}"></div>
    <div class="lp-base"></div>
  </div>`;
const janela = (src, w, url = 'roteiroonline.com') => `
  <div class="janela" style="width:${w}px">
    <div class="jn-bar"><span></span><span></span><span></span><div class="jn-url">${ico('lock')}${url}</div></div>
    <img src="${src}">
  </div>`;
const celular = (src, w, extra = '') => `
  <div class="celular" style="width:${w}px;${extra}">
    <div class="cl-tela"><img src="${src}"><div class="cl-ilha"></div></div>
  </div>`;
const selo = (txt, i = 'sparkles') => `<span class="selo">${ico(i)}${txt}</span>`;
const lista = itens => `<ul class="lista">${itens.map(t => `<li>${ico('circle-check')}<span>${t}</span></li>`).join('')}</ul>`;
const logo = (v = 'horizontal-fundo-escuro', h = 46) => `<img class="logo" src="${LOGO(v)}" style="height:${h}px">`;
const rodape = (txt = 'roteiroonline.com') => `<div class="rodape">${ico('globe')}${txt}</div>`;

// ---------- estilos ----------
const CSS = `
:root{--noite:#0A110E;--noite2:#0F1D17;--noite3:#14281F;--viaje:#0A6346;--on:#90EE8F;--trilha:#15915C;--nevoa:#EFF3ED;--tinta:#0B1712;--mudo:#55665E;}
*{box-sizing:border-box;margin:0;padding:0}
body{width:var(--w);height:var(--h);overflow:hidden;font-family:Inter,sans-serif;-webkit-font-smoothing:antialiased}
.pc{position:relative;width:100%;height:100%;overflow:hidden}
.escuro{background:radial-gradient(ellipse 70% 60% at 85% 10%,rgba(144,238,143,.16),transparent 65%),radial-gradient(ellipse 60% 50% at 0% 100%,rgba(21,145,92,.30),transparent 70%),var(--noite);color:#fff}
.verde{background:radial-gradient(ellipse 70% 60% at 90% 0%,rgba(144,238,143,.28),transparent 60%),linear-gradient(160deg,#0C7452,var(--viaje) 55%,#06402D);color:#fff}
.claro{background:radial-gradient(ellipse 60% 50% at 100% 0%,rgba(144,238,143,.45),transparent 65%),var(--nevoa);color:var(--tinta)}
.grade::before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(144,238,143,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(144,238,143,.06) 1px,transparent 1px);background-size:48px 48px;mask-image:radial-gradient(ellipse 80% 70% at 50% 40%,#000,transparent);pointer-events:none}
.claro.grade::before{background-image:linear-gradient(rgba(10,99,70,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(10,99,70,.06) 1px,transparent 1px)}
h1,h2,h3{font-family:Sora,Inter,sans-serif;letter-spacing:-.025em;line-height:1.06;font-weight:800}
h1{font-size:76px} h2{font-size:58px} h3{font-size:30px;font-weight:700}
.dest{color:var(--on)} .claro .dest{color:var(--trilha)}
.sub{font-size:25px;line-height:1.42;color:rgba(255,255,255,.78);font-weight:450}
.claro .sub{color:var(--mudo)}
.selo{display:inline-flex;align-items:center;gap:10px;padding:10px 18px;border-radius:999px;font-weight:700;font-size:19px;letter-spacing:.01em;background:rgba(144,238,143,.14);color:var(--on);border:1px solid rgba(144,238,143,.35)}
.claro .selo{background:#fff;color:var(--viaje);border-color:rgba(10,99,70,.18)}
.selo svg{width:20px;height:20px}
.lista{list-style:none;display:grid;gap:16px}
.lista li{display:flex;gap:14px;align-items:flex-start;font-size:var(--fs,24px);font-weight:550;line-height:1.3}
.lista svg{flex:none;width:28px;height:28px;color:var(--on);margin-top:1px}
.claro .lista svg{color:var(--trilha)}
.rodape{position:absolute;display:flex;align-items:center;gap:10px;font-weight:650;font-size:21px;color:rgba(255,255,255,.7)}
.rodape svg{width:22px;height:22px;color:var(--on)}
.claro .rodape{color:var(--mudo)} .claro .rodape svg{color:var(--trilha)}
.abs{position:absolute}
/* dispositivos */
.laptop .lp-screen{background:#0b0f0d;border-radius:22px 22px 6px 6px;padding:14px 14px 18px;box-shadow:0 0 0 2px #2a312d inset,0 40px 80px -20px rgba(0,0,0,.55)}
.laptop .lp-screen img{display:block;width:100%;border-radius:6px}
.laptop .lp-base{height:20px;margin:0 -7%;background:linear-gradient(#d7ddd9,#9aa39e);border-radius:0 0 22px 22px;position:relative;box-shadow:0 30px 50px -18px rgba(0,0,0,.6)}
.laptop .lp-base::before{content:"";position:absolute;left:50%;top:0;width:16%;height:8px;transform:translateX(-50%);background:#b6beb9;border-radius:0 0 10px 10px}
.janela{border-radius:18px;overflow:hidden;background:#fff;box-shadow:0 0 0 1px rgba(0,0,0,.08),0 40px 90px -25px rgba(0,0,0,.55)}
.janela .jn-bar{height:46px;display:flex;align-items:center;gap:9px;padding:0 18px;background:#F4F7F5;border-bottom:1px solid #E1E8E4}
.janela .jn-bar>span{width:13px;height:13px;border-radius:50%;background:#E5484D}.janela .jn-bar>span:nth-child(2){background:#F5B83D}.janela .jn-bar>span:nth-child(3){background:#3CC66B}
.janela .jn-url{margin-left:18px;flex:1;max-width:520px;height:28px;border-radius:999px;background:#fff;border:1px solid #E1E8E4;display:flex;align-items:center;gap:8px;padding:0 14px;font-size:15px;color:#55665E;font-weight:500}
.janela .jn-url svg{width:14px;height:14px;color:var(--trilha)}
.janela img{display:block;width:100%}
.celular{background:#0b0f0d;border-radius:15%/7%;padding:3.2%;box-shadow:0 0 0 2px #2c3430,0 0 0 5px #0b0f0d,0 50px 90px -25px rgba(0,0,0,.65)}
.cl-tela{position:relative;width:100%;aspect-ratio:390/844;border-radius:12.5%/5.8%;overflow:hidden;background:#fff}
.cl-tela img{display:block;width:100%;height:100%;object-fit:cover;object-position:top}
.cl-ilha{position:absolute;top:2.1%;left:50%;width:31%;height:3.6%;transform:translateX(-50%);background:#000;border-radius:999px}
/* cartões */
.cartao{background:rgba(255,255,255,.05);border:1px solid rgba(144,238,143,.18);border-radius:28px;padding:30px;box-shadow:0 10px 30px rgba(0,0,0,.22)}
.claro .cartao{background:#fff;border-color:rgba(10,99,70,.12);box-shadow:0 18px 40px -22px rgba(10,60,40,.35)}
.cartao .ic{width:58px;height:58px;border-radius:16px;display:grid;place-items:center;background:rgba(144,238,143,.15);color:var(--on);margin-bottom:18px}
.claro .cartao .ic{background:#E3F4E6;color:var(--viaje)}
.cartao .ic svg{width:30px;height:30px}
.cartao h3{font-size:27px;margin-bottom:8px}
.cartao p{font-size:20px;line-height:1.4;color:rgba(255,255,255,.72)}
.claro .cartao p{color:var(--mudo)}
.chip{display:inline-flex;align-items:center;gap:10px;padding:13px 20px;border-radius:16px;background:#fff;color:var(--tinta);font-weight:700;font-size:21px;box-shadow:0 18px 40px -15px rgba(0,0,0,.45)}
.chip svg{width:24px;height:24px;color:var(--trilha)}
.chip.escuro{background:var(--noite2);color:#fff;border:1px solid rgba(144,238,143,.3)}
.chip.escuro svg{color:var(--on)}
.num{font-family:Sora,Inter;font-weight:800;font-size:64px;letter-spacing:-.03em;color:var(--on);line-height:1}
.claro .num{color:var(--viaje)}
`;

const pagina = (w, h, corpo) => `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Sora:wght@600;700;800&display=block" rel="stylesheet">
<script src="https://unpkg.com/lucide@0.460.0/dist/umd/lucide.min.js"></script>
<style>${CSS} :root{--w:${w}px;--h:${h}px}</style></head><body>${corpo}
<script>lucide.createIcons({attrs:{'stroke-width':2.2}});</script></body></html>`;

// ---------- peças ----------
const Q = [1200, 1200];   // produto (quadrado)
const F = [1200, 900];    // foto/destaque 4:3
const PECAS = [];
const peca = (arquivo, [w, h], corpo) => PECAS.push({ arquivo, w, h, corpo });

// ===== PRODUTOS (catálogo) =====
peca('produtos/p01-roteiro-online-assinatura', Q, `
<div class="pc escuro grade">
  <div class="abs" style="left:72px;top:72px">${logo('horizontal-fundo-escuro', 50)}</div>
  <div class="abs" style="left:72px;top:170px;width:1056px">
    ${selo('Plano único com tudo incluso', 'badge-check')}
    <h1 style="margin-top:26px">Páginas de roteiro<br>que <span class="dest">vendem</span></h1>
    <p class="sub" style="margin-top:22px;width:820px">Crie a página da sua viagem em minutos e mande o link no WhatsApp. Sem designer, sem programação.</p>
  </div>
  <div class="abs" style="left:72px;top:560px;width:430px">${lista(['Roteiros ilimitados', 'Editor visual', 'Assistente de IA', 'Módulo Leads', 'Pixels Meta e Google', 'Domínio próprio'])}</div>
  <div class="abs" style="right:-120px;top:560px">${laptop(TELA('conhecer-o-painel/passo-01-dark.webp'), 760)}</div>
  <div class="abs" style="right:400px;top:700px">${celular(CEL('italia-0'), 210)}</div>
  <div class="abs" style="left:72px;bottom:60px"><span class="chip">${ico('shield-check')}7 dias de garantia</span></div>
</div>`);

peca('produtos/p02-editor-visual', Q, `
<div class="pc claro grade">
  <div class="abs" style="left:72px;top:76px;width:1056px">
    ${selo('Editor visual', 'mouse-pointer-click')}
    <h2 style="margin-top:24px">Monte o roteiro com<br><span class="dest">seções prontas</span></h2>
    <p class="sub" style="margin-top:18px;width:900px">Capa, itinerário dia a dia, inclusos, preços e dúvidas. É só trocar o conteúdo.</p>
  </div>
  <div class="abs" style="left:72px;top:440px">${janela(TELA('titulo-e-link/passo-01-light.webp'), 1000, 'roteiroonline.com/admin')}</div>
  <div class="abs" style="right:44px;bottom:-60px">${celular(CEL('abrolhos-2'), 260)}</div>
</div>`);

peca('produtos/p03-assistente-de-ia', Q, `
<div class="pc escuro grade">
  <div class="abs" style="left:72px;top:76px;width:1056px">
    ${selo('Assistente de IA', 'sparkles')}
    <h2 style="margin-top:24px">Conte a viagem.<br><span class="dest">A IA monta a página.</span></h2>
    <p class="sub" style="margin-top:18px;width:960px">Banner, roteiro dia a dia, inclusos, preços e dúvidas, com fotos. Você só revisa e publica.</p>
  </div>
  <div class="abs" style="left:72px;top:470px;display:flex;gap:14px">
    <span class="chip escuro">${ico('message-circle')}Texto</span><span class="chip escuro">${ico('mic')}Áudio</span><span class="chip escuro">${ico('file-text')}PDF</span><span class="chip escuro">${ico('images')}Prints e fotos</span>
  </div>
  <div class="abs" style="left:110px;top:580px">${janela(TELA('assistente-ia/passo-03-light.webp'), 1100, 'roteiroonline.com/admin')}</div>
</div>`);

peca('produtos/p04-modulo-leads', Q, `
<div class="pc verde grade">
  <div class="abs" style="left:72px;top:76px;width:1056px">
    ${selo('Módulo Leads', 'magnet')}
    <h2 style="margin-top:24px">Cada interessado vira<br><span class="dest">oportunidade de venda</span></h2>
    <p class="sub" style="margin-top:18px;width:960px">Formulário dentro do roteiro, funil por etapas e contato no WhatsApp com um clique.</p>
  </div>
  <div class="abs" style="left:72px;top:450px">${janela(TELA('oportunidades/passo-01-light.webp'), 1180, 'roteiroonline.com/admin/leads')}</div>
  <div class="abs" style="right:60px;top:410px"><span class="chip">${ico('bell-ring')}Novo lead: Jalapão 6 dias</span></div>
</div>`);

peca('produtos/p05-pagina-de-roteiro-no-celular', Q, `
<div class="pc claro grade">
  <div class="abs" style="left:0;right:0;top:70px;text-align:center">
    ${selo('100% pensado para o celular', 'smartphone')}
    <h2 style="margin-top:22px">Um link só, que abre<br>em <span class="dest">qualquer celular</span></h2>
  </div>
  <div class="abs" style="left:110px;top:430px;transform:rotate(-5deg)">${celular(CEL('abrolhos-0'), 300)}</div>
  <div class="abs" style="left:450px;top:380px;z-index:2">${celular(CEL('beto-2'), 300)}</div>
  <div class="abs" style="left:790px;top:430px;transform:rotate(5deg)">${celular(CEL('salvador-3'), 300)}</div>
</div>`);

peca('produtos/p06-pixel-meta-e-google', Q, `
<div class="pc escuro grade">
  <div class="abs" style="left:72px;top:76px;width:1056px">
    ${selo('Pixel Meta e Google', 'chart-column')}
    <h2 style="margin-top:24px">Anuncie para a página e<br>faça <span class="dest">remarketing</span></h2>
    <p class="sub" style="margin-top:18px;width:960px">Acompanhe visitas, cliques no WhatsApp e leads de cada roteiro no painel.</p>
  </div>
  <div class="abs" style="left:72px;top:470px">${laptop(TELA('conhecer-o-painel/passo-02-dark.webp'), 820)}</div>
  <div class="abs" style="right:60px;top:500px;display:grid;gap:16px">
    <span class="chip">${ico('activity')}Pixel Meta</span><span class="chip">${ico('chart-line')}Google Ads</span><span class="chip">${ico('bar-chart-3')}Google Analytics</span>
  </div>
</div>`);

peca('produtos/p07-dominio-proprio', Q, `
<div class="pc verde grade">
  <div class="abs" style="left:72px;top:76px;width:1056px">
    ${selo('Domínio próprio', 'globe')}
    <h2 style="margin-top:24px">Seus roteiros no<br><span class="dest">endereço da sua agência</span></h2>
    <p class="sub" style="margin-top:18px;width:960px">Publique com um clique em domínio seguro. Alterou? Atualiza para todo mundo na hora.</p>
  </div>
  <div class="abs" style="left:72px;top:445px"><span class="chip" style="font-size:26px;padding:18px 26px">${ico('lock')}<span>roteiros.<b style="color:var(--viaje)">suaagencia</b>.com.br/jalapao</span></span></div>
  <div class="abs" style="left:72px;top:560px">${janela(TELA('dominio-proprio/passo-02-light.webp'), 1180, 'roteiroonline.com/admin/dominios')}</div>
</div>`);

peca('produtos/p08-precos-e-whatsapp', Q, `
<div class="pc claro grade">
  <div class="abs" style="left:72px;top:76px;width:480px">
    ${selo('Preços e WhatsApp', 'credit-card')}
    <h2 style="margin-top:24px">Do roteiro à <span class="dest">reserva</span> no WhatsApp</h2>
    <p class="sub" style="margin-top:20px">Cards de investimento para adulto, criança e tipo de quarto, contagem regressiva e botão de WhatsApp com mensagem pronta.</p>
  </div>
  <div class="abs" style="left:72px;top:640px;width:480px">${lista(['Quantas categorias de preço precisar', 'Pix, cartão e parcelamento', 'Contagem regressiva até a saída', 'Lead chega sabendo o roteiro'])}</div>
  <div class="abs" style="right:270px;top:300px;transform:rotate(-4deg)">${celular(CEL('serra-3'), 290)}</div>
  <div class="abs" style="right:30px;top:360px;transform:rotate(4deg)">${celular(CEL('salvador-3'), 290)}</div>
</div>`);

// ===== FOTOS (capa, logo e telas) =====
peca('fotos/f01-capa', [1920, 1080], `
<div class="pc escuro grade">
  <div class="abs" style="left:110px;top:120px">${logo('horizontal-fundo-escuro', 64)}</div>
  <div class="abs" style="left:110px;top:270px;width:820px">
    <h1 style="font-size:92px">Páginas de roteiro<br>que <span class="dest">vendem</span></h1>
    <p class="sub" style="margin-top:28px;font-size:30px">Crie a página da sua viagem em minutos, mande o link no WhatsApp e faça o cliente ver o valor antes do preço.</p>
    <div style="margin-top:44px;display:flex;gap:14px;flex-wrap:wrap">${selo('Assistente de IA', 'sparkles')}${selo('Módulo Leads', 'magnet')}${selo('7 dias de garantia', 'shield-check')}</div>
  </div>
  <div class="abs" style="left:990px;top:230px">${laptop(TELA('titulo-e-link/passo-01-light.webp'), 860)}</div>
  <div class="abs" style="left:1640px;top:400px">${celular(CEL('italia-0'), 240)}</div>
  <div class="rodape" style="left:110px;bottom:80px;font-size:26px">${ico('globe')}roteiroonline.com</div>
</div>`);

peca('fotos/f02-logo', [720, 720], `
<div class="pc verde" style="display:grid;place-items:center">${logo('vertical-fundo-verde', 440)}</div>`);

peca('fotos/f03-painel', F, `
<div class="pc escuro grade">
  <div class="abs" style="left:64px;top:56px">${selo('Painel da agência', 'layout-dashboard')}<h2 style="margin-top:18px;font-size:50px">Visitas, cliques e leads<br>de cada roteiro, <span class="dest">em um lugar</span></h2></div>
  <div class="abs" style="left:150px;top:330px">${laptop(TELA('conhecer-o-painel/passo-01-dark.webp'), 900)}</div>
</div>`);

peca('fotos/f04-editor-computador-e-celular', F, `
<div class="pc claro grade">
  <div class="abs" style="left:64px;top:56px">${selo('Editor visual', 'mouse-pointer-click')}<h2 style="margin-top:18px;font-size:50px">Edite no computador,<br>veja como fica <span class="dest">no celular</span></h2></div>
  <div class="abs" style="left:64px;top:330px">${laptop(TELA('cores-da-pagina/passo-01-light.webp'), 860)}</div>
  <div class="abs" style="right:60px;top:300px">${celular(CEL('abrolhos-0'), 250)}</div>
</div>`);

peca('fotos/f05-roteiros-no-celular', F, `
<div class="pc verde grade">
  <div class="abs" style="left:64px;top:60px;width:460px">${selo('Exemplos reais', 'map-pinned')}<h2 style="margin-top:20px;font-size:52px">Roteiros que o passageiro <span class="dest">abre, revisita e compartilha</span></h2>
  <div style="margin-top:34px">${lista(['Itinerário dia a dia', 'Galeria com carrossel', 'Botão de WhatsApp'])}</div></div>
  <div class="abs" style="left:560px;top:120px;transform:rotate(-4deg)">${celular(CEL('italia-2'), 290)}</div>
  <div class="abs" style="left:850px;top:70px;transform:rotate(3deg)">${celular(CEL('abrolhos-0'), 290)}</div>
</div>`);

peca('fotos/f06-paginas-da-agencia', F, `
<div class="pc claro grade">
  <div class="abs" style="left:64px;top:56px">${selo('Páginas', 'files')}<h2 style="margin-top:18px;font-size:50px">Todos os roteiros da agência,<br><span class="dest">duplicados em um clique</span></h2></div>
  <div class="abs" style="left:64px;top:320px">${janela(TELA('gerenciar-paginas/passo-01-light.webp'), 1072, 'roteiroonline.com/admin/paginas')}</div>
</div>`);

peca('fotos/f07-secoes-prontas', F, `
<div class="pc escuro grade">
  <div class="abs" style="left:64px;top:56px">${selo('Seções prontas', 'layout-template')}<h2 style="margin-top:18px;font-size:50px">Capa, itinerário, inclusos,<br>preços, vídeo e <span class="dest">muito mais</span></h2></div>
  <div class="abs" style="left:64px;top:320px">${janela(TELA('adicionar-secao/passo-03-light.webp'), 1072, 'roteiroonline.com/admin')}</div>
</div>`);

peca('fotos/f08-precos-e-pacotes', F, `
<div class="pc verde grade">
  <div class="abs" style="left:64px;top:56px">${selo('Preços e pacotes', 'credit-card')}<h2 style="margin-top:18px;font-size:50px">Quarto duplo, triplo, criança:<br><span class="dest">cada preço no seu card</span></h2></div>
  <div class="abs" style="left:64px;top:320px">${janela(TELA('precos-e-pacotes/passo-02-light.webp'), 1072, 'roteiroonline.com/admin')}</div>
</div>`);

peca('fotos/f09-assistente-de-ia', F, `
<div class="pc claro grade">
  <div class="abs" style="left:64px;top:56px">${selo('Assistente de IA', 'sparkles')}<h2 style="margin-top:18px;font-size:50px">Mande texto, áudio ou PDF.<br><span class="dest">A página sai pronta.</span></h2></div>
  <div class="abs" style="left:64px;top:320px">${janela(TELA('assistente-ia/passo-03-light.webp'), 1072, 'roteiroonline.com/admin')}</div>
</div>`);

peca('fotos/f10-leads', F, `
<div class="pc escuro grade">
  <div class="abs" style="left:64px;top:56px">${selo('Módulo Leads', 'magnet')}<h2 style="margin-top:18px;font-size:50px">Funil de vendas com os<br>leads <span class="dest">das suas páginas</span></h2></div>
  <div class="abs" style="left:64px;top:320px">${janela(TELA('oportunidades/passo-01-light.webp'), 1072, 'roteiroonline.com/admin/leads')}</div>
</div>`);

// ===== DESTAQUES =====
peca('destaques/d01-antes-e-depois', F, `
<div class="pc escuro grade">
  <div class="abs" style="left:0;right:0;top:56px;text-align:center"><h2 style="font-size:54px">Saia do textão.<br>Mande <span class="dest">uma página</span>.</h2></div>
  <div class="abs" style="left:64px;top:290px;width:520px;--fs:28px" >
    <div class="cartao" style="background:rgba(229,72,77,.07);border-color:rgba(229,72,77,.3);height:540px;padding:40px">
      <div style="display:flex;gap:12px;align-items:center;font-weight:800;font-size:30px;color:#FF8A8D;margin-bottom:26px">${ico('x-circle')}Antes</div>
      <ul class="lista" style="gap:26px">${['Textão que ninguém lê até o fim', 'PDF pesado que não abre no celular', 'Arte do Canva refeita a cada mudança', 'Cliente compara só o preço'].map(t => `<li><span style="color:#FF8A8D;font-size:26px;line-height:1">×</span><span style="color:rgba(255,255,255,.75)">${t}</span></li>`).join('')}</ul>
    </div></div>
  <div class="abs" style="right:64px;top:290px;width:520px;--fs:28px">
    <div class="cartao" style="background:linear-gradient(180deg,rgba(144,238,143,.14),rgba(5,20,11,.4));border-color:rgba(144,238,143,.45);height:540px;padding:40px">
      <div style="display:flex;gap:12px;align-items:center;font-weight:800;font-size:30px;color:var(--on);margin-bottom:26px">${ico('circle-check')}Com o Roteiro Online</div>
      ${lista(['Página bonita que abre em qualquer celular', 'Um link só, sempre atualizado', 'Botão de WhatsApp com mensagem pronta', 'Cliente enxerga o valor antes do preço'])}
    </div></div>
</div>`);

peca('destaques/d02-como-funciona', F, `
<div class="pc claro grade">
  <div class="abs" style="left:0;right:0;top:60px;text-align:center">${selo('Como funciona', 'route')}<h2 style="margin-top:20px;font-size:54px">Seu roteiro no ar em <span class="dest">3 passos</span></h2></div>
  <div class="abs" style="left:64px;right:64px;top:300px;display:grid;grid-template-columns:repeat(3,1fr);gap:24px">
    ${[['1', 'layout-template', 'Escolha um modelo', 'Comece do zero ou parta de um modelo pronto. Cadastro em 3 minutos.'],
       ['2', 'pencil-ruler', 'Monte o roteiro', 'Troque fotos, textos e valores, ou deixe a IA montar para você.'],
       ['3', 'send', 'Mande o link', 'Cole no WhatsApp, no Instagram e nos anúncios. Um link só.']]
      .map(([n, i, t, p]) => `<div class="cartao" style="height:470px;padding:36px"><div style="display:flex;justify-content:space-between;align-items:flex-start"><div class="ic">${ico(i)}</div><span class="num" style="font-size:72px;opacity:.25">${n}</span></div><h3 style="margin-top:22px;font-size:32px">${t}</h3><p style="margin-top:14px;font-size:23px">${p}</p></div>`).join('')}
  </div>
</div>`);

peca('destaques/d03-para-quem-e', F, `
<div class="pc escuro grade">
  <div class="abs" style="left:0;right:0;top:56px;text-align:center">${selo('Para quem é', 'users-round')}<h2 style="margin-top:18px;font-size:50px">Feito para quem <span class="dest">vende viagem</span></h2></div>
  <div class="abs" style="left:64px;right:64px;top:270px;display:grid;grid-template-columns:repeat(3,1fr);gap:20px">
    ${[['bus', 'Agências de excursão', 'Grupos, bate-volta e saídas confirmadas.'], ['briefcase', 'Agentes e operadoras', 'Pacotes nacionais e internacionais.'], ['map-pinned', 'Receptivos e guias', 'Passeios, transfers e roteiros no destino.'],
       ['hotel', 'Hotéis e pousadas', 'Day use e roteiros para hóspedes.'], ['wine', 'Experiências', 'Gastronomia, enoturismo, aventura e cultura.'], ['users-round', 'Times de vendas', 'A equipe toda no mesmo padrão.']]
      .map(([i, t, p]) => `<div class="cartao" style="padding:26px;height:280px"><div class="ic">${ico(i)}</div><h3 style="font-size:25px">${t}</h3><p style="font-size:19px">${p}</p></div>`).join('')}
  </div>
</div>`);

peca('destaques/d04-tudo-incluso', F, `
<div class="pc verde grade">
  <div class="abs" style="left:64px;top:60px;width:560px">${selo('Plano único', 'badge-check')}<h2 style="margin-top:20px;font-size:54px">Tudo incluso, <span class="dest">sem recurso bloqueado</span></h2>
    <p class="sub" style="margin-top:20px">Você usa tudo desde o primeiro dia.</p>
    <div style="margin-top:40px;display:flex;gap:12px;flex-wrap:wrap"><span class="chip">${ico('shield-check')}7 dias de garantia</span><span class="chip">${ico('circle-check')}Sem fidelidade</span></div>
  </div>
  <div class="abs" style="right:64px;top:70px;width:470px"><div class="cartao" style="background:rgba(6,40,28,.55);border-color:rgba(144,238,143,.35);padding:36px">
    <ul class="lista" style="gap:17px">${['Roteiros ilimitados no ar', 'Duplicar páginas em um clique', 'Editor visual com seções prontas', 'Pixels Meta e Google', 'Assistente de IA', 'Módulo Leads e funil de vendas', 'Notificações inteligentes', 'Criativos para anúncios e stories', 'Domínio próprio da agência', 'Equipe com até 5 usuários'].map(t => `<li style="font-size:22px">${ico('circle-check')}<span>${t}</span></li>`).join('')}</ul>
  </div></div>
</div>`);

peca('destaques/d05-numeros', F, `
<div class="pc escuro grade">
  <div class="abs" style="left:64px;top:60px">${logo('horizontal-fundo-escuro', 44)}</div>
  <div class="abs" style="left:64px;top:170px;width:1072px"><h2 style="font-size:56px">Agências de todo o Brasil já<br>vendem com <span class="dest">páginas de roteiro</span></h2></div>
  <div class="abs" style="left:64px;right:64px;top:430px;display:grid;grid-template-columns:repeat(4,1fr);gap:20px">
    ${[['+200', 'Agências ativas'], ['+1.000', 'Páginas criadas'], ['3 min', 'Para se cadastrar'], ['7 dias', 'Garantia total']].map(([n, l]) => `<div class="cartao" style="padding:34px 26px;text-align:left"><div class="num">${n}</div><p style="margin-top:14px;font-size:21px;font-weight:600">${l}</p></div>`).join('')}
  </div>
  <div class="rodape" style="left:64px;bottom:64px">${ico('globe')}roteiroonline.com</div>
</div>`);

peca('destaques/d06-whatsapp', F, `
<div class="pc claro grade">
  <div class="abs" style="left:64px;top:70px;width:560px">${selo('Botão de WhatsApp', 'message-circle')}<h2 style="margin-top:20px;font-size:52px">O lead chega no seu WhatsApp <span class="dest">já sabendo o roteiro</span></h2>
    <p class="sub" style="margin-top:22px">Botão em qualquer seção, com mensagem pronta. Menos explicação, mais reserva.</p>
    <div style="margin-top:34px">${lista(['Mensagem com o nome da viagem', 'Cliques medidos no painel', 'Funciona em qualquer celular'])}</div></div>
  <div class="abs" style="left:700px;top:90px;transform:rotate(-3deg)">${celular(CEL('beto-0'), 330)}</div>
</div>`);

// ---------- render ----------
(async () => {
  const pedidos = process.argv.slice(2);
  const lista = PECAS.filter(p => !pedidos.length || pedidos.some(x => path.basename(p.arquivo).startsWith(x)));
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ deviceScaleFactor: 1 });
  for (const p of lista) {
    const page = await ctx.newPage();
    await page.setViewportSize({ width: p.w, height: p.h });
    const html = path.join(AQUI, '.tmp.html');
    fs.writeFileSync(html, pagina(p.w, p.h, p.corpo));
    await page.goto('file://' + html, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
    const saida = path.join(AQUI, p.arquivo + '.jpg');
    fs.mkdirSync(path.dirname(saida), { recursive: true });
    await page.screenshot({ path: saida, type: 'jpeg', quality: 92 });
    console.log('✓', p.arquivo, `${p.w}x${p.h}`);
    await page.close();
  }
  fs.rmSync(path.join(AQUI, '.tmp.html'), { force: true });
  await browser.close();
})();
