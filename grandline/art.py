"""Procedurele tekeningen: held, mannetjes met rare gezichten, draken, decor."""
import math
import random

import pygame

from .core import shade

SKIN_TONES = [(240, 200, 160), (220, 170, 120), (190, 140, 100), (150, 105, 75), (255, 215, 180),
              (170, 220, 140), (200, 170, 230)]  # ook groene en paarse mannetjes!


def make_face(rnd, style="normaal"):
    """Genereert een raar gezicht als dict met kenmerken."""
    face = dict(
        skin=rnd.choice(SKIN_TONES),
        eyes=rnd.choice(["twee", "cycloop", "scheel", "drie", "groot_klein", "spleet", "spiraal"]),
        mouth=rnd.choice(["grijns", "o", "zigzag", "tong", "scheef", "tanden", "snor"]),
        nose=rnd.choice(["knol", "lang", "varken", "geen", "haak"]),
        ears=rnd.choice(["klein", "flap", "puntig"]),
        hair=rnd.choice([None, (40, 30, 20), (250, 220, 60), (230, 60, 60), (60, 200, 90), (90, 90, 250)]),
        head_w=rnd.uniform(0.85, 1.3),
        head_h=rnd.uniform(0.85, 1.25),
        wobble=rnd.uniform(0, 6.28),
    )
    if style == "clown":
        face.update(skin=(250, 250, 250), nose="clown", hair=rnd.choice([(250, 120, 40), (60, 200, 250)]))
    if style == "vis":
        face.update(skin=rnd.choice([(110, 170, 210), (120, 200, 180), (160, 130, 210)]), ears="vin",
                    nose="geen", mouth=rnd.choice(["tanden", "o"]), hair=None)
    return face


def draw_eye(s, x, y, r, look=(0, 0), white=(255, 255, 255)):
    pygame.draw.circle(s, white, (int(x), int(y)), max(2, int(r)))
    pygame.draw.circle(s, (0, 0, 0), (int(x + look[0] * r * 0.4), int(y + look[1] * r * 0.4)), max(1, int(r * 0.5)))
    pygame.draw.circle(s, (0, 0, 0), (int(x), int(y)), max(2, int(r)), 1)


