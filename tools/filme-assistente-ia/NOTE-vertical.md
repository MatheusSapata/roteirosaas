# NOTE: "Conte a viagem" vertical (anúncio responsivo), 29,6 s, 1080x1920, 30 fps, com som

## A ideia, em uma linha
O mesmo documentário de interface da versão 16:9, reescrito para o celular: começa na dor de quem vende viagem (o roteiro mandado em textão no WhatsApp e o cliente que só pergunta "quanto fica?"), mostra a frase virando a página completa, o preço e o visual mudando em tela dividida (edita em cima, aparece embaixo), passa por quatro tipos de viagem reais no celular e fecha no logo com o botão **Saiba mais agora**.

## Formato: 9:16 com tudo o que importa dentro do 4:5
- Quadro 1080x1920. A faixa **y 285 a 1635** (1080x1350, o corte 4:5 central) guarda todo o conteúdo: textos, campo digitado, prévia, preços, celular, logo e CTA.
- Fora da faixa só há mundo: o cabeçalho e a barra de digitação do chat, o chão do editor, as placas de foto. Em 4:5 nada some; em 9:16 a tela fica cheia.
- Entrego também `final-vertical-4x5.mp4`, o corte 1080x1350 tirado do mesmo render (ffmpeg `crop=1080:1350:0:285`), para quem quiser subir o 4:5 direto.

## Locução (contínua, sem respiros longos)
Uma tomada só, ElevenLabs (mesma voz do ambiente), velocidade 1,06, 87 palavras em 28,5 s, colocada a 0,25 s:
> Você vende viagem e ainda manda o roteiro em textão no WhatsApp? Agora é só contar a viagem do seu jeito, numa frase. O Roteiro Online monta a página inteira: banner, roteiro dia a dia, o que está incluso, preços e dúvidas. Mudou o preço? Clica e digita. Quer outro visual? Um clique, sem refazer arte nenhuma. Serve pra excursão, pacote, ecoturismo ou grupo internacional, e abre lindo no celular do cliente. Porque seu cliente não compra o que não consegue imaginar. Roteiro Online. Saiba mais agora.

Os cortes de imagem caem nas palavras: o chat corta no "Agora", o banner aparece no "banner", a página rola e para em cada seção quando ela é dita, o campo é clicado no "Clica", o layout troca no "clique", cada página real entra no nome do tipo de viagem, o botão pousa no "Saiba".

## Cenas
| Cena | Tempo | O espectador... |
|---|---|---|
| Gancho | 0-3,9 s | se reconhece: o textão de Gramado rolando sem fim, o PDF "FINAL-v3" e a cliente que responde "Oi! Quanto fica? 😅". Texto na tela: "Você vende viagem?" e "Ainda manda roteiro em textão?" |
| S1 | 3,9-6,5 s | vê a frase sendo digitada no Assistente IA real ("Conte a viagem do seu jeito.") |
| S2 + página | 6,5-12,9 s | vê a IA montar as seções, "Inserir no fim", a página aparecer e rolar sozinha por dia a dia, incluso, preços e dúvidas |
| S3 | 12,9-18,4 s | vê, em tela dividida, o preço digitado em cima mudar o card da página embaixo (R$ 1.290 → 1.190, passando por 11 e 119), e o layout Cartão trocar o banner com um clique; fecha com "Mais fácil que editar no Canva!" |
| S4 | 18,4-23,3 s | vê páginas reais publicadas por agências no celular: Foz (excursão), Gramado (pacote), Abrolhos (ecoturismo), Itália (grupo internacional), e Gramado de novo, rolando |
| S5 | 23,3-29,6 s | vê o cliente chamar ("Quero reservar 2 lugares"), o logo pousar com a seta voltando ao pin, e o botão **Saiba mais agora** |

