import numpy as np
from PIL import Image
import chars
from chars import Char, hx
R = {
    'tail': dict(base='#F4F4F2', shade='#C9CED6'),
    'leg': dict(base='#E9EBEE', shade='#B8BEC6'),
    'body': dict(base='#F7F7F5', shade='#CDD2D9', light='#FFFFFF'),
    'head': dict(base='#F7F7F5', shade='#CDD2D9', light='#FFFFFF'),
    'snout': dict(base='#FFFFFF', shade='#D6DAE0'),
    'ear': dict(base='#BCC3CC', shade='#9AA2AD'),
    'collar': dict(base='#E0464F'),
}
def dog(pose='stand', step=0, wag=0, happy=False):
    c = Char(26, 20, R); S = []; det = []
    if pose == 'sit':
        S += [('poly', [(4, 9 + wag), (2, 4 + wag * 2), (4, 3 + wag * 2), (6, 9)], 'tail'),
              ('ell', (5, 7, 15, 17), 'body'), ('ell', (4, 13, 11, 18), 'leg'),
              ('rect', (12, 11, 14, 18), 'leg'), ('rect', (15, 11, 17, 18), 'leg')]
        hy = -2
    elif pose == 'jump':
        S += [('poly', [(3, 7), (0, 2), (2, 1), (5, 6)], 'tail'),
              ('ell', (3, 6, 18, 13), 'body'),
              ('poly', [(4, 11), (7, 11), (3, 17), (1, 16)], 'leg'), ('poly', [(15, 10), (18, 10), (22, 15), (20, 16)], 'leg')]
        hy = -1
    else:
        a, b = (1, -1) if step else (-1, 1)
        S += [('poly', [(4, 9), (2 - wag, 3), (4 - wag, 2), (6, 8)], 'tail'),
              ('ell', (3, 7, 18, 14), 'body'),
              ('rect', (5 + a, 12, 7 + a, 18), 'leg'), ('rect', (8 - a, 12, 10 - a, 18), 'leg'),
              ('rect', (13 + b, 12, 15 + b, 18), 'leg'), ('rect', (16 - b, 12, 18 - b, 18), 'leg')]
        hy = 0
    S += [('ell', (13, 1 + hy, 23, 11 + hy), 'head'), ('ell', (19, 5 + hy, 25, 11 + hy), 'snout'),
          ('ell', (13, 2 + hy, 18, 10 + hy), 'ear'), ('rect', (15, 10 + hy, 19, 11 + hy), 'collar')]
    det += [(24, 7 + hy, '#0A0C10'), (25, 7 + hy, '#0A0C10'), (24, 8 + hy, '#0A0C10')]
    if happy:
        det += [(19, 5 + hy, '#0A0C10'), (20, 4 + hy, '#0A0C10'), (21, 5 + hy, '#0A0C10'), (22, 11 + hy, '#FF7FA8'), (22, 12 + hy, '#FF7FA8'), (21, 12 + hy, '#E85A86')]
    else:
        det += [(20, 4 + hy, '#0A0C10'), (20, 5 + hy, '#0A0C10'), (21, 4 + hy, '#FFFFFF') if False else (20, 4 + hy, '#0A0C10')]
        det += [(21, 4 + hy, '#0A0C10'), (21, 5 + hy, '#2A2A35'), (20, 4 + hy, '#FFFFFF')]
    det += [(17, 12 + hy, '#F0C95C')]
    det += [(19, 8 + hy, '#F2A3B5')]  # cheek blush
    c.render(S, det, soft_pairs=[('head', 'snout'), ('body', 'leg'), ('body', 'tail'), ('head', 'body'), ('collar', 'head'), ('ear', 'head')])
    rgba = np.zeros((c.h, c.w, 4), np.uint8); rgba[..., :3] = np.clip(c.rgb, 0, 255).astype(np.uint8); rgba[..., 3] = (c.a > 0) * 255
    return Image.fromarray(rgba, 'RGBA')
frames = {'walk0': dog('stand', 0, 0), 'walk1': dog('stand', 1, 1), 'sit0': dog('sit', wag=0), 'sit1': dog('sit', wag=1), 'jump': dog('jump', happy=True), 'happy': dog('sit', wag=1, happy=True)}
for k, im in frames.items():
    im.save(f'ui/j_{k}.png')
sheet = Image.new('RGBA', (6 * 30, 22), (12, 32, 38, 255))
for i, im in enumerate(frames.values()): sheet.paste(im, (i * 30 + 2, 1), im)
sheet.resize((sheet.width * 8, sheet.height * 8), Image.NEAREST).save('ui/j_check.png')
# dialog portrait for Johnny (happy sit, square)
im = frames['happy']; sq = Image.new('RGBA', (26, 26), (0, 0, 0, 0)); sq.paste(im, (0, 5), im)
sq.resize((104, 104), Image.NEAREST).save('ui/p_johnny.png')
