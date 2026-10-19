import math
import numpy as np
from PIL import Image, ImageDraw

def hx(c):
    c = c.lstrip('#'); return np.array([int(c[i:i+2], 16) for i in (0, 2, 4)], float)

OUT = hx('#05080B')
LINE = hx('#0A0E12')

def plaid(base, shade):
    b, s, d = hx(base), hx(shade), hx('#0B1410')
    def f(x, y):
        if x % 6 in (0,) or y % 6 in (0,):
            return d
        if (x // 3 + y // 3) % 2 == 0:
            return b
        return s
    return f

class Char:
    """Shapes painted into a region map, then auto-shaded and outlined."""
    def __init__(self, w, h, regions):
        self.w, self.h = w, h
        self.regions = regions  # name -> dict(base, shade, light, soft:set, pattern)
        self.names = list(regions.keys())

    def render(self, shapes, details=(), soft_pairs=()):
        w, h = self.w, self.h
        im = Image.new('L', (w, h), 0)
        d = ImageDraw.Draw(im)
        idx = {n: i + 1 for i, n in enumerate(self.names)}
        for kind, geo, name in shapes:
            v = idx[name]
            if kind == 'poly':
                d.polygon(geo, fill=v)
            elif kind == 'ell':
                d.ellipse(geo, fill=v)
            elif kind == 'rect':
                d.rectangle(geo, fill=v)
            elif kind == 'line':
                d.line(geo[0], fill=v, width=geo[1])
        L = np.array(im)
        self.L = L; self.idx = {n: i + 1 for i, n in enumerate(self.names)}
        rgb = np.zeros((h, w, 3)); alpha = np.zeros((h, w))
        inv = {v: n for n, v in idx.items()}
        soft = set()
        for a, b in soft_pairs:
            soft.add((idx[a], idx[b])); soft.add((idx[b], idx[a]))
        def same(x, y, v):
            return 0 <= x < w and 0 <= y < h and L[y, x] == v
        for y in range(h):
            for x in range(w):
                v = L[y, x]
                if not v:
                    continue
                r = self.regions[inv[v]]
                base = r['pattern'](x, y) if r.get('pattern') else hx(r['base'])
                col = base
                if 'shade' in r and not same(x + r.get('sd', 2), y, v):
                    col = hx(r['shade']) if not r.get('pattern') else base * 0.62
                if 'light' in r and not same(x - 1, y, v):
                    col = hx(r['light'])
                if r.get('top') and not same(x, y - 1, v):
                    col = hx(r['top'])
                if r.get('bottom') and not same(x, y + r.get('bd', 2), v):
                    col = hx(r['bottom']) if not r.get('pattern') else base * 0.7
                rgb[y, x] = col; alpha[y, x] = 1
        # internal lines + outline
        res = rgb.copy(); ra = alpha.copy()
        for y in range(h):
            for x in range(w):
                v = L[y, x]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < w and 0 <= ny < h):
                        continue
                    nv = L[ny, nx]
                    if v and not nv:
                        res[ny, nx] = OUT; ra[ny, nx] = 1
                    elif v and nv and nv != v and nv < v and (v, nv) not in soft:
                        res[ny, nx] = LINE
        self.rgb, self.a = res, ra
        for (x, y, c) in details:
            if 0 <= x < w and 0 <= y < h:
                self.rgb[y, x] = hx(c); self.a[y, x] = 1
        return self

    def paste(self, canvas, ox, oy):
        H, W = canvas.shape[:2]
        for y in range(self.h):
            for x in range(self.w):
                if self.a[y, x] > 0:
                    X, Y = ox + x, oy + y
                    if 0 <= X < W and 0 <= Y < H:
                        canvas[Y, X] = self.rgb[y, x]

SKIN = dict(base='#E9AE8C', shade='#C07F63', light='#F7CDB1')
SKIN_D = dict(base='#9C6446', shade='#73452F', light='#B97B58')

BLINK = False

def eye(det, x, y, iris='#2B1E3A', hl=True, tall=3):
    """Anime eye: dark lash on top, iris, white highlight."""
    if BLINK:
        for k in range(3):
            det.append((x + k, y + tall - 1, '#120C14'))
        return
    for k in range(3):
        det.append((x + k, y, '#120C14'))
    for yy in range(1, tall):
        det.append((x, y + yy, iris)); det.append((x + 1, y + yy, iris))
    if hl:
        det.append((x + 1, y + 1, '#FFFFFF'))

