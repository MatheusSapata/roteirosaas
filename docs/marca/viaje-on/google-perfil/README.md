# Imagens do Perfil da Empresa no Google: Viaje On

Peças para o Perfil da Empresa (Google Business Profile) da Viaje On: catálogo de produtos,
fotos (logo, capa e telas do sistema) e destaques (posts).

- **Telas** (`telas/`): a demonstração do Sistema Viaje On da página viajeon.com/sistema
  (agência fictícia "Serra Turismo"), capturada em alta resolução e sem a barra de progresso.
- **Logo** (`marca/`): avião do favicon (`viajeon-icone.png`, `viajeon-aviao.png`) e o texto
  "Viajeon" tirado de `frontend/src/assets/logo-viajeon-modoescuro.png`, sem a palavra "Sistema"
  e com o "on" no Verde On (#90EE8F), igual ao banner de compartilhamento de app.viajeon.com.
- **Textos**: seguem a página viajeon.com/sistema e o DNA da marca. Nenhuma imagem mostra preço,
  porque os valores mudam nas promoções (ex.: Black). O preço vai no campo de preço do produto.

## O que subir em cada lugar

| Pasta | Tamanho | Onde usar no Perfil |
|---|---|---|
| `produtos/` | 1200×1200 | Produtos (uma imagem por produto) |
| `fotos/f01-capa.jpg` | 1920×1080 | Foto de capa |
| `fotos/f02-logo.jpg` | 720×720 | Logotipo (o Google corta em círculo; o avião fica inteiro) |
| `fotos/f03` a `f11` | 1200×900 | Fotos |
| `destaques/` | 1200×900 | Atualizações (posts) e fotos extras |

Para o produto **Roteiro Online**, use `docs/marca/roteiro-online/google-perfil/produtos/p01-roteiro-online-assinatura.jpg`.

## Textos prontos para o catálogo

Categorias sugeridas: **Sistema Viaje On**, **Planos** e **Mentoria**.

| Imagem | Nome do produto | Descrição | Link |
|---|---|---|---|
| `p01` | Sistema Viaje On | Backoffice completo para agências de viagens: vendas online, passageiros, poltronas, contratos, rooming list e financeiro no mesmo sistema. Saiba em tempo real quanto cada viagem está dando de lucro. | viajeon.com/sistema |
| `p02` | Venda online por link | Mande o link no WhatsApp, Instagram ou anúncio. O passageiro preenche os dados, escolhe a poltrona e paga sozinho, num checkout com a marca e o domínio da agência. | viajeon.com/sistema |
| `p03` | Mapa de poltronas | Cada venda ocupa a poltrona escolhida no checkout. Veja ocupadas, livres, pendentes e bloqueadas em tempo real, sem controle manual. | viajeon.com/sistema |
| `p04` | Contrato automático | Contrato gerado com os dados da viagem e do passageiro e assinado online pelo celular, com data, hora e IP. Sem editar um por um. | viajeon.com/sistema |
| `p05` | Custos, financeiro e lucro por viagem | Custos por categoria e fornecedor, parcelas dos passageiros, contas a pagar e fluxo de caixa. Saiba o lucro de cada viagem antes do embarque. | viajeon.com/sistema |
| `p06` | PDV: venda presencial | Venda no balcão com pacotes e opcionais, cadastro rápido do passageiro, parcelamento e mais de uma forma de pagamento. | viajeon.com/sistema |
| `p07` | Check-in com QR code e área do guia | O guia confere cada passageiro no embarque pelo celular, com QR code e a poltrona de cada um. | viajeon.com/sistema |
| `p08` | E-mail e WhatsApp automáticos | Mensagens automáticas ao passageiro: reserva confirmada, contrato pendente, lembrete de parcela e instruções de embarque, com modelos editáveis. | viajeon.com/sistema |
| `p09` | Sistema Viaje On: plano Básico | Vendas online, 1 usuário, custos, financeiro e PDV, veículos, assentos e rooming list e contratos automáticos. 7 dias de garantia. | viajeon.com/sistema |
| `p10` | Sistema Viaje On: plano Intermediário | Tudo do Básico, 5 usuários, área do cliente e do guia, WhatsApp, afiliados e domínio próprio. 7 dias de garantia. | viajeon.com/sistema |
| `p11` | Sistema Viaje On: plano Avançado | Tudo do Intermediário, usuários ilimitados, sem taxa nas vendas online e integrações Asaas, Mercado Pago e InfinitePay. 7 dias de garantia. | viajeon.com/sistema |
| `p12` | PAAV: Plano de Aceleração para Agência de Viagens | Mentoria para o dono de agência que quer parar de competir no preço e crescer com processo, posicionamento e margem. Comece com uma conversa gratuita de 30 minutos. | link de agendamento do PAAV |

Preços dos planos na página em 2026-11-10 (mensal): Básico R$ 147, Intermediário R$ 247 e
Avançado R$ 397. Confira na página antes de preencher, porque a promoção pode estar ativa.

## Gerar de novo

Precisa de acesso à internet (fontes Inter e Fraunces e ícones Lucide).

    cd docs/marca/viaje-on/google-perfil
    node gerar.cjs           # todas as peças
    node gerar.cjs p03 f01   # só as pedidas

Para atualizar as telas, capture de novo a demonstração de viajeon.com/sistema (elemento
`.vo-stage`, uma captura por etapa `.vo-seg`) e corte a barra de progresso embaixo.
