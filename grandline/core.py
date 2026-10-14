"""Gedeelde helpers: tekst, panelen, geluid, profiel/opslag en uitdagingen."""
import array
import json
import math
import os
import random
import sys

import pygame

from .settings import (CHALLENGES, DRAGON_TYPES, ENEMY_TYPES, GOLD, HUMANOID_TYPES, ISLANDS,
                       RESEARCH_KILLS, WEAPON_ORDER)

SAVE_DIR = os.path.join(os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share"),
                        "grandline-avontuur")
SAVE_PATH = os.path.join(SAVE_DIR, "save.json")
SAVE_KEY = "grandline-avontuur/save"   # localStorage-sleutel in de browser

# In de browser (pygbag/WebAssembly) draait Python onder emscripten.
WEB = sys.platform == "emscripten"


def _storage():
    """localStorage van de browser, of None op desktop."""
    if not WEB:
        return None
    try:
        import platform
        return platform.window.localStorage
    except Exception:
        return None

# ------------------------------------------------------------------ tekst
_fonts = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        f = pygame.font.Font(None, size)
        f.bold = bold
        _fonts[key] = f
    return _fonts[key]


def text(surf, s, size, color, pos, anchor="topleft", bold=False, shadow=True):
    f = font(size, bold)
    img = f.render(str(s), True, color)
    r = img.get_rect(**{anchor: pos})
    if shadow:
        sh = f.render(str(s), True, (0, 0, 0))
        surf.blit(sh, r.move(2, 2))
    surf.blit(img, r)
    return r


def wrap(s, size, width, bold=False):
    f = font(size, bold)
    lines, cur = [], ""
    for word in str(s).split(" "):
        test = (cur + " " + word).strip()
        if f.size(test)[0] <= width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def panel(surf, rect, color=(16, 22, 40), alpha=225, border=GOLD, radius=14, width=3):
    rect = pygame.Rect(rect)
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=radius)
    surf.blit(s, rect.topleft)
    if border:
        pygame.draw.rect(surf, border, rect, width, border_radius=radius)


def bar(surf, rect, frac, color, back=(45, 45, 55), border=(0, 0, 0)):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, back, rect, border_radius=4)
    frac = max(0.0, min(1.0, frac))
    if frac > 0:
        pygame.draw.rect(surf, color, (rect.x, rect.y, max(2, int(rect.w * frac)), rect.h), border_radius=4)
    pygame.draw.rect(surf, border, rect, 2, border_radius=4)


def dim(surf, alpha=150):
    s = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    s.fill((0, 0, 0, alpha))
    surf.blit(s, (0, 0))


def shade(color, f):
    return tuple(max(0, min(255, int(c * f))) for c in color)


# ------------------------------------------------------------------ geluid
def _synth(parts, rate, channels, vol=0.35):
    """parts: lijst van (freq_start, freq_eind, duur, golfvorm)."""
    buf = array.array("h")
    rnd = random.Random(1)
    for f0, f1, dur, wave in parts:
        n = int(rate * dur)
        phase = 0.0
        for i in range(n):
            t = i / max(1, n)
            f = f0 + (f1 - f0) * t
            phase += f / rate
            if wave == "sq":
                v = 1.0 if (phase % 1) < 0.5 else -1.0
            elif wave == "noise":
                v = rnd.uniform(-1, 1)
            elif wave == "tri":
                v = 4 * abs((phase % 1) - 0.5) - 1
            else:
                v = math.sin(phase * 2 * math.pi)
            env = min(1.0, i / (rate * 0.005 + 1)) * (1 - t) ** 1.5
            s = int(v * env * vol * 32767)
            for _ in range(channels):
                buf.append(s)
    return pygame.mixer.Sound(buffer=buf.tobytes())


class Sfx:
    def __init__(self):
        self.sounds = {}
        try:
            pygame.mixer.init(22050, -16, 1, 512)
            rate, _, ch = pygame.mixer.get_init()
        except Exception:
            return
        try:
            S = lambda parts, vol=0.35: _synth(parts, rate, ch, vol)  # noqa: E731
            self.sounds = {
                "swing": S([(900, 300, 0.08, "noise")], 0.18),
                "hit": S([(180, 60, 0.09, "sq")], 0.3),
                "crit": S([(300, 80, 0.12, "sq")], 0.35),
                "hurt": S([(400, 120, 0.18, "sq")], 0.3),
                "coin": S([(988, 988, 0.05, "sq"), (1319, 1319, 0.12, "sq")], 0.18),
                "kick": S([(140, 50, 0.08, "sine"), (2000, 500, 0.03, "noise")], 0.5),
                "goal": S([(523, 523, 0.12, "tri"), (659, 659, 0.12, "tri"), (784, 784, 0.12, "tri"),
                           (1047, 1047, 0.35, "tri")], 0.4),
                "whistle": S([(2200, 2300, 0.35, "sine")], 0.25),
                "shoot": S([(700, 200, 0.1, "tri")], 0.25),
                "fire": S([(300, 100, 0.25, "noise")], 0.2),
                "boom": S([(120, 30, 0.45, "noise")], 0.5),
                "dash": S([(300, 900, 0.1, "tri")], 0.2),
                "clue": S([(660, 660, 0.1, "tri"), (880, 880, 0.1, "tri"), (1320, 1320, 0.25, "tri")], 0.35),
                "wrong": S([(220, 180, 0.3, "sq")], 0.25),
                "buy": S([(784, 784, 0.07, "sq"), (1175, 1175, 0.15, "sq")], 0.2),
                "select": S([(600, 600, 0.04, "sq")], 0.12),
                "win": S([(523, 523, 0.15, "sq"), (659, 659, 0.15, "sq"), (784, 784, 0.15, "sq"),
                          (1047, 1047, 0.15, "sq"), (784, 784, 0.1, "sq"), (1047, 1047, 0.5, "sq")], 0.25),
                "special": S([(80, 600, 0.35, "sq"), (600, 100, 0.3, "noise")], 0.35),
            }
        except Exception:
            self.sounds = {}

    def play(self, name):
        snd = self.sounds.get(name)
        if snd:
            snd.play()


