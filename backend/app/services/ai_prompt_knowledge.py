PAGE_PLANNER_STRUCTURE_KNOWLEDGE = """
NARRATIVA PADRÃO PARA ROTEIROS

Sempre que houver insumos no briefing, respeite esta sequência de blocos:
1. Hero imersivo com título forte, subtítulo com destino/datas, chips ou bullets e CTA principal (WhatsApp ou reserva) logo no topo.
2. Razões/diferenciais em cards simétricos (mínimo 3) para provar autoridade logo após o hero.
3. Story/banner com texto + imagem alternados para contextualizar a experiência.
4. Itinerário dia a dia em accordion (um bloco por dia) com destaques e imagens quando existirem.
5. Depoimentos com foto e nome real (mínimo 3) para reforçar prova social.
6. Blocos de serviço (o que inclui / o que não inclui, hospedagem, etc.) apresentados em listas curtas.
7. Planos e preços com pelo menos 3 pacotes nominais (ex.: Pacote Família, Pacote Premium) contendo valor, descrição e CTA "Reservar agora".
8. Countdown destacado em fundo na cor da agência antes do CTA final para criar urgência.
9. CTA final repetindo o benefício e direcionando novamente para WhatsApp ou reserva.

Se algum dado estiver ausente, marque como lacuna, mas mantenha a estrutura. Só pule uma seção se ela estiver redundante ou o briefing não trouxer nenhuma informação relevante.

SEÇÕES DISPONÍVEIS NO MODELO

As seções válidas são exatamente estas:
- hero
- reasons
- story
- photo
- itinerary
- banner_card
- prices
- testimonials
- countdown
- cta
- faq
- featured_video
- agency_footer

Você deve sempre usar os nomes originais acima.

DIRETRIZES VISUAIS POR SEÇÃO
- Hero: use layout "immersive" ou "split" com gradiente escuro sobre a foto, liste chips com argumentos (ex.: "Saída confirmada", "Grupo reduzido") e sempre inclua CTA principal e secundário quando houver link adicional.
- Reasons/testimonials/services: produza cards simétricos (3 por linha), com títulos curtos e descrições de 2-3 frases.
- Story/banner_card/photo: mantenha combinação texto + imagem alternando posições para evitar monotonia.
- Itinerary e FAQ: use accordion cronológico (um bloco por dia/pergunta) e destaque o título de cada etapa.
- Prices: gere pelo menos três pacotes diferentes com nome comercial, valor, descrição resumida e botão "Reservar agora"; use labels como "Melhor opção" para o plano destaque.
- Countdown: sempre defina backgroundColor e textColor coerentes com a cor principal da agência e conecte a mensagem de urgência com o CTA final.
- CTA: use o mesmo backgroundColor do tema/branding, headline curta e CTA explícito ("Quero falar no WhatsApp").

CAMPOS ORIGINAIS QUE VOCÊ DEVE RESPEITAR

Você deve sempre mapear usando os nomes originais do modelo.

Campos mais importantes por seção:

hero
- type
- title
- subtitle
- chips
- ctaLabel
- ctaLink
- backgroundImage
- logoUrl
- layout
- gradientColor

reasons
- type
- headingLabel
- title
- subtitle
- items[].icon
- items[].title
- items[].description

story
- type
- badge
- title
- subtitle
- images
- imagePosition
- ctaEnabled
- ctaLabel
- ctaLink

photo
- type
- image
- altText
- layout

itinerary
- type
- headingLabel
- title
- subtitle
- days[].day
- days[].title
- days[].description
- days[].image

banner_card
- type
- title
- subtitle
- ctaLabel
- ctaLink
- backgroundImage
- gradientColor
- bodyColor
- textColor
- cardBackground
- cardBorderColor

prices
- type
- headingLabel
- title
- subtitle
- description
- ctaLabel
- ctaLink
- items[].badge
- items[].titleLabel
- items[].title
- items[].description
- items[].priceLabel
- items[].price
- items[].currency
- items[].highlight

testimonials
- type
- headingLabel
- title
- subtitle
- items[].name
- items[].role
- items[].text
- items[].avatar

countdown
- type
- headingLabel
- label
- targetDate

cta
- type
- headingLabel
- label
- description
- ctaText
- link
- highlight

faq
- type
- headingLabel
- title
- subtitle
- items[].question
- items[].answer

featured_video
- type
- headingLabel
- title
- subtitle
- videoUrl
- ctaLabel
- ctaLink

agency_footer
- type
- displayVariant
- showCadastur
"""

PAGE_PLANNER_SECTION_FUNCTIONS = """
FUNÇÃO DE CADA SEÇÃO

hero
Abre a página.
Serve para impacto, desejo, resumo da experiência e CTA principal.

reasons
Transforma diferenciais em benefícios.
Ideal para mostrar por que vale a pena viver essa viagem.

story
Aprofunda.
Pode falar sobre destino, hotel, proposta da viagem, experiência ou contexto.

photo
Cria respiro visual e reforço emocional.

itinerary
Organiza o dia a dia ou as etapas principais.
Deve explicar a experiência, não só listar ações.

banner_card
Serve para destaque intermediário.
Use para escassez, convite, chamada especial ou oportunidade.

prices
Apresenta a oferta.
Deve deixar o investimento claro e bem organizado.

testimonials
Gera prova social e confiança.

countdown
Gera urgência temporal real.

cta
Fecha a decisão com clareza.

faq
Remove objeções.

featured_video
Aprofunda a compreensão quando houver vídeo.

agency_footer
Fecha institucionalmente.
"""

