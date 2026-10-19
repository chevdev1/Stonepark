import math, random
import numpy as np
from PIL import Image, ImageDraw

S = 64
N = 32
DELAY = 110

def hx(c):
    c = c.lstrip('#'); return np.array([int(c[i:i+2], 16) for i in (0, 2, 4)], float)

# region ids in draw order
BG, JACKET, TEE, NECK, HAIR, EAR, FACE, CAP, BRIM, PHONE, CUP = range(11)

def regions(nod=0):
    im = Image.new('L', (S, S), BG)
    d = ImageDraw.Draw(im)
    d.polygon([(4, 64), (8, 52), (16, 46), (28, 44), (44, 44), (54, 48), (60, 56), (63, 64)], fill=JACKET)
    d.polygon([(27, 45), (40, 45), (37, 64), (30, 64)], fill=TEE)
    d.polygon([(29, 36 + nod), (40, 36 + nod), (41, 47), (28, 47)], fill=NECK)
    y = nod
    d.polygon([(38, 20 + y), (47, 21 + y), (47, 33 + y), (42, 38 + y), (37, 31 + y)], fill=HAIR)
    d.polygon([(21, 20 + y), (17, 25 + y), (16, 27 + y), (13, 31 + y), (15, 32 + y), (16, 33 + y),
               (15, 35 + y), (17, 37 + y), (18, 40 + y), (22, 42 + y), (29, 43 + y), (35, 41 + y),
               (40, 36 + y), (43, 28 + y), (40, 19 + y), (28, 17 + y)], fill=FACE)
    d.ellipse([(36, 26 + y), (42, 34 + y)], fill=EAR)
    d.ellipse([(19, 7 + y), (48, 30 + y)], fill=CAP)
    d.rectangle([(19, 19 + y), (47, 23 + y)], fill=CAP)
    d.polygon([(9, 23 + y), (22, 20 + y), (31, 20 + y), (31, 24 + y), (20, 25 + y), (10, 26 + y)], fill=BRIM)
    # headphones resting on neck
    d.arc([(21, 40), (47, 52)], 0, 180, fill=PHONE, width=2)
    d.ellipse([(18, 41), (25, 50)], fill=CUP)
    d.ellipse([(43, 41), (50, 50)], fill=CUP)
    return np.array(im)

BASE = {JACKET: '#151A22', TEE: '#D3DDDA', NECK: '#B77C5E', HAIR: '#121418', EAR: '#C08263',
        FACE: '#C68A6A', CAP: '#26303D', BRIM: '#171D26', PHONE: '#2EC7D6', CUP: '#0F1519'}

