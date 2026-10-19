"""SERGIO riding a rocket: 6-frame sprite sheet (transparent), 220x160 per frame."""
import sys, math, random
sys.path.insert(0, '.')
import numpy as np
from PIL import Image
import chars
from chars import hx
W, H, N = 220, 160, 6
A = math.radians(32)
C = (112, 96)
def frame(f):
    rgba = np.zeros((H, W, 4), np.float32)
    def put(x, y, c, a=1.0):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < H:
            col = hx(c); rgba[y, x, :3] = rgba[y, x, :3] * (1 - a) + col * a if rgba[y, x, 3] > 0 else col; rgba[y, x, 3] = max(rgba[y, x, 3], a)
    rnd = random.Random(f)
    # speed streaks (stars rushing past)
    for k in range(18):
        sx = (k * 37 + f * 14) % (W + 40) - 20; sy = (k * 53) % H
        for i in range(6 + k % 5): put(sx - i * math.cos(A), sy + i * math.sin(A), '#E8F1EE', 0.55 * (1 - i / 11))
    # smoke puffs behind
    for k in range(6):
        u = -66 - k * 14 - (f * 3) % 14; r = 4 + k * 1.6
        px = C[0] + u * math.cos(A); py = C[1] - u * math.sin(A)
        for yy in range(int(-r), int(r) + 1):
            for xx in range(int(-r), int(r) + 1):
                if xx * xx + yy * yy <= r * r and rnd.random() < 0.85: put(px + xx, py + yy + k, '#C9D3DC' if (xx + yy) % 3 else '#9AA6B2', 0.75 - k * 0.1)
    # rocket in its own coordinates: u along the axis (nose at +u), v across
    body = np.zeros((H, W), np.int8)   # 1 body, 2 nose/fins red, 3 window, 4 flame, 5 flame core, 6 stripe, 7 shade
    flame_len = 18 + [0, 5, 2, 7, 1, 4][f]
    for y in range(H):
        for x in range(W):
            dx, dy = x - C[0], y - C[1]
            u = dx * math.cos(A) - dy * math.sin(A); v = dx * math.sin(A) + dy * math.cos(A)
            hw = 12.0
            if u > 30: hw = 12.0 * max(0.0, (52 - u) / 22)
            if -48 <= u <= 52 and abs(v) <= hw:
                k = 1
                if u > 30: k = 2
                elif 8 <= u <= 13: k = 6
                elif v > 5: k = 7
                if (u - 18) ** 2 + v ** 2 <= 30: k = 3
                body[y, x] = k
            elif -48 <= u <= -32 and 12 < abs(v) <= 12 + (u + 48) * 0.7: body[y, x] = 2
            elif -48 - flame_len <= u < -48 and abs(v) <= 9 * (1 - (-48 - u) / flame_len) + 1:
                body[y, x] = 5 if abs(v) <= 4 * (1 - (-48 - u) / flame_len) + 0.5 else 4
    cols = {1: '#E9EEF0', 2: '#D7263D', 3: '#2EE6E6', 4: '#FF8A3D', 5: '#FFE36A', 6: '#D7263D', 7: '#AEB8C2'}
    ys, xs = np.nonzero(body)
    for y, x in zip(ys, xs):
        k = body[y, x]
        edge = any(not (0 <= y + dy < H and 0 <= x + dx < W) or body[y + dy, x + dx] == 0 for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge and k not in (4, 5): put(x, y, '#05090D')
        else: put(x, y, cols[k], 0.95 if k in (4, 5) else 1)
    # window glint
    wu, wv = 18, -2
    put(C[0] + wu * math.cos(A) + wv * math.sin(A), C[1] - wu * math.sin(A) + wv * math.cos(A), '#FFFFFF')
    # SERGIO sits on top, riding it
    s = chars.sky_sit(nod=1 if f % 3 == 0 else 0)
    u0, v0 = -10, -13
    px = C[0] + u0 * math.cos(A) + v0 * math.sin(A); py = C[1] - u0 * math.sin(A) + v0 * math.cos(A)
    ox, oy = int(px - 25), int(py - 44)
    m = s.a > 0
    sy_, sx_ = np.nonzero(m)
    for y, x in zip(sy_, sx_):
        Y, X = oy + y, ox + x
        if 0 <= Y < H and 0 <= X < W: rgba[Y, X, :3] = np.clip(s.rgb[y, x], 0, 255); rgba[Y, X, 3] = 1
    return Image.fromarray(np.clip(np.dstack([rgba[..., :3], rgba[..., 3] * 255]), 0, 255).astype(np.uint8), 'RGBA')
frames = [frame(f) for f in range(N)]
sheet = Image.new('RGBA', (W * N, H), (0, 0, 0, 0))
for i, fr in enumerate(frames): sheet.paste(fr, (i * W, 0), fr)
sheet.save('ui/rocket.png', optimize=True)
prev = Image.new('RGB', (W * 3, H), (10, 12, 30))
for i in range(3): prev.paste(frames[i], (i * W, 0), frames[i])
prev.resize((W * 6, H * 2), Image.NEAREST).save('rocket_check.png')
print('ok')
