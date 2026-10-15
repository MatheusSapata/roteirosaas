"""prep_assets.py CAPTURE_DIR FILM_DIR : convert real captures into film assets (webp), cut the logo arrow, make plates."""
import json, os, sys, shutil
import numpy as np
from PIL import Image, ImageFilter

CAP, FILM = sys.argv[1], sys.argv[2]
A = os.path.join(FILM, 'assets'); os.makedirs(A, exist_ok=True)
for d in ('ed', 'type', 'stream', 'phone', 'plate', 'logo'): os.makedirs(os.path.join(A, d), exist_ok=True)
M = os.path.join(CAP, 'main')

def webp(src, dst, scale=None, q=92, crop=None):
    im = Image.open(src).convert('RGB')
    if crop: im = im.crop(crop)
    if scale and scale != 1: im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    im.save(dst, 'WEBP', quality=q, method=6)
    return im.size

# full editor states: captured at 3x (4320x2700) -> 2x (2880x1800)
FULL = ['a01b-blank-ai-tall', 'a03-structure', 'a04-structure-hover', 'a05-applied-t0', 'a06-applied', 'a07-saved',
        'b00-price-panel', 'b01-ofertas', 'b02-price-selected', 'b03-price-1', 'b03-price-11', 'b03-price-119', 'b03-price-1190',
        'b04-price-saved', 'c00-banner-aparencia', 'c01-hover-Cartão', 'c02-layout-Cartão', 'c03-cartao-saved', 'd00-celular-hover', 'd01-celular']
for n in FULL:
    s = webp(os.path.join(M, n + '.png'), os.path.join(A, 'ed', n.replace('ã', 'a') + '.webp'), scale=2 / 3, q=90)
print('ed', len(FULL), s)
# typing crops (3x, clip 1004..1432 x 600..900 css) keep 3x for the macro
for f in sorted(os.listdir(os.path.join(M, 'type2'))):
    webp(os.path.join(M, 'type2', f), os.path.join(A, 'type', f.replace('.png', '.webp')), q=92)
# stream crops (3x sidebar column 1004..1432 x 0..900) -> 2x
for f in sorted(os.listdir(os.path.join(M, 'stream'))):
    webp(os.path.join(M, 'stream', f), os.path.join(A, 'stream', f.replace('.png', '.webp')), scale=2 / 3, q=90)
# tall preview (3x) -> 2x
print('tall', webp(os.path.join(M, 'preview-tall.png'), os.path.join(A, 'ed', 'preview-tall.webp'), scale=2 / 3, q=90))
# phone pages (3x, 390 css wide) -> 2x, first two screens
R = os.path.join(CAP, 'real')
for n in ['gramado-cartao', 'gramado-imersivo', 'foz', 'italia', 'abrolhos']:
    im = Image.open(os.path.join(R, n + '-long.png')).convert('RGB')
    im = im.crop((0, 0, im.width, min(im.height, 844 * 3 * 2)))
    im = im.resize((780, round(im.height * 780 / im.width)), Image.LANCZOS)
    im.save(os.path.join(A, 'phone', n + '.webp'), 'WEBP', quality=92, method=6)
    # ambient plate from the top screen: heavy blur, small
    top = Image.open(os.path.join(R, n + '-top.png')).convert('RGB').resize((195, 422), Image.LANCZOS)
    top = top.filter(ImageFilter.GaussianBlur(14))
    top.save(os.path.join(A, 'plate', n + '.webp'), 'WEBP', quality=88)
print('phone + plates ok')