def colorize(L, f):
    a = np.zeros((S, S, 3))
    rnd = random.Random(4)
    # background wall
    a[:] = hx('#0C2026')
    for _ in range(500):
        a[rnd.randrange(S), rnd.randrange(S)] = hx(rnd.choice(['#0F262D', '#0A1A1F', '#11303A']))
    # magenta neon tube on the right + tags
    for yy in range(4, 44):
        a[yy, 55] = hx('#FF3EA5'); a[yy, 56] = hx('#FFC2E3')
    a[3, 55:57] = hx('#3A4652'); a[44, 55:57] = hx('#3A4652')
    ys0, xs0 = np.mgrid[0:S, 0:S]
    gl = np.clip(1 - np.abs(xs0 - 55.5) / 12, 0, 1) ** 2 * (np.clip(1 - np.abs(ys0 - 24) / 30, 0, 1))
    a += hx('#5A1440') * (np.floor(gl * 8) / 8)[..., None]
    tx, ty = 46, 50
    for k in range(10):
        a[ty + int(2 * math.sin(k * 1.3)), tx + k] = hx('#7CFF6B')
    for k in range(7):
        a[8 + int(1.5 * math.sin(k)), 4 + k] = hx('#36BEE6')
    # neon edge light from left (green LED) + teal from right
    ys, xs = np.mgrid[0:S, 0:S]
    a += hx('#0F3D2A') * np.clip(1 - xs / 40, 0, 1)[..., None] * 0.5
    fg = L != BG
    for rid, c in BASE.items():
        a[L == rid] = hx(c)
    def same(x, y, rid):
        return 0 <= x < S and 0 <= y < S and L[y, x] == rid
    out = a.copy()
    for y in range(S):
        for x in range(S):
            r = L[y, x]
            if r == BG:
                continue
            # left rim light (green/teal neon)
            if r in (JACKET, CAP, HAIR, BRIM) and not same(x - 1, y, r) and not same(x - 2, y, r) is False:
                pass
            if r == JACKET:
                if not same(x - 2, y, r):
                    out[y, x] = hx('#2E6E73')
                elif not same(x + 3, y, r) and x > 40:
                    out[y, x] = hx('#0E1218')
            if r == CAP:
                if not same(x - 2, y, r) or not same(x, y - 2, r):
                    out[y, x] = hx('#41606E')
                if not same(x + 3, y, r):
                    out[y, x] = hx('#1A222C')
            if r == BRIM and not same(x, y - 1, r):
                out[y, x] = hx('#2F3D4C')
            if r in (FACE, NECK, EAR):
                if not same(x + 3, y, r) and r == FACE:
                    out[y, x] = hx('#8C5944')
                elif not same(x, y + 2, r) and r == FACE:
                    out[y, x] = hx('#9E6650')
                elif not same(x - 1, y, r) and r == FACE:
                    out[y, x] = hx('#E0A585')
                if r == NECK and y < 41:
                    out[y, x] = hx('#7E4F3D')
            if r == TEE and (x > 35 or y < 47):
                out[y, x] = hx('#93A6A6') if x > 35 else hx('#AFC0BE')
            if r == HAIR and not same(x - 1, y, r):
                out[y, x] = hx('#2A3640')
            if r == PHONE and y > 49:
                out[y, x] = hx('#1A7F8A')
            if r == CUP and (not same(x - 1, y, r) or not same(x, y - 1, r)):
                out[y, x] = hx('#2EC7D6')
    # under-brim shadow on face
    for y in range(S):
        for x in range(S):
            if L[y, x] == FACE and y > 0 and any(0 <= y - k and L[y - k, x] == BRIM for k in (1, 2)):
                out[y, x] = out[y, x] * 0.55
    # outlines: silhouette + region boundaries
    res = out.copy()
    order = {BG: 0, JACKET: 1, TEE: 2, NECK: 3, HAIR: 4, EAR: 5, FACE: 6, CAP: 7, BRIM: 8, PHONE: 9, CUP: 10}
    for y in range(S):
        for x in range(S):
            r = L[y, x]
            if r == BG:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < S and 0 <= ny < S):
                    continue
                nr = L[ny, nx]
                if nr == BG:
                    res[ny, nx] = hx('#060A0D')
                elif nr != r and order[nr] < order[r] and not (r == EAR and nr == FACE) and not (r == FACE and nr == NECK) and not (r == NECK and nr == TEE):
                    res[ny, nx] = hx('#090D11')
    return res

