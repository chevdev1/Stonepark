"""Prototype #0 poster: the first lineup in costumes, stoned. python3 proto_poster.py"""
import sys, random
sys.path.insert(0, '.')
import numpy as np, chars
from PIL import Image, ImageDraw
from chars import recolor, _mask, hx
W, H = 320, 180
def P(c, x, y, col):
    if 0 <= x < c.w and 0 <= y < c.h: c.rgb[y, x] = hx(col); c.a[y, x] = 1
def box(c, x0, y0, x1, y1, col):
    for y in range(y0, y1):
        for x in range(x0, x1): P(c, x, y, col)
def edge(c, m, col):
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        for dy, dx in ((-1, 0), (0, -1), (0, 1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < c.h and 0 <= xx < c.w and not m[yy, xx] and c.a[yy, xx]: pass
        if (y > 0 and not m[y - 1, x]) or (x > 0 and not m[y, x - 1]): c.rgb[y, x] = hx(col)
# ---------------- costumes
def mecha_ch():
    chars.BLINK = True; c = chars.vex()[0]; chars.BLINK = False
    m = recolor(c, {'jacket', 'sleeve', 'rib', 'tee', 'pants', 'shoe'}, '#8C99A6')
    edge(c, m, '#C9D3DC')
    recolor(c, {'cap', 'brim', 'phones', 'cup'}, '#5E6B78')
    for x in range(11, 27): P(c, x, 14, '#05080B'); P(c, x, 15, '#FF2A44'); P(c, x, 16, '#FF2A44'); P(c, x, 17, '#05080B')   # red visor
    for x in range(13, 17): P(c, x, 15, '#FFB0B8')
    for y in range(-1, 4): P(c, 22, y, '#5E6B78')
    P(c, 22, -2, '#FF2A44')
    for (cx, cy) in ((20, 34),):   # glowing chest core
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 5: P(c, cx + dx, cy + dy, '#2EE6E6' if dx * dx + dy * dy <= 1 else '#1A8C92')
    for y in range(40, 70, 6): box(c, 10, y, 32, y + 1, '#5E6B78')   # panel lines
    for (x0, x1) in ((3, 12), (30, 39)):
        box(c, x0, 25, x1, 31, '#A7B3BF'); box(c, x0, 25, x1, 26, '#E2E9EF'); box(c, x0, 30, x1, 31, '#4A5560')
    return c, None
def goalie_og():
    c = chars.true_og()
    for (ex, ey) in ((22, 15), (32, 15)):
        for d in range(1, 4): P(c, ex + d, ey + 1, '#C98A64')
        for d in range(5): P(c, ex + d, ey + 2, '#E04848')
    # goalie mask pushed up on the head
    m = recolor(c, {'cap', 'brim'}, '#EEF1F0')
    ys, xs = np.nonzero(m)
    for x in range(xs.min(), xs.max() + 1, 3):
        for y in range(ys.min(), ys.max() + 1): 
            if m[y, x]: c.rgb[y, x] = hx('#2B2F38')
    # big leg pads
    pm = recolor(c, {'pants'}, '#F2F2EE')
    for y in range(64, 86, 5):
        for x in range(0, c.w):
            if pm[y, x]: c.rgb[y, x] = hx('#D7263D')
    # blocker and catcher
    box(c, -2, 54, 10, 66, '#F2F2EE'); box(c, -2, 54, 10, 55, '#05080B'); box(c, 0, 58, 8, 60, '#D7263D')
    box(c, 50, 54, 62, 66, '#7A4A2A'); box(c, 52, 56, 60, 58, '#B5824F')
    joint = (33, 25)
    for dx in range(5): P(c, joint[0] + dx, joint[1], '#F4EEDC')
    P(c, joint[0] + 4, joint[1], '#D9A35F'); P(c, joint[0] + 5, joint[1], '#FF7A2E')
    return c, (39, 25)
def idol_ruby():
    chars.BLINK = True; c = chars.ruby(); chars.BLINK = False
    for (x, y, t) in ((17, 14, 3), (27, 14, 3)):
        for dx in range(3): P(c, x + dx, y + t, '#E04848')
    m = recolor(c, {'jacket', 'arm'}, '#FF4FA3'); edge(c, m, '#FFE1F0')
    recolor(c, {'top'}, '#F4F1E8'); recolor(c, {'pants'}, '#2A1E3A'); recolor(c, {'boot'}, '#F4F1E8')
    recolor(c, {'belt'}, '#FFD23A')
    # headset: band over the hair, mic in front of the mouth
    for (x, y) in ((33, 9), (34, 10), (34, 11), (34, 12), (34, 13), (33, 14)): P(c, x, y, '#1A1C22')
    for (x, y) in ((33, 15), (32, 17), (31, 18), (30, 19), (29, 20)): P(c, x, y, '#1A1C22')
    for (x, y) in ((33, 16), (32, 18), (31, 19), (30, 20)): P(c, x, y, '#1A1C22')
    box(c, 26, 19, 29, 22, '#C9D3DC'); P(c, 27, 20, '#FF4FA3')
    for (sx, sy) in ((16, 4), (30, 3)):   # star clips
        for (dx, dy) in ((0, -1), (-1, 0), (0, 0), (1, 0), (0, 1)): P(c, sx + dx, sy + dy, '#FFD23A')
    for dx in range(5): P(c, 25 + dx, 21, '#F4EEDC')
    P(c, 29, 21, '#D9A35F'); P(c, 30, 21, '#FF7A2E')
    return c, (31, 21)
def knight_brew():
    c, _ = chars.brew()
    for (lx, ly) in ((16, 15), (28, 15)):
        for dx in range(5): P(c, lx + dx, ly, '#E9AE8C'); P(c, lx + dx, ly + 1, '#120C14')
        for dx in range(1, 4): P(c, lx + dx, ly + 2, '#E04848')
    m = recolor(c, {'shirt', 'sleeve', 'pants', 'shoe'}, '#9AA6B2'); edge(c, m, '#D5DEE6')
    recolor(c, {'beanie', 'cuff', 'patch'}, '#7D8996')
    for x in range(13, 37): P(c, x, 9, '#05080B')
    box(c, 18, 30, 31, 52, '#6A3FB8'); box(c, 18, 30, 31, 31, '#E7C55A'); box(c, 18, 51, 31, 52, '#E7C55A')   # tabard
    for (dx, dy) in ((0, -2), (0, -1), (-1, 0), (0, 0), (1, 0), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2)): P(c, 24 + dx, 39 + dy, '#E7C55A')   # flask crest
    for dx in range(5): P(c, 26 + dx, 22, '#F4EEDC')
    P(c, 30, 22, '#D9A35F'); P(c, 31, 22, '#FF7A2E')
    return c, (32, 22)
# ---------------- poster
def poster():
    img = np.zeros((H, W, 3), np.float32)
    stops = [(0, (46, 160, 70)), (0.45, (240, 226, 40)), (1, (240, 120, 30))]
    for x in range(W):
        t = x / (W - 1)
        for k in range(len(stops) - 1):
            a, ca = stops[k]; b, cb = stops[k + 1]
            if a <= t <= b:
                u = round((t - a) / (b - a) * 8) / 8; img[:, x] = np.array(ca) * (1 - u) + np.array(cb) * u
    rnd = random.Random(4)
    by0, by1, bx0, bx1 = 10, 46, 30, 290
    img[by0:by1, bx0:bx1] = (34, 86, 40)
    for _ in range(150):
        cx, cy = rnd.randrange(bx0 + 2, bx1 - 2), rnd.randrange(by0 + 2, by1 - 2)
        col = rnd.choice([(58, 130, 60), (74, 150, 70), (44, 108, 48)])
        for ang in range(-3, 4):
            for r in range(1, 6 - abs(ang) // 2):
                x = int(cx + np.sin(ang * 0.45) * r); y = int(cy - np.cos(ang * 0.45) * r)
                if by0 <= y < by1 and bx0 <= x < bx1: img[y, x] = col
    img[by0, bx0:bx1] = img[by1 - 1, bx0:bx1] = (10, 20, 12); img[by0:by1, bx0] = img[by0:by1, bx1 - 1] = (10, 20, 12)
    F = {'S': ['.###.', '#....', '.###.', '....#', '###..'], 'T': ['#####', '..#..', '..#..', '..#..', '..#..'], 'O': ['.###.', '#...#', '#...#', '#...#', '.###.'],
         'N': ['#...#', '##..#', '#.#.#', '#..##', '#...#'], 'E': ['####', '#...', '###.', '#...', '####'], 'P': ['###.', '#..#', '###.', '#...', '#...'],
         'A': ['.##.', '#..#', '####', '#..#', '#..#'], 'R': ['###.', '#..#', '###.', '#.#.', '#..#'], 'K': ['#..#', '#.#.', '##..', '#.#.', '#..#']}
    word, sc, gap = 'STONEPARK', 5, 3
    tw = sum(len(F[c][0]) * sc for c in word) + gap * (len(word) - 1); x0, y0 = (W - tw) // 2, 15
    def blit(off, colf):
        x = x0
        for c in word:
            for gy, row in enumerate(F[c]):
                for gx, p in enumerate(row):
                    if p == '#':
                        for dy in range(sc):
                            for dx in range(sc):
                                X, Y = x + gx * sc + dx + off, y0 + gy * sc + dy + off
                                if 0 <= X < W and 0 <= Y < H: img[Y, X] = colf(gy * sc + dy)
            x += len(F[c][0]) * sc + gap
    blit(2, lambda r: (8, 12, 10)); blit(0, lambda r: np.array((140, 220, 60)) * (1 - r / 25) + np.array((250, 150, 30)) * (r / 25))
    lineup = [(mecha_ch, 34, 64), (goalie_og, 96, 54), (idol_ruby, 172, 64), (knight_brew, 236, 64)]
    joints = []
    def put(x, y, col):
        if 0 <= x < W and 0 <= y < H: img[y, x] = hx(col)
    for fn, x, top in lineup:
        c, jp = fn()
        ys, xs = np.nonzero(c.a > 0)
        for yy, xx in zip(ys, xs):
            if 0 <= top + yy < H and 0 <= x + xx < W: img[top + yy, x + xx] = np.clip(c.rgb[yy, xx], 0, 255)
        if fn is knight_brew:   # red plume on the helmet
            for k in range(16):
                for w in range(4): put(x + 20 + k, top + 1 - int(5 * np.sin(k / 16 * np.pi)) + w - (k // 6), '#D7263D' if w < 3 else '#8A1220')
        if fn is goalie_og: og_x, og_top = x, top
        if fn is idol_ruby:     # floating notes
            for (nx, ny) in ((x + 46, top + 10), (x + 50, top + 22)):
                for k in range(5): put(nx, ny + k, '#FF4FA3')
                put(nx - 1, ny + 4, '#FF4FA3'); put(nx - 2, ny + 4, '#FF4FA3'); put(nx + 1, ny, '#FF4FA3')
        if jp: joints.append((x + jp[0], top + jp[1]))
        else: joints.append((x + 10, top + 22))
    def rect(x0, y0, x1, y1, col): img[y0:y1, x0:x1] = col
    for yb in (118, 128):
        rect(18, yb, 302, yb + 7, (128, 88, 52)); rect(18, yb, 302, yb + 1, (170, 126, 80)); rect(18, yb + 6, 302, yb + 7, (70, 46, 26))
    rect(18, 140, 302, 152, (120, 82, 48)); rect(18, 140, 302, 142, (176, 130, 84)); rect(18, 151, 302, 152, (64, 42, 24))
    for lx in (26, 156, 290): rect(lx, 112, lx + 6, 180, (84, 56, 32))
    img[152:180, :] *= 0.75
    # TRUE OG in front of the bench: stick, blocker and catcher
    for k in range(64):
        put(og_x + 60 + k // 8, og_top + 58 + k, '#C99A62'); put(og_x + 61 + k // 8, og_top + 58 + k, '#8A5E36')
    for k in range(14): put(og_x + 67 + k, og_top + 121, '#1A1C22'); put(og_x + 67 + k, og_top + 122, '#1A1C22'); put(og_x + 67 + k, og_top + 123, '#3A3F4C')
    for yy_ in range(og_top + 56, og_top + 70):
        for xx_ in range(og_x - 4, og_x + 9): put(xx_, yy_, '#F2F2EE' if (yy_ - og_top) % 5 else '#D7263D')
    for yy_ in range(og_top + 56, og_top + 69):
        for xx_ in range(og_x + 51, og_x + 64): put(xx_, yy_, '#7A4A2A' if (xx_ + yy_) % 4 else '#B5824F')
    for (sx, sy) in joints:
        for k in range(60):
            y = sy - 2 - k; x = int(sx + np.sin(k * 0.22 + sx) * (2 + k / 18)); r = 1 + k // 18
            if 48 < y < H and rnd.random() < 0.85:
                v = 236 - k; img[max(0, y - r // 2):y + r // 2 + 1, max(0, x - r // 2):x + r // 2 + 1] = (v, v, v - 4)
    yy, xx = np.mgrid[0:H, 0:W]
    img *= (1 - 0.32 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2))[..., None]
    img += np.random.RandomState(1).randint(-8, 8, (H, W, 1))
    art = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    art.resize((W * 3, H * 3), Image.NEAREST).save('ui/proto_big.png')
    th = art.resize((14, 10), Image.BOX)
    pol = Image.new('RGBA', (18, 20), (0, 0, 0, 0)); d = ImageDraw.Draw(pol)
    d.rectangle((0, 2, 17, 19), fill=(236, 232, 220, 255), outline=(20, 24, 26, 255)); pol.paste(th, (2, 4)); d.rectangle((6, 0, 11, 3), fill=(255, 242, 122, 210))
    pol.rotate(-6, resample=Image.NEAREST, expand=True).save('ui/proto_thumb.png')
if __name__ == '__main__':
    poster(); print('ok')
