import math, random
import numpy as np
from PIL import Image
import chars, piece

W, H = 400, 225
N = 32
DELAY = 110
BEAT = 8
FLOOR = 196
OG = False      # TRUE OG in the scene (after unlock)
VIBE = None     # None | 'clan' | 'winter' | 'party'

def hx(c):
    c = c.lstrip('#'); return np.array([int(c[i:i+2], 16) for i in (0, 2, 4)], float)

def put(a, x, y, c, alpha=1.0):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H:
        col = hx(c) if isinstance(c, str) else c
        a[y, x] = a[y, x] * (1 - alpha) + col * alpha

def rect(a, x, y, w, h, c, alpha=1.0):
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w)), min(H, int(y + h))
    if x1 <= x0 or y1 <= y0:
        return
    col = hx(c) if isinstance(c, str) else c
    a[y0:y1, x0:x1] = a[y0:y1, x0:x1] * (1 - alpha) + col * alpha

YS, XS = np.mgrid[0:H, 0:W]
def glow(a, cx, cy, r, c, strength, sx=1.0, sy=1.0, bands=12):
    d = np.sqrt(((XS - cx) / sx) ** 2 + ((YS - cy) / sy) ** 2) / r
    f = np.clip(1 - d, 0, 1) ** 2 * strength
    f = np.floor(f * bands) / bands
    a += hx(c) * f[..., None]

def ellipse(a, cx, cy, rx, ry, c, alpha=1.0):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                put(a, x, y, c, alpha)

G5 = piece.G5
def text5(a, s, x, y, c, clip=None):
    for ch in s:
        if ch in G5:
            for gy, row in enumerate(G5[ch]):
                for gx, p in enumerate(row):
                    if p == '#':
                        xx = x + gx
                        if clip is None or clip[0] <= xx < clip[1]:
                            put(a, xx, y + gy, c)
        x += 6

def stair_xr(i):
    return 168 - 7 * i