def draw_face(s, cx, cy, size, face, t, look=(1, 0), hurt=False):
    """Hoofd met rare gezichtskenmerken. size = straal hoofd."""
    hw = size * face["head_w"]
    hh = size * face["head_h"]
    wob = math.sin(t * 6 + face["wobble"]) * size * 0.04
    skin = (255, 120, 120) if hurt else face["skin"]
    rect = pygame.Rect(0, 0, int(hw * 2), int(hh * 2 + wob))
    rect.center = (int(cx), int(cy))
    # oren
    ex = hw * 0.95
    if face["ears"] == "flap":
        for d in (-1, 1):
            pygame.draw.ellipse(s, shade(skin, 0.85), (cx + d * ex - size * 0.35, cy - size * 0.3, size * 0.7, size * 0.9))
    elif face["ears"] == "puntig":
        for d in (-1, 1):
            pygame.draw.polygon(s, shade(skin, 0.85), [(cx + d * ex * 0.8, cy - size * 0.2),
                                                        (cx + d * (ex + size * 0.6), cy - size * 0.8),
                                                        (cx + d * ex * 0.85, cy + size * 0.25)])
    elif face["ears"] == "vin":
        for d in (-1, 1):
            pygame.draw.polygon(s, shade(skin, 0.7), [(cx + d * ex * 0.8, cy - size * 0.4),
                                                       (cx + d * (ex + size * 0.5), cy - size * 0.1),
                                                       (cx + d * ex * 0.8, cy + size * 0.3)])
    else:
        for d in (-1, 1):
            pygame.draw.circle(s, shade(skin, 0.85), (int(cx + d * ex), int(cy)), int(size * 0.22))
    pygame.draw.ellipse(s, skin, rect)
    pygame.draw.ellipse(s, (0, 0, 0), rect, 2)
    if face["hair"]:
        pygame.draw.ellipse(s, face["hair"], (rect.x + 2, rect.y - size * 0.15, rect.w - 4, rect.h * 0.4))
    # ogen
    lx, ly = look
    ey = cy - hh * 0.2
    er = size * 0.26
    e = face["eyes"]
    if e == "twee":
        draw_eye(s, cx - hw * 0.38, ey, er, look)
        draw_eye(s, cx + hw * 0.38, ey, er, look)
    elif e == "cycloop":
        draw_eye(s, cx, ey, er * 1.8, look)
    elif e == "scheel":
        draw_eye(s, cx - hw * 0.38, ey, er, (1, 0))
        draw_eye(s, cx + hw * 0.38, ey, er, (-1, 0))
    elif e == "drie":
        draw_eye(s, cx - hw * 0.45, ey, er * 0.8, look)
        draw_eye(s, cx + hw * 0.45, ey, er * 0.8, look)
        draw_eye(s, cx, ey - hh * 0.35, er * 0.8, look)
    elif e == "groot_klein":
        draw_eye(s, cx - hw * 0.35, ey, er * 1.5, look)
        draw_eye(s, cx + hw * 0.42, ey + 2, er * 0.6, look)
    elif e == "spleet":
        for d in (-1, 1):
            pygame.draw.line(s, (0, 0, 0), (cx + d * hw * 0.15, ey), (cx + d * hw * 0.6, ey - d * 2), 3)
    elif e == "spiraal":
        for d in (-1, 1):
            ox = cx + d * hw * 0.38
            pygame.draw.circle(s, (255, 255, 255), (int(ox), int(ey)), int(er))
            pts = [(ox + math.cos(a + t * 8) * er * a / 12, ey + math.sin(a + t * 8) * er * a / 12)
                   for a in [i * 0.5 for i in range(24)]]
            pygame.draw.lines(s, (0, 0, 0), False, pts, 1)
    # neus
    n = face["nose"]
    ny = cy + hh * 0.12
    if n == "knol":
        pygame.draw.circle(s, shade(skin, 0.8), (int(cx + lx * 3), int(ny)), int(size * 0.2))
    elif n == "lang":
        pygame.draw.line(s, shade(skin, 0.7), (cx, ny - 2), (cx + lx * size * 0.9 + 3, ny + 2), max(3, int(size * 0.13)))
    elif n == "varken":
        pygame.draw.ellipse(s, (240, 150, 170), (cx - size * 0.22, ny - size * 0.13, size * 0.44, size * 0.28))
        pygame.draw.circle(s, (0, 0, 0), (int(cx - size * 0.08), int(ny)), 2)
        pygame.draw.circle(s, (0, 0, 0), (int(cx + size * 0.08), int(ny)), 2)
    elif n == "haak":
        pygame.draw.polygon(s, shade(skin, 0.75), [(cx, ny - size * 0.2), (cx + lx * size * 0.45, ny + size * 0.15),
                                                   (cx, ny + size * 0.12)])
    elif n == "clown":
        pygame.draw.circle(s, (230, 30, 40), (int(cx), int(ny)), int(size * 0.24))
    # mond
    m = face["mouth"]
    my = cy + hh * 0.52
    mw = hw * 0.5
    if m == "grijns":
        pygame.draw.arc(s, (0, 0, 0), (cx - mw, my - size * 0.35, mw * 2, size * 0.5), math.pi * 1.1, math.pi * 1.9, 3)
    elif m == "o":
        pygame.draw.ellipse(s, (60, 0, 0), (cx - size * 0.15, my - size * 0.18, size * 0.3, size * 0.32))
    elif m == "zigzag":
        pts = [(cx - mw + i * mw / 3, my + (4 if i % 2 else -2)) for i in range(7)]
        pygame.draw.lines(s, (0, 0, 0), False, pts, 2)
    elif m == "tong":
        pygame.draw.line(s, (0, 0, 0), (cx - mw, my - 3), (cx + mw, my - 3), 3)
        pygame.draw.ellipse(s, (230, 80, 100), (cx - 3, my - 3, size * 0.3, size * 0.35))
    elif m == "scheef":
        pygame.draw.line(s, (0, 0, 0), (cx - mw, my - 5), (cx + mw, my + 4), 3)
    elif m == "tanden":
        r = pygame.Rect(cx - mw, my - size * 0.15, mw * 2, size * 0.3)
        pygame.draw.rect(s, (255, 255, 255), r)
        pygame.draw.rect(s, (0, 0, 0), r, 2)
        for i in range(1, 4):
            x = r.x + r.w * i / 4
            pygame.draw.line(s, (0, 0, 0), (x, r.y), (x, r.bottom), 1)
    elif m == "snor":
        pygame.draw.arc(s, (40, 25, 10), (cx - mw * 1.2, my - size * 0.4, mw * 1.2, size * 0.4), math.pi, math.pi * 2, 4)
        pygame.draw.arc(s, (40, 25, 10), (cx, my - size * 0.4, mw * 1.2, size * 0.4), math.pi, math.pi * 2, 4)


