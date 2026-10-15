# NOTE: "Conte a viagem" (Roteiro Online), 27,6 s, 1920x1080, 30 fps, com som

## A ideia, em uma linha
Um documentário de interface de uma tarefa real: uma frase comum digitada no Assistente IA vira a página completa de Gramado e Canela, o preço muda digitando, o visual muda com um clique, a página abre no celular e o cliente chama. O ponteiro do filme é a **seta de navegação do próprio logo** (recortada do arquivo oficial) e, no fim, ela volta para dentro do pin.

Por quê: a prova é o produto funcionando de verdade, não uma promessa em letreiro. A seta do logo dá identidade sem rótulos, e o filme não funcionaria para um concorrente (seções de roteiro, dia a dia, preço por pessoa, botão de WhatsApp, editor e assistente reais).

## Cenas e o que cada uma compra
| Cena | Tempo | Compra: o espectador... |
|---|---|---|
| S1 gancho | 0-2,8 s | vê que basta escrever uma frase comum, do jeito que mandaria no WhatsApp |
| S2 prova (herói) | 2,8-10,4 s | acredita que a página inteira sai pronta da frase (a IA monta as seções; "Inserir no fim"; a página em branco vira Gramado; a câmera desce até o preço) |
| S3 prova | 10,4-17,2 s | vê que mudar é clicar e digitar (1.290 → 1.190) e que trocar o visual é um clique (layout Cartão); fecha com a frase da LP "Mais fácil que editar no Canva!" |
| S4 prova | 17,2-21,5 s | acredita que serve para qualquer viagem e fica bonito no celular (o celular sai do editor; passam páginas reais publicadas) |
| S5 cta | 21,5-27,6 s | fica com a frase da marca e o nome (o cliente chama; o logo pousa e a seta volta para o pin) |

## O que é real, o que é ilustrativo
**Real (capturado do produto rodando, sem montagem):**
- Todo o editor: o sistema do repositório foi levantado localmente (API FastAPI + painel Vue + Postgres), com a agência de demonstração do próprio repositório ("Rota Sul Viagens", `tools/help-media/seed.mjs`). Capturas em 3x de cada estado (digitação letra a letra, a resposta da IA em 12 estados, "Inserir no fim", página aplicada, rolagem, painel de preços, campo de preço digitado, layouts do banner, prévia no celular).
- A resposta da IA é a **IA de demonstração do repositório** (`tools/help-media/ia-falsa.py`), a mesma usada para gravar a animação da LP: ela devolve sempre a estrutura de Gramado e Canela. O fluxo, as telas e as seções aplicadas são os reais; o texto da resposta é o roteiro de demonstração do repositório.
- As três páginas do "qualquer viagem" são páginas **publicadas de verdade** em roteiroonline.com (Status Viajar: Foz do Iguaçu; Beth Tur: Itália Magnífica; Ecoar Ecoturismo: Abrolhos), as mesmas que a página de vendas já mostra em "Exemplos reais". Capturadas em celular, 3x, só leitura.
- Moldura do celular: as regras CSS `.ed-phone` do próprio editor. Cartão "Novo contato": as regras `.lp-float` da própria LP.
- Logo: arquivos oficiais `Logo Cor` e `Logo Branco` do repositório; a seta foi recortada por máscara, sem redesenho.
- Frases: "Conte a viagem do seu jeito", "Mais fácil que editar no Canva!" e "Seu cliente não compra o que não consegue imaginar" são da LP.

**Ilustrativo (declarado aqui, nunca na tela):**
- A viagem de Gramado e Canela, a data, o preço (R$ 1.290 → R$ 1.190) e o "Quero reservar 2 lugares" são conteúdo de demonstração.
- O campo do assistente foi redimensionado para 3 linhas (pela alça dele mesmo) para a frase aparecer inteira; o corretor ortográfico foi desligado na captura.
- O cursor de texto (a barrinha piscando) é desenhado por cima das capturas, nas posições medidas no navegador (as capturas escondem o cursor nativo).

**Fotos (todas em domínio público, Wikimedia Commons):**
- Catedral de Pedra, Canela: Renato Soares / MTur Destinos (Ministério do Turismo), domínio público.
- Largo/Rua Coberta (Dia 1), Snowland (Dia 3), Reino do Chocolate (Dia 4), Gramado: Renato Soares / MTur Destinos, domínio público.
- Cascata do Caracol (Dia 2): Fernando Schultz Aldado, domínio público.
Não há obrigação de crédito; deixo a lista acima por boa prática.

## Som
- Locução: ElevenLabs, voz configurada no ambiente (`ELEVENLABS_VOICE_ID`), modelo eleven_multilingual_v2. 7 falas, 16,3 s. **Não consegui ouvir a voz**: vale escutar o sotaque e a pronúncia de "Roteiro Online".
- Trilha e efeitos: a chave da ElevenLabs não tem permissão de música nem de efeitos (`music_generation`, `sound_generation`), então ambos foram **sintetizados em código** (`ferramentas/synth_music.py`, `ferramentas/synth_sfx.py`): violão dedilhado em levada de bossa (síntese aditiva), pad, shaker, baixo e kick suaves, a 100 BPM, com a levada entrando no quadro em que a página aparece (6,1 s), mais brilho quando o celular sai do editor (18,1 s) e o acorde final quando o logo pousa (25,3 s); respiros de 8 a 10 dB antes desses três momentos. Efeitos: teclado (um tick por rajada de digitação), clique, whoosh, notificação, pouso do logo.
- Também entrego `audio/voz-e-efeitos.wav` (sem trilha) para trocar a música por uma licenciada, se preferirem.

## Gates (números dos scripts)
(preenchido após o render)

## Quadros (uma frase por quadro do sheet)
(preenchido após o render)

## O que eu ainda melhoraria
(preenchido após o render)
