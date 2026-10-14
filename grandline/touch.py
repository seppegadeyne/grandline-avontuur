"""Touch-besturing: vertaalt de JS-overlay (joystick + knoppen) naar pygame-events.

Alleen actief in de browser; op desktop is alles een no-op.
"""
import json

import pygame
from pygame.math import Vector2 as V

from .core import WEB
from .settings import WEAPON_ORDER

DEADZONE = 0.25      # joystick-dode zone
NAV_THRESHOLD = 0.5  # drempel voor menunavigatie
REPEAT_FIRST = 0.4   # eerste herhaling (s)
REPEAT_NEXT = 0.18   # volgende herhalingen (s)
NAV_HOLD = "hold"    # joystick eerst loslaten voor menunavigatie (na moduswissel of na lopen)

ACTION_KEYS = {
    "attack": pygame.K_SPACE,
    "dash": pygame.K_LSHIFT,
    "special": pygame.K_r,
    "eat": pygame.K_f,
    "use": pygame.K_e,
    "journal": pygame.K_TAB,
    "pause": pygame.K_ESCAPE,
    "back": pygame.K_ESCAPE,
    "ok": pygame.K_RETURN,
    "shop": pygame.K_b,
}


def _key(k, up=False):
    return pygame.event.Event(pygame.KEYUP if up else pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


def _web_poll():
    """Eén poll van de JS-kant (JSON-string) of None als die ontbreekt."""
    try:
        import platform
        raw = platform.window.gaTouchPoll()
        return json.loads(str(raw))
    except Exception:
        return None


def _web_set_mode(mode):
    try:
        import platform
        platform.window.gaSetMode(mode)
    except Exception:
        pass


class TouchInput:
    def __init__(self, source=None, set_mode=None):
        if source is None and WEB:
            source = _web_poll
        self.source = source
        self.set_mode = set_mode or (_web_set_mode if WEB else None)
        self.move = V()
        self.active = False
        self.mode = None
        self._nav = None      # huidige navigatierichting (toets) of None
        self._nav_t = 0.0

    # ------------------------------------------------------------------
    @staticmethod
    def mode_for(game):
        from .football import FootballScene
        from .scenes import WorldMap
        from .world import BossScene, IslandScene
        if not game.stack:
            return "menu"
        sc = game.stack[-1]
        if isinstance(sc, BossScene):
            return "boss"
        if isinstance(sc, IslandScene):
            return "island"
        if isinstance(sc, FootballScene):
            return "menu" if sc.over else "football"
        if isinstance(sc, WorldMap):
            return "map"
        return "menu"

    def _update_mode(self, game):
        mode = self.mode_for(game)
        if mode != self.mode:
            self.mode = mode
            # een joystick die nog vastgehouden wordt mag in een net geopend menu niets selecteren:
            # eerst loslaten
            self._nav = NAV_HOLD
            if self.set_mode:
                self.set_mode(mode)
        return mode

    @staticmethod
    def _next_weapon(prof):
        owned = [w for w in WEAPON_ORDER if w in prof.weapons]
        if len(owned) < 2:
            return None
        cur = prof.weapon if prof.weapon in owned else owned[0]
        return owned[(owned.index(cur) + 1) % len(owned)]

    def poll(self, game, dt):
        """Eén keer per frame: geeft synthetische events terug."""
        mode = self._update_mode(game)
        data = self.source() if self.source else None
        if not data:
            self.move = V()
            self._nav = None
            return []
        self.active = bool(data.get("active", False))
        mx, my = float(data.get("mx", 0)), float(data.get("my", 0))
        stick = V(mx, my)
        events = []
        # joystick
        if mode in ("menu", "map"):
            self.move = V()
            events += self._nav_events(stick, dt)
        else:
            self._nav = NAV_HOLD
            self.move = stick if stick.length() >= DEADZONE else V()
        # knoppen
        for name in data.get("down", []):
            if name == "weapon":
                wid = self._next_weapon(game.profile)
                if wid:
                    events.append(_key(pygame.K_1 + WEAPON_ORDER.index(wid)))
            elif name in ACTION_KEYS:
                events.append(_key(ACTION_KEYS[name]))
        for name in data.get("up", []):
            if name in ACTION_KEYS:
                events.append(_key(ACTION_KEYS[name], up=True))
        return events

    def _nav_events(self, stick, dt):
        d = None
        if stick.length() >= NAV_THRESHOLD:
            if abs(stick.x) >= abs(stick.y):
                d = pygame.K_RIGHT if stick.x > 0 else pygame.K_LEFT
            else:
                d = pygame.K_DOWN if stick.y > 0 else pygame.K_UP
        if d is None:
            self._nav = None
            return []
        if self._nav is NAV_HOLD:
            return []
        if d != self._nav:
            self._nav, self._nav_t = d, REPEAT_FIRST
            return [_key(d)]
        self._nav_t -= dt
        if self._nav_t <= 0:
            self._nav_t = REPEAT_NEXT
            return [_key(d)]
        return []
