"""Eilanden (verkennen, onderzoeken, vechten) en baasgevechten."""
import math
import random

import pygame
from pygame.math import Vector2 as V

from . import art
from .combat import Boss, CombatScene, Enemy
from .core import check_challenges, panel, shade, text, wrap
from .settings import BOSSES, GOLD, H, ISLANDS, W, WHITE

SEA = 360  # rand zee rond het eiland


class IslandScene(CombatScene):
    def __init__(self, game, idx):
        self.idx = idx
        self.isl = ISLANDS[idx]
        lw, lh = self.isl["size"]
        super().__init__(game, idx, (SEA, SEA, lw, lh))
        self.rnd = random.Random(1000 + idx)
        self.bg = None
        self.interact = []
        self.decor = []
        self.respawn_t = 0.0
        self.riddle_lock = {}
        self.build()
        self.player.pos = V(self.ship_pos) + V(110, -10)
        self.cam = self.player.pos - V(W / 2, H / 2)
        if idx not in game.profile.seen_intro:
            game.profile.seen_intro.append(idx)
            from .scenes import Dialog
            game.push(Dialog(game, self.isl["intro"]))

    # ---------------------------------------------------------------- bouwen
    def build(self):
        b = self.bounds
        rnd = self.rnd
        self.ship_pos = V(b.left - 40, b.bottom - 230)
        cx, cy = b.center
        self.shop_pos = V(b.left + 380, b.bottom - 330)
        self.field_pos = V(b.left + 380, b.top + 330)
        self.gate_pos = V(b.right - 230, b.top + 230)
        self.interact = [
            dict(kind="ship", pos=self.ship_pos + V(70, 0), label="Aan boord van de Going Merry (wereldkaart)"),
            dict(kind="shop", pos=self.shop_pos + V(0, 20), label="Winkel: kracht, HP en wapens"),
            dict(kind="field", pos=self.field_pos + V(0, 70), label="Voetbalwedstrijd spelen"),
            dict(kind="gate", pos=self.gate_pos + V(0, 60), label=f"Hol van {BOSSES[self.isl['boss']]['name']}"),
        ]
        spots = [V(cx - 150, b.top + 260), V(cx + 260, cy + 240), V(b.right - 420, b.bottom - 260)]
        for i, sp in enumerate(spots):
            self.interact.append(dict(kind="riddle", pos=sp, idx=i, label="Onderzoeken"))
        npc_spots = [self.shop_pos + V(170, 40), V(cx - 40, cy), V(b.right - 360, cy - 40)]
        for i, (name, line) in enumerate(self.isl["npcs"]):
            face = art.make_face(random.Random(hash(name) & 0xFFFF))
            face["eyes"] = "twee"
            shirt = (rnd.randint(60, 240), rnd.randint(60, 240), rnd.randint(60, 240))
            self.interact.append(dict(kind="npc", pos=npc_spots[i], name=name, line=line, face=face, shirt=shirt,
                                      label=f"Praten met {name}"))
        # decor + obstakels
        tree = {"dorp": "boom", "stad": "boom", "circus": "palm", "vulkaan": "dood", "koraal": "koraal"}[self.isl["decor"]]
        keep = [i["pos"] for i in self.interact] + [V(self.shop_pos), V(self.field_pos), V(self.gate_pos), self.player_start()]
        for _ in range(int(b.w * b.h / 60000)):
            p = V(rnd.uniform(b.left + 60, b.right - 60), rnd.uniform(b.top + 80, b.bottom - 40))
            if any((p - k).length() < 200 for k in keep) or (p - self.field_pos).length() < 330:
                continue
            kind = tree if rnd.random() < 0.75 else "steen"
            self.decor.append((kind, p, rnd.uniform(0, 6)))
            self.obstacles.append((p, 22 if kind != "steen" else 18))
        self.obstacles.append((V(self.shop_pos), 52))
        self.obstacles.append((V(self.gate_pos) + V(0, -10), 50))
        self.spawn_all()

    def player_start(self):
        return V(self.ship_pos) + V(110, -10)

    def spawn_all(self):
        for etype, n in self.isl["enemies"].items():
            for _ in range(n):
                self.spawn(etype)

    def spawn(self, etype, near=None):
        b = self.bounds
        for _ in range(40):
            if near is not None:
                p = V(near) + V(1, 0).rotate(random.uniform(0, 360)) * random.uniform(160, 260)
            else:
                p = V(random.uniform(b.left + 500, b.right - 80), random.uniform(b.top + 80, b.bottom - 80))
                if (p - self.player.pos).length() < 600:
                    continue
                if (p - self.field_pos).length() < 300 or (p - self.shop_pos).length() < 300:
                    continue
            if b.inflate(-60, -60).collidepoint(p):
                e = Enemy(etype, p, self.level)
                if near is not None:
                    e.aggro = True
                self.enemies.append(e)
                return e
        return None

    # ---------------------------------------------------------------- achtergrond
    def build_bg(self):
        b = self.bounds
        isl = self.isl
        surf = pygame.Surface((b.w + SEA * 2, b.h + SEA * 2)).convert()
        surf.fill((40, 110, 190))
        rnd = random.Random(7 + self.idx)
        for _ in range(300):
            x, y = rnd.randint(0, surf.get_width()), rnd.randint(0, surf.get_height())
            pygame.draw.line(surf, (70, 140, 215), (x, y), (x + 18, y), 2)
        land = pygame.Rect(SEA - 40, SEA - 40, b.w + 80, b.h + 80)
        pygame.draw.rect(surf, (60, 140, 210), land.inflate(80, 80), border_radius=140)
        pygame.draw.rect(surf, isl["sand"], land, border_radius=120)
        pygame.draw.rect(surf, isl["grass"], land.inflate(-90, -90), border_radius=100)
        for _ in range(700):
            x = rnd.randint(land.left + 80, land.right - 80)
            y = rnd.randint(land.top + 80, land.bottom - 80)
            pygame.draw.circle(surf, isl["grass2"], (x, y), rnd.randint(8, 30))
        # paden naar de belangrijke plekken
        hub = V(b.center) - V(b.topleft) + V(SEA, SEA)
        for pos in [self.ship_pos, self.shop_pos, self.field_pos, self.gate_pos] + [i["pos"] for i in self.interact if i["kind"] == "riddle"]:
            q = V(pos) - V(b.topleft) + V(SEA, SEA)
            pygame.draw.line(surf, shade(isl["sand"], 0.92), hub, q, 34)
        pygame.draw.circle(surf, shade(isl["sand"], 0.92), hub, 60)
        # voetbalveld
        f = pygame.Rect(0, 0, 360, 220)
        f.center = V(self.field_pos) - V(b.topleft) + V(SEA, SEA)
        pygame.draw.rect(surf, (70, 160, 70), f.inflate(20, 20))
        for i in range(6):
            pygame.draw.rect(surf, (80, 175, 80) if i % 2 else (70, 160, 70), (f.x + i * 60, f.y, 60, f.h))
        pygame.draw.rect(surf, WHITE, f, 3)
        pygame.draw.line(surf, WHITE, f.midtop, f.midbottom, 3)
        pygame.draw.circle(surf, WHITE, f.center, 36, 3)
        for side in (f.left, f.right - 6):
            pygame.draw.rect(surf, (230, 230, 230), (side, f.centery - 35, 6, 70))
        # steiger
        sx, sy = V(self.ship_pos) - V(b.topleft) + V(SEA, SEA)
        pygame.draw.rect(surf, (140, 100, 60), (sx + 20, sy - 14, 140, 28))
        for i in range(8):
            pygame.draw.line(surf, (100, 70, 40), (sx + 20 + i * 18, sy - 14), (sx + 20 + i * 18, sy + 14), 2)
        self.bg = surf

    # ---------------------------------------------------------------- input
    def nearest_interact(self):
        best, bd = None, 80
        for it in self.interact:
            d = (it["pos"] - self.player.pos).length()
            if d < bd:
                best, bd = it, d
        return best

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            from .scenes import Journal, Pause
            if e.key == pygame.K_ESCAPE:
                self.game.push(Pause(self.game))
                return
            if e.key in (pygame.K_TAB, pygame.K_i):
                self.game.push(Journal(self.game))
                return
            if e.key in (pygame.K_e, pygame.K_RETURN):
                it = self.nearest_interact()
                if it:
                    self.use(it)
                return
        self.handle_combat_event(e)

    def use(self, it):
        from .football import FootballScene
        from .scenes import Dialog, Riddle, Shop, WorldMap
        g, prof = self.game, self.game.profile
        k = it["kind"]
        if k == "ship":
            prof.save()
            g.replace(WorldMap(g))
        elif k == "shop":
            g.push(Shop(g))
        elif k == "field":
            if any((en.pos - self.player.pos).length() < 400 and en.aggro for en in self.enemies):
                g.toast("Er zijn vijanden in de buurt! Versla ze eerst.", (255, 160, 160))
                return
            g.push(FootballScene(g, self.idx, self))
        elif k == "npc":
            g.push(Dialog(g, [(it["name"], it["line"])]))
        elif k == "riddle":
            i = it["idx"]
            if i in prof.clue_list(self.idx):
                clue = self.isl["riddles"][i]["clue"]
                g.push(Dialog(g, [("Aanwijzing", clue)]))
                return
            if self.riddle_lock.get(i, 0) > self.time:
                g.toast(f"Hier kun je over {int(self.riddle_lock[i] - self.time) + 1} s opnieuw zoeken.", WHITE)
                return
            if self.isl.get("football_clue") and i == 2 and self.idx not in prof.football_won:
                g.push(Dialog(g, [("Clownpiraat", "Hihi! Die aanwijzing krijg je pas als je ons verslaat met voetbal!"),
                                  ("Clownpiraat", "Het voetbalveld ligt linksboven op het eiland. Durf je?")]))
                return
            g.push(Riddle(g, self, i))
        elif k == "gate":
            bid = self.isl["boss"]
            if bid in prof.bosses:
                g.push(Dialog(g, [("Verteller", f"Het hol is leeg. {BOSSES[bid]['name']} is al verslagen!")]))
                return
            need = 3 - prof.clue_count(self.idx)
            if need > 0:
                g.push(Dialog(g, [("Verteller", f"De poort zit op slot. Je hebt nog {need} aanwijzing(en) nodig. "
                                                "Zoek de ?-plekken op het eiland.")]))
                return
            prof.save()
            g.push(BossScene(g, self.idx, self))

    def riddle_result(self, i, correct):
        prof = self.game.profile
        if correct:
            prof.clue_list(self.idx).append(i)
            prof.berries += 40
            self.game.sfx.play("clue")
            self.game.toast("Aanwijzing gevonden! +40 Berries", (120, 220, 255))
            check_challenges(self.game)
            prof.save()
        else:
            self.game.sfx.play("wrong")
            self.riddle_lock[i] = self.time + 15
            self.game.toast("Fout! Het was een val... vijanden komen eraan!", (255, 120, 120))
            pos = next(it["pos"] for it in self.interact if it["kind"] == "riddle" and it["idx"] == i)
            kinds = list(self.isl["enemies"].keys())
            for _ in range(3):
                self.spawn(random.choice(kinds), near=pos)

    # ---------------------------------------------------------------- update
    def update(self, dt):
        self.update_combat(dt)
        self.respawn_t -= dt
        total = sum(self.isl["enemies"].values())
        if self.respawn_t <= 0 and len(self.enemies) < total:
            self.respawn_t = 4.0
            self.spawn(random.choice(list(self.isl["enemies"].keys())))
        target = self.player.pos - V(W / 2, H / 2)
        self.cam += (target - self.cam) * min(1, dt * 8)
        full = self.bounds.inflate(SEA * 2 - 400, SEA * 2 - 400)
        self.cam.x = max(full.left, min(full.right - W, self.cam.x))
        self.cam.y = max(full.top, min(full.bottom - H, self.cam.y))

    # ---------------------------------------------------------------- tekenen
    def draw(self, s):
        if self.bg is None:
            self.build_bg()
        cam = self.cam + self.shake_off()
        b = self.bounds
        s.blit(self.bg, (b.left - SEA - cam.x, b.top - SEA - cam.y))
        t = self.time
        art.draw_ship(s, *(self.ship_pos - cam), t, 1.3)
        view = pygame.Rect(cam.x - 150, cam.y - 150, W + 300, H + 300)
        extra = []
        for kind, p, v in self.decor:
            if view.collidepoint(p):
                extra.append((p.y, lambda s_, c, kind=kind, p=p, v=v: self.draw_decor(s_, c, kind, p, v)))
        extra.append((self.shop_pos.y, self.draw_shop))
        extra.append((self.gate_pos.y, self.draw_gate))
        if self.isl["decor"] == "dorp":
            mp = V(self.bounds.centerx + 120, self.bounds.top + 200)
            extra.append((mp.y, lambda s_, c: art.draw_windmill(s_, *(mp - c), t)))
        prof = self.game.profile
        for it in self.interact:
            if it["kind"] == "riddle":
                extra.append((it["pos"].y, lambda s_, c, it=it: self.draw_spot(s_, c, it)))
            elif it["kind"] == "npc":
                extra.append((it["pos"].y, lambda s_, c, it=it: art.draw_humanoid(
                    s_, *(it["pos"] - c), 17, t, (0, 0.3), it["shirt"], (70, 70, 90), it["face"])))
        self.draw_entities(s, cam, extra)
        # prompt
        it = self.nearest_interact()
        if it:
            x, y = it["pos"] - cam
            label = it["label"]
            if it["kind"] == "riddle" and it["idx"] in prof.clue_list(self.idx):
                label = "Aanwijzing bekijken"
            r = text(s, f"[E] {label}", 26, WHITE, (x, y - 70), "center", bold=True)
            del r
        self.draw_hud(s)
        # info rechtsboven
        n = prof.clue_count(self.idx)
        panel(s, (W - 330, 12, 318, 92), alpha=200)
        text(s, self.isl["name"], 30, GOLD, (W - 318, 20), bold=True)
        text(s, f"Aanwijzingen: {n}/3", 24, (120, 220, 255), (W - 318, 50))
        boss_done = self.isl["boss"] in prof.bosses
        text(s, "Baas verslagen!" if boss_done else ("Poort open: ga naar het hol!" if n >= 3 else "Zoek de ?-plekken"),
             22, (160, 255, 160) if boss_done or n >= 3 else WHITE, (W - 318, 76))
        self.draw_minimap(s)
        text(s, "Tab: dagboek   Esc: pauze", 20, (220, 220, 220), (W - 12, H - 12), "bottomright")

    def draw_minimap(self, s):
        b = self.bounds
        mw = 180
        mh = int(mw * b.h / b.w)
        r = pygame.Rect(W - mw - 14, 112, mw, mh)
        panel(s, r.inflate(8, 8), color=(30, 80, 140), alpha=200, radius=8, width=2)
        pygame.draw.rect(s, self.isl["grass"], r, border_radius=10)

        def mp(p):
            return (r.x + (p.x - b.left) / b.w * mw, r.y + (p.y - b.top) / b.h * mh)
        prof = self.game.profile
        for it in self.interact:
            k = it["kind"]
            col = {"ship": (140, 90, 40), "shop": GOLD, "field": (240, 240, 240), "gate": (200, 40, 40),
                   "npc": (200, 160, 255)}.get(k)
            if k == "riddle":
                col = (120, 220, 255) if it["idx"] in prof.clue_list(self.idx) else (255, 255, 0)
            pygame.draw.circle(s, col, mp(it["pos"]), 4)
        for e in self.enemies:
            pygame.draw.circle(s, (220, 60, 60), mp(e.pos), 2)
        pygame.draw.circle(s, WHITE, mp(self.player.pos), 4)
        pygame.draw.circle(s, (0, 0, 0), mp(self.player.pos), 4, 1)

    def draw_decor(self, s, cam, kind, p, v):
        x, y = p - cam
        if kind == "steen":
            pygame.draw.ellipse(s, (120, 120, 125), (x - 22, y - 16, 44, 30))
            pygame.draw.ellipse(s, (0, 0, 0), (x - 22, y - 16, 44, 30), 2)
        else:
            art.draw_tree(s, int(x), int(y), v, kind)

    def draw_shop(self, s, cam):
        x, y = self.shop_pos - cam
        art.draw_house(s, x, y + 30, (230, 200, 150), self.rnd, "tent" if self.isl["decor"] == "circus" else "huis")
        panel(s, (x - 50, y - 60, 100, 28), color=(120, 70, 30), alpha=255, radius=6, width=2)
        text(s, "WINKEL", 24, GOLD, (x, y - 46), "center", bold=True)

    def draw_gate(self, s, cam):
        x, y = self.gate_pos - cam
        prof = self.game.profile
        open_ = prof.clue_count(self.idx) >= 3
        pygame.draw.ellipse(s, (60, 50, 45), (x - 75, y - 90, 150, 140))
        pygame.draw.ellipse(s, (20, 15, 15), (x - 50, y - 60, 100, 110))
        if not open_ and self.isl["boss"] not in prof.bosses:
            for i in range(5):
                pygame.draw.line(s, (130, 90, 50), (x - 40 + i * 20, y - 55), (x - 40 + i * 20, y + 45), 7)
            pygame.draw.circle(s, GOLD, (int(x), int(y)), 9)
        else:
            glow = int(120 + 80 * math.sin(self.time * 4))
            pygame.draw.ellipse(s, (glow, 30, 30), (x - 40, y - 45, 80, 90), 3)
        text(s, "HOL", 22, (255, 120, 120), (x, y - 100), "center", bold=True)

    def draw_spot(self, s, cam, it):
        x, y = it["pos"] - cam
        done = it["idx"] in self.game.profile.clue_list(self.idx)
        bob = math.sin(self.time * 3 + it["idx"]) * 5
        pygame.draw.ellipse(s, (0, 0, 0, 80), (x - 20, y - 6, 40, 14))
        col = (120, 220, 255) if done else (255, 230, 50)
        pygame.draw.circle(s, col, (int(x), int(y - 30 + bob)), 20)
        pygame.draw.circle(s, (0, 0, 0), (int(x), int(y - 30 + bob)), 20, 2)
        text(s, "i" if done else "?", 34, (0, 0, 0), (x, y - 29 + bob), "center", bold=True, shadow=False)


