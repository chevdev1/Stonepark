"""STONEPARK comic, chapter 1 "The first wall". Renders 12 panels into comic/p01.png ... p12.png (native x3)."""
import sys, math, random
sys.path.insert(0, '.')
import numpy as np
from PIL import Image
import chars, piece
from chars import hx
WIDE, HALF = (400, 160), (196, 150)
def blank(w, h, c='#000000'): a = np.zeros((h, w, 3), np.float32); a[:] = hx(c); return a
def put(a, x, y, c, k=1.0):
    x, y = int(round(x)), int(round(y))
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]: a[y, x] = a[y, x] * (1 - k) + hx(c) * k
def rect(a, x0, y0, x1, y1, c, k=1.0):
    H, W = a.shape[:2]; x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(W, int(x1)), min(H, int(y1))
    if x1 > x0 and y1 > y0: a[y0:y1, x0:x1] = a[y0:y1, x0:x1] * (1 - k) + hx(c) * k
def glow(a, cx, cy, r, c, k):
    H, W = a.shape[:2]; col = hx(c)
    ys, xs = np.mgrid[0:H, 0:W]; d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) / r
    m = np.clip(1 - d, 0, 1) ** 2
    a += m[..., None] * col * k
def grad(a, top, bot):
    H = a.shape[0]
    for y in range(H): a[y] = hx(top) * (1 - y / H) + hx(bot) * (y / H)
def vignette(a, k=0.45):
    H, W = a.shape[:2]; ys, xs = np.mgrid[0:H, 0:W]
    a *= (1 - k * (((xs - W / 2) / (W / 2)) ** 2 + ((ys - H / 2) / (H / 2)) ** 2))[..., None]
def bricks(a, x0, y0, x1, y1, base='#2A2F3C', var=('#262B37', '#2E3442', '#23283A'), seed=1):
    r = random.Random(seed)
    rect(a, x0, y0, x1, y1, '#14161E')
    for row, y in enumerate(range(y0, y1, 6)):
        off = (row % 2) * 6
        for x in range(x0 - off, x1, 12):
            rect(a, max(x0, x + 1), y + 1, min(x1, x + 12), min(y1, y + 6), r.choice(var))
def skyline(a, ground, seed=2, far=('#121029', '#1A1638'), win=('#FFD23A', '#FF4FD8', '#2EE6E6', '#F4F1E8')):
    W = a.shape[1]; r = random.Random(seed)
    for layer, col in enumerate(far):
        x = -5
        while x < W:
            bw = r.randrange(14, 34); bh = r.randrange(20, 60) - layer * 10
            rect(a, x, ground - bh, x + bw, ground, col)
            if layer == 1:
                for wy in range(ground - bh + 4, ground - 3, 5):
                    for wx in range(x + 3, x + bw - 2, 4):
                        if r.random() < 0.28: put(a, wx, wy, r.choice(win), 0.9)
            x += bw + r.randrange(0, 4)
def stars(a, n=40, h=60, seed=3):
    r = random.Random(seed)
    for _ in range(n): put(a, r.randrange(a.shape[1]), r.randrange(h), '#E8F1EE', r.uniform(0.4, 1))
def moon(a, cx, cy, r=9):
    for y in range(-r, r + 1):
        for x in range(-r, r + 1):
            if x * x + y * y <= r * r: put(a, cx + x, cy + y, '#E8E2D0' if (x + 3) ** 2 + (y - 2) ** 2 > (r - 2) ** 2 or x < 2 else '#CFC8B4')
    glow(a, cx, cy, r * 4, '#5A5A90', 0.25)
def lamp(a, x, top, ground, c='#FFD08A', k=0.7):
    rect(a, x, top, x + 2, ground, '#0C0E14'); rect(a, x - 4, top, x + 4, top + 2, '#0C0E14'); rect(a, x - 3, top + 2, x + 3, top + 4, c)
    H, W = a.shape[:2]
    for y in range(top + 4, ground):
        sp = (y - top) * 0.55
        for xx in range(int(x - sp), int(x + sp) + 2):
            if 0 <= xx < W: a[y, xx] = a[y, xx] + hx(c) * 0.08 * k * (1 - (y - top) / (ground - top + 30))
    glow(a, x + 1, top + 3, 26, c, 0.35 * k)
