// Gera as imagens do Perfil da Empresa no Google da Viaje On (catálogo, fotos e destaques).
// Tudo é feito com telas REAIS do Sistema Viaje On, recortadas para real/ a partir do
// repositório do sistema (oi-charm-glow): public/apresentacao/telas e public/help/shots,
// com a agência fictícia "Serra Turismo". O logo é o oficial (public/brand).
// A capa tem gerador próprio: gerar-capa.cjs.
//
//   node gerar.cjs            todas as peças
//   node gerar.cjs p01 f03    só as pedidas (pelo prefixo do nome)
//
// Saída: produtos/, fotos/ e destaques/ ao lado deste arquivo, em JPG.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const AQUI = __dirname;
const REAL = n => 'file://' + path.join(AQUI, 'real', n);
const TELA = n => REAL(n + '.jpg');
const MARCA = n => 'file://' + path.join(AQUI, 'marca', n + '.png');

const ico = (nome, cls = '') => `<i data-lucide="${nome}" class="${cls}"></i>`;
const laptop = (src, w) => `
  <div class="laptop" style="width:${w}px">
    <div class="lp-screen"><img src="${src}"></div>
    <div class="lp-base"></div>
  </div>`;
const janela = (src, w, url = 'app.viajeon.com') => `
  <div class="janela" style="width:${w}px">
    <div class="jn-bar"><span></span><span></span><span></span><div class="jn-url">${ico('lock')}${url}</div></div>
    <img src="${src}">
  </div>`;
