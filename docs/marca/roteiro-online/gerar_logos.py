import re, math, sys, os
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
s = open(src).read()
ds = re.findall(r'<path[^>]*?d="([^"]+)"', s)
ONLINE = ds[0:6]; ROTEIRO = ds[6:13]
XH = 346.23
ONLINE[2] = f"M866.0977 423.2109 L857.9453 423.2109 L857.9453 {XH} L866.0977 {XH} Z"
_dr = 6.5488; _dcy = XH + _dr; _st = _dcy + _dr + 5.2
ONLINE[3] = (f"M886.4102 {_st:.3f} L894.5625 {_st:.3f} L894.5625 423.2109 L886.4102 423.2109 Z "
             f"M{890.5547-_dr:.4f} {_dcy:.4f} a{_dr} {_dr} 0 1 0 {2*_dr:.4f} 0 a{_dr} {_dr} 0 1 0 {-2*_dr:.4f} 0Z")
# wordmark box in source coords
WX0, WX1, WY0, WY1 = 233, 1071, 312, 426
BASE = 423.5  # baseline

# ---- SIMBOLO: pin atual do Roteiro Online (Favicon.png) + aviao do favicon do Viaje On ----
# Pin redesenhado em vetor a partir do Favicon.png (1080 px): topo = circulo R=436
# concentrico ao furo; laterais = curvas ate a ponta (erro medio < 1 px do original).
CX, CY, R = 540.5, 464.0, 436.0
HR = 308.0                                     # furo
TIP = (540.5, 1051.5)
_P = [(976.43, 471.61), (971.89, 731.57), (774.18, 937.53), (540.5, 1051.5)]  # lado direito
def pin_d():
    (x0,y0),(x1,y1),(x2,y2),(x3,y3) = _P
    m = lambda x: 2*CX - x
    return (f"M{x0:.2f} {y0:.2f} C{x1:.2f} {y1:.2f} {x2:.2f} {y2:.2f} {x3:.2f} {y3:.2f} "
            f"C{m(x2):.2f} {y2:.2f} {m(x1):.2f} {y1:.2f} {m(x0):.2f} {y0:.2f} "
            f"A{R} {R} 0 1 1 {x0:.2f} {y0:.2f}Z "
            f"M{CX-HR} {CY} a{HR} {HR} 0 1 0 {2*HR} 0 a{HR} {HR} 0 1 0 {-2*HR} 0Z")

# Aviao do favicon do Viaje On (512 px), redesenhado como poligono de 6 lados.
def _line(p, q): return (p, (q[0]-p[0], q[1]-p[1]))
def _inter(l1, l2):
    (p, d), (q, e) = l1, l2
    den = d[0]*e[1] - d[1]*e[0]
    t = ((q[0]-p[0])*e[1] - (q[1]-p[1])*e[0]) / den
    return (p[0] + t*d[0], p[1] + t*d[1])
_E = [_line((96,207),(411,93)), _line((69,233),(179,285)), _line((195,288),(327,182)),
      _line((327,182),(223,318)), _line((223,318),(280,440)), _line((301,438),(416,104))]
PLANE_RR = 7.0                                  # raio dos cantos (unid. do favicon)
def _offset(l, r):
    (p, d) = l; n = math.hypot(*d); nx, ny = d[1]/n, -d[0]/n   # normal para dentro (sentido anti-horario na tela)
    return ((p[0]+nx*r, p[1]+ny*r), d)
def _poly(r):
    E = [_offset(l, r) for l in _E]
    return [_inter(E[i-1], E[i]) for i in range(len(E))]
PLANE_PTS = _poly(PLANE_RR)
if abs(sum((PLANE_PTS[i-1][0]*PLANE_PTS[i][1]-PLANE_PTS[i][0]*PLANE_PTS[i-1][1]) for i in range(6))) < abs(sum((a[0]*b[1]-b[0]*a[1]) for a,b in zip(_poly(0),_poly(0)[1:]+_poly(0)[:1]))):
    pass
else:
    PLANE_RR = -PLANE_RR; PLANE_PTS = _poly(PLANE_RR)
# pontas: [0]=bico (dir. alto), [1]=asa esquerda, [5]=ponta de baixo
def _circ(a, b, c):
    ax, ay = a; bx, by = b; cx, cy = c
    d = 2*(ax*(by-cy) + bx*(cy-ay) + cx*(ay-by))
    ux = ((ax*ax+ay*ay)*(by-cy) + (bx*bx+by*by)*(cy-ay) + (cx*cx+cy*cy)*(ay-by)) / d
    uy = ((ax*ax+ay*ay)*(cx-bx) + (bx*bx+by*by)*(ax-cx) + (cx*cx+cy*cy)*(bx-ax)) / d
    return ux, uy, math.hypot(ax-ux, ay-uy)
