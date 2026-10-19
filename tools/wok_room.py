"""WOK's lair: 400x225 pixel room, 8 animation frames."""
import sys, math, random
sys.path.insert(0, '.')
import numpy as np
from PIL import Image
from chars import hx
W, H = 400, 225
def blank(): return np.zeros((H, W, 3), np.float32)
def put(a, x, y, c, k=1.0):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H:
        a[y, x] = a[y, x] * (1 - k) + hx(c) * k
def rect(a, x0, y0, x1, y1, c, k=1.0):
    x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(W, int(x1)), min(H, int(y1))
    if x1 > x0 and y1 > y0: a[y0:y1, x0:x1] = a[y0:y1, x0:x1] * (1 - k) + hx(c) * k
def frame_rect(a, x0, y0, x1, y1, c):
    rect(a, x0, y0, x1, y0 + 1, c); rect(a, x0, y1 - 1, x1, y1, c); rect(a, x0, y0, x0 + 1, y1, c); rect(a, x1 - 1, y0, x1, y1, c)
def glow(a, cx, cy, r, c, k):
    col = hx(c)
    y0, y1, x0, x1 = max(0, int(cy - r)), min(H, int(cy + r)), max(0, int(cx - r)), min(W, int(cx + r))
    for y in range(y0, y1):
        for x in range(x0, x1):
            d = math.hypot(x - cx, y - cy) / r
            if d < 1: a[y, x] = a[y, x] + col * (1 - d) ** 2 * k
def disc(a, cx, cy, r, c):
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r: put(a, x, y, c)
def cable(a, x0, y0, x1, y1, sag, c):
    for i in range(80):
        t = i / 79
        x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        put(a, x, y, c)