class BossScene(CombatScene):
    aggro_range = 2000

    def __init__(self, game, idx, island):
        super().__init__(game, idx, (0, 0, W, H))
        self.bounds = pygame.Rect(60, 90, W - 120, H - 170)
        self.idx = idx
        self.island = island
        self.bid = ISLANDS[idx]["boss"]
        self.boss = Boss(self.bid, (self.bounds.right - 200, self.bounds.centery), game.profile)
        self.enemies = [self.boss]
        self.player.pos = V(self.bounds.left + 150, self.bounds.centery)
        self.intro_t = 2.2
        self.won_t = None
        self.start_hp = game.profile.hp
        rnd = random.Random(idx)
        self.rocks = [(V(rnd.uniform(self.bounds.left + 250, self.bounds.right - 250),
                         rnd.uniform(self.bounds.top + 80, self.bounds.bottom - 80)), 26) for _ in range(3)]
        self.obstacles = list(self.rocks)
        game.sfx.play("boom")

    def handle(self, e):
        if self.intro_t > 0 or self.won_t is not None:
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            from .scenes import Pause
            self.game.push(Pause(self.game, can_flee=True, scene=self))
            return
        self.handle_combat_event(e)

    def flee(self):
        self.game.pop()
        self.island.player.pos = V(self.island.gate_pos) + V(0, 120)
        self.game.toast("Je bent gevlucht. Word sterker en probeer opnieuw!", WHITE)

    def on_player_dead(self):
        from .scenes import GameOver
        self.game.push(GameOver(self.game, self, boss=True))

    def on_boss_dead(self, boss):
        prof = self.game.profile
        self.won_t = 4.0
        self.projs.clear()
        for e in self.enemies:
            e.dead = True
        prof.bosses.append(self.bid)
        prof.berries += boss.reward
        if prof.hp >= prof.max_hp * 0.5:
            prof.flawless = True
        if self.idx + 1 < len(ISLANDS):
            prof.unlocked = max(prof.unlocked, self.idx + 2)
        self.game.sfx.play("win")
        self.shake = 0.6
        for _ in range(6):
            self.fx_burst(boss.pos + V(random.uniform(-60, 60), random.uniform(-60, 60)), (255, 200, 80), 30, 300, 8)
        check_challenges(self.game)
        prof.save()

    def update(self, dt):
        if self.intro_t > 0:
            self.intro_t -= dt
            self.time += dt
            self.boss.t += dt
            return
        if self.won_t is not None:
            self.won_t -= dt
            self.update_combat(dt)
            if self.won_t <= 0:
                self.finish()
            return
        self.update_combat(dt)

    def finish(self):
        from .scenes import Dialog, Victory
        g = self.game
        g.pop()
        self.island.player.pos = V(self.island.gate_pos) + V(0, 120)
        if self.bid == "zeedraak":
            g.push(Victory(g))
        else:
            nxt = ISLANDS[self.idx + 1]["name"]
            g.push(Dialog(g, [("Verteller", f"Je versloeg {BOSSES[self.bid]['name']}! +{BOSSES[self.bid]['reward']} Berries."),
                              ("Verteller", f"Een nieuw eiland verschijnt op de kaart: {nxt}. Ga aan boord van je schip!")]))

    def draw(self, s):
        cam = self.shake_off()
        isl = ISLANDS[self.idx]
        s.fill(shade(isl["grass"], 0.45))
        b = self.bounds
        pygame.draw.rect(s, shade(isl["sand"], 0.75), b.move(-cam.x, -cam.y), border_radius=30)
        pygame.draw.rect(s, shade(isl["sand"], 0.55), b.move(-cam.x, -cam.y), 8, border_radius=30)
        for p, r in self.rocks:
            x, y = p - cam
            pygame.draw.circle(s, (100, 95, 95), (int(x), int(y)), r)
            pygame.draw.circle(s, (0, 0, 0), (int(x), int(y)), r, 2)
        self.draw_entities(s, cam)
        # baas-HP
        bo = self.boss
        panel(s, (W // 2 - 310, 14, 620, 62), alpha=210, border=(220, 60, 60))
        text(s, bo.b["name"] + ("  (WOEDEND!)" if bo.enraged and bo.hp > 0 else ""), 28,
             (255, 120, 120) if bo.enraged else WHITE, (W // 2, 30), "center", bold=True)
        from .core import bar
        bar(s, (W // 2 - 290, 46, 580, 20), bo.hp / bo.maxhp, (220, 50, 50))
        # speler-HP mini
        prof = self.game.profile
        panel(s, (14, H - 74, 300, 60), alpha=200)
        text(s, f"HP {prof.hp}/{prof.max_hp}   Vlees: {prof.meat} (F)", 22, WHITE, (26, H - 66))
        bar(s, (26, H - 42, 276, 14), prof.hp / prof.max_hp, (90, 210, 110))
        bar(s, (26, H - 24, 276, 6), self.player.special / 100, GOLD)
        text(s, "Esc: vluchten", 20, (220, 220, 220), (W - 14, H - 14), "bottomright")
        if self.intro_t > 0:
            from .core import dim
            dim(s, 120)
            text(s, bo.b["name"].upper(), 64, (255, 90, 90), (W // 2, H // 2 - 20), "center", bold=True)
            for i, line in enumerate(wrap("Rode lijnen en cirkels waarschuwen voor zijn aanvallen. Ontwijk met Shift!", 28, 700)):
                text(s, line, 28, WHITE, (W // 2, H // 2 + 40 + i * 30), "center")
        if self.won_t is not None:
            text(s, "BAAS VERSLAGEN!", 72, GOLD, (W // 2, H // 2), "center", bold=True)
