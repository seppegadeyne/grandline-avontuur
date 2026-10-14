"""Menu's en overlays: titel, wereldkaart, dialoog, raadsel, winkel, dagboek, pauze, einde."""
import math
import random

import pygame
from pygame.math import Vector2 as V

from . import art
from .combat import draw_weapon_icon
from .core import WEB, Profile, Scene, check_challenges, dim, is_back, is_confirm, panel, tap_pos, text, wrap
from .settings import (BOSSES, CHALLENGES, ENEMY_TYPES, GOLD, H, ISLANDS, RESEARCH_KILLS, TITLE, W, WEAPON_ORDER,
                       WEAPONS, WHITE)


def nav(e, n, sel):
    if e.type == pygame.KEYDOWN:
        if e.key in (pygame.K_UP, pygame.K_w, pygame.K_z):
            return (sel - 1) % n
        if e.key in (pygame.K_DOWN, pygame.K_s):
            return (sel + 1) % n
    return sel


def tap_row(e, rects):
    """Index van de rij die getikt is (linkermuisknop/touch), anders None."""
    pos = tap_pos(e)
    if pos:
        for i, r in enumerate(rects):
            if r.collidepoint(pos):
                return i
    return None


def draw_sea(s, t):
    s.fill((30, 90, 170))
    for i in range(14):
        y = i * 56 + (t * 20) % 56
        for x in range(-60, W + 60, 120):
            xx = x + math.sin(t + i) * 30 + (i % 2) * 60
            pygame.draw.arc(s, (70, 140, 215), (xx, y, 60, 22), 0, math.pi, 3)