def draw_hat(s, cx, top, size, hat, t):
    if hat == "bandana":
        pygame.draw.ellipse(s, (200, 40, 40), (cx - size, top - size * 0.1, size * 2, size * 0.7))
        pygame.draw.line(s, (200, 40, 40), (cx - size * 0.8, top + size * 0.2), (cx - size * 1.4, top + size * 0.6 + math.sin(t * 9) * 3), 4)
    elif hat == "marine":
        pygame.draw.rect(s, (250, 250, 250), (cx - size * 0.85, top - size * 0.35, size * 1.7, size * 0.5), border_radius=4)
        pygame.draw.rect(s, (40, 70, 150), (cx - size * 0.85, top + size * 0.05, size * 1.7, size * 0.18))
        text_marine = pygame.Rect(cx - 5, top - size * 0.25, 10, 8)
        pygame.draw.ellipse(s, (40, 70, 150), text_marine)
    elif hat == "clown":
        pygame.draw.polygon(s, (250, 60, 150), [(cx - size * 0.7, top + size * 0.1), (cx + size * 0.7, top + size * 0.1),
                                                (cx + math.sin(t * 4) * 4, top - size * 1.1)])
        pygame.draw.circle(s, (250, 230, 60), (int(cx + math.sin(t * 4) * 4), int(top - size * 1.1)), int(size * 0.2))
    elif hat == "vin":
        pygame.draw.polygon(s, (60, 110, 160), [(cx - size * 0.4, top + size * 0.2), (cx + size * 0.4, top + size * 0.2),
                                                (cx + size * 0.1, top - size * 0.7)])
    elif hat == "stro":
        pygame.draw.ellipse(s, (235, 200, 90), (cx - size * 1.3, top + size * 0.05, size * 2.6, size * 0.6))
        pygame.draw.ellipse(s, (235, 200, 90), (cx - size * 0.75, top - size * 0.55, size * 1.5, size * 0.95))
        pygame.draw.rect(s, (200, 30, 30), (cx - size * 0.75, top + size * 0.02, size * 1.5, size * 0.16))
        pygame.draw.ellipse(s, (120, 90, 30), (cx - size * 1.3, top + size * 0.05, size * 2.6, size * 0.6), 1)