# ----------------------------------------------------------------- VEX
def vex(nod=0, hot=False):
    R = {
        'shoe': dict(base='#E9EEEC', shade='#9AA8A8', bottom='#5E6A6A'),
        'pants': dict(base='#2E4670', shade='#1D2E4D', light='#4467A0'),
        'jacket': dict(base='#191E27', shade='#0E1218', light='#3B8F94'),
        'sleeve': dict(base='#1D232D', shade='#0E1218', light='#3B8F94'),
        'rib': dict(base='#2B323C', shade='#1A1F26'),
        'tee': dict(base='#E2EAE7', shade='#A9BBB8'),
        'neck': dict(base='#C07F63'),
        'phones': dict(base='#33D4E0', shade='#1A8590'),
        'cup': dict(base='#151A1F', light='#33D4E0'),
        'hair': dict(base='#1A1C2A', shade='#0E0F18', light='#3A3F5C'),
        'face': SKIN,
        'cap': dict(base='#2A3343', shade='#1A202B', light='#55708A', top='#55708A'),
        'brim': dict(base='#151A22', top='#3A4656'),
    }
    c = Char(42, 80, R)
    y = nod
    S = [
        ('ell', (7, 72, 19, 79), 'shoe'), ('ell', (22, 72, 34, 79), 'shoe'),
        ('poly', [(11, 48), (31, 48), (34, 74), (22, 74), (21, 56), (20, 74), (8, 74)], 'pants'),
        ('poly', [(8, 28), (34, 28), (36, 50), (6, 50)], 'jacket'),
        ('poly', [(4, 30), (11, 28), (12, 49), (3, 48)], 'sleeve'),
        ('poly', [(31, 28), (38, 30), (39, 48), (30, 49)], 'sleeve'),
        ('rect', (6, 48, 36, 50), 'rib'),
        ('poly', [(17, 28), (25, 28), (24, 49), (18, 49)], 'tee'),
        ('rect', (18, 22 + y, 24, 29), 'neck'),
        ('poly', [(10, 10 + y), (30, 10 + y), (30, 18 + y), (27, 22 + y), (22, 25 + y), (19, 25 + y), (14, 22 + y), (11, 18 + y)], 'face'),
        ('poly', [(9, 8 + y), (32, 8 + y), (33, 18 + y), (30, 15 + y), (29, 11 + y), (12, 11 + y), (11, 16 + y), (9, 13 + y)], 'hair'),
        ('poly', [(10, 10 + y), (11, 5 + y), (15, 1 + y), (27, 1 + y), (31, 5 + y), (32, 10 + y)], 'cap'),
        ('poly', [(2, 10 + y), (19, 8 + y), (20, 11 + y), (3, 13 + y)], 'brim'),
        ('line', ([(14, 27), (21, 30), (28, 27)], 2), 'phones'),
        ('ell', (10, 24, 15, 30), 'cup'), ('ell', (27, 24, 32, 30), 'cup'),
    ]
    det = []
    # bangs falling under the brim
    for (x, yy) in ((12, 12), (13, 12), (13, 13), (16, 12), (17, 12), (17, 13), (21, 12), (25, 12), (26, 12), (26, 13), (27, 14)):
        det.append((x, yy + y, '#1A1C2A'))
    eye(det, 14, 15 + y, iris='#3A2A55'); eye(det, 21, 15 + y, iris='#3A2A55')
    det += [(13, 14 + y, '#2A1A14'), (14, 14 + y, '#2A1A14'), (21, 14 + y, '#2A1A14'), (22, 14 + y, '#2A1A14'), (23, 14 + y, '#2A1A14')]
    det += [(18, 21 + y, '#A4564A'), (19, 21 + y, '#A4564A')]
    det += [(13, 19 + y, '#F2A3A0'), (24, 19 + y, '#F2A3A0')]  # blush
    det += [(23, 4 + y, '#E0464F'), (24, 4 + y, '#E0464F'), (23, 5 + y, '#E0464F')]
    for k in range(7):  # chain
        det.append((17 + k, 31 + abs(3 - k) // 2, '#E8C35A' if k % 2 else '#B08A33'))
    for yy in range(30, 48, 3):
        det.append((15, yy, '#3A4250'))  # zipper teeth
    det += [(29, 36, '#E8C35A'), (30, 36, '#E8C35A')]  # pin
    c.render(S, det, soft_pairs=[('face', 'neck'), ('neck', 'tee'), ('cup', 'phones')])
    # cigarette
    mx, my = 17, 21 + y
    tip = (mx - 7, my)
    for x in range(mx - 6, mx):
        c.rgb[my, x] = hx('#F1EFE7'); c.a[my, x] = 1
    c.rgb[my, mx - 2] = hx('#D9A35F')
    c.rgb[my, mx - 7] = hx('#FFE2A8' if hot else '#FF7A2E'); c.a[my, mx - 7] = 1
    return c, tip

# ----------------------------------------------------------------- YUZU
YEL = dict(base='#FFD23A', shade='#D9A21A', light='#FFF08A')
def yuzu(t=0.0):
    """Back view, yellow tracksuit with black stripes, arm up spraying."""
    R = {
        'shoe': dict(base='#F0F2EE', shade='#9EA8A6', bottom='#5E6A6A'),
        'pants': YEL,
        'stripe': dict(base='#121212'),
        'jacket': YEL,
        'arm': YEL,
        'hand': SKIN,
        'neck': dict(base='#C07F63'),
        'cheek': SKIN,
        'hair': dict(base='#17151F', shade='#0C0B12', light='#4A3F6A', top='#4A3F6A'),
        'streak': dict(base='#FF4FB0', shade='#C23584'),
        'can': dict(base='#E9EEEC', shade='#9AA8A8', top='#FF3EA5'),
        'collar': dict(base='#121212'),
    }
    c = Char(46, 80, R)
    hx_, hy_ = 36 + round(math.cos(t) * 2), 9 + round(math.sin(t) * 2)  # spraying hand circles
    S = [
        ('ell', (9, 72, 20, 79), 'shoe'), ('ell', (23, 72, 34, 79), 'shoe'),
        ('poly', [(12, 46), (32, 46), (34, 74), (23, 74), (22, 56), (21, 74), (9, 74)], 'pants'),
        ('poly', [(9, 52), (10, 52), (10, 74), (9, 74)], 'stripe'),
        ('poly', [(33, 52), (34, 52), (34, 74), (33, 74)], 'stripe'),
        ('poly', [(10, 27), (33, 27), (34, 48), (9, 48)], 'jacket'),
        ('poly', [(9, 28), (10, 28), (10, 48), (9, 48)], 'stripe'),
        ('poly', [(33, 28), (34, 28), (34, 48), (33, 48)], 'stripe'),
        ('poly', [(5, 29), (11, 28), (11, 46), (6, 46)], 'arm'),
        ('ell', (5, 45, 10, 50), 'hand'),
        ('rect', (5, 47, 8, 55), 'can'),
        ('poly', [(29, 28), (34, 27), (hx_ + 2, hy_ + 4), (hx_ - 2, hy_ + 6)], 'arm'),
        ('ell', (hx_ - 2, hy_ + 1, hx_ + 2, hy_ + 5), 'hand'),
        ('rect', (hx_ - 1, hy_ - 5, hx_ + 1, hy_ + 1), 'can'),
        ('rect', (19, 21, 25, 28), 'neck'),
        ('rect', (16, 26, 28, 28), 'collar'),
        ('poly', [(27, 13), (31, 12), (31, 20), (28, 23)], 'cheek'),
        ('poly', [(11, 10), (13, 4), (18, 1), (26, 1), (31, 4), (33, 10), (32, 20), (29, 14), (28, 22), (14, 23), (11, 19)], 'hair'),
        ('poly', [(16, 3), (19, 2), (17, 14), (15, 14)], 'streak'),
    ]
    det = []
    # bob ends + hair clip
    for x in range(13, 29, 3):
        det.append((x, 23, '#17151F'))
    det += [(26, 6, '#FF4FB0'), (27, 6, '#FF4FB0'), (26, 7, '#FFC2E3')]
    # profile eye + lashes on visible cheek
    det += [(30, 15, '#120C14'), (31, 15, '#120C14'), (30, 16, '#3A2A55'), (30, 17, '#3A2A55'), (31, 19, '#F2A3A0')]
    # jacket back print: small black triangle logo
    for k in range(5):
        for j in range(5 - k):
            det.append((19 + k // 2 + j, 34 + k, '#121212'))
    # stripes on raised sleeve
    for k in range(9):
        fx = 31 + (hx_ - 31) * k / 9; fy = 28 + (hy_ + 5 - 28) * k / 9
        det.append((int(fx) + 2, int(fy), '#121212'))
    c.render(S, det, soft_pairs=[('neck', 'collar'), ('cheek', 'hair'), ('pants', 'stripe'), ('jacket', 'stripe'), ('hand', 'can'), ('arm', 'hand')])
    nozzle = (hx_, hy_ - 6)
    return c, nozzle

# ----------------------------------------------------------------- DEUCE
def deuce(nod=0):
    """90s West Coast: bandana, shades, open plaid flannel over white tank, khakis."""
    R = {
        'shoe': dict(base='#F2F4F1', shade='#A2ACAA', bottom='#5E6A6A'),
        'pants': dict(base='#C8AA74', shade='#9A7F50', light='#E2C994'),
        'tank': dict(base='#EEF2EF', shade='#B4C2BF'),
        'flannel': dict(pattern=plaid('#2F8A4E', '#1E5E36'), shade=True, sd=2, light='#58B07A'),
        'sleeve': dict(pattern=plaid('#2F8A4E', '#1E5E36'), shade=True, sd=3, bottom=True),
        'hand': SKIN_D,
        'neck': dict(base='#73452F'),
        'face': SKIN_D,
        'bandana': dict(base='#2E62D9', shade='#1E3F96', light='#6E97F0', top='#6E97F0'),
        'shades': dict(base='#0B0D10', top='#7FE7F0'),
    }
    c = Char(46, 80, R)
    y = nod
    S = [
        ('ell', (7, 72, 20, 79), 'shoe'), ('ell', (25, 72, 38, 79), 'shoe'),
        ('poly', [(10, 46), (36, 46), (39, 75), (25, 75), (23, 56), (22, 75), (6, 75)], 'pants'),
        ('poly', [(8, 26), (38, 26), (39, 50), (7, 50)], 'flannel'),
        ('poly', [(16, 26), (30, 26), (29, 48), (17, 48)], 'tank'),
        ('poly', [(3, 29), (10, 26), (11, 41), (4, 41)], 'sleeve'),
        ('poly', [(36, 26), (43, 29), (42, 41), (35, 41)], 'sleeve'),
        ('rect', (9, 35, 37, 41), 'sleeve'),
        ('ell', (5, 34, 11, 41), 'hand'), ('ell', (35, 34, 41, 41), 'hand'),
        ('rect', (19, 20 + y, 27, 27), 'neck'),
        ('ell', (10, 12 + y, 14, 18 + y), 'face'), ('ell', (32, 12 + y, 36, 18 + y), 'face'),
        ('poly', [(12, 9 + y), (34, 9 + y), (34, 17 + y), (31, 22 + y), (25, 25 + y), (21, 25 + y), (15, 22 + y), (12, 17 + y)], 'face'),
        ('poly', [(11, 11 + y), (12, 5 + y), (17, 1 + y), (29, 1 + y), (34, 5 + y), (35, 11 + y), (33, 10 + y), (13, 10 + y)], 'bandana'),
        ('poly', [(34, 7 + y), (39, 5 + y), (41, 9 + y), (38, 10 + y), (41, 14 + y), (36, 12 + y)], 'bandana'),
        ('rect', (14, 13 + y, 21, 15 + y), 'shades'), ('rect', (25, 13 + y, 32, 15 + y), 'shades'),
        ('rect', (21, 13 + y, 25, 13 + y), 'shades'),
    ]
    det = []
    for (x, yy) in ((16, 4), (21, 3), (26, 5), (30, 3), (19, 7), (28, 8), (39, 8)):
        det.append((x, yy + y, '#F4F1E8'))
    det += [(15, 13 + y, '#7FE7F0'), (16, 13 + y, '#FF7FC8'), (26, 13 + y, '#7FE7F0'), (27, 13 + y, '#FF7FC8')]
    det += [(17, 12 + y, '#3E2216'), (18, 12 + y, '#3E2216'), (19, 12 + y, '#3E2216'), (27, 12 + y, '#3E2216'), (28, 12 + y, '#3E2216'), (29, 12 + y, '#3E2216')]
    det += [(23, 18 + y, '#73452F'), (24, 18 + y, '#73452F')]  # nose
    det += [(21, 21 + y, '#5A2E22'), (22, 21 + y, '#5A2E22'), (23, 21 + y, '#5A2E22'), (24, 21 + y, '#5A2E22'), (25, 21 + y, '#5A2E22')]
    det += [(22, 23 + y, '#24130C'), (23, 23 + y, '#24130C'), (24, 23 + y, '#24130C'), (23, 24 + y, '#24130C')]  # goatee
    det += [(11, 15 + y, '#73452F'), (35, 15 + y, '#73452F'), (11, 17 + y, '#F0C95C'), (35, 17 + y, '#F0C95C')]  # ears + studs
    for k in range(11):
        det.append((18 + k, 28 + (abs(5 - k) < 3) * 2 + (abs(5 - k) < 1), '#F0C95C' if k % 2 else '#B48A30'))
    det += [(23, 32, '#F0C95C'), (23, 33, '#B48A30')]
    c.render(S, det, soft_pairs=[('face', 'neck'), ('neck', 'tank'), ('sleeve', 'hand'), ('flannel', 'sleeve')])
    return c

if __name__ == '__main__':
    canvas = np.zeros((84, 150, 3)); canvas[:] = hx('#0C2026')
    v, _ = vex(); v.paste(canvas, 2, 2)
    yz, _ = yuzu(0.0); yz.paste(canvas, 50, 2)
    d = deuce(); d.paste(canvas, 100, 2)
    Image.fromarray(canvas.astype(np.uint8)).resize((1200, 672), Image.NEAREST).save('chars_preview.png')

# ----------------------------------------------------------------- RUBY
def ruby(sway=0):
    """Red hair, cropped leather jacket, white crop top, cargo pants, platform boots. Hand on hip."""
    R = {
        'hairback': dict(base='#C72A2A', shade='#8E1717', light='#FF6A4D'),
        'boot': dict(base='#15171C', light='#3A3F4A', bottom='#E9EEEC', bd=3),
        'pants': dict(base='#3B3F4C', shade='#262934', light='#5A6072'),
        'belt': dict(base='#0E0F12'),
        'midriff': SKIN,
        'top': dict(base='#F1F3F0', shade='#B9C4C1'),
        'jacket': dict(base='#17181E', shade='#0C0D10', light='#3E8F96'),
        'arm': dict(base='#17181E', shade='#0C0D10', light='#3E8F96'),
        'hand': SKIN,
        'neck': dict(base='#C07F63'),
        'face': SKIN,
        'hair': dict(base='#E03A30', shade='#A0201C', light='#FF8466', top='#FF8466'),
    }
    c = Char(48, 82, R)
    s = sway
    S = [
        ('poly', [(12, 8), (36, 8), (41, 30), (41, 50 + s), (36, 47), (12, 47), (7, 50 + s), (7, 30)], 'hairback'),
        ('poly', [(13, 73), (21, 73), (21, 81), (12, 81)], 'boot'), ('poly', [(27, 73), (35, 73), (36, 81), (27, 81)], 'boot'),
        ('poly', [(14, 44), (34, 44), (36, 75), (27, 75), (24, 54), (21, 75), (12, 75)], 'pants'),
        ('rect', (14, 43, 34, 45), 'belt'),
        ('rect', (16, 39, 32, 43), 'midriff'),
        ('poly', [(16, 27), (32, 27), (32, 39), (16, 39)], 'top'),
        ('poly', [(12, 26), (19, 26), (18, 38), (13, 38)], 'jacket'),
        ('poly', [(29, 26), (36, 26), (35, 38), (30, 38)], 'jacket'),
        ('poly', [(9, 28), (13, 26), (14, 44), (9, 46)], 'arm'),
        ('ell', (8, 44, 13, 50), 'hand'),
        ('poly', [(34, 26), (39, 28), (44, 36), (36, 44), (33, 41), (38, 36), (34, 32)], 'arm'),
        ('ell', (32, 40, 37, 45), 'hand'),
        ('rect', (21, 21, 27, 28), 'neck'),
        ('poly', [(14, 9), (34, 9), (34, 17), (31, 22), (26, 25), (22, 25), (17, 22), (14, 17)], 'face'),
        ('poly', [(12, 11), (14, 4), (19, 1), (29, 1), (34, 4), (36, 11), (35, 20), (33, 13), (30, 10), (22, 12), (16, 10), (14, 15), (13, 21)], 'hair'),
    ]
    det = []
    eye(det, 17, 14, iris='#1E8F5A'); eye(det, 27, 14, iris='#1E8F5A')
    det += [(16, 14, '#120C14'), (30, 14, '#120C14')]  # outer lashes
    det += [(17, 13, '#7A1A16'), (18, 13, '#7A1A16'), (28, 13, '#7A1A16'), (29, 13, '#7A1A16')]  # brows
    det += [(23, 21, '#D2343F'), (24, 21, '#D2343F'), (25, 21, '#E8505A')]  # lips
    det += [(18, 19, '#F2A3A0'), (30, 19, '#F2A3A0')]
    for (x, y) in ((13, 18), (13, 19), (12, 20), (13, 21), (35, 18), (35, 19), (36, 20), (35, 21)):
        det.append((x, y, '#F0C95C'))  # hoop earrings
    for y in range(28, 38, 2):
        det.append((18, y, '#8A8F99'))  # jacket zip
    det += [(24, 41, '#B5654A')]  # navel
    det += [(18, 44, '#C9CED6'), (19, 44, '#C9CED6'), (24, 44, '#F0C95C'), (25, 44, '#F0C95C')]  # belt buckle
    for y in range(52, 70, 3):
        det.append((15, y, '#262934')); det.append((33, y, '#262934'))  # cargo pocket seams
    det += [(15, 58, '#5A6072'), (16, 58, '#5A6072'), (33, 58, '#5A6072'), (32, 58, '#5A6072')]
    det += [(22, 31, '#D2343F'), (23, 31, '#D2343F'), (24, 31, '#D2343F'), (23, 32, '#D2343F')]  # heart print
    c.render(S, det, soft_pairs=[('face', 'neck'), ('neck', 'top'), ('top', 'midriff'), ('arm', 'hand'), ('hairback', 'hair')])
    return c

# ----------------------------------------------------------------- MIKA
def mika(sip=False):
    """Lavender space buns, oversized hoodie, baggy jeans, chunky sneakers, boba in hand."""
    R = {
        'shoe': dict(base='#F6F2F4', shade='#B9A9B4', bottom='#FF7FC8', bd=2),
        'jeans': dict(base='#8FB3D9', shade='#6189B5', light='#B7D2EE'),
        'hoodie': dict(base='#B9A2EA', shade='#8C72C9', light='#DCCBFF'),
        'sleeve': dict(base='#B9A2EA', shade='#8C72C9', light='#DCCBFF'),
        'hand': SKIN,
        'cup': dict(base='#CFE7EA', shade='#9CC0C6'),
        'tea': dict(base='#C79A6B', shade='#9C7148'),
        'neck': dict(base='#C07F63'),
        'face': SKIN,
        'bun': dict(base='#C6A8F2', shade='#9278C9', light='#E8D9FF'),
        'hair': dict(base='#C6A8F2', shade='#9278C9', light='#E8D9FF', top='#E8D9FF'),
    }
    c = Char(48, 82, R)
    hy = 33 if not sip else 27
    S = [
        ('ell', (11, 73, 22, 81), 'shoe'), ('ell', (26, 73, 37, 81), 'shoe'),
        ('poly', [(13, 47), (35, 47), (37, 75), (26, 75), (24, 56), (22, 75), (11, 75)], 'jeans'),
        ('poly', [(10, 26), (38, 26), (40, 50), (8, 50)], 'hoodie'),
        ('poly', [(6, 29), (12, 26), (13, 49), (6, 49)], 'sleeve'),
        ('ell', (6, 47, 12, 53), 'hand'),
        ('poly', [(36, 26), (42, 29), (40, hy + 6), (31, hy + 4), (32, hy - 1), (36, hy - 1)], 'sleeve'),
        ('rect', (27, hy - 8, 33, hy + 3), 'cup'),
        ('rect', (28, hy - 4, 32, hy + 2), 'tea'),
        ('ell', (27, hy, 33, hy + 6), 'hand'),
        ('rect', (21, 21, 27, 28), 'neck'),
        ('ell', (6, 1, 15, 10), 'bun'), ('ell', (33, 1, 42, 10), 'bun'),
        ('poly', [(14, 9), (34, 9), (34, 17), (31, 22), (26, 25), (22, 25), (17, 22), (14, 17)], 'face'),
        ('poly', [(12, 12), (14, 5), (19, 2), (29, 2), (34, 5), (36, 12), (35, 19), (33, 12), (29, 11), (26, 13), (22, 11), (18, 13), (15, 11), (14, 18), (13, 19)], 'hair'),
    ]
    det = []
    eye(det, 17, 14, iris='#5A3A9A', tall=4); eye(det, 27, 14, iris='#5A3A9A', tall=4)
    det += [(30, 14, '#120C14'), (16, 14, '#120C14')]
    det += [(23, 21, '#C0505A'), (24, 21, '#C0505A')]
    det += [(18, 19, '#F2A3A0'), (19, 19, '#F2A3A0'), (29, 19, '#F2A3A0'), (30, 19, '#F2A3A0')]
    det += [(15, 6, '#FFD23A'), (16, 7, '#FFD23A'), (14, 7, '#FFD23A'), (15, 8, '#FFD23A')]  # star clip
    # hoodie strings + kangaroo pocket + print
    det += [(21, 29, '#F4F1E8'), (21, 30, '#F4F1E8'), (21, 31, '#F4F1E8'), (26, 29, '#F4F1E8'), (26, 30, '#F4F1E8'), (26, 31, '#F4F1E8'), (26, 32, '#F4F1E8')]
    for x in range(15, 34):
        det.append((x, 42, '#8C72C9'))
    det += [(15, 43, '#8C72C9'), (33, 43, '#8C72C9')]
    det += [(18, 35, '#FF7FC8'), (19, 34, '#FF7FC8'), (20, 35, '#FF7FC8'), (19, 36, '#FF7FC8')]  # tiny heart
    # boba pearls + straw
    for (x, yy) in ((28, 1), (30, 0), (31, 1), (29, 0)):
        det.append((x, hy + yy, '#2A1A14'))
    for k in range(5):
        det.append((31, hy - 9 - k, '#FF7FC8'))
    det += [(27, hy - 8, '#FFFFFF')]
    # knee rips
    det += [(15, 62, '#E9F1FA'), (16, 62, '#E9F1FA'), (31, 63, '#E9F1FA'), (32, 63, '#E9F1FA')]
    c.render(S, det, soft_pairs=[('face', 'neck'), ('neck', 'hoodie'), ('sleeve', 'hand'), ('cup', 'tea'), ('hand', 'cup'), ('bun', 'hair')])
    return c

def preview_girls():
    canvas = np.zeros((86, 104, 3)); canvas[:] = hx('#0C2026')
    ruby().paste(canvas, 2, 2); mika().paste(canvas, 54, 2)
    Image.fromarray(canvas.astype(np.uint8)).resize((832, 688), Image.NEAREST).save('girls_preview.png')

# ----------------------------------------------------------------- BREW
def stripes(x, y):
    return hx('#F1F3F0') if (y // 2) % 2 == 0 else hx('#16171D')

def brew(f=0, nod=0):
    """Purple cuffed beanie with a patch, thick black glasses, striped long-sleeve, potion flask."""
    R = {
        'shoe': dict(base='#2A2F38', light='#4A5260', bottom='#E9EEEC', bd=2),
        'pants': dict(base='#191A21', shade='#0E0F14', light='#3A3F4A'),
        'shirt': dict(pattern=stripes, shade=True, sd=2),
        'sleeve': dict(pattern=stripes, shade=True, sd=2),
        'hand': SKIN,
        'neck': dict(base='#C07F63'),
        'face': SKIN,
        'hair': dict(base='#15161C', light='#3A3F5C'),
        'beanie': dict(base='#6E40C9', shade='#4B2A92', light='#9C76EA', top='#9C76EA'),
        'cuff': dict(base='#5A33AE', shade='#40227E', light='#8A62DE'),
        'patch': dict(base='#F4F1E8'),
        'glass': dict(base='#D9ECF4', shade='#A9C7D4', light='#FFFFFF'),
        'potion': dict(base='#8E4BFF', shade='#6A2FD6', light='#C9A2FF'),
        'cork': dict(base='#A47148', shade='#7A5232'),
        'frame': dict(base='#08090C'),
    }
    c = Char(50, 82, R)
    y = nod
    S = [
        ('ell', (12, 73, 23, 81), 'shoe'), ('ell', (25, 73, 36, 81), 'shoe'),
        ('poly', [(14, 47), (34, 47), (35, 75), (25, 75), (24, 57), (23, 75), (13, 75)], 'pants'),
        ('poly', [(11, 27), (37, 27), (38, 49), (10, 49)], 'shirt'),
        ('poly', [(7, 29), (12, 27), (13, 47), (7, 47)], 'sleeve'),
        ('ell', (6, 45, 12, 51), 'hand'),
        ('poly', [(35, 27), (40, 29), (43, 40), (37, 42), (35, 36)], 'sleeve'),
        # flask: bulb, neck, cork
        ('rect', (37, 16, 42, 27), 'glass'),
        ('ell', (32, 24, 47, 39), 'glass'),
        ('ell', (34, 29, 45, 38), 'potion'),
        ('rect', (38, 14, 41, 16), 'cork'),
        ('ell', (36, 38, 42, 44), 'hand'),
        ('rect', (21, 21 + y, 27, 28), 'neck'),
        ('poly', [(13, 10 + y), (35, 10 + y), (35, 18 + y), (32, 23 + y), (27, 26 + y), (21, 26 + y), (16, 23 + y), (13, 18 + y)], 'face'),
        ('poly', [(10, 10 + y), (14, 10 + y), (15, 19 + y), (11, 17 + y)], 'hair'),
        ('poly', [(34, 10 + y), (38, 10 + y), (37, 17 + y), (33, 19 + y)], 'hair'),
        ('poly', [(11, 6 + y), (13, 1 + y), (19, -2 + y), (29, -2 + y), (35, 1 + y), (37, 6 + y)], 'beanie'),
        ('rect', (10, 6 + y, 38, 11 + y), 'cuff'),
        ('rect', (17, 7 + y, 30, 10 + y), 'patch'),
        # glasses
        ('rect', (14, 13 + y, 22, 19 + y), 'frame'), ('rect', (26, 13 + y, 34, 19 + y), 'frame'),
        ('rect', (22, 14 + y, 26, 15 + y), 'frame'),
    ]
    det = []
    # lenses + eyes inside the frames
    for (lx, ly) in ((16, 15), (28, 15)):
        for xx in range(lx, lx + 5):
            for yy in range(ly, ly + 3):
                det.append((xx, yy + y, '#E9AE8C'))
        if BLINK:
            for xx in range(lx + 1, lx + 4):
                det.append((xx, ly + 1 + y, '#120C14'))
            continue
        det.append((lx + 2, ly + y, '#120C14')); det.append((lx + 2, ly + 1 + y, '#120C14'))
        det.append((lx + 3, ly + y, '#2B1E3A')); det.append((lx + 3, ly + 1 + y, '#2B1E3A'))
        det.append((lx + 2, ly + y, '#FFFFFF'))
    det += [(23, 22 + y, '#8C4A3C'), (24, 22 + y, '#8C4A3C'), (25, 22 + y, '#8C4A3C')]
    det += [(17, 21 + y, '#F2A3A0'), (31, 21 + y, '#F2A3A0')]
    # beanie: patch marks + cuff ribs
    for (xx, yy) in ((23, 7), (22, 8), (23, 8), (24, 8), (21, 8), (25, 8), (22, 9), (24, 9), (23, 9)):
        det.append((xx, yy + y, '#6E40C9'))
    for xx in range(11, 38, 2):
        if not (17 <= xx <= 30):
            det.append((xx, 9 + y, '#40227E'))
    # potion bubbles (animated) + glass shine
    for k in range(3):
        age = (f + k * 4) % 12
        bx = 37 + (k * 3) % 7
        by = 37 - age
        if by >= 30:
            det.append((bx, by, '#E6D2FF'))
    det += [(35, 27, '#FFFFFF'), (34, 28, '#FFFFFF'), (38, 18, '#FFFFFF'), (38, 19, '#FFFFFF')]
    c.render(S, det, soft_pairs=[('face', 'neck'), ('neck', 'shirt'), ('sleeve', 'hand'), ('glass', 'potion'), ('glass', 'cork'), ('hand', 'glass'), ('cuff', 'patch'), ('beanie', 'cuff'), ('frame', 'face')])
    return c, (39, 32)

def preview_brew():
    canvas = np.zeros((86, 56, 3)); canvas[:] = hx('#0C2026')
    c, _ = brew(); c.paste(canvas, 3, 2)
    Image.fromarray(canvas.astype(np.uint8)).resize((448, 688), Image.NEAREST).save('brew_preview.png')


def yuzu_front():
    """Front view: black bob with a pink streak, yellow tracksuit with black stripes, can in hand."""
    R = {
        'shoe': dict(base='#F0F2EE', shade='#9EA8A6', bottom='#5E6A6A'),
        'pants': YEL,
        'stripe': dict(base='#121212'),
        'jacket': YEL,
        'arm': YEL,
        'hand': SKIN,
        'neck': dict(base='#C07F63'),
        'face': SKIN,
        'hairback': dict(base='#17151F', shade='#0C0B12', light='#4A3F6A'),
        'hair': dict(base='#17151F', shade='#0C0B12', light='#4A3F6A', top='#4A3F6A'),
        'streak': dict(base='#FF4FB0', shade='#C23584'),
        'can': dict(base='#E9EEEC', shade='#9AA8A8', top='#FF3EA5'),
        'collar': dict(base='#121212'),
    }
    c = Char(48, 82, R)
    S = [
        ('poly', [(11, 8), (37, 8), (38, 24), (10, 24)], 'hairback'),
        ('ell', (11, 73, 22, 81), 'shoe'), ('ell', (26, 73, 37, 81), 'shoe'),
        ('poly', [(13, 46), (35, 46), (37, 75), (26, 75), (24, 56), (22, 75), (11, 75)], 'pants'),
        ('poly', [(11, 52), (12, 52), (12, 75), (11, 75)], 'stripe'),
        ('poly', [(35, 52), (36, 52), (37, 75), (36, 75)], 'stripe'),
        ('poly', [(11, 27), (37, 27), (38, 48), (10, 48)], 'jacket'),
        ('poly', [(7, 29), (12, 27), (13, 46), (8, 46)], 'arm'),
        ('ell', (7, 44, 13, 50), 'hand'),
        ('poly', [(36, 27), (41, 29), (44, 38), (40, 40), (37, 34)], 'arm'),
        ('rect', (40, 26, 44, 36), 'can'),
        ('ell', (39, 34, 45, 40), 'hand'),
        ('rect', (21, 21, 27, 28), 'neck'),
        ('rect', (18, 26, 30, 28), 'collar'),
        ('poly', [(14, 9), (34, 9), (34, 17), (31, 22), (26, 25), (22, 25), (17, 22), (14, 17)], 'face'),
        ('poly', [(11, 11), (13, 4), (18, 1), (30, 1), (35, 4), (37, 11), (37, 22), (34, 20), (33, 12), (28, 10), (20, 10), (15, 12), (14, 20), (11, 22)], 'hair'),
        ('poly', [(28, 2), (31, 3), (30, 13), (28, 11)], 'streak'),
    ]
    det = []
    eye(det, 17, 14, iris='#3A2A55'); eye(det, 27, 14, iris='#3A2A55')
    det += [(16, 14, '#120C14'), (30, 14, '#120C14')]
    det += [(23, 21, '#C0505A'), (24, 21, '#C0505A')]
    det += [(18, 19, '#F2A3A0'), (30, 19, '#F2A3A0')]
    det += [(32, 6, '#FF4FB0'), (33, 6, '#FF4FB0'), (32, 7, '#FFC2E3')]
    for y in range(28, 48):
        det.append((24, y, '#121212'))
    det += [(23, 29, '#9AA6A6'), (25, 29, '#9AA6A6')]
    for y in range(29, 46):
        det.append((10 + (y - 29) // 9, y, '#121212'))
    for k in range(10):
        det.append((37 + k // 3, 29 + k, '#121212'))
    det += [(14, 35, '#121212'), (15, 35, '#121212'), (14, 36, '#121212'), (33, 35, '#121212'), (34, 35, '#121212'), (34, 36, '#121212')]
    c.render(S, det, soft_pairs=[('neck', 'collar'), ('face', 'neck'), ('pants', 'stripe'), ('hand', 'can'), ('arm', 'hand'), ('hairback', 'hair'), ('hair', 'streak')])
    return c

# ----------------------------------------------------------------- SERGIO (b-boy, backflips)
def _sky_regions():
    return {
        'shoe': dict(base='#E0464F', shade='#A82E36', bottom='#F2F4F1', bd=2),
        'pants': dict(base='#1E1F27', shade='#111218', light='#3E4150'),
        'jacket': dict(base='#FF8A3D', shade='#D2621B', light='#FFB57A'),
        'sleeve': dict(base='#FF8A3D', shade='#D2621B', light='#FFB57A'),
        'stripe': dict(base='#F4F1E8'),
        'hand': dict(base='#D9976F', shade='#A86A4C', light='#ECB48F'),
        'neck': dict(base='#A86A4C'),
        'face': dict(base='#D9976F', shade='#A86A4C', light='#ECB48F'),
        'hair': dict(base='#E6ECF2', shade='#AEB8C4', light='#FFFFFF', top='#FFFFFF'),
        'band': dict(base='#E0464F', shade='#A82E36'),
    }

def _sky_head(S, det, oy, ox=0):
    y, x = oy, ox
    S += [
        ('rect', (21 + x, 21 + y, 26 + x, 27 + y), 'neck'),
        ('poly', [(14 + x, 9 + y), (33 + x, 9 + y), (33 + x, 17 + y), (30 + x, 22 + y), (25 + x, 25 + y), (21 + x, 25 + y), (16 + x, 22 + y), (14 + x, 17 + y)], 'face'),
        ('poly', [(12 + x, 12 + y), (11 + x, 5 + y), (14 + x, 6 + y), (15 + x, 1 + y), (19 + x, 3 + y), (22 + x, -2 + y), (25 + x, 2 + y), (29 + x, -1 + y), (31 + x, 4 + y), (35 + x, 3 + y), (35 + x, 12 + y)], 'hair'),
        ('rect', (12 + x, 9 + y, 35 + x, 11 + y), 'band'),
    ]
    eye(det, 17 + x, 14 + y, iris='#2B1E3A'); eye(det, 26 + x, 14 + y, iris='#2B1E3A')
    det += [(22 + x, 21 + y, '#8C4A3C'), (23 + x, 21 + y, '#8C4A3C'), (24 + x, 21 + y, '#8C4A3C'), (24 + x, 20 + y, '#8C4A3C')]  # grin
    det += [(13 + x, 15 + y, '#E8C35A'), (34 + x, 15 + y, '#E8C35A')]
    for xx in range(14, 34, 3):
        det.append((xx + x, 10 + y, '#F4F1E8'))

SKY_SOFT = [('face', 'neck'), ('neck', 'jacket'), ('sleeve', 'hand'), ('jacket', 'stripe'), ('sleeve', 'stripe'), ('hair', 'band')]

def sky_stand(nod=0, crouch=0, arms_up=False):
    """crouch: 0 standing, 1 knees bent (take-off / landing). arms_up: jump frame."""
    c = Char(48, 82, _sky_regions()); S = []; det = []
    d = 6 if crouch else 0
    if arms_up:
        S += [('poly', [(10, 30), (15, 27), (12, 6), (7, 7)], 'sleeve'), ('poly', [(33, 27), (38, 30), (41, 7), (36, 6)], 'sleeve'),
              ('ell', (6, 1, 12, 7), 'hand'), ('ell', (36, 1, 42, 7), 'hand')]
    S += [
        ('ell', (11, 73, 22, 81), 'shoe'), ('ell', (26, 73, 37, 81), 'shoe'),
        ('poly', [(13, 47 + d), (35, 47 + d), (37, 75), (26, 75), (24, 58 + d), (22, 75), (11, 75)], 'pants'),
        ('poly', [(11, 27 + d), (37, 27 + d), (38, 49 + d), (10, 49 + d)], 'jacket'),
        ('poly', [(23, 27 + d), (25, 27 + d), (25, 49 + d), (23, 49 + d)], 'stripe'),
    ]
    if not arms_up:
        S += [
        ('poly', [(6, 29 + d), (12, 27 + d), (13, 46 + d), (7, 46 + d)] if not crouch else [(4, 30 + d), (12, 27 + d), (10, 40 + d), (2, 42 + d)], 'sleeve'),
        ('poly', [(36, 27 + d), (42, 29 + d), (41, 46 + d), (35, 46 + d)] if not crouch else [(36, 27 + d), (44, 30 + d), (46, 42 + d), (38, 40 + d)], 'sleeve'),
        ('ell', (6, 44 + d, 12, 50 + d) if not crouch else (1, 40 + d, 7, 46 + d), 'hand'),
        ('ell', (36, 44 + d, 42, 50 + d) if not crouch else (41, 40 + d, 47, 46 + d), 'hand'),
        ]
    _sky_head(S, det, nod + d)
    if not arms_up:
        det += [(8, 36 + d, '#F4F1E8'), (39, 36 + d, '#F4F1E8')]
    c.render(S, det, soft_pairs=SKY_SOFT)
    return c

def sky_sit(nod=0):
    """Sitting on a step, shins dangling, elbows on knees. Hips at row 44."""
    c = Char(48, 66, _sky_regions()); S = []; det = []
    S += [
        ('ell', (11, 58, 21, 65), 'shoe'), ('ell', (27, 58, 37, 65), 'shoe'),
        ('rect', (13, 48, 20, 60), 'pants'), ('rect', (28, 48, 35, 60), 'pants'),
        ('ell', (10, 40, 23, 50), 'pants'), ('ell', (25, 40, 38, 50), 'pants'),
        ('poly', [(12, 26), (36, 26), (37, 44), (11, 44)], 'jacket'),
        ('poly', [(23, 26), (25, 26), (25, 44), (23, 44)], 'stripe'),
        ('poly', [(7, 28), (13, 26), (16, 41), (9, 43)], 'sleeve'),
        ('poly', [(35, 26), (41, 28), (39, 43), (32, 41)], 'sleeve'),
        ('ell', (12, 38, 18, 44), 'hand'), ('ell', (30, 38, 36, 44), 'hand'),
    ]
    _sky_head(S, det, nod - 1)
    c.render(S, det, soft_pairs=SKY_SOFT + [('pants', 'hand')])
    return c

def sky_tuck():
    """Mid-air tuck in side profile, facing LEFT. Rotate clockwise for a backflip. 40x40."""
    c = Char(40, 40, _sky_regions()); S = []; det = []
    S += [
        ('ell', (13, 12, 37, 37), 'jacket'),                       # rounded back
        ('poly', [(30, 14), (34, 17), (36, 26), (33, 28)], 'stripe'),
        ('ell', (6, 18, 26, 31), 'pants'),                         # thighs hugged to the chest
        ('poly', [(6, 24), (14, 24), (14, 36), (6, 36)], 'pants'),  # shins
        ('ell', (1, 32, 14, 39), 'shoe'),
        ('poly', [(26, 16), (31, 20), (14, 27), (10, 23)], 'sleeve'),  # arm wrapped round the knees
        ('ell', (6, 21, 12, 27), 'hand'),
        # head in profile, facing left
        ('poly', [(6, 6), (20, 4), (22, 15), (16, 19), (9, 18), (6, 14), (4, 12), (6, 10)], 'face'),
        ('poly', [(8, 5), (9, 0), (13, 2), (15, -1), (19, 2), (23, 0), (25, 5), (26, 12), (22, 14), (20, 6)], 'hair'),
        ('poly', [(7, 5), (24, 3), (24, 6), (7, 8)], 'band'),
    ]
    det += [(9, 10, '#120C14'), (9, 11, '#2B1E3A'), (10, 11, '#2B1E3A'), (10, 10, '#120C14'), (9, 11, '#FFFFFF')]
    det += [(7, 15, '#8C4A3C'), (8, 15, '#8C4A3C')]
    det += [(18, 10, '#A86A4C'), (18, 11, '#A86A4C'), (19, 12, '#E8C35A')]  # ear + stud
    c.render(S, det, soft_pairs=SKY_SOFT + [('pants', 'hand'), ('jacket', 'pants'), ('face', 'hair'), ('pants', 'shoe')])
    return c

def rot(c, k):
    """Rotate a rendered Char by k*90 degrees (pixel-perfect)."""
    import copy
    n = copy.copy(c)
    n.rgb = np.rot90(c.rgb, k).copy(); n.a = np.rot90(c.a, k).copy()
    n.h, n.w = n.a.shape
    return n

def preview_sky():
    canvas = np.zeros((86, 200, 3)); canvas[:] = hx('#0C2026')
    sky_stand().paste(canvas, 0, 2); sky_sit().paste(canvas, 50, 18); sky_stand(crouch=1).paste(canvas, 100, 2)
    tk = sky_tuck(); tk.paste(canvas, 150, 2); rot(tk, 1).paste(canvas, 150, 44)
    Image.fromarray(canvas.astype(np.uint8)).resize((1200, 516), Image.NEAREST).save('sky_preview.png')


# ----------------------------------------------------------------- TRUE OG (unlockable)
def true_og(nod=0, bounce=0):
    """Big heavy hip-hop dude, not a ball: broad shoulders, gut under an oversized red CANADA hoodie,
    beard, backwards cap, chunky chain, baggy jeans, fat sneakers."""
    R = {
        'shoe': dict(base='#F4F6F3', shade='#A9B3B1', bottom='#5E6A6A'),
        'pants': dict(base='#2B3A57', shade='#1B263B', light='#41557C'),
        'hood': dict(base='#A51B2E', shade='#7E1222'),
        'hoodie': dict(base='#D7263D', shade='#A51B2E', light='#F2566A'),
        'belly': dict(base='#D7263D', shade='#A51B2E', light='#F2566A'),
        'pocket': dict(base='#C11F35', shade='#9A1828'),
        'sleeve': dict(base='#D7263D', shade='#A51B2E', light='#F2566A'),
        'hand': dict(base='#C98A64', shade='#9C6546', light='#E2A985'),
        'neck': dict(base='#9C6546'),
        'face': dict(base='#C98A64', shade='#9C6546', light='#E2A985'),
        'beard': dict(base='#2A1B12', shade='#170E08'),
        'cap': dict(base='#15171C', shade='#0B0C10', light='#3A3F4C', top='#3A3F4C'),
        'brim': dict(base='#0E0F13', top='#2C3038'),
    }
    c = Char(60, 92, R)
    y, b = nod, bounce
    S = [
        ('ell', (6, 82, 27, 91), 'shoe'), ('ell', (33, 82, 54, 91), 'shoe'),
        ('poly', [(11, 58), (49, 58), (53, 85), (32, 85), (30, 68), (28, 85), (7, 85)], 'pants'),
        ('ell', (16, 27, 44, 37), 'hood'),
        ('poly', [(6, 33), (54, 33), (55, 48), (54, 64), (6, 64), (5, 48)], 'hoodie'),
        ('ell', (10, 42 + b, 50, 66 + b), 'belly'),
        ('poly', [(18, 54 + b), (42, 54 + b), (44, 63 + b), (16, 63 + b)], 'pocket'),
        ('poly', [(0, 37), (8, 33), (11, 58), (2, 60)], 'sleeve'),
        ('poly', [(52, 33), (60, 37), (58, 60), (49, 58)], 'sleeve'),
        ('ell', (0, 56, 9, 64), 'hand'), ('ell', (51, 56, 60, 64), 'hand'),
        ('rect', (24, 25 + y, 36, 33), 'neck'),
        ('poly', [(19, 9 + y), (41, 9 + y), (42, 19 + y), (40, 25 + y), (35, 29 + y), (25, 29 + y), (20, 25 + y), (18, 19 + y)], 'face'),
        ('poly', [(19, 19 + y), (21, 25 + y), (25, 29 + y), (35, 29 + y), (39, 25 + y), (41, 19 + y), (41, 24 + y), (37, 31 + y), (23, 31 + y), (19, 24 + y)], 'beard'),
        ('poly', [(18, 11 + y), (19, 4 + y), (24, 1 + y), (36, 1 + y), (41, 4 + y), (42, 11 + y)], 'cap'),
        ('poly', [(37, 8 + y), (49, 10 + y), (49, 13 + y), (38, 12 + y)], 'brim'),
    ]
    det = []
    # relaxed half-lidded eyes, heavy brows, smirk inside the beard
    for (ex, ey) in ((22, 15), (32, 15)):
        for k in range(5): det.append((ex + k, ey + y, '#1A100A'))
        det += [(ex + 1, ey + 1 + y, '#2B1E3A'), (ex + 2, ey + 1 + y, '#2B1E3A'), (ex + 2, ey + 1 + y, '#FFFFFF')]
    det += [(29, 19 + y, '#9C6546'), (30, 19 + y, '#9C6546'), (30, 20 + y, '#9C6546')]
    for k in range(6): det.append((27 + k, 25 + y - (1 if k == 5 else 0), '#5A2A22'))
    det += [(28, 24 + y, '#E9EEEC'), (29, 24 + y, '#E9EEEC'), (30, 24 + y, '#E9EEEC')]
    det += [(19, 15 + y, '#F0C95C'), (19, 16 + y, '#F0C95C')]  # ear stud
    # chunky chain with a pendant
    for k in range(19): det.append((21 + k, 35 + (abs(9 - k) < 5) + (abs(9 - k) < 3) + (abs(9 - k) < 1), '#F0C95C' if k % 2 else '#B48A30'))
    for (dx, dy) in ((0, 0), (-1, 1), (0, 1), (1, 1), (0, 2), (-1, 2), (1, 2), (0, 3)): det.append((30 + dx, 39 + dy, '#F0C95C' if dy < 3 else '#B48A30'))
    # CANADA across the chest
    G = {'C': ['###', '#..', '#..', '#..', '###'], 'A': ['.#.', '#.#', '###', '#.#', '#.#'], 'N': ['#.#', '###', '###', '###', '#.#'], 'D': ['##.', '#.#', '#.#', '#.#', '##.']}
    x0 = 18
    for ch in 'CANADA':
        for gy, row in enumerate(G[ch]):
            for gx, p in enumerate(row):
                if p == '#': det.append((x0 + gx, 45 + gy + b, '#FFFFFF'))
        x0 += 4
    # flag patch on the left sleeve
    for yy in range(40, 45):
        for xx in range(2, 10):
            det.append((xx, yy, '#D7263D' if xx < 4 or xx > 7 else '#FFFFFF'))
    det += [(5, 41, '#D7263D'), (6, 41, '#D7263D'), (5, 42, '#D7263D'), (6, 42, '#D7263D'), (4, 42, '#D7263D'), (7, 42, '#D7263D'), (5, 43, '#D7263D'), (6, 43, '#D7263D')]
    for k in range(6): det += [(26, 34 + k, '#F4F1E8'), (34, 34 + k, '#F4F1E8')]   # hoodie strings
    for yy in range(66, 84, 4): det += [(16, yy, '#1B263B'), (44, yy, '#1B263B')]       # baggy jean creases
    c.render(S, det, soft_pairs=[('face', 'neck'), ('neck', 'hoodie'), ('hood', 'hoodie'), ('hoodie', 'belly'), ('belly', 'pocket'), ('sleeve', 'hand'), ('cap', 'brim'), ('hood', 'neck'), ('face', 'beard')])
    return c

def kitsune(bob=0, glow=False):
    """KITSUNE, TRUE OG's buddy: white hoodie with the hood up, a fox mask pushed to the side,
    cyan scarf, a fox spirit sleeping inside him (folklore kitsune, not anyone else's character)."""
    R = {
        'shoe': dict(base='#1A1C22', light='#3A3F4C', bottom='#E9EEEC', bd=2),
        'pants': dict(base='#22252E', shade='#14161B', light='#3E4352'),
        'hoodie': dict(base='#EEF1F0', shade='#B9C3C6', light='#FFFFFF'),
        'sleeve': dict(base='#EEF1F0', shade='#B9C3C6', light='#FFFFFF'),
        'hand': dict(base='#E9C2A0', shade='#C49A78', light='#F6D9BF'),
        'scarf': dict(base='#2EE6E6', shade='#1A9FA6', light='#9FF7F7'),
        'face': dict(base='#E9C2A0', shade='#C49A78', light='#F6D9BF'),
        'hair': dict(base='#2A2E3A', shade='#171A22', light='#4A5266'),
        'hood': dict(base='#E2E7E6', shade='#AEB8BB', light='#FFFFFF', top='#FFFFFF'),
        'mask': dict(base='#F7F7F2', shade='#D6D8D2'),
    }
    c = Char(46, 82, R)
    y = bob
    S = [
        ('ell', (10, 74, 21, 81), 'shoe'), ('ell', (25, 74, 36, 81), 'shoe'),
        ('poly', [(13, 47), (33, 47), (35, 76), (25, 76), (23, 57), (21, 76), (11, 76)], 'pants'),
        ('poly', [(10, 27), (36, 27), (37, 50), (9, 50)], 'hoodie'),
        ('poly', [(6, 29), (11, 27), (12, 48), (6, 48)], 'sleeve'), ('poly', [(35, 27), (40, 29), (40, 48), (34, 48)], 'sleeve'),
        ('ell', (5, 46, 11, 52), 'hand'), ('ell', (35, 46, 41, 52), 'hand'),
        ('poly', [(14, 24 + y), (32, 24 + y), (33, 30 + y), (13, 30 + y)], 'scarf'),
        ('poly', [(29, 28 + y), (34, 28 + y), (35, 40), (31, 40)], 'scarf'),
        ('poly', [(10, 8 + y), (13, 2 + y), (19, -1 + y), (27, -1 + y), (33, 2 + y), (36, 8 + y), (37, 24 + y), (9, 24 + y)], 'hood'),
        ('poly', [(14, 9 + y), (32, 9 + y), (32, 17 + y), (29, 22 + y), (25, 24 + y), (21, 24 + y), (17, 22 + y), (14, 17 + y)], 'face'),
        ('poly', [(13, 8 + y), (33, 8 + y), (33, 12 + y), (28, 11 + y), (23, 13 + y), (18, 11 + y), (13, 13 + y)], 'hair'),
        ('poly', [(30, 4 + y), (37, 3 + y), (40, 9 + y), (38, 15 + y), (32, 13 + y)], 'mask'),
    ]
    det = []
    eye(det, 17, 14, iris='#1A9FA6' if glow else '#2B3550'); eye(det, 26, 14, iris='#1A9FA6' if glow else '#2B3550')
    det += [(22, 20 + y, '#B5654A'), (23, 20 + y, '#B5654A')]
    det += [(18, 18 + y, '#F2A3A0'), (28, 18 + y, '#F2A3A0')]
    # fox mask markings (red and black), ears
    det += [(31, 4 + y, '#05080B'), (32, 3 + y, '#05080B'), (36, 3 + y, '#05080B'), (37, 4 + y, '#05080B')]
    det += [(33, 8 + y, '#D7263D'), (34, 9 + y, '#D7263D'), (36, 8 + y, '#D7263D'), (35, 9 + y, '#D7263D'), (34, 12 + y, '#05080B'), (35, 12 + y, '#05080B')]
    # hoodie print: small cyan flame
    for (dx, dy) in ((0, 0), (-1, 1), (0, 1), (1, 1), (-1, 2), (0, 2), (1, 2), (0, -1)): det.append((22 + dx, 36 + dy, '#2EE6E6'))
    c.render(S, det, soft_pairs=[('face', 'hood'), ('hood', 'scarf'), ('hoodie', 'scarf'), ('sleeve', 'hand'), ('hair', 'hood'), ('mask', 'hood')])
    return c

def fox_spirit(phase=0):
    """White folklore fox with nine tails of cyan fire. 72x48."""
    import math
    c = Char(72, 48, {'tail': dict(base='#9FF7F7', shade='#2EE6E6', light='#FFFFFF'), 'body': dict(base='#F4FAFA', shade='#BFE3E6', light='#FFFFFF'),
                      'head': dict(base='#F4FAFA', shade='#BFE3E6', light='#FFFFFF'), 'ear': dict(base='#F4FAFA', shade='#9FC9CC')})
    S = []
    for k in range(9):
        a = math.pi * (0.62 + k * 0.11) + math.sin(phase + k) * 0.08
        x1, y1 = 26 + math.cos(a) * 24, 30 - math.sin(a) * 26
        S.append(('line', ([(26, 30), (int(x1), int(y1))], 4), 'tail'))
        S.append(('ell', (int(x1) - 3, int(y1) - 3, int(x1) + 3, int(y1) + 3), 'tail'))
    S += [('ell', (24, 22, 54, 38), 'body'), ('poly', [(48, 18), (62, 16), (68, 24), (62, 30), (50, 30)], 'head'),
          ('poly', [(52, 18), (54, 8), (58, 17)], 'ear'), ('poly', [(58, 17), (62, 7), (63, 17)], 'ear'),
          ('rect', (30, 36, 33, 44), 'body'), ('rect', (46, 36, 49, 44), 'body')]
    det = [(60, 21, '#2EE6E6'), (61, 21, '#2EE6E6'), (60, 22, '#FFFFFF'), (67, 24, '#0A0C10'), (55, 25, '#F2A3B5')]
    for k in range(6): det.append((40 + k * 2 % 9, 25 + k % 3, '#9FF7F7'))
    c.render(S, det, soft_pairs=[('tail', 'body'), ('head', 'body'), ('ear', 'head')])
    return c
# ----------------------------------------------------------------- costumes (TRUE OG's vibes)
CLOTH_TOP = {'jacket', 'sleeve', 'shirt', 'hoodie', 'flannel', 'tank', 'top', 'arm', 'rib', 'collar', 'stripe', 'tee', 'belly', 'pocket', 'hood'}
CLOTH_LOW = {'pants', 'jeans'}
HEAD = {'face', 'hair', 'cap', 'brim', 'bandana', 'beanie', 'cuff', 'hairback', 'bun', 'streak', 'patch', 'frame'}

def _mask(c, names):
    m = np.zeros(c.L.shape, bool)
    for n in names:
        if n in c.idx: m |= c.L == c.idx[n]
    return m & (c.a > 0)

def recolor(c, names, base, pattern=None):
    """Swap the color of the given regions keeping their shading and line work."""
    m = _mask(c, names)
    if not m.any(): return m
    lum = c.rgb[m].mean(1)
    ref = np.percentile(lum, 70) or 1
    f = np.clip(lum / ref, 0.25, 1.35)[:, None]
    c.rgb[m] = np.clip(hx(base)[None, :] * f, 0, 255)
    return m

def head_box(c):
    """(face_x0, head_top, face_x1, face_top): face width for hats, whole head top for height."""
    m = _mask(c, HEAD)
    if not m.any(): return None
    ys, xs = np.nonzero(m)
    f = _mask(c, {'face'})
    if f.sum() < 12: f = _mask(c, {'hair', 'hairback'})
    fy, fx = np.nonzero(f)
    return fx.min(), ys.min(), fx.max(), fy.min()

def apply_costume(c, vibe):
    """Recolor clothes in-sprite. Returns the head box (sprite coords) for hats drawn in the scene."""
    if vibe == 'clan':
        m = recolor(c, CLOTH_TOP | CLOTH_LOW, '#1A1A22')
        ys, xs = np.nonzero(m)
        if len(ys):
            # neon-green STONEPARK leaves on the robe
            for k, (fx, fy) in enumerate(((0.3, 0.25), (0.7, 0.45), (0.4, 0.7), (0.65, 0.15))):
                x = int(xs.min() + (xs.max() - xs.min()) * fx); y = int(ys.min() + (ys.max() - ys.min()) * fy)
                for (dx, dy) in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1), (1, -1)):
                    if 0 <= y + dy < c.h and 0 <= x + dx < c.w and m[y + dy, x + dx]:
                        c.rgb[y + dy, x + dx] = hx('#5CFF96' if (dx, dy) != (0, 0) else '#C9FFDD')
            # red inner lining on the collar line
            top = ys.min()
            for x in range(xs.min(), xs.max() + 1):
                if m[top, x]: c.rgb[top, x] = hx('#C4253A')
    elif vibe == 'winter':
        m = recolor(c, CLOTH_TOP, '#D7263D')
        ys, xs = np.nonzero(m)
        if len(ys):
            cx = int(xs.mean()); cy = int(ys.min() + (ys.max() - ys.min()) * 0.35)
            leaf = [(0, -2), (-1, -1), (0, -1), (1, -1), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (0, 2)]
            for (dx, dy) in leaf:
                if 0 <= cy + dy < c.h and 0 <= cx + dx < c.w and m[cy + dy, cx + dx]: c.rgb[cy + dy, cx + dx] = hx('#FFFFFF')
    return head_box(c)

def draw_hat(put, ox, oy, box, vibe, t=0):
    """Hats are drawn straight into the scene so they can stick out above the sprite."""
    if not box: return
    x0, top, x1, ftop = box
    X0, X1, T, F = ox + x0, ox + x1, oy + top, oy + ftop
    w = X1 - X0; cx = X0 + w // 2
    if vibe == 'clan':   # forehead protector: metal plate on a dark band
        yb = F + 1
        for x in range(X0, X1 + 1):
            put(x, yb, '#22252E'); put(x, yb + 1, '#22252E')
        for x in range(cx - 4, cx + 5):
            put(x, yb - 1, '#05080B'); put(x, yb, '#AEB8C2'); put(x, yb + 1, '#8A949E'); put(x, yb + 2, '#05080B')
        put(cx, yb, '#5CFF96'); put(cx - 1, yb + 1, '#5CFF96'); put(cx + 1, yb + 1, '#5CFF96')
    elif vibe == 'winter':  # ushanka
        for yy in range(T - 3, F + 2):
            inset = max(0, 2 - (yy - (T - 3)))
            for x in range(X0 - 1 + inset, X1 + 2 - inset):
                put(x, yy, '#6B4A2E' if yy < F - 1 else '#D9CBB0')
            put(X0 - 2 + inset, yy, '#05080B'); put(X1 + 2 - inset, yy, '#05080B')
        for x in range(X0 + 1, X1): put(x, T - 4, '#05080B')
        for yy in range(F, F + 9):
            for k in range(3):
                put(X0 - 1 + k, yy, '#D9CBB0'); put(X1 + 1 - k, yy, '#D9CBB0')
            put(X0 - 2, yy, '#05080B'); put(X1 + 2, yy, '#05080B')
        put(cx, T - 1, '#F0C95C')
    elif vibe == 'party':   # striped cone hat with a pom
        for k in range(14):
            half = 1 + k * 6 // 14
            for x in range(cx - half, cx + half + 1):
                put(x, T - 13 + k, ('#FF3EA5', '#FFD23A', '#2EE6E6')[(k // 3) % 3])
            put(cx - half - 1, T - 13 + k, '#05080B'); put(cx + half + 1, T - 13 + k, '#05080B')
        for (dx, dy) in ((0, -15), (-1, -14), (1, -14), (0, -14)): put(cx + dx, T + dy, '#F4F1E8')


def wok(nod=0, visor=0):
    """WOK: beatmaker, VR headset always on, grey hoodie, messy hair. Front view."""
    R = {
        'shoe': dict(base='#E9EEF0', shade='#9AA6A6', bottom='#3A3F4C'),
        'pants': dict(base='#22252E', shade='#14161B', light='#3E4352'),
        'hoodie': dict(base='#3A3F4C', shade='#262A33', light='#555B6B'),
        'sleeve': dict(base='#3A3F4C', shade='#262A33', light='#555B6B'),
        'hand': dict(base='#C98A64', shade='#9C6546', light='#E2A985'),
        'neck': dict(base='#9C6546'),
        'face': dict(base='#C98A64', shade='#9C6546', light='#E2A985'),
        'hair': dict(base='#1E140E', shade='#120A06', light='#3A2A1E'),
        'vr': dict(base='#E9EEF0', shade='#AEB8C2', light='#FFFFFF'),
        'visor': dict(base='#5B2BB8', shade='#3A1C80', light='#9B5CFF'),
        'strap': dict(base='#2A2E3A'),
    }
    c = Char(46, 82, R)
    y = nod
    S = [
        ('ell', (9, 74, 21, 81), 'shoe'), ('ell', (25, 74, 37, 81), 'shoe'),
        ('poly', [(12, 47), (34, 47), (36, 76), (25, 76), (23, 58), (21, 76), (10, 76)], 'pants'),
        ('poly', [(8, 27), (38, 27), (39, 52), (7, 52)], 'hoodie'),
        ('poly', [(4, 29), (9, 27), (10, 50), (4, 50)], 'sleeve'), ('poly', [(37, 27), (42, 29), (42, 50), (36, 50)], 'sleeve'),
        ('ell', (3, 48, 10, 54), 'hand'), ('ell', (36, 48, 43, 54), 'hand'),
        ('rect', (19, 22 + y, 27, 28), 'neck'),
        ('ell', (12, 4 + y, 34, 26 + y), 'face'),
        ('poly', [(11, 10 + y), (12, 2 + y), (16, -1 + y), (22, 1 + y), (26, -1 + y), (31, 1 + y), (35, 4 + y), (35, 10 + y), (33, 7 + y), (28, 5 + y), (22, 7 + y), (16, 5 + y), (13, 8 + y)], 'hair'),
        ('rect', (10, 10 + y, 36, 19 + y), 'vr'),
        ('rect', (12, 12 + y, 34, 17 + y), 'visor'),
        ('rect', (8, 12 + y, 10, 16 + y), 'strap'), ('rect', (36, 12 + y, 38, 16 + y), 'strap'),
    ]
    det = []
    # visor scanline + glow pixels
    vx = 13 + (visor % 20)
    det += [(vx, 14 + y, '#2EE6E6'), (vx + 1, 14 + y, '#9FF7F7'), (vx + 2, 14 + y, '#2EE6E6')]
    det += [(11, 11 + y, '#2EE6E6'), (34, 11 + y, '#2EE6E6')]
    # unimpressed mouth, stubble
    for k in range(5): det.append((21 + k, 22 + y, '#6A3A2A'))
    for (x, yy) in ((18, 22), (19, 23), (27, 23), (28, 22), (23, 24)): det.append((x, yy + y, '#7A5040'))
    # hoodie: cable-print and drawstrings
    for k in range(6): det += [(20, 28 + k, '#C9D3DC'), (26, 28 + k, '#C9D3DC')]
    for (x, yy) in ((14, 38), (15, 39), (16, 40), (17, 40), (18, 39), (19, 38), (20, 38), (21, 39), (22, 40), (23, 40), (24, 39), (25, 38), (26, 38), (27, 39), (28, 40), (29, 40), (30, 39), (31, 38)):
        det.append((x, yy, '#9B5CFF'))
    c.render(S, det, soft_pairs=[('face', 'neck'), ('neck', 'hoodie'), ('sleeve', 'hand'), ('hair', 'face'), ('vr', 'face'), ('vr', 'hair'), ('visor', 'vr'), ('strap', 'vr')])
    return c
