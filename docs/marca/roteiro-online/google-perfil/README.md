# Imagens do Perfil da Empresa no Google

Peças para preencher o Perfil da Empresa (Google Business Profile) do Roteiro Online:
catálogo de produtos, fotos (logo, capa e telas do sistema) e destaques (posts).

As telas do sistema são reais: vêm da agência de demonstração "Rota Sul Viagens"
(`frontend/src/help/media`). As telas de celular são páginas publicadas que já
aparecem como exemplo na página de vendas e nos materiais (pasta `celular/`).
Os textos seguem a página de vendas atual (plano único, 7 dias de garantia).
Nenhuma peça mostra preço de assinatura, porque ele muda nas ofertas do Admin Master.

## O que subir em cada lugar

| Pasta | Tamanho | Onde usar no Perfil |
|---|---|---|
| `produtos/` | 1200×1200 | Produtos (uma imagem por produto) |
| `fotos/f01-capa.jpg` | 1920×1080 | Foto de capa |
| `fotos/f02-logo.jpg` | 720×720 | Logotipo |
| `fotos/f03` a `f10` | 1200×900 | Fotos (seção "No trabalho" / "Interior") |
| `destaques/` | 1200×900 | Atualizações (posts) e fotos extras |

## Textos prontos para o catálogo de produtos

Categoria sugerida: **Roteiro Online**. Link de cada produto: https://roteiroonline.com

| Imagem | Nome do produto | Descrição |
|---|---|---|
| `p01` | Roteiro Online: assinatura completa | Plataforma para criar páginas profissionais de roteiro de viagem e mandar o link no WhatsApp. Plano único com tudo incluso: roteiros ilimitados, editor visual, Assistente de IA, Módulo Leads, Pixels Meta e Google e domínio próprio. 7 dias de garantia. |
| `p02` | Editor visual de páginas de roteiro | Monte a página da viagem com seções prontas de capa, itinerário dia a dia, inclusos, preços e dúvidas. É só trocar fotos, textos e valores, sem conhecimento técnico. |
| `p03` | Assistente de IA para roteiros | Conte a viagem por texto, áudio, PDF ou prints e a IA monta a página inteira, com banner, roteiro dia a dia, inclusos, preços e dúvidas. Você só revisa e publica. |
| `p04` | Módulo Leads e funil de vendas | Formulário dentro do roteiro, funil por etapas e contato no WhatsApp com um clique. Cada interessado vira uma oportunidade de venda. |
| `p05` | Página de roteiro para celular | Um link só, que abre em qualquer celular. O passageiro abre, revisita e compartilha o roteiro, que fica sempre atualizado. |
| `p06` | Pixel Meta e Google | Anuncie para a página do roteiro e faça remarketing com quem viu e não fechou. Visitas, cliques no WhatsApp e leads no painel. |
| `p07` | Domínio próprio da agência | Publique seus roteiros no endereço da sua agência, em domínio seguro. Alterou? Atualiza para todo mundo na hora. |
| `p08` | Preços, contagem regressiva e WhatsApp | Cards de investimento para adulto, criança e tipo de quarto, contagem regressiva até a saída e botão de WhatsApp com mensagem pronta. |

## Gerar de novo

Precisa de acesso à internet (fontes Sora e Inter e ícones Lucide).

    cd docs/marca/roteiro-online/google-perfil
    node gerar.cjs           # todas as peças
    node gerar.cjs p03 f01   # só as pedidas

Para trocar uma tela, mude o arquivo usado em `gerar.cjs` (`TELA(...)` para as telas do painel,
`CEL(...)` para as de celular). As telas do painel se atualizam com `tools/help-media`.
