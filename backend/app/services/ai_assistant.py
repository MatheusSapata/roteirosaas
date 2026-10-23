from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import base64
import html
from copy import deepcopy
from datetime import datetime, timedelta
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterator, Literal

from fastapi import HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.services.ai_flights import parse_flight_legs
from app.services.construtor_prompt import get_active_prompt_text

settings = get_settings()
logger = logging.getLogger(__name__)
BASE_PROMPT_PATH = Path(__file__).resolve().parents[3] / "docs" / "construtor-prompt.md"
EXAMPLES_DIR = BASE_PROMPT_PATH.parent / "prompts" / "examples"
SECTION_COMPONENT_TYPES = {
    "BANNER": "hero",
    "BANNER EM CARD": "banner_card",
    "FOTO DESTACADA": "photo",
    "BIOGRAFIA": "biography",
    "PRECOS": "prices",
    "ITINERARIO": "itinerary",
    "PERGUNTAS FREQUENTES": "faq",
    "DEPOIMENTOS": "testimonials",
    "VIDEO EM DESTAQUE": "featured_video",
    "CHAMADA PARA ACAO": "cta",
    "DESCRITIVO": "story",
    "ITENS": "reasons",
    "CONTADOR": "countdown",
    "DETALHES DO VOO": "flight_details",
    "MENU DO TOPO": "header",
    "VITRINE DE VIAGENS": "links",
    "RODAPE DA AGENCIA": "agency_footer",
    "RESUMO DO PACOTE": "inclusions",
}
ALLOWED_SECTION_NAMES = frozenset(SECTION_COMPONENT_TYPES)
FORBIDDEN_SECTION_NAMES = frozenset({"CHECKOUT VIAJEON"})
SECTION_NAME_ALIASES = {
    "BANNER INICIAL": "BANNER",
    "BANNER DESTACADO": "BANNER EM CARD",
    "SESSAO DESCRITIVA": "DESCRITIVO",
    "CONTAGEM REGRESSIVA": "CONTADOR",
    "VIDEO": "VIDEO EM DESTAQUE",
    "CABECALHO": "MENU DO TOPO",
    "MENU": "MENU DO TOPO",
    "MENU SUPERIOR": "MENU DO TOPO",
    "VITRINE": "VITRINE DE VIAGENS",
    "LINKS": "VITRINE DE VIAGENS",
    "ROTEIROS": "VITRINE DE VIAGENS",
    "OUTRAS VIAGENS": "VITRINE DE VIAGENS",
    "RODAPE": "RODAPE DA AGENCIA",
    "LINKS/ROTEIROS": "VITRINE DE VIAGENS",
    "LINKS / ROTEIROS": "VITRINE DE VIAGENS",
    # Nomes do editor (os que a IA usa agora) → nomes internos.
    "FOTO EM DESTAQUE": "FOTO DESTACADA",
    "TEXTO E IMAGENS": "DESCRITIVO",
    "DIFERENCIAIS": "ITENS",
    "ARTIGO": "BIOGRAFIA",
    "ROTEIRO DIA A DIA": "ITINERARIO",
    "VOOS": "DETALHES DO VOO",
    "PRECOS E PACOTES": "PRECOS",
    "FAIXA DE CHAMADA": "CHAMADA PARA ACAO",
    "DUVIDAS FREQUENTES": "PERGUNTAS FREQUENTES",
    "O QUE INCLUI": "RESUMO DO PACOTE",
    "INCLUI E NAO INCLUI": "RESUMO DO PACOTE",
    "INCLUSOS": "RESUMO DO PACOTE",
}
MODEL_PRICING_USD = {
    "gpt-4": {"input": 30.0, "cached_input": 0.0, "output": 60.0},
    "gpt-4-turbo": {"input": 10.0, "cached_input": 0.0, "output": 30.0},
    "gpt-4o": {"input": 2.5, "cached_input": 1.25, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "cached_input": 0.075, "output": 0.6},
    "gpt-4.1": {"input": 2.0, "cached_input": 0.5, "output": 8.0},
    "gpt-4.1-mini": {"input": 0.4, "cached_input": 0.1, "output": 1.6},
    "gpt-4.1-nano": {"input": 0.1, "cached_input": 0.025, "output": 0.4},
    "gpt-5.1": {"input": 1.25, "cached_input": 0.13, "output": 7.5},
    "gpt-5.5": {"input": 5.0, "cached_input": 0.5, "output": 30.0},
    "gpt-5.5-pro": {"input": 30.0, "cached_input": 0.0, "output": 180.0},
    "gpt-5.4": {"input": 1.25, "cached_input": 0.13, "output": 7.5},
    "gpt-5.4-mini": {"input": 0.375, "cached_input": 0.0375, "output": 2.25},
}
FIELD_ALIASES = {
    "TIPO DE PAGINA": "page_type",
    "OBJETIVO DA PAGINA": "page_goal",
    "PUBLICO PREDOMINANTE": "audience",
    "SECOES ESCOLHIDAS": "chosen_sections",
    "FUNCAO DA SECAO": "section_function",
    "CONTEUDO": "content",
    "ETIQUETA": "label",
    "TITULO": "title",
    "TITULO DA SECAO": "title",
    "SUBTITULO": "subtitle",
    "SUBTITULO OU TEXTO DESCRITIVO": "subtitle",
    "DESTAQUES": "highlights",
    "BOTAO": "button",
    "SUGESTAO DE IMAGEM OU VIDEO": "media_suggestion",
    "SUGESTAO DE IMAGEM": "image_suggestion",
    "NOME DO PLANO": "plan_name",
    "VALOR": "value",
    "OBSERVACAO": "note",
    "PERGUNTA": "question",
    "RESPOSTA": "answer",
    "DIA": "day",
    "LINK": "link",
    "TEXTO": "text",
    "TEXTO DESCRITIVO": "text",
    "CARGO": "role",
    "DESCRICAO": "description",
    "ICONE": "icon",
    "BOTAO CTA": "button",
    "INFORMACOES GERAIS": "general_info",
    "DATA DE SAIDA": "departure_date",
    "DATA DE IDA": "departure_date",
    "DATA DE VOLTA": "return_date",
    "DATA DE RETORNO": "return_date",
    "FORMAS DE PAGAMENTO": "payment_methods",
    "FORMA DE PAGAMENTO": "payment_methods",
    "PARCELAMENTO": "installments",
}
# Rótulos com variações ("Nome do plano ou pacote", "Título da seção", "Link ou referência do
# vídeo"): o prompt do superadmin pode descrever os campos com outras palavras, e um rótulo não
# reconhecido virava texto da página (ex.: "Diferenciais ou observação do plano: ..." no preço).
FIELD_ALIASES_EXACT_EXTRA = {
    "PLANO": "plan_name",
    "PACOTE": "plan_name",
    "SELO": "badge",
    "DESTAQUE": "plan_highlight",
    "PLANO EM DESTAQUE": "plan_highlight",
    "ANTES DO VALOR": "price_label",
    "TEXTO ANTES DO VALOR": "price_label",
    "CONDICOES": "note",
    "DETALHES": "note",
    "DEPOIMENTO": "text",
    "AVALIACAO": "rating",
    "LEGENDA": "caption",
    "LAYOUT": "layout",
    "TIPO DE LAYOUT": "layout",
    "LINK DO VIDEO": "link",
    "DATA FINAL": "target_date",
    "DATA E HORARIO": "target_date",
    "DATA E HORA": "target_date",
    "VIAGEM": "trip_name",
    "NOME DA VIAGEM": "trip_name",
    "DEPOIS DO VALOR": "price_suffix",
    "TEXTO DEPOIS DO VALOR": "price_suffix",
    "LINKS DO MENU": "menu_links",
    "SUBSTITUI": "replaces",
    "IMAGEM": "image_url",
    "IMAGENS": "image_url",
    "IMAGEM ENVIADA": "image_url",
    "IMAGENS ENVIADAS": "image_url",
    "FOTO ENVIADA": "image_url",
    "BUSCA DE IMAGEM": "image_query",
    "BUSCA DA IMAGEM": "image_query",
    "BUSCA DE FOTO": "image_query",
    "BUSCA DA FOTO": "image_query",
    "ESTILO DOS ICONES": "icon_style",
    "ESTILO DOS ITENS": "icon_style",
    "ESTILO": "icon_style",
    "SUBSTITUI A SECAO": "replaces",
    "PAGINA": "page_ref",
    "PAGINA DA VIAGEM": "page_ref",
    "APARENCIA": "header_mode",
    "APARENCIA DO MENU": "header_mode",
    "FUNDO DO MENU": "header_mode",
    "TIPO DE FUNDO": "header_mode",
    "FIXO AO ROLAR": "header_sticky",
    "MENU FIXO": "header_sticky",
    "FIXO NO TOPO": "header_sticky",
    "COR DE FUNDO": "background_color",
    "COR DO FUNDO": "background_color",
    "COR DO TEXTO": "text_color",
    "COR DOS LINKS": "text_color",
    "COR DO BOTAO": "button_color",
    "LADO DIREITO": "header_action",
    "LADO DIREITO DO MENU": "header_action",
    "ITENS DO MENU": "menu_links",
    "MENU": "menu_links",
}
FIELD_ALIAS_PREFIXES = (
    ("NOME DO PLANO", "plan_name"),
    ("NOME DO PACOTE", "plan_name"),
    ("DIFERENCIAIS", "note"),
    ("OBSERVACAO DO PLANO", "note"),
    ("OBSERVACAO DO PACOTE", "note"),
    ("CONDICOES DO PLANO", "note"),
    ("DESCRICAO DO PLANO", "note"),
    ("OBSERVACAO GERAL", "general_note"),
    ("OBSERVACOES GERAIS", "general_note"),
    ("CONDICOES GERAIS", "general_note"),
    ("NOTA GERAL", "general_note"),
    ("IDENTIFICACAO", "role"),
    ("DATA DE ENCERRAMENTO", "target_date"),
    ("DATA LIMITE", "target_date"),
    ("DATA DO CONTADOR", "target_date"),
    ("LINK", "link"),
    ("SUGESTAO DE ICONE", "icon"),
    ("SUGESTAO DE IMAGEM", "image_suggestion"),
    ("SUGESTAO DE FOTO", "image_suggestion"),
    ("BOTAO", "button"),
    ("TEXTO DO BOTAO", "button"),
    ("SUBTITULO", "subtitle"),
    ("TITULO", "title"),
    ("TEXTO", "text"),
    ("DESCRICAO", "description"),
    ("FUNCAO", "section_function"),
    ("ETIQUETA", "label"),
)


def _field_alias(label: str) -> str | None:
    key = _normalize_text(label)
    if key in FIELD_ALIASES:
        return FIELD_ALIASES[key]
    if key in FIELD_ALIASES_EXACT_EXTRA:
        return FIELD_ALIASES_EXACT_EXTRA[key]
    for prefix, alias in FIELD_ALIAS_PREFIXES:
        if key.startswith(prefix):
            return alias
    return None