# logo: cut the navigation arrow out of the official files (no redraw)
LOGO = '/home/user/roteirosaas/frontend/src/assets'
cor = np.array(Image.open(os.path.join(LOGO, 'Logo Cor - Roteiro Online.png')).convert('RGBA')).astype(np.int32)
bra = np.array(Image.open(os.path.join(LOGO, 'Logo Branco - Roteiro Online.png')).convert('RGBA')).astype(np.int32)
# inner disk of the pin (transparent hole of the ring) and the arrow inside it
from scipy.ndimage import binary_fill_holes, label
H, W = cor.shape[:2]
yy, xx = np.mgrid[0:H, 0:W]
opaque = (cor[..., 3] > 40) & (xx < 520)
lab, n = label(opaque)
sizes = np.bincount(lab.ravel()); sizes[0] = 0
ring = lab == sizes.argmax()                      # the pin body (largest blob)
filled = binary_fill_holes(ring)
hole = filled & ~ring                             # disk interior incl. the arrow
cy, cx = yy[hole].mean(), xx[hole].mean()
r_disk = np.sqrt(hole.sum() / np.pi)
inner = (xx - cx) ** 2 + (yy - cy) ** 2 < (r_disk * 0.97) ** 2
arrow_c = inner & opaque
ys, xs = np.where(arrow_c)
x0, x1, y0, y1 = xs.min() - 6, xs.max() + 7, ys.min() - 6, ys.max() + 7
print('disk', round(cx, 1), round(cy, 1), round(r_disk, 1), 'arrow bbox', x0, y0, x1, y1)
# green arrow (cursor) with alpha from the colour logo
ac = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
sub = cor[y0:y1, x0:x1].copy(); m = inner[y0:y1, x0:x1]
alpha = np.where(m, sub[..., 3], 0)
ac[..., :3] = sub[..., :3]; ac[..., 3] = alpha
Image.fromarray(ac).save(os.path.join(A, 'logo', 'arrow-green.png'))
# white logo split: arrow (inside the disk) and the rest. The white file is 1921 px wide and sits 1 px right:
# find its own disk the same way, then crop to 1920 aligned with the colour file.
Hb, Wb = bra.shape[:2]
yb, xb = np.mgrid[0:Hb, 0:Wb]
opb = (bra[..., 3] > 40) & (xb < 520)
lb, _ = label(opb); sb = np.bincount(lb.ravel()); sb[0] = 0
ringb = lb == sb.argmax(); holeb = binary_fill_holes(ringb) & ~ringb
cyb, cxb = yb[holeb].mean(), xb[holeb].mean(); rb = np.sqrt(holeb.sum() / np.pi)
innerb = (xb - cxb) ** 2 + (yb - cyb) ** 2 < (rb * 0.97) ** 2
dx = int(round(cxb - cx)); dy = int(round(cyb - cy))
print('white disk', round(cxb, 1), round(cyb, 1), round(rb, 1), 'offset', dx, dy)
bra = bra[dy:dy + H, dx:dx + W]; innerb = innerb[dy:dy + H, dx:dx + W]
wa = bra.copy(); wa[~innerb] = [255, 255, 255, 0]
Image.fromarray(wa[y0:y1, x0:x1].astype(np.uint8)).save(os.path.join(A, 'logo', 'arrow-white.png'))
rest = bra.copy(); rest[innerb] = [255, 255, 255, 0]
Image.fromarray(rest.astype(np.uint8)).crop((0, 230, 1920, 850)).save(os.path.join(A, 'logo', 'logo-white-noarrow.png'))
Image.fromarray(bra.astype(np.uint8)).crop((0, 230, 1920, 850)).save(os.path.join(A, 'logo', 'logo-white.png'))
json.dump({'arrow_box_in_logo': [int(x0), int(y0 - 230), int(x1), int(y1 - 230)], 'logo_size': [1920, 620],
           'disk_center': [float(cx), float(cy - 230)], 'disk_r': float(r_disk)}, open(os.path.join(A, 'logo', 'logo.json'), 'w'), indent=1)
# photos (for the end plate)
shutil.copy(os.path.join(CAP, '..', 'photos', 'full', 'catedral.jpg'), os.path.join(A, 'plate', 'catedral.jpg'))
print('done')