def details(a, L, f, nod, hot):
    def p(x, y, c, al=1.0):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < S and 0 <= y < S:
            a[y, x] = a[y, x] * (1 - al) + hx(c) * al
    y = nod
    # brow + eye
    for x in (19, 20, 21, 22): p(x, 27 + y, '#2A1A14')
    p(20, 29 + y, '#E6EEEE'); p(21, 29 + y, '#090D11'); p(22, 29 + y, '#090D11'); p(21, 30 + y, '#7A4A38')
    # nose shadow + nostril
    p(16, 32 + y, '#8C5944'); p(17, 32 + y, '#8C5944')
    # lips
    for x in (16, 17, 18): p(x, 35 + y, '#7E4236')
    p(18, 36 + y, '#A5644E')
    # cheek line / jaw
    # ear detail
    p(38, 30 + y, '#8C5944'); p(39, 31 + y, '#8C5944'); p(38, 32 + y, '#8C5944')
    # cap logo + button
    for (x, yy) in ((34, 13), (35, 13), (34, 14), (35, 14), (36, 14)): p(x, yy + y, '#D9434E')
    p(32, 8 + y, '#41606E'); p(33, 8 + y, '#41606E')
    # hair sideburn
    p(36, 27 + y, '#121418'); p(36, 28 + y, '#121418'); p(37, 33 + y, '#121418')
    # chain
    for t in range(13):
        ang = math.pi * t / 12
        cx = 33.5 + math.cos(ang) * 6
        cy = 47 + math.sin(ang) * 6
        p(cx, cy, '#E2BC55' if t % 2 == 0 else '#A6852E')
    p(33, 54, '#E2BC55'); p(34, 54, '#E2BC55'); p(33, 55, '#A6852E'); p(34, 55, '#E2BC55')
    # jacket zipper + folds
    for yy in range(48, 64): p(26, yy, '#0B0F14'); p(41, yy, '#0B0F14')
    for yy in range(52, 64, 3): p(25, yy, '#3A4652')
    for k in range(6): p(14 + k, 56 + k, '#0E1218'); p(50 - k, 54 + k, '#0E1218')
    # tee print
    for (x, yy) in ((31, 58), (32, 58), (33, 58), (34, 58), (31, 59), (34, 59), (31, 60), (32, 60), (33, 60), (34, 60)):
        p(x, yy, '#D9434E')
    # cigarette
    my = 35 + y
    for x in range(6, 16): p(x, my - (1 if x < 9 else 0), '#ECEAE2')
    for x in range(13, 16): p(x, my, '#D6A15C')
    tip = 5
    p(tip, my - 1, '#FFE2A8' if hot else '#FF7A2E')
    p(tip, my - 2, '#5A5A5A'); p(tip + 1, my - 2, '#7A7A7A')
    return my, tip

def frame(f):
    beat = f % 8 < 2
    nod = 1 if beat else 0
    hot = f % 16 < 5
    L = regions(nod)
    a = colorize(L, f)
    my, tip = details(a, L, f, nod, hot)
    # ember glow
    ys, xs = np.mgrid[0:S, 0:S]
    r = 9 if hot else 5
    g = np.clip(1 - np.sqrt((xs - tip) ** 2 + (ys - my + 1) ** 2) / r, 0, 1) ** 2
    a += hx('#FF6A1A') * (np.floor(g * 6) / 6 * (0.45 if hot else 0.2))[..., None]
    # smoke
    def p(x, y, c, al):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < S and 0 <= y < S:
            a[y, x] = a[y, x] * (1 - al) + hx(c) * al
    for i in range(18):
        age = (f + i * 2) % N
        sx = tip - age * 0.25 + math.sin(age * 0.3 + i * 0.8) * 2.5
        sy = my - 3 - age * 1.0
        al = 0.8 * (1 - age / N)
        sz = 1 + age // 8
        for dx in range(sz):
            for dy in range(sz):
                p(sx + dx, sy - dy, '#B4CACA', al * (0.9 if dx == dy == 0 else 0.5))
    if 6 <= f % 16 <= 13:
        t = (f % 16) - 6
        for k in range(7):
            p(14 - t * 1.4 - k * 0.7, my + 1 - t * 0.5 + math.sin(k + t) * 1.3, '#C4D6D6', 0.7 * (1 - t / 9))
    # LED flicker on background left
    if f not in (13, 27):
        a[:, :3] = a[:, :3] * 0.85 + hx('#1F7A45') * 0.15
    # vignette
    v = 1 - 0.45 * np.clip(np.sqrt(((xs - 32) / 40) ** 2 + ((ys - 30) / 40) ** 2) - 0.45, 0, 1)
    a *= (np.floor(v * 10) / 10)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGB')

if __name__ == '__main__':
    import sys
    frames = [frame(f) for f in range(N)]
    frames[3].resize((S * 12, S * 12), Image.NEAREST).save('avatar_preview.png')
    if len(sys.argv) > 1:
        pal = frames[0].quantize(255, method=Image.Quantize.MEDIANCUT)
        q = [fr.quantize(palette=pal, dither=Image.Dither.NONE).resize((S * 12, S * 12), Image.NEAREST) for fr in frames]
        q[0].save('stonepark_avatar.gif', save_all=True, append_images=q[1:], duration=DELAY, loop=0, disposal=1)
        frames[3].resize((S * 12, S * 12), Image.NEAREST).save('stonepark_avatar.png')