def draw_humanoid(s, x, y, r, t, look, shirt, pants, face, hat=None, moving=False, hurt=False, extra=None, scale=1.0):
    """Mannetje met groot hoofd (chibi-stijl). (x,y) = voeten-midden-ish (centrum lichaam)."""
    r *= scale
    step = math.sin(t * 12) * r * 0.25 if moving else 0
    # schaduw
    pygame.draw.ellipse(s, (0, 0, 0, 0), (0, 0, 0, 0))
    sh = pygame.Surface((int(r * 2.4), int(r * 0.8)), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 70), sh.get_rect())
    s.blit(sh, (x - r * 1.2, y + r * 0.9))
    # benen
    for d, ph in ((-1, step), (1, -step)):
        pygame.draw.line(s, pants, (x + d * r * 0.3, y + r * 0.3), (x + d * r * 0.35 + ph * 0.3, y + r * 1.1), max(3, int(r * 0.32)))
        pygame.draw.circle(s, (40, 30, 20), (int(x + d * r * 0.35 + ph * 0.3), int(y + r * 1.15)), max(2, int(r * 0.2)))
    # lijf
    body = pygame.Rect(0, 0, int(r * 1.3), int(r * 1.1))
    body.center = (int(x), int(y + r * 0.1))
    pygame.draw.ellipse(s, shirt, body)
    pygame.draw.ellipse(s, (0, 0, 0), body, 2)
    # armen
    for d, ph in ((-1, -step), (1, step)):
        pygame.draw.line(s, shirt, (x + d * r * 0.55, y - r * 0.1), (x + d * r * 0.85, y + r * 0.45 + ph * 0.3), max(3, int(r * 0.25)))
        pygame.draw.circle(s, face["skin"], (int(x + d * r * 0.85), int(y + r * 0.5 + ph * 0.3)), max(2, int(r * 0.16)))
    if extra == "bijl":
        pygame.draw.line(s, (120, 120, 130), (x + r * 0.85, y + r * 0.5), (x + r * 1.3, y - r * 0.2), 4)
        pygame.draw.polygon(s, (190, 190, 200), [(x + r * 1.15, y - r * 0.4), (x + r * 1.6, y - r * 0.2), (x + r * 1.3, y + r * 0.1)])
    # hoofd
    hr = r * 0.85
    hy = y - r * 0.85
    draw_face(s, x, hy, hr, face, t, look, hurt)
    if extra == "baard":
        pygame.draw.ellipse(s, (60, 40, 20), (x - hr * 0.7, hy + hr * 0.45, hr * 1.4, hr * 0.8))
    if hat:
        draw_hat(s, x, hy - hr * face["head_h"] * 0.85, hr, hat, t)


HERO_FACE = dict(skin=(245, 205, 165), eyes="twee", mouth="grijns", nose="geen", ears="klein", hair=(25, 20, 20),
                 head_w=1.0, head_h=1.0, wobble=0)


def draw_hero(s, x, y, t, look, moving, hurt=False, scale=1.0):
    r = 20 * scale
    draw_humanoid(s, x, y, r / scale, t, look, (210, 40, 40), (60, 100, 200), HERO_FACE, hat=None,
                  moving=moving, hurt=hurt, scale=scale)
    hr = r * 0.85
    hy = y - r * 0.85
    # litteken onder het oog
    pygame.draw.line(s, (150, 40, 40), (x - hr * 0.5, hy + hr * 0.15), (x - hr * 0.3, hy + hr * 0.25), 2)
    draw_hat(s, x, hy - hr * 0.85, hr, "stro", t)


