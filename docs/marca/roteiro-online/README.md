# Marca Roteiro Online

Logo no estilo do Viaje On: "roteiro" em bold, "online" em traço fino e um pin de localização com um avião vazado.
O texto saiu dos vetores do arquivo `ROTEIROONLINE_BASE.ai`.

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

O avião é vazado (transparente), então aparece a cor do fundo.
SVG para uso geral e impressão; PNG transparente (3000 px no lado maior; ícone em 1024 px).

## Trocar o avião
O avião fica na constante `PLANE` de `gerar_logos.py` (caixa 100x100, bico para cima).
Para usar o avião oficial do Viaje On, cole o path dele ali e rode:

    python3 gerar_logos.py <ROTEIROONLINE_BASE convertido em svg> svg
