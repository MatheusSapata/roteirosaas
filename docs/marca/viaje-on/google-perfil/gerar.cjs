// Gera as imagens do Perfil da Empresa no Google da Viaje On (catálogo, fotos, capa e destaques).
// As telas (telas/eNN.jpg) são a demonstração do Sistema Viaje On da página viajeon.com/sistema
// (agência fictícia "Serra Turismo"), capturadas sem a barra de progresso.
//
//   node gerar.cjs            todas as peças
//   node gerar.cjs p01 f03    só as pedidas (pelo prefixo do nome)
//
// Saída: produtos/, fotos/ e destaques/ ao lado deste arquivo, em JPG.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const AQUI = __dirname;
const TELA = n => 'file://' + path.join(AQUI, 'telas', n + '.jpg');
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
const selo = (txt, i = 'sparkles') => `<span class="selo">${ico(i)}${txt}</span>`;
const lista = itens => `<ul class="lista">${itens.map(t => `<li>${ico('circle-check')}<span>${t}</span></li>`).join('')}</ul>`;
// Logo: avião + "Viajeon" (versão para fundo escuro). Em fundo claro, vai dentro de uma pílula escura.
const logo = (h = 46) => `<span class="vlogo" style="height:${h}px"><img src="${MARCA('viajeon-aviao')}" style="height:${Math.round(h * .86)}px"><img src="${MARCA('viajeon-texto-escuro')}" style="height:${h}px"></span>`;
const rodape = (txt = 'viajeon.com/sistema') => `<div class="rodape">${ico('globe')}${txt}</div>`;

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
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fraunces:ital,opsz,wght@1,9..144,500;1,9..144,600&display=block" rel="stylesheet">
<script src="https://unpkg.com/lucide@0.460.0/dist/umd/lucide.min.js"></script>
<style>${CSS} :root{--w:${w}px;--h:${h}px}</style></head><body>${corpo}
<script>lucide.createIcons({attrs:{'stroke-width':2.2}});</script></body></html>`;

// ---------- peças ----------
const Q = [1200, 1200];   // produto (quadrado)
const F = [1200, 900];    // foto/destaque 4:3
const PECAS = [];
const peca = (arquivo, [w, h], corpo) => PECAS.push({ arquivo, w, h, corpo });

// Produto com uma tela do sistema embaixo do título.
const prodTela = (arquivo, tema, [seloTxt, seloIco], titulo, sub, tela, url, extra = '') => peca(arquivo, Q, `
<div class="pc ${tema} grade">
  <div class="abs" style="left:72px;top:76px;width:1056px">
    ${selo(seloTxt, seloIco)}
    <h2 style="margin-top:24px">${titulo}</h2>
    <p class="sub" style="margin-top:18px;width:960px">${sub}</p>
  </div>
  <div class="abs" style="left:72px;top:480px">${janela(TELA(tela), 1056, url)}</div>
  ${extra}
</div>`);

// Foto 4:3 com uma tela do sistema.
const fotoTela = (arquivo, tema, [seloTxt, seloIco], titulo, tela, url) => peca(arquivo, F, `
<div class="pc ${tema} grade">
  <div class="abs" style="left:64px;top:56px">${selo(seloTxt, seloIco)}<h2 style="margin-top:18px;font-size:50px">${titulo}</h2></div>
  <div class="abs" style="left:64px;top:310px">${janela(TELA(tela), 1072, url)}</div>
