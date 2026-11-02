import re, math, sys, os
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
s = open(src).read()
ds = re.findall(r'<path[^>]*?d="([^"]+)"', s)
ONLINE = ds[0:6]; ROTEIRO = ds[6:13]
# wordmark box in source coords
WX0, WX1, WY0, WY1 = 233, 1071, 312, 426
BASE = 423.5  # baseline

# ---- AVIAO (troque aqui pelo aviao oficial do Viaje On) ----
# desenhado numa caixa 100x100, bico para cima
PLANE = ("M50 4 C55.5 4 58 9.5 58 15 L58 37 L93 57.5 C95 58.7 96 60.6 96 62.8 L96 68.5 "
         "L58 58.5 L58 79 L68 86.5 L68 93 L50 88.5 L32 93 L32 86.5 L42 79 L42 58.5 "
         "L4 68.5 L4 62.8 C4 60.6 5 58.7 7 57.5 L42 37 L42 15 C42 9.5 44.5 4 50 4 Z")

def pin_path(R=50.0, H=112.0):
    # circulo de raio R centrado em (0,0), ponta em (0,H) levemente arredondada
    a = math.asin(R / H)
    tx, ty = R * math.cos(a), R * math.sin(a)
    # pontos de tangencia
    r = 7.0  # arredondamento da ponta
    # ponto ao longo da tangente a r da ponta
    L = math.hypot(tx, H - ty)
    ux, uy = tx / L, (ty - H) / L
    px, py = ux * r * 2.2, H + uy * r * 2.2
    return (f"M{-tx:.2f} {ty:.2f} A{R} {R} 0 1 1 {tx:.2f} {ty:.2f} "
            f"L{px:.2f} {py:.2f} Q0 {H:.2f} {-px:.2f} {py:.2f} Z")

def symbol(uid, pin_color, plane_color=None):
    """Pin com aviao. plane_color None = aviao vazado (transparente)."""
    R, H = 50.0, 112.0
    k = 0.80  # aviao ocupa ~66% do diametro
    sz = 2 * R * k
    plane = (f'<g transform="translate(0 0) rotate(45) translate({-sz/2:.2f} {-sz/2:.2f}) scale({sz/100:.4f})">'
             f'<path d="{PLANE}"/></g>')
    if plane_color is None:
        return (f'<defs><mask id="m{uid}" maskUnits="userSpaceOnUse" x="-60" y="-60" width="120" height="200">'
                f'<rect x="-60" y="-60" width="120" height="200" fill="#fff"/>'
                f'<g fill="#000">{plane}</g></mask></defs>'
                f'<path d="{pin_path(R,H)}" fill="{pin_color}" mask="url(#m{uid})"/>')
    return (f'<path d="{pin_path(R,H)}" fill="{pin_color}"/><g fill="{plane_color}">{plane}</g>')
SYM_W, SYM_TOP, SYM_BOT = 100.0, -50.0, 112.0
SYM_H = SYM_BOT - SYM_TOP

def wordmark(c1, c2):
    a = "".join(f'<path d="{d}"/>' for d in ROTEIRO)
    b = "".join(f'<path d="{d}"/>' for d in ONLINE)
    return f'<g fill="{c1}">{a}</g><g fill="{c2}">{b}</g>'

PAL = {
    # nome: (pin, aviao(None=vazado), roteiro, online, fundo de preview)
    "principal":        ("#02BA80", None, "#02BA80", "#1FEBA0", "#FFFFFF"),
    "fundo-escuro":     ("#1FEBA0", None, "#FFFFFF", "#1FEBA0", "#111111"),
    "fundo-verde":      ("#FFFFFF", None, "#FFFFFF", "#FFFFFF", "#02BA80"),
    "verde-cinza":      ("#02BA80", None, "#5E5E5E", "#02BA80", "#FFFFFF"),
    "preto":            ("#111111", None, "#111111", "#111111", "#FFFFFF"),
    "branco":           ("#FFFFFF", None, "#FFFFFF", "#FFFFFF", "#111111"),
}

PAD = 0.0
def svg(w, h, body, bg=None):
    bgr = f'<rect width="100%" height="100%" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
            f'width="{w:.0f}" height="{h:.0f}"><title>Roteiro Online</title>{bgr}{body}</svg>\n')

def horizontal(name, p, bg=None):
    pin, pl, c1, c2, _ = p
    wh = WY1 - WY0
    sh = wh * 1.5                # altura do simbolo
    sc = sh / SYM_H
    gap = wh * 0.42
    sw = SYM_W * sc
    # simbolo: base da ponta alinhada um pouco abaixo da linha de base
    sy = (WY1 + wh * 0.18) - SYM_BOT * sc
    top = min(sy + SYM_TOP * sc, WY0)
    bot = max(WY1, sy + SYM_BOT * sc)
    m = wh * 0.25
    W = sw + gap + (WX1 - WX0) + 2 * m
    Hh = bot - top + 2 * m
    body = (f'<g transform="translate({m + sw/2:.2f} {m + (sy - top):.2f}) scale({sc:.4f})">{symbol(name+"h", pin, pl)}</g>'
            f'<g transform="translate({m + sw + gap - WX0:.2f} {m - top:.2f})">{wordmark(c1, c2)}</g>')
    return svg(W, Hh, body, bg)

def vertical(name, p, bg=None):
    pin, pl, c1, c2, _ = p
    RX0, RX1 = 233, 594   # roteiro
    OX0, OX1 = 594, 1071  # online
    wh = WY1 - WY0
    lw = max(RX1-RX0, OX1-OX0)
    sh = wh * 2.7
    sc = sh / SYM_H
    gap = wh * 0.40
    lead = wh * 1.12      # distancia entre as linhas
    m = wh * 0.35
    W = lw + 2*m
    Hh = sh + gap + wh + lead + 2*m
    ty = m + sh + gap - WY0
    a = "".join(f'<path d="{d}"/>' for d in ROTEIRO)
    b = "".join(f'<path d="{d}"/>' for d in ONLINE)
    body = (f'<g transform="translate({W/2:.2f} {m - SYM_TOP*sc:.2f}) scale({sc:.4f})">{symbol(name+"v", pin, pl)}</g>'
            f'<g fill="{c1}" transform="translate({W/2 - (RX0+RX1)/2:.2f} {ty:.2f})">{a}</g>'
            f'<g fill="{c2}" transform="translate({W/2 - (OX0+OX1)/2:.2f} {ty + lead:.2f})">{b}</g>')
    return svg(W, Hh, body, bg)

def icone(name, p, bg=None):
    pin, pl, *_ = p
    m = 14
    W = SYM_W + 2*m; Hh = SYM_H + 2*m
    side = max(W, Hh)
    body = f'<g transform="translate({side/2:.2f} {(side-SYM_H)/2 - SYM_TOP:.2f})">{symbol(name+"i", pin, pl)}</g>'
    return svg(side, side, body, bg)

for name, p in PAL.items():
    for kind, fn in (("horizontal", horizontal), ("vertical", vertical), ("icone", icone)):
        open(f"{out}/roteiro-online-{kind}-{name}.svg", "w").write(fn(name, p))
        open(f"{out}/_preview-{kind}-{name}.svg", "w").write(fn(name+"pv", p, p[4]))
print("ok")