# ------------------------------------------------------------------ static
def build_static():
    rnd = random.Random(7)
    a = np.zeros((H, W, 3))
    rect(a, 0, 0, W, H, '#0C1F25')
    for _ in range(4200):
        put(a, rnd.randrange(W), rnd.randrange(H), rnd.choice(['#0F252C', '#0A1A1F', '#10282F', '#0D2329']))
    # concrete panel seams + water stains
    for x in range(204, W, 52):
        rect(a, x, 66, 1, 130, '#0A191E')
    for (sx, sw) in ((228, 6), (300, 4), (352, 8)):
        for y in range(66, 120):
            if rnd.random() < 0.8:
                rect(a, sx + rnd.randint(-1, 1), y, sw - (y - 66) // 20, 1, '#0B1B20')
    keep = a[:, 196:].copy()
    # ---- city opening
    OX1, OY1 = 196, 58
    bands = ['#0A0A1E', '#0D0B23', '#120E2A', '#181131', '#211338', '#2C1540', '#3A1846', '#481A4A', '#521C4B', '#5A1E4B']
    for i, c in enumerate(bands):
        rect(a, 0, i * 6, OX1, 6, c)
    for y in range(0, OY1, 6):
        for x in range(0, OX1, 2):
            put(a, x + (y // 6) % 2, y, bands[min(len(bands) - 1, y // 6 + 1)])
    # moon
    ellipse(a, 150, 15, 8, 8, '#F4E9D6'); ellipse(a, 147, 13, 2, 2, '#DCCFB8'); ellipse(a, 153, 18, 1.5, 1.5, '#DCCFB8')
    glow(a, 150, 15, 22, '#3A2A3A', 0.5)
    rr = random.Random(3)
    x = 0
    while x < OX1:
        w = rr.randint(8, 16); h = rr.randint(14, 30)
        rect(a, x, OY1 - h, w, h, '#1C1638'); x += w
    x = -4
    while x < OX1:
        w = rr.randint(12, 24); h = rr.randint(18, 40)
        rect(a, x, OY1 - h, w, h, '#120F27')
        for wy in range(OY1 - h + 3, OY1 - 2, 3):
            for wx in range(x + 2, x + w - 2, 3):
                if rr.random() < 0.33:
                    put(a, wx, wy, rr.choice(['#FFD66B', '#FFB65C', '#5FE3F0', '#F27FC3']))
        x += w + rr.randint(0, 3)
    # billboard + neon signs
    rect(a, 96, 12, 34, 14, '#0B0A18'); rect(a, 97, 13, 32, 12, '#2A0F33')
    text5(a, "LOFI", 101, 15, '#FF7FC8')
    rect(a, 60, 8, 4, 22, '#FF3EA5'); rect(a, 61, 9, 2, 20, '#FFC2E3')
    rect(a, 170, 14, 4, 18, '#2EE6E6'); rect(a, 171, 15, 2, 16, '#C9FFFF')
    rect(a, 20, 22, 16, 4, '#7CFF6B'); rect(a, 21, 23, 14, 2, '#E3FFDD')
    # elevated rail
    rect(a, 0, 46, OX1, 2, '#0B0A18')
    for x in range(4, OX1, 24):
        rect(a, x, 48, 2, 10, '#0B0A18')
    a[:, 196:] = keep
    # ---- ceiling area right: pipes, LED board
    rect(a, OX1, 0, 4, 66, '#0A181D'); rect(a, OX1 + 4, 0, 1, 66, '#1D3B41')
    for (py, c1, c2) in ((5, '#23464C', '#4C8C8C'), (11, '#1C3A40', '#3D7276')):
        rect(a, OX1 + 5, py, W, 4, c1); rect(a, OX1 + 5, py, W, 1, c2)
        for x in range(OX1 + 14, W, 34):
            rect(a, x, py - 1, 2, 6, '#0A181D')
    rect(a, 392, 15, 4, FLOOR - 15, '#1C3A40'); rect(a, 392, 15, 1, FLOOR - 15, '#3D7276')
    # cables hanging
    for k in range(40):
        put(a, 206 + k, 18 + int(3 * math.sin(k / 40 * math.pi)), '#081418')
        put(a, 250 + k * 1.2, 17 + int(5 * math.sin(k / 40 * math.pi)), '#081418')
    # LED board
    rect(a, 214, 22, 104, 22, '#060B0D'); rect(a, 214, 22, 104, 1, '#1D3B41')
    rect(a, 216, 24, 100, 18, '#04130B')
    rect(a, 236, 18, 1, 4, '#0A181D'); rect(a, 296, 18, 1, 4, '#0A181D')
    # beam
    rect(a, 0, 58, W, 8, '#0A181D'); rect(a, 0, 58, OX1, 1, '#24474E'); rect(a, 0, 65, W, 1, '#07121A')
    # tube housings
    for tx in (232, 330):
        rect(a, tx, 66, 40, 2, '#0A181D')
    # EXIT sign
    rect(a, 2, 68, 28, 11, '#06100B'); rect(a, 3, 69, 26, 9, '#0C3A1F')
    text5(a, "EXIT", 25, 70, '#5CFF96') if False else None
    for i, ch in enumerate("EXIT"):
        pass
    # ---- stairs
    for i in range(24):
        ty = FLOOR - 6 * (i + 1); xr = stair_xr(i)
        if ty < 66 or xr <= 0:
            break
        rect(a, 0, ty, xr, 6, '#0E262C')
        rect(a, 0, ty, xr, 1, '#5AA99D'); rect(a, 0, ty + 1, xr, 1, '#1D4A50')
        rect(a, xr - 1, ty, 1, 6, '#08171B')
    for _ in range(700):
        x, y = rnd.randrange(0, 168), rnd.randrange(66, FLOOR)
        if a[y, x].sum() < 120:
            put(a, x, y, '#112D33')
    # handrail
    def rail_y(x): return int(160 - (172 - x) * 6 / 7)
    for x in range(6, 178):
        y = rail_y(x)
        if y > 0:
            rect(a, x, y, 1, 2, '#2E6E6A'); put(a, x, y, '#7CCBBE')
    for x in range(24, 176, 28):
        y = rail_y(x) + 2
        i = max(0, int((168 - x) / 7))
        sy = FLOOR - 6 * (i + 1)
        rect(a, x, y, 1, max(0, sy - y), '#1F4F50')
    # ---- wall detail: posters / flyers
    def poster(x, y, w, h, base, accent, torn=True):
        rect(a, x, y, w, h, base)
        rect(a, x + 2, y + 2, w - 4, h // 3, accent)
        for k in range(3):
            rect(a, x + 2, y + h // 3 + 4 + k * 3, w - 6 - k * 3, 1, '#8D96A0')
        if torn:
            for k in range(4):
                put(a, x + w - 1 - k, y + h - 1, '#0C1F25'); put(a, x + w - 1, y + h - 1 - k, '#0C1F25')
    poster(120, 150, 16, 22, '#2A2F3A', '#C7493F')
    poster(134, 158, 14, 18, '#E8E0CC', '#2D5BD6')
    poster(176, 140, 14, 20, '#E8E0CC', '#FF3EA5')
    rect(a, 124, 148, 3, 3, '#FFD23A'); rect(a, 182, 138, 3, 3, '#9AA6A6')
    # graffiti piece
    prgb, pa = piece.make_piece(k=0.82)
    ph, pw = pa.shape
    PX, PY = 150, 66
    for y in range(ph):
        for x in range(pw):
            if pa[y, x]:
                put(a, PX + x, PY + y, prgb[y, x])
    # small tags + stickers
    def scribble(x, y, w, c, seed):
        r = random.Random(seed); px, py = x, y
        for i in range(w):
            put(a, px, py, c); py += r.choice([-1, 0, 1]); py = max(y - 3, min(y + 3, py)); px += 1
    scribble(212, 152, 18, '#7CFF6B', 1); scribble(340, 104, 16, '#E9E2D0', 2)
    scribble(110, 120, 14, '#FF3EA5', 3); scribble(356, 150, 12, '#36BEE6', 4)
    scribble(196, 176, 10, '#FFD23A', 5); scribble(300, 160, 12, '#F4F1E8', 6)
    rect(a, 330, 140, 6, 4, '#FFD66B'); rect(a, 205, 132, 4, 6, '#E9E2D0'); rect(a, 288, 150, 5, 5, '#FF3EA5')
    # ---- vending machine
    vx, vy = 358, 120
    rect(a, vx - 1, vy - 1, 32, FLOOR - vy + 1, '#05090D')
    rect(a, vx, vy, 30, FLOOR - vy, '#C43B5A'); rect(a, vx, vy, 30, 2, '#E8698A')
    rect(a, vx + 3, vy + 5, 18, 50, '#0B1A20')
    rows = ['#2EE6E6', '#FFD23A', '#7CFF6B', '#FF7FC8', '#F4F1E8']
    for r_, c in enumerate(rows):
        for k in range(4):
            rect(a, vx + 5 + k * 4, vy + 8 + r_ * 9, 2, 5, c)
            put(a, vx + 5 + k * 4, vy + 8 + r_ * 9, '#FFFFFF')
        rect(a, vx + 4, vy + 14 + r_ * 9, 16, 1, '#3A5560')
    rect(a, vx + 23, vy + 8, 5, 8, '#0B1A20'); rect(a, vx + 24, vy + 9, 3, 2, '#5CFF96')
    for k in range(3):
        rect(a, vx + 23, vy + 20 + k * 4, 5, 2, '#F4F1E8')
    rect(a, vx + 4, vy + 60, 22, 8, '#0B1A20')
    text5(a, "", 0, 0, '#fff')
    # ---- things on the stairs
    def tread(i): return FLOOR - 6 * (i + 1), stair_xr(i)
    ty, xr = tread(4)   # record crate
    rect(a, 117, ty - 11, 18, 11, '#05090D'); rect(a, 118, ty - 10, 16, 10, '#7A5434')
    rect(a, 118, ty - 7, 16, 1, '#4A311C'); rect(a, 118, ty - 4, 16, 1, '#4A311C')
    for k, c in enumerate(['#FF3EA5', '#F4F1E8', '#2EE6E6', '#FFD23A', '#15181E', '#9B5CFF', '#7CFF6B']):
        rect(a, 119 + k * 2, ty - 15 + (k % 3), 2, 6 - (k % 3), c)
    ty, xr = tread(6)   # monstera in a pot
    rect(a, 113, ty - 8, 10, 8, '#05090D'); rect(a, 114, ty - 7, 8, 7, '#B5603A'); rect(a, 113, ty - 8, 10, 2, '#D37A50')
    for (lx, ly, rx_, ry_) in ((112, ty - 13, 4, 3), (122, ty - 14, 4, 3), (117, ty - 18, 3, 4), (110, ty - 18, 3, 2), (124, ty - 20, 3, 2)):
        ellipse(a, lx, ly, rx_ + 1, ry_ + 1, '#05090D'); ellipse(a, lx, ly, rx_, ry_, '#2F8A4E'); put(a, lx - 1, ly - 1, '#58B07A'); put(a, lx, ly, '#1E5E36')
    rect(a, 117, ty - 14, 1, 7, '#1E5E36')
    ty, xr = tread(8)   # skateboard
    rect(a, 92, ty - 3, 20, 2, '#05090D'); rect(a, 93, ty - 3, 18, 1, '#15181E'); rect(a, 93, ty - 2, 18, 1, '#E0464F')
    put(a, 92, ty - 4, '#05090D'); put(a, 111, ty - 4, '#05090D')
    for wx in (96, 107):
        rect(a, wx, ty - 1, 2, 1, '#F4F1E8')
    ty, xr = tread(9)   # blackbook + markers
    rect(a, 95, ty - 4, 10, 4, '#05090D'); rect(a, 96, ty - 3, 8, 3, '#1B1F27'); rect(a, 96, ty - 1, 8, 1, '#E9E2D0')
    for k, c in enumerate(['#FF3EA5', '#2EE6E6', '#FFD23A']):
        rect(a, 96 + k * 3, ty - 5, 2, 1, c)
    ty, xr = tread(14)  # pizza box
    rect(a, 51, ty - 5, 20, 5, '#05090D'); rect(a, 52, ty - 4, 18, 4, '#D9C49A'); rect(a, 52, ty - 4, 18, 1, '#EDE0BE')
    ellipse(a, 61, ty - 2, 2, 1, '#C7493F')
    ty, xr = tread(15)  # cassette + headphones
    rect(a, 54, ty - 4, 9, 4, '#05090D'); rect(a, 55, ty - 3, 7, 3, '#E9E2D0'); rect(a, 56, ty - 2, 5, 1, '#3A4250')
    put(a, 57, ty - 2, '#FF3EA5'); put(a, 59, ty - 2, '#FF3EA5')
    for k in range(7):
        put(a, 44 + k, ty - 3 - int(2 * math.sin(k / 6 * math.pi)), '#F4F1E8')
    rect(a, 43, ty - 3, 2, 3, '#FF7FC8'); rect(a, 50, ty - 3, 2, 3, '#FF7FC8')
    # ---- wall decor
    # polaroids
    for k, (px_, py_, c) in enumerate(((118, 104, '#FF7FC8'), (126, 106, '#2EE6E6'), (134, 103, '#FFD23A'))):
        rect(a, px_ - 1, py_ - 1, 9, 10, '#05090D'); rect(a, px_, py_, 7, 8, '#F4F1E8'); rect(a, px_ + 1, py_ + 1, 5, 5, c)
        put(a, px_ + 2, py_ + 3, '#1B1F27'); put(a, px_ + 4, py_ + 2, '#1B1F27')
        rect(a, px_ + 2, py_ - 2, 3, 1, '#E9E2D0')
    # ---- more cozy details
    # ivy hanging from the beam over the opening and down the frame
    rv = random.Random(21)
    for vx in range(4, 194, 9):
        ln = rv.randint(3, 11)
        for k in range(ln):
            xx = vx + int(math.sin(k * 0.8 + vx) * 1.2)
            put(a, xx, 66 + k, '#2F8A4E' if k % 3 else '#58B07A')
            if k % 3 == 1:
                put(a, xx + 1, 66 + k, '#1E5E36')
    for k in range(40):
        put(a, 197 + int(math.sin(k * 0.6) * 1.5), 20 + k, '#2F8A4E' if k % 2 else '#58B07A')
        if k % 4 == 0:
            put(a, 198 + int(math.sin(k * 0.6) * 1.5), 20 + k, '#7CCB8A')
    # hanging planters from the pipes
    for (hx_, ln) in ((206, 10), (384, 16)):
        rect(a, hx_, 15, 1, ln, '#081418')
        rect(a, hx_ - 4, 15 + ln, 9, 6, '#05090D'); rect(a, hx_ - 3, 16 + ln, 7, 4, '#E8E0CC'); rect(a, hx_ - 3, 16 + ln, 7, 1, '#FF7FC8')
        for v in range(4):
            vx_ = hx_ - 3 + v * 2
            for k in range(4 + (v * 3) % 7):
                put(a, vx_ + (k % 2), 21 + ln + k, '#2F8A4E' if k % 2 else '#58B07A')
        put(a, hx_ - 1, 14 + ln, '#58B07A'); put(a, hx_ + 1, 13 + ln, '#58B07A'); put(a, hx_, 13 + ln, '#2F8A4E')
    # sneakers tossed over a cable
    for k in range(70):
        put(a, 322 + k, 16 + int(6 * math.sin(k / 70 * math.pi)), '#081418')
    for (sx_, ln) in ((350, 7), (355, 9)):
        rect(a, sx_, 22, 1, ln, '#C9CED6')
        rect(a, sx_ - 2, 22 + ln, 5, 3, '#05090D'); rect(a, sx_ - 1, 22 + ln, 4, 2, '#F2F4F1'); put(a, sx_, 23 + ln, '#E0464F')
    # wall clock
    ellipse(a, 108, 64 + 40, 6, 6, '#05090D'); ellipse(a, 108, 104, 5, 5, '#E8E0CC'); ellipse(a, 108, 104, 4, 4, '#F4F1E8')
    rect(a, 108, 100, 1, 4, '#1B1F27'); rect(a, 108, 104, 3, 1, '#1B1F27'); put(a, 108, 104, '#E0464F')
    # moss on the lower stair edges
    for i in range(0, 12):
        ty_ = FLOOR - 6 * (i + 1); xr_ = stair_xr(i)
        for k in range(rv.randint(0, 3)):
            put(a, xr_ - 2 - rv.randint(0, 5), ty_, rv.choice(['#2F8A4E', '#58B07A']))
            put(a, xr_ - 2, ty_ + 1 + rv.randint(0, 3), '#1E5E36')
    # stickers on the vending machine
    for (sx_, sy_, c) in ((361, 182, '#FFD23A'), (366, 186, '#2EE6E6'), (380, 184, '#7CFF6B'), (375, 190, '#F4F1E8'), (384, 125, '#FF7FC8')):
        rect(a, sx_, sy_, 3, 3, c)
    # traffic cone by the trash
    for k in range(9):
        rect(a, 112 - k // 3, 187 + k, 1 + 2 * (k // 3), 1, '#FF7A2E')
    rect(a, 111, 190, 3, 1, '#F4F1E8'); rect(a, 108, 196, 9, 1, '#C4501E')
    # ---- floor
    rect(a, 0, FLOOR, W, H - FLOOR, '#081418')
    rect(a, 0, FLOOR, W, 1, '#1E3D43')
    for x in range(0, W, 18):
        rect(a, x, FLOOR + 1, 1, H - FLOOR, '#0B1C21')
    for y in (FLOOR + 9, FLOOR + 20):
        rect(a, 0, y, W, 1, '#0B1C21')
    # floor grate
    rect(a, 196, 216, 22, 6, '#05090D')
    for k in range(0, 22, 3):
        rect(a, 196 + k, 216, 1, 6, '#1E3D43')
    # trash bags + cans by the stairs
    ellipse(a, 18, 190, 10, 7, '#15181E'); ellipse(a, 16, 187, 4, 2, '#2A2F38')
    ellipse(a, 33, 192, 7, 5, '#1B1F27'); put(a, 33, 186, '#2A2F38')
    def can(x, y, c, lying=False):
        if lying:
            rect(a, x, y, 8, 4, '#05090D'); rect(a, x, y + 1, 7, 2, c); rect(a, x + 7, y + 1, 1, 2, '#9AA6A6'); rect(a, x + 2, y + 1, 3, 1, '#F4F1E8')
        else:
            rect(a, x - 1, y - 1, 6, 10, '#05090D'); rect(a, x, y, 4, 8, c)
            rect(a, x + 1, y - 2, 2, 2, '#9AA6A6'); rect(a, x, y + 3, 4, 1, '#F4F1E8'); put(a, x, y + 1, '#FFFFFF')
    can(376, 204, '#D9434E'); can(383, 212, '#2EC7D6', True); can(390, 205, '#E9E2D0')
    can(270, 216, '#FF3EA5', True); can(178, 210, '#7CFF6B')
    return a

# ------------------------------------------------------------------ dynamic
def dress(a, c, ox, oy, hat=True):
    if not VIBE:
        c.paste(a, ox, oy); return
    box = chars.apply_costume(c, VIBE)
    c.paste(a, ox, oy)
    if hat:
        chars.draw_hat(lambda x, y, col: put(a, x, y, col), ox, oy, box, VIBE)
def frame(static, F):
    f = F % N
    a = static.copy()
    rnd = random.Random(100)
    on_beat = f % BEAT < 2
    # city windows blink
    for (x, y, c, per, ph) in ((24, 34, '#FFD66B', 16, 3), (80, 30, '#5FE3F0', 8, 1), (140, 40, '#F27FC3', 16, 9), (110, 44, '#FFD66B', 32, 20), (186, 36, '#FFD66B', 16, 5)):
        if ((f + ph) // (per // 2)) % 2 == 0:
            put(a, x, y, c)
    if f in (13, 15, 27):
        rect(a, 170, 14, 4, 18, '#123A44')
    if f % 16 < 3:
        put(a, 40, 9, '#FF3B3B')
    # train (clipped to the opening)
    keep = a[:, 196:].copy()
    tx = -110 + f * 10
    for car in range(3):
        cx = tx + car * 34
        rect(a, cx, 38, 32, 1, '#3A4466')
        rect(a, cx, 39, 32, 6, '#1E2338')
        rect(a, cx, 44, 32, 1, '#0B0A18')
        for wx in range(cx + 2, cx + 30, 5):
            rect(a, wx, 40, 3, 2, '#FFE08A')
        rect(a, cx + 15, 40, 1, 4, '#0B0A18')
        rect(a, cx + 2, 43, 28, 1, '#FF3EA5' if car % 2 else '#2EE6E6')
        if car < 2:
            rect(a, cx + 32, 41, 2, 2, '#0B0A18')
    nose = tx + 3 * 34 - 2
    rect(a, nose, 39, 3, 6, '#1E2338'); rect(a, nose + 3, 40, 2, 4, '#1E2338'); rect(a, nose + 5, 41, 1, 2, '#1E2338')
    put(a, nose + 5, 41, '#FFF6C0'); put(a, tx, 42, '#FF3B3B')
    for k in range(12):
        rect(a, nose + 6 + k, 41 - k // 4, 1, 2 + k // 2, '#FFF1B0', 0.10)
    a[:, 196:] = keep
    # rain
    for i in range(70):
        rx = rnd.randrange(0, 240); ry0 = rnd.randrange(0, 64)
        y = (ry0 + f * 4) % 64; x = rx - y // 3
        for k in range(3):
            yy, xx = y - k, x + k // 3
            if 0 <= yy < 58 and 0 <= xx < 196:
                put(a, xx, yy, '#8FB4D8', 0.45)
    # LED marquee
    off = (f * 2) % 64
    for rep in range(-1, 3):
        cx = 218 + rep * 64 - off
        text5(a, "STONEPARK", cx, 29, '#5CFF96', clip=(217, 315))
    for xx in range(217, 315, 2):
        for yy in range(24, 42, 2):
            put(a, xx, yy, '#000000', 0.35)
    glow(a, 266, 34, 46, '#0F4A2A', 0.3, sx=1.6, sy=0.8)
    # EXIT sign
    for i, ch in enumerate("EXIT"):
        g = piece.G5[ch]
        for gy, row in enumerate(g):
            for gx, p in enumerate(row):
                if p == '#':
                    put(a, 5 + i * 6 + gx, 70 + gy, '#5CFF96')
    glow(a, 16, 74, 16, '#0F4A2A', 0.4)
    # fluorescent tubes
    t1 = f not in (20, 22)
    rect(a, 234, 68, 36, 1, '#E8FFF8' if t1 else '#3E5A57')
    rect(a, 332, 68, 36, 1, '#E8FFF8')
    if t1:
        glow(a, 252, 90, 90, '#2B6F6A', 0.26, sx=1.5)
    glow(a, 350, 90, 80, '#2B6F6A', 0.22, sx=1.5)
    # moths around tube 2
    for k in range(2):
        ang = f / N * 2 * math.pi * (1 + k) + k * 2
        put(a, 350 + math.cos(ang) * (8 + k * 4), 72 + math.sin(ang * 2) * 3, '#D8D2C0')
    # vending machine light spill + flicker
    glow(a, 373, 160, 50, '#5A1A30', 0.35, sx=1.0, sy=1.3)
    glow(a, 370, 150, 26, '#1F5560', 0.35)
    # dust motes in the light
    for i in range(14):
        ph = i * 2.3
        x = 230 + (i * 37) % 140 + math.sin(f / N * 2 * math.pi + ph) * 3
        y = 80 + (i * 23) % 60 + math.cos(f / N * 2 * math.pi + ph) * 2
        put(a, x, y, '#9FD6CE', 0.35)
    # steam from the grate
    for i in range(10):
        age = (f + i * 3) % N
        sx = 207 + math.sin(age * 0.3 + i) * 3 + (i % 3) - 1
        sy = 215 - age * 0.9
        put(a, sx, sy, '#9DB8B4', 0.35 * (1 - age / N))
    # water drip from the pipe into a puddle
    dy = 16 + (f * 7) % 224
    if dy < 207:
        put(a, 340, dy, '#9FD6E8', 0.8); put(a, 340, dy - 1, '#9FD6E8', 0.4)
    # puddles
    for (cx, cy, rx, ry) in ((248, 219, 30, 3), (340, 208, 9, 2)):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1:
                    put(a, x, y, '#0D2E37')
                    if (x * 7 + y * 3) % 11 == 0 and (x + y + f // 2) % 4 == 0:
                        put(a, x, y, ['#CFE3FF', '#5793E8', '#F6A5E1'][(x // 9) % 3], 0.6)
    rip = (f * 7) % 224
    if 200 <= rip + 16 <= 230:
        pass
    ring = ((f * 7 + 16) % 224) - 207
    if 0 <= ring < 6:
        for dx in range(-ring - 1, ring + 2):
            put(a, 340 + dx, 208, '#7FA9B0', 0.6)
    # cat on the stairs (tail swish + blink)
    cty = 120; cxr = 366   # the cat now sits on top of the vending machine
    cat = [".k...k..", ".kk.kk..", ".kkkkk..", ".kekek..", ".kkkkkk.", "kkkkkkkk", "kkkkkkkk"]
    blink = f % 32 in (20, 21)
    cells = {(xx, yy) for yy, row in enumerate(cat) for xx, ch in enumerate(row) if ch in 'ke'}
    for (xx, yy) in cells:  # teal rim so the black cat reads against the dark wall
        for dx, dy in ((1, 0), (-1, 0), (0, -1)):
            if (xx + dx, yy + dy) not in cells:
                put(a, cxr + xx + dx, cty - 7 + yy + dy, '#3E8A90')
    for yy, row in enumerate(cat):
        for xx, ch in enumerate(row):
            if ch == 'k':
                put(a, cxr + xx, cty - 7 + yy, '#0A0C10')
            elif ch == 'e':
                put(a, cxr + xx, cty - 7 + yy, '#0A0C10' if blink else '#FFD23A')
    sw = int(round(math.sin(f / N * 4 * math.pi) * 2))
    for k in range(5):
        put(a, cxr + 8 + (sw if k > 2 else 0) // 2, cty - 1 + k, '#0A0C10')
    # boombox on the first steps
    bx, by = 74, 181
    rect(a, bx - 1, by - 1, 32, 17, '#05090D')
    rect(a, bx, by, 30, 15, '#2A2F3A'); rect(a, bx, by, 30, 1, '#4A5260')
    rect(a, bx + 8, by - 4, 14, 1, '#05090D'); rect(a, bx + 8, by - 4, 1, 3, '#05090D'); rect(a, bx + 21, by - 4, 1, 3, '#05090D')
    rect(a, bx + 11, by + 2, 8, 4, '#0E1A1E'); rect(a, bx + 12, by + 3, 6, 2, '#47FF8A' if on_beat else '#1F7A45')
    for sxc in (bx + 5, bx + 25):
        r = 4 if on_beat else 3
        for ddx in range(-4, 5):
            for ddy in range(-4, 5):
                d2 = ddx * ddx + ddy * ddy
                if d2 <= r * r:
                    put(a, sxc + ddx, by + 9 + ddy, '#0E1215' if d2 > 2 else '#3A4250')
    if on_beat:
        glow(a, bx + 15, by + 8, 22, '#2B1640', 0.25)
    for i, c in enumerate(('#FF3EA5', '#2EE6E6', '#FFD66B')):
        age = (f + i * 11) % N
        nx = bx + 6 + i * 9 + math.sin(age * 0.3 + i) * 3
        ny = by - 6 - age * 0.9
        al = 1 - age / N
        if al > 0.1:
            for (ox, oy) in ((0, 0), (0, -1), (0, -2), (-1, 0), (1, -2)):
                put(a, nx + ox, ny + oy, c, al)
    # ---- dynamic decor
    def lglow(x, y, r, c, s):
        col = hx(c)
        for yy in range(int(y - r), int(y + r) + 1):
            for xx in range(int(x - r), int(x + r) + 1):
                if 0 <= xx < W and 0 <= yy < H:
                    d = math.hypot(xx - x, yy - y) / r
                    if d < 1:
                        a[yy, xx] += col * (math.floor((1 - d) ** 2 * s * 6) / 6)
    BULBS = ['#FFD66B', '#FF7FC8', '#7FE7F0', '#FFB65C']
    def string_lights(pts_from, pts_to, sag, idx0):
        (x0, y0), (x1, y1) = pts_from, pts_to
        n = int(abs(x1 - x0))
        for k in range(n + 1):
            t = k / max(1, n)
            x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t + sag * math.sin(math.pi * t)
            put(a, x, y, '#0A1418')
            if k % 5 == 2:
                idx = idx0 + k // 5
                on = (idx + f // 4) % 3 != 0
                c = BULBS[idx % 4]
                if on:
                    put(a, x, y + 1, c); put(a, x, y + 2, c); put(a, x, y + 1, '#FFFFFF', 0.4); lglow(x, y + 1.5, 6, c, 0.4)
                else:
                    put(a, x, y + 1, '#3A3530'); put(a, x, y + 2, '#3A3530')
        return idx0 + n // 5 + 1
    # along the handrail
    def rail_y(x): return int(160 - (172 - x) * 6 / 7) + 2
    idx = 0
    posts = [24, 52, 80, 108, 136, 164]
    for p0, p1 in zip(posts, posts[1:]):
        idx = string_lights((p0, rail_y(p0)), (p1, rail_y(p1)), 5, idx)
    # under the beam on the right
    hooks = list(range(202, 399, 39))
    for p0, p1 in zip(hooks, hooks[1:]):
        idx = string_lights((p0, 66), (p1, 66), 6, idx)
    # twinkling stars
    for (x, y, ph) in ((14, 4, 0), (44, 12, 5), (88, 6, 11), (126, 3, 17), (182, 8, 23), (70, 18, 29)):
        if (f + ph) % 16 < 10:
            put(a, x, y, '#F4F1E8')
        if (f + ph) % 16 < 3:
            put(a, x - 1, y, '#9FB4D8'); put(a, x + 1, y, '#9FB4D8'); put(a, x, y - 1, '#9FB4D8'); put(a, x, y + 1, '#9FB4D8')
    # neon heart above the vending machine
    heart = [".##...##.", "####.####", "#########", "#########", ".#######.", "..#####..", "...###...", "....#...."]
    heart_on = f not in (9, 10, 25)
    for yy, row in enumerate(heart):
        for xx, ch in enumerate(row):
            if ch == '#':
                edge = any(not (0 <= yy + dy < len(heart) and 0 <= xx + dx < 9 and heart[yy + dy][xx + dx] == '#') for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if edge:
                    put(a, 368 + xx, 104 + yy, '#FF3EA5' if heart_on else '#5A1A3A')
                elif heart_on:
                    put(a, 368 + xx, 104 + yy, '#FFC2E3', 0.25)
    if heart_on:
        lglow(372, 108, 14, '#5A1440', 0.6)
    # neon lightning bolt over the stairs
    bolt = [(122, 76), (118, 84), (123, 84), (116, 96), (120, 86), (115, 86), (119, 76)]
    bolt_on = f not in (4, 18)
    for (p, q) in zip(bolt, bolt[1:] + bolt[:1]):
        n = max(abs(q[0] - p[0]), abs(q[1] - p[1]))
        for k in range(n + 1):
            put(a, p[0] + (q[0] - p[0]) * k / max(1, n), p[1] + (q[1] - p[1]) * k / max(1, n), '#2EE6E6' if bolt_on else '#14444A')
    if bolt_on:
        lglow(119, 86, 14, '#0E4048', 0.6)
    # lantern on step 7
    lt = FLOOR - 6 * 8
    flick = 0.8 + 0.2 * math.sin(f * 1.7) + (0.15 if f % 5 == 0 else 0)
    rect(a, 107, lt - 10, 7, 10, '#05090D'); rect(a, 108, lt - 9, 5, 8, '#FFC86B' if flick > 0.85 else '#E8A24E')
    rect(a, 109, lt - 12, 3, 2, '#05090D'); rect(a, 108, lt - 6, 5, 1, '#2A2F38')
    lglow(110, lt - 5, 12, '#5A3A10', 0.6 * flick)
    # candles on step 16
    ct = FLOOR - 6 * 17
    for k, (cx_, hgt) in enumerate(((46, 4), (49, 6), (52, 3))):
        rect(a, cx_ - 1, ct - hgt - 1, 3, hgt + 1, '#05090D'); rect(a, cx_, ct - hgt, 1, hgt, '#F4EEDC')
        fl = (f + k * 3) % 6
        put(a, cx_, ct - hgt - 1, '#FFD66B'); put(a, cx_, ct - hgt - 2, '#FF9A3C' if fl < 4 else '#FFD66B')
        if fl < 2:
            put(a, cx_, ct - hgt - 3, '#FF9A3C', 0.6)
    lglow(49, ct - 6, 11, '#5A3A10', 0.55)
    # paper lanterns over the stairs
    for k, (lx, c1, c2) in enumerate(((42, '#E0464F', '#FF8A6A'), (132, '#FF9A3C', '#FFC27A'))):
        swing = int(round(math.sin(f / N * 2 * math.pi + k * 1.5) * 1.2))
        rect(a, lx, 66, 1, 6, '#081418')
        cx_ = lx + swing
        rect(a, cx_ - 4, 72, 9, 1, '#05090D')
        ellipse(a, cx_, 78, 5, 5.5, '#05090D'); ellipse(a, cx_, 78, 4, 4.5, c1)
        for yy in (75, 78, 81):
            rect(a, cx_ - 3, yy, 7, 1, c2)
        rect(a, cx_ - 2, 84, 5, 1, '#05090D'); rect(a, cx_, 85, 1, 3, c1)
        lglow(cx_, 78, 16, '#5A2010', 0.55)
    # CRT tv on the floor showing static
    tvx, tvy = 47, 167
    rect(a, 45, 181, 24, 15, '#05090D'); rect(a, 46, 182, 22, 14, '#2EC7D6'); rect(a, 46, 182, 22, 1, '#7FE7F0')
    for yy in range(185, 195, 3):
        for xx in range(48, 66, 4):
            rect(a, xx, yy, 2, 2, '#1A7F8A')
    rect(a, tvx - 1, tvy - 1, 22, 16, '#05090D'); rect(a, tvx, tvy, 20, 14, '#3A3530'); rect(a, tvx, tvy, 20, 1, '#5A5248')
    rn = random.Random(f)
    for yy in range(tvy + 2, tvy + 11):
        for xx in range(tvx + 2, tvx + 15):
            v = rn.random()
            put(a, xx, yy, '#D8F0EC' if v > 0.6 else ('#7FA9B0' if v > 0.3 else '#2B4A50'))
    if f % 16 < 8:
        rect(a, tvx + 2, tvy + 5 + (f % 4), 13, 1, '#F4F1E8', 0.6)
    rect(a, tvx + 16, tvy + 3, 2, 2, '#1B1F27'); rect(a, tvx + 16, tvy + 7, 2, 2, '#1B1F27')
    put(a, tvx + 17, tvy + 11, '#E0464F')
    rect(a, tvx + 5, tvy - 5, 1, 4, '#9AA6A6'); rect(a, tvx + 12, tvy - 6, 1, 5, '#9AA6A6')
    lglow(tvx + 8, tvy + 7, 18, '#1F4F55', 0.5)
    # a mouse runs across the floor
    mx_ = 420 - f * 15
    if -6 < mx_ < W:
        my_ = 223
        rect(a, mx_, my_ - 2, 4, 2, '#5A5A66'); put(a, mx_ - 1, my_ - 2, '#5A5A66'); put(a, mx_, my_ - 3, '#8A8A96')
        put(a, mx_ - 1, my_ - 2, '#FF9AC0'); rect(a, mx_ + 4, my_ - 1, 3, 1, '#8A6A6A')
        put(a, mx_ + (f % 2), my_, '#3A3A44'); put(a, mx_ + 2 + (f % 2), my_, '#3A3A44')
    # light rays through the opening onto the stairs
    sh = 0.5 + 0.5 * math.sin(f / N * 2 * math.pi)
    for (x0, w0, al) in ((20, 10, 0.10), (70, 14, 0.085), (130, 8, 0.07)):
        for y in range(66, FLOOR):
            t = (y - 66) / (FLOOR - 66)
            xs0 = int(x0 + t * 70); ww = int(w0 + t * 18)
            rect(a, xs0, y, ww, 1, '#B7A4E8', al * (0.7 + 0.3 * sh) * (1 - t * 0.6))
    # police drone over the city with a sweeping searchlight (clipped to the opening)
    keep = a[:, 196:].copy()
    dxp = 100 + 60 * math.sin(f / N * 2 * math.pi)
    dyp = 20 + 2 * math.sin(f / N * 4 * math.pi)
    ang = math.sin(f / N * 2 * math.pi + 1.2) * 0.5
    for k in range(1, 38):
        cx_ = dxp + math.sin(ang) * k; cy_ = dyp + 2 + k
        ww = k * 0.45
        for xx in range(int(cx_ - ww), int(cx_ + ww) + 1):
            if cy_ < 58:
                put(a, xx, cy_, '#E8F4FF', 0.10)
    rect(a, dxp - 4, dyp, 9, 2, '#2A2F3A'); rect(a, dxp - 6, dyp - 1, 3, 1, '#6B6488'); rect(a, dxp + 4, dyp - 1, 3, 1, '#6B6488')
    put(a, dxp - 3, dyp + 1, '#FF3B3B' if f % 4 < 2 else '#3D7BFF'); put(a, dxp + 3, dyp + 1, '#3D7BFF' if f % 4 < 2 else '#FF3B3B')
    # shooting star
    if 4 <= f <= 9:
        t = f - 4
        for k in range(6):
            put(a, 30 + t * 9 - k, 3 + t * 3 - k // 2, '#FFFFFF', 0.9 - k * 0.14)
    a[:, 196:] = keep
    # pigeon on the beam
    pg = [".kk.", "kwkk", ".kkkk", "..kk."]
    peck = (f // 4) % 4 == 1
    px_, py_ = 336, 53
    body = [(1, 1), (2, 1), (3, 1), (1, 2), (2, 2), (3, 2), (4, 2), (2, 3), (3, 3)]
    for (xx, yy) in body:
        put(a, px_ + xx, py_ + yy, '#7A8090')
    put(a, px_ + 4, py_ + 2, '#5A6070'); put(a, px_ + 2, py_ + 2, '#9AA0AE')
    hx0, hy0 = (px_, py_ + 1) if peck else (px_ + 0, py_ - 1)
    put(a, hx0, hy0, '#8A90A0'); put(a, hx0 + 1, hy0, '#8A90A0'); put(a, hx0, hy0, '#0A0C10') if False else None
    put(a, hx0 - 1, hy0 + (1 if peck else 0), '#E8A040'); put(a, hx0 + 1, hy0 + 1, '#3E8F6A')
    put(a, px_ + 2, py_ + 4, '#E8A040'); put(a, px_ + 3, py_ + 4, '#E8A040')
    # fireflies around the plant and the lantern
    for i in range(6):
        ph = i * 1.9
        fx2 = 104 + (i * 13) % 34 + math.sin(f / N * 2 * math.pi * (1 + i % 2) + ph) * 5
        fy2 = 120 + (i * 7) % 30 + math.cos(f / N * 2 * math.pi + ph) * 4
        if (f + i * 5) % 8 < 6:
            put(a, fx2, fy2, '#E8FF8A'); lglow(fx2, fy2, 4, '#3A4A10', 0.6)
    # vending machine + neon reflections on the wet floor
    for xx in range(358, 388):
        for yy in range(198, 222):
            if (xx + yy * 3 + f) % 7 == 0:
                put(a, xx, yy, ['#2EE6E6', '#FFD23A', '#FF7FC8', '#C43B5A'][(xx // 4) % 4], 0.22 * (1 - (yy - 198) / 24))
    # low haze drifting across the floor
    ph = f / N * 2 * math.pi
    for yy in range(176, 206):
        row = 0.06 * (1 - abs(yy - 191) / 15)
        wav = 0.5 + 0.5 * np.sin(np.arange(W) / 23.0 + ph + yy * 0.15)
        a[yy] += hx('#4A6A70')[None, :] * (row * wav)[:, None]
    # ---- SERGIO on the top of the stairs: sits, then gets up and does a backflip
    SX, SY = 51, 112          # sprite left, tread y (step 13)
    Fm = F % 64
    # 0-39 sit | 40 crouch | 41 arms up | 42-45 backflip | 46-47 land in a crouch | 48+ straight back to sitting
    if Fm < 40 or Fm >= 48:
        c = chars.sky_sit(nod=1 if f % 8 < 2 else 0); dress(a, c, SX, SY - 44)
    elif Fm in (40, 46, 47):
        c = chars.sky_stand(crouch=1); dress(a, c, SX, SY - 79)
    elif Fm == 41:
        c = chars.sky_stand(arms_up=True); dress(a, c, SX, SY - 85)
    else:
        k = Fm - 42
        _t = chars.sky_tuck()
        if VIBE: chars.apply_costume(_t, VIBE)
        tk = chars.rot(_t, -k)
        tt = (Fm - 41.5) / 4.0
        cy_ = SY - 30 - math.sin(math.pi * tt) * 24
        cx_ = SX + 24 + math.sin(math.pi * tt) * 3
        tk.paste(a, int(cx_ - 20), int(cy_ - 20))
        for q in range(8):
            ang = -k * math.pi / 2 - math.pi / 2 + q * 0.22
            put(a, cx_ + math.cos(ang) * 23, cy_ + math.sin(ang) * 23, '#F4F1E8', 0.7 - q * 0.08)
    if 46 <= Fm <= 48:
        tt = Fm - 46
        for q in range(5):
            put(a, SX + 12 - q * 2 - tt * 2, SY - 1 - (q % 2), '#9DB8B4', 0.6 - tt * 0.13)
            put(a, SX + 36 + q * 2 + tt * 2, SY - 1 - (q % 2), '#9DB8B4', 0.6 - tt * 0.13)
    # ---- characters, back to front
    hot = f % 16 < 5
    nod = 1 if on_beat else 0
    people = []
    people.append((206, 'deuce', 160))
    people.append((206, 'yuzu', 274))
    people.append((210, 'vex', 316))
    people.append((214, 'mika', 192))
    people.append((218, 'ruby', 234))
    people.append((222, 'brew', 116))
    if OG: people.append((224, 'og', 2))
    people.sort()
    for (feet, who, x) in people:
        ellipse(a, x + 23, feet, 15, 2.5, '#03080A', 0.6)
    tip = None; nozzle = None; flask = None
    blinks = {'vex': (21, 22), 'mika': (13, 14), 'ruby': (5, 6), 'brew': (27, 28)}
    for (feet, who, x) in people:
        chars.BLINK = (f % N) in blinks.get(who, ())
        if who == 'deuce':
            c = chars.deuce(nod=1 if (f + 4) % 8 < 2 else 0); dress(a, c, x, feet - 79)
        elif who == 'yuzu':
            c, nz = chars.yuzu(t=2 * math.pi * f / 16); dress(a, c, x, feet - 79); nozzle = (x + nz[0], feet - 79 + nz[1])
        elif who == 'vex':
            c, tp = chars.vex(nod=nod, hot=hot); dress(a, c, x, feet - 79); tip = (x + tp[0], feet - 79 + tp[1])
        elif who == 'mika':
            c = chars.mika(sip=(f % 32) in range(16, 24)); dress(a, c, x, feet - 81)
        elif who == 'og':
            c = chars.true_og(nod=1 if f % 8 < 2 else 0, bounce=1 if (f + 4) % 8 < 2 else 0); dress(a, c, x, feet - 91)
        elif who == 'brew':
            c, fl = chars.brew(f=f, nod=1 if (f + 2) % 8 < 2 else 0); dress(a, c, x, feet - 81); flask = (x + fl[0], feet - 81 + fl[1])
        elif who == 'ruby':
            c = chars.ruby(sway=1 if (f // 8) % 2 else 0); dress(a, c, x, feet - 81)
    chars.BLINK = False
    # potion glow + sparkles
    fx_, fy_ = flask
    pulse = 0.45 + 0.15 * math.sin(f / N * 4 * math.pi)
    glow(a, fx_, fy_, 30, '#4A1C8C', pulse * 1.5)
    for i in range(6):
        age = (f + i * 5) % N
        put(a, fx_ - 3 + (i * 5) % 8 + math.sin(age * 0.4 + i) * 2, fy_ - 14 - age * 0.6, '#C9A2FF', 0.9 * (1 - age / N))
    # ember + smoke
    tx_, ty_ = tip
    glow(a, tx_, ty_, 7 if hot else 4, '#FF6A1A', 0.35 if hot else 0.18)
    for i in range(16):
        age = (f + i * 2) % N
        sx = tx_ - age * 0.3 + math.sin(age * 0.28 + i * 0.7) * 2.5
        sy = ty_ - 1 - age * 1.15
        al = 0.85 * (1 - age / N) ** 0.8
        sz = 1 + age // 9
        for ddx in range(sz):
            for ddy in range(sz):
                put(a, sx + ddx, sy - ddy, '#B4CACA', al * (0.9 if ddx == ddy == 0 else 0.55))
    if 6 <= f % 16 <= 13:
        t = (f % 16) - 6
        for k in range(6):
            put(a, tx_ + 5 - t * 1.6 - k * 0.8, ty_ + 1 - t * 0.4 + math.sin(k + t) * 1.2, '#C4D6D6', 0.75 * (1 - t / 9))
    # spray mist
    nx_, ny_ = nozzle
    cols = ['#F6A5E1', '#CFE3FF', '#5793E8']
    for i in range(24):
        age = (f * 3 + i * 5) % 12
        ang = -math.pi / 2 + math.sin(i * 1.7) * 0.6
        rr = age * 0.9
        put(a, nx_ + math.cos(ang) * rr + math.sin(i) * 1.5, ny_ + math.sin(ang) * rr, cols[i % 3], 0.85 * (1 - age / 12))
    glow(a, nx_, ny_ - 5, 9, '#24305A', 0.4)
    if VIBE == 'party':
        rc = random.Random(77)
        for i in range(90):
            cx0 = rc.randrange(0, W); sp = rc.choice((2, 3, 4)); ph = rc.randrange(0, H)
            cy = (ph + f * sp) % (H + 20) - 10
            cx = cx0 + int(math.sin((f + i) * 0.4) * 3)
            col = rc.choice(('#FF3EA5', '#FFD23A', '#2EE6E6', '#5CFF96', '#F4F1E8'))
            put(a, cx, cy, col); put(a, cx + (f + i) % 2, cy + 1, col)
        for (lx, lc) in ((90, '#5A1440'), (210, '#0F4A48'), (330, '#5A4A10')):
            glow(a, lx + math.sin(f / 64 * 2 * math.pi + lx) * 40, 150, 40, lc, 0.35)
    # vignette
    v = 1 - 0.5 * np.clip(np.sqrt(((XS - 230) / 290) ** 2 + ((YS - 120) / 180) ** 2) - 0.35, 0, 1)
    v = np.floor(v * 12) / 12
    a = a * v[..., None]
    return np.clip(a, 0, 255).astype(np.uint8)

def export(prefix='stonepark', scale=3, frames_only=False):
    st = build_static()
    frames = [Image.fromarray(frame(st, f), 'RGB') for f in range(2 * N)]
    if frames_only:
        return frames
    strip = Image.new('RGB', (W, H * 8))
    for i, k in enumerate(range(0, 2 * N, 8)):
        strip.paste(frames[k], (0, i * H))
    pal = strip.quantize(255, method=Image.Quantize.MEDIANCUT)
    q = [fr.quantize(palette=pal, dither=Image.Dither.NONE).resize((W * scale, H * scale), Image.NEAREST) for fr in frames]
    q[0].save(prefix + '_scene.gif', save_all=True, append_images=q[1:], duration=DELAY, loop=0, disposal=1)
    frames[3].resize((W * scale, H * scale), Image.NEAREST).save(prefix + '_scene_still.png')
    return frames

if __name__ == '__main__':
    import sys
    st = build_static()
    if len(sys.argv) > 1:
        Image.fromarray(frame(st, int(sys.argv[1]))).resize((W * 3, H * 3), Image.NEAREST).save('preview2.png')
    else:
        export()
