# Marca Roteiro Online

- **Símbolo:** o pin atual do Roteiro Online (`frontend/src/assets/Favicon.png`), redesenhado em vetor. A seta foi trocada pelo avião do favicon do Viaje On.
- **Texto:** vem dos vetores de `ROTEIROONLINE_BASE.ai`. "roteiro" é bold e "online" é traço fino. O "l" e o "i" de "online" foram baixados para a altura do "o", "n" e "e", então todas as letras ficam com a mesma altura.

## Regras de montagem
- **Avião:** fica centralizado no círculo do pin, com as três pontas (bico, asa e cauda) na mesma distância do pin. Essa distância é 74% do raio do círculo.
- **Horizontal:** o topo do pin alinha com o topo das letras altas de "roteiro", e o centro do círculo fica no meio da altura das letras baixas.
- **Vertical:** o pin fica centralizado e tem metade da largura do texto. "roteiro" e "online" ficam empilhados e próximos.

## Modelos
- `horizontal`: pin à esquerda e o texto numa linha
- `vertical`: pin em cima, "roteiro" e "online" empilhados
- `icone`: só o pin (avatar, favicon, app)

## Variações de cor
| Arquivo | Uso | Pin | roteiro | online |
|---|---|---|---|---|
| `principal` | fundo claro | #02BA80 | #02BA80 | #1FEBA0 |
| `fundo-escuro` | fundo escuro | #1FEBA0 | #FFFFFF | #1FEBA0 |
| `fundo-verde` | sobre o verde #02BA80 | branco | branco | branco |
| `verde-cinza` | fundo claro, mais sóbrio | #02BA80 | #5E5E5E | #02BA80 |
| `preto` | uma cor, fundo claro | #111111 | #111111 | #111111 |
| `branco` | uma cor, fundo escuro | branco | branco | branco |

O círculo do pin é vazado (transparente), então aparece a cor do fundo.
SVG para uso geral e impressão; PNG transparente (3000 px no lado maior; ícone em 1024 px).

## Gerar de novo

    python3 gerar_logos.py <ROTEIROONLINE_BASE convertido em svg> svg