# ------------------------------------------------------------------ profiel
class Profile:
    def __init__(self):
        self.berries = 0
        self.str_lvl = 0
        self.hp_lvl = 0
        self.spd_lvl = 0
        self.weapons = ["vuist"]
        self.weapon = "vuist"
        self.meat = 2
        self.kills = {}
        self.clues = {}          # "eiland-index" -> [riddle-indexen]
        self.bosses = []
        self.unlocked = 1
        self.island = 0
        self.goals = 0
        self.wins = 0
        self.matches = 0
        self.best_match_goals = 0
        self.flawless = False
        self.football_won = []   # eilanden waar je een voetbalwedstrijd won
        self.done = []
        self.seen_intro = []
        self.hp = self.max_hp

    # afgeleide statistieken
    @property
    def max_hp(self):
        return 100 + 20 * self.hp_lvl

    @property
    def dmg_mult(self):
        return 1 + 0.15 * self.str_lvl

    @property
    def speed(self):
        return 255 + 18 * self.spd_lvl

    def researched(self, etype):
        return self.kills.get(etype, 0) >= RESEARCH_KILLS

    def clue_list(self, idx):
        return self.clues.setdefault(str(idx), [])

    def clue_count(self, idx):
        return len(self.clues.get(str(idx), []))

    def total_clues(self):
        return sum(len(v) for v in self.clues.values())

    def to_dict(self):
        return dict(self.__dict__)

    def save(self):
        data = json.dumps(self.to_dict(), indent=1)
        store = _storage()
        if store is not None:
            try:
                store.setItem(SAVE_KEY, data)
            except Exception as exc:
                print("Opslaan mislukt:", exc)
            return
        try:
            os.makedirs(SAVE_DIR, exist_ok=True)
            tmp = SAVE_PATH + ".tmp"
            with open(tmp, "w") as fh:
                fh.write(data)
            os.replace(tmp, SAVE_PATH)
        except OSError as exc:
            print("Opslaan mislukt:", exc)

    @staticmethod
    def _read_raw():
        store = _storage()
        if store is not None:
            try:
                return store.getItem(SAVE_KEY)
            except Exception:
                return None
        try:
            with open(SAVE_PATH) as fh:
                return fh.read()
        except OSError:
            return None

    @classmethod
    def load(cls):
        p = cls()
        raw = cls._read_raw()
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except ValueError:
            return None
        if not isinstance(data, dict):
            return None
        for k, v in data.items():
            if hasattr(p, k):
                setattr(p, k, v)
        p.weapons = [w for w in WEAPON_ORDER if w in p.weapons] or ["vuist"]
        if p.weapon not in p.weapons:
            p.weapon = p.weapons[0]
        p.hp = max(1, min(p.hp, p.max_hp))
        return p

    @staticmethod
    def exists():
        return bool(Profile._read_raw())


def challenge_met(p, cid):
    hum = sum(p.kills.get(t, 0) for t in HUMANOID_TYPES)
    drk = sum(p.kills.get(t, 0) for t in DRAGON_TYPES)
    return {
        "eerste": hum + drk >= 1,
        "jager": hum >= 25,
        "draak1": drk >= 1,
        "draak10": drk >= 10,
        "hattrick": p.best_match_goals >= 3,
        "spits": p.goals >= 20,
        "kampioen": p.wins >= 5,
        "speurneus": p.total_clues() >= 6,
        "professor": all(p.researched(t) for t in ENEMY_TYPES),
        "onaantastbaar": p.flawless,
        "sterk": p.str_lvl >= 10,
        "wapens": len(p.weapons) >= len(WEAPON_ORDER),
        "koning": "zeedraak" in p.bosses,
    }.get(cid, False)


def check_challenges(game):
    p = game.profile
    for cid, name, _desc, reward in CHALLENGES:
        if cid not in p.done and challenge_met(p, cid):
            p.done.append(cid)
            p.berries += reward
            game.toast(f"Uitdaging voltooid: {name}!  +{reward} Berries", GOLD)
            game.sfx.play("win")


def island_name(i):
    return ISLANDS[i]["name"]


# ------------------------------------------------------------------ scènes
class Scene:
    opaque = True

    def __init__(self, game):
        self.game = game

    def handle(self, e):
        pass

    def update(self, dt):
        pass

    def draw(self, s):
        pass

    def on_resume(self):
        pass


def is_confirm(e):
    return e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_e)


def is_back(e):
    return e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE)