</div>`);

// Plano: só texto (os valores mudam nas promoções, por isso não vão na imagem).
const plano = (arquivo, tema, nome, publico, itens, destaque = '') => peca(arquivo, Q, `
<div class="pc ${tema} grade">
  <div class="abs" style="left:72px;top:72px">${logo(48)}</div>
  <div class="abs" style="left:72px;top:200px;width:1056px">
    ${destaque ? selo(destaque, 'star') : selo('Plano do Sistema Viaje On', 'badge-check')}
    <h1 style="margin-top:24px;font-size:96px">Plano <span class="dest">${nome}</span></h1>
    <p class="sub" style="margin-top:16px">${publico}</p>
  </div>
  <div class="abs" style="left:72px;top:560px;width:1056px"><div class="cartao" style="padding:44px;--fs:27px">${lista(itens)}</div></div>
  <div class="abs" style="left:72px;bottom:64px;display:flex;gap:12px"><span class="chip">${ico('shield-check')}7 dias de garantia</span><span class="chip">${ico('zap')}Acesso imediato</span><span class="chip">${ico('circle-off')}Sem taxa de adesão</span></div>
</div>`);

// ===== PRODUTOS (catálogo) =====
peca('produtos/p01-sistema-viaje-on', Q, `
<div class="pc escuro grade">
  <div class="abs" style="left:72px;top:72px">${logo(54)}</div>
  <div class="abs" style="left:72px;top:190px;width:1056px">
    ${selo('Backoffice completo para agências', 'layout-dashboard')}
    <h1 style="margin-top:26px;font-size:80px">A operação da sua agência <span class="dest">em um só lugar</span></h1>
    <p class="sub" style="margin-top:22px;width:940px">Vendas online, passageiros, poltronas, contratos, rooming list e financeiro no mesmo sistema.</p>
  </div>
  <div class="abs" style="left:150px;top:640px">${laptop(TELA('e01'), 900)}</div>
</div>`);

prodTela('produtos/p02-venda-online-por-link', 'claro', ['Vendas online', 'shopping-cart'],
  'O cliente <span class="dest">compra sozinho</span> pelo link',
  'Mande o link no WhatsApp, Instagram ou anúncio. O passageiro preenche os dados, escolhe a poltrona e paga.',
  'e03', 'app.viajeon.com/vendas',
  `<div class="abs" style="right:52px;top:430px"><span class="chip escuro" style="font-size:22px">${ico('link')}<span>checkout.<b style="color:var(--on)">suaagencia</b>.com.br</span></span></div>`);

prodTela('produtos/p03-mapa-de-poltronas', 'escuro', ['Mapa de poltronas', 'armchair'],
  'Cada venda ocupa a poltrona, <span class="dest">sem controle manual</span>',
  'O passageiro escolhe o assento no checkout e você vê ocupadas, livres e pendentes em tempo real.',
  'e07', 'app.viajeon.com/operacoes');

prodTela('produtos/p04-contrato-automatico', 'verde', ['Contrato automático', 'file-signature'],
  'Contrato gerado e <span class="dest">assinado online</span>',
  'Sai com os dados da viagem e do passageiro e é assinado pelo celular, com data, hora e IP. Sem editar um por um.',
  'e06', 'app.viajeon.com/contratos');

prodTela('produtos/p05-financeiro-e-lucro-por-viagem', 'escuro', ['Custos e financeiro', 'chart-line'],
  'Saiba o lucro de cada viagem <span class="dest">antes do embarque</span>',
  'Custos por categoria e fornecedor, parcelas dos passageiros, contas a pagar e fluxo de caixa.',
  'e08', 'app.viajeon.com/financeiro');

prodTela('produtos/p06-pdv-venda-presencial', 'claro', ['PDV', 'store'],
  'Venda no balcão <span class="dest">em segundos</span>',
  'Pacotes e opcionais no pedido, cadastro rápido do passageiro e mais de uma forma de pagamento.',
  'e04', 'app.viajeon.com/pdv');

prodTela('produtos/p07-check-in-com-qr-code', 'verde', ['Área do guia', 'qr-code'],
  'Embarque com <span class="dest">QR code</span> no celular do guia',
  'O guia confere cada passageiro no ponto de embarque, com a poltrona de cada um na tela.',
  'e11', 'app.viajeon.com/check-in');

prodTela('produtos/p08-whatsapp-e-email-automaticos', 'escuro', ['E-mail e WhatsApp', 'message-circle'],
  'Mensagens automáticas <span class="dest">para o passageiro</span>',
  'Reserva confirmada, contrato pendente, lembrete de parcela e instruções de embarque, com modelos editáveis.',
  'e10', 'app.viajeon.com/notificacoes');

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

// ===== FOTOS (capa, logo e telas) =====
peca('fotos/f01-capa', [1920, 1080], `
<div class="pc escuro grade">
  <div class="abs" style="left:110px;top:110px">${logo(70)}</div>
  <div class="abs" style="left:110px;top:270px;width:800px">
    <h1 style="font-size:84px">Você sabe se a próxima excursão <span class="dest">vai dar lucro?</span></h1>
    <p class="sub" style="margin-top:28px;font-size:29px">Vendas, contratos, poltronas, rooming list e financeiro no mesmo sistema.</p>
    <div style="margin-top:40px;display:flex;gap:14px;flex-wrap:wrap">${selo('Vendas online', 'shopping-cart')}${selo('Contrato automático', 'file-signature')}${selo('7 dias de garantia', 'shield-check')}</div>
  </div>
  <div class="abs" style="left:940px;top:270px">${laptop(TELA('e01'), 900)}</div>
  <div class="rodape" style="left:110px;bottom:80px;font-size:26px">${ico('globe')}viajeon.com</div>
