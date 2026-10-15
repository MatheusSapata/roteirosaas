# Storyboard: "Conte a viagem" (Roteiro Online)

## PAGE
- **Problema:** a agência tem uma viagem para vender e hoje explica tudo num textão no WhatsApp ou passa a noite no Canva montando uma arte que precisa ser refeita a cada mudança de preço ou data.
- **Público:** donos e vendedores de agências de viagem, excursões e receptivos no Brasil. Assistem no feed (Instagram/Facebook, muitas vezes sem som no começo) ou na página de vendas. Português do Brasil.
- **Objetivo:** querer testar o Roteiro Online (assinar ou agendar demonstração).
- **Emoção:** do cansaço ("mais uma arte para refazer") para o alívio ("eu escrevo uma frase e a página sai pronta; mudar é clicar e digitar").

**A coisa verdadeira:** o Assistente IA transforma a mensagem que a agência já escreveria no WhatsApp numa página completa (banner, roteiro dia a dia, inclusos, preços, dúvidas), e qualquer mudança é feita clicando e digitando, com a prévia mudando na hora.

## Inventário da marca
| Olhar | Resposta |
|---|---|
| Forma do logo | Pin de mapa verde com uma **seta de navegação** dentro. A seta já é um ponteiro. |
| Controle principal | O campo do Assistente IA ("Digite ou grave um áudio...") e o botão de enviar; no editor, clicar numa seção e digitar. |
| Material | Fotos de destino; a página de roteiro (banner imersivo, dia a dia, preços). |
| Verbo | "montar" ("A IA monta a página"), "contar" ("Conte a viagem do seu jeito"). |
| Momento de sucesso | O cliente abre o link no celular e chama: "Quero reservar 2 lugares" (o mesmo cartão da LP). |
| Voz | Direta, calorosa, conversada: "Conte a viagem do seu jeito", "Mais fácil que editar no Canva!", "Seu cliente não compra o que não consegue imaginar!". |
| Lógica de cor | Verde = marca, publicado, botão; roxo/violeta = Assistente IA agindo; fundo "night" verde-escuro (#07130e) nas seções escuras da LP. |
| Tipo | Sora (títulos), Inter (interface). |
| Nunca faria | Luxo de gravata, neon tecnológico, orbes de IA. |

## Ideias
1. **Primeira (descartada):** caixa de prompt, blocos voando para montar um site, "Mais fácil que o Canva", logo. É o filme da categoria (qualquer construtor de sites com IA).
2. **Escolhida, documentário de UI de uma tarefa real:** uma viagem (Gramado e Canela) do zero ao cliente pedindo reserva, na tela real do produto, filmada por uma câmera: frase digitada no assistente real, a página em branco vira a página completa, o preço muda digitando, o visual muda com um clique, a página abre no celular e o cliente chama. Só esta marca tem esse fluxo (seções de roteiro, dia a dia, preço por pessoa, botão de WhatsApp).
3. **Outra (descartada):** ensaio tipográfico "Do textão para uma página que vende", com o textão desmontando em seções. Forte na voz da marca, mas o pedido é mostrar a facilidade na prática e a edição.

Porquê: a prova é o produto funcionando de verdade (capturas reais do editor em 3x, com a IA de demonstração do repositório), uma tarefa com começo e fim, e o ponteiro do filme é a seta do próprio logo.

## Sistema do filme
| Campo | Decisão |
|---|---|
| Forma | Documentário de UI de uma tarefa (rejeitados: cadeia de transformação; ensaio tipográfico) |
| Duração | ~29 s, 30 fps, 1920x1080 |
| Relógio | suave 30 fps; digitação e estados da IA em passos |
| Gramática de blur | shutter blur no render final (sem smear por elemento) |
| Tipo | Sora 600 nas frases do filme; Inter na interface (capturada) |
| Acento | verde da marca = "pronto / da marca" (frase final, pin); o roxo fica só onde a interface real já usa (Assistente IA) |
| Cursor | a seta de navegação do logo, verde com contorno escuro; entra grande, estaciona, aperta |
| Objeto carregado | o cursor-seta (S1→S3), o preço (S2→S3), a página Gramado (S2→S4) |
| Momento herói | S2: a página em branco vira a página de Gramado com a Catedral de Pedra, puxando a câmera para trás |
| Overshoot | nenhum, só o pouso do logo no fim |

## Mundo por ato
| Ato | Chão | Luz | Profundidade | Textura | Som |
|---|---|---|---|---|---|
| 1 (S1-S3, montar e editar) | a tela real do editor, ampliada e cortada pela borda | chave suave do alto à esquerda, falloff para baixo à direita | o que não é herói fica desfocado (4 a 10 px) | grão leve no render | violão dedilhado, teclado, cliques secos |
| 2 (S4-S5, o cliente) | verde-noite da marca + a foto do destino da página como placa desfocada (muda a cada viagem) | a tela do celular é a fonte de luz | celular nítido, placa a 60 px de blur | grão | a trilha abre; um "pop" na notificação; nota final no logo |

## Locução (ElevenLabs, voz configurada no ambiente, eleven_multilingual_v2)
1. Conte a viagem do seu jeito.
2. O Roteiro Online monta a página inteira pra você.
3. Mudou o preço? Clica e digita.
4. Quer outro visual? Um clique.
5. Sem refazer nenhuma arte. *(na tela: "Mais fácil que editar no Canva!", frase oficial da LP)*
6. Serve pra qualquer viagem, e abre lindo no celular.
7. Seu cliente não compra o que não consegue imaginar. *(H1 oficial da LP)*

## Cenas
| # | Papel | Imp. | Compra: o espectador... | Imagem sem texto | Na tela | Locução | Tempo |
|---|---|---|---|---|---|---|---|
| S1 | hook | 2 | vê que basta escrever uma frase comum | campo real do Assistente IA em macro, frase sendo digitada, a seta-cursor chega e aperta enviar | o prompt real (UI) | 1 | 0-3,4 s |
| S2 | prova (herói) | 3 | acredita que a página inteira sai pronta da frase | a IA trabalhando ("Montando as seções"), clique em "Inserir no fim", a página em branco vira Gramado com a Catedral de Pedra; a câmera desce pela página até o preço | UI real | 2 | 3,4-10,6 s |
| S3 | prova | 2 | vê que mudar é clicar e digitar, sem refazer arte | preço 1.290 vira 1.190 digitando; o banner troca de layout com um clique; a frase da LP sobre o editor desfocado | "Mais fácil que editar no Canva!" | 3, 4, 5 | 10,6-17,2 s |
| S4 | prova | 2 | acredita que serve para qualquer viagem e fica bonito no celular | "Celular"; o celular sai do editor para o mundo noturno; páginas reais (Foz, Itália, Abrolhos) passam na tela, com a foto de cada uma como luz de fundo | páginas reais | 6 | 17,2-23,6 s |
| S5 | cta | 2 | fica com a frase da marca e o nome | a notificação "Quero reservar 2 lugares" chega; a seta volta para dentro do pin e o logo pousa | logo | 7 | 23,6-29 s |

Checagens: cta = ~5,4 s de 29 (19 %); só S2 com importância 3 (20 %); cada prova tem um objeto legível por vez (o campo, o card de preço, o banner, o celular); nenhum rótulo, contador ou barra.
