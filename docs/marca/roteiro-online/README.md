# Marca Roteiro Online

- **Símbolo:** o pin atual do Roteiro Online (`frontend/src/assets/Favicon.png`), redesenhado em vetor. A seta foi trocada pelo avião do favicon do Viaje On.
- **Texto:** vem dos vetores de `ROTEIROONLINE_BASE.ai`. "roteiro" é bold e "online" é traço fino. O "l" e o "i" de "online" foram baixados e ficam só um pouco acima do "o", "n" e "e", para a palavra encaixar na versão vertical.

## Regras de montagem
- **Avião:** fica centralizado no círculo do pin, com as três pontas (bico, asa e cauda) na mesma distância do pin. Essa distância é 74% do raio do círculo.
- **Horizontal:** o pin tem 1,45 vez a altura do texto, e o centro dele fica alinhado ao centro do texto.
- **Horizontal empilhado:** "online" em 80% do tamanho, alinhado pela esquerda com "roteiro". O pin fica um pouco maior que o bloco de texto e centralizado na altura dele.
- **Vertical:** o pin fica centralizado e tem metade da largura de "roteiro". "online" fica embaixo, em 80% do tamanho e centralizado.

## Modelos
- `horizontal`: pin à esquerda e o texto numa linha
- `horizontal-empilhado`: pin à esquerda, com "roteiro" em cima e "online" embaixo, alinhados pela esquerda (formato do logo antigo)
- `vertical`: pin em cima, "roteiro" e "online" empilhados
- `icone`: só o pin (avatar, favicon, app)

## Variações de cor (paleta Viaje On de 2026-11)
Mesma paleta do painel (`frontend/src/styles/main.css`): Verde Viaje #0A6346, Verde On #90EE8F, Verde Trilha #15915C, Névoa #EFF3ED e Noite #0A110E.

| Arquivo | Uso | Pin | roteiro | online |
|---|---|---|---|---|
| `principal` | fundo claro (branco ou Névoa) | Verde Viaje #0A6346 | Verde Viaje #0A6346 | Verde Trilha #15915C |
| `fundo-escuro` | fundo Noite #0A110E | Verde On #90EE8F | branco | Verde On #90EE8F |
| `fundo-verde` | fundo Verde Viaje #0A6346 | Verde On #90EE8F | branco | Verde On #90EE8F |
| `verde-noite` | fundo claro, mais sóbrio | Verde Viaje #0A6346 | Noite #0A110E | Verde Trilha #15915C |
| `noite` | uma cor, fundo claro | Noite #0A110E | Noite #0A110E | Noite #0A110E |
| `branco` | uma cor, fundo escuro | branco | branco | branco |

O círculo do pin é vazado (transparente), então aparece a cor do fundo.
SVG para uso geral e impressão; PNG transparente (3000 px no lado maior; ícone em 1024 px).

## Gerar de novo

    python3 gerar_logos.py <ROTEIROONLINE_BASE convertido em svg> svg
