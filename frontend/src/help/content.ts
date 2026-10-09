/**
 * Conteúdo da Central de Ajuda. Veja as regras de atualização em ./index.ts.
 * Texto: português do Brasil, frases curtas, "você", nomes de botões como aparecem na tela.
 * **negrito** marca botões e campos. `tela` aponta o passo da demonstração (passos.json).
 */
import {
  BuildingIcon,
  FileTextIcon,
  LayersIcon,
  PencilRulerIcon,
  PlugIcon,
  RocketIcon,
  UserRoundIcon,
  UsersIcon
} from "lucide-vue-next";
import type { HelpArticle, HelpModule } from "./index";

export const HELP_MODULES: HelpModule[] = [
  { id: "comece", titulo: "O básico", descricao: "O painel e as palavras que você vai ver por todo lado.", icone: RocketIcon },
  { id: "paginas", titulo: "Páginas", descricao: "Criar, publicar, duplicar e acompanhar suas páginas.", icone: FileTextIcon },
  { id: "editor", titulo: "Editor de páginas", descricao: "Montar a página: seções, cores, link e Assistente IA.", icone: PencilRulerIcon },
  { id: "secoes", titulo: "Seções", descricao: "O que cada seção faz e como configurar as principais.", icone: LayersIcon },
  { id: "leads", titulo: "Captação de leads", descricao: "Formulários, oportunidades, etapas e clientes.", icone: UsersIcon },
  { id: "integracoes", titulo: "Integrações", descricao: "Pixel, Viaje On, ViajeChat e WhatsApp.", icone: PlugIcon },
  { id: "agencia", titulo: "Agência", descricao: "Dados da agência, equipe, domínio e faturas.", icone: BuildingIcon },
  { id: "conta", titulo: "Sua conta", descricao: "Perfil, senha, plano e assinatura.", icone: UserRoundIcon }
];

/** Ordem de "Comece por aqui". */
export const FIRST_STEPS = ["configurar-agencia", "criar-pagina", "adicionar-secao", "editar-secao", "publicar-pagina", "criar-formulario"];

