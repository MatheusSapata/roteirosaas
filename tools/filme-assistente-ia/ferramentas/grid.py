"""grid.py src.png out.jpg x0 y0 x1 y1 [dpr=3] [step=50] : crop in CSS px with a labelled grid."""
import sys
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]; x0, y0, x1, y1 = map(float, sys.argv[3:7])
D = float(sys.argv[7]) if len(sys.argv) > 7 else 3; step = int(sys.argv[8]) if len(sys.argv) > 8 else 50
im = Image.open(src).convert('RGB').crop((int(x0 * D), int(y0 * D), int(x1 * D), int(y1 * D)))
s = 900 / max(im.size); im = im.resize((int(im.width * s), int(im.height * s)))
d = ImageDraw.Draw(im); f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
k = D * s
for x in range(int(x0 // step * step + step), int(x1), step):
    X = (x - x0) * k; d.line([(X, 0), (X, im.height)], fill=(255, 0, 80), width=1); d.text((X + 2, 2), str(x), fill=(255, 0, 80), font=f)
for y in range(int(y0 // step * step + step), int(y1), step):
    Y = (y - y0) * k; d.line([(0, Y), (im.width, Y)], fill=(0, 120, 255), width=1); d.text((2, Y + 2), str(y), fill=(0, 120, 255), font=f)
im.save(out, quality=88)
