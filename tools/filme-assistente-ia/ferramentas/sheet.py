"""sheet.py OUT.jpg cols cellW cellH img1 img2 ... : numbered contact sheet."""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
out, cols, cw, ch = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
files = sys.argv[5:]
rows = (len(files) + cols - 1) // cols
S = Image.new('RGB', (cols * cw, rows * ch), (20, 20, 20))
d = ImageDraw.Draw(S)
try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
except Exception: font = ImageFont.load_default()
for i, f in enumerate(files):
    try: im = ImageOps.fit(Image.open(f).convert('RGB'), (cw, ch))
    except Exception: continue
    x, y = (i % cols) * cw, (i // cols) * ch
    S.paste(im, (x, y)); d.rectangle([x, y, x + 44, y + 28], fill=(0, 0, 0)); d.text((x + 6, y + 2), str(i + 1), fill=(255, 255, 255), font=font)
S.save(out, quality=88)
