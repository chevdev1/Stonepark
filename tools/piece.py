import math, random
import numpy as np
from PIL import Image, ImageDraw

G4 = {
 'S': ["####", "#...", "####", "...#", "####"],
 'T': ["####", ".##.", ".##.", ".##.", ".##."],
 'O': ["####", "#..#", "#..#", "#..#", "####"],
 'N': ["#..#", "##.#", "####", "#.##", "#..#"],
 'E': ["####", "#...", "###.", "#...", "####"],
 'P': ["####", "#..#", "####", "#...", "#..."],
 'A': ["####", "#..#", "####", "#..#", "#..#"],
 'R': ["####", "#..#", "###.", "#.#.", "#..#"],
 'K': ["#..#", "#.#.", "##..", "#.#.", "#..#"],
}
G5 = {
 'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
 'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
 'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
 'N': ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
 'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
 'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
 'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
 'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
 'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
 'X': ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
 'I': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
 'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
 'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
}

def hx(c):
    c = c.lstrip('#'); return np.array([int(c[i:i+2], 16) for i in (0, 2, 4)], float)

def dilate(m, r=1):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r + r:
                out |= shift(m, dx, dy)
    return out

def round_corners(m, it=2):
    for _ in range(it):
        p = np.pad(m, 1)
        n = sum(p[1 + dy:1 + dy + m.shape[0], 1 + dx:1 + dx + m.shape[1]].astype(int)
                for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy)
        m = m & (n >= 4)
    return m

def shift(m, dx, dy):
    o = np.zeros_like(m)
    H, W = m.shape
    ys = slice(max(0, dy), H + min(0, dy)); yd = slice(max(0, -dy), H + min(0, -dy))
    xs = slice(max(0, dx), W + min(0, dx)); xd = slice(max(0, -dx), W + min(0, -dx))
    o[ys, xs] = m[yd, xd]
    return o