# ------------------------------------------------------------------ titel
class Title(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.t = 0
        self.sel = 0
        self.has_save = Profile.exists()
        self.items = (["Verder spelen"] if self.has_save else []) + ["Nieuw avontuur", "Besturing"] + \
            ([] if WEB else ["Afsluiten"])
        rnd = random.Random()
        self.faces = [art.make_face(rnd) for _ in range(4)]

    def handle(self, e):
        self.sel = nav(e, len(self.items), self.sel)
        go = is_confirm(e)
        hit = tap_row(e, self.rects())
        if hit is not None:
            self.sel, go = hit, True
        if go:
            self.game.sfx.play("select")
            item = self.items[self.sel]
            if item == "Verder spelen":
                self.game.profile = Profile.load() or Profile()
                self.game.replace(WorldMap(self.game))
            elif item == "Nieuw avontuur":
                if self.has_save:
                    self.game.push(Confirm(self.game, "Je huidige opslag wordt overschreven. Zeker?", self.new_game))
                else:
                    self.new_game()
            elif item == "Besturing":
                self.game.push(Help(self.game))
            else:
                self.game.running = False

    def rects(self):
        return [pygame.Rect(W // 2 - 170, 410 + i * 44 - 22, 340, 44) for i in range(len(self.items))]

    def new_game(self):
        self.game.profile = Profile()
        self.game.profile.save()
        self.game.replace(WorldMap(self.game))
        self.game.push(Dialog(self.game, [
            ("Verteller", "Je bent Luffy-achtig: een jonge piraat met een strohoed en een lichaam van rubber."),
            ("Verteller", "Je droom: Koning der Piraten worden! Daarvoor moet je de Grand Line oversteken."),
            ("Verteller", "Vecht tegen draken en mannetjes met rare gezichten, voetbal voor Berries, "
                          "koop kracht en wapens en los de mysteries van elk eiland op."),
            ("Verteller", "Kies een eiland op de kaart en vaar erheen met Enter. Veel succes, kapitein!"),
        ]))

    def update(self, dt):
        self.t += dt

    def draw(self, s):
        draw_sea(s, self.t)
        art.draw_ship(s, W // 2 + math.sin(self.t * 0.4) * 420, 680, self.t, 1.6)
        for i, f in enumerate(self.faces):
            x = 140 + i * 330
            art.draw_humanoid(s, x, 330 + math.sin(self.t * 2 + i) * 10, 26, self.t, (math.sin(self.t + i), 0),
                              (100 + i * 40, 80, 160 - i * 30), (50, 50, 70), f, ["bandana", "marine", "clown", "vin"][i],
                              True)
        art.draw_dragon(s, 1080 + math.sin(self.t) * 40, 170, 36, self.t, (-1, 0.2), (210, 70, 40))
        text(s, "GRAND LINE", 110, GOLD, (W // 2, 110), "center", bold=True)
        text(s, "AVONTUUR", 70, WHITE, (W // 2, 185), "center", bold=True)
        text(s, "Vechten - Voetballen - Onderzoeken", 28, (220, 230, 255), (W // 2, 232), "center")
        panel(s, (W // 2 - 170, 380, 340, 44 * len(self.items) + 24), alpha=250)
        for i, it in enumerate(self.items):
            sel = i == self.sel
            text(s, ("> " if sel else "") + it, 36, GOLD if sel else WHITE, (W // 2, 410 + i * 44), "center", bold=sel)
        text(s, "Pijltjes + Enter", 20, (200, 200, 200), (W // 2, H - 14), "midbottom")


class Help(Scene):
    opaque = False
    LINES = [
        ("Lopen", "WASD / ZQSD / pijltjes"),
        ("Aanvallen", "Spatie / J / linkermuisknop (mikken met muis)"),
        ("Ontwijken (dash)", "Shift / K / rechtermuisknop"),
        ("Speciale aanval", "R (als de gele SP-balk vol is)"),
        ("Vlees eten (+HP)", "F"),
        ("Wapen wisselen", "1 - 6"),
        ("Praten / onderzoeken", "E of Enter"),
        ("Dagboek (uitdagingen)", "Tab of I"),
        ("Voetbal: schieten", "Spatie ingedrukt houden en loslaten (of muis)"),
        ("Voetbal: sprint", "Shift"),
        ("Pauze / terug", "Esc"),
    ]

    PANEL = pygame.Rect(W // 2 - 420, 80, 840, 560)

    def handle(self, e):
        pos = tap_pos(e)
        if is_back(e) or is_confirm(e) or pos:  # tik (ook buiten het paneel) sluit
            self.game.pop()

    def draw(self, s):
        dim(s, 170)
        panel(s, self.PANEL)
        text(s, "Besturing", 50, GOLD, (W // 2, 120), "center", bold=True)
        for i, (a, b) in enumerate(self.LINES):
            text(s, a, 28, GOLD, (W // 2 - 380, 170 + i * 38))
            text(s, b, 28, WHITE, (W // 2 - 80, 170 + i * 38))
        text(s, "Esc om terug te gaan", 22, (200, 200, 200), (W // 2, 615), "center")


# ------------------------------------------------------------------ wereldkaart
class WorldMap(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.t = 0.0
        prof = game.profile
        self.sel = min(prof.island, prof.unlocked - 1)
        self.ship = V(ISLANDS[self.sel]["map_pos"])
        self.sailing = None

    def handle(self, e):
        prof = self.game.profile
        if self.sailing is not None:
            return
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_UP, pygame.K_w, pygame.K_z):
                self.sel = min(prof.unlocked - 1, self.sel + 1)
                self.game.sfx.play("select")
            elif e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_q, pygame.K_DOWN, pygame.K_s):
                self.sel = max(0, self.sel - 1)
                self.game.sfx.play("select")
            elif e.key in (pygame.K_TAB, pygame.K_i):
                self.game.push(Journal(self.game))
            elif e.key == pygame.K_b:
                self.game.push(Shop(self.game))
            elif e.key == pygame.K_ESCAPE:
                self.game.push(Pause(self.game))
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, isl in enumerate(ISLANDS[:prof.unlocked]):
                if (V(isl["map_pos"]) - V(e.pos)).length() < 60:
                    self.sel = i
        go = e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e, pygame.K_SPACE)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            go = (V(ISLANDS[self.sel]["map_pos"]) - V(e.pos)).length() < 60
        if go:
            self.sailing = 0.0
            self.game.sfx.play("whistle")

    def update(self, dt):
        self.t += dt
        target = V(ISLANDS[self.sel]["map_pos"])
        if self.sailing is not None:
            self.sailing += dt
            self.ship += (target - self.ship) * min(1, dt * 4)
            if self.sailing > 0.9:
                from .world import IslandScene
                prof = self.game.profile
                prof.island = self.sel
                prof.hp = prof.max_hp  # uitgerust na de zeereis
                prof.save()
                self.game.replace(IslandScene(self.game, self.sel))
        else:
            self.ship += (target - self.ship) * min(1, dt * 3)

    def draw(self, s):
        draw_sea(s, self.t * 0.5)
        prof = self.game.profile
        pts = [V(i["map_pos"]) for i in ISLANDS]
        for a, b in zip(pts, pts[1:]):
            for k in range(12):
                p = a + (b - a) * (k / 12)
                pygame.draw.circle(s, (230, 230, 240), p, 3)
        for i, isl in enumerate(ISLANDS):
            x, y = isl["map_pos"]
            unlocked = i < prof.unlocked
            pygame.draw.ellipse(s, isl["sand"] if unlocked else (90, 100, 120), (x - 70, y - 40, 140, 80))
            pygame.draw.ellipse(s, isl["grass"] if unlocked else (70, 80, 100), (x - 55, y - 32, 110, 60))
            if isl["decor"] == "vulkaan":
                pygame.draw.polygon(s, (90, 60, 50), [(x - 30, y + 10), (x + 30, y + 10), (x + 10, y - 40), (x - 10, y - 40)])
                pygame.draw.circle(s, (255, 120, 30), (int(x), int(y - 42)), 8)
            if i == self.sel:
                pygame.draw.ellipse(s, GOLD, (x - 78, y - 48, 156, 96), 4)
            name = isl["name"] if unlocked else "???"
            text(s, name, 28, WHITE if unlocked else (160, 160, 170), (x, y + 50), "center", bold=True)
            if unlocked:
                done = isl["boss"] in prof.bosses
                text(s, "verslagen" if done else f"aanwijzingen {prof.clue_count(i)}/3", 20,
                     (160, 255, 160) if done else (200, 230, 255), (x, y + 72), "center")
        art.draw_ship(s, self.ship.x, self.ship.y - 30, self.t, 0.7)
        isl = ISLANDS[self.sel]
        panel(s, (20, 20, 470, 150), alpha=215)
        text(s, isl["name"], 40, GOLD, (36, 32), bold=True)
        text(s, isl["sub"], 26, WHITE, (36, 72))
        b = BOSSES[isl["boss"]]
        text(s, f"Baas: {b['name']}", 24, (255, 150, 150), (36, 102))
        kinds = ", ".join(ENEMY_TYPES[k]["name"] for k in isl["enemies"])
        text(s, f"Vijanden: {kinds}", 20, (220, 220, 220), (36, 132))
        panel(s, (W - 380, 20, 360, 116), alpha=215)
        text(s, f"Berries: {prof.berries}", 30, GOLD, (W - 364, 32), bold=True)
        text(s, f"Uitdagingen: {len(prof.done)}/{len(CHALLENGES)}", 24, WHITE, (W - 364, 68))
        text(s, f"Bazen verslagen: {len(prof.bosses)}/{len(ISLANDS)}", 24, WHITE, (W - 364, 96))
        text(s, "Pijltjes: kies eiland   Enter: varen   B: winkel   Tab: dagboek   Esc: menu", 22, WHITE,
             (W // 2, H - 16), "midbottom")


# ------------------------------------------------------------------ dialoog
class Dialog(Scene):
    opaque = False

    def __init__(self, game, lines, on_done=None):
        super().__init__(game)
        self.lines = lines
        self.i = 0
        self.chars = 0.0
        self.on_done = on_done

    def handle(self, e):
        if is_confirm(e) or (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or is_back(e):
            full = self.lines[self.i][1]
            if self.chars < len(full) and not is_back(e):
                self.chars = len(full)
                return
            self.i += 1
            self.chars = 0
            if self.i >= len(self.lines) or is_back(e):
                self.game.pop()
                if self.on_done:
                    self.on_done()

    def update(self, dt):
        self.chars += dt * 60

    def draw(self, s):
        if self.i >= len(self.lines):
            return
        name, line = self.lines[self.i]
        r = pygame.Rect(80, H - 210, W - 160, 180)
        panel(s, r, alpha=235)
        panel(s, (r.x + 20, r.y - 22, max(160, len(name) * 15 + 30), 40), color=(120, 40, 40), alpha=255, radius=10)
        text(s, name, 28, GOLD, (r.x + 36, r.y - 12), bold=True)
        shown = line[:int(self.chars)]
        for k, ln in enumerate(wrap(shown, 30, r.w - 60)):
            text(s, ln, 30, WHITE, (r.x + 30, r.y + 32 + k * 32))
        text(s, f"{self.i + 1}/{len(self.lines)}  Enter >", 20, (200, 200, 200), (r.right - 20, r.bottom - 14), "bottomright")


# ------------------------------------------------------------------ onderzoek: raadsel
class Riddle(Scene):
    opaque = False

    def __init__(self, game, island, i):
        super().__init__(game)
        self.island = island
        self.i = i
        rd = ISLANDS[island.idx]["riddles"][i]
        self.q = rd["q"]
        self.correct = rd["options"][0]
        self.opts = list(rd["options"])
        random.shuffle(self.opts)
        self.sel = 0

    def handle(self, e):
        self.sel = nav(e, len(self.opts), self.sel)
        hit = tap_row(e, self.rects())
        if hit is not None:
            self.sel = hit
            self.answer()
        elif e.type == pygame.KEYDOWN and pygame.K_1 <= e.key <= pygame.K_3:
            self.sel = e.key - pygame.K_1
            self.answer()
        elif is_confirm(e):
            self.answer()
        elif is_back(e):
            self.game.pop()

    PANEL = pygame.Rect(W // 2 - 440, 150, 880, 400)

    def rects(self):
        r = self.PANEL
        return [pygame.Rect(r.x + 120, r.y + 190 + k * 58, r.w - 240, 48) for k in range(len(self.opts))]

    def answer(self):
        ok = self.opts[self.sel] == self.correct
        self.game.pop()
        self.island.riddle_result(self.i, ok)
        if ok:
            self.game.push(Dialog(self.game, [("Aanwijzing", ISLANDS[self.island.idx]["riddles"][self.i]["clue"])]))

    def draw(self, s):
        dim(s, 150)
        r = self.PANEL
        panel(s, r)
        text(s, "ONDERZOEK", 44, (120, 220, 255), (W // 2, r.y + 36), "center", bold=True)
        for k, ln in enumerate(wrap(self.q, 32, r.w - 80)):
            text(s, ln, 32, WHITE, (W // 2, r.y + 90 + k * 34), "center")
        for k, o in enumerate(self.opts):
            sel = k == self.sel
            rr = self.rects()[k]
            panel(s, rr, color=(50, 70, 120) if sel else (30, 35, 55), alpha=240, border=GOLD if sel else (90, 90, 110),
                  radius=10, width=2)
            text(s, f"{k + 1}. {o}", 30, GOLD if sel else WHITE, rr.center, "center", bold=sel)
        text(s, "Fout antwoord = een val met vijanden!  Esc: later", 20, (255, 170, 170), (W // 2, r.bottom - 18), "center")


# ------------------------------------------------------------------ winkel
class Shop(Scene):
    opaque = False

    def __init__(self, game):
        super().__init__(game)
        self.sel = 0

    def items(self):
        p = self.game.profile
        out = [
            dict(id="str", name=f"Kracht  (niveau {p.str_lvl} -> {p.str_lvl + 1})", price=80 + 70 * p.str_lvl,
                 desc="+15% schade met alle wapens.", ok=p.str_lvl < 20),
            dict(id="hp", name=f"Uithouding  (niveau {p.hp_lvl} -> {p.hp_lvl + 1})", price=70 + 60 * p.hp_lvl,
                 desc="+20 maximale HP.", ok=p.hp_lvl < 20),
            dict(id="spd", name=f"Snelheid  (niveau {p.spd_lvl} -> {p.spd_lvl + 1})", price=90 + 90 * p.spd_lvl,
                 desc="Sneller lopen. Handig bij voetbal!", ok=p.spd_lvl < 8),
            dict(id="meat", name=f"Vlees  (je hebt er {p.meat})", price=30, desc="Eet met F: herstelt 45% HP.",
                 ok=p.meat < 9),
            dict(id="heal", name="Volledige genezing", price=40, desc="Meteen al je HP terug.", ok=p.hp < p.max_hp),
        ]
        for wid in WEAPON_ORDER[1:]:
            wd = WEAPONS[wid]
            owned = wid in p.weapons
            out.append(dict(id="w:" + wid, name=wd["name"] + ("  (in bezit)" if owned else ""), price=wd["price"],
                            desc=f"{wd['desc']}  Schade {wd['dmg']}.", ok=not owned, weapon=wid))
        return out

    def handle(self, e):
        its = self.items()
        self.sel = nav(e, len(its), self.sel)
        hit = tap_row(e, self.rects(len(its)))
        if is_back(e):
            self.game.profile.save()
            self.game.pop()
        elif hit is not None:
            # eerste tik selecteert, tik op de gekozen rij koopt
            if hit == self.sel:
                self.buy(its[hit])
            self.sel = hit
        elif is_confirm(e):
            self.buy(its[self.sel])

    PANEL = pygame.Rect(W // 2 - 520, 40, 1040, 640)

    def rects(self, n):
        r = self.PANEL
        return [pygame.Rect(r.x + 30, r.y + 100 + k * 48, r.w - 60, 42) for k in range(n)]

    def buy(self, it):
        p = self.game.profile
        if not it["ok"]:
            self.game.toast("Dat kun je nu niet kopen.", WHITE)
            self.game.sfx.play("wrong")
            return
        if p.berries < it["price"]:
            self.game.toast("Niet genoeg Berries! Vecht of voetbal voor meer.", (255, 150, 150))
            self.game.sfx.play("wrong")
            return
        p.berries -= it["price"]
        i = it["id"]
        if i == "str":
            p.str_lvl += 1
        elif i == "hp":
            p.hp_lvl += 1
            p.hp += 20
        elif i == "spd":
            p.spd_lvl += 1
        elif i == "meat":
            p.meat += 1
        elif i == "heal":
            p.hp = p.max_hp
        else:
            wid = it["weapon"]
            p.weapons.append(wid)
            p.weapons = [w for w in WEAPON_ORDER if w in p.weapons]
            p.weapon = wid
        self.game.sfx.play("buy")
        self.game.toast(f"Gekocht: {it['name'].split('  (')[0]}", GOLD)
        check_challenges(self.game)

    def draw(self, s):
        dim(s, 160)
        p = self.game.profile
        r = self.PANEL
        panel(s, r)
        text(s, "WINKEL", 52, GOLD, (r.x + 30, r.y + 18), bold=True)
        text(s, f"Berries: {p.berries}", 36, GOLD, (r.right - 30, r.y + 26), "topright", bold=True)
        text(s, f"HP {p.hp}/{p.max_hp}   Schade x{p.dmg_mult:.2f}", 24, WHITE, (r.right - 30, r.y + 62), "topright")
        its = self.items()
        rects = self.rects(len(its))
        for k, it in enumerate(its):
            sel = k == self.sel
            rr = rects[k]
            afford = p.berries >= it["price"]
            panel(s, rr, color=(50, 70, 120) if sel else (28, 32, 52), alpha=240, border=GOLD if sel else (70, 70, 90),
                  radius=8, width=2 if sel else 1)
            if "weapon" in it:
                draw_weapon_icon(s, it["weapon"], (rr.x + 24, rr.centery), 0.8)
            col = WHITE if it["ok"] else (130, 130, 140)
            text(s, it["name"], 28, col, (rr.x + 50, rr.y + 10), bold=sel)
            if it["ok"]:
                text(s, f"{it['price']} B", 28, GOLD if afford else (220, 90, 90), (rr.right - 16, rr.y + 10), "topright",
                     bold=True)
        cur = its[self.sel]
        text(s, cur["desc"], 26, (200, 230, 255), (r.x + 30, r.bottom - 50))
        text(s, "Enter: kopen   Esc: sluiten", 20, (200, 200, 200), (r.right - 30, r.bottom - 44), "topright")


# ------------------------------------------------------------------ dagboek
class Journal(Scene):
    opaque = False
    TABS = ["Uitdagingen", "Onderzoek", "Aanwijzingen"]

    def __init__(self, game):
        super().__init__(game)
        self.tab = 0

    PANEL = pygame.Rect(W // 2 - 540, 30, 1080, 660)

    def tab_rects(self):
        r = self.PANEL
        return [pygame.Rect(r.x + 30 + k * 220, r.y + 70, 210, 40) for k in range(len(self.TABS))]

    def handle(self, e):
        pos = tap_pos(e)
        if pos:
            hit = tap_row(e, self.tab_rects())
            if hit is not None:
                self.tab = hit
            elif not self.PANEL.collidepoint(pos):
                self.game.pop()
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_q):
                self.tab = (self.tab - 1) % 3
            elif e.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_TAB):
                self.tab = (self.tab + 1) % 3
            elif e.key in (pygame.K_ESCAPE, pygame.K_i, pygame.K_RETURN):
                self.game.pop()

    def draw(self, s):
        dim(s, 170)
        p = self.game.profile
        r = self.PANEL
        panel(s, r)
        text(s, "DAGBOEK VAN DE KAPITEIN", 44, GOLD, (r.x + 30, r.y + 18), bold=True)
        for k, name in enumerate(self.TABS):
            sel = k == self.tab
            tr = self.tab_rects()[k]
            panel(s, tr, color=(60, 80, 140) if sel else (30, 34, 54), alpha=255, border=GOLD if sel else (80, 80, 100),
                  radius=8, width=2)
            text(s, name, 28, GOLD if sel else WHITE, tr.center, "center", bold=sel)
        y = r.y + 130
        if self.tab == 0:
            for cid, name, desc, reward in CHALLENGES:
                done = cid in p.done
                pygame.draw.rect(s, (90, 210, 110) if done else (80, 80, 90), (r.x + 34, y + 4, 18, 18), 0 if done else 2)
                text(s, name, 26, GOLD if done else WHITE, (r.x + 64, y), bold=True)
                text(s, desc, 24, (210, 210, 220), (r.x + 300, y + 2))
                text(s, f"+{reward}", 24, GOLD, (r.right - 30, y + 2), "topright")
                y += 38
        elif self.tab == 1:
            text(s, f"Versla een vijandsoort {RESEARCH_KILLS} keer om haar te onderzoeken: +25% schade tegen die soort.",
                 24, (200, 230, 255), (r.x + 34, y))
            y += 46
            for k, (etype, d) in enumerate(ENEMY_TYPES.items()):
                n = p.kills.get(etype, 0)
                known = n > 0
                done = n >= RESEARCH_KILLS
                cx, cy = r.x + 90 + (k % 3) * 340, y + 70 + (k // 3) * 220
                panel(s, (cx - 70, cy - 70, 320, 200), color=(26, 30, 48), alpha=255,
                      border=(120, 220, 255) if done else (70, 70, 90), radius=10, width=2)
                if known:
                    if d["kind"] == "dragon":
                        art.draw_dragon(s, cx, cy + 10, d["radius"] * 0.9, pygame.time.get_ticks() / 1000, (1, 0), d["color"])
                    else:
                        face = art.make_face(random.Random(k * 7), d.get("style", "normaal"))
                        art.draw_humanoid(s, cx, cy + 20, 18, pygame.time.get_ticks() / 1000, (1, 0), d["shirt"],
                                          d["pants"], face, d["hat"])
                    text(s, d["name"], 28, WHITE, (cx + 60, cy - 55), bold=True)
                    text(s, f"HP {d['hp']}  Schade {d['dmg']}", 22, (220, 220, 220), (cx + 60, cy - 25))
                    soort = {"melee": "Vecht van dichtbij", "shooter": "Schiet met musket", "dragon": "Spuwt vuur"}[d["kind"]]
                    text(s, soort, 22, (220, 220, 220), (cx + 60, cy + 0))
                    text(s, f"{min(n, RESEARCH_KILLS)}/{RESEARCH_KILLS} {'ONDERZOCHT' if done else ''}", 24,
                         (120, 220, 255) if done else GOLD, (cx + 60, cy + 30), bold=True)
                else:
                    text(s, "???", 60, (90, 90, 100), (cx + 90, cy + 30), "center", bold=True)
        else:
            for i, isl in enumerate(ISLANDS):
                if i >= p.unlocked:
                    break
                text(s, isl["name"], 28, GOLD, (r.x + 34, y), bold=True)
                y += 30
                got = p.clues.get(str(i), [])
                for j, rd in enumerate(isl["riddles"]):
                    if j in got:
                        for ln in wrap("- " + rd["clue"], 22, r.w - 90)[:2]:
                            text(s, ln, 22, (200, 230, 255), (r.x + 54, y))
                            y += 22
                    else:
                        text(s, "- ??? (nog te onderzoeken)", 22, (130, 130, 140), (r.x + 54, y))
                        y += 22
                y += 8
        text(s, "Pijltjes/Tab: tabblad   Esc: sluiten", 20, (200, 200, 200), (r.right - 24, r.bottom - 28), "topright")


# ------------------------------------------------------------------ pauze / bevestigen
class Pause(Scene):
    opaque = False

    def __init__(self, game, can_flee=False, scene=None):
        super().__init__(game)
        self.scene = scene
        self.items = ["Verder"] + (["Vluchten uit gevecht"] if can_flee else []) + \
            ["Besturing", "Opslaan en naar titel"] + ([] if WEB else ["Opslaan en afsluiten"])
        self.sel = 0

    def handle(self, e):
        self.sel = nav(e, len(self.items), self.sel)
        hit = tap_row(e, self.rects())
        if hit is not None:
            self.sel = hit
        if is_back(e):
            self.game.pop()
        elif is_confirm(e) or hit is not None:
            it = self.items[self.sel]
            g = self.game
            if it == "Verder":
                g.pop()
            elif it.startswith("Vluchten"):
                g.pop()
                self.scene.flee()
            elif it == "Besturing":
                g.push(Help(g))
            elif it.startswith("Opslaan en naar"):
                g.profile.save()
                g.stack.clear()
                g.push(Title(g))
            else:
                g.profile.save()
                g.running = False

    def rects(self):
        top = H // 2 - (90 + 50 * len(self.items)) // 2
        return [pygame.Rect(W // 2 - 200, top + 95 + i * 50 - 25, 400, 50) for i in range(len(self.items))]

    def draw(self, s):
        dim(s, 150)
        h = 90 + 50 * len(self.items)
        panel(s, (W // 2 - 220, H // 2 - h // 2, 440, h))
        text(s, "PAUZE", 48, GOLD, (W // 2, H // 2 - h // 2 + 40), "center", bold=True)
        for i, it in enumerate(self.items):
            sel = i == self.sel
            text(s, it, 32, GOLD if sel else WHITE, (W // 2, H // 2 - h // 2 + 95 + i * 50), "center", bold=sel)


class Confirm(Scene):
    opaque = False

    def __init__(self, game, msg, on_yes):
        super().__init__(game)
        self.msg, self.on_yes, self.sel = msg, on_yes, 1

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d, pygame.K_q):
            self.sel ^= 1
        hit = tap_row(e, self.rects())
        if hit is not None:
            self.sel = hit
        if is_back(e):
            self.game.pop()
        elif is_confirm(e) or hit is not None:
            self.game.pop()
            if self.sel == 0:
                self.on_yes()

    def rects(self):
        return [pygame.Rect(W // 2 - 80 + i * 160 - 70, H // 2 + 35 - 25, 140, 50) for i in range(2)]

    def draw(self, s):
        dim(s, 150)
        panel(s, (W // 2 - 330, H // 2 - 90, 660, 180))
        text(s, self.msg, 30, WHITE, (W // 2, H // 2 - 40), "center")
        for i, lbl in enumerate(["Ja", "Nee"]):
            sel = i == self.sel
            text(s, lbl, 36, GOLD if sel else WHITE, (W // 2 - 80 + i * 160, H // 2 + 35), "center", bold=sel)


# ------------------------------------------------------------------ game over / overwinning
class GameOver(Scene):
    opaque = False

    def __init__(self, game, scene, boss=False):
        super().__init__(game)
        self.scene, self.boss = scene, boss
        p = game.profile
        self.lost = p.berries // 5
        p.berries -= self.lost
        self.t = 0

    def update(self, dt):
        self.t += dt

    def handle(self, e):
        if self.t > 0.8 and (is_confirm(e) or tap_pos(e)):
            g = self.game
            p = g.profile
            p.hp = p.max_hp
            g.pop()
            if self.boss:
                self.scene.flee()
            else:
                isl = self.scene
                isl.player.pos = isl.player_start()
                isl.projs.clear()
                for en in isl.enemies:
                    en.aggro = False
                    en.pos = V(en.home)
            p.save()

    def draw(self, s):
        dim(s, 190)
        text(s, "KNOCK-OUT!", 90, (255, 90, 90), (W // 2, H // 2 - 80), "center", bold=True)
        text(s, f"Je verloor {self.lost} Berries. Je wordt wakker bij je schip.", 30, WHITE, (W // 2, H // 2), "center")
        text(s, "Tip: koop kracht en HP in de winkel, en speel voetbal voor extra Berries.", 26, (200, 230, 255),
             (W // 2, H // 2 + 44), "center")
        if self.t > 0.8:
            text(s, "Druk op Enter", 26, GOLD, (W // 2, H // 2 + 110), "center")


class Victory(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.t = 0
        self.confetti = [[random.uniform(0, W), random.uniform(-H, 0), random.uniform(60, 160),
                          random.choice([GOLD, (255, 80, 80), (80, 160, 255), WHITE, (90, 210, 110)])] for _ in range(200)]

    def update(self, dt):
        self.t += dt
        for c in self.confetti:
            c[1] += c[2] * dt
            if c[1] > H:
                c[1] = -10

    def handle(self, e):
        if self.t > 2 and (is_confirm(e) or tap_pos(e)):
            self.game.replace(WorldMap(self.game))

    def draw(self, s):
        draw_sea(s, self.t)
        art.draw_ship(s, W // 2, 520, self.t, 2.5)
        for c in self.confetti:
            pygame.draw.rect(s, c[3], (c[0], c[1], 6, 10))
        p = self.game.profile
        text(s, "KONING DER PIRATEN!", 84, GOLD, (W // 2, 120), "center", bold=True)
        text(s, "Je versloeg Zeedraak Leviathan en stak de hele Grand Line over!", 32, WHITE, (W // 2, 190), "center")
        text(s, f"Uitdagingen: {len(p.done)}/{len(CHALLENGES)}    Goals: {p.goals}    Berries: {p.berries}", 28,
             (200, 230, 255), (W // 2, 232), "center")
        text(s, "Speel verder om alle uitdagingen te halen!", 26, WHITE, (W // 2, 268), "center")
        if self.t > 2:
            text(s, "Enter: terug naar de kaart", 26, GOLD, (W // 2, H - 30), "center")