const flut = (arq, w) => `<div class="flut" style="width:${w}px"><img src="${REAL(arq)}"></div>`;
const papel = (arq, w) => `<div class="papel" style="width:${w}px"><img src="${REAL(arq)}"></div>`;
const selo = (txt, i = 'sparkles') => `<span class="selo">${ico(i)}${txt}</span>`;
const lista = itens => `<ul class="lista">${itens.map(t => `<li>${ico('circle-check')}<span>${t}</span></li>`).join('')}</ul>`;
// Logo oficial (public/brand/viajeon-logo-dark.png). Em fundo claro, vai numa pílula escura.
const logo = (h = 46) => `<span class="vlogo"><img src="${REAL('viajeon-logo-dark.png')}" style="height:${h}px"></span>`;

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
h1,h2,h3{font-family:Inter,sans-serif;letter-spacing:-.035em;line-height:1.06;font-weight:800}
h1{font-size:76px} h2{font-size:58px} h3{font-size:30px;font-weight:700}
.dest{color:var(--on);font-family:Fraunces,serif;font-style:italic;font-weight:600;letter-spacing:-.02em} .claro .dest{color:var(--viaje)}
.vlogo{display:inline-flex;align-items:center;gap:.32em}.claro .vlogo{background:#0A110E;padding:.32em .6em;border-radius:.45em;box-sizing:content-box}.vlogo img{display:block}
.num{font-family:Fraunces,serif!important;font-style:italic;font-weight:600!important}
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
.janela{border-radius:18px;overflow:hidden;background:#0B100D;box-shadow:0 0 0 1px rgba(0,0,0,.08),0 40px 90px -25px rgba(0,0,0,.55)}
.janela .jn-bar{height:46px;display:flex;align-items:center;gap:9px;padding:0 18px;background:#141B17;border-bottom:1px solid #222B26}
.janela .jn-bar>span{width:13px;height:13px;border-radius:50%;background:#E5484D}.janela .jn-bar>span:nth-child(2){background:#F5B83D}.janela .jn-bar>span:nth-child(3){background:#3CC66B}
.janela .jn-url{margin-left:18px;flex:1;max-width:520px;height:28px;border-radius:999px;background:#0B100D;border:1px solid #26302B;display:flex;align-items:center;gap:8px;padding:0 14px;font-size:15px;color:#9FB0A7;font-weight:500}
.janela .jn-url svg{width:14px;height:14px;color:var(--on)}
.flut{border-radius:20px;overflow:hidden;box-shadow:0 0 0 1px rgba(144,238,143,.22),0 40px 80px -20px rgba(0,0,0,.8)}.flut img{display:block;width:100%}
.papel{background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 40px 80px -20px rgba(0,0,0,.7)}.papel img{display:block;width:100%}
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
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fraunces:ital,opsz,wght@1,9..144,500;1,9..144,600&display=block" rel="stylesheet">
<script src="https://unpkg.com/lucide@0.460.0/dist/umd/lucide.min.js"></script>
<style>${CSS} :root{--w:${w}px;--h:${h}px}</style></head><body>${corpo}
<script>lucide.createIcons({attrs:{'stroke-width':2.2}});</script></body></html>`;

// ---------- peças ----------
const Q = [1200, 1200];   // produto (quadrado)
const F = [1200, 900];    // foto/destaque 4:3
const PECAS = [];
const peca = (arquivo, [w, h], corpo) => PECAS.push({ arquivo, w, h, corpo });

// Produto com uma tela real embaixo do título e, opcionalmente, um recorte flutuando.
const prodTela = (arquivo, tema, [seloTxt, seloIco], titulo, sub, tela, url, extra = '') => peca(arquivo, Q, `
<div class="pc ${tema} grade">
  <div class="abs" style="left:72px;top:76px;width:1056px">
    ${selo(seloTxt, seloIco)}
    <h2 style="margin-top:24px">${titulo}</h2>
    <p class="sub" style="margin-top:18px;width:960px">${sub}</p>
  </div>
  <div class="abs" style="left:72px;top:470px">${janela(TELA(tela), 1056, url)}</div>
  ${extra}
</div>`);

const fotoTela = (arquivo, tema, [seloTxt, seloIco], titulo, tela, url, extra = '') => peca(arquivo, F, `
<div class="pc ${tema} grade">
  <div class="abs" style="left:64px;top:56px">${selo(seloTxt, seloIco)}<h2 style="margin-top:18px;font-size:50px">${titulo}</h2></div>
  <div class="abs" style="left:64px;top:310px">${janela(TELA(tela), 1072, url)}</div>
  ${extra}
</div>`);

const plano = (arquivo, tema, nome, publico, itens, destaque = '') => peca(arquivo, Q, `
<div class="pc ${tema} grade">
  <div class="abs" style="left:72px;top:72px">${logo(48)}</div>
  <div class="abs" style="left:72px;top:200px;width:1056px">
    ${destaque ? selo(destaque, 'star') : selo('Plano do Sistema Viaje On', 'badge-check')}
    <h1 style="margin-top:24px;font-size:96px">Plano <span class="dest">${nome}</span></h1>
    <p class="sub" style="margin-top:16px">${publico}</p>
  </div>
  <div class="abs" style="left:72px;top:540px;width:1056px"><div class="cartao" style="padding:44px;--fs:27px">${lista(itens)}</div></div>
  <div class="abs" style="left:72px;bottom:64px;display:flex;gap:12px"><span class="chip">${ico('shield-check')}7 dias de garantia</span><span class="chip">${ico('zap')}Acesso imediato</span><span class="chip">${ico('circle-off')}Sem taxa de adesão</span></div>
</div>`);

// ===== PRODUTOS (catálogo) =====
peca('produtos/p01-sistema-viaje-on', Q, `
<div class="pc escuro grade">
  <div class="abs" style="left:72px;top:72px">${logo(56)}</div>
  <div class="abs" style="left:72px;top:190px;width:1056px">
    ${selo('Backoffice completo para agências', 'layout-dashboard')}
    <h1 style="margin-top:26px;font-size:80px">A operação da sua agência <span class="dest">em um só lugar</span></h1>
    <p class="sub" style="margin-top:22px;width:940px">Vendas online, passageiros, poltronas, contratos, rooming list e financeiro no mesmo sistema.</p>
  </div>
  <div class="abs" style="left:120px;top:640px">${laptop(TELA('painel'), 960)}</div>
  <div class="abs" style="left:830px;top:590px">${flut('kpi-valor-vendido.png', 300)}</div>
</div>`);

prodTela('produtos/p02-venda-online-por-link', 'escuro', ['Vendas online', 'shopping-cart'],
  'O cliente <span class="dest">compra sozinho</span> pelo link',
  'Copie o link do checkout e mande no WhatsApp, Instagram ou anúncio. O passageiro preenche os dados, escolhe a poltrona e paga.',
  'op-checkout', 'app.viajeon.com/operacoes');

prodTela('produtos/p03-mapa-de-poltronas', 'verde', ['Mapa de poltronas', 'armchair'],
  'Cada venda ocupa a poltrona, <span class="dest">sem controle manual</span>',
  'O passageiro escolhe o assento no checkout e você vê ocupadas, livres e pendentes de cada ônibus.',
  'assento-op', 'app.viajeon.com/operacoes');

prodTela('produtos/p04-contrato-automatico', 'escuro', ['Contrato automático', 'file-signature'],
  'Contrato gerado e <span class="dest">assinado online</span>',
  'Escolha o modelo uma vez por operação. Cada venda gera o contrato com os dados do passageiro, para assinar pelo celular.',
  'ctr-op', 'app.viajeon.com/operacoes');

prodTela('produtos/p05-financeiro-e-lucro-por-viagem', 'verde', ['Custos e financeiro', 'chart-line'],
  'Saiba o lucro de cada viagem <span class="dest">antes do embarque</span>',
  'Recebimentos, pagamentos e saldo da operação, custos por fornecedor e o caixa da agência.',
  'op-custos', 'app.viajeon.com/operacoes',
  `<div class="abs" style="left:150px;top:900px">${flut('kpis-financeiro-op.png', 900)}</div>`);

prodTela('produtos/p06-pdv-venda-presencial', 'escuro', ['PDV', 'store'],
  'Venda no balcão <span class="dest">em segundos</span>',
  'Cliente, operação e pacotes no mesmo pedido, com desconto, vendedor e mais de uma forma de pagamento.',
  'pdv-pedido', 'app.viajeon.com/pdv');

prodTela('produtos/p07-embarque-e-rooming-list', 'verde', ['Embarque e rooming list', 'clipboard-list'],
  'Lista de embarque e rooming list <span class="dest">prontas</span>',
  'Passageiros por ponto de embarque, quartos montados e relatórios em PDF para o guia e o hotel.',
  'op-hospedagem', 'app.viajeon.com/operacoes',
  `<div class="abs" style="right:40px;top:780px;transform:rotate(3deg)">${papel('pdf-rooming.jpg', 500)}</div>`);

prodTela('produtos/p08-whatsapp-e-email-automaticos', 'escuro', ['WhatsApp e e-mail', 'message-circle'],
  'Mensagens automáticas <span class="dest">para o passageiro</span>',
  'Confirmação de reserva, lembrete de parcela e instruções de embarque, com modelos editáveis.',
  'wa-templates', 'app.viajeon.com/whatsapp');

plano('produtos/p09-plano-basico', 'claro', 'Básico', 'Para começar a vender online e sair da planilha.',
  ['Vendas online por link', '1 usuário', 'Custos, financeiro e PDV', 'Veículos, assentos e rooming list', 'Contratos automáticos']);
plano('produtos/p10-plano-intermediario', 'verde', 'Intermediário', 'Para a agência com equipe e venda todo dia.',
  ['Tudo do plano Básico', '5 usuários', 'Área do cliente e área do guia', 'WhatsApp, afiliados e domínio próprio', 'Taxa menor nos pagamentos com cartão'], 'Mais popular');
plano('produtos/p11-plano-avancado', 'escuro', 'Avançado', 'Para a operação que quer escala, sem limite de equipe.',
  ['Tudo do plano Intermediário', 'Usuários ilimitados', 'Sem taxa nas vendas online', 'Asaas, Mercado Pago e InfinitePay', 'Todas as integrações de pagamento']);

peca('produtos/p12-paav-aceleracao-de-agencias', Q, `
<div class="pc verde grade">
  <div class="abs" style="left:72px;top:72px">${logo(48)}</div>
  <div class="abs" style="left:72px;top:200px;width:1056px">
    ${selo('PAAV', 'rocket')}
    <h1 style="margin-top:24px;font-size:74px">Plano de Aceleração para <span class="dest">Agência de Viagens</span></h1>
    <p class="sub" style="margin-top:22px;width:960px">Mentoria para o dono de agência que quer parar de competir no preço e crescer com processo, posicionamento e margem.</p>
  </div>
  <div class="abs" style="left:72px;top:690px;width:1056px;display:grid;grid-template-columns:repeat(3,1fr);gap:20px">
    ${[['tag', 'Venda pelo valor', 'Saia do balcão do preço.'], ['workflow', 'Processo comercial', 'Do orçamento ao fechamento.'], ['trending-up', 'Gestão e margem', 'Decisões de dono, com números.']]
      .map(([i, t, p]) => `<div class="cartao" style="background:rgba(6,40,28,.55);padding:28px"><div class="ic">${ico(i)}</div><h3 style="font-size:26px">${t}</h3><p style="font-size:20px">${p}</p></div>`).join('')}
  </div>
  <div class="abs" style="left:72px;bottom:64px"><span class="chip">${ico('calendar-check')}Conversa gratuita de 30 minutos</span></div>
</div>`);

// ===== FOTOS =====
peca('fotos/f02-logo', [720, 720], `
<div class="pc" style="background:#0A110E;display:grid;place-items:center"><img src="${MARCA('viajeon-aviao')}" style="width:380px;margin:0 30px 20px 0"></div>`);

peca('fotos/f03-logo-horizontal', F, `
<div class="pc escuro grade" style="display:grid;place-items:center"><div style="text-align:center">${logo(150)}<p class="sub" style="margin-top:40px;font-size:30px">Sistema e educação para agências de viagens</p></div></div>`);

fotoTela('fotos/f04-painel', 'escuro', ['Dashboard', 'layout-dashboard'],
  'Vendas, ocupação e próximo<br>embarque <span class="dest">logo ao entrar</span>', 'painel', 'app.viajeon.com');
fotoTela('fotos/f05-operacao', 'verde', ['Operações', 'bus'],
  'Cada viagem com ocupação,<br>vendas e saldo <span class="dest">numa tela só</span>', 'op-geral', 'app.viajeon.com/operacoes');
fotoTela('fotos/f06-vendas-da-operacao', 'escuro', ['Vendas', 'shopping-cart'],
  'Quem comprou, quanto pagou<br>e <span class="dest">quem ainda deve</span>', 'op-vendas', 'app.viajeon.com/operacoes');
fotoTela('fotos/f07-editor-de-veiculo', 'claro', ['Veículos', 'bus-front'],
  'Monte o mapa do ônibus<br><span class="dest">do jeito que ele é</span>', 'veiculo-editor', 'app.viajeon.com/veiculos');
fotoTela('fotos/f08-financeiro', 'escuro', ['Financeiro', 'wallet'],
  'Entradas, saídas e previsão<br><span class="dest">do caixa da agência</span>', 'financeiro', 'app.viajeon.com/financeiro');
fotoTela('fotos/f09-pdv-pagamento', 'verde', ['PDV', 'credit-card'],
  'Pix, cartão e parcelamento<br><span class="dest">no mesmo pedido</span>', 'pdv-pagamento', 'app.viajeon.com/pdv');
fotoTela('fotos/f10-rooming-list', 'escuro', ['Hospedagem', 'bed-double'],
  'Rooming list montada<br><span class="dest">sem planilha</span>', 'op-hospedagem', 'app.viajeon.com/operacoes');
fotoTela('fotos/f11-insights', 'claro', ['Insights', 'chart-column'],
  'Destinos, clientes e temporadas<br>que <span class="dest">mais vendem</span>', 'insights', 'app.viajeon.com/insights');

peca('fotos/f12-relatorios-em-pdf', F, `
<div class="pc verde grade">
  <div class="abs" style="left:64px;top:56px">${selo('Relatórios', 'file-text')}<h2 style="margin-top:18px;font-size:50px">Lista de embarque e rooming list<br><span class="dest">em PDF, num clique</span></h2></div>
  <div class="abs" style="left:60px;top:320px;transform:rotate(-3deg)">${papel('pdf-embarque.jpg', 620)}</div>
  <div class="abs" style="left:540px;top:380px;transform:rotate(3deg)">${papel('pdf-rooming.jpg', 620)}</div>
</div>`);

// ===== DESTAQUES =====
const bolha = (txt, hora, eu = false) => `<div style="align-self:${eu ? 'flex-end' : 'flex-start'};max-width:84%;background:${eu ? '#D9FDD3' : '#fff'};color:#111;border-radius:14px;padding:12px 16px;font-size:19px;line-height:1.35;box-shadow:0 2px 4px rgba(0,0,0,.08)">${txt}<div style="text-align:right;font-size:13px;color:#667;margin-top:4px">${hora}</div></div>`;
peca('destaques/d01-whatsapp-x-sistema', F, `
<div class="pc claro grade">
  <div class="abs" style="left:64px;top:56px;width:1072px"><h2 style="font-size:52px">O problema não são as vendas.<br>É <span class="dest">não saber</span> no que elas viraram.</h2></div>
  <div class="abs" style="left:64px;top:290px;width:470px;height:500px;border-radius:28px;background:#E9DFC9;padding:28px;display:flex;flex-direction:column;gap:12px">
    <div style="font-weight:700;font-size:20px;color:#6b5f45;margin-bottom:4px">Como é hoje, no WhatsApp</div>
    ${bolha('Oi! Vi a excursão pra Gramado, ainda tem vaga?', '09:14')}
    ${bolha('Tem sim! Deixa eu te passar os dados pra reservar', '09:22', true)}
    ${bolha('Oi, só pra avisar: acabei fechando com outra agência, foi mais rápido.', '3 dias depois')}
  </div>
  <div class="abs" style="left:570px;top:290px">${flut('card-operacao.png', 570)}</div>
  <div class="abs" style="left:570px;top:420px;width:570px;display:grid;gap:14px;--fs:21px">${lista(['Cliente compra sozinho pelo link', 'Escolhe a poltrona e paga no checkout', 'Contrato gerado na hora', 'Você vê quem pagou e quem deve'])}</div>
</div>`);

peca('destaques/d02-como-funciona', F, `
<div class="pc escuro grade">
  <div class="abs" style="left:64px;top:56px">${selo('Como funciona', 'route')}<h2 style="margin-top:18px;font-size:50px">Da venda ao contrato assinado,<br><span class="dest">sem sair do sistema</span></h2></div>
  <div class="abs" style="left:64px;right:64px;top:330px;display:grid;grid-template-columns:repeat(4,1fr);gap:16px">
    ${[['Crie a viagem', 'Valores, vagas, veículo e contrato.'], ['Gere o link', 'WhatsApp, Instagram ou anúncio.'], ['Cliente acessa', 'Checkout com a marca da agência.'], ['Preenche os dados', 'Documentos e contatos.'],
       ['Escolhe a poltrona', 'Sozinho, no mapa do ônibus.'], ['Paga online', 'Já entra no financeiro.'], ['Contrato assinado', 'Gerado e assinado na hora.']]
      .map(([t, p], k) => `<div class="cartao" style="padding:22px 22px 24px"><span class="num" style="font-size:44px">0${k + 1}</span><h3 style="font-size:23px;margin-top:10px">${t}</h3><p style="font-size:17px">${p}</p></div>`).join('')}
    <div class="cartao" style="padding:22px;background:var(--on);border-color:var(--on);color:var(--noite);display:flex;flex-direction:column;justify-content:center"><h3 style="font-size:26px;color:var(--noite)">Você só acompanha.</h3><p style="font-size:17px;color:#14281F;margin-top:6px">Tudo registrado na operação.</p></div>
  </div>
</div>`);

peca('destaques/d03-para-quem-e', F, `
<div class="pc claro grade">
  <div class="abs" style="left:0;right:0;top:56px;text-align:center">${selo('Feito pra quem vive disso', 'users-round')}<h2 style="margin-top:18px;font-size:50px">Uma operação, <span class="dest">vários jeitos</span> de vender viagem</h2></div>
  <div class="abs" style="left:64px;right:64px;top:270px;display:grid;grid-template-columns:repeat(2,1fr);gap:20px">
    ${[['bus', 'Excursões', 'Ônibus, assentos, passageiros, contratos e rooming list.'], ['briefcase', 'Operadoras de turismo', 'Pacotes, fornecedores, hotéis e custos por operação.'],
       ['plane', 'Agências de viagem', 'Pacotes, produtos e serviços com checkout no seu domínio.'], ['map-pinned', 'Turismo receptivo', 'Hospedagens, transfers, passeios e serviços.']]
      .map(([i, t, p]) => `<div class="cartao" style="padding:30px;height:270px"><div class="ic">${ico(i)}</div><h3 style="font-size:29px">${t}</h3><p style="font-size:21px;margin-top:6px">${p}</p></div>`).join('')}
  </div>
</div>`);

peca('destaques/d04-tempo-e-dinheiro', F, `
<div class="pc escuro grade">
  <div class="abs" style="left:64px;top:60px;width:1072px">${selo('Tempo é dinheiro', 'timer')}<h2 style="margin-top:20px;font-size:54px">Cada tarefa manual rouba minutos que <span class="dest">deveriam estar vendendo</span></h2></div>
  <div class="abs" style="left:64px;right:64px;top:400px"><div class="cartao" style="padding:46px">
    <div style="font-size:24px;font-weight:700;margin-bottom:34px">Gerar um contrato</div>
    <div style="display:grid;grid-template-columns:240px 1fr 150px;align-items:center;gap:24px;font-size:22px">
      <span style="color:rgba(255,255,255,.7)">WhatsApp e planilha</span><div style="height:18px;border-radius:9px;background:rgba(255,255,255,.08)"><div style="width:78%;height:100%;border-radius:9px;background:#E5484D"></div></div><b style="font-size:40px;color:#FF7A7E;text-align:right">15 min</b>
      <span style="color:rgba(255,255,255,.7)">Sistema Viaje On</span><div style="height:18px;border-radius:9px;background:rgba(255,255,255,.08)"><div style="width:4%;height:100%;border-radius:9px;background:var(--on)"></div></div><b style="font-size:40px;color:var(--on);text-align:right">20 seg</b>
    </div>
  </div>
  <p style="margin-top:20px;font-size:16px;color:rgba(255,255,255,.5)">Tempos médios estimados, relatados por agências que usavam planilha e WhatsApp antes de migrar.</p></div>
</div>`);

peca('destaques/d05-lucro-em-tempo-real', F, `
<div class="pc verde grade">
  <div class="abs" style="left:64px;top:56px;width:1072px">${selo('Visibilidade financeira', 'eye')}<h2 style="margin-top:18px;font-size:52px">Pare de descobrir o lucro<br><span class="dest">depois que a viagem acaba</span></h2></div>
  <div class="abs" style="left:64px;top:380px">${flut('card-operacao.png', 1072)}</div>
  <div class="abs" style="left:64px;top:620px">${flut('kpis-financeiro-op.png', 1072)}</div>
</div>`);

peca('destaques/d06-garantia-e-onboarding', F, `
<div class="pc escuro grade">
  <div class="abs" style="left:64px;top:60px">${logo(46)}</div>
  <div class="abs" style="left:64px;top:160px;width:1072px"><h2 style="font-size:56px">Comece hoje, <span class="dest">sem risco</span></h2><p class="sub" style="margin-top:14px">Sem taxa de adesão e sem instalação. 100% online, no computador ou no celular.</p></div>
  <div class="abs" style="left:64px;right:64px;top:400px;display:grid;grid-template-columns:repeat(2,1fr);gap:20px">
    ${[['shield-check', '7 dias de garantia', 'Não gostou? Reembolso integral.'], ['zap', 'Acesso imediato', 'Pagamento aprovado, login liberado.'], ['handshake', 'Onboarding guiado', 'A equipe configura junto com você.'], ['lock', 'Pagamento seguro', 'Pix ou cartão, em ambiente criptografado.']]
      .map(([i, t, p]) => `<div class="cartao" style="padding:26px;display:flex;gap:20px;align-items:center"><div class="ic" style="margin:0;flex:none">${ico(i)}</div><div><h3 style="font-size:25px">${t}</h3><p style="font-size:19px;margin-top:4px">${p}</p></div></div>`).join('')}
  </div>
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