def draw_dragon(s, x, y, r, t, look, color, hurt=False):
    col = (255, 120, 120) if hurt else color
    dark = shade(col, 0.65)
    flap = math.sin(t * 10)
    lx, ly = look
    sh = pygame.Surface((int(r * 2.6), int(r * 0.9)), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 60), sh.get_rect())
    s.blit(sh, (x - r * 1.3, y + r * 1.0))
    hover = math.sin(t * 3) * r * 0.1
    y = y + hover - r * 0.15
    # vleugels
    for d in (-1, 1):
        tip = (x + d * r * 2.0, y - r * (0.9 + 0.6 * flap))
        pts = [(x + d * r * 0.3, y - r * 0.2), tip, (x + d * r * 1.7, y + r * 0.2), (x + d * r * 1.0, y + r * 0.1)]
        pygame.draw.polygon(s, dark, pts)
        pygame.draw.polygon(s, (0, 0, 0), pts, 2)
    # staart
    tail = [(x - lx * r * (0.6 + i * 0.35) + math.sin(t * 5 + i) * r * 0.15,
             y + r * 0.3 - ly * r * 0.3 * i) for i in range(5)]
    pygame.draw.lines(s, col, False, tail, max(3, int(r * 0.3)))
    pygame.draw.polygon(s, dark, [tail[-1], (tail[-1][0] - lx * r * 0.4 - r * 0.2, tail[-1][1] - r * 0.25),
                                  (tail[-1][0] - lx * r * 0.4 + r * 0.2, tail[-1][1] + r * 0.25)])
    # lijf
    pygame.draw.ellipse(s, col, (x - r * 0.75, y - r * 0.55, r * 1.5, r * 1.3))
    pygame.draw.ellipse(s, (240, 220, 160), (x - r * 0.4, y - r * 0.2, r * 0.8, r * 0.8))
    pygame.draw.ellipse(s, (0, 0, 0), (x - r * 0.75, y - r * 0.55, r * 1.5, r * 1.3), 2)
    # kop
    hx, hy = x + lx * r * 0.75, y - r * 0.7 + ly * r * 0.3
    pygame.draw.circle(s, col, (int(hx), int(hy)), int(r * 0.55))
    pygame.draw.ellipse(s, col, (hx + lx * r * 0.2 - r * 0.35, hy - r * 0.1, r * 0.7, r * 0.45))
    pygame.draw.circle(s, (0, 0, 0), (int(hx), int(hy)), int(r * 0.55), 2)
    # hoorns
    for d in (-1, 1):
        pygame.draw.polygon(s, (240, 230, 200), [(hx + d * r * 0.25, hy - r * 0.35), (hx + d * r * 0.45, hy - r * 0.95),
                                                 (hx + d * r * 0.05, hy - r * 0.45)])
    draw_eye(s, hx - r * 0.2, hy - r * 0.12, r * 0.17, look, (255, 240, 80))
    draw_eye(s, hx + r * 0.2, hy - r * 0.12, r * 0.17, look, (255, 240, 80))
    # neusgaten met rookje
    if int(t * 3) % 2 == 0:
        pygame.draw.circle(s, (120, 120, 120), (int(hx + lx * r * 0.5), int(hy + r * 0.0 - (t * 20) % 10)), 3)


def draw_tree(s, x, y, rnd_v, kind="boom"):
    if kind == "palm":
        pygame.draw.line(s, (120, 85, 50), (x, y), (x + 8, y - 60), 7)
        for a in range(5):
            ang = a * 1.25 + rnd_v
            pygame.draw.line(s, (40, 140, 60), (x + 8, y - 60), (x + 8 + math.cos(ang) * 35, y - 60 + math.sin(ang) * 18 + 8), 6)
    elif kind == "dood":
        pygame.draw.line(s, (60, 50, 45), (x, y), (x, y - 50), 6)
        pygame.draw.line(s, (60, 50, 45), (x, y - 30), (x - 18, y - 48), 4)
        pygame.draw.line(s, (60, 50, 45), (x, y - 38), (x + 15, y - 56), 4)
    elif kind == "koraal":
        for a in range(4):
            pygame.draw.line(s, (240, 110, 130), (x, y), (x + (a - 1.5) * 12, y - 30 - (a % 2) * 15), 5)
            pygame.draw.circle(s, (250, 160, 170), (int(x + (a - 1.5) * 12), int(y - 30 - (a % 2) * 15)), 5)
    else:
        pygame.draw.rect(s, (110, 75, 45), (x - 6, y - 28, 12, 30))
        pygame.draw.circle(s, (40, 120, 50), (x, y - 45), 28)
        pygame.draw.circle(s, (55, 145, 60), (x - 10, y - 52), 16)


