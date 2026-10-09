# Mídia da Central de Ajuda

Gera as telas, as demonstrações interativas e os vídeos curtos da Central de Ajuda
(`/admin/ajuda`) a partir do sistema rodando de verdade, numa agência de demonstração
("Rota Sul Viagens"). A saída vai para `frontend/src/help/media/<id>/` e entra no build.

- **Demonstração interativa**: uma tela por passo, nos temas claro e escuro
  (`passo-NN-light.webp`, `passo-NN-dark.webp`), e `passos.json` com a legenda e o ponto
  de clique de cada passo. Na Central, a pessoa clica no ponto destacado para avançar.
- **Vídeo** (quando o roteiro tem `video: true`): MP4 curto, sem som, com cursor,
  marca de clique e legenda. Toca em repetição na aba "Vídeo".

## Quando algo muda no sistema

1. Ajuste o roteiro em `roteiros/<id>.mjs` (seletores, legendas) se a tela mudou.
2. Rode `node gerar.mjs <id>` para refazer a mídia.
3. Revise o artigo em `frontend/src/help/content.ts` e troque a data `atualizado`.
4. Se o artigo cobre o assunto de uma aula, a aula passa a mostrar o artigo enquanto o
   vídeo dela for mais antigo que essa data. A ligação vem do campo **Artigo da Central
   de Ajuda** da aula (Admin Master › Aulas) ou de `substituiAulas` no artigo (trechos do
   título da aula). Gravou um vídeo novo para a aula? Ela volta a aparecer normalmente.

Artigo novo: crie `roteiros/<id>.mjs` a partir de `roteiros/_modelo.mjs` (o id é o mesmo
do artigo) e adicione o artigo em `content.ts`, com `tela` em cada passo apontando o
passo da demonstração.

## Como rodar

Precisa do sistema rodando localmente (API em `:8000` e painel em `:5173`) com o visual
novo liberado para todos (`PAGE_DESIGN_V2_ROLLOUT=all` na API) e do `ffmpeg` instalado.

```bash
cd tools/help-media
npm install                      # Playwright e as fontes do painel (@fontsource)

# 1. Agência de demonstração (uma vez, ou para recomeçar do zero)
HELP_ADMIN_EMAIL=superusuario@local HELP_ADMIN_PASSWORD=... \
HELP_PSQL_URL=postgresql://usuario:senha@localhost:5432/banco \
node seed.mjs

# 2. Mídia
node gerar.mjs                   # todos os roteiros
node gerar.mjs criar-pagina      # só os pedidos
node gerar.mjs --sem-video       # pula os vídeos
```

- `HELP_ADMIN_*`: um superusuário do banco local, só para criar a conta de demonstração.
- `HELP_PSQL_URL` (opcional): preenche as visitas dos últimos 30 dias do Dashboard.
- `HELP_API` / `HELP_APP`: outros endereços da API e do painel.
- `PW_CHROMIUM`: caminho de um Chromium já instalado.

Os roteiros que mudam dados (publicar, adicionar seção, duplicar) devolvem a demonstração
ao estado do `seed.mjs` antes e depois de gravar (`antesDeTudo` / `depoisDeTudo`).

## Estrutura

- `seed.mjs`: cria a conta, a agência, as páginas, os formulários, os leads e os pixels.
- `gerar.mjs`: roda os roteiros e grava a mídia.
- `roteiros/`: um arquivo por artigo, com os passos (veja `_modelo.mjs`).
- `lib/`: API, sessão do navegador, captura das telas, gravação do vídeo e dados da
  demonstração (`paginas.mjs`, `fotos.mjs`, `demo.mjs`).