export const HELP_ARTICLES: HelpArticle[] = [
  // ───────────── Comece por aqui ─────────────
  {
    id: "conhecer-o-painel",
    modulo: "comece",
    titulo: "Conhecer o painel",
    resumo: "Onde fica cada coisa e o que os números do Dashboard mostram.",
    atualizado: "2026-10-09",
    rota: "/admin/dashboard",
    rotaRotulo: "Abrir o Dashboard",
    busca: "dashboard inicio menu lateral navegar painel metricas visitas cliques resumo periodo tema escuro",
    passos: [
      { titulo: "Use o menu para navegar", texto: "**Principal** tem Dashboard, Páginas e Captação de leads. **Configurar** tem Integrações, Minha Agência e Domínios. **Aprender** tem esta Central e as Aulas. O alfinete no topo deixa o menu sempre aberto.", tela: 1 },
      { titulo: "Crie páginas de qualquer tela", texto: "O botão **Nova página** fica no topo do menu.", tela: 2 },
      { titulo: "Escolha o período", texto: "**7 dias**, **14 dias** ou **30 dias** mudam todos os números do Dashboard.", tela: 3 },
      { titulo: "Acompanhe os números", texto: "**Visitas**, **Cliques nos botões**, **Leads** e **Páginas no ar**, com a comparação com o período anterior.", tela: 4 },
      { titulo: "Veja onde as visitas se perdem", texto: "**Do clique ao lead** mostra quantas visitas clicaram no WhatsApp ou nos botões e quantas viraram lead.", tela: 5 },
      { titulo: "Atenda quem acabou de chegar", texto: "**Chegaram agora** lista os últimos leads, com atalho para o WhatsApp e para os detalhes.", tela: 6 }
    ],
    blocos: [{ tipo: "dica", texto: "Prefere o painel escuro? Ligue **Tema escuro** no fim do menu. A escolha fica salva neste navegador." }],
    relacionados: ["configurar-agencia", "criar-pagina", "oportunidades"],
    substituiAulas: ["visao geral da plataforma", "boas-vindas"]
  },
  {
    id: "palavras-do-roteiro",
    modulo: "comece",
    titulo: "Palavras que você vai ver no Roteiro Online",
    resumo: "Página, seção, camada, lead, oportunidade, pixel: o que cada termo quer dizer aqui.",
    atualizado: "2026-10-09",
    busca: "glossario termos significado o que e slug link camada rascunho publicada lead oportunidade etapa funil pixel dominio",
    blocos: [
      {
        tipo: "tabela",
        colunas: ["Palavra", "O que é"],
        linhas: [
          ["Página", "A página de venda de uma viagem ou da agência, com link próprio para divulgar."],
          ["Seção", "Cada bloco da página: Banner Inicial, Preços e pacotes, Depoimentos…"],
          ["Camadas", "A lista de seções no editor, na ordem em que aparecem na página."],
          ["Rascunho", "Página que só você vê. Ela vai ao ar quando você clica em **Publicar**."],
          ["Publicada", "Página no ar, aberta para qualquer pessoa com o link."],
          ["Página principal", "A página que abre no link da agência, sem o nome da página no final."],
          ["Link da agência", "O começo do endereço de todas as suas páginas: roteiroonline.com/link-da-agencia."],
          ["Lead", "A pessoa que deixou nome e contato num formulário da página."],
          ["Oportunidade", "O atendimento de um lead, que anda pelas etapas do funil até virar venda ou perda."],
          ["Etapa do funil", "Cada fase do atendimento: Novo contato, Em atendimento, Proposta enviada…"],
          ["Cliente", "O cadastro da pessoa, que junta todas as oportunidades dela."],
          ["Pixel", "O código do Meta ou do Google que conta visitas e conversões para os anúncios."],
          ["Domínio próprio", "Um endereço da sua agência, como viagens.suaagencia.com.br, no lugar do roteiroonline.com."]
        ]
      }
    ],
    relacionados: ["conhecer-o-painel", "conhecer-o-editor", "oportunidades"]
  },

  // ───────────── Páginas ─────────────
  {
    id: "criar-pagina",
    modulo: "paginas",
    titulo: "Criar uma página",
    resumo: "Comece do zero ou a partir de um modelo pronto. A página nasce como rascunho.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Ir para Páginas",
    busca: "nova pagina roteiro criar modelo template rascunho comecar",
    passos: [
      { titulo: "Abra Páginas e clique em Nova Página", texto: "Fica no topo da lista de páginas. O botão **Nova página** do menu lateral faz o mesmo.", tela: 1 },
      { titulo: "Escolha como começar", texto: "**Criar página do zero** abre o editor vazio. **Criar a partir de modelo** traz uma página pronta para você trocar só o conteúdo.", tela: 2 },
      { titulo: "Monte a página no editor", texto: "A página abre no editor como rascunho. Adicione as seções e publique quando estiver pronta.", tela: 3 }
    ],
    duvidas: [
      ["Quantas páginas posso ter?", "O limite do plano vale para páginas publicadas: até 3 no Profissional, até 10 no Agência e sem limite no Escala. Rascunhos não contam."],
      ["Criei do zero e a página veio vazia. É normal?", "Sim. Use **+ Seção** no editor para adicionar a primeira seção, ou peça ao **Assistente IA** para montar a estrutura."],
      ["Não aparece nenhum modelo", "Os modelos são publicados pela equipe do Roteiro Online. Se a lista estiver vazia, comece do zero ou duplique uma página sua."]
    ],
    relacionados: ["adicionar-secao", "duplicar-pagina", "publicar-pagina"]
  },
  {
    id: "gerenciar-paginas",
    modulo: "paginas",
    titulo: "Encontrar e gerenciar páginas",
    resumo: "Filtrar, buscar, copiar o link e ver os números de cada página.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Ir para Páginas",
    busca: "lista paginas buscar filtrar copiar link metricas despublicar excluir pagina principal padrao menu acoes",
    passos: [
      { titulo: "Filtre por situação", texto: "**Todas**, **Publicadas** ou **Rascunhos**. Ao lado, ordene por mais recentes ou mais visitadas.", tela: 1 },
      { titulo: "Busque pelo nome", tela: 2 },
      { titulo: "Copie o link para divulgar", texto: "**Copiar** fica no card de cada página publicada. Rascunhos ganham link quando forem publicados.", tela: 3 },
      { titulo: "Confira os números", texto: "Visitas, cliques e leads da página, e quanto das visitas virou lead.", tela: 4 },
      { titulo: "Use o menu de ações", texto: "Os três pontinhos do card têm **Duplicar**, **Definir como principal**, **Despublicar** e **Excluir**.", tela: 5 }
    ],
    blocos: [
      { tipo: "texto", texto: "A **página principal** abre no link da agência, sem o nome da página no final. Ela aparece com o selo **Padrão**." },
      { tipo: "atencao", texto: "**Excluir** apaga a página e não dá para desfazer. Se for só tirar do ar, use **Despublicar**." }
    ],
    relacionados: ["duplicar-pagina", "publicar-pagina", "titulo-e-link"]
  },
  {
    id: "duplicar-pagina",
    modulo: "paginas",
    titulo: "Duplicar uma página",
    resumo: "Use uma página pronta como ponto de partida para outra viagem.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Ir para Páginas",
    busca: "copiar pagina duplicar clonar copia nova data saida reaproveitar",
    passos: [
      { titulo: "Abra o menu de ações da página", texto: "Os três pontinhos no card da página.", tela: 1 },
      { titulo: "Clique em Duplicar", tela: 2 },
      { titulo: "Dê um título à cópia", texto: "O **Link da página** se ajusta sozinho; você pode trocar.", tela: 3 },
      { titulo: "Confirme em Duplicar", texto: "A cópia nasce como rascunho, com todas as seções, fotos e cores.", tela: 5 }
    ],
    blocos: [{ tipo: "dica", texto: "Para uma nova data da mesma viagem, duplique e troque só as datas e os preços." }],
    relacionados: ["gerenciar-paginas", "publicar-pagina"]
  },
  {
    id: "publicar-pagina",
    modulo: "paginas",
    titulo: "Publicar a página",
    resumo: "Coloque o rascunho no ar e pegue o link para divulgar.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Ir para Páginas",
    busca: "publicar no ar ativar link divulgar rascunho despublicar visualizar compartilhar",
    passos: [
      { titulo: "Confira a situação", texto: "No topo do editor, **Rascunho** quer dizer que só você vê a página.", tela: 1 },
      { titulo: "Clique em Publicar", texto: "O editor salva o que estiver pendente e publica.", tela: 2 },
      { titulo: "Visualize e divulgue", texto: "**Visualizar página** abre a página no ar. O link também fica no card da página, em Páginas.", tela: 3 }
    ],
    blocos: [
      { tipo: "texto", texto: "Depois de publicada, cada **Salvar** já atualiza a página no ar." },
      { tipo: "texto", texto: "Para tirar do ar, use **Despublicar** no menu de ações do card, em Páginas. Ela volta a ser rascunho." }
    ],
    duvidas: [
      ["Apareceu um aviso de limite ao publicar", "O plano chegou ao número máximo de páginas publicadas. Despublique uma página antiga ou mude de plano."],
      ["Mudei a página e não aparece no ar", "Clique em **Salvar** no editor e recarregue a página publicada."]
    ],
    relacionados: ["titulo-e-link", "pixel-meta-google", "gerenciar-paginas"],
    substituiAulas: ["publicando e acompanhando"]
  },

  // ───────────── Editor ─────────────
  {
    id: "conhecer-o-editor",
    modulo: "editor",
    titulo: "Conhecer o editor",
    resumo: "Camadas, prévia, configurações da página e os botões de salvar e publicar.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Abrir uma página",
    busca: "editor construtor tela de edicao camadas previa celular computador configuracoes",
    passos: [
      { titulo: "Camadas", texto: "A lista de seções, na ordem da página. Clique numa camada para editar a seção.", tela: 1 },
      { titulo: "Prévia", texto: "A página como o visitante vê. Passe o mouse numa seção para editar, mover, duplicar, esconder ou excluir.", tela: 2 },
      { titulo: "Computador e celular", texto: "Alterne para conferir como a página fica no celular.", tela: 3 },
      { titulo: "Configurações da página", texto: "Na barra da esquerda: **Título e link**, **Cores**, **Rastreamento** e **Captação de leads**.", tela: 4 },
      { titulo: "Assistente IA", texto: "Monta a estrutura, melhora textos e cria seções com você.", tela: 5 },
      { titulo: "Salvar e Publicar", texto: "**Salvar** guarda as mudanças. **Publicar** coloca a página no ar.", tela: 6 }
    ],
    blocos: [{ tipo: "dica", texto: "No celular, o editor mostra uma barra embaixo com **Seções**, **Página** e **+** para adicionar seção." }],
    relacionados: ["adicionar-secao", "editar-secao", "organizar-secoes"],
    substituiAulas: ["editor de historias"]
  },
  {
    id: "adicionar-secao",
    modulo: "editor",
    titulo: "Adicionar uma seção",
    resumo: "Escolha no catálogo e a seção entra na página com textos de exemplo.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Abrir uma página",
    busca: "nova secao adicionar inserir bloco catalogo categoria",
    passos: [
      { titulo: "Clique em + Seção", texto: "Fica no topo das Camadas. Na prévia, a linha **+** entre duas seções insere naquele ponto.", tela: 1 },
      { titulo: "Escolha a categoria ou busque", texto: "As seções ficam em Menu e rodapé, Capa, Detalhamento, Fotos e vídeos, Venda, Confiança e Contato.", tela: 2 },
      { titulo: "Clique na seção", texto: "O cartão mostra a seção de verdade, com textos de exemplo.", tela: 3 },
      { titulo: "Troque o conteúdo de exemplo", texto: "A seção entra no fim da página, antes do rodapé. Clique nela para editar.", tela: 4 },
      { titulo: "Salve a página", tela: 5 }
    ],
    blocos: [{ tipo: "dica", texto: "Inseriu sem querer? Clique em **Desfazer** no aviso que aparece embaixo." }],
    relacionados: ["secoes-disponiveis", "editar-secao", "organizar-secoes"]
  },
  {
    id: "editar-secao",
    modulo: "editor",
    titulo: "Editar uma seção",
    resumo: "Textos, fotos e botões em Conteúdo; layout e cores em Aparência.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Abrir uma página",
    busca: "editar secao trocar texto foto botao layout aparencia conteudo alinhamento salvar secao descartar",
    passos: [
      { titulo: "Abra a seção", texto: "Clique na camada ou, na prévia, em **Editar seção**.", tela: 1 },
      { titulo: "Abra o grupo que quer mudar", texto: "**Conteúdo** tem textos, fotos, datas e botões. Os grupos vêm fechados para a lista ficar curta.", tela: 2 },
      { titulo: "Edite: a prévia muda na hora", tela: 3 },
      { titulo: "Ajuste o visual em Aparência", texto: "Layout, fundo, alinhamento do título e outras opções de cada seção.", tela: 4 },
      { titulo: "Salve a seção", texto: "**Salvar seção** guarda; **Descartar** volta ao que estava. Se trocar de seção com mudanças pendentes, o editor pergunta se quer salvar.", tela: 6 }
    ],
    relacionados: ["adicionar-secao", "organizar-secoes", "cores-da-pagina"]
  },
  {
    id: "organizar-secoes",
    modulo: "editor",
    titulo: "Mudar a ordem, esconder e duplicar seções",
    resumo: "Arraste as camadas, esconda sem apagar e use as ações da prévia.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Abrir uma página",
    busca: "ordem mover arrastar reordenar esconder ocultar duplicar excluir apagar secao",
    passos: [
      { titulo: "Arraste pela alça", texto: "Os pontinhos à esquerda de cada camada.", tela: 1 },
      { titulo: "Esconda sem apagar", texto: "O interruptor tira a seção da página publicada. Ligue de novo para voltar.", tela: 2 },
      { titulo: "Use as ações da prévia", texto: "Passe o mouse sobre a seção: subir, descer, duplicar, esconder e excluir.", tela: 4 }
    ],
    blocos: [{ tipo: "texto", texto: "O **Menu do topo** e o **Vídeo de Vendas (VSL)** ficam sempre no começo da página." }],
    relacionados: ["editar-secao", "adicionar-secao"]
  },
  {
    id: "titulo-e-link",
    modulo: "editor",
    titulo: "Título, link e descrição da página",
    resumo: "O nome na aba do navegador, o endereço da página e o texto do Google e do WhatsApp.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Abrir uma página",
    busca: "titulo link slug endereco url descricao seo google whatsapp compartilhar previa do link",
    passos: [
      { titulo: "Clique em Título e link", texto: "O primeiro ícone da barra de configurações do editor.", tela: 1 },
      { titulo: "Título da página", texto: "Aparece na aba do navegador, no Google e na sua lista de páginas.", tela: 2 },
      { titulo: "Link da página", texto: "O endereço que você divulga. Só letras, números e hífens, sem espaços nem acentos.", tela: 3 },
      { titulo: "Descrição curta", texto: "Aparece no Google e na prévia do link no WhatsApp.", tela: 4 }
    ],
    blocos: [{ tipo: "atencao", texto: "Trocar o link de uma página publicada quebra o link antigo que já foi divulgado." }],
    relacionados: ["publicar-pagina", "dominio-proprio"]
  },
  {
    id: "cores-da-pagina",
    modulo: "editor",
    titulo: "Cores da página",
    resumo: "Cor de destaque, fundo das seções e o visual de todas as seções de uma vez.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Abrir uma página",
    busca: "cor cores destaque botao fundo tema visual cantos sombra paleta",
    passos: [
      { titulo: "Clique em Cores", tela: 1 },
      { titulo: "Cor de destaque", texto: "Botões, selos e ícones de todas as seções.", tela: 2 },
      { titulo: "Fundo das seções", texto: "As duas cores que as seções alternam no fundo. Cada seção pode ter o próprio fundo em Aparência.", tela: 3 },
      { titulo: "Visual das seções", texto: "Cantos, sombras e títulos de todas as seções de uma vez.", tela: 4 },
      { titulo: "Salve", tela: 5 }
    ],
    blocos: [{ tipo: "dica", texto: "A cor principal da agência (em Minha Agência) é o ponto de partida de toda página nova." }],
    relacionados: ["editar-secao", "configurar-agencia"]
  },
  {
    id: "assistente-ia",
    modulo: "editor",
    titulo: "Assistente IA",
    resumo: "Peça a estrutura da página, textos melhores ou seções novas, com base nas suas informações.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Abrir uma página",
    busca: "inteligencia artificial ia assistente gerar texto estrutura automatica pdf print chat",
    passos: [
      { titulo: "Clique em Assistente IA", texto: "No topo do editor.", tela: 1 },
      { titulo: "Comece por um atalho", texto: "**Montar estrutura da página**, **Melhorar texto da capa** ou **Criar perguntas frequentes**.", tela: 2 },
      { titulo: "Ou escreva o que precisa", texto: "Mande também PDF, prints ou fotos com as informações da viagem.", tela: 3 },
      { titulo: "Revise antes de aplicar", texto: "Você escolhe se insere as seções sugeridas no fim da página ou substitui a estrutura.", tela: 4 }
    ],
    blocos: [{ tipo: "texto", texto: "O plano tem um número de mensagens por mês, que aparece no topo do assistente." }],
    relacionados: ["adicionar-secao", "editar-secao"]
  },

  // ───────────── Seções ─────────────
  {
    id: "secoes-disponiveis",
    modulo: "secoes",
    titulo: "Seções disponíveis",
    resumo: "Todas as seções do catálogo, por categoria, e quando usar cada uma.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Abrir uma página",
    busca: "catalogo secoes lista tipos blocos categorias capa venda confianca contato detalhamento",
    blocos: [
      {
        tipo: "tabela",
        titulo: "Catálogo de seções",
        colunas: ["Categoria", "Seção", "Para que serve"],
        linhas: [
          ["Menu e rodapé", "Menu do topo", "Logo, links para as seções e botão de contato."],
          ["Menu e rodapé", "Rodapé da agência", "Contatos, Cadastur e redes da agência."],
          ["Capa", "Banner Inicial", "Foto grande, título, datas e o botão principal."],
          ["Capa", "Banner em Card", "Foto de fundo com texto e botão por cima, com ou sem card."],
          ["Capa", "Vídeo de Vendas (VSL)", "Vídeo com botão embaixo; pode esconder o resto da página até um momento do vídeo."],
          ["Detalhamento", "Texto e Imagens", "Texto com carrossel de até 10 fotos."],
          ["Detalhamento", "Diferenciais", "Cards com ícone, título e texto curto."],
          ["Detalhamento", "Artigo", "Imagem de capa com título e texto formatado, como um post."],
          ["Detalhamento", "Roteiro dia a dia", "Linha do tempo com data e foto de cada dia."],
          ["Detalhamento", "Voos", "Horários, conexões e bagagem de ida e volta."],
          ["Detalhamento", "Links/Roteiros", "Cards que levam para suas outras páginas."],
          ["Fotos e vídeos", "Foto em destaque", "Uma imagem grande com legenda."],
          ["Fotos e vídeos", "Vídeo", "Vídeo do YouTube ou Vimeo com título."],
          ["Venda", "Preços e pacotes", "Lista de ofertas, de uma até várias."],
          ["Venda", "Compra Online (Viaje On)", "Pacotes do Viaje On com compra direta. Precisa da integração."],
          ["Venda", "Contagem regressiva", "Prazo da oferta com dias, horas e minutos."],
          ["Venda", "Faixa de chamada", "Frase curta com um botão de destaque."],
          ["Confiança", "Depoimentos", "Relatos de quem já viajou com você."],
          ["Confiança", "Dúvidas frequentes", "Perguntas e respostas que abrem com um toque."],
          ["Contato", "Formulário de contato", "Capta nome, WhatsApp e e-mail do interessado."]
        ]
      },
      {
        tipo: "lista",
        titulo: "Uma ordem que costuma funcionar",
        itens: [
          "Menu do topo e Banner Inicial com datas e o botão principal.",
          "Texto e Imagens contando a experiência, e Diferenciais.",
          "Roteiro dia a dia e Galeria ou Vídeo.",
          "Preços e pacotes, com Contagem regressiva se houver prazo.",
          "Depoimentos e Dúvidas frequentes.",
          "Formulário de contato ou Faixa de chamada, e o Rodapé da agência."
        ]
      }
    ],
    relacionados: ["adicionar-secao", "editar-secao", "assistente-ia"],
    substituiAulas: ["catalogo de secoes"]
  },
  {
    id: "menu-do-topo",
    modulo: "secoes",
    titulo: "Menu do topo",
    resumo: "Links para as seções, botão de WhatsApp e o menu transparente sobre a capa.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Abrir uma página",
    busca: "menu topo cabecalho header navegacao transparente desfoque fixo links logo",
    passos: [
      { titulo: "Clique em Menu do topo", tela: 1 },
      { titulo: "Monte os links", texto: "Até 7 links, cada um levando a uma seção da página. Em **Lado direito do menu**, o botão abre o WhatsApp com mensagem pronta ou um link.", tela: 2 },
      { titulo: "Em Aparência, escolha o fundo", texto: "**Sólido**, **Transparente** ou **Desfoque**.", tela: 3 },
      { titulo: "Transparente fica sobre a capa", texto: "Transparente e desfoque ficam sobre a foto do Banner Inicial e ganham fundo quando o visitante rola a página.", tela: 4 },
      { titulo: "Salve a seção", tela: 5 }
    ],
    blocos: [{ tipo: "texto", texto: "O logo vem do Banner Inicial ou, sem ele, de Minha Agência." }],
    relacionados: ["editar-secao", "configurar-agencia"]
  },
  {
    id: "video-de-vendas",
    modulo: "secoes",
    titulo: "Vídeo de Vendas (VSL)",
    resumo: "Um vídeo no topo da página que libera o botão e o resto da página no momento certo.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Abrir uma página",
    busca: "vsl video de vendas liberar botao momento do video aula gratuita webinar esconder pagina youtube vimeo panda",
    passos: [
      { titulo: "Clique em Vídeo de Vendas (VSL)", texto: "Ela fica sempre no topo da página.", tela: 1 },
      { titulo: "Cole o link do vídeo", texto: "YouTube, Vimeo ou Panda. A capa do vídeo é opcional.", tela: 2 },
      { titulo: "Escolha quando o botão aparece", texto: "Em **Liberação do botão**, ligue **Liberar só no momento da oferta**, informe minutos e segundos e escolha **O que aparece**: botão e página, só o botão ou só a página. Até lá, o visitante vê apenas o vídeo.", tela: 3 },
      { titulo: "Salve a seção", tela: 4 }
    ],
    blocos: [{ tipo: "dica", texto: "Use o minuto em que você apresenta a oferta no vídeo. A **Barra de progresso** ajuda o visitante a ficar até lá." }],
    relacionados: ["precos-e-pacotes", "editar-secao"]
  },
  {
    id: "precos-e-pacotes",
    modulo: "secoes",
    titulo: "Preços e pacotes",
    resumo: "Ofertas com preço, complemento, selo e o botão de reserva.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Abrir uma página",
    busca: "preco valor pacote oferta parcelas por pessoa reservar pagamento pix cartao",
    passos: [
      { titulo: "Clique em Preços e pacotes", tela: 1 },
      { titulo: "Monte as ofertas", texto: "Nome, preço e moeda, **Complemento** (por pessoa, parcelas) e **Selo**. **Destacar esta oferta** chama atenção para a principal.", tela: 2 },
      { titulo: "Escolha o botão de cada oferta", texto: "Dentro da oferta, em **Botão da oferta**: texto e para onde ele leva.", tela: 3 },
      { titulo: "Mostre as formas de pagamento", tela: 4 }
    ],
    relacionados: ["compra-online", "editar-secao"]
  },
  {
    id: "links-roteiros",
    modulo: "secoes",
    titulo: "Links/Roteiros",
    resumo: "Cards que levam para suas outras páginas ou para qualquer link.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Abrir uma página",
    busca: "links roteiros outros roteiros cards carrossel outras paginas vitrine",
    passos: [
      { titulo: "Clique em Links/Roteiros", tela: 1 },
      { titulo: "Adicione os cards", texto: "Escolha uma página sua ou cole um link. **Buscar foto e texto do link** preenche título, foto e datas.", tela: 2 },
      { titulo: "Confira na prévia", texto: "As setas nas laterais passam os cards, até 4 por vez no computador.", tela: 3 }
    ],
    relacionados: ["secoes-disponiveis", "gerenciar-paginas"]
  },
  {
    id: "compra-online",
    modulo: "secoes",
    titulo: "Compra Online (Viaje On)",
    resumo: "Pacotes ativos do Viaje On na página, com compra direta.",
    atualizado: "2026-10-09",
    rota: "/admin/integracoes/viajeon",
    rotaRotulo: "Abrir Viaje On",
    busca: "checkout viajeon compra online pagamento pacotes travado bloqueado integrar",
    passos: [
      { titulo: "Clique em + Seção", tela: 1 },
      { titulo: "Abra a categoria Venda", tela: 2 },
      { titulo: "Escolha Compra Online (Viaje On)", texto: "Sem a integração, o cartão fica travado e o botão **Integrar** leva para a conexão.", tela: 3 }
    ],
    blocos: [{ tipo: "texto", texto: "Com o Viaje On conectado, escolha o checkout na seção: ela mostra os pacotes ativos e leva o cliente para o pagamento." }],
    relacionados: ["conectar-viajeon", "precos-e-pacotes"]
  },

  // ───────────── Captação de leads ─────────────
  {
    id: "criar-formulario",
    modulo: "leads",
    titulo: "Criar um formulário de captação",
    resumo: "Escolha os campos, o texto e a etapa em que o lead entra no funil.",
    atualizado: "2026-10-09",
    rota: "/admin/leads/forms",
    rotaRotulo: "Ir para Formulários",
    busca: "formulario captacao lead campos nome whatsapp email cpf cidade notificacao inteligente mensagem automatica",
    passos: [
      { titulo: "Clique em Novo formulário", texto: "Em Captação de leads, aba **Formulários**.", tela: 1 },
      { titulo: "Dê um nome interno", texto: "Só você vê. Serve para achar o formulário depois.", tela: 2 },
      { titulo: "Escreva o título e a descrição", texto: "É o que o visitante lê. O **Texto do botão** também muda.", tela: 3 },
      { titulo: "Marque os campos", texto: "Nome completo, Telefone / WhatsApp, E-mail, CPF, Cidade e Data de nascimento. **+ Adicionar campo** cria perguntas livres.", tela: 4 },
      { titulo: "Confira a prévia", tela: 6 },
      { titulo: "Ative a Notificação inteligente", texto: "Manda uma mensagem automática no WhatsApp para quem preencheu. Disponível no plano Escala.", tela: 7 },
      { titulo: "Salve", tela: 8 }
    ],
    blocos: [{ tipo: "dica", texto: "Em **Status inicial do lead**, escolha a etapa do funil em que os leads deste formulário entram." }],
    relacionados: ["formulario-na-pagina", "oportunidades", "viajechat"]
  },
  {
    id: "formulario-na-pagina",
    modulo: "leads",
    titulo: "Captar leads na página",
    resumo: "Use a seção Formulário de contato ou abra o formulário antes da página.",
    atualizado: "2026-10-09",
    rota: "/admin/pages",
    rotaRotulo: "Abrir uma página",
    busca: "formulario na pagina captacao modal antes de abrir popup lead secao formulario de contato",
    passos: [
      { titulo: "No editor, clique em Captação de leads", tela: 1 },
      { titulo: "Escolha o formulário", texto: "Ele abre antes do visitante ver a página.", tela: 2 },
      { titulo: "Decida se pode fechar sem enviar", texto: "Ligado, o visitante pode pular o formulário.", tela: 3 },
      { titulo: "Teste em Ver prévia", texto: "Depois, salve a página.", tela: 4 }
    ],
    blocos: [
      { tipo: "texto", texto: "Prefere o formulário no meio da página? Adicione a seção **Formulário de contato** (categoria Contato) e escolha o formulário nela." },
      { tipo: "texto", texto: "Cada envio vira uma oportunidade em **Captação de leads > Oportunidades**, com a página de origem." }
    ],
    relacionados: ["criar-formulario", "oportunidades"]
  },
  {
    id: "oportunidades",
    modulo: "leads",
    titulo: "Acompanhar oportunidades",
    resumo: "Mude a etapa, marque ganho ou perda e registre notas de cada atendimento.",
    atualizado: "2026-10-09",
    rota: "/admin/leads/opportunities",
    rotaRotulo: "Ir para Oportunidades",
    busca: "oportunidades leads funil etapa ganho perda valor notas historico atendimento whatsapp filtros colunas",
    passos: [
      { titulo: "Veja o funil", texto: "Cada etapa com o número de contatos e o valor.", tela: 1 },
      { titulo: "Filtre a lista", texto: "Por etapa, status, página de origem ou tempo sem interação. **Colunas** escolhe o que aparece.", tela: 2 },
      { titulo: "Mude a etapa direto na lista", tela: 3 },
      { titulo: "Escolha a nova etapa", texto: "O histórico registra cada mudança.", tela: 4 },
      { titulo: "Abra a oportunidade", tela: 5 },
      { titulo: "Feche o atendimento", texto: "Informe o valor, marque **Ganha** ou **Perdida**, escreva notas e vincule a um cliente.", tela: 6 }
    ],
    blocos: [{ tipo: "dica", texto: "Marque várias linhas para ganhar, perder, mover de etapa ou excluir de uma vez." }],
    relacionados: ["etapas-do-funil", "clientes", "criar-formulario"]
  },
  {
    id: "etapas-do-funil",
    modulo: "leads",
    titulo: "Etapas do funil",
    resumo: "Crie, renomeie, pinte e ordene as etapas do atendimento.",
    atualizado: "2026-10-09",
    rota: "/admin/leads/settings",
    rotaRotulo: "Abrir Configurações",
    busca: "etapas funil status pipeline cor ordem configuracoes kanban",
    passos: [
      { titulo: "Abra Configurações em Captação de leads", texto: "A lista mostra as etapas na ordem do funil.", tela: 1 },
      { titulo: "Arraste para mudar a ordem", tela: 2 },
      { titulo: "Clique em Editar", tela: 3 },
      { titulo: "Troque nome e cor e salve", tela: 4 }
    ],
    blocos: [{ tipo: "texto", texto: "**Nova etapa do funil** cria mais uma. Ao excluir uma etapa, os leads dela passam para **Sem etapa**." }],
    relacionados: ["oportunidades", "criar-formulario"]
  },
  {
    id: "clientes",
    modulo: "leads",
    titulo: "Base de clientes",
    resumo: "O cadastro de cada pessoa, com todas as oportunidades, notas e documentos.",
    atualizado: "2026-10-09",
    rota: "/admin/leads/clients",
    rotaRotulo: "Ir para Clientes",
    busca: "clientes cadastro contato cpf historico documentos notas novo cliente",
    passos: [
      { titulo: "Busque o cliente", texto: "Por nome, CPF, telefone ou e-mail. Filtre também por cidade, período e status.", tela: 1 },
      { titulo: "Abra o cliente", tela: 2 },
      { titulo: "Veja tudo num lugar", texto: "Oportunidades, notas, documentos, histórico e dados. Daqui você chama no WhatsApp ou cria uma oportunidade.", tela: 3 }
    ],
    relacionados: ["oportunidades"]
  },

  // ───────────── Integrações ─────────────
  {
    id: "pixel-meta-google",
    modulo: "integracoes",
    titulo: "Pixel do Meta e Google Analytics",
    resumo: "Cadastre o código uma vez e escolha em cada página o que enviar.",
    atualizado: "2026-10-09",
    rota: "/admin/integracoes/rastreamento",
    rotaRotulo: "Abrir Rastreamento",
    busca: "pixel meta facebook instagram google analytics ga4 rastreamento eventos conversao anuncios tag",
    passos: [
      { titulo: "Clique em Novo código", texto: "Em Integrações, aba **Rastreamento**.", tela: 1 },
      { titulo: "Dê um nome", tela: 2 },
      { titulo: "Escolha Meta ou Google", tela: 3 },
      { titulo: "Cole o código", texto: "O número do pixel do Meta ou o código G- do Google Analytics.", tela: 4 },
      { titulo: "Salve", tela: 5 },
      { titulo: "Na página, abra Rastreamento", texto: "No editor, ícone **Rastreamento** da barra de configurações.", tela: 6 },
      { titulo: "Escolha o pixel e os eventos", texto: "**Page view**, **Cliques em CTAs** e **Leads** (envios de formulário). Salve a página.", tela: 7 }
    ],
    blocos: [{ tipo: "texto", texto: "O número de códigos depende do plano: 1 no Profissional e até 3 no Agência." }],
    relacionados: ["publicar-pagina", "formulario-na-pagina"],
    substituiAulas: ["pixel do meta", "pixel do facebook", "configurar o pixel", "configurando o pixel"]
  },
  {
    id: "conectar-viajeon",
    modulo: "integracoes",
    titulo: "Conectar o Viaje On",
    resumo: "Mostre os pacotes ativos do Viaje On nas suas páginas.",
    atualizado: "2026-10-09",
    rota: "/admin/integracoes/viajeon",
    rotaRotulo: "Abrir Viaje On",
    busca: "viaje on viajeon token secret checkout pacotes integrar conectar",
    passos: [
      { titulo: "Clique em Conectar Viaje On", texto: "Em Integrações, aba **Viaje On**.", tela: 1 },
      { titulo: "Cole o token e o secret", texto: "Gerados no painel do Viaje On. O secret fica guardado de forma criptografada.", tela: 2 },
      { titulo: "Clique em Conectar e testar", texto: "Com a conexão ativa, a seção **Compra Online (Viaje On)** fica liberada no editor.", tela: 3 }
    ],
    relacionados: ["compra-online"]
  },
  {
    id: "viajechat",
    modulo: "integracoes",
    titulo: "Enviar leads para o ViajeChat",
    resumo: "Os leads dos formulários entram no funil do ViajeChat com etiqueta e campos.",
    atualizado: "2026-10-09",
    rota: "/admin/integracoes/viajechat",
    rotaRotulo: "Abrir ViajeChat",
    busca: "viajechat crm chave api funil coluna etiqueta enviar leads destino do lead",
    passos: [
      { titulo: "Cole a chave da API", texto: "Em Integrações, aba **ViajeChat**. A chave é gerada nas configurações do ViajeChat.", tela: 1 },
      { titulo: "Clique em Conectar", tela: 2 },
      { titulo: "Escolha o destino em cada formulário", texto: "Em **Captação de leads > Formulários**, edite o formulário e use a aba **Destino do Lead**: funil, coluna, etiqueta e campos.", tela: 3 }
    ],
    relacionados: ["criar-formulario", "whatsapp-da-agencia"]
  },
  {
    id: "whatsapp-da-agencia",
    modulo: "integracoes",
    titulo: "Conectar o WhatsApp da agência",
    resumo: "O número usado no atendimento e nas mensagens automáticas dos formulários.",
    atualizado: "2026-10-09",
    rota: "/admin/integracoes/atendimento",
    rotaRotulo: "Abrir WhatsApp",
    busca: "whatsapp qr code conectar numero atendimento mensagens automaticas desconectado",
    passos: [
      { titulo: "Veja a situação da conexão", texto: "Em Integrações, aba **WhatsApp**.", tela: 1 },
      { titulo: "Conecte pelo QR Code", texto: "Clique em **Conectar WhatsApp** e, no celular, abra WhatsApp > Aparelhos conectados > Conectar aparelho.", tela: 2 },
      { titulo: "Confira o status", texto: "**Atualizar status** mostra se a conexão continua ativa.", tela: 3 }
    ],
    blocos: [
      { tipo: "texto", texto: "Cada agência pode ter uma conexão de WhatsApp." },
      { tipo: "atencao", texto: "Se desconectar, as mensagens automáticas param até você conectar de novo." }
    ],
    relacionados: ["criar-formulario", "viajechat"]
  },

  // ───────────── Agência ─────────────
  {
    id: "configurar-agencia",
    modulo: "agencia",
    titulo: "Configurar os dados da agência",
    resumo: "Nome, link, cor, WhatsApp, logo e redes: tudo que aparece nas suas páginas.",
    atualizado: "2026-10-09",
    rota: "/admin/agency",
    rotaRotulo: "Abrir Minha Agência",
    busca: "agencia dados nome logo cor whatsapp email cnpj endereco redes sociais instagram cadastur link da agencia",
    passos: [
      { titulo: "Abra Minha Agência", texto: "Confira o **Nome da agência**: ele aparece no topo e no rodapé das páginas.", tela: 1 },
      { titulo: "Escreva o resumo da agência", texto: "Aparece no rodapé das páginas.", tela: 2 },
      { titulo: "Confira o link da agência", texto: "É o começo do endereço de todas as páginas: roteiroonline.com/link-da-agencia/nome-da-pagina.", tela: 3 },
      { titulo: "Escolha a cor principal", texto: "A base dos botões. Dá para ajustar em cada página.", tela: 4 },
      { titulo: "Informe o WhatsApp", texto: "O número padrão dos botões de WhatsApp das páginas.", tela: 5 },
      { titulo: "Envie o logo e as redes sociais", texto: "Logo com fundo transparente fica bem em qualquer cor.", tela: 6 },
      { titulo: "Salve", texto: "A barra de salvar aparece embaixo quando há mudanças.", tela: 7 }
    ],
    blocos: [{ tipo: "atencao", texto: "Trocar o link da agência muda o endereço de todas as páginas. Os links antigos param de funcionar." }],
    relacionados: ["criar-pagina", "dominio-proprio", "equipe"]
  },
  {
    id: "equipe",
    modulo: "agencia",
    titulo: "Convidar pessoas para a equipe",
    resumo: "Dê acesso ao painel com o nível certo para cada pessoa.",
    atualizado: "2026-10-09",
    rota: "/admin/agency/team",
    rotaRotulo: "Abrir Equipe",
    busca: "equipe usuarios convidar colaborador acesso permissao admin editor visualizador personalizado",
    passos: [
      { titulo: "Clique em Convidar pessoa", texto: "Em Minha Agência, aba **Equipe**.", tela: 1 },
      { titulo: "Informe nome e e-mail", texto: "A pessoa recebe um e-mail para criar a senha e entrar.", tela: 2 },
      { titulo: "Escolha o nível de acesso", texto: "**Admin** acessa tudo, inclusive equipe e faturas. **Editor** cuida de páginas e leads. **Visualizador** só consulta. **Personalizado** você escolhe área por área.", tela: 4 },
      { titulo: "Clique em Enviar convite", tela: 5 }
    ],
    blocos: [{ tipo: "texto", texto: "O número de pessoas depende do plano. O total aparece em **Usuários extras**." }],
    relacionados: ["configurar-agencia", "perfil-e-senha"]
  },
  {
    id: "dominio-proprio",
    modulo: "agencia",
    titulo: "Usar um domínio próprio",
    resumo: "Publique as páginas no endereço da sua agência, como viagens.suaagencia.com.br.",
    atualizado: "2026-10-09",
    rota: "/admin/domains",
    rotaRotulo: "Abrir Domínios",
    busca: "dominio proprio personalizado dns cname endereco url favicon icone da aba",
    passos: [
      { titulo: "Digite o endereço", texto: "Só o endereço, sem https://.", tela: 1 },
      { titulo: "Marque se ele vira o principal", texto: "As páginas passam a abrir neste endereço quando ele for ativado.", tela: 2 },
      { titulo: "Clique em Adicionar domínio", texto: "Em seguida aparecem os registros de DNS para configurar onde o domínio foi registrado.", tela: 3 },
      { titulo: "Envie o ícone da aba", texto: "Com o domínio ativo, o favicon aparece na aba do navegador.", tela: 4 }
    ],
    blocos: [
      { tipo: "texto", texto: "Domínio próprio é um recurso do plano Escala." },
      { tipo: "dica", texto: "A propagação do DNS pode levar algumas horas. Use **Atualizar** para conferir a situação." }
    ],
    relacionados: ["titulo-e-link", "configurar-agencia"]
  },
  {
    id: "faturas",
    modulo: "agencia",
    titulo: "Faturas do plano",
    resumo: "Faturas a vencer, vencidas e pagas, com o link de pagamento.",
    atualizado: "2026-10-09",
    rota: "/admin/agency/invoices",
    rotaRotulo: "Abrir Faturas",
    busca: "faturas boleto pagamento cobranca vencida paga nota",
    passos: [
      { titulo: "Veja o resumo", texto: "A vencer, vencidas e pagas.", tela: 1 },
      { titulo: "Filtre por situação", tela: 2 },
      { titulo: "Pague pelo link da fatura", tela: 3 }
    ],
    relacionados: ["plano-e-assinatura"]
  },

  // ───────────── Sua conta ─────────────
  {
    id: "perfil-e-senha",
    modulo: "conta",
    titulo: "Perfil e senha",
    resumo: "Seus dados, sua foto e a troca de senha.",
    atualizado: "2026-10-09",
    rota: "/admin/perfil",
    rotaRotulo: "Abrir Perfil",
    busca: "perfil senha trocar alterar foto nome telefone conta",
    passos: [
      { titulo: "Confira o plano", texto: "Plano atual, próxima renovação e forma de pagamento.", tela: 1 },
      { titulo: "Atualize seus dados", texto: "Nome, foto e telefone. Clique em **Salvar dados**.", tela: 2 },
      { titulo: "Troque a senha", texto: "Pelo menos 8 caracteres, com maiúsculas, minúsculas e um número.", tela: 3 }
    ],
    duvidas: [["Esqueci a senha", "Na tela de entrada, use **Esqueci minha senha** para receber um link por e-mail."]],
    relacionados: ["plano-e-assinatura", "equipe"]
  },
  {
    id: "plano-e-assinatura",
    modulo: "conta",
    titulo: "Planos e assinatura",
    resumo: "Compare os planos e mude o seu quando quiser.",
    atualizado: "2026-10-09",
    rota: "/admin/planos",
    rotaRotulo: "Ver planos",
    busca: "plano assinatura upgrade downgrade profissional agencia escala renovar cancelar preco",
    passos: [
      { titulo: "Veja o plano atual", texto: "No Perfil, com a próxima renovação e a forma de pagamento.", tela: 1 },
      { titulo: "Clique em Ver planos", tela: 2 },
      { titulo: "Compare e mude", texto: "O plano atual aparece marcado.", tela: 3 }
    ],
    blocos: [
      {
        tipo: "tabela",
        colunas: ["Plano", "Páginas publicadas", "Destaques"],
        linhas: [
          ["Profissional", "Até 3", "1 pixel, botão de WhatsApp em cada seção, galeria de fotos."],
          ["Agência", "Até 10", "Até 3 pixels, duplicação de páginas e o módulo de leads."],
          ["Escala", "Sem limite", "Vários destinos ao mesmo tempo e domínio próprio."]
        ]
      },
      { tipo: "texto", texto: "Ao cancelar a renovação, o plano segue ativo até o fim do período pago." }
    ],
    relacionados: ["faturas", "perfil-e-senha"]
  }
];