def make_piece(word="STONEPARK", seed=3, cw=6, ch=6, k=1.0):
    rnd = random.Random(seed)
    PW, PH = 300, 96
    lab = np.zeros((PH, PW), np.int16)  # 0 = empty, i+1 = letter i
    tops, bots = {}, {}
    x0 = 16
    bounce = [2, -3, 1, -2, 3, -1, -3, 2, -2]
    scale = [1.12, 0.95, 1.0, 0.95, 1.0, 0.95, 1.0, 0.95, 1.1]
    shear = 0.2
    for i, chh in enumerate(word):
        g = G4[chh]
        sc = scale[i]
        colw = [round(v * sc * k) for v in (9, 5, 5, 9)]
        rowh = [round(v * sc * k) for v in (10, 5, 8, 5, 10)]
        cx = [2]; [cx.append(cx[-1] + w_) for w_ in colw]
        cy = [2]; [cy.append(cy[-1] + h_) for h_ in rowh]
        lw, lh = cx[-1] + 2, cy[-1] + 2
        loc = np.zeros((lh, lw), bool)
        for gy, row in enumerate(g):
            for gx, p in enumerate(row):
                if p == '#':
                    loc[cy[gy]:cy[gy + 1], cx[gx]:cx[gx + 1]] = True
        loc = round_corners(loc, 3)
        oy = PH - 18 - lh + bounce[i]
        for y in range(lh):
            for x in range(lw):
                if loc[y, x]:
                    X = x0 + x + round((lh - y) * shear); Y = oy + y
                    if 0 <= X < PW and 0 <= Y < PH:
                        lab[Y, X] = i + 1
        tops[i] = oy; bots[i] = oy + lh
        x0 += lw - 7
    # arrows (part of their letter's label)
    im = Image.fromarray(lab.astype(np.uint8))
    d = ImageDraw.Draw(im)
    def L0(i): return int(np.nonzero((lab == i + 1).any(0))[0].min())
    def L1(i): return int(np.nonzero((lab == i + 1).any(0))[0].max())
    # S: tail arrow sweeping left from the bottom
    sx0, sb = L0(0), bots[0]
    d.polygon([(sx0 + 14, sb - 9), (sx0 - 2, sb - 4), (sx0 - 1, sb - 9), (sx0 - 12, sb - 1), (sx0 - 1, sb + 6), (sx0, sb + 1), (sx0 + 12, sb - 2)], fill=1)
    # T: arrow up off the bar
    tx, tt = L1(1), tops[1]
    d.polygon([(tx - 10, tt + 4), (tx - 2, tt - 8), (tx - 6, tt - 8), (tx + 4, tt - 14), (tx + 5, tt - 3), (tx + 1, tt - 5), (tx - 4, tt + 6)], fill=2)
    # E: arrow off the middle bar
    ex, et = L1(4), (tops[4] + bots[4]) // 2
    d.polygon([(ex - 4, et - 4), (ex + 6, et - 4), (ex + 6, et - 8), (ex + 14, et), (ex + 6, et + 8), (ex + 6, et + 3), (ex - 4, et + 3)], fill=5)
    # K: long kick arrow to the lower right
    kx, kb = L1(8), bots[8]
    d.polygon([(kx - 10, kb - 12), (kx + 6, kb - 4), (kx + 7, kb - 9), (kx + 18, kb + 2), (kx + 4, kb + 6), (kx + 5, kb + 1), (kx - 12, kb - 5)], fill=9)
    lab = np.array(im).astype(np.int16)
    M = lab > 0
    # extrusion down-left
    sh = np.zeros_like(M)
    for k in range(1, 4):
        sh |= shift(M, -k, k)
    sh &= ~M
    from scipy import ndimage
    lbl, n = ndimage.label(~(M | sh))
    border = set(np.unique(np.concatenate([lbl[0], lbl[-1], lbl[:, 0], lbl[:, -1]])))
    enclosed = (~(M | sh)) & ~np.isin(lbl, list(border))
    sh = sh | enclosed
    body = M | sh
    outline = dilate(body, 1) & ~body
    rgb = np.zeros((PH, PW, 3)); a = np.zeros((PH, PW))
    ys, xs = np.mgrid[0:PH, 0:PW]
    chk = (xs + ys) % 2 == 0
    # shadow: dark checker
    rgb[sh & chk] = hx('#06060C'); rgb[sh & ~chk] = hx('#1C1C30'); a[sh] = 1
    rgb[outline] = hx('#F2DB9A'); a[outline] = 1
    # letters: two-tone checker fill split by height
    for i in range(len(word)):
        L = lab == i + 1
        t0, t1 = tops[i], bots[i]
        for y, x in zip(*np.nonzero(L)):
            split = t0 + (t1 - t0) * 0.48 + math.sin(x * 0.35) * 1.2
            if y < split:
                c = '#CFE3FF' if chk[y, x] else '#A8CBFF'
            else:
                c = '#78B1F4' if chk[y, x] else '#5793E8'
            rgb[y, x] = hx(c); a[y, x] = 1
    # green polka dots and diamonds in lower halves
    for i in range(len(word)):
        L = lab == i + 1
        pts = list(zip(*np.nonzero(L)))
        rnd.shuffle(pts)
        placed = 0
        for (y, x) in pts:
            if placed >= 2:
                break
            if y < tops[i] + (bots[i] - tops[i]) * 0.5:
                continue
            r = rnd.choice([1, 2, 2, 3])
            diamond = rnd.random() < 0.4
            ok = True
            cells = []
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    inside = (abs(dx) + abs(dy) <= r) if diamond else (dx * dx + dy * dy <= r * r + 1)
                    if inside:
                        yy, xx = y + dy, x + dx
                        if not (0 <= yy < PH and 0 <= xx < PW and L[yy, xx]):
                            ok = False
                        cells.append((yy, xx))
            if ok:
                for (yy, xx) in cells:
                    rgb[yy, xx] = hx('#2BE07A' if chk[yy, xx] else '#16B85A')
                placed += 1
    # black separators where letters touch each other or the shadow, white highlight on top edges
    out = rgb.copy()
    for y in range(PH):
        for x in range(PW):
            v = lab[y, x]
            if not v:
                continue
            sep = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < PW and 0 <= ny < PH:
                    nv = lab[ny, nx]
                    if (nv and nv != v and nv > v) or sh[ny, nx]:
                        sep = True
            if sep:
                out[y, x] = hx('#05060A')
            elif y > 0 and lab[y - 1, x] != v and not sh[y - 1, x]:
                out[y, x] = hx('#FFFFFF')
            elif x > 0 and lab[y, x - 1] != v and lab[y, x - 1] == 0 and not sh[y, x - 1]:
                out[y, x] = hx('#E9F3FF')
    rgb = out
    def P(x, y, c):
        if 0 <= x < PW and 0 <= y < PH:
            rgb[y, x] = hx(c); a[y, x] = 1
    # pink drip caps on top of some letters
    for i in (0, 3, 6, 8):
        L = lab == i + 1
        cols = np.nonzero(L.any(0))[0]
        cx = int(cols[len(cols) // 2 + (2 if i == 0 else -1)])
        cy = int(np.nonzero(L[:, cx])[0][0])
        for dy in range(-4, 3):
            for dx in range(-6, 7):
                if (dx / 6.2) ** 2 + ((dy + 1) / 3.4) ** 2 <= 1:
                    P(cx + dx, cy + dy, '#F6A5E1' if (dx + dy) % 2 else '#F08FD8')
        for dx in range(-4, 2):
            P(cx + dx, cy - 4, '#FFD9F3')
        P(cx - 6, cy - 1, '#05060A'); P(cx + 6, cy - 1, '#05060A')
        for dx in range(-5, 6):
            if (dx / 5.2) ** 2 + 0 <= 1:
                pass
        for (ddx, ln) in ((-3, 7 + i % 3), (1, 4 + i % 2), (4, 9 - i % 3)):
            for k in range(ln):
                P(cx + ddx, cy + 2 + k, '#F08FD8')
            P(cx + ddx, cy + 2 + ln, '#FFD9F3')
    # sparkle star on O
    L = lab == 3
    ys_, xs_ = np.nonzero(L)
    sx, sy = int(xs_.mean()) + 1, int(ys_.min()) + 9
    for k in range(-3, 4):
        P(sx + k, sy, '#05060A'); P(sx, sy + k, '#05060A')
    for k in (-1, 1):
        P(sx + k, sy + k, '#05060A'); P(sx + k, sy - k, '#05060A')
    P(sx, sy, '#FFFFFF')
    # black drips from the shadow
    for x in (L0(1) - 4, L0(3) + 2, L0(5) + 4, L0(7) + 2):
        col = np.nonzero(sh[:, x])[0]
        if len(col):
            yb = int(col.max())
            for k in range(1, 9 + x % 5):
                P(x, yb + k, '#05060A')
    # bubbles
    for (bx, by, br) in ((max(6, L0(0) - 12), tops[0] + 8, 4), (min(PW - 6, L1(8) + 10), tops[8] - 2, 3), (min(PW - 4, L1(8) + 14), tops[8] + 8, 2)):
        for dy in range(-br - 1, br + 2):
            for dx in range(-br - 1, br + 2):
                d2 = dx * dx + dy * dy
                if d2 <= (br + 1) ** 2:
                    P(bx + dx, by + dy, '#F2DB9A')
                if d2 <= br * br:
                    P(bx + dx, by + dy, '#A8CBFF' if (dx + dy) % 2 else '#CFE3FF')
        P(bx - 1, by - 1, '#FFFFFF')
    ys_, xs_ = np.nonzero(a)
    y0, y1, x0_, x1 = ys_.min(), ys_.max() + 1, xs_.min(), xs_.max() + 1
    return rgb[y0:y1, x0_:x1], a[y0:y1, x0_:x1]

if __name__ == '__main__':
    rgb, a = make_piece()
    H, W = a.shape
    bg = np.zeros((H + 20, W + 20, 3)); bg[:] = hx('#070820')
    for y in range(H):
        for x in range(W):
            if a[y, x]:
                bg[y + 10, x + 10] = rgb[y, x]
    Image.fromarray(bg.astype(np.uint8)).resize(((W + 20) * 6, (H + 20) * 6), Image.NEAREST).save('piece_preview.png')