## O que é real, o que é ilustrativo
- **Real:** todo o editor, o assistente, as seções, a prévia, o painel de preço, os layouts e a prévia ao vivo do preço (as telas de baixo da tela dividida são as mesmas capturas, mostrando o card mudando a cada tecla, como no produto). As páginas de Foz, Itália e Abrolhos são publicadas de verdade. Moldura do celular (`.ed-phone`), cartão "Novo contato" (`.lp-float`) e o botão (`.lp-btn` da LP no fundo noturno: menta com texto escuro) seguem as regras CSS do próprio repositório. Logo: arquivos oficiais.
- **Ilustrativo:** o chat do gancho é uma reconstrução genérica de app de mensagens (sem marca nem logo do WhatsApp), com contato, horários e textão de demonstração ("Luciana Souza" é nome fictício). O conteúdo de Gramado e Canela, datas, preços e o "Quero reservar 2 lugares" são de demonstração, como na 16:9.
- Emojis do chat: fonte Noto Color Emoji do sistema (se renderizar em outra máquina, instale `fonts-noto-color-emoji`).

## Som
- `audio-v/mix.wav`: voz + trilha + efeitos, mixagem final.
- **`audio-v/trilha-e-efeitos.wav`: só trilha e efeitos sonoros, sem voz** (o arquivo separado pedido). Sem abaixamento sob a voz, normalizado a -14 LUFS, para usar com outra locução ou outra edição.
- Trilha sintetizada em código (mesmo violão de bossa a 100 BPM da 16:9, em nova grade): a levada entra junto da página (8,8 s), clareia quando o celular entra (18,4 s) e o acorde final cai com o botão (28,0 s), com respiros de 8 a 10 dB antes desses momentos.
- Efeitos: rolagem do chat, notificação da resposta, teclado (um tick por rajada), cliques, whoosh na revelação e no celular, toques nas trocas de página, notificação do cliente, pouso do logo, toque no botão.

## Gates (números dos scripts, em `final-vertical.mp4`)
- **G0 render existe:** PASS. 29,60 s, 888 quadros, 1080x1920, h264, áudio AAC presente (`look.py --expect 29.6 --expect-audio`).
- **G1 prova legível:** por olho no sheet. Campo do assistente com o texto a ~35 px; na tela dividida o campo de preço e o card ocupam a largura toda; título das seções da página a ~37 px.
- **G2 sem quadro vazio:** PASS. Nenhum trecho com mais de 3 quadros chapados.
- **G3 fim curto:** PASS. Logo + botão parados 1,13 s (faixa 0,6-1,4 s); último plano 2,93 s = 10 % do filme.
- **G4 um herói por quadro:** por olho no sheet. Na tela dividida são duas vistas do mesmo objeto (campo e card), lidas de cima para baixo.
- **G5 sem cara de página:** PASS em todas as regras (`lint.mjs --width 1080 --height 1920`).
- **Autoteste de seek:** 0 divergências em 24 saltos aleatórios (`Motion.selfTest`).
- **Corte 4:5:** conferido quadro a quadro em `quadros-vertical-4x5.jpg` (18 momentos): nenhum texto, campo, card, celular, logo ou botão sai da faixa.
- **Áudio:** -14,5 LUFS integrado, LRA 2,6 LU, pico real -1,5 dBTP no AAC, 99 % audível. Trilha 9 dB abaixo sob a voz.
- **Movimento:** variação média 3,6/255, **abaixo** da faixa de filmes feitos por pessoas (4,4-9,8). Somei câmera lenta na digitação e na tela dividida, deriva no chat e uma rolagem a mais no celular (subiu de 3,5 para 3,6/3,7). O que segura o número: as pausas de leitura (digitação, preço digitado, frase do Canva) e o fim parado com o logo e o botão.

## O que eu ainda melhoraria
- Ouvir a voz (não consigo escutar): pronúncia de "Roteiro Online", "ecoturismo" e o ritmo sem pausas.
- O chat do gancho é desenhado em HTML (genérico). Se tiverem uma captura real de conversa (com autorização e sem dados de cliente), fica ainda mais verdadeiro.
- Trocar a trilha sintetizada por uma música licenciada: use `audio-v/trilha-e-efeitos` como guia de tempo ou refaça só a trilha com o mesmo `music-plan.json`.
- O botão "Saiba mais agora" é imagem do vídeo; nas plataformas de anúncio o botão real de CTA fica por conta da plataforma.