PLANE_FRAC = 0.74   # distancia centro->pontas = 74% do raio do furo (as 3 pontas a mesma distancia do pin)

def symbol(uid, pin_color, plane_color=None):
    plane_color = plane_color or pin_color
    pts = PLANE_PTS; rr = abs(PLANE_RR)
    ux, uy, cr = _circ(pts[0], pts[1], pts[5])
    k = HR * PLANE_FRAC / (cr + rr)
    poly = " ".join(f"{(x-ux)*k + CX:.2f},{(y-uy)*k + CY:.2f}" for x, y in pts)
    return (f'<g transform="translate({-CX})">'
            f'<path fill-rule="evenodd" fill="{pin_color}" d="{pin_d()}"/>'
            f'<polygon points="{poly}" fill="{plane_color}" stroke="{plane_color}" '
            f'stroke-width="{2*rr*k:.2f}" stroke-linejoin="round"/></g>')
SYM_W = 2 * R
SYM_TOP, SYM_BOT = CY - R, TIP[1]
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

# Medidas do texto (coordenadas do .ai)
AT = 319.2      # topo das letras altas (pingo do i de "roteiro")
XT = 345.0      # topo das letras baixas (altura x)
BL = 423.5      # linha de base
XH_ = BL - XT

def horizontal(name, p, bg=None):
    """Regra: topo do pin = topo das letras altas; centro do circulo = meio da altura x."""
    pin, pl, c1, c2, _ = p
    cy_txt = (XT + BL) / 2
    sc = (cy_txt - AT) / R                  # raio externo do pin = distancia ate o topo
    sw = SYM_W * sc
    sy = cy_txt - CY * sc                   # y de origem do simbolo (CY do pin cai em cy_txt)
    top = AT
    bot = sy + SYM_BOT * sc
    gap = XH_ * 0.55
    m = XH_ * 0.45
    W = sw + gap + (WX1 - WX0) + 2 * m
    Hh = bot - top + 2 * m
    body = (f'<g transform="translate({m + sw/2:.2f} {m + sy - top:.2f}) scale({sc:.5f})">{symbol(name+"h", pin, pl)}</g>'
            f'<g transform="translate({m + sw + gap - WX0:.2f} {m - top:.2f})">{wordmark(c1, c2)}</g>')
    return svg(W, Hh, body, bg)

def vertical(name, p, bg=None):
    """Pin centrado; largura do pin = 50% da linha mais larga; linhas proximas."""
    pin, pl, c1, c2, _ = p
    RX0, RX1 = 233.0, 675.3    # roteiro
    OX0, OX1 = 680.4, 1071.0   # online
    lw = max(RX1 - RX0, OX1 - OX0)
    sc = (lw * 0.50) / SYM_W
    sh = SYM_H * sc
    gap = XH_ * 0.50                       # ponta do pin -> topo das letras altas
    line_gap = XH_ * 0.22                  # base do "roteiro" -> topo do "online"
    lead = BL + line_gap - XT
    m = XH_ * 0.55
    W = lw + 2 * m
    y_pin = m
    y_txt = y_pin + sh + gap - AT          # deslocamento aplicado ao "roteiro"
    Hh = y_txt + lead + 426.0 + m
    a = "".join(f'<path d="{d}"/>' for d in ROTEIRO)
    b = "".join(f'<path d="{d}"/>' for d in ONLINE)
    body = (f'<g transform="translate({W/2:.2f} {y_pin - SYM_TOP*sc:.2f}) scale({sc:.5f})">{symbol(name+"v", pin, pl)}</g>'
            f'<g fill="{c1}" transform="translate({W/2 - (RX0+RX1)/2:.2f} {y_txt:.2f})">{a}</g>'
            f'<g fill="{c2}" transform="translate({W/2 - (OX0+OX1)/2:.2f} {y_txt + lead:.2f})">{b}</g>')
    return svg(W, Hh, body, bg)

def icone(name, p, bg=None):
    pin, pl, *_ = p
    m = SYM_H * 0.08
    W = SYM_W + 2*m; Hh = SYM_H + 2*m
    side = max(W, Hh)
    body = f'<g transform="translate({side/2:.2f} {(side-SYM_H)/2 - SYM_TOP:.2f})">{symbol(name+"i", pin, pl)}</g>'
    return svg(side, side, body, bg)

for name, p in PAL.items():
    for kind, fn in (("horizontal", horizontal), ("vertical", vertical), ("icone", icone)):
        open(f"{out}/roteiro-online-{kind}-{name}.svg", "w").write(fn(name, p))
        open(f"{out}/_preview-{kind}-{name}.svg", "w").write(fn(name+"pv", p, p[4]))
print("ok")
