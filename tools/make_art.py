"""
STONEPARK — regenerate all pixel art straight into web/assets/img.

    cd tools
    python make_art.py            # everything
    python make_art.py scene      # only the animated scene (atlas + still)
    python make_art.py portraits  # dialog portraits, hover outlines, stoned frames, crew cards
    python make_art.py johnny     # the dog

Characters are defined in chars.py, the scene in scene2.py, the wildstyle piece in piece.py.
Change a color or a shape there, run this script, refresh the page.
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, '..', 'web', 'assets', 'img')
UI = os.path.join(OUT, 'ui')
CREW = os.path.join(OUT, 'crew')
for d in (OUT, UI, CREW):
    os.makedirs(d, exist_ok=True)

import chars  # noqa: E402


def to_rgba(c):
    rgba = np.zeros((c.h, c.w, 4), np.uint8)
    rgba[..., :3] = np.clip(c.rgb, 0, 255).astype(np.uint8)
    rgba[..., 3] = (c.a > 0) * 255
    return rgba


def make_char(name, blink=False, scene_pose=False):
    """Front-facing sprite for portraits (scene_pose=True gives the pose used in the hero scene)."""
    chars.BLINK = blink
    try:
        if name == 'vex':
            return chars.vex()[0]
        if name == 'brew':
            return chars.brew()[0]
        if name == 'yuzu':
            return chars.yuzu(t=0.0)[0] if scene_pose else chars.yuzu_front()
        if name == 'sergio':
            return chars.sky_sit() if scene_pose else chars.sky_stand()
        return getattr(chars, name)()
    finally:
        chars.BLINK = False


NAMES = ['vex', 'ruby', 'mika', 'deuce', 'brew', 'yuzu', 'sergio']
ROWS = {'vex': 31, 'ruby': 29, 'mika': 29, 'deuce': 28, 'brew': 30, 'yuzu': 29, 'sergio': 29}
MOUTH = {'vex': [(18, 22), (19, 22)], 'ruby': [(23, 22), (24, 22)], 'mika': [(23, 22), (24, 22)], 'deuce': [(22, 22), (24, 22)],
         'brew': [(23, 23), (24, 23), (25, 23)], 'yuzu': [(23, 22), (24, 22)], 'sergio': [(22, 22), (23, 22), (24, 22)]}
EYES = {'vex': [(14, 15, 3), (21, 15, 3)], 'ruby': [(17, 14, 3), (27, 14, 3)], 'mika': [(17, 14, 4), (27, 14, 4)], 'deuce': [],
        'brew': [], 'yuzu': [(17, 14, 3), (27, 14, 3)], 'sergio': [(17, 14, 3), (26, 14, 3)]}
LIPS = {'vex': None, 'ruby': (25, 21), 'mika': (25, 21), 'deuce': (26, 21), 'brew': (26, 22), 'yuzu': (25, 21), 'sergio': (25, 21)}


def put(c, x, y, col):
    if 0 <= x < c.w and 0 <= y < c.h:
        c.rgb[y, x] = chars.hx(col)
        c.a[y, x] = 1


def save_square(frames, name, rows, prefix, extra_right=2):
    a0 = to_rgba(frames[0])[:rows]
    ys, xs = np.nonzero(a0[..., 3])
    x0, x1 = max(0, xs.min() - 1), min(frames[0].w, xs.max() + extra_right)
    for k, c in enumerate(frames):
        crop = to_rgba(c)[:rows, x0:x1]
        w = crop.shape[1]
        side = max(w, rows)
        sq = np.zeros((side, side, 4), np.uint8)
        sq[side - rows:, (side - w) // 2:(side - w) // 2 + w] = crop
        Image.fromarray(sq, 'RGBA').resize((side * 4, side * 4), Image.NEAREST).save(os.path.join(UI, f'{prefix}_{name}_{k}.png'))


def portraits():
    for n in NAMES:
        # talking portraits: 0 = idle, 1 = mouth open, 2 = blink
        base, talk, blink = make_char(n), make_char(n), make_char(n, blink=True)
        for (x, y) in MOUTH[n]:
            put(talk, x, y, '#3A1418')
        save_square([base, talk, blink], n, ROWS[n], 'p')
        Image.open(os.path.join(UI, f'p_{n}_0.png')).save(os.path.join(UI, f'p_{n}.png'))
        # stoned portraits (smoke break): heavy red eyes + joint
        frames = []
        for k in range(3):
            c = make_char(n, blink=True)
            for (x, y, tall) in EYES[n]:
                for dx in range(3):
                    put(c, x + dx, y + tall, '#E58A8A')
                put(c, x + 1, y + tall - 2, '#C2505A')
            if n == 'brew':
                for (lx, ly) in ((16, 15), (28, 15)):
                    for dx in range(5):
                        put(c, lx + dx, ly, '#E9AE8C'); put(c, lx + dx, ly + 1, '#120C14')
                    for dx in range(1, 4):
                        put(c, lx + dx, ly + 2, '#E58A8A')
            if n == 'deuce':
                for dx in range(14, 33):
                    put(c, dx, 12, '#73452F')
            if k == 1:
                for (x, y) in MOUTH[n]:
                    put(c, x, y, '#3A1418')
            if LIPS[n]:
                x, y = LIPS[n]
                for dx in range(4):
                    put(c, x + dx, y, '#F4EEDC')
                put(c, x + 3, y, '#D9A35F'); put(c, x + 4, y, '#FF7A2E' if k != 2 else '#FFD08A')
                if k == 2:
                    put(c, x + 5, y - 1, '#C9D6D6'); put(c, x + 6, y - 2, '#C9D6D6'); put(c, x + 5, y - 3, '#B4C4C4')
            frames.append(c)
        save_square(frames, n, ROWS[n], 's', extra_right=4)
        # crew card portrait (full body, transparent)
        card = make_char(n)
        Image.fromarray(to_rgba(card), 'RGBA').resize((card.w * 5, card.h * 5), Image.NEAREST).save(os.path.join(CREW, f'crew_{n}.png'))
        # hover outline matching the pose in the hero scene
        a = to_rgba(make_char(n, scene_pose=True))[..., 3] > 0
        p = np.pad(a, 2)
        dil = np.zeros_like(p)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                dil |= np.roll(np.roll(p, dy, 0), dx, 1)
        ring = dil & ~p
        out = np.zeros(p.shape + (4,), np.uint8)
        out[ring] = (255, 242, 122, 255)
        Image.fromarray(out[1:-1, 1:-1], 'RGBA').save(os.path.join(UI, f'o_{n}.png'))
    print('portraits, stoned frames, crew cards, outlines -> web/assets/img')


def scene():
    import scene2
    st = scene2.build_static()
    frames = [Image.fromarray(scene2.frame(st, f), 'RGB') for f in range(64)]
    strip = Image.new('RGB', (400, 225 * 8))
    for i, k in enumerate(range(0, 64, 8)):
        strip.paste(frames[k], (0, i * 225))
    pal = strip.quantize(255, method=Image.Quantize.MEDIANCUT)
    sheet = Image.new('RGB', (3200, 1800))
    for i, fr in enumerate(frames):
        sheet.paste(fr, ((i % 8) * 400, (i // 8) * 225))
    sheet.quantize(palette=pal, dither=Image.Dither.NONE).save(os.path.join(OUT, 'scene_sheet.png'), optimize=True)
    frames[3].resize((1200, 675), Image.NEAREST).save(os.path.join(OUT, 'scene_still.png'))
    print('scene atlas (64 frames, 8x8 grid of 400x225) + still -> web/assets/img')


def johnny():
    cwd = os.getcwd()
    os.makedirs(os.path.join(HERE, 'ui'), exist_ok=True)
    os.chdir(HERE)
    try:
        import johnny as j  # noqa: F401  (the module renders on import into tools/ui)
    finally:
        os.chdir(cwd)
    for f in os.listdir(os.path.join(HERE, 'ui')):
        if f.startswith(('j_', 'p_johnny')) and 'check' not in f:
            Image.open(os.path.join(HERE, 'ui', f)).save(os.path.join(UI, f))
    print('johnny frames -> web/assets/img/ui')


if __name__ == '__main__':
    what = sys.argv[1:] or ['portraits', 'johnny', 'scene']
    for w in what:
        {'portraits': portraits, 'scene': scene, 'johnny': johnny}[w]()