# ------------------------------------------------------------------ static room
def base():
    a = blank()
    for y in range(H):   # walls: purple, darker to the top
        a[y, :] = hx('#1B1033') * (0.65 + 0.35 * y / H)
    rect(a, 0, 168, W, H, '#140B26')
    for y in range(168, H): a[y, :] = hx('#130A24') * (0.8 + 0.4 * (y - 168) / (H - 168))
    rect(a, 0, 167, W, 169, '#2C1A4D')
    for x in range(0, W, 16): rect(a, x, 168, x + 1, H, '#1A0F30')                   # floor seams
    rect(a, 0, 0, W, 8, '#120A22'); rect(a, 0, 8, W, 9, '#2C1A4D')                  # ceiling beam
    for x in range(10, W, 46): rect(a, x, 0, x + 4, 8, '#0C0618')
    # window with a neon city (right)
    rect(a, 300, 26, 392, 112, '#070514')
    rnd = random.Random(3)
    for bx in range(300, 392, 9):
        bh = rnd.randrange(30, 74); rect(a, bx, 112 - bh, bx + 8, 112, rnd.choice(['#140C2E', '#1A1040', '#0F0A26']))
        for wy in range(112 - bh + 3, 110, 4):
            for wx in range(bx + 1, bx + 7, 3):
                if rnd.random() < 0.45: put(a, wx, wy, rnd.choice(['#FF4FD8', '#2EE6E6', '#FFD23A', '#9B5CFF']))
    rect(a, 352, 64, 366, 72, '#FF2E9A', 0.9); rect(a, 312, 52, 322, 58, '#2EE6E6', 0.9)
    frame_rect(a, 298, 24, 394, 114, '#3A2468'); rect(a, 298, 68, 394, 70, '#3A2468'); rect(a, 345, 24, 347, 114, '#3A2468')
    for y in range(26, 50, 3): rect(a, 300, y, 392, y + 1, '#2A1A4A')                 # blinds, half down
    rect(a, 296, 112, 396, 116, '#2C1A4D')
    # cables from the ceiling
    for (x0, x1, s, c) in ((60, 150, 30, '#0B0716'), (90, 200, 44, '#2A1546'), (130, 250, 24, '#0B0716'), (220, 290, 30, '#3A1F5E'), (250, 120, 40, '#160C2A'), (170, 330, 22, '#0B0716')):
        cable(a, x0, 9, x1, 40, s, c)
    # big speakers
    for (x0, x1) in ((30, 92), (306, 366)):
        y0 = 72 if x0 < 100 else 118
        rect(a, x0, y0, x1, 196, '#0E0A16'); frame_rect(a, x0, y0, x1, 196, '#2C2240'); rect(a, x0 + 1, y0 + 1, x1 - 1, y0 + 2, '#3A2E54')
    # desk
    rect(a, 96, 140, 304, 147, '#2A1E3C'); rect(a, 96, 140, 304, 141, '#4A3A66'); rect(a, 96, 147, 304, 149, '#140E20')
    rect(a, 104, 149, 110, 196, '#1A1228'); rect(a, 290, 149, 296, 196, '#1A1228')
    # keyboard, pads, mug, cans
    rect(a, 150, 135, 206, 140, '#0F0C18'); 
    for x in range(152, 204, 3): put(a, x, 137, '#9B5CFF'); put(a, x + 1, 138, '#5A3A9A')
    rect(a, 214, 133, 238, 140, '#16121F')
    for i, c in enumerate(['#FF2E9A', '#2EE6E6', '#FFD23A', '#5CFF96', '#9B5CFF', '#FF8A3D', '#2EE6E6', '#FF2E9A']):
        rect(a, 216 + (i % 4) * 5 + 1, 134 + (i // 4) * 3, 216 + (i % 4) * 5 + 4, 136 + (i // 4) * 3, c)
    rect(a, 118, 131, 124, 140, '#D9D2E6'); rect(a, 124, 133, 126, 137, '#D9D2E6')   # mug
    for (cx, c) in ((128, '#D7263D'), (133, '#2EE6E6'), (276, '#5CFF96')): rect(a, cx, 132, cx + 4, 140, c); rect(a, cx, 132, cx + 4, 133, '#E9EEF0')
    # mini fridge (left bottom)
    rect(a, 4, 150, 30, 198, '#3A3550'); frame_rect(a, 4, 150, 30, 198, '#55506E'); rect(a, 7, 154, 27, 180, '#7FE8F2', 0.45)
    for y in (160, 168, 176): rect(a, 8, y, 26, y + 1, '#C9F6FA', 0.6)
    rect(a, 10, 156, 13, 160, '#D7263D'); rect(a, 16, 162, 19, 166, '#FFD23A'); rect(a, 21, 170, 24, 174, '#5CFF96')
    # PC tower with green LEDs (under desk right)
    rect(a, 254, 152, 286, 196, '#120E1C'); frame_rect(a, 254, 152, 286, 196, '#2C2240')
    for y in range(158, 192, 6): rect(a, 258, y, 282, y + 2, '#0A3A1E')
    # pizza boxes (floor right)
    for k in range(3):
        rect(a, 368 - k * 2, 204 - k * 5, 398 - k * 2, 209 - k * 5, '#C9A26A'); rect(a, 368 - k * 2, 204 - k * 5, 398 - k * 2, 205 - k * 5, '#E6C590')
    rect(a, 376, 190, 388, 192, '#D7263D')
    # floppy disks + cables on the floor
    rnd = random.Random(9)
    for _ in range(14):
        x, y = rnd.randrange(40, 380), rnd.randrange(200, 222); c = rnd.choice(['#6A4BC4', '#4A35A0', '#8A6BE0'])
        rect(a, x, y, x + 5, y + 4, c); rect(a, x + 1, y, x + 4, y + 1, '#D9D2E6')
    for (x0, y0, x1, y1, s) in ((110, 196, 250, 214, 8), (150, 150, 120, 205, 10), (260, 196, 360, 210, 6)):
        cable(a, x0, y0, x1, y1, s, '#0B0716')
    return a
# ------------------------------------------------------------------ animated parts
SCREENS = [  # x0, y0, x1, y1, kind
    (138, 92, 262, 132, 'main'), (112, 60, 150, 86, 'code'), (156, 52, 200, 84, 'daw'), (206, 50, 250, 82, 'pink'),
    (256, 58, 290, 86, 'code'), (120, 34, 154, 56, 'pink'), (196, 28, 232, 46, 'wave'), (238, 30, 270, 50, 'daw'),
]
def screens(a, f):
    rnd = random.Random(f * 7)
    for (x0, y0, x1, y1, kind) in SCREENS:
        rect(a, x0 - 2, y0 - 2, x1 + 2, y1 + 2, '#0A0712'); frame_rect(a, x0 - 2, y0 - 2, x1 + 2, y1 + 2, '#2C2240')
        w, hgt = x1 - x0, y1 - y0
        if kind == 'main':   # synthwave sunset with a grid
            for y in range(y0, y1):
                t = (y - y0) / hgt
                rect(a, x0, y, x1, y + 1, '#2A0F4A' if t < 0.5 else '#140829')
            for y in range(y0, y0 + hgt // 2):
                for x in range(x0, x1):
                    if (x - (x0 + w / 2)) ** 2 / 400 + (y - (y0 + hgt * 0.48)) ** 2 / 120 < 1 and (y % 3 != (f % 3)): put(a, x, y, '#FF4FD8')
            for k in range(0, w, 8): put(a, x0 + (k + f * 2) % w, y0 + hgt * 0.75, '#2EE6E6')
            rect(a, x0, int(y0 + hgt * 0.5), x1, int(y0 + hgt * 0.5) + 1, '#9B5CFF')
            for i in range(-6, 7):
                for t in range(0, 20):
                    gx, gy = x0 + w / 2 + i * (2 + t * 1.2), y0 + hgt * 0.5 + t
                    if x0 <= gx < x1 and y0 <= gy < y1: put(a, gx, gy, '#2EE6E6', 0.7)
            for k in range(4): rect(a, x0, y0 + hgt * 0.62 + k * k * 1.3 + (f % 2), x1, y0 + hgt * 0.62 + k * k * 1.3 + 1 + (f % 2), '#2EE6E6', 0.6)
        elif kind == 'code':
            rect(a, x0, y0, x1, y1, '#071016')
            for r in range(0, hgt, 3):
                ln = rnd.randrange(4, w - 4) if (r // 3 + f) % 5 else 0
                rect(a, x0 + 2 + (r // 3 % 3) * 3, y0 + r + 1, x0 + 2 + ln, y0 + r + 2, rnd.choice(['#5CFF96', '#2EE6E6', '#9B5CFF']))
        elif kind == 'daw':  # tracks + playhead
            rect(a, x0, y0, x1, y1, '#120A1E')
            for r in range(5):
                yy = y0 + 3 + r * (hgt - 4) // 5
                for x in range(x0 + 2, x1 - 2, 6):
                    if (x + r * 7) % 18 < 12: rect(a, x, yy, x + 5, yy + 3, ['#FF4FD8', '#2EE6E6', '#FFD23A', '#5CFF96', '#9B5CFF'][r])
            px_ = x0 + (f * 6) % w; rect(a, px_, y0, px_ + 1, y1, '#FFFFFF')
        elif kind == 'pink':
            for y in range(y0, y1): rect(a, x0, y, x1, y + 1, '#FF4FD8' if (y + f) % 6 < 3 else '#C23AB0')
            rect(a, x0 + 4, y0 + 4, x0 + 4 + (f * 4) % (w - 8), y0 + 6, '#FFFFFF')
        elif kind == 'wave':
            rect(a, x0, y0, x1, y1, '#0A0F1E')
            for x in range(x0, x1):
                y = y0 + hgt / 2 + math.sin((x + f * 4) / 3) * (hgt / 2 - 2) * math.sin((x - x0) / w * math.pi)
                put(a, x, y, '#2EE6E6'); put(a, x, y + 1, '#1A8C92')
        glow(a, (x0 + x1) / 2, (y0 + y1) / 2, max(w, hgt) * 0.9, '#7A3AD0', 0.10)
def speakers(a, f):
    beat = 1.0 if f % 4 == 0 else 0.4 if f % 4 == 1 else 0.0
    for (x0, x1, y0) in ((30, 92, 72), (306, 366, 118)):
        cx = (x0 + x1) / 2; ww = x1 - x0
        cones = [(y0 + 14, ww * 0.16), (y0 + 50 if y0 < 100 else y0 + 34, ww * 0.34), (y0 + 98 if y0 < 100 else y0 + 64, ww * 0.34)]
        for i, (cy, r) in enumerate(cones):
            rr = r + (beat * 1.5 if i else 0)
            disc(a, cx, cy, rr + 2, '#05030A'); disc(a, cx, cy, rr, '#1E1830'); disc(a, cx, cy, rr * 0.62, '#2C2444'); disc(a, cx, cy, rr * 0.2, '#0A0712')
            for k in range(24):
                t = k / 24 * math.tau; put(a, cx + math.cos(t) * (rr + 1), cy + math.sin(t) * (rr + 1), '#9B5CFF', 0.35 + 0.4 * beat)
        put(a, x0 + 5, 194, '#5CFF96' if f % 2 else '#1A6A3A')
        glow(a, cx, cones[1][0], ww * 0.7, '#9B5CFF', 0.05 + 0.1 * beat)
def leds(a, f):
    for y in range(158, 192, 6):
        on = (y // 6 + f) % 3 != 0
        rect(a, 258, y, 258 + (12 if on else 4), y + 2, '#5CFF96' if on else '#0A3A1E')
    glow(a, 270, 175, 26, '#2EB86A', 0.08)
    glow(a, 17, 168, 22, '#7FE8F2', 0.12)
    glow(a, 345, 70, 60, '#FF2E9A', 0.05)
def wok(a, f):
    """WOK in his chair, back to us, VR headset on, nodding to the beat."""
    nod = 1 if f % 4 in (0, 1) else 0
    # chair
    rect(a, 176, 116, 234, 182, '#14111C'); frame_rect(a, 176, 116, 234, 182, '#2A2438')
    rect(a, 172, 150, 180, 176, '#1C1828'); rect(a, 230, 150, 238, 176, '#1C1828')            # armrests
    for x in range(184, 228, 6): rect(a, x, 122, x + 3, 176, '#1E1A2A')                        # stitching
    rect(a, 200, 128, 210, 140, '#9B5CFF', 0.25)                                                # logo glow
    rect(a, 202, 182, 208, 198, '#0E0C14'); rect(a, 186, 198, 224, 201, '#0E0C14')             # base
    for x in (186, 205, 223): rect(a, x - 2, 201, x + 2, 204, '#2A2438')
    # hoodie shoulders sticking out from the chair
    rect(a, 168, 128, 178, 148, '#2B2F3A'); rect(a, 232, 128, 242, 148, '#2B2F3A')
    rect(a, 160, 136, 172, 144, '#2B2F3A'); rect(a, 238, 136, 250, 144, '#2B2F3A')            # arms to the keyboard
    rect(a, 156, 134, 162, 140, '#C98A64'); rect(a, 248, 134, 254, 140, '#C98A64')            # hands
    # head + VR headset (seen from behind)
    hy = 98 + nod
    for y in range(hy, hy + 22):
        for x in range(193, 217):
            if ((x - 205) / 12) ** 2 + ((y - hy - 11) / 11) ** 2 <= 1: put(a, x, y, '#1E140E')       # hair
    for x in range(193, 217): put(a, x, hy + 11, '#2A2E3A'); put(a, x, hy + 12, '#2A2E3A')        # side strap
    for x in range(198, 212): put(a, x, hy + 2, '#2A2E3A')                                     # top strap
    for y in range(hy + 2, hy + 12): put(a, 205, y, '#2A2E3A')
    rect(a, 200, hy + 14, 210, hy + 19, '#3A3F4C'); rect(a, 201, hy + 15, 209, hy + 18, '#9B5CFF', 0.8)   # battery pack glow
    rect(a, 189, hy + 8, 194, hy + 16, '#E9EEF0'); rect(a, 216, hy + 8, 221, hy + 16, '#E9EEF0')         # headset sides
    put(a, 191, hy + 9, '#2EE6E6'); put(a, 218, hy + 9, '#2EE6E6')
    glow(a, 205, hy + 8, 22, '#2EE6E6', 0.12)
    rect(a, 202, hy + 22, 208, hy + 26, '#C98A64')                                              # neck
def render():
    b = base(); frames = []
    for f in range(8):
        a = b.copy(); screens(a, f); speakers(a, f); leds(a, f); wok(a, f)
        yy, xx = np.mgrid[0:H, 0:W]
        a *= (1 - 0.35 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2))[..., None]
        frames.append(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    sheet = Image.new('RGB', (W * 8, H))
    for i, fr in enumerate(frames): sheet.paste(fr, (i * W, 0))
    sheet.quantize(255, method=Image.Quantize.MEDIANCUT).save('ui/wok_room.png', optimize=True)
    frames[0].resize((W * 3, H * 3), Image.NEAREST).save('wok_room_check.png')
    return frames
if __name__ == '__main__':
    render(); print('ok')
