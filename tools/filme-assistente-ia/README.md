# Filme "Conte a viagem" (Assistente IA do Roteiro Online)

Vídeo de 27 s, 1920x1080, 30 fps, com locução: uma frase digitada no Assistente IA vira a página
completa de Gramado e Canela, o preço muda digitando, o visual muda com um clique, a página abre no
celular e o cliente chama. Feito com a skill **motionmaxxing** (runtime GSAP em HTML, render quadro a
quadro no Chromium + ffmpeg).

- `final.mp4`: o vídeo final, com trilha.
- `index.html`: o filme editável (abra num servidor local ou renderize com o `render.mjs` da skill).
- `STORYBOARD.md`: ideia, mundo, cenas e locução. `NOTE.md`: o que é real, o que é ilustrativo, gates e números.
- `audio/`: locução por fala (`vo/lineNN.wav`), trilha sintetizada (`music.wav`), efeitos (`sfx/`),
  mixagem final (`mix.wav`) e uma versão **só voz + efeitos** (`voz-e-efeitos.wav`) para trocar a música.
- `assets/`: capturas reais do editor (3x, convertidas para WebP), páginas no celular, placas das fotos, logo.
- `captura/`: os scripts que levantam a demonstração e capturam o editor real (usam `tools/help-media`).
- `ferramentas/`: síntese da trilha e dos efeitos, preparo dos assets, autoteste de seek.

## Renderizar de novo

Precisa de Node 22+, ffmpeg e Chromium, e da pasta da skill motionmaxxing (`$SKILL`).

```bash
# rascunho rápido (meia resolução)
node $SKILL/scripts/render.mjs index.html draft.mp4 --scale 0.5 --audio audio/mix.flac
# final (motion blur de obturador + grão)
node $SKILL/scripts/render.mjs index.html final.mp4 --audio audio/mix.flac --shutter 180 --subframes 8 --grain 0.03 --grain-seed 7
# revisão
python3 $SKILL/scripts/look.py final.mp4 --out look-final --expect 27 --expect-audio
node $SKILL/scripts/lint.mjs index.html
```

Como root no Linux, o Chromium precisa de `--no-sandbox` (aponte `CHROME_PATH` para um script que
chame o Chromium com essa flag).

## Trocar a voz ou a música

- Locução: `audio/vo.txt` + `voice.py vo` da skill (ElevenLabs). Os tempos de cada fala estão em
  `NOTE.md`; se a duração mudar, ajuste os quadros no `index.html`.
- Música: substitua `audio/music.wav` por uma faixa licenciada de 27 s e rode o `mix.py` com os mesmos
  `--vo` e `--events audio/events.json` (comando completo no `NOTE.md`).

## Recapturar o editor

Os scripts em `captura/` seguem o mesmo ambiente de `tools/help-media/README.md`: API em `:8000` com
`GPT_KEY=falsa OPENAI_BASE_URL=http://127.0.0.1:8765/v1` (IA de demonstração `ia-falsa.py`), painel em
`:5173`, `seed.mjs` feito. Ordem: `setup-page.mjs` (sobe as fotos e cria a página em branco),
`capture-main.mjs`, `capture-type.mjs`, `capture-phone.mjs`, `real-pages.mjs`; depois
`ferramentas/prep_assets.py <pasta das capturas> <pasta do filme>`.