def rain(a, n=180, seed=5, c='#9FB7D8', k=0.35):
    r = random.Random(seed); H, W = a.shape[:2]
    for _ in range(n):
        x, y, l = r.randrange(W), r.randrange(H), r.randrange(4, 9)
        for i in range(l): put(a, x - i // 3, y + i, c, k)
def sprite(a, c, ox, oy, tint=None, dark=0.0, sil=None, rim=None, flip=False, scale=1):
    rgb = np.clip(c.rgb, 0, 255).astype(np.float32); m = c.a > 0
    if flip: rgb = rgb[:, ::-1]; m = m[:, ::-1]
    if scale > 1: rgb = rgb.repeat(scale, 0).repeat(scale, 1); m = m.repeat(scale, 0).repeat(scale, 1)
    if sil: rgb[:] = hx(sil)
    if dark: rgb *= (1 - dark)
    if tint is not None: rgb = rgb * (1 - tint[1]) + hx(tint[0]) * tint[1]
    if rim:
        e = m & ~(np.roll(m, 1, 1) & np.roll(m, -1, 1) & np.roll(m, 1, 0) & np.roll(m, -1, 0))
        rgb[e] = hx(rim)
    H, W = a.shape[:2]; h, w = m.shape
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        Y, X = oy + y, ox + x
        if 0 <= Y < H and 0 <= X < W: a[Y, X] = rgb[y, x]
def spray_mist(a, cx, cy, c, n=60, r=8, seed=7):
    rr = random.Random(seed)
    for _ in range(n):
        t = rr.uniform(0, 6.28); d = rr.uniform(0, r)
        put(a, cx + math.cos(t) * d, cy + math.sin(t) * d * 0.7, c, rr.uniform(0.3, 0.9))
def motion(a, x, y, l, c='#C9D6E6', k=0.5):
    for i in range(l): put(a, x - i, y, c, k * (1 - i / l))
def save(a, name, grade=None):
    if grade: a = a * np.array(grade, np.float32)
    vignette(a, 0.35)
    a += np.random.RandomState(len(name)).randint(-5, 5, a.shape[:2])[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    im = im.resize((im.width * 3, im.height * 3), Image.NEAREST)
    im.quantize(200, method=Image.Quantize.MEDIANCUT).save(f'comic/{name}.png', optimize=True)

# ----------------------------------------------------------------- helpers for chapter 1 "The first wall"
def jsprite(name, scale=2):
    im = np.asarray(Image.open(f'ui/j_{name}.png').convert('RGBA'))
    class S: pass
    c = S(); c.rgb = im[..., :3].astype(np.float32); c.a = (im[..., 3] > 0).astype(np.uint8); c.h, c.w = im.shape[:2]
    return c
def night_street(a, wall_top=40, ground=126, seed=1, lamp_x=None):
    W, H = a.shape[1], a.shape[0]
    grad(a, '#07061A', '#221A3E'); stars(a, 40, wall_top, seed=seed)
    skyline(a, wall_top + 6, seed=seed + 3)
    rect(a, 0, wall_top, W, ground, '#3A3F4A')
    for y in range(wall_top, ground, 8): rect(a, 0, y, W, y + 1, '#33373F')
    for x in range(0, W, 46): rect(a, x, wall_top, x + 1, ground, '#2E3239')
    rect(a, 0, ground, W, H, '#0E1016'); rect(a, 0, ground, W, ground + 1, '#4A4F5C')
    if lamp_x is not None: lamp(a, lamp_x, wall_top - 26, ground)
def flash_cone(a, x0, y0, x1, ya, yb, c='#FFF6C8', k=0.35):
    H, W = a.shape[:2]
    for x in range(min(x0, x1), max(x0, x1)):
        t = (x - x0) / (x1 - x0)
        top, bot = y0 + (ya - y0) * t, y0 + (yb - y0) * t
        for y in range(max(0, int(top)), min(H, int(bot))): a[y, x] = a[y, x] * (1 - k) + hx(c) * k
def piece_on(a, ox, oy, fade=1.0, seed=3):
    rgb, al = piece.make_piece(seed=seed); ph, pw = al.shape; H, W = a.shape[:2]
    for y in range(ph):
        for x in range(pw):
            if al[y, x] and 0 <= oy + y < H and 0 <= ox + x < W: a[oy + y, ox + x] = a[oy + y, ox + x] * (1 - fade) + rgb[y, x] * fade
# ----------------------------------------------------------------- page 1: an empty wall
def p01():
    a = blank(*WIDE); W, H = WIDE
    night_street(a, 34, 128, seed=2, lamp_x=200)
    moon(a, 340, 18, 8)
    rect(a, 0, 150, W, H, '#0B0C12')
    save(a, 'p01')
def p02():   # RUBY picks the wall
    a = blank(*HALF); W, H = HALF
    night_street(a, 20, 124, seed=5)
    r = chars.ruby(); sprite(a, r, 78, 124 - r.h + 30)
    for k in range(8): put(a, 122 + k * 3, 70 - k * 2, '#FFD23A', 0.8)   # pointing line
    glow(a, 150, 50, 50, '#FFD23A', 0.08)
    save(a, 'p02')
def p03():   # DEUCE drops the boombox
    a = blank(*HALF); W, H = HALF
    night_street(a, 20, 124, seed=7)
    d = chars.deuce(); sprite(a, d, 40, 124 - d.h + 30)
    bx, by = 112, 108   # boombox
    rect(a, bx, by, bx + 44, by + 18, '#22252E'); rect(a, bx, by, bx + 44, by + 2, '#3A3F4C')
    for cx in (bx + 10, bx + 34):
        for yy in range(-6, 7):
            for xx in range(-6, 7):
                if xx * xx + yy * yy <= 36: put(a, cx + xx, by + 10 + yy, '#0A0B10' if xx * xx + yy * yy > 9 else '#5CFF96')
    rect(a, bx + 16, by + 4, bx + 28, by + 8, '#5CFF96')
    for k in range(3):
        for t in range(14): put(a, bx + 22 + math.cos(t / 14 * 3.14) * (14 + k * 6), by - 2 - math.sin(t / 14 * 3.14) * (8 + k * 5), '#5CFF96', 0.5 - k * 0.12)
    save(a, 'p03')
# ----------------------------------------------------------------- page 2: everyone brings something
def p04():   # SADTR1P mixes "midnight", the others wait
    a = blank(*WIDE); W, H = WIDE
    night_street(a, 30, 128, seed=11, lamp_x=60)
    b, fl = chars.brew(); sprite(a, b, 150, 128 - b.h + 30)
    glow(a, 196, 96, 60, '#9B5CFF', 0.55)
    for k in range(14): put(a, 190 + (k * 7) % 22, 86 - k * 3, '#C9A2FF', 0.8)
    for i, x in enumerate((236, 262, 288)):   # cans getting filled
        rect(a, x, 132, x + 10, 150, ['#9B5CFF', '#FF3EA5', '#2EE6E6'][i]); rect(a, x, 132, x + 10, 134, '#E9EEF0')
    for fn, x in ((lambda: chars.vex()[0], 20), (chars.mika, 330)):
        c = fn(); sprite(a, c, x, 128 - c.h + 30, dark=0.35)
    save(a, 'p04', (0.98, 0.95, 1.08))
def p05():   # YUZU lays the first letters
    a = blank(*HALF); W, H = HALF
    night_street(a, 14, 124, seed=13)
    piece_on(a, -70, 26, 0.85)
    c, nz = chars.yuzu(t=1.6); sprite(a, c, 112, 124 - c.h + 30)
    spray_mist(a, 132, 40, '#FF7FC8', 90, 10)
    save(a, 'p05')
def p06():   # SERGIO on the roof, keeping watch
    a = blank(*HALF); W, H = HALF
    grad(a, '#07061A', '#2A1A48'); stars(a, 60, 90, seed=17); moon(a, 160, 28, 9)
    skyline(a, 120, seed=19)
    rect(a, 0, 118, W, H, '#14161E'); rect(a, 0, 118, W, 120, '#3A3F4C')
    s = chars.sky_stand(); sprite(a, s, 70, 118 - s.h + 2)
    rect(a, 120, 112, 146, 115, '#FF8A3D'); put(a, 124, 116, '#F4F1E8'); put(a, 141, 116, '#F4F1E8')   # board
    save(a, 'p06')
# ----------------------------------------------------------------- page 3: someone is coming
def p07():   # a flashlight sweeps the wall, the crew hides
    a = blank(*WIDE); W, H = WIDE
    night_street(a, 30, 128, seed=23)
    piece_on(a, 40, 34, 0.6)
    a *= 0.6
    flash_cone(a, W, 60, 160, 20, 150, k=0.32)
    rect(a, 40, 104, 120, 134, '#1F3A2A'); rect(a, 40, 104, 120, 107, '#2E5A3E')   # dumpster
    for i, x in enumerate((44, 64, 84, 100)):
        c = [chars.ruby, chars.deuce, chars.mika, lambda: chars.yuzu(0.0)[0]][i]()
        sprite(a, c, x, 104 - c.h + 34, sil='#07080C', rim='#5A4A90')
    rect(a, 40, 112, 120, 134, '#1F3A2A'); rect(a, 40, 112, 120, 113, '#2E5A3E')
    save(a, 'p07')
def p08():   # ...and out of the light comes a small white dog
    a = blank(*HALF); W, H = HALF
    night_street(a, 14, 124, seed=29)
    a *= 0.55
    flash_cone(a, W, 40, 20, 70, 150, k=0.33)
    for y in range(118, 132):   # bright spot on the ground
        w = int(46 * math.sin((y - 118) / 14 * math.pi)); rect(a, 86 - w, y, 86 + w, y + 1, '#FFF6C8', 0.25)
    j = jsprite('happy', 4); sprite(a, j, 36, 124 - j.h + 6)
    glow(a, 86, 100, 70, '#FFF6C8', 0.22)
    save(a, 'p08')
def p09():   # relief: everyone comes out, Johnny stays
    a = blank(*HALF); W, H = HALF
    night_street(a, 14, 124, seed=31)
    r = chars.ruby(); sprite(a, r, 12, 124 - r.h + 30)
    m = chars.mika(); sprite(a, m, 58, 124 - m.h + 30)
    j = jsprite('sit1', 2); sprite(a, j, 120, 124 - j.h + 2)
    for k in range(3): put(a, 136 + k * 4, 90 - k * 5, '#FF4FA3')   # hearts
    save(a, 'p09')
# ----------------------------------------------------------------- page 4: morning
def p10():   # the wall at dawn, everyone exhausted in front of it
    a = blank(*WIDE); W, H = WIDE
    grad(a, '#F2A86A', '#8FB8D8'); skyline(a, 40, seed=37, far=('#C08A78', '#9A7A88'), win=('#FFE6B0',))
    rect(a, 0, 34, W, 128, '#8A8F9A')
    for y in range(34, 128, 8): rect(a, 0, y, W, y + 1, '#7E838E')
    piece_on(a, 52, 40, 1.0)
    rect(a, 0, 128, W, H, '#5A5E68'); rect(a, 0, 128, W, 129, '#A0A4AE')
    glow(a, 360, 10, 160, '#FFD8A0', 0.35)
    crew = [(lambda: chars.vex()[0], 30, 0.1), (chars.ruby, 80, 0.1), (chars.deuce, 128, 0.1), (lambda: chars.brew()[0], 176, 0.1), (chars.mika, 228, 0.1), (lambda: chars.yuzu_front(), 276, 0.1), (chars.sky_sit, 326, 0.1)]
    for fn, x, d in crew:
        c = fn(); sprite(a, c, x, (160 - c.h + 26) if fn is not chars.sky_sit else 160 - c.h + 8, dark=d)
    j = jsprite('sit0', 2); sprite(a, j, 368, 160 - j.h - 2)
    save(a, 'p10', (1.05, 1.0, 0.95))
def p11():   # passers-by stop and look
    a = blank(*HALF); W, H = HALF
    grad(a, '#F2B07A', '#9CC0DC')
    rect(a, 0, 20, W, 120, '#8A8F9A'); piece_on(a, -120, 30, 1.0)
    rect(a, 0, 120, W, H, '#5A5E68')
    for i, (fn, x) in enumerate(((chars.ruby, 20), (lambda: chars.vex()[0], 70), (chars.deuce, 120))):
        c = fn(); sprite(a, c, x, 120 - c.h + 32, sil='#3A3F4C', rim='#C9D0DA')
    save(a, 'p11')
def p12():   # the crew, together
    a = blank(*HALF); W, H = HALF
    bricks(a, 0, 0, W, 124, seed=41); piece_on(a, -40, 4, 0.5)
    rect(a, 0, 124, W, H, '#0E1016')
    for fn, x in ((chars.ruby, 6), (lambda: chars.yuzu_front(), 44), (chars.mika, 84), (chars.deuce, 124)):
        c = fn(); sprite(a, c, x, 124 - c.h + 32)
    j = jsprite('happy', 2); sprite(a, j, 150, 124 - j.h + 2)
    glow(a, 98, 70, 110, '#FFB060', 0.12)
    save(a, 'p12')
if __name__ == '__main__':
    for f in (p01, p02, p03, p04, p05, p06, p07, p08, p09, p10, p11, p12):
        f(); print(f.__name__, end=' ', flush=True)
    print()
    ims = [Image.open(f'comic/p{i:02d}.png').convert('RGB') for i in range(1, 13)]
    sheet = Image.new('RGB', (1200 + 20, 4 * (480 + 450 + 20)), (0, 0, 0))
    y = 0
    for p in range(4):
        w, h1, h2 = ims[p * 3], ims[p * 3 + 1], ims[p * 3 + 2]
        sheet.paste(w, (0, y)); sheet.paste(h1, (0, y + 490)); sheet.paste(h2, (600, y + 490)); y += 490 + 460
    sheet.resize((sheet.width // 3, sheet.height // 3)).save('comic/contact.png')