</div>`);

peca('fotos/f02-logo', [720, 720], `
<div class="pc" style="background:#0A110E;display:grid;place-items:center"><img src="${MARCA('viajeon-aviao')}" style="width:380px;margin:0 30px 20px 0"></div>`);

peca('fotos/f03-logo-horizontal', [1200, 900], `
<div class="pc escuro grade" style="display:grid;place-items:center"><div style="text-align:center">${logo(150)}<p class="sub" style="margin-top:40px;font-size:30px">Sistema e educação para agências de viagens</p></div></div>`);

fotoTela('fotos/f04-painel', 'escuro', ['Dashboard', 'layout-dashboard'],
  'Vendas, ocupação e próximo<br>embarque <span class="dest">logo ao entrar</span>', 'e01', 'app.viajeon.com');
fotoTela('fotos/f05-monte-a-operacao', 'claro', ['Operações', 'bus'],
  'Embarques, veículo, hotel, pacotes<br>e contrato <span class="dest">numa tela só</span>', 'e02', 'app.viajeon.com/operacoes');
fotoTela('fotos/f06-checkout-do-passageiro', 'verde', ['Checkout', 'smartphone'],
  'Dados, poltrona e pagamento<br><span class="dest">pelo celular</span>', 'e05', 'checkout.suaagencia.com.br');
fotoTela('fotos/f07-mapa-de-poltronas', 'claro', ['Mapa de poltronas', 'armchair'],
  'O ônibus inteiro <span class="dest">num relance</span>', 'e07', 'app.viajeon.com/operacoes');
fotoTela('fotos/f08-financeiro', 'escuro', ['Financeiro', 'wallet'],
  'Recebido, a receber e a pagar,<br>com <span class="dest">previsão de caixa</span>', 'e09', 'app.viajeon.com/financeiro');
fotoTela('fotos/f09-custos-da-operacao', 'verde', ['Custos', 'chart-pie'],
  'Receita, custos e lucro<br><span class="dest">de cada viagem</span>', 'e08', 'app.viajeon.com/financeiro');
fotoTela('fotos/f10-contratos', 'claro', ['Contratos', 'file-signature'],
  'Gerado, enviado e <span class="dest">assinado</span><br>sem sair do sistema', 'e06', 'app.viajeon.com/contratos');
fotoTela('fotos/f11-check-in', 'escuro', ['Check-in', 'qr-code'],
  'Embarque conferido<br><span class="dest">com QR code</span>', 'e11', 'app.viajeon.com/check-in');

// ===== DESTAQUES =====
const bolha = (txt, hora, eu = false) => `<div style="align-self:${eu ? 'flex-end' : 'flex-start'};max-width:84%;background:${eu ? '#D9FDD3' : '#fff'};color:#111;border-radius:14px;padding:12px 16px;font-size:19px;line-height:1.35;box-shadow:0 2px 4px rgba(0,0,0,.08)">${txt}<div style="text-align:right;font-size:13px;color:#667;margin-top:4px">${hora}</div></div>`;
peca('destaques/d01-whatsapp-x-sistema', F, `
<div class="pc claro grade">
  <div class="abs" style="left:64px;top:56px;width:1072px"><h2 style="font-size:52px">O problema não são as vendas.<br>É <span class="dest">não saber</span> no que elas viraram.</h2></div>
  <div class="abs" style="left:64px;top:290px;width:520px;height:480px;border-radius:28px;background:#E9DFC9;padding:28px;display:flex;flex-direction:column;gap:12px">
    <div style="font-weight:700;font-size:20px;color:#6b5f45;margin-bottom:4px">Como é hoje, no WhatsApp</div>
    ${bolha('Oi! Vi a excursão pra Foz, ainda tem vaga?', '09:14')}
    ${bolha('Tem sim! Deixa eu te passar os dados pra reservar', '09:22', true)}
    ${bolha('Oi, só pra avisar: acabei fechando com outra agência, foi mais rápido.', '3 dias depois')}
  </div>
  <div class="abs" style="right:64px;top:290px;width:520px;height:480px;border-radius:28px;background:#0A110E;color:#fff;padding:34px;--fs:22px">
    <div style="font-weight:800;font-size:22px;color:var(--on);margin-bottom:22px">Com o Sistema Viaje On</div>
    <ul class="lista" style="gap:18px">${['Cliente compra sozinho pelo link', 'Escolhe a poltrona e paga no mesmo checkout', 'Contrato gerado e assinado na hora', 'Você vê quem pagou e quem deve', 'Rooming list organizada sozinha', 'Fluxo de caixa por excursão'].map(t => `<li>${ico('circle-check')}<span>${t}</span></li>`).join('')}</ul>
  </div>
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
  <div class="abs" style="left:64px;top:56px;width:1072px">${selo('Sem visibilidade financeira', 'eye-off')}<h2 style="margin-top:18px;font-size:52px">Quem opera só na planilha <span class="dest">opera no escuro</span></h2></div>
  <div class="abs" style="left:64px;right:64px;top:300px;display:grid;grid-template-columns:1fr 1fr;gap:24px">
    ${[['Sem sistema', ['?', '?', '???'], '#FF8A8D', 'rgba(6,30,20,.6)'], ['Com Sistema Viaje On', ['R$ 59.340', 'R$ 37.300', 'R$ 22.040'], 'var(--on)', 'rgba(6,40,28,.75)']]
      .map(([t, v, c, bg]) => `<div class="cartao" style="background:${bg};padding:34px"><div style="font-weight:800;font-size:24px;color:${c};margin-bottom:8px">${t}</div><p style="font-size:18px;margin-bottom:22px">Excursão Foz do Iguaçu · 42 passageiros</p>
        ${['Receita', 'Custos', 'Lucro'].map((l, k) => `<div style="display:flex;justify-content:space-between;align-items:baseline;padding:14px 0;border-top:1px solid rgba(255,255,255,.1)"><span style="font-size:22px;color:rgba(255,255,255,.75)">${l}</span><b style="font-size:${k == 2 ? 40 : 30}px;color:${k == 2 ? c : '#fff'}">${v[k]}</b></div>`).join('')}</div>`).join('')}
  </div>
  <p class="abs" style="left:64px;bottom:40px;font-size:16px;color:rgba(255,255,255,.6)">Exemplo ilustrativo de uma excursão dentro do painel.</p>
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
