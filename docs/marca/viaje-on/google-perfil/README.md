# Imagens do Perfil da Empresa no Google: Viaje On

Peças para o Perfil da Empresa (Google Business Profile) da Viaje On: catálogo de produtos,
fotos (logo, capa e telas do sistema) e destaques (posts).

- **Telas** (`real/`): capturas reais do Sistema Viaje On, do repositório do sistema
  (`oi-charm-glow`: `public/apresentacao/telas` e `public/help/shots`), com a agência fictícia
  "Serra Turismo". Nenhum dado de cliente real.
- **Logo**: o oficial (`public/brand/viajeon-logo-dark.png`, copiado em `real/`). O avião do
  logotipo quadrado vem do favicon oficial (`marca/viajeon-aviao.png`).
- **Textos**: seguem a página viajeon.com/sistema e o DNA da marca. Nenhuma imagem mostra preço,
  porque os valores mudam nas promoções (ex.: Black). O preço vai no campo de preço do produto.

## O que subir em cada lugar

| Pasta | Tamanho | Onde usar no Perfil |
|---|---|---|
| `produtos/` | 1200×1200 | Produtos (uma imagem por produto) |
| `capa-viaje-on.jpg` | 1920×1080 | Foto de capa (gerador: `gerar-capa.cjs`) |
| `fotos/f02-logo.jpg` | 720×720 | Logotipo (o Google corta em círculo; o avião fica inteiro) |
| `fotos/f03` a `f12` | 1200×900 | Fotos |
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
| `p05` | Custos, financeiro e lucro por viagem | Recebimentos, pagamentos e saldo de cada operação, custos por fornecedor e o caixa da agência. Saiba o lucro de cada viagem antes do embarque. | viajeon.com/sistema |
| `p06` | PDV: venda presencial | Venda no balcão com pacotes e opcionais, cadastro rápido do passageiro, parcelamento e mais de uma forma de pagamento. | viajeon.com/sistema |
| `p07` | Lista de embarque e rooming list | Passageiros por ponto de embarque, quartos montados e relatórios em PDF para o guia e o hotel. | viajeon.com/sistema |
| `p08` | WhatsApp e e-mail automáticos | Mensagens automáticas ao passageiro: confirmação de reserva, lembrete de parcela e instruções de embarque, com modelos editáveis. | viajeon.com/sistema |
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

Para atualizar as telas, recorte de novo as capturas do repositório do sistema para `real/`
(as de `public/apresentacao/telas` em 1920×1200, a partir do topo).