def draw_house(s, x, y, color, rnd, kind="huis"):
    w, h = 90, 70
    pygame.draw.rect(s, color, (x - w // 2, y - h, w, h))
    pygame.draw.rect(s, (0, 0, 0), (x - w // 2, y - h, w, h), 2)
    roof = (180, 60, 50) if kind != "tent" else (240, 60, 120)
    pygame.draw.polygon(s, roof, [(x - w // 2 - 10, y - h), (x + w // 2 + 10, y - h), (x, y - h - 45)])
    pygame.draw.polygon(s, (0, 0, 0), [(x - w // 2 - 10, y - h), (x + w // 2 + 10, y - h), (x, y - h - 45)], 2)
    pygame.draw.rect(s, (90, 60, 35), (x - 12, y - 34, 24, 34))
    pygame.draw.rect(s, (160, 210, 240), (x - 36, y - 55, 16, 16))
    pygame.draw.rect(s, (160, 210, 240), (x + 20, y - 55, 16, 16))


def draw_windmill(s, x, y, t):
    pygame.draw.polygon(s, (230, 220, 200), [(x - 30, y), (x + 30, y), (x + 15, y - 110), (x - 15, y - 110)])
    pygame.draw.polygon(s, (0, 0, 0), [(x - 30, y), (x + 30, y), (x + 15, y - 110), (x - 15, y - 110)], 2)
    for i in range(4):
        a = t * 1.5 + i * math.pi / 2
        ex, ey = x + math.cos(a) * 70, y - 110 + math.sin(a) * 70
        pygame.draw.line(s, (100, 70, 40), (x, y - 110), (ex, ey), 5)
        px, py = -math.sin(a) * 14, math.cos(a) * 14
        pygame.draw.polygon(s, (250, 250, 240), [(x + (ex - x) * 0.3, y - 110 + (ey - y + 110) * 0.3),
                                                 (ex, ey), (ex + px, ey + py), (x + (ex - x) * 0.3 + px, y - 110 + (ey - y + 110) * 0.3 + py)])


def draw_ship(s, x, y, t, scale=1.0, sail=(250, 250, 245)):
    bob = math.sin(t * 2) * 3 * scale
    y += bob
    hull = [(x - 60 * scale, y - 10 * scale), (x + 60 * scale, y - 10 * scale), (x + 45 * scale, y + 18 * scale), (x - 48 * scale, y + 18 * scale)]
    pygame.draw.polygon(s, (150, 95, 50), hull)
    pygame.draw.polygon(s, (0, 0, 0), hull, 2)
    pygame.draw.circle(s, (240, 220, 120), (int(x + 52 * scale), int(y - 16 * scale)), int(11 * scale))  # schapenkop
    pygame.draw.line(s, (90, 60, 30), (x, y - 10 * scale), (x, y - 80 * scale), max(2, int(4 * scale)))
    pygame.draw.rect(s, sail, (x - 30 * scale, y - 75 * scale, 60 * scale, 45 * scale))
    pygame.draw.rect(s, (0, 0, 0), (x - 30 * scale, y - 75 * scale, 60 * scale, 45 * scale), 1)
    # doodshoofd met strohoed
    cx, cy = x, y - 52 * scale
    pygame.draw.circle(s, (20, 20, 20), (int(cx), int(cy)), int(10 * scale))
    pygame.draw.ellipse(s, (235, 200, 90), (cx - 13 * scale, cy - 12 * scale, 26 * scale, 7 * scale))
    pygame.draw.rect(s, (20, 20, 20), (x - 6 * scale, y - 96 * scale, 16 * scale, 12 * scale))


def random_for(seed):
    return random.Random(seed)