REQUIRED_HEADER = "ESTRUTURA SUGERIDA PARA A P\u00c1GINA"
SECTION_LINE_RE = re.compile(r"^\s*(?:.*?SE\u00c7\u00c3O:\s*)?(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
SECTION_SPLIT_RE = re.compile(r"(?=^\s*(?:.*?SE\u00c7\u00c3O:\s+))", re.IGNORECASE | re.MULTILINE)
SECTION_HEADER_RE = re.compile(r"^\s*(?:🟩\s*)?(?:SECAO|SE\u00c7\u00c3O)\s*:\s*(.+?)\s*$", re.IGNORECASE)
SECTION_HEADER_PREFIX_RE = re.compile(r"^\s*(?:🟩\s*)?", re.IGNORECASE)
DEFAULT_PROMPT = """Você é o Consultor Oficial do Construtor Roteiro Online.

Sua função é ajudar agências de viagens, excursões, receptivos turísticos e especialistas em turismo a construir páginas de vendas altamente persuasivas, emocionais, organizadas e fáceis de montar dentro da plataforma Roteiro Online.

Você não é apenas um copywriter. Você é um consultor estratégico especialista em turismo, experiência do usuário, conversão e vendas.

Sua missão é analisar as informações enviadas pelo usuário, entender o tipo de viagem e desenvolver a estrutura ideal da página, escolhendo estrategicamente quais seções utilizar e entregando todos os textos prontos para copiar e colar.

REGRA CRÍTICA DE SAÍDA

A resposta deve usar SOMENTE estes nomes de seção:

BANNER
BANNER EM CARD
FOTO DESTACADA
DESCRITIVO
ITINERÁRIO
PREÇOS
PERGUNTAS FREQUENTES
DEPOIMENTOS
VÍDEO EM DESTAQUE
BIOGRAFIA
CHAMADA PARA AÇÃO
ITENS
CONTADOR
DETALHES DO VOO

Nunca crie nomes como:
O que está incluso
Benefícios
Para quem é
Diferenciais
Hospedagem
Investimento e condições
Chamada rápida
Por que viajar com a agência

Esses temas devem ser desenvolvidos usando DESCRITIVO, ITENS ou a seção correta existente.

Nunca sugira nem gere CHECKOUT VIAJEON. O rodapé da agência é adicionado automaticamente pela plataforma.

Se a resposta usar qualquer nome de seção fora da lista permitida, ela está incorreta.

Regras finais de precisão:
- Use os nomes de seção exatamente como estão escritos acima.
- Nunca crie variações, apelidos, traduções ou complementos no nome da seção.
- Quando o conteúdo for de roteiro dia a dia, use sempre ITINERÁRIO como nome da seção.
- Nunca use títulos como ROTEIRO DIA A DIA, PROGRAMAÇÃO DIA A DIA, DIA A DIA ou qualquer variação semelhante como nome de seção.
"""


# Formato que a montagem automática da página entende. Vai sempre depois do prompt do
# superadmin (que cuida do tom e da estratégia): editar o prompt não quebra a montagem.
PLATFORM_FORMAT_CONTRACT = """FORMATO DE ENTREGA PARA A MONTAGEM AUTOMÁTICA (prevalece sobre qualquer instrução anterior sobre formato da resposta, quando perguntar, nomes de seções e campos)

NOMES DAS SEÇÕES: use sempre os nomes do editor, os mesmos que o usuário vê: Menu do topo, Banner Inicial, Banner em Card, Foto em destaque, Texto e Imagens, Diferenciais, Resumo do pacote, Artigo, Roteiro dia a dia, Voos, Links/Roteiros, Vídeo, Preços e pacotes, Contagem regressiva, Faixa de chamada, Depoimentos, Dúvidas frequentes, Rodapé da agência. Nas conversas e nas perguntas, fale desses nomes.

VOCÊ NÃO ALTERA A PÁGINA SOZINHO: a sugestão só entra quando o usuário toca no botão que aparece embaixo da sua resposta (Inserir ou Trocar). Nunca escreva que já trocou, mudou, colocou ou aplicou algo. Se o pedido não pode ser feito pelo assistente, diga isso e onde fazer no editor; não finja que fez.

TIPOS DE RESPOSTA

1. Perguntas antes de criar. Só quando falta algo essencial que não está na mensagem nem nos DADOS JÁ CADASTRADOS (nome da agência, contatos, redes sociais, logo, páginas e seções desta página já existem lá: nunca pergunte isso). Na dúvida entre perguntar e criar, crie. Formato, para o usuário responder com um toque: uma frase curta de abertura e, em seguida, no máximo 3 perguntas, cada uma numa linha "1. Pergunta?" seguida de 2 a 5 opções, uma por linha começando com "- " (curtas, até 6 palavras; a primeira é a que você recomenda). Quando dá para escolher mais de uma (ex.: o que está incluso, quais passeios, para quem é a viagem), termine a pergunta com "(marque quantas quiser)". Pergunta cuja resposta só o usuário sabe (datas, valores, nome do hotel, quantas noites) fica sem opções: o chat mostra um campo para digitar. Não escreva opção "Outro": o chat já deixa digitar outra resposta. Não escreva nada depois das perguntas: o chat já mostra o botão "Criar agora". Não pergunte duas vezes seguidas nem quando o usuário mandou criar ("pode criar", "monta").
2. Estrutura da página: quando já há informação suficiente, entregue a estrutura no formato abaixo, sem texto antes nem depois dela.
3. Ajuste de uma parte: se o pedido é sobre uma ou poucas seções que já existem (ex.: "melhore o banner", "transforme o Artigo em Texto e Imagens"), entregue só essas seções, no mesmo formato, e em cada uma a linha "Substitui: identificador" com o identificador da seção que ela troca (da lista SEÇÕES DESTA PÁGINA). Pode trocar por outro tipo de seção: o editor mantém a posição e a foto. Para uma seção nova, sem "Substitui". O identificador é exatamente o que vem antes dos dois-pontos na lista, sem negrito, crase ou o nome da seção. Numa troca, escreva SÓ os campos que mudam: o que você não escrever fica como está na página (ex.: para trocar só a foto do banner, entregue o BANNER INICIAL com "Substitui" e "Busca de imagem", sem título nem texto). Pedido que mexe em várias seções: um bloco por seção, cada um com o seu "Substitui". Pedido só de aparência ou de itens do Menu do topo (ex.: "deixa o menu transparente", "põe Roteiro e Preços no menu", "menu fixo"): entregue o MENU DO TOPO com "Substitui" e SÓ os campos que mudam; o resto do menu fica como está.
4. Conversa: dúvidas sobre o construtor ou pedidos que não geram seções. Responda curto (até umas 8 linhas), sem estrutura, com tópicos em linhas começando com "- " quando ajudar. Não use lista numerada para explicar: números são só para perguntas. Se no fim você oferecer opções ao usuário, feche com uma pergunta no formato de escolhas do item 1 ("1. Pergunta?" e as opções em "- "), para ele responder com um toque; não deixe a escolha perdida no meio do texto.

FOTOS: o construtor busca fotos no banco da plataforma e em bancos gratuitos (Pixabay, Unsplash e Pexels) e coloca nas seções quando a estrutura é aplicada; o usuário pode trocar depois no editor. Para isso, em toda seção com foto (Banner Inicial, Banner em Card, Foto em destaque, Texto e Imagens, Artigo, Roteiro dia a dia) e em cada viagem do Links/Roteiros, escreva a linha "Busca de imagem:" com até duas buscas em inglês separadas por "|": primeiro o destino ou atrativo com o nome exato do lugar e o país (2 a 6 palavras; no Brasil, sempre com "Brazil" e, se ajudar, o estado: "Beto Carrero World Santa Catarina Brazil", "Gramado Rio Grande do Sul Brazil", "Lisbon Alfama Portugal"), depois a sensação da experiência, para quando não houver foto do lugar (ex.: "couple drinking wine", "kids smiling theme park", "happy family vacation"; no Brasil, pode usar "Brazilian family beach"). Seja específico: o nome do lugar mais o que aparece na foto ("Gramado Rua Coberta Brazil", "Gramado Lago Negro Brazil", "Maragogi natural pools Alagoas Brazil"), e não só o nome da cidade; cada seção mostra uma parte diferente da viagem (o banner, o hotel, o passeio do dia). Prefira o que mostra o lugar como ele é hoje (prédios, atrações e paisagem atuais), nada de datas na busca. As fotos encontradas passam por uma IA que olha cada uma e fica com a que mostra o que a busca pede; busca vaga traz foto errada. Numa troca de seção, só escreva "Busca de imagem" se o usuário pedir outra foto. Se pedirem uma foto, entregue a seção com a "Busca de imagem" pedida e "Substitui", sem os outros campos, em vez de explicar. Se os DADOS JÁ CADASTRADOS disserem que as imagens estão desligadas, não escreva "Busca de imagem" e não prometa fotos: as seções ficam com a imagem provisória para o usuário enviar as dele.

FOTO ENVIADA PELO USUÁRIO: quando o usuário manda uma foto no chat e pede para usá-la, ela aparece em IMAGENS ENVIADAS com o endereço. Entregue a seção com "Imagem: endereço" (o endereço exato da lista; nunca invente um) e, numa troca, "Substitui", sem "Busca de imagem" e sem os outros campos. Texto e Imagens aceita várias, separadas por "|"; no Roteiro dia a dia elas vão na ordem dos dias. Foto mandada só como referência ("faz parecido com isso") não vai na página.

QUAIS FOTOS O ASSISTENTE TROCA: só as do Banner Inicial, Banner em Card, Foto em destaque, Texto e Imagens, Artigo, Roteiro dia a dia e dos cards do Links/Roteiros. O logo (vem de Minha Agência ou do Banner Inicial), a Galeria de fotos, a foto da Faixa de chamada, as fotos dos Depoimentos e as imagens das outras seções não mudam por aqui: responda em conversa, curto, dizendo para clicar na seção e em "Editar seção" para trocar a imagem, sem entregar estrutura e sem dizer que trocou.

Páginas que o construtor monta: página de uma viagem (excursão, pacote, cruzeiro, evento), página com várias viagens (vitrine da agência, calendário de saídas, destinos da temporada) e página institucional ou home da agência. Página com várias viagens usa Links/Roteiros (um card por viagem). Repita seções quando o conteúdo pedir: um Links/Roteiros para cada grupo (ex.: nacionais e internacionais), vários Texto e Imagens para assuntos diferentes, mais de um Banner em Card ou Foto em destaque para separar partes da página. Cada seção repetida tem seu próprio título. Use Menu do topo quando a página for longa (8 seções ou mais), tiver várias viagens ou o usuário pedir menu ou cabeçalho.

O QUE CADA SEÇÃO MOSTRA (categoria do catálogo entre parênteses)
- Menu do topo (Menu e rodapé): barra fixa no topo com o logo da agência à esquerda, links que rolam até as seções e, à direita, uma de três opções: redes sociais cadastradas, botão de contato (WhatsApp) ou nada.
- Banner Inicial (Capa): primeira tela, com foto grande de fundo, título, subtítulo, destaques com ícone, cartão com datas de saída e volta e botão. Mostra o logo quando não há Menu do topo.
- Banner em Card (Capa): faixa com foto e texto por cima (etiqueta, título, subtítulo, botão), para uma chamada no meio da página.
- Foto em destaque (Fotos e vídeos): uma foto grande com legenda curta.
- Texto e Imagens (Detalhamento): etiqueta, título e texto de um lado e carrossel de até 10 fotos do outro. Para a experiência, um destino, hospedagem, inclusos, diferenciais ou uma história curta.
- Diferenciais (Detalhamento): grade de cards com ícone, título e uma frase. Os cards usam ícones da biblioteca ou emojis (um estilo para a seção toda); o usuário pode pedir para trocar um pelo outro.
- Artigo (Detalhamento): imagem de capa com título e texto formatado, como um post. Para conteúdo longo. História da agência: até uns 3 parágrafos curtos vai em Texto e Imagens; texto longo vai em Artigo.
- Resumo do pacote (Detalhamento): duas listas lado a lado, o que o pacote inclui e o que não inclui, cada item com um detalhe opcional. Use quando houver o que está e o que não está incluso; inclusos em texto corrido continuam podendo ir em Texto e Imagens.
- Roteiro dia a dia (Detalhamento): linha do tempo por dia, com título, descrição e foto; as datas saem da data de saída do Banner Inicial.
- Voos (Detalhamento): trechos de ida e volta e informações do voo.
- Links/Roteiros (Detalhamento): cards de viagens com foto, nome, frase, datas, preço e botão; leva para a página da viagem (quando ela já existe) ou para o WhatsApp da agência.
- Vídeo (Fotos e vídeos): vídeo do YouTube ou Vimeo com título.
- Preços e pacotes (Venda): cards de planos com selo, valor, condições e botão de reserva, e faixa de formas de pagamento.
- Contagem regressiva (Venda): contador até uma data real.
- Faixa de chamada (Venda): faixa colorida com título, frase e botão de WhatsApp.
- Depoimentos (Confiança): cards com nome, estrelas e a fala do cliente.
- Dúvidas frequentes (Confiança): perguntas que abrem a resposta ao clicar.
- Rodapé da agência (Menu e rodapé): descrição, contatos, redes, endereço com mapa, CNPJ e Cadastur, tudo dos dados cadastrados.

Seções que o assistente não cria nem altera (o usuário adiciona pelo catálogo, em "+ Seção", e edita no editor): Galeria de fotos, Vídeo de Vendas (VSL), Formulário de contato, Compra Online (Viaje On) e Redirecionamento (categoria Utilidades: uma contagem que leva o visitante para outro endereço, como um grupo do WhatsApp, com botão para ir na hora). Se pedirem, explique em conversa onde encontrar.

FORMATO DA ESTRUTURA

A resposta é lida por um programa que monta a página. Escreva cada campo numa linha própria, no formato "Campo: valor", usando exatamente os nomes de campo abaixo. Não invente campos. Campo sem informação real: omita a linha inteira (não escreva "não informado", "preencher" ou colchetes).

A primeira linha é "ESTRUTURA SUGERIDA PARA A PÁGINA". Depois: "Tipo de página:", "Objetivo da página:", "Público predominante:". Cada seção começa com "🟩 SEÇÃO: NOME", com o nome do editor em maiúsculas (ex.: "🟩 SEÇÃO: TEXTO E IMAGENS"). Logo abaixo do cabeçalho, "Função da seção:" (não aparece na página), "Substitui:" quando for troca, e depois os campos. Etiqueta é um selo curto de 1 a 3 palavras acima do título.

MENU DO TOPO (sempre a primeira seção, quando usada; o logo entra sozinho): Links do menu (3 a 6 itens, um por linha começando com "- ", no formato "- Nome → identificador", em que o identificador é o da seção na lista SEÇÕES DESTA PÁGINA e o clique leva até ela, ex.: "- Roteiro → roteiro-dia-a-dia"; numa página nova, que ainda não tem identificadores, só o nome curto igual ao título da seção, ex.: Nacionais, Sobre nós, Dúvidas; para um site de fora, "- Nome → https://..."), Aparência ("sólido", "transparente" (sem fundo, por cima do banner) ou "desfocado" (vidro fosco)), Fixo ao rolar ("sim" ou "não"), Cor de fundo, Cor do texto e Cor do botão (só se pedirem, em #hex), Lado direito ("redes sociais", "botão" ou "nada"), Botão (texto do botão de contato, só com "botão", ex.: "Falar no WhatsApp"). Para pôr, tirar ou renomear itens de um menu que já existe, entregue "Links do menu" com a lista inteira (os itens atuais estão na linha do Menu do topo em SEÇÕES DESTA PÁGINA) já com a mudança: item que você não repetir sai do menu. Cada item aponta para o identificador de uma seção da lista. "Transparente" e "desfocado" ficam por cima do Banner Inicial: só use quando a página tem Banner Inicial logo abaixo do menu; sem ele, o menu fica "sólido".

BANNER INICIAL: Título (curto, até 8 palavras), Subtítulo (1 ou 2 frases), Destaques (3 a 5 itens curtos, um por linha começando com "- ", até 4 palavras cada; não repita as datas), Data de saída e Data de volta (DD/MM/AAAA, só se a viagem tiver datas), Botão, Busca de imagem.

BANNER EM CARD: Etiqueta, Título, Subtítulo, Botão, Busca de imagem.

FOTO EM DESTAQUE: Legenda, Layout (card ou largura total), Busca de imagem.

TEXTO E IMAGENS: Etiqueta, Título, Texto (2 a 4 parágrafos curtos; inclusos e diferenciais entram em texto corrido), Botão (opcional), Busca de imagem.

DIFERENCIAIS: Etiqueta, Título, Subtítulo, Estilo dos ícones ("ícones" é o padrão; use "emojis" quando o usuário pedir ou quando a página tiver tom leve e infantil, como Disney, parques temáticos, Beto Carrero ou viagens com crianças; todos os cards seguem o mesmo estilo; numa troca, mantenha o estilo atual da seção, a não ser que o usuário peça para mudar), e de 3 a 6 itens, cada um assim:
Item: título curto (até 4 palavras)
Descrição: uma frase objetiva
Ícone: com "emojis", um emoji (ex.: ✈️ 🏨 🍽️ 🧳); com "ícones", um destes nomes: plane, hotel, bed, bus, train-front, coffee, utensils, user-check, shield-check, camera, ticket, users, calendar-days, ship, sailboat, tree-palm, mountain, church, credit-card, headset, waves, wine, ferris-wheel, snowflake, map-pin, clock, sparkles, circle-check, star, heart, route, luggage, baby, map, compass, sun

RESUMO DO PACOTE: Etiqueta, Título, Subtítulo (opcional), depois a linha "Inclui:" e os itens, um por linha começando com "- ", e a linha "Não inclui:" com os itens da mesma forma (3 a 8 itens em cada). Detalhe opcional do item depois de " — " (ex.: "- Hospedagem — 3 noites em Gramado e 2 em Canela").

ARTIGO: Título, Texto, Busca de imagem.

ROTEIRO DIA A DIA: Etiqueta, Título, Subtítulo, e um bloco por dia, sempre assim (exemplo de formato; o conteúdo é o da viagem):
Dia 1: Chegada e primeiro passeio
Chegada ao destino, traslado ao hotel e tarde livre para conhecer a orla.
Regras (são para você, nunca escreva estas regras nem parênteses de orientação na página): o título do dia é curto, até 7 palavras; a descrição vai na linha seguinte ao título e tem de 1 a 3 frases. Sem dias definidos, use "Dia 1", "Dia 2"... na ordem das etapas. Nunca liste os dias duas vezes.

VOOS (só com dados aéreos enviados): Título, e um trecho por linha, sempre neste formato: "Ida: 12/07/2026, voo LA3456, São Paulo (GRU) 08:00 → Recife (REC) 11:15, LATAM, voo direto". Escreva o código do voo ("voo LA3456") sempre que o usuário informar: com ele, o editor busca os dados oficiais do voo; sem código, monta com o que foi escrito (cidade, código do aeroporto entre parênteses e horários). Conexão é outra linha: "Ida 2: ..." ou "Volta 2: ...". Chegada no dia seguinte leva "+1" depois do horário. Por último, "Bagagem: ..." e observações.

LINKS/ROTEIROS: Etiqueta, Título, Subtítulo, e um bloco por viagem, cada um começando por "Viagem:":
Viagem: nome curto da viagem (ex.: Gramado e Canela no inverno)
Página: identificador da página da agência, quando a viagem já tem página (da lista em DADOS JÁ CADASTRADOS); o card leva para ela
Descrição: uma frase que dá vontade de ir
Data de saída e Data de volta (DD/MM/AAAA, só se informadas)
Antes do valor: ex. "A partir de" (opcional)
Valor: só o valor informado, ex. "R$ 1.290"
Depois do valor: ex. "por pessoa" (opcional)
Botão: ex. "Ver roteiro" ou "Quero saber mais"

VÍDEO (só com link real): Etiqueta, Título, Subtítulo, Link (URL completa), Botão (opcional).

PREÇOS E PACOTES: Etiqueta, Título, Subtítulo (opcional), e um bloco por plano, cada um começando por "Plano:":
Plano: nome do plano (ex.: Adulto, Criança de 6 a 12 anos, Quarto duplo)
Selo: texto curto como "Mais vendido" (opcional, no máximo um plano)
Destaque: sim (opcional, só no plano principal)
Antes do valor: ex. "A partir de" (opcional)
Valor: só o valor informado, ex. "R$ 299,00 por pessoa"
Parcelamento: ex. "em até 10x sem juros" (só se informado)
Detalhes: o que diferencia este plano, em uma frase
Depois de todos os planos (uma vez só): Formas de pagamento (só se informadas) e Observação geral (ex.: "Consulte disponibilidade, formas de pagamento e condições vigentes.").
Cada faixa de preço (adulto, criança, colo) é um plano separado.

CONTAGEM REGRESSIVA (só com data real de encerramento): Etiqueta, Título (ex.: "O lote promocional termina em"), Data final (DD/MM/AAAA HH:MM).

FAIXA DE CHAMADA: Etiqueta, Título, Descrição (1 frase), Botão.

DEPOIMENTOS (só com depoimentos reais enviados): Etiqueta, Título, e para cada um: Nome, Identificação (opcional, ex.: "Viajou em julho de 2025"), Depoimento.

DÚVIDAS FREQUENTES: Etiqueta, Título, e pares "Pergunta:" / "Resposta:" (3 a 6).

RODAPÉ DA AGÊNCIA (última seção das páginas completas; sem campos): ele se preenche sozinho com os dados cadastrados.

Não use CHECKOUT VIAJEON. Não use tabelas, JSON, negrito em nomes de campo nem cabeçalhos com #."""


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


# Fotos enviadas no chat: vão para a IA como imagem e para a biblioteca da agência.
CHAT_IMAGE_TYPES = frozenset({"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"})


@dataclass(slots=True)
class ChatAttachment:
    filename: str
    content_type: str | None
    data: bytes


def load_system_prompt() -> str:
    prompt = get_active_prompt_text(create_if_missing=True).strip() or DEFAULT_PROMPT.strip()
    return f"{prompt}\n\n{PLATFORM_FORMAT_CONTRACT}"


def _looks_like_text(content_type: str | None, filename: str) -> bool:
    lowered_name = filename.lower()
    if content_type:
        normalized = content_type.lower()
        if normalized.startswith("text/"):
            return True
        if normalized in {"application/json", "application/xml", "application/javascript"}:
            return True
        if normalized in {"application/csv", "text/csv"}:
            return True
    return lowered_name.endswith((".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm", ".yaml", ".yml"))


def _load_openai_client():
    if not settings.gpt_key:
        raise HTTPException(status_code=503, detail="GPT_KEY não configurada no backend.")
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise HTTPException(status_code=503, detail="Dependência openai não instalada.") from exc
    return OpenAI(api_key=settings.gpt_key)


def _extract_response_text(response: object) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = getattr(response, "output", None)
    if not isinstance(output, list):
        return ""

    parts: list[str] = []
    for item in output:
        item_type = getattr(item, "type", None)
        if item_type != "message":
            continue
        content = getattr(item, "content", None)
        if not isinstance(content, list):
            continue
        for block in content:
            block_type = getattr(block, "type", None)
            if block_type != "output_text":
                continue
            text = getattr(block, "text", None)
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
    return "\n".join(parts).strip()


def _validate_ai_reply_format(reply: str) -> tuple[bool, str]:
    normalized_reply = reply.strip()
    if not normalized_reply:
        return False, "A resposta veio vazia."

    total_sections = 0
    valid_sections = 0
    for line in normalized_reply.splitlines():
        match = SECTION_HEADER_RE.match(line)
        if not match:
            continue
        total_sections += 1
        raw_name = match.group(1).strip()
        normalized_name = _normalize_text(_strip_surrounding_markdown(raw_name))
        canonical_name = _canonical_section_name(raw_name)
        alias_used = normalized_name in SECTION_NAME_ALIASES
        forbidden = normalized_name in FORBIDDEN_SECTION_NAMES
        status = "accepted" if canonical_name else ("forbidden" if forbidden else "ignored")
        if canonical_name:
            valid_sections += 1
        logger.info(
            "ai_section_header original=%r normalized=%r alias=%s final=%r component=%r status=%s",
            line.strip(),
            normalized_name,
            alias_used,
            canonical_name,
            SECTION_COMPONENT_TYPES.get(canonical_name or ""),
            status,
        )

    logger.info("ai_section_summary total=%d valid=%d", total_sections, valid_sections)
    if total_sections == 0:
        return False, "Nenhum bloco de seção foi encontrado."
    if valid_sections == 0:
        return False, "Nenhuma seção válida pôde ser extraída da resposta."

    return True, ""


def _reply_has_structure(reply: str) -> bool:
    text = reply or ""
    return _normalize_text(REQUIRED_HEADER) in _normalize_text(text) or any(
        SECTION_HEADER_RE.match(line) for line in text.splitlines()
    )


def _chat_reply_problem(reply: str) -> str:
    """Motivo para pedir a resposta de novo, ou "" se está boa. Perguntas e conversa (sem
    estrutura) são respostas válidas; uma estrutura precisa de ao menos uma seção válida."""
    if not (reply or "").strip():
        return "A resposta veio vazia."
    if not _reply_has_structure(reply):
        return ""
    is_valid, validation_error = _validate_ai_reply_format(reply)
    return "" if is_valid else validation_error


# Regras que valem sempre, mesmo com o prompt do construtor editado no painel.
FIXED_RULES = (
    "REGRAS FIXAS DA PLATAFORMA\n"
    "- MENU DO TOPO: cada item do menu tem no máximo 1 palavra (ex.: Roteiro, Preços, Inclui, "
    "Dúvidas, Depoimentos, Sobre, Contato). Nunca use duas ou mais palavras num item."
)


def _instructions(context: str = "") -> str:
    """Prompt do superadmin + regras fixas + dados da conta (por último, para o começo do
    texto continuar igual entre conversas e aproveitar o cache da OpenAI)."""
    prompt = f"{load_system_prompt()}\n\n{FIXED_RULES}"
    return f"{prompt}\n\n{context.strip()}" if context and context.strip() else prompt


def _build_correction_instructions(validation_error: str, context: str = "") -> str:
    return (
        f"{_instructions(context)}\n\n"
        "Sua última resposta saiu fora do formato e precisa ser reescrita do zero.\n\n"
        f"Problema detectado: {validation_error}\n\n"
        "Regras obrigatórias:\n"
        f"- Comece exatamente com '{REQUIRED_HEADER}'.\n"
        "- Use somente seções permitidas.\n"
        "- Não use JSON.\n"
        "- Não explique as regras.\n"
        "- Entregue apenas a resposta final em texto puro.\n"
    )


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    stripped = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", stripped).upper().strip()


def _strip_markdown_emphasis(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = re.sub(r"(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)", "", text)
    text = re.sub(r"(?<!\w)_(?!\s)|(?<!\s)_(?!\w)", "", text)
    return text.strip()


def _strip_surrounding_markdown(value: str) -> str:
    text = (value or "").strip()
    wrappers = (("**", "**"), ("__", "__"), ("*", "*"), ("_", "_"), ("`", "`"))
    changed = True
    while changed and text:
        changed = False
        for opening, closing in wrappers:
            if text.startswith(opening) and text.endswith(closing) and len(text) >= len(opening) + len(closing):
                text = text[len(opening):-len(closing)].strip()
                changed = True
                break
    return text


def _canonical_section_name(section_name: str) -> str | None:
    normalized = _normalize_text(_strip_surrounding_markdown(section_name))
    canonical = SECTION_NAME_ALIASES.get(normalized, normalized)
    return canonical if canonical in ALLOWED_SECTION_NAMES else None


def _normalize_label_line(text: str) -> str:
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned_lines = [_strip_markdown_emphasis(line) for line in normalized.splitlines()]
    return "\n".join(cleaned_lines)


def _extract_first_match(block: str, label: str) -> str:
    fields = _parse_key_value_lines(block)
    return fields.get(_field_alias(label) or "", "").strip()


def _split_sections(reply: str) -> tuple[dict[str, str], list[tuple[str, str]]]:
    normalized = (reply or "").strip().replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.splitlines()

    intro_lines: list[str] = []
    parsed_sections: list[tuple[str, str]] = []
    current_name: str | None = None
    current_body: list[str] = []
    saw_section = False
    total_sections = 0

    for line in lines:
        match = SECTION_HEADER_RE.match(line)
        if match:
            saw_section = True
            total_sections += 1
            if current_name:
                parsed_sections.append((current_name, "\n".join(current_body).strip()))
            current_body = []
            raw_section_name = match.group(1).strip()
            current_name = _canonical_section_name(raw_section_name)
            normalized_name = _normalize_text(_strip_surrounding_markdown(raw_section_name))
            status = "accepted" if current_name else ("forbidden" if normalized_name in FORBIDDEN_SECTION_NAMES else "ignored")
            logger.info(
                "ai_section_parser original=%r normalized=%r alias=%s final=%r component=%r status=%s",
                line.strip(),
                normalized_name,
                normalized_name in SECTION_NAME_ALIASES,
                current_name,
                SECTION_COMPONENT_TYPES.get(current_name or ""),
                status,
            )
            continue

        if not saw_section:
            intro_lines.append(line)
            continue

        if current_name:
            current_body.append(line)

    if current_name:
        parsed_sections.append((current_name, "\n".join(current_body).strip()))

    logger.info("ai_section_parser_summary total=%d valid=%d", total_sections, len(parsed_sections))

    intro_text = "\n".join(intro_lines).strip()
    intro_fields = _parse_key_value_lines(intro_text)
    meta = {
        "Tipo de página": intro_fields.get("page_type", ""),
        "Objetivo da página": intro_fields.get("page_goal", ""),
        "Público predominante": intro_fields.get("audience", ""),
        "Seções escolhidas": intro_fields.get("chosen_sections", ""),
    }
    return meta, parsed_sections


def _split_bullets(value: str) -> list[str]:
    normalized = (value or "").replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("•", "\n").replace("‣", "\n")
    items: list[str] = []
    for line in normalized.splitlines():
        cleaned = re.sub(r"^\s*[-*•‣]\s*", "", line).strip()
        if cleaned:
            items.append(cleaned)
    return items


def _parse_key_value_lines(text: str) -> dict[str, str]:
    result: dict[str, list[str]] = {}
    current_key: str | None = None
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    for raw_line in normalized.splitlines():
        line = _strip_markdown_emphasis(raw_line.strip())
        line = re.sub(r"^[-*•‣]\s+", "", line).strip()
        if not line:
            if current_key:
                result.setdefault(current_key, []).append("")
            continue

        match = re.match(r"^([^:]+?):\s*(.*)$", line)
        if match:
            alias = _field_alias(match.group(1))
            if alias:
                current_key = alias
                result.setdefault(alias, [])
                value = match.group(2).strip()
                if value:
                    result[alias].append(value)
                continue

        if current_key:
            result.setdefault(current_key, []).append(line)

    return {key: "\n".join(value).strip() for key, value in result.items()}


def _parse_price_value(value: str) -> float:
    # Read one amount, without joining installment counts or other numbers.
    amount_text = (value or "").split("R$", 1)[-1]
    match = re.search(r"\d+(?:\.\d{3})*(?:,\d{1,2})?", amount_text)
    if not match:
        return 0.0
    digits = match.group(0)
    digits = digits.replace(".", "").replace(",", ".")
    try:
        return float(digits)
    except ValueError:
        return 0.0


MONTHS_PT = {
    "JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "ABRIL": 4, "MAIO": 5, "JUNHO": 6,
    "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12,
}


def _parse_trip_date(value: str) -> str:
    """Data da viagem no formato da página (AAAA-MM-DD). Só aceita datas com ano."""
    text = _normalize_text(value or "")
    match = re.search(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b", text)
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
    else:
        match = re.search(r"\b(\d{1,2})\s+DE\s+([A-Z]+)\s+DE\s+(\d{4})\b", text)
        if not match or match.group(2) not in MONTHS_PT:
            return ""
        day, month, year = int(match.group(1)), MONTHS_PT[match.group(2)], int(match.group(3))
    if year < 100:
        year += 2000
    try:
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return ""


PAYMENT_KEYWORDS = (
    ("pix", r"\bPIX\b"),
    ("boleto", r"\bBOLETO"),
    ("cartao", r"\bCARTAO|\bCREDITO\b"),
    ("visa", r"\bVISA\b"),
    ("mastercard", r"\bMASTER"),
    ("elo", r"\bELO\b"),
    ("amex", r"\bAMEX\b|AMERICAN EXPRESS"),
    ("hipercard", r"\bHIPER"),
    ("diners", r"\bDINERS\b"),
)


def _parse_payment_methods(value: str) -> tuple[list[str], str]:
    """Formas de pagamento citadas no texto e a condição de parcelamento, se houver."""
    text = _normalize_text(value or "")
    methods = [method for method, pattern in PAYMENT_KEYWORDS if re.search(pattern, text)]
    if any(brand in methods for brand in ("visa", "mastercard", "elo", "amex", "hipercard", "diners")) and "cartao" not in methods:
        methods.append("cartao")
    order = [method for method, _ in PAYMENT_KEYWORDS]
    methods.sort(key=order.index)
    installment = re.search(r"(?:em\s+ate\s+|ate\s+)?\d{1,2}\s*x[^.;,\n]*", text, re.I)
    note = ""
    if installment:
        original = value or ""
        raw = re.search(r"(?:em\s+at[eé]\s+|at[eé]\s+)?\d{1,2}\s*x[^.;,\n]*", original, re.I)
        note = (raw.group(0) if raw else installment.group(0)).strip()
        note = note[:1].upper() + note[1:]
    return methods, note


def _split_price_text(value: str) -> tuple[str, str]:
    """Separa o que vem antes do valor ("a partir de") e depois ("por pessoa")."""
    text = (value or "").strip()
    match = re.search(r"R\$\s*\d+(?:\.\d{3})*(?:,\d{1,2})?|\d+(?:\.\d{3})*,\d{2}", text)
    if not match:
        return "", ""
    before = text[: match.start()].strip(" :-–")
    after = text[match.end():].strip(" :-–")
    label = before[:1].upper() + before[1:] if before else ""
    return label, after


# Orientações do prompt que o modelo às vezes copia para o conteúdo do dia ("descrição do dia na
# linha seguinte, em 1 a 3 frases", "(até 7 palavras)"). Não são texto da página.
_INSTRUCTION_LEAK_LINE_RE = re.compile(
    r"^[\s(\[*_-]*(?:descri[cç][aã]o(?:\s+do\s+dia)?|texto(?:\s+do\s+dia)?|t[ií]tulo(?:\s+curto)?(?:\s+do\s+dia)?)?"
    r"[^.!?\n]{0,60}?\b(?:na\s+linha\s+seguinte|de\s+1\s+a\s+3\s+(?:frases|linhas)|em\s+1\s+a\s+3\s+(?:frases|linhas)|1\s*[-–a]\s*3\s+(?:frases|linhas))\b[^\n]*$",
    re.I,
)
_INSTRUCTION_LEAK_HINT_RE = re.compile(
    r"\s*[(\[]\s*(?:at[eé]\s+\d+\s+palavras|\d+\s*(?:a|-|–)\s*\d+\s+(?:frases|linhas|palavras))\s*[)\]]",
    re.I,
)


def _strip_instruction_leaks(line: str) -> str:
    """Remove do texto do dia as orientações do prompt que vazaram para a resposta do modelo."""
    stripped = line.strip()
    if _INSTRUCTION_LEAK_LINE_RE.match(stripped) or re.fullmatch(r"[\s(\[*_-]*t[ií]tulo\s+curto(?:\s+do\s+dia)?[\s)\]*_.-]*", stripped, re.I):
        return ""
    return _INSTRUCTION_LEAK_HINT_RE.sub("", line).strip()


def _itinerary_day_content(body: str) -> tuple[str, str]:
    lines = [
        cleaned
        for cleaned in (
            _strip_instruction_leaks(_strip_markdown_emphasis(line.strip()))
            for line in body.splitlines()
            if line.strip() and not re.fullmatch(r"\s*(?:[-*_]\s*){3,}", line)
        )
        if cleaned
    ]
    if not lines:
        return "Programação do dia", ""
    first = re.sub(r"^(?:[-*•]\s*)?(?:Título|Titulo)\s*:\s*", "", lines[0], flags=re.I)
    # Keep a supplied short heading; otherwise summarize without dropping details.
    if len(lines) > 1 and len(first) <= 65 and len(first.split()) <= 9:
        description = "\n".join(lines[1:])
        description = re.sub(r"^(?:Descrição|Descricao)\s*:\s*", "", description, flags=re.I)
        return first, description
    description = "\n".join(lines)
    normalized = _normalize_text(description)
    if "CHECK-OUT" in normalized or "RETORNO PARA CASA" in normalized:
        title = "Check-out e retorno" if "CHECK-OUT" in normalized else "Retorno para casa"
    elif "EMBARQUE" in normalized:
        title = "Embarque e traslado" if "TRASLADO" in normalized else "Embarque e início da viagem"
    elif "PASSEIO OPCIONAL" in normalized:
        title = "Passeio opcional"
    elif "DIA LIVRE" in normalized:
        title = "Dia livre e piscinas naturais" if "PISCINAS NATURAIS" in normalized else "Dia livre para aproveitar"
    elif "COMPRAS" in normalized and "GASTRONOM" in normalized:
        title = "Compras e gastronomia"
    else:
        sentence = re.split(r"[.!?;]\s*", first, maxsplit=1)[0]
        words = sentence.split()
        title = " ".join(words[:7])
        if len(title) > 60:
            title = title[:60].rsplit(" ", 1)[0]
        if title != sentence:
            title = title.rstrip(",:;") + "…"
        elif title.strip() == description.strip():
            title = "Programação do dia"
    return title, description


def _parse_countdown_date(value: str) -> str:
    """Data e hora do fim do contador ("20/12/2026 23:59", horário de Brasília) em ISO UTC."""
    day = _parse_trip_date(value)
    if not day:
        return ""
    time_match = re.search(r"\b(\d{1,2})\s*(?:h|:)\s*(\d{2})?\b", re.sub(r"\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}", "", value or ""), re.I)
    hour, minute = (int(time_match.group(1)), int(time_match.group(2) or 0)) if time_match else (23, 59)
    if hour > 23 or minute > 59:
        hour, minute = 23, 59
    local = datetime.strptime(day, "%Y-%m-%d").replace(hour=hour, minute=minute)
    return (local + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _flight_info_text(block: str) -> str:
    """Dados do voo enviados pela IA ("Companhia aérea: ...", "Ida: ..."), um por linha."""
    lines: list[str] = []
    for raw_line in (block or "").splitlines():
        line = _structure_line(raw_line)
        if not line:
            continue
        match = re.match(r"^([^:]+?):\s*(.*)$", line)
        if match and _field_alias(match.group(1)) in {"title", "subtitle", "label", "section_function", "content", "button"}:
            continue
        if match and not match.group(2).strip():
            lines.append(match.group(1).strip() + ":")
            continue
        lines.append(line)
    return "\n".join(lines).strip()


HEX_COLOR_RE = re.compile(r"#(?:[0-9a-fA-F]{3}){1,2}\b")
MENU_TARGET_SPLIT_RE = re.compile(r"\s*(?:→|->|=>|\|)\s*")


def _header_mode(value: str) -> str | None:
    text = _normalize_text(value or "")
    if not text:
        return None
    if "TRANSPAR" in text or "SEM FUNDO" in text or "SOBRE O BANNER" in text:
        return "transparent"
    if "DESFOC" in text or "VIDRO" in text or "BLUR" in text or "FOSCO" in text:
        return "blurred"
    if "SOLID" in text or "COR" in text or "BRANCO" in text or "NORMAL" in text or "PADRAO" in text:
        return "solid"
    return None


def _menu_item(raw: str, number: int) -> dict[str, Any] | None:
    """ "Roteiro → roteiro-dia-a-dia" (identificador da seção), "Instagram → https://..." ou só
    "Roteiro" (ligado depois pelo título da seção)."""
    parts = MENU_TARGET_SPLIT_RE.split(raw.strip(), maxsplit=1)
    label = parts[0].strip()
    target = (parts[1] if len(parts) > 1 else "").strip().strip("()").lstrip("#").strip()
    # "Roteiro (#roteiro-dia)" também vale.
    match = re.match(r"^(.*?)\s*\(#?([a-z0-9][a-z0-9-]*)\)\s*$", label)
    if match and not target:
        label, target = match.group(1).strip(), match.group(2)
    if not label or len(label) > 40:
        return None
    item: dict[str, Any] = {"id": f"ai-menu-{number}", "label": label, "targetType": "section", "target": ""}
    if target.lower().startswith(("http://", "https://", "www.")):
        item.update(targetType="external", target=target if "://" in target else f"https://{target}", openInNewTab=True)
    elif re.fullmatch(r"[a-z0-9][a-z0-9-]*", target or ""):
        item["target"] = target
    return item


def _header_section(fields: dict[str, str], index: int) -> dict[str, Any]:
    """Menu do topo. Só leva os campos que a resposta trouxe além do básico, e marca em
    aiSetKeys o que foi pedido: numa troca ("Substitui"), o editor muda só isso (ex.: deixar o
    menu transparente não apaga os itens)."""
    section: dict[str, Any] = {
        "type": "header",
        "enabled": True,
        "anchorId": _generate_anchor("header", "menu", index),
        "mode": "solid",
        "stickyEnabled": True,
        "logoActionType": "top",
        "links": [],
        "actionType": "contact",
        "contactLabel": "Falar no WhatsApp",
        "contactType": "whatsapp",
    }
    set_keys: list[str] = []
    # "Links:" dentro do Menu do topo também são os itens do menu.
    menu_links = fields.get("menu_links", "").strip() or fields.get("link", "").strip()
    if menu_links:
        items = [_menu_item(label, number) for number, label in enumerate(_split_bullets(menu_links), 1)]
        # Itens sem identificador são ligados depois pelo título (_link_header_menu e editor).
        section["_menuItems"] = [item for item in items if item][:7]
        set_keys.append("links")
    mode = _header_mode(fields.get("header_mode", "")) or _header_mode(fields.get("icon_style", ""))
    if mode:
        section["mode"] = mode
        set_keys.append("mode")
    if fields.get("header_sticky", "").strip():
        # "não", "sem fixar", "desligado": solto. Qualquer outra resposta ("sim", "normal"): fixo.
        sticky = _normalize_text(fields["header_sticky"])
        section["stickyEnabled"] = not re.match(r"^(NAO|NO|SEM|DESLIG|DESATIV|FALSE|OFF)\b", sticky)
        set_keys.append("stickyEnabled")
    for field, key in (("background_color", "backgroundColor"), ("text_color", "textColor"), ("button_color", "buttonColor")):
        color = HEX_COLOR_RE.search(fields.get(field, "") or "")
        if color:
            section[key] = color.group(0)
            set_keys.append(key)
            if key == "textColor":
                section["linkTextColor"] = color.group(0)
                set_keys.append("linkTextColor")
    if fields.get("header_action", "").strip() or fields.get("button", "").strip():
        section["actionType"] = _header_action(fields.get("header_action", ""), bool(fields.get("button")))
        set_keys.append("actionType")
    if fields.get("button", "").strip():
        section["contactLabel"] = fields["button"].strip()
        set_keys.append("contactLabel")
    # Redes sociais: o editor preenche com as redes cadastradas da agência.
    section["aiSetKeys"] = set_keys
    return section


def _header_action(value: str, has_button: bool) -> str:
    """Lado direito do Menu do topo: redes sociais, botão de contato ou nada."""
    text = _normalize_text(value or "")
    if "REDE" in text or "SOCIA" in text:
        return "social"
    if text.startswith(("NADA", "NENHUM", "SEM", "VAZIO")):
        return "none"
    return "contact" if ("BOTAO" in text or "CONTATO" in text or has_button or not text) else "none"


def _is_yes(value: str) -> bool:
    return _normalize_text(value or "").rstrip(".!") in {"SIM", "S", "YES", "TRUE", "X", "DESTAQUE", "EM DESTAQUE"}

# Ícones da biblioteca do editor ("icon:<nome>") que a IA pode escolher, com palavras que os
# indicam quando ela não escolhe (destaques do Banner e cards de Itens).
AI_ICON_KEYWORDS: dict[str, tuple[str, ...]] = {
    "plane": ("AEREO", "AEREA", "VOO", "VOOS", "PASSAGEM", "PASSAGENS", "AVIAO"),
    "hotel": ("HOTEL", "RESORT"),
    "bed": ("HOSPEDAGEM", "POUSADA", "NOITE", "NOITES", "DIARIA", "DIARIAS", "ACOMODACAO"),
    "bus": ("ONIBUS", "TRANSPORTE", "RODOVIARIO", "RODOVIARIA", "TRASLADO", "TRASLADOS", "TRANSFER", "VAN"),
    "coffee": ("CAFE",),
    "utensils": ("REFEICAO", "REFEICOES", "ALMOCO", "ALMOCOS", "JANTAR", "JANTARES", "GASTRONOMIA", "PENSAO", "ALL INCLUSIVE"),
    "user-check": ("GUIA", "GUIAS", "ACOMPANHANTE", "COORDENADOR", "COORDENACAO", "MONITOR", "MONITORES"),
    "shield-check": ("SEGURO", "SEGURANCA"),
    "train-front": ("TREM", "TRENS", "MARIA FUMACA"),
    "ship": ("CRUZEIRO", "NAVIO"),
    "sailboat": ("BARCO", "LANCHA", "ESCUNA", "CATAMARA"),
    "camera": ("PASSEIO", "PASSEIOS", "CITY TOUR", "TOUR", "TOURS", "FOTOS"),
    "ticket": ("INGRESSO", "INGRESSOS", "ENTRADA", "ENTRADAS"),
    "users": ("GRUPO", "GRUPOS", "FAMILIA", "FAMILIAS"),
    "calendar-days": ("DATA", "DATAS", "FERIADO", "DIAS", "SAIDA", "SAIDAS"),
    "tree-palm": ("PRAIA", "PRAIAS", "LITORAL"),
    "mountain": ("SERRA", "MONTANHA", "MONTANHAS", "TRILHA", "TRILHAS"),
    "church": ("IGREJA", "SANTUARIO", "PEREGRINACAO", "MISSA", "RELIGIOSO", "RELIGIOSA", "FE"),
    "credit-card": ("PARCELA", "PARCELAS", "PARCELAMENTO", "CARTAO", "PAGAMENTO", "PIX", "SEM JUROS"),
    "headset": ("ATENDIMENTO", "SUPORTE", "ASSISTENCIA"),
    "waves": ("PISCINA", "PISCINAS", "AGUAS", "PARQUE AQUATICO"),
    "wine": ("VINHO", "VINHOS", "VINICOLA", "VINICOLAS"),
    "ferris-wheel": ("PARQUE", "PARQUES", "DISNEY"),
    "snowflake": ("NEVE", "INVERNO"),
    "map-pin": ("DESTINO", "LOCALIZACAO", "CENTRO"),
    "clock": ("HORARIO", "HORARIOS", "PONTUALIDADE"),
    "sparkles": ("EXPERIENCIA", "EXPERIENCIAS", "EXCLUSIVO", "EXCLUSIVA", "INESQUECIVEL"),
}
# Emoji equivalente de cada ícone, para os Diferenciais no estilo "emojis".
AI_ICON_EMOJIS = {
    "plane": "✈️", "hotel": "🏨", "bed": "🛏️", "bus": "🚌", "train-front": "🚆", "coffee": "☕", "utensils": "🍽️",
    "user-check": "🧑‍✈️", "shield-check": "🛡️", "camera": "📸", "ticket": "🎟️", "users": "👨‍👩‍👧", "calendar-days": "📅",
    "ship": "🚢", "sailboat": "⛵", "tree-palm": "🌴", "mountain": "⛰️", "church": "⛪", "credit-card": "💳",
    "headset": "🎧", "waves": "🌊", "wine": "🍷", "ferris-wheel": "🎡", "snowflake": "❄️", "map-pin": "📍",
    "clock": "⏰", "sparkles": "✨", "circle-check": "✅", "star": "⭐", "heart": "❤️", "route": "🗺️",
    "luggage": "🧳", "baby": "👶", "map": "🗺️", "compass": "🧭", "sun": "☀️",
}
AI_ICON_NAMES = frozenset(AI_ICON_KEYWORDS) | frozenset({"circle-check", "star", "heart", "route", "luggage", "baby", "map", "compass", "sun"})


def _is_emoji(value: str) -> bool:
    return bool(value) and len(value) <= 12 and not re.search(r"[A-Za-z0-9À-ÿ]", value)


def _ai_icon_value(raw: str, *texts: str) -> str:
    """Ícone escolhido pela IA ("plane", "icon:plane" ou emoji); sem escolha válida, deduz pelo texto."""
    value = (raw or "").strip().strip("`\"'")
    name = value[5:] if value.lower().startswith("icon:") else value
    if name.lower() in AI_ICON_NAMES:
        return f"icon:{name.lower()}"
    # Emoji (sem letras), como "✈️" ou "👨‍👩‍👧": continua emoji.
    if _is_emoji(value):
        return value
    # O título decide antes da descrição ("Refeições: café da manhã e jantares" → talheres).
    for text in texts:
        haystack = " " + re.sub(r"[^A-Z ]", " ", _normalize_text(text or "")) + " "
        for icon, words in AI_ICON_KEYWORDS.items():
            if any(f" {word} " in haystack for word in words):
                return f"icon:{icon}"
    return ""


def _slug_from_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", (value or "").strip().lower())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return re.sub(r"-{2,}", "-", normalized).strip("-")


def _generate_anchor(section_type: str, title: str, index: int) -> str:
    base = _slug_from_text(title) or section_type
    return f"{base}-{index + 1}"


def _structure_line(raw_line: str) -> str:
    return re.sub(r"^(?:[-*+•‣]|\d+[.)])\s+", "", _strip_markdown_emphasis(raw_line.strip())).strip()


ITINERARY_DAY_RE = re.compile(r"^Dia\s*(\d+)\s*(?:\(([^)]+)\)\s*)?:\s*(.*)$", re.I)


def _parse_reason_items(block: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    current: dict[str, str] = {}
    inside_list = False

    def flush() -> None:
        nonlocal current
        if current.get("title"):
            item = {"title": current["title"]}
            if current.get("description"):
                item["description"] = current["description"]
            if current.get("icon"):
                item["icon"] = current["icon"]
            items.append(item)
        current = {}

    for raw_line in (block or "").replace("\r\n", "\n").replace("\r", "\n").splitlines():
        line = _structure_line(raw_line)
        normalized_line = _normalize_text(line)
        if normalized_line.rstrip(":") in {"LISTA DE ITENS", "ITENS"}:
            inside_list = True
            continue
        if re.match(r"^ITEM(?:\s+\d+)?\s*:", normalized_line):
            flush()
            inside_list = True
            inline_title = line.split(":", 1)[1].strip() if ":" in line else ""
            if inline_title:
                current["title"] = inline_title
            continue
        if not inside_list:
            continue
        match = re.match(r"^([^:]+?):\s*(.*)$", line)
        if not match:
            if line and re.match(r"^\s*(?:[-*+•‣]|\d+[.)])\s+", raw_line):
                flush()
                current["title"] = line
            elif current.get("title") and line:
                current["description"] = f"{current.get('description', '')}\n{line}".strip()
            continue
        key = _field_alias(match.group(1))
        value = match.group(2).strip()
        if key == "title":
            if current.get("title"):
                flush()
            current["title"] = value
        elif key in {"description", "icon"}:
            current[key] = value
        elif key in {"label", "subtitle", "button", "image_suggestion", "section_function", "content"}:
            flush()
            inside_list = False
        else:
            # "Transporte: ida e volta" é um item (título: descrição), mesmo que a palavra
            # coincida com algum rótulo de outra seção.
            flush()
            current = {"title": match.group(1).strip(), "description": value}
    flush()
    return items


# Resumo do pacote: "Inclui:", "O que inclui:", "Não inclui:", "O que não inclui:".
INCLUSION_LIST_RE = re.compile(r"^((?:o\s+que\s+)?n[ãa]o\s+inclui|(?:o\s+que\s+)?inclui|n[ãa]o\s+incluso|incluso)\s*:\s*(.*)$", re.I)


def _inclusion_item(text: str) -> dict[str, str]:
    parts = re.split(r"\s+[—–]\s+", text.strip(), maxsplit=1)
    title = parts[0].strip()
    details = parts[1].strip() if len(parts) > 1 else ""
    return {"title": title, "details": details}


def _parse_ai_section_block(section_name: str, block: str, index: int) -> dict[str, Any] | None:
    normalized_name = _normalize_text(section_name)
    header_lines = []
    for raw_line in block.splitlines():
        line = _structure_line(raw_line)
        if normalized_name == "ITINERARIO" and ITINERARY_DAY_RE.match(line):
            break
        if normalized_name == "ITENS" and (
            _normalize_text(line).rstrip(":") in {"LISTA DE ITENS", "ITENS"}
            or re.match(r"^ITEM(?:\s+\d+)?\s*:", line, re.I)
        ):
            break
        if normalized_name == "RESUMO DO PACOTE" and INCLUSION_LIST_RE.match(line):
            break
        header_lines.append(raw_line)
    fields = _parse_key_value_lines("\n".join(header_lines))

    if normalized_name == _normalize_text("BANNER"):
        title = fields.get("title", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        content = fields.get("content", "").strip()
        highlights_source = fields.get("highlights", "").strip()
        cta_label = fields.get("button", "").strip()
        if not title:
            title = next((line.strip() for line in content.splitlines() if line.strip()), "")
        if not subtitle and content and content != title:
            subtitle = content
        highlights = _split_bullets(highlights_source)
        if not highlights and content:
            highlights = _split_bullets(content)
        # Datas da viagem alimentam o cartão de datas da capa e o calendário do roteiro dia a dia.
        departure_date = _parse_trip_date(fields.get("departure_date", ""))
        return_date = _parse_trip_date(fields.get("return_date", ""))
        trip_dates = {"departureDate": departure_date} if departure_date else {}
        if departure_date and return_date and return_date >= departure_date:
            trip_dates["returnDate"] = return_date
        chip_icons = [_ai_icon_value("", chip) for chip in highlights]
        if any(chip_icons):
            trip_dates["chipIcons"] = chip_icons
        return {
            **trip_dates,
            "type": "hero",
            "enabled": True,
            "anchorId": _generate_anchor("hero", title or "banner-inicial", index),
            "layout": "immersive",
            "title": title or "Banner inicial",
            "subtitle": subtitle or "",
            "chips": highlights,
            "ctaLabel": cta_label or "Saiba mais",
            "ctaMode": "link",
            "ctaLink": "",
            "ctaSectionId": None,
            "ctaOpenInNewTab": False,
            "backgroundImage": "",
            "mobileBackgroundImage": "",
            "enableAnimation": False,
        }

    if normalized_name == _normalize_text("BANNER EM CARD"):
        title = fields.get("title", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        content = fields.get("content", "").strip()
        if not title:
            title = next((line.strip() for line in content.splitlines() if line.strip()), "")
        if not subtitle and content and content != title:
            subtitle = content
        return {
            "type": "banner_card",
            "enabled": True,
            "anchorId": _generate_anchor("banner-card", title or "banner-destacado", index),
            "title": title or "Banner destacado",
            "subtitle": subtitle or "",
            "backgroundImage": "",
            "ctaEnabled": False,
            "ctaMode": "link",
            "ctaSectionId": None,
            "ctaOpenInNewTab": False,
        }

    if normalized_name == _normalize_text("FOTO DESTACADA"):
        image = fields.get("image_suggestion", "").strip() or fields.get("link", "").strip()
        caption = fields.get("caption", "").strip() or fields.get("title", "").strip() or fields.get("subtitle", "").strip()
        layout_text = _normalize_text(fields.get("layout", ""))
        return {
            "type": "photo",
            "enabled": True,
            "anchorId": _generate_anchor("photo", caption or "foto-destacada", index),
            "image": image,
            "layout": "full" if ("LARGURA" in layout_text or "FULL" in layout_text or "TOTAL" in layout_text) else "card",
            "caption": caption,
            "altText": caption or image,
        }

    if normalized_name == _normalize_text("DESCRITIVO"):

        label = fields.get("label", "").strip()
        title = fields.get("title", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        content = fields.get("content", "").strip()
        if not title:
            title = next((line.strip() for line in content.splitlines() if line.strip()), "")
        body = subtitle or fields.get("text", "").strip() or fields.get("description", "").strip() or content
        return {
            "type": "story",
            "enabled": True,
            "anchorId": _generate_anchor("story", title or label or "sessao-descritiva", index),
            "layout": "single",
            "imagePosition": "right",
            "badge": label or "",
            "title": title or "Seção descritiva",
            "subtitle": body or "",
            "ctaEnabled": False,
            "ctaMode": "link",
            "ctaSectionId": None,
            "ctaOpenInNewTab": False,
            "ctaLink": "",
            "ctaLabel": "",
            "ctaColor": "",
            "images": [],
            "videoUrls": [],
            "videoUrl": "",
            "backgroundColor": "",
            "borderEnabled": False,
            "borderColor": "",
        }

    if normalized_name == _normalize_text("ITINERARIO"):

        title = fields.get("title", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        content = fields.get("content", "").strip()
        days: list[dict[str, Any]] = []
        day_blocks: list[tuple[str, str, list[str]]] = []
        for raw_line in block.splitlines():
            line = _structure_line(raw_line)
            match = ITINERARY_DAY_RE.match(line)
            if match:
                day_blocks.append((match.group(1), match.group(2) or "", [match.group(3)]))
            elif day_blocks:
                day_blocks[-1][2].append(line)
        for day_number, weekday, body_lines in day_blocks:
            day_body = "\n".join(body_lines).strip()
            day_title, day_description = _itinerary_day_content(day_body)
            days.append(
                {
                    "day": f"Dia {day_number}" + (f" ({weekday})" if weekday else ""),
                    "title": day_title or f"Dia {day_number}",
                    "description": day_description,
                }
            )
        if not days:
            day_text = content
            if day_text:
                day_title, day_description = _itinerary_day_content(day_text)
                days.append({"day": "Dia 1", "title": day_title, "description": day_description})
        return {
            "type": "itinerary",
            "enabled": True,
            "anchorId": _generate_anchor("itinerary", title or "itinerario", index),
            "layout": "timeline",
            "title": title or "Itinerário",
            "subtitle": subtitle or "",
            "days": days,
        }

    if normalized_name == _normalize_text("PRECOS"):
        # Cada "Nome do plano" abre um plano; o que vem antes do primeiro é da seção
        # (etiqueta, título, subtítulo) e a observação geral vale para a lista toda.
        intro_lines: list[str] = []
        plan_blocks: list[list[str]] = []
        current_plan: list[str] | None = None
        for raw_line in block.splitlines():
            line = _strip_markdown_emphasis(raw_line.strip())
            if re.fullmatch(r"(?:[-*_]\s*){3,}", line):
                continue
            line = re.sub(r"^(?:[-*+•‣]|\d+[.)])\s+", "", line)
            label = line.split(":", 1)[0]
            if ":" in line and _field_alias(label) == "plan_name":
                current_plan = [line]
                plan_blocks.append(current_plan)
            elif current_plan is not None:
                current_plan.append(line)
            else:
                intro_lines.append(line)
        intro = _parse_key_value_lines("\n".join(intro_lines))
        plans = [_parse_key_value_lines("\n".join(lines)) for lines in plan_blocks] or [fields]
        general_note = intro.get("general_note", "").strip() or next(
            (plan.get("general_note", "").strip() for plan in plans if plan.get("general_note")), ""
        )
        # Frase geral solta depois do último plano ("Consulte disponibilidade, formas de
        # pagamento..."): vale para a lista toda, não para o último plano.
        last_note = plans[-1].get("note", "").strip()
        if last_note and plan_blocks:
            note_lines = last_note.splitlines()
            while len(note_lines) > 1 and re.match(r"^(?:CONSULTE|VALORES|PRECOS|CONDICOES|SUJEITO)", _normalize_text(note_lines[-1])):
                general_note = "\n".join(part for part in (note_lines.pop().strip(), general_note) if part)
            plans[-1]["note"] = "\n".join(note_lines).strip()
        notes = [plan.get("note", "").strip() for plan in plans]
        # A mesma observação em todos os planos vira a nota única abaixo da lista.
        shared_note = notes[0] if len(notes) > 1 and notes[0] and all(note == notes[0] for note in notes) else ""
        # Formas de pagamento valem para a seção; o parcelamento de cada plano fica no próprio plano.
        payment_text = " ".join(
            source.get("payment_methods", "") for source in [intro, *plans] if source.get("payment_methods")
        )
        payment_methods, payment_note = _parse_payment_methods(payment_text)
        price_items = []
        for plan in plans:
            raw_value = plan.get("value", "").strip()
            note = plan.get("note", "").strip()
            split_label, terms = _split_price_text(raw_value)
            price = _parse_price_value(raw_value) if re.search(r"\d", raw_value) else 0.0
            if not price and raw_value and not split_label and not terms:
                # Valor sem número ("Sob consulta"): o texto vai para as condições.
                terms = raw_value
            installments = plan.get("installments", "").strip()
            details = [terms, installments, "" if note == shared_note else note]
            item: dict[str, Any] = {
                "title": plan.get("plan_name", "").strip() or "Pacote",
                "price": price,
                "priceLabel": plan.get("price_label", "").strip() or split_label,
                "description": "\n".join(part for part in details if part),
                "currency": "BRL",
            }
            badge = plan.get("badge", "").strip()
            if badge and _normalize_text(badge) not in {"NAO", "NENHUM", "SEM SELO", "-"}:
                item["badge"] = badge
            if _is_yes(plan.get("plan_highlight", "")):
                item["highlight"] = True
            price_items.append(item)
        prices_section: dict[str, Any] = {
            "type": "prices",
            "enabled": True,
            "anchorId": _generate_anchor("prices", "precos", index),
            "layout": "cards" if len(price_items) > 1 else "highlight",
            "title": intro.get("title", "").strip() or "Preços",
            "subtitle": intro.get("subtitle", "").strip(),
            "description": "\n".join(part for part in (shared_note, general_note) if part),
            "items": price_items,
        }
        if intro.get("label"):
            prices_section["headingLabel"] = intro["label"].strip()
        if payment_methods:
            prices_section.update({"showPayments": True, "paymentMethods": payment_methods, "paymentNote": payment_note})
        return prices_section

    if normalized_name == _normalize_text("PERGUNTAS FREQUENTES"):
        questions: list[dict[str, Any]] = []
        current_question = ""
        current_answer_lines: list[str] = []
        reading_answer = False
        for raw_line in block.splitlines():
            line = _strip_markdown_emphasis(raw_line.strip())
            if re.fullmatch(r"(?:[-*_]\s*){3,}", line):
                continue
            label_line = re.sub(r"^(?:[-*+•‣]|\d+[.)])\s+", "", line)
            question_match = re.match(r"^Pergunta\s*:\s*(.*)$", label_line, flags=re.IGNORECASE)
            answer_match = re.match(r"^Resposta\s*:\s*(.*)$", label_line, flags=re.IGNORECASE)
            if question_match:
                if current_question and current_answer_lines:
                    questions.append({"question": current_question, "answer": "\n".join(current_answer_lines).strip()})
                current_question = question_match.group(1).strip()
                current_answer_lines = []
                reading_answer = False
            elif answer_match and current_question:
                current_answer_lines = [answer_match.group(1).strip()]
                reading_answer = True
            elif current_question and line:
                if reading_answer:
                    current_answer_lines.append(line)
                else:
                    current_question = f"{current_question} {line}"
        if current_question and current_answer_lines:
            questions.append({"question": current_question, "answer": "\n".join(current_answer_lines).strip()})
        return {
            "type": "faq",
            "enabled": True,
            "anchorId": _generate_anchor("faq", "perguntas-frequentes", index),
            "layout": "accordion",
            "title": fields.get("title", "").strip() or "Perguntas frequentes",
            "subtitle": fields.get("subtitle", "").strip(),
            "items": questions,
        }

    if normalized_name == _normalize_text("DEPOIMENTOS"):
        # Cada "Nome" abre um depoimento; "Depoimento"/"Texto" é a fala e "Identificação"/"Cargo"
        # aparece embaixo do nome. A avaliação não tem campo na seção (as estrelas são fixas).
        items: list[dict[str, Any]] = []
        current_item: dict[str, str] = {}
        current_key = ""
        intro: dict[str, str] = {}

        def flush_testimonial() -> None:
            if current_item.get("name") and current_item.get("text"):
                items.append(dict(current_item))

        for raw_line in block.splitlines():
            line = _structure_line(raw_line)
            if not line:
                continue
            match = re.match(r"^([^:]+?):\s*(.*)$", line)
            key = _field_alias(match.group(1)) if match else None
            if match and _normalize_text(match.group(1)) == "NOME":
                flush_testimonial()
                current_item = {"name": match.group(2).strip()}
                current_key = "name"
            elif key in {"text", "description"} and current_item:
                current_item["text"] = match.group(2).strip()
                current_key = "text"
            elif key == "role" and current_item:
                current_item["role"] = match.group(2).strip()
                current_key = "role"
            elif key in {"title", "subtitle", "label"} and not current_item:
                intro[key] = match.group(2).strip()
            elif key:
                current_key = ""
            elif current_key == "text":
                current_item["text"] = f"{current_item['text']}\n{line}".strip()
        flush_testimonial()
        for item in items:
            item["text"] = item["text"].strip().strip('"“”').strip()
        section_data: dict[str, Any] = {
            "type": "testimonials",
            "enabled": True,
            "anchorId": _generate_anchor("testimonials", "depoimentos", index),
            "layout": "cards",
            "title": intro.get("title") or "Depoimentos",
            "subtitle": intro.get("subtitle", ""),
            "items": items,
        }
        if intro.get("label"):
            section_data["headingLabel"] = intro["label"]
        return section_data

    if normalized_name == _normalize_text("VIDEO EM DESTAQUE"):

        title = fields.get("title", "").strip() or fields.get("label", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        # Só um link de verdade vira vídeo; "inserir link" ou "não informado" fica vazio.
        video_url = next(iter(re.findall(r"https?://\S+", fields.get("link", ""))), "").rstrip(").,;")
        return {
            "type": "featured_video",
            "enabled": True,
            "anchorId": _generate_anchor("featured-video", title or "video", index),
            "title": title or "Vídeo",
            "subtitle": subtitle or "",
            "videoUrl": video_url or "",
            "ctaEnabled": False,
            "ctaMode": "link",
            "ctaSectionId": None,
            "ctaOpenInNewTab": False,
        }

    if normalized_name == _normalize_text("BIOGRAFIA"):
        label = fields.get("label", "").strip()
        title = fields.get("title", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        content = fields.get("content", "").strip()
        text = fields.get("text", "").strip() or fields.get("description", "").strip() or subtitle or content
        return {
            "type": "biography",
            "enabled": True,
            "anchorId": _generate_anchor("biography", title or label or "biografia", index),
            "title": title or "Biografia",
            "text": text or "",
            "titleFontSize": 36,
            "textFontSize": 18,
            "image": "",
            "mobileImage": "",
            "overlayOpacity": 0.45,
        }

    if normalized_name == _normalize_text("CHAMADA PARA ACAO"):

        label = fields.get("label", "").strip()
        title = fields.get("title", "").strip()
        button = fields.get("button", "").strip()
        description = fields.get("description", "").strip() or fields.get("text", "").strip() or fields.get("content", "").strip()
        return {
            "type": "cta",
            "enabled": True,
            "anchorId": _generate_anchor("cta", title or label or "cta", index),
            "layout": "simple",
            "label": title or label or "Chamada para ação",
            **({"headingLabel": label} if title and label else {}),
            "description": fields.get("subtitle", "").strip() or description or "",
            "ctaText": button or "",
            "ctaColor": "",
            "textColor": "",
            "highlight": False,
            "fullWidth": True,
            "ctaMode": "link",
            "ctaSectionId": None,
            "ctaOpenInNewTab": False,
        }

    if normalized_name == _normalize_text("ITENS"):
        label = fields.get("label", "").strip()
        title = fields.get("title", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        items = _parse_reason_items(block)
        # Estilo dos cards: ícones da biblioteca (padrão) ou emojis. Sem estilo indicado, emojis
        # só quando a IA mandou emoji em todos os cards. Todos os cards seguem o mesmo estilo.
        style = _normalize_text(fields.get("icon_style", ""))
        given = [str(item.get("icon", "")).strip().strip("`\"'") for item in items]
        use_emoji = "EMOJI" in style or (not style and items and all(_is_emoji(icon) for icon in given))
        for item, raw_icon in zip(items, given):
            if use_emoji:
                if _is_emoji(raw_icon):
                    item["icon"] = raw_icon
                    continue
                key = _ai_icon_value(raw_icon, item.get("title", ""), item.get("description", ""))
                item["icon"] = AI_ICON_EMOJIS.get(key.removeprefix("icon:"), "✅")
                continue
            chosen = _ai_icon_value(raw_icon)
            if not chosen.startswith("icon:"):
                chosen = _ai_icon_value("", item.get("title", ""), item.get("description", ""))
            item["icon"] = chosen or "icon:circle-check"
        icon_mode = "emoji" if use_emoji else "icon"
        return {
            "type": "reasons",
            "iconMode": icon_mode,
            "enabled": True,
            "anchorId": _generate_anchor("reasons", title or label or "itens", index),
            "headingLabel": label,
            "title": title or "Itens",
            "subtitle": subtitle,
            "items": items,
            "enableAnimation": False,
        }

    if normalized_name == _normalize_text("CONTADOR"):
        label = fields.get("label", "").strip()
        title = fields.get("title", "").strip()
        target_date = _parse_countdown_date(fields.get("target_date", ""))
        if not target_date:
            # Sem data informada a IA não deveria usar o Contador; fica uma data provisória
            # para a agência trocar no editor.
            target_date = (datetime.utcnow() + timedelta(days=3)).replace(microsecond=0).isoformat() + "Z"
        countdown: dict[str, Any] = {
            "type": "countdown",
            "enabled": True,
            "anchorId": _generate_anchor("countdown", title or label or "contagem-regressiva", index),
            "label": title or label or "Contagem regressiva",
            "countdownMode": "fixed",
            "sessionDuration": 15,
            "sessionUnit": "minutes",
            "targetDate": target_date,
            "layout": "flip",
        }
        if title and label:
            countdown["headingLabel"] = label
        return countdown

    if normalized_name == _normalize_text("DETALHES DO VOO"):
        legs, other_lines = parse_flight_legs(block)
        title = fields.get("title", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        return {
            "type": "flight_details",
            "enabled": True,
            "anchorId": _generate_anchor("flight-details", title or "detalhes-do-voo", index),
            "sectionId": _generate_anchor("flight", title or "detalhes-do-voo", index),
            "title": title or "Informações do voo",
            "subtitle": subtitle,
            # O texto do voo é rico (HTML): uma linha por parágrafo. Os trechos ("Ida: ...") viram
            # os cartões de voo (aiFlights); aqui ficam só bagagem e observações.
            "generalInfo": "".join(
                f"<p>{html.escape(line)}</p>"
                for line in (
                    fields.get("general_info", "").strip() or _flight_info_text("\n".join(other_lines) if legs else block)
                ).splitlines()
                if line.strip()
            ),
            "visualStyle": "decolar",
            "showOutbound": True,
            "showInbound": True,
            "journeys": [],
            # Trechos para o editor gravar na seção: com código, buscados na API; sem, manuais.
            **({"aiFlights": legs} if legs else {}),
        }

    if normalized_name == _normalize_text("MENU DO TOPO"):
        return _header_section(fields, index)

    if normalized_name == _normalize_text("RESUMO DO PACOTE"):
        # "Inclui:" e "Não inclui:" abrem as listas; cada linha com "- " é um item. Detalhe do
        # item (ex.: noites por cidade) depois de " — " ou ": ".
        lists: dict[str, list[dict[str, str]]] = {"included": [], "excluded": []}
        bucket: str | None = None
        for raw_line in block.splitlines():
            line = _structure_line(raw_line)
            head = INCLUSION_LIST_RE.match(line)
            if head:
                bucket = "excluded" if _normalize_text(head.group(1)).startswith(("NAO", "O QUE NAO")) else "included"
                rest = head.group(2).strip()
                for part in [item for item in re.split(r"\s*;\s*", rest) if item]:
                    lists[bucket].append(_inclusion_item(part))
                continue
            if bucket is None or not line:
                continue
            if not re.match(r"^\s*(?:[-*+•‣]|\d+[.)])\s+", raw_line):
                # Outro campo depois da lista encerra a lista.
                if re.match(r"^[^:]+:\s*", line) and _field_alias(line.split(":", 1)[0]):
                    bucket = None
                continue
            lists[bucket].append(_inclusion_item(line))
        heading = fields.get("label", "").strip()
        return {
            "type": "inclusions",
            "enabled": True,
            "anchorId": _generate_anchor("inclusions", fields.get("title", "") or "resumo-do-pacote", index),
            "headingLabel": heading or "Resumo do pacote",
            "headingLabelStyle": "outline",
            "title": fields.get("title", "").strip() or "O que está incluso na sua viagem",
            "subtitle": fields.get("subtitle", "").strip(),
            "includedTitle": "Seu pacote inclui",
            "excludedTitle": "Não inclui",
            "included": lists["included"][:12],
            "excluded": lists["excluded"][:12],
        }

    if normalized_name == _normalize_text("RODAPE DA AGENCIA"):
        # Preenchido pelos dados da agência; o editor completa com o padrão da seção.
        return {"type": "agency_footer", "enabled": True, "anchorId": _generate_anchor("agency-footer", "rodape", index), "showCadastur": True}

    if normalized_name == _normalize_text("VITRINE DE VIAGENS"):
        intro_lines: list[str] = []
        trip_blocks: list[list[str]] = []
        for raw_line in block.splitlines():
            line = _structure_line(raw_line)
            label = line.split(":", 1)[0]
            if ":" in line and _field_alias(label) == "trip_name":
                trip_blocks.append([line])
            elif trip_blocks:
                trip_blocks[-1].append(line)
            else:
                intro_lines.append(line)
        intro = _parse_key_value_lines("\n".join(intro_lines))
        cards = []
        for number, lines in enumerate(trip_blocks, 1):
            trip = _parse_key_value_lines("\n".join(lines))
            raw_value = trip.get("value", "").strip()
            split_label, terms = _split_price_text(raw_value)
            value_match = re.search(r"R\$\s*\d+(?:\.\d{3})*(?:,\d{1,2})?|\d+(?:\.\d{3})*,\d{2}", raw_value)
            departure = _parse_trip_date(trip.get("departure_date", ""))
            back = _parse_trip_date(trip.get("return_date", ""))
            card: dict[str, Any] = {
                "id": f"ai-trip-{index + 1}-{number}",
                "source": "external",
                "url": "",
                "image": AI_IMAGE_PLACEHOLDER,
                "title": trip.get("trip_name", "").strip(),
                "description": trip.get("description", "").strip() or trip.get("text", "").strip(),
                "buttonLabel": trip.get("button", "").strip() or "Quero saber mais",
                "openInNewTab": True,
            }
            if trip.get("image_query"):
                card["aiImageQuery"] = trip["image_query"].strip()
            page_ref = re.sub(r"[^a-z0-9-]", "", trip.get("page_ref", "").strip().lower().split("/")[-1])
            if page_ref:
                # O editor liga o card à página da agência com esse endereço (link e foto dela).
                card["pageSlug"] = page_ref
            if departure:
                card.update({"showDates": True, "departureDate": departure})
                if back and back >= departure:
                    card["returnDate"] = back
            if value_match:
                card.update({
                    "showPrice": True,
                    "pricePrefix": trip.get("price_label", "").strip() or split_label,
                    "priceValue": value_match.group(0).strip(),
                    "priceSuffix": trip.get("price_suffix", "").strip() or terms,
                })
            if card["title"]:
                cards.append(card)
        links_section: dict[str, Any] = {
            "type": "links",
            "enabled": True,
            "anchorId": _generate_anchor("links", "viagens", index),
            "title": intro.get("title", "").strip() or "Nossas viagens",
            "subtitle": intro.get("subtitle", "").strip(),
            "items": cards,
            "carouselEnabled": len(cards) > 3,
        }
        if intro.get("label"):
            links_section["headingLabel"] = intro["label"].strip()
        return links_section

    return None


AI_IMAGE_PLACEHOLDER = "data:image/svg+xml;base64," + base64.b64encode(
    b'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">'
    b'<rect width="1200" height="800" fill="#e2e8f0"/>'
    b'<path d="M420 460l120-140 90 100 60-70 110 110z" fill="#94a3b8"/>'
    b'<circle cx="720" cy="270" r="35" fill="#94a3b8"/>'
    b'<text x="600" y="550" text-anchor="middle" font-family="sans-serif" font-size="32" fill="#475569">Substitua pela sua imagem</text></svg>'
).decode("ascii")


def _fill_ai_image_placeholders(section: dict[str, Any]) -> None:
    image_fields = {
        "hero": ("backgroundImage", "mobileBackgroundImage"),
        "banner_card": ("backgroundImage",),
        "photo": ("image",),
        "biography": ("image", "mobileImage"),
    }
    for field in image_fields.get(section["type"], ()):
        section[field] = AI_IMAGE_PLACEHOLDER
    if section["type"] == "story":
        section["images"] = [AI_IMAGE_PLACEHOLDER]
    if section["type"] == "itinerary":
        for day in section["days"]:
            day["image"] = AI_IMAGE_PLACEHOLDER
    # Depoimentos ficam sem foto: a seção mostra as iniciais do nome até a agência enviar uma.


# Palavras de cada link do menu e a seção para onde ele leva.
MENU_TARGETS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("ROTEIRO", "ITINERARIO", "PROGRAMACAO", "DIA A DIA", "CRONOGRAMA"), ("itinerary",)),
    (("PRECO", "PRECOS", "VALOR", "VALORES", "INVESTIMENTO", "PACOTE", "PACOTES", "TARIFA"), ("prices",)),
    (("DUVIDA", "DUVIDAS", "PERGUNTA", "PERGUNTAS", "FAQ"), ("faq",)),
    (("DEPOIMENTO", "DEPOIMENTOS", "AVALIACOES", "CLIENTES"), ("testimonials",)),
    (("SOBRE", "QUEM SOMOS", "AGENCIA", "NOS"), ("biography",)),
    (("VIAGENS", "VIAGEM", "DESTINOS", "ROTEIROS", "SAIDAS", "PACOTES"), ("links",)),
    (("INCLUSO", "INCLUSOS", "INCLUI", "BENEFICIOS", "DIFERENCIAIS", "VANTAGENS"), ("reasons", "story")),
    (("VOO", "VOOS", "AEREO"), ("flight_details",)),
    (("VIDEO",), ("featured_video",)),
    (("EXPERIENCIA", "DESTINO", "HOSPEDAGEM", "HOTEL"), ("story", "reasons")),
    (("CONTATO", "RESERVA", "RESERVAR", "FALE"), ("cta",)),
)


PHOTO_SECTION_TYPES = frozenset({"hero", "banner_card", "photo", "biography", "story", "itinerary"})
# Endereço de uma imagem enviada no chat (biblioteca da agência): http(s) ou /uploads/.
SENT_PHOTO_RE = re.compile(r"^(?:https?://|/uploads/)\S+$", re.I)
SENT_PHOTO_FIELDS = {
    "hero": ("backgroundImage", "mobileBackgroundImage"),
    "banner_card": ("backgroundImage",),
    "photo": ("image",),
    "biography": ("image", "mobileImage"),
}


def _sent_photo_urls(value: str) -> list[str]:
    """Endereços em "Imagem:" (um ou vários, separados por "|", vírgula ou linha)."""
    urls = []
    for part in re.split(r"[|,\n]", value or ""):
        url = part.strip().strip("<>()[]`\"'")
        if SENT_PHOTO_RE.match(url) and url not in urls:
            urls.append(url)
    return urls[:10]


def _apply_sent_photos(section: dict[str, Any], urls: list[str]) -> None:
    """Coloca a(s) foto(s) enviada(s) na seção. aiStockPhoto avisa o editor que é foto nova (numa
    troca, ela entra no lugar da atual); sem crédito de banco de fotos."""
    kind = section.get("type")
    if kind in SENT_PHOTO_FIELDS:
        for field_name in SENT_PHOTO_FIELDS[kind]:
            section[field_name] = urls[0]
    elif kind == "story":
        section["images"] = urls
    elif kind == "itinerary":
        days = [day for day in section.get("days") or [] if isinstance(day, dict)]
        for day, url in zip(days, urls):
            day["image"] = url
    else:
        return
    section.pop("aiImageQuery", None)
    section["aiStockPhoto"] = True
    section["photoCredits"] = []
# Numa troca, estes campos não contam como "pedidos": foto vem do banco (aiStockPhoto) e
# âncora/identificador ficam os da seção que já está na página.
SWAP_FIXED_KEYS = frozenset({
    "type", "enabled", "anchorId", "sectionId", "id",
    "backgroundImage", "mobileBackgroundImage", "image", "mobileImage", "images",
})


def _answered_keys(section_name: str, section: dict[str, Any], index: int) -> list[str] | None:
    """Campos que a resposta trouxe numa troca: os que diferem da mesma seção sem nenhum campo.
    Com isso "troca só a foto do banner" não apaga título, roteiro ou cards da seção atual."""
    try:
        empty = _parse_ai_section_block(section_name, "", index)
    except Exception:  # noqa: BLE001 - sem a referência, a troca segue a regra antiga
        return None
    if not empty:
        return None
    return [
        key for key, value in section.items()
        if key not in SWAP_FIXED_KEYS and not key.startswith(("ai", "_")) and value != empty.get(key)
    ]


# Nomes de várias palavras que têm um equivalente de uma palavra só.
MENU_ONE_WORD = {
    "O QUE INCLUI": "Inclui",
    "O QUE ESTA INCLUSO": "Inclui",
    "INCLUI E NAO INCLUI": "Inclui",
    "ITENS INCLUSOS": "Inclui",
    "PERGUNTAS FREQUENTES": "Dúvidas",
    "DUVIDAS FREQUENTES": "Dúvidas",
    "ROTEIRO DIA A DIA": "Roteiro",
    "DIA A DIA": "Roteiro",
    "PRECOS E PACOTES": "Preços",
    "VALORES E PACOTES": "Preços",
    "FALE CONOSCO": "Contato",
    "FALE COM A GENTE": "Contato",
    "QUEM SOMOS": "Sobre",
    "SOBRE NOS": "Sobre",
    "SOBRE A AGENCIA": "Sobre",
    "OUTRAS VIAGENS": "Viagens",
    "MAIS VIAGENS": "Viagens",
    "PROXIMAS VIAGENS": "Viagens",
    "DETALHES DO VOO": "Voos",
    "RESERVE AGORA": "Reservar",
    "RESERVE JA": "Reservar",
}
MENU_SKIP_WORDS = frozenset(
    {"O", "A", "OS", "AS", "DE", "DA", "DO", "DAS", "DOS", "E", "QUE", "COM", "PARA", "NOSSO", "NOSSA",
     "NOSSOS", "NOSSAS", "SEU", "SUA", "SEUS", "SUAS", "UM", "UMA", "NO", "NA", "NOS", "NAS", "EM", "MAIS"}
)


def one_word_menu_label(label: str) -> str:
    """Nome do item do Menu do topo com no máximo 1 palavra: o equivalente conhecido ("O que
    inclui" → "Inclui") ou a primeira palavra que não é artigo nem preposição."""
    words = [word for word in re.split(r"\s+", (label or "").strip()) if word]
    if len(words) <= 1:
        return words[0] if words else ""
    key = " ".join(re.sub(r"[^A-Z ]", " ", _normalize_text(label)).split())
    if key in MENU_ONE_WORD:
        return MENU_ONE_WORD[key]
    for word in words:
        clean = word.strip(".,;:!?()[]\"'")
        if clean and _normalize_text(clean) not in MENU_SKIP_WORDS:
            return clean[:1].upper() + clean[1:]
    return words[0].strip(".,;:!?()[]\"'")


def _link_header_menu(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Liga os itens do Menu do topo às seções da página e deixa o menu em primeiro."""
    headers = [section for section in sections if section.get("type") == "header"]
    others = [section for section in sections if section.get("type") != "header"]
    if not headers:
        return sections
    header = headers[0]
    links = []
    used: set[str] = set()
    def stems(text: str) -> set[str]:
        return {word[:5] for word in re.sub(r"[^A-Z ]", " ", _normalize_text(text)).split() if len(word) >= 4}

    def heading(section: dict[str, Any]) -> str:
        return " ".join(str(section.get(key) or "") for key in ("title", "headingLabel", "badge", "label"))

    if "_menuItems" not in header:
        # Sem itens na resposta (ex.: só deixar o menu transparente): os atuais ficam.
        header.pop("links", None)
        for extra in headers[1:]:
            extra.pop("_menuItems", None)
        return [header, *others]
    for item in header.pop("_menuItems", []):
        if item["targetType"] != "section" or item["target"]:
            # Já veio com o identificador da seção (ou é link externo).
            used.add(item["target"])
            links.append(item)
            continue
        label = item["label"]
        words = f" {re.sub(r'[^A-Z ]', ' ', _normalize_text(label))} "
        # Primeiro pelo título da seção ("Nacionais" → "Pacotes nacionais"), o que separa seções
        # repetidas do mesmo tipo; depois pelas palavras de cada tipo.
        label_stems = stems(label)
        target = next(
            (
                s for s in others
                if s.get("type") not in {"hero", "banner_card", "photo", "countdown", "agency_footer"}
                and s.get("anchorId") not in used and label_stems and label_stems & stems(heading(s))
            ),
            None,
        )
        for keywords, types in MENU_TARGETS if target is None else ():
            if any(f" {word} " in words for word in keywords):
                target = next(
                    (s for t in types for s in others if s.get("type") == t and s.get("anchorId") not in used),
                    None,
                )
                if target:
                    break
        if target:
            used.add(target["anchorId"])
            links.append({**item, "target": target["anchorId"]})
        else:
            # Seção que não veio nesta resposta (ex.: só o menu foi trocado): o editor liga pelo
            # título das seções que já estão na página.
            links.append({**item, "aiTargetLabel": label})
    # Regra fixa: no máximo 1 palavra por item (a ligação acima usa o nome inteiro).
    header["links"] = [{**link, "label": one_word_menu_label(link["label"])} for link in links]
    for extra in headers[1:]:
        extra.pop("_menuItems", None)
    return [header, *others]


def _footer_last(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    footers = [section for section in sections if section.get("type") == "agency_footer"][:1]
    return [section for section in sections if section.get("type") != "agency_footer"] + footers


def build_page_base_config_from_reply(
    reply: str, current_config: Any | None = None, *, strict: bool = False
) -> tuple[Any, str | None]:
    is_valid, validation_error = _validate_ai_reply_format(reply)
    if not is_valid:
        raise HTTPException(status_code=400, detail=validation_error)
    if strict:
        for line in reply.splitlines():
            match = SECTION_HEADER_RE.match(line)
            if match and not _canonical_section_name(match.group(1)):
                raise HTTPException(
                    status_code=400,
                    detail="A sugestão contém uma seção não suportada. Peça à IA uma nova estrutura com as seções disponíveis.",
                )
    meta, blocks = _split_sections(reply)
    sections: list[dict[str, Any]] = []
    hero_title: str | None = None

    for index, (section_name, block) in enumerate(blocks):
        parsed_section = _parse_ai_section_block(section_name, block, index)
        if not parsed_section:
            continue
        fields = _parse_key_value_lines(block)
        # Troca de uma seção que já existe: o editor põe esta no lugar dela.
        replaces = fields.get("replaces", "").strip().strip("`\"'")
        if replaces:
            parsed_section["aiReplaces"] = replaces.split()[0]
        # Foto enviada pelo usuário no chat ("Imagem: endereço"): entra no lugar da atual e o banco
        # de fotos não é consultado para esta seção.
        sent_photos = _sent_photo_urls(fields.get("image_url", "")) if parsed_section["type"] in PHOTO_SECTION_TYPES else []
        # Termos para o banco de fotos. Numa troca, só com "Busca de imagem" (foto nova pedida);
        # numa estrutura nova, sempre (sem termos, entra uma foto genérica do tipo da seção).
        if parsed_section["type"] in PHOTO_SECTION_TYPES and not sent_photos:
            # "Sugestão de imagem" (nome antigo do campo) vale como "Busca de imagem", inclusive numa
            # troca: linha de foto numa troca é foto nova pedida.
            image_query = fields.get("image_query", "").strip() or fields.get("image_suggestion", "").strip()
            if image_query or not replaces:
                parsed_section["aiImageQuery"] = image_query
        # "Etiqueta" é o selo acima do título nas seções que o mostram.
        if (
            parsed_section["type"] in {"banner_card", "itinerary", "faq", "featured_video"}
            and fields.get("label")
            and not parsed_section.get("headingLabel")
        ):
            parsed_section["headingLabel"] = fields["label"].strip()
        if parsed_section["type"] in {"story", "banner_card", "featured_video"} and fields.get("button"):
            parsed_section["ctaEnabled"] = True
            parsed_section["ctaLabel"] = fields["button"].strip()
        if replaces and parsed_section["type"] != "header":
            # O Menu do topo já marca o que mudou (_header_section).
            answered = _answered_keys(section_name, parsed_section, index)
            if answered is not None:
                parsed_section["aiSetKeys"] = answered
        _fill_ai_image_placeholders(parsed_section)
        if sent_photos:
            _apply_sent_photos(parsed_section, sent_photos)
        sections.append(parsed_section)
        if not hero_title and parsed_section.get("type") == "hero":
            hero_title = str(parsed_section.get("title") or "").strip() or None

    if not sections:
        raise HTTPException(status_code=400, detail="Não foi possível identificar seções válidas na resposta da IA.")
    sections = _footer_last(_link_header_menu(sections))

    base_config = deepcopy(current_config) if isinstance(current_config, dict) else {}
    base_config["sections"] = sections
    return base_config, hero_title or (meta.get("Tipo de página") or None)

def _is_reasoning_model(model: str) -> bool:
    return (model or "").strip().lower().startswith(("gpt-5", "o1", "o3", "o4"))


def _model_kwargs(model: str) -> dict[str, object]:
    # Modelos que raciocinam antes de responder (gpt-5, o-series) não aceitam temperature;
    # com esforço "low" a resposta começa bem mais cedo, e a estrutura da página não pede
    # raciocínio longo.
    if _is_reasoning_model(model):
        return {"reasoning": {"effort": "low"}}
    return {"temperature": 0.2}


def _request_ai_reply(
    client: object,
    model: str,
    instructions: str,
    input_items: list[dict[str, object]],
) -> str:
    return _extract_response_text(_request_ai_reply_response(client, model, instructions, input_items))


def _request_ai_reply_response(
    client: object,
    model: str,
    instructions: str,
    input_items: list[dict[str, object]],
) -> object:
    return client.responses.create(
        model=model,
        instructions=instructions,
        input=input_items,
        **_model_kwargs(model),
    )


def _extract_usage_data(response: object) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cached_input_tokens": 0}

    def _read_int(*names: str) -> int:
        for name in names:
            value = getattr(usage, name, None)
            if isinstance(value, (int, float)):
                return int(value)
        return 0

    input_tokens = _read_int("input_tokens", "prompt_tokens")
    output_tokens = _read_int("output_tokens", "completion_tokens")
    total_tokens = _read_int("total_tokens") or (input_tokens + output_tokens)
    cached_input_tokens = _read_int("cached_input_tokens")

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_input_tokens": cached_input_tokens,
    }


def _estimate_model_cost_usd(model: str, usage: dict[str, int]) -> float:
    pricing = MODEL_PRICING_USD.get(model, MODEL_PRICING_USD["gpt-5.4"])
    input_tokens = max(int(usage.get("input_tokens", 0) or 0), 0)
    cached_input_tokens = max(int(usage.get("cached_input_tokens", 0) or 0), 0)
    output_tokens = max(int(usage.get("output_tokens", 0) or 0), 0)
    billed_input_tokens = max(input_tokens - cached_input_tokens, 0)
    estimated = (
        (billed_input_tokens / 1_000_000) * pricing["input"]
        + (cached_input_tokens / 1_000_000) * pricing["cached_input"]
        + (output_tokens / 1_000_000) * pricing["output"]
    )
    return round(estimated, 6)


def _build_ai_conversation_input(
    conversation: list[ChatMessage],
    attachments: list[ChatAttachment] | None = None,
) -> list[dict[str, object]]:
    input_items: list[dict[str, object]] = []
    normalized_conversation = [item for item in conversation if (item.content or "").strip()]

    for item in normalized_conversation[:-1]:
        input_items.append({"role": item.role, "content": item.content.strip()})

    last_message = normalized_conversation[-1] if normalized_conversation else None
    if last_message is None:
        raise HTTPException(status_code=400, detail="Mensagem do usuário ausente.")

    last_content: list[dict[str, object]] = [
        {
            "type": "input_text",
            "text": last_message.content.strip()
            or "Analise os arquivos anexados e responda seguindo o formato do Construtor Roteiro Online.",
        }
    ]
    for attachment in attachments or []:
        encoded_file = base64.b64encode(attachment.data).decode("ascii")
        mime_type = attachment.content_type or "application/octet-stream"
        if mime_type.lower() in CHAT_IMAGE_TYPES:
            # Foto vai como imagem (a IA vê a foto); arquivo (PDF, texto) vai como arquivo.
            last_content.append({"type": "input_image", "image_url": f"data:{mime_type};base64,{encoded_file}", "detail": "low"})
            continue
        last_content.append(
            {
                "type": "input_file",
                "filename": attachment.filename or "arquivo",
                "file_data": f"data:{mime_type};base64,{encoded_file}",
                "detail": "low",
            }
        )
    input_items.append({"role": last_message.role, "content": last_content})
    return input_items


def _run_ai_reply(
    conversation: list[ChatMessage],
    attachments: list[ChatAttachment] | None = None,
    *,
    validate_output: bool = True,
    model_override: str | None = None,
    context: str = "",
) -> tuple[str, str, dict[str, int]]:
    if not conversation:
        raise HTTPException(status_code=400, detail="Conversa vazia.")

    model = (model_override or settings.gpt_model or "gpt-5.4").strip() or "gpt-5.4"
    client = _load_openai_client()
    input_items = _build_ai_conversation_input(conversation, attachments)

    try:
        response = _request_ai_reply_response(client, model, _instructions(context), input_items)
        reply = _extract_response_text(response)
        if validate_output:
            problem = _chat_reply_problem(reply)
            if problem:
                response = _request_ai_reply_response(
                    client,
                    model,
                    _build_correction_instructions(problem, context),
                    input_items,
                )
                reply = _extract_response_text(response)
                problem = _chat_reply_problem(reply)
                if problem:
                    raise HTTPException(status_code=502, detail=f"A OpenAI retornou uma resposta fora do padrão: {problem}")
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - network/runtime guard
        raise HTTPException(status_code=502, detail=f"Falha ao consultar a OpenAI: {exc}") from exc

    if not reply:
        raise HTTPException(status_code=502, detail="A OpenAI não retornou uma resposta válida.")

    usage = _extract_usage_data(response)
    return reply, model, usage


def stream_ai_assistant_reply(
    conversation: list[ChatMessage],
    attachments: list[ChatAttachment] | None = None,
    *,
    model_override: str | None = None,
    context: str = "",
) -> Iterator[dict[str, Any]]:
    """Resposta do assistente em eventos, para o chat mostrar o andamento enquanto a IA escreve:
    {"type": "status", "step": ...} nas etapas, {"type": "delta", "text": ...} a cada trecho,
    {"type": "replace", "text": ...} se a resposta precisou ser refeita e, no fim,
    {"type": "done", "reply", "model", "usage"}. Erros saem como HTTPException."""
    if not conversation:
        raise HTTPException(status_code=400, detail="Conversa vazia.")
    model = (model_override or settings.gpt_model or "gpt-5.4").strip() or "gpt-5.4"
    client = _load_openai_client()
    input_items = _build_ai_conversation_input(conversation, attachments)

    yield {"type": "status", "step": "thinking"}
    parts: list[str] = []
    usage: dict[str, int] = {}
    try:
        stream = client.responses.create(
            model=model,
            instructions=_instructions(context),
            input=input_items,
            stream=True,
            **_model_kwargs(model),
        )
        writing = False
        for event in stream:
            event_type = getattr(event, "type", "")
            if event_type == "response.output_text.delta":
                delta = getattr(event, "delta", "") or ""
                if not delta:
                    continue
                if not writing:
                    writing = True
                    yield {"type": "status", "step": "writing"}
                parts.append(delta)
                yield {"type": "delta", "text": delta}
            elif event_type == "response.completed":
                usage = _extract_usage_data(getattr(event, "response", None))
            elif event_type in {"response.failed", "error"}:
                error = getattr(getattr(event, "response", None), "error", None) or getattr(event, "message", "")
                raise RuntimeError(str(error) or "falha na geração")
        reply = "".join(parts).strip()

        problem = _chat_reply_problem(reply)
        if problem:
            # Raro: a estrutura veio sem nenhuma seção válida. Refaz uma vez, sem streaming.
            yield {"type": "status", "step": "fixing"}
            response = _request_ai_reply_response(client, model, _build_correction_instructions(problem, context), input_items)
            reply = _extract_response_text(response)
            usage = _extract_usage_data(response)
            if _chat_reply_problem(reply):
                raise HTTPException(status_code=502, detail="A IA respondeu fora do padrão. Tente reformular a mensagem.")
            yield {"type": "replace", "text": reply}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - network/runtime guard
        raise HTTPException(status_code=502, detail=f"Falha ao consultar a OpenAI: {exc}") from exc

    if not reply:
        raise HTTPException(status_code=502, detail="A OpenAI não retornou uma resposta válida.")
    yield {"type": "done", "reply": reply, "model": model, "usage": usage}


TRANSCRIPTION_MODELS = ("gpt-4o-mini-transcribe", "whisper-1")


def transcribe_audio(data: bytes, filename: str, content_type: str | None) -> str:
    """Texto falado num áudio do chat (português), para a mensagem do assistente."""
    if not data:
        raise HTTPException(status_code=400, detail="Áudio vazio.")
    client = _load_openai_client()
    last_error: Exception | None = None
    for model in TRANSCRIPTION_MODELS:
        try:
            result = client.audio.transcriptions.create(
                model=model,
                file=(filename or "audio.webm", data, content_type or "application/octet-stream"),
                language="pt",
            )
            text = getattr(result, "text", None)
            if text is None and isinstance(result, str):
                text = result
            return (text or "").strip()
        except Exception as exc:  # pragma: no cover - depende do modelo disponível na conta
            last_error = exc
            logger.warning("ai_transcription_failed model=%s error=%s", model, exc)
    raise HTTPException(status_code=502, detail=f"Não foi possível transcrever o áudio: {last_error}")


def generate_ai_assistant_reply_with_usage(
    conversation: list[ChatMessage],
    attachments: list[ChatAttachment] | None = None,
    *,
    validate_output: bool = True,
    model_override: str | None = None,
) -> tuple[str, str, dict[str, int], float]:
    reply, model, usage = _run_ai_reply(
        conversation,
        attachments,
        validate_output=validate_output,
        model_override=model_override,
    )
    return reply, model, usage, _estimate_model_cost_usd(model, usage)


def generate_ai_assistant_reply(
    conversation: list[ChatMessage],
    attachments: list[ChatAttachment] | None = None,
    *,
    validate_output: bool = True,
    model_override: str | None = None,
    context: str = "",
) -> str:
    reply, _, _ = _run_ai_reply(
        conversation,
        attachments,
        validate_output=validate_output,
        model_override=model_override,
        context=context,
    )
    return reply
