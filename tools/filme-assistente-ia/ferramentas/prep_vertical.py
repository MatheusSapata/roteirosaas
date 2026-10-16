"""prep_vertical.py FILM_DIR : crops for the vertical film's split screen (S3) and its blurred backdrops.
A = the edit panel (css box 150,150 -> 600,720), B = the page preview (css box 590,150 -> 1150,540), both from the 2x editor states."""
import os, sys
from PIL import Image, ImageFilter

FILM = sys.argv[1]
ED, V = os.path.join(FILM, 'assets', 'ed'), os.path.join(FILM, 'assets', 'v')
os.makedirs(V, exist_ok=True)
S = ['b01-ofertas', 'b02-price-selected', 'b03-price-1', 'b03-price-11', 'b03-price-119', 'b03-price-1190',
     'c00-banner-aparencia', 'c01-hover-Cartao', 'c02-layout-Cartao']
A, B = (150, 150, 600, 720), (590, 150, 1150, 540)
for n in S:
    im = Image.open(os.path.join(ED, n + '.webp')).convert('RGB')
    im.crop(tuple(v * 2 for v in A)).save(os.path.join(V, 'A-' + n + '.webp'), 'WEBP', quality=90, method=6)
    im.crop(tuple(v * 2 for v in B)).save(os.path.join(V, 'B-' + n + '.webp'), 'WEBP', quality=90, method=6)
for src, dst in [('b01-ofertas', 'split-bg'), ('c02-layout-Cartao', 'split-bg-c')]:
    bg = Image.open(os.path.join(ED, src + '.webp')).convert('RGB').resize((720, 450), Image.LANCZOS).filter(ImageFilter.GaussianBlur(10))
    bg.save(os.path.join(V, dst + '.webp'), 'WEBP', quality=85)
print('ok', len(os.listdir(V)), 'files in', V)
