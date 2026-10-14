"""Gevechtsmotor: speler, vijanden, bazen, projectielen, effecten."""
import math
import random

import pygame
from pygame.math import Vector2 as V

from . import art
from .core import Scene, bar, check_challenges, panel, text
from .settings import (BOSSES, DRAGON_TYPES, ENEMY_TYPES, GOLD, GREEN, H, RED, RESEARCH_KILLS, W, WEAPON_ORDER,
                       WEAPONS, WHITE)


def unit(v):
    return v.normalize() if v.length_squared() > 1e-6 else V(1, 0)


# ------------------------------------------------------------------ effecten
class Particle:
    __slots__ = ("pos", "vel", "life", "max", "color", "size", "grav")

    def __init__(self, pos, vel, life, color, size, grav=0.0):
        self.pos, self.vel, self.life, self.max, self.color, self.size, self.grav = V(pos), V(vel), life, life, color, size, grav


class FloatText:
    __slots__ = ("pos", "s", "color", "life", "size")

    def __init__(self, pos, s, color, size=26):
        self.pos, self.s, self.color, self.life, self.size = V(pos), s, color, 0.9, size


class Proj:
    def __init__(self, pos, vel, dmg, r, owner, color, kind="ball", pierce=False, life=2.0):
        self.pos, self.vel = V(pos), V(vel)
        self.dmg, self.r, self.owner, self.color, self.kind, self.pierce, self.life = dmg, r, owner, color, kind, pierce, life
        self.hit = set()
        self.dead = False


class Pickup:
    def __init__(self, pos, kind, value):
        self.pos = V(pos)
        self.vel = V(random.uniform(-120, 120), random.uniform(-120, 120))
        self.kind, self.value = kind, value
        self.t = 0.0


# ------------------------------------------------------------------ speler
class Player:
    def __init__(self, pos):
        self.pos = V(pos)
        self.r = 18
        self.facing = V(1, 0)
        self.aim = V(1, 0)
        self.atk_cd = 0.0
        self.atk_t = 0.0
        self.atk_len = 0.0
        self.atk_kind = None
        self.atk_dir = V(1, 0)
        self.hitset = set()
        self.dash_cd = 0.0
        self.dash_t = 0.0
        self.dash_dir = V(1, 0)
        self.inv = 0.0
        self.special = 0.0
        self.special_t = 0.0
        self.moving = False
        self.t = 0.0
        self.mouse_t = -10.0


# ------------------------------------------------------------------ vijanden
class Enemy:
    is_boss = False

    def __init__(self, etype, pos, level, rnd=random):
        d = ENEMY_TYPES[etype]
        self.etype, self.d = etype, d
        self.kind = d["kind"]
        self.maxhp = self.hp = d["hp"] * (1 + 0.45 * level)
        self.dmg = d["dmg"] * (1 + 0.3 * level)
        self.reward = int(d["reward"] * (1 + 0.35 * level))
        self.speed = d["speed"] * (1 + 0.04 * level)
        self.r = d["radius"]
        self.pos = V(pos)
        self.home = V(pos)
        self.knock = V()
        self.cd = rnd.uniform(0.6, 1.6)
        self.windup = 0.0
        self.hurt_t = 0.0
        self.t = rnd.uniform(0, 10)
        self.aggro = False
        self.wander = V()
        self.wander_t = 0.0
        self.moving = False
        self.look = V(1, 0)
        self.orbit = rnd.choice((-1, 1))
        self.dead = False
        self.face = art.make_face(rnd, d.get("style", "normaal")) if self.kind != "dragon" else None
        self.flying = self.kind == "dragon"

    def update(self, w, dt):
        self.t += dt
        self.hurt_t = max(0, self.hurt_t - dt)
        p = w.player
        to = p.pos - self.pos
        dist = to.length()
        if dist < w.aggro_range or self.hp < self.maxhp:
            self.aggro = True
        elif dist > w.aggro_range * 2:
            self.aggro = False
        move = V()
        if self.aggro:
            self.look = unit(to)
            if self.kind == "melee":
                if self.windup > 0:
                    self.windup -= dt
                    if self.windup <= 0:
                        if dist < self.r + p.r + 22:
                            w.hurt_player(self.dmg, self.pos)
                        w.fx_burst(self.pos + self.look * (self.r + 8), (255, 255, 255), 5, 120)
                        self.cd = 1.0
                elif dist < self.r + p.r + 10 and self.cd <= 0:
                    self.windup = 0.32
                else:
                    move = unit(to)
            elif self.kind == "shooter":
                if dist > 330:
                    move = unit(to)
                elif dist < 220:
                    move = -unit(to)
                else:
                    move = unit(to).rotate(90 * self.orbit) * 0.6
                if self.cd <= 0 and dist < 560:
                    w.add_proj(Proj(self.pos, unit(to) * 330, self.dmg, 7, "enemy", (40, 40, 40), "ball"))
                    w.game.sfx.play("shoot")
                    self.cd = 1.9
            else:  # draak
                if dist > 300:
                    move = unit(to)
                elif dist < 200:
                    move = -unit(to)
                else:
                    move = unit(to).rotate(90 * self.orbit) * 0.8
                if self.cd <= 0 and dist < 480:
                    w.fire_breath(self.pos + self.look * self.r, self.look, self.dmg * 0.7, 5, 36)
                    self.cd = 2.6
        else:
            self.wander_t -= dt
            if self.wander_t <= 0:
                self.wander_t = random.uniform(1.5, 3.5)
                self.wander = V(random.uniform(-1, 1), random.uniform(-1, 1)) * 0.5 if random.random() < 0.7 else V()
                if (self.pos - self.home).length() > 250:
                    self.wander = unit(self.home - self.pos) * 0.5
            move = self.wander
            if move.length_squared() > 0:
                self.look = unit(move)
        self.cd -= dt
        self.moving = move.length_squared() > 0.01
        self.pos += move * self.speed * dt + self.knock * dt
        self.knock *= max(0.0, 1 - 8 * dt)

    def draw(self, s, cam):
        x, y = self.pos - cam
        hurt = self.hurt_t > 0
        if self.kind == "dragon":
            art.draw_dragon(s, x, y, self.r, self.t, (self.look.x, self.look.y), self.d["color"], hurt)
        else:
            d = self.d
            art.draw_humanoid(s, x, y, self.r, self.t, (self.look.x, self.look.y), d["shirt"], d["pants"], self.face,
                              d["hat"], self.moving, hurt)
            if self.windup > 0:
                pygame.draw.circle(s, (255, 60, 60), (int(x), int(y)), self.r + 14, 2)
        if self.hp < self.maxhp:
            bar(s, (x - 22, y - self.r * 2.4 - 6, 44, 6), self.hp / self.maxhp, RED)


class Boss(Enemy):
    is_boss = True

    def __init__(self, bid, pos, profile):
        b = BOSSES[bid]
        self.bid, self.b = bid, b
        self.etype = bid
        self.d = b
        self.kind = "boss"
        self.maxhp = self.hp = b["hp"]
        self.dmg = b["dmg"]
        self.reward = b["reward"]
        self.speed = b["speed"]
        self.r = b["r"]
        self.pos = V(pos)
        self.home = V(pos)
        self.knock = V()
        self.hurt_t = 0.0
        self.t = 0.0
        self.look = V(-1, 0)
        self.moving = False
        self.dead = False
        self.aggro = True
        self.flying = b["look"] == "dragon"
        self.face = art.make_face(random.Random(b["seed"]), "clown" if b.get("extra") == "clown" else "normaal")
        self.state = "idle"
        self.state_t = 1.5
        self.pattern_i = 0
        self.target = V()
        self.charge_dir = V()
        self.breath_t = 0.0

    @property
    def enraged(self):
        return self.hp < self.maxhp * 0.5

    def next_pattern(self, w):
        pats = self.b["patterns"]
        self.state = pats[self.pattern_i % len(pats)]
        self.pattern_i += 1
        p = w.player
        if self.state == "charge":
            self.state_t = 0.7
            self.charge_dir = unit(p.pos - self.pos)
        elif self.state == "slam":
            self.state_t = 0.9
            self.target = V(p.pos)
        elif self.state == "aimed":
            self.state_t = 0.4
        elif self.state == "spray":
            self.state_t = 0.5
        elif self.state == "breath":
            self.state_t = 0.5
            self.breath_t = 1.4
        elif self.state == "summon":
            self.state_t = 0.6

    def update(self, w, dt):
        self.t += dt
        self.hurt_t = max(0, self.hurt_t - dt)
        p = w.player
        to = p.pos - self.pos
        self.look = unit(to)
        speed_mult = 1.35 if self.enraged else 1.0
        self.state_t -= dt * speed_mult
        self.moving = False
        if self.state == "idle":
            if to.length() > 160:
                self.pos += unit(to) * self.speed * 0.6 * dt
                self.moving = True
            if self.state_t <= 0:
                self.next_pattern(w)
        elif self.state == "charge":
            if self.state_t <= 0:
                self.state = "charging"
                self.state_t = 0.55
                w.game.sfx.play("dash")
        elif self.state == "charging":
            self.pos += self.charge_dir * self.speed * 4.2 * dt
            self.moving = True
            if (p.pos - self.pos).length() < self.r + p.r:
                w.hurt_player(self.dmg * 1.2, self.pos)
            if self.state_t <= 0 or not w.bounds.inflate(-self.r * 2, -self.r * 2).collidepoint(self.pos):
                self.end_attack(0.9)
        elif self.state == "slam":
            if self.state_t <= 0:
                w.shockwave(self.target, 130, self.dmg * 1.3)
                if self.enraged:
                    w.shockwave(self.pos, 170, self.dmg)
                self.end_attack(1.0)
        elif self.state == "aimed":
            if self.state_t <= 0:
                n = 5 if self.enraged else 3
                for i in range(n):
                    ang = (i - (n - 1) / 2) * 12
                    w.add_proj(Proj(self.pos + self.look * self.r, self.look.rotate(ang) * 360, self.dmg * 0.8, 10,
                                    "enemy", (60, 30, 30)))
                w.game.sfx.play("shoot")
                self.end_attack(0.9)
        elif self.state == "spray":
            if self.state_t <= 0:
                n = 18 if self.enraged else 12
                off = random.uniform(0, 30)
                for i in range(n):
                    d = V(1, 0).rotate(i * 360 / n + off)
                    col = (250, 120, 30) if self.flying else (240, 60, 160)
                    w.add_proj(Proj(self.pos + d * self.r, d * 260, self.dmg * 0.7, 10, "enemy", col,
                                    "fire" if self.flying else "ball"))
                w.game.sfx.play("boom")
                self.end_attack(1.1)
        elif self.state == "breath":
            if self.state_t <= 0:
                self.breath_t -= dt
                if int(self.breath_t * 12) != int((self.breath_t + dt) * 12):
                    w.fire_breath(self.pos + self.look * self.r, self.look, self.dmg * 0.6, 2, 26, speed=380)
                if self.breath_t <= 0:
                    self.end_attack(1.0)
        elif self.state == "summon":
            if self.state_t <= 0:
                n = 3 if self.enraged else 2
                for i in range(n):
                    ang = random.uniform(0, 360)
                    pos = self.pos + V(1, 0).rotate(ang) * (self.r + 60)
                    pos.x = max(w.bounds.left + 40, min(w.bounds.right - 40, pos.x))
                    pos.y = max(w.bounds.top + 40, min(w.bounds.bottom - 40, pos.y))
                    e = Enemy(self.b["summon"], pos, w.level)
                    e.aggro = True
                    w.enemies.append(e)
                    w.fx_burst(pos, (200, 200, 255), 14, 200)
                self.end_attack(1.2)
        # aanraakschade
        if self.state not in ("charging",) and (p.pos - self.pos).length() < self.r + p.r - 4:
            w.hurt_player(self.dmg * 0.5, self.pos)
        self.pos += self.knock * dt
        self.knock *= max(0, 1 - 10 * dt)

    def end_attack(self, rest):
        self.state = "idle"
        self.state_t = rest * (0.7 if self.enraged else 1.0)

    def draw(self, s, cam):
        x, y = self.pos - cam
        hurt = self.hurt_t > 0
        # telegrafie
        if self.state == "charge":
            end = self.pos + self.charge_dir * 600 - cam
            pygame.draw.line(s, (255, 60, 60), (x, y), end, 4)
        if self.state == "slam":
            pulse = 1 - max(0, self.state_t) / 0.9
            tx, ty = self.target - cam
            pygame.draw.circle(s, (255, 60, 60), (int(tx), int(ty)), 130, 3)
            pygame.draw.circle(s, (255, 60, 60), (int(tx), int(ty)), int(130 * pulse), 0 if pulse > 0.95 else 2)
        if self.state in ("spray", "aimed", "summon", "breath") and self.state_t > 0:
            pygame.draw.circle(s, (255, 230, 80), (int(x), int(y)), int(self.r + 12 + math.sin(self.t * 30) * 4), 3)
        if self.b["look"] == "dragon":
            art.draw_dragon(s, x, y, self.r, self.t, (self.look.x, self.look.y), self.b["color"], hurt)
        else:
            art.draw_humanoid(s, x, y, self.r * 0.5, self.t, (self.look.x, self.look.y), self.b["shirt"], self.b["pants"],
                              self.face, self.b["hat"], self.moving, hurt, extra=self.b.get("extra"), scale=2.0)


# ------------------------------------------------------------------ wereld met gevechten
class CombatScene(Scene):
    aggro_range = 380

    def __init__(self, game, level, bounds):
        super().__init__(game)
        self.level = level
        self.bounds = pygame.Rect(bounds)
        self.player = Player(self.bounds.center)
        self.enemies = []
        self.projs = []
        self.particles = []
        self.texts = []
        self.pickups = []
        self.obstacles = []  # (V(pos), r)
        self.cam = V()
        self.shake = 0.0
        self.time = 0.0
        self.hint = ""

    @property
    def prof(self):
        return self.game.profile

    # ------------------------------------------------ helpers
    def add_proj(self, p):
        self.projs.append(p)

    def fx_burst(self, pos, color, n=10, speed=180, size=4, grav=0.0):
        for _ in range(n):
            d = V(1, 0).rotate(random.uniform(0, 360)) * random.uniform(0.3, 1) * speed
            self.particles.append(Particle(pos, d, random.uniform(0.25, 0.6), color, random.uniform(size * 0.5, size), grav))

    def float_text(self, pos, s, color, size=26):
        self.texts.append(FloatText(V(pos) + V(random.uniform(-10, 10), -20), s, color, size))

    def fire_breath(self, pos, direction, dmg, n, spread, speed=300):
        for i in range(n):
            ang = (i - (n - 1) / 2) * (spread / max(1, n - 1)) + random.uniform(-4, 4)
            self.add_proj(Proj(pos, direction.rotate(ang) * speed * random.uniform(0.9, 1.1), dmg, 9, "enemy",
                               (255, 130, 30), "fire", life=1.3))
        self.game.sfx.play("fire")

    def shockwave(self, pos, radius, dmg):
        self.fx_burst(pos, (220, 200, 160), 40, radius * 2.5, 7)
        self.shake = 0.35
        self.game.sfx.play("boom")
        if (self.player.pos - pos).length() < radius + self.player.r:
            self.hurt_player(dmg, pos)

    def hurt_player(self, dmg, src):
        p = self.player
        if p.inv > 0 or p.dash_t > 0 or self.prof.hp <= 0:
            return
        dmg = max(1, int(dmg))
        self.prof.hp -= dmg
        p.inv = 0.7
        p.pos += unit(p.pos - V(src)) * 18
        self.float_text(p.pos, f"-{dmg}", (255, 90, 90))
        self.shake = 0.2
        self.game.sfx.play("hurt")
        if self.prof.hp <= 0:
            self.prof.hp = 0
            self.on_player_dead()

    def on_player_dead(self):
        from .scenes import GameOver
        self.game.push(GameOver(self.game, self))

    def damage_enemy(self, e, base, knock_dir, knock=260):
        if e.dead:
            return
        mult = self.prof.dmg_mult
        if not e.is_boss and self.prof.researched(e.etype):
            mult *= 1.25
        crit = random.random() < 0.12
        dmg = base * mult * (2 if crit else 1) * random.uniform(0.9, 1.1)
        e.hp -= dmg
        e.hurt_t = 0.12
        e.knock += knock_dir * knock * (0.25 if e.is_boss else 1)
        e.aggro = True
        self.player.special = min(100, self.player.special + dmg * 0.25)
        self.float_text(e.pos - V(0, e.r), f"{int(dmg)}{'!' if crit else ''}", GOLD if crit else WHITE, 32 if crit else 24)
        self.fx_burst(e.pos, (255, 240, 180), 6, 160)
        self.game.sfx.play("crit" if crit else "hit")
        if e.hp <= 0:
            self.kill_enemy(e)

    def kill_enemy(self, e):
        e.dead = True
        self.fx_burst(e.pos, (255, 220, 120), 24, 260, 6)
        if e.is_boss:
            self.on_boss_dead(e)
            return
        prof = self.prof
        before = prof.kills.get(e.etype, 0)
        prof.kills[e.etype] = before + 1
        if before + 1 == RESEARCH_KILLS:
            self.game.toast(f"Onderzoek voltooid: {e.d['name']}! +25% schade tegen deze soort", (120, 220, 255))
            self.game.sfx.play("clue")
        n = max(1, e.reward // 10)
        for i in range(n):
            self.pickups.append(Pickup(e.pos, "coin", e.reward // n))
        if random.random() < 0.12:
            self.pickups.append(Pickup(e.pos, "meat", 1))
        check_challenges(self.game)

    def on_boss_dead(self, boss):
        pass

    # ------------------------------------------------ speler-aanval
    def player_attack(self):
        p = self.player
        if p.atk_cd > 0:
            return
        wid = self.prof.weapon
        wd = WEAPONS[wid]
        p.atk_cd = wd["cd"]
        p.atk_kind = wd["kind"]
        p.atk_dir = V(p.aim)
        p.hitset = set()
        self.game.sfx.play("swing")
        if wd["kind"] == "stretch":
            p.atk_len = 0.2
        elif wd["kind"] in ("arc", "spin"):
            p.atk_len = 0.16
            for e in self.enemies:
                to = e.pos - p.pos
                if to.length() > wd["range"] + e.r:
                    continue
                if wd["kind"] == "arc" and to.length() > e.r + 10:
                    ang = (p.atk_dir.angle_to(to) + 180) % 360 - 180
                    if abs(ang) > wd["arc"] / 2:
                        continue
                self.damage_enemy(e, wd["dmg"], unit(to))
        elif wd["kind"] in ("shot", "bolt"):
            p.atk_len = 0.1
            bolt = wd["kind"] == "bolt"
            self.add_proj(Proj(p.pos + p.atk_dir * 20, p.atk_dir * wd["speed"], wd["dmg"], 12 if bolt else 7, "player",
                               wd["color"], "bolt" if bolt else "rock", pierce=bolt, life=1.2))
            self.game.sfx.play("shoot")
        p.atk_t = p.atk_len

    def special_attack(self):
        p = self.player
        if p.special < 100:
            self.game.toast("Speciale aanval laadt nog op (raak vijanden!)", (200, 200, 200))
            return
        p.special = 0
        p.special_t = 0.9
        self.game.sfx.play("special")
        self.float_text(p.pos - V(0, 60), "GOMU GOMU NO... GATLING!", GOLD, 36)
        self.shake = 0.4
        base = max(WEAPONS[self.prof.weapon]["dmg"], 10) * 2.2 + 20
        for e in list(self.enemies):
            to = e.pos - p.pos
            if to.length() < 280 + e.r:
                self.damage_enemy(e, base, unit(to), 500)

    # ------------------------------------------------ update
    def mouse_world(self):
        return V(pygame.mouse.get_pos()) + self.cam

    def handle_combat_event(self, e):
        p = self.player
        if e.type == pygame.MOUSEMOTION:
            p.mouse_t = self.time
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_SPACE, pygame.K_j):
                self.player_attack()
            elif e.key in (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_k):
                self.dash()
            elif e.key == pygame.K_r:
                self.special_attack()
            elif e.key == pygame.K_f:
                self.eat()
            elif pygame.K_1 <= e.key <= pygame.K_6:
                idx = e.key - pygame.K_1
                wid = WEAPON_ORDER[idx]
                if wid in self.prof.weapons:
                    self.prof.weapon = wid
                    self.game.toast(f"Wapen: {WEAPONS[wid]['name']}", WHITE)
                    self.game.sfx.play("select")
        if e.type == pygame.MOUSEBUTTONDOWN:
            p.mouse_t = self.time
            if e.button == 1:
                self.player_attack()
            elif e.button == 3:
                self.dash()

    def dash(self):
        p = self.player
        if p.dash_cd > 0:
            return
        p.dash_cd = 0.75
        p.dash_t = 0.18
        p.dash_dir = V(p.facing)
        self.game.sfx.play("dash")

    def eat(self):
        prof = self.prof
        if prof.meat <= 0:
            self.game.toast("Geen vlees meer! Koop het in de winkel.", (220, 180, 180))
            return
        if prof.hp >= prof.max_hp:
            self.game.toast("Je HP is al vol.", WHITE)
            return
        prof.meat -= 1
        heal = int(prof.max_hp * 0.45)
        prof.hp = min(prof.max_hp, prof.hp + heal)
        self.float_text(self.player.pos, f"+{heal} HP  *smak*", GREEN)
        self.game.sfx.play("coin")

    def update_combat(self, dt):
        self.time += dt
        p = self.player
        p.t += dt
        keys = pygame.key.get_pressed()
        mv = V(
            (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_q] or keys[pygame.K_LEFT]),
            (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_z] or keys[pygame.K_UP]),
        )
        p.moving = mv.length_squared() > 0
        if p.moving:
            p.facing = unit(mv)
        if self.time - p.mouse_t < 3.0:
            p.aim = unit(self.mouse_world() - p.pos)
        else:
            p.aim = V(p.facing)
        for attr in ("atk_cd", "atk_t", "dash_cd", "dash_t", "inv", "special_t"):
            setattr(p, attr, max(0.0, getattr(p, attr) - dt))
        if p.dash_t > 0:
            p.pos += p.dash_dir * 1100 * dt
            if random.random() < 0.6:
                self.particles.append(Particle(p.pos, V(), 0.25, (250, 250, 250), 6))
        elif p.moving:
            p.pos += unit(mv) * self.prof.speed * dt
        # rubberarm raakt alles op de lijn
        if p.atk_t > 0 and p.atk_kind == "stretch":
            wd = WEAPONS[self.prof.weapon]
            prog = 1 - abs(p.atk_t / p.atk_len * 2 - 1)
            tip = p.pos + p.atk_dir * (20 + wd["range"] * prog)
            for e in self.enemies:
                if id(e) in p.hitset:
                    continue
                if seg_dist(p.pos, tip, e.pos) < e.r + 10:
                    p.hitset.add(id(e))
                    self.damage_enemy(e, wd["dmg"], p.atk_dir)
        # vijanden
        for e in self.enemies:
            e.update(self, dt)
        self.enemies = [e for e in self.enemies if not e.dead]
        # botsingen
        self.resolve(p.pos, p.r)
        for e in self.enemies:
            if not e.flying:
                self.resolve(e.pos, e.r)
            self.clamp(e.pos, e.r)
            if not e.is_boss:
                for o in self.enemies:
                    if o is not e and not o.is_boss:
                        d = e.pos - o.pos
                        if 0 < d.length() < e.r + o.r:
                            e.pos += unit(d) * (e.r + o.r - d.length()) * 0.5
        self.clamp(p.pos, p.r)
        # projectielen
        for pr in self.projs:
            pr.pos += pr.vel * dt
            pr.life -= dt
            if pr.kind == "fire":
                pr.r = min(18, pr.r + dt * 10)
            if pr.life <= 0 or not self.bounds.inflate(200, 200).collidepoint(pr.pos):
                pr.dead = True
                continue
            if pr.kind != "fire" and any((pr.pos - o).length() < r for o, r in self.obstacles):
                pr.dead = True
                self.fx_burst(pr.pos, pr.color, 4, 80)
                continue
            if pr.owner == "enemy":
                if (pr.pos - p.pos).length() < pr.r + p.r - 4:
                    self.hurt_player(pr.dmg, pr.pos)
                    pr.dead = True
            else:
                for e in self.enemies:
                    if id(e) in pr.hit:
                        continue
                    if (pr.pos - e.pos).length() < pr.r + e.r:
                        pr.hit.add(id(e))
                        self.damage_enemy(e, pr.dmg, unit(pr.vel), 160)
                        if not pr.pierce:
                            pr.dead = True
                            break
        self.projs = [x for x in self.projs if not x.dead]
        # pickups
        for pk in self.pickups:
            pk.t += dt
            pk.pos += pk.vel * dt
            pk.vel *= max(0, 1 - 5 * dt)
            d = p.pos - pk.pos
            if pk.t > 0.4 and d.length() < 150:
                pk.pos += unit(d) * 420 * dt
            if pk.t > 0.3 and d.length() < p.r + 10:
                pk.t = -99
                if pk.kind == "coin":
                    self.prof.berries += pk.value
                    self.game.sfx.play("coin")
                else:
                    self.prof.meat += 1
                    self.float_text(p.pos, "+1 vlees", (240, 160, 120))
        self.pickups = [x for x in self.pickups if x.t > -50 and x.t < 25]
        # effecten
        for pa in self.particles:
            pa.pos += pa.vel * dt
            pa.vel *= max(0, 1 - 4 * dt)
            pa.vel.y += pa.grav * dt
            pa.life -= dt
        self.particles = [x for x in self.particles if x.life > 0]
        for ft in self.texts:
            ft.pos.y -= 50 * dt
            ft.life -= dt
        self.texts = [x for x in self.texts if x.life > 0]
        self.shake = max(0, self.shake - dt)

    def resolve(self, pos, r):
        for o, orad in self.obstacles:
            d = pos - o
            dl = d.length()
            if dl < r + orad:
                pos += unit(d) * (r + orad - dl)

    def clamp(self, pos, r):
        pos.x = max(self.bounds.left + r, min(self.bounds.right - r, pos.x))
        pos.y = max(self.bounds.top + r, min(self.bounds.bottom - r, pos.y))

    # ------------------------------------------------ tekenen
    def shake_off(self):
        if self.shake > 0:
            return V(random.uniform(-6, 6), random.uniform(-6, 6))
        return V()

    def draw_entities(self, s, cam, extra=()):
        p = self.player
        items = [(e.pos.y, e.draw) for e in self.enemies]
        items.append((p.pos.y, self.draw_player))
        items.extend(extra)
        for pk in self.pickups:
            x, y = pk.pos - cam
            if pk.kind == "coin":
                pygame.draw.circle(s, GOLD, (int(x), int(y)), 7)
                pygame.draw.circle(s, (160, 110, 20), (int(x), int(y)), 7, 2)
            else:
                pygame.draw.ellipse(s, (180, 80, 60), (x - 9, y - 6, 18, 12))
                pygame.draw.line(s, (250, 250, 240), (x + 6, y), (x + 13, y - 5), 4)
        for _, fn in sorted(items, key=lambda it: it[0]):
            fn(s, cam)
        for pr in self.projs:
            x, y = pr.pos - cam
            if pr.kind == "fire":
                pygame.draw.circle(s, (255, 90, 20), (int(x), int(y)), int(pr.r))
                pygame.draw.circle(s, (255, 220, 80), (int(x), int(y)), int(pr.r * 0.55))
            elif pr.kind == "bolt":
                tail = pr.pos - unit(pr.vel) * 30 - cam
                pygame.draw.line(s, (200, 230, 255), tail, (x, y), 8)
                pygame.draw.line(s, (255, 255, 255), tail, (x, y), 3)
            else:
                pygame.draw.circle(s, pr.color, (int(x), int(y)), int(pr.r))
                pygame.draw.circle(s, (0, 0, 0), (int(x), int(y)), int(pr.r), 1)
        for pa in self.particles:
            x, y = pa.pos - cam
            sz = max(1, int(pa.size * pa.life / pa.max))
            pygame.draw.circle(s, pa.color, (int(x), int(y)), sz)
        for ft in self.texts:
            x, y = ft.pos - cam
            text(s, ft.s, ft.size, ft.color, (x, y), "center", bold=True)

    def draw_player(self, s, cam):
        p = self.player
        x, y = p.pos - cam
        if p.inv > 0 and int(p.inv * 20) % 2 == 0:
            return
        wd = WEAPONS[self.prof.weapon]
        if p.special_t > 0:
            for i in range(10):
                d = V(1, 0).rotate(random.uniform(0, 360)) * random.uniform(40, 270)
                pygame.draw.circle(s, (245, 205, 165), (int(x + d.x), int(y + d.y)), 13)
                pygame.draw.circle(s, (0, 0, 0), (int(x + d.x), int(y + d.y)), 13, 2)
        art.draw_hero(s, x, y, p.t, (p.aim.x, p.aim.y), p.moving)
        if p.atk_t > 0:
            prog = 1 - abs(p.atk_t / p.atk_len * 2 - 1) if p.atk_len else 0
            if p.atk_kind == "stretch":
                tip = V(x, y) + p.atk_dir * (20 + wd["range"] * prog)
                pygame.draw.line(s, (245, 205, 165), (x, y), tip, 9)
                pygame.draw.line(s, (210, 40, 40), (x, y), V(x, y) + p.atk_dir * 14, 11)
                pygame.draw.circle(s, (245, 205, 165), (int(tip.x), int(tip.y)), 13)
                pygame.draw.circle(s, (0, 0, 0), (int(tip.x), int(tip.y)), 13, 2)
            elif p.atk_kind == "arc":
                ang = -math.degrees(math.atan2(p.atk_dir.y, p.atk_dir.x))
                rect = pygame.Rect(0, 0, wd["range"] * 2, wd["range"] * 2)
                rect.center = (x, y)
                a0 = math.radians(ang - wd["arc"] / 2)
                a1 = math.radians(ang + wd["arc"] / 2)
                pygame.draw.arc(s, wd["color"], rect, a0, a1, 10)
                pygame.draw.arc(s, (255, 255, 255), rect.inflate(-14, -14), a0, a1, 3)
            elif p.atk_kind == "spin":
                pygame.draw.circle(s, (255, 255, 255), (int(x), int(y)), int(wd["range"] * (0.5 + prog * 0.5)), 5)
                pygame.draw.circle(s, (255, 150, 40), (int(x), int(y)), int(wd["range"] * (0.4 + prog * 0.5)), 3)

    def draw_hud(self, s):
        prof = self.prof
        panel(s, (12, 12, 330, 112), alpha=200)
        ready = self.player.special >= 100
        if ready and int(self.time * 4) % 2 == 0:
            text(s, "R: SPECIALE AANVAL KLAAR!", 22, GOLD, (24, 130), bold=True)
        text(s, "HP", 24, WHITE, (24, 24), bold=True)
        bar(s, (60, 24, 268, 18), prof.hp / prof.max_hp, GREEN if prof.hp > prof.max_hp * 0.3 else RED)
        text(s, f"{prof.hp}/{prof.max_hp}", 20, WHITE, (194, 33), "center")
        text(s, "SP", 24, WHITE, (24, 50), bold=True)
        bar(s, (60, 50, 268, 12), self.player.special / 100, GOLD if ready else (200, 160, 60))
        text(s, f"Berries: {prof.berries}", 24, GOLD, (24, 72), bold=True)
        text(s, f"Vlees: {prof.meat} (F)", 22, (240, 170, 140), (200, 73))
        text(s, f"Kracht {prof.str_lvl}  HP-lvl {prof.hp_lvl}  Snelheid {prof.spd_lvl}", 20, (200, 220, 255), (24, 98))
        # wapens
        x0 = W // 2 - 3 * 64
        for i, wid in enumerate(WEAPON_ORDER):
            r = pygame.Rect(x0 + i * 64, H - 70, 58, 58)
            owned = wid in prof.weapons
            panel(s, r, color=(30, 40, 70) if owned else (25, 25, 25), alpha=210,
                  border=GOLD if prof.weapon == wid else (90, 90, 100), radius=8, width=3 if prof.weapon == wid else 1)
            text(s, str(i + 1), 18, WHITE, (r.x + 5, r.y + 3))
            if owned:
                draw_weapon_icon(s, wid, r.center)
            else:
                text(s, "?", 30, (90, 90, 90), r.center, "center")
        text(s, WEAPONS[prof.weapon]["name"], 22, WHITE, (W // 2, H - 84), "midbottom", bold=True)


def seg_dist(a, b, p):
    ab = b - a
    if ab.length_squared() == 0:
        return (p - a).length()
    t = max(0, min(1, (p - a).dot(ab) / ab.length_squared()))
    return (p - (a + ab * t)).length()


def draw_weapon_icon(s, wid, c, scale=1.0):
    x, y = c
    k = scale
    col = WEAPONS[wid]["color"]
    if wid == "vuist":
        pygame.draw.circle(s, col, (x, y), int(14 * k))
        pygame.draw.circle(s, (0, 0, 0), (x, y), int(14 * k), 2)
        for i in range(3):
            pygame.draw.line(s, (0, 0, 0), (x - 8 * k + i * 6 * k, y - 10 * k), (x - 8 * k + i * 6 * k, y - 2 * k), 1)
    elif wid in ("zwaard", "driezwaard"):
        n = 3 if wid == "driezwaard" else 1
        for i in range(n):
            off = (i - (n - 1) / 2) * 8 * k
            pygame.draw.line(s, col, (x - 14 * k + off, y + 14 * k), (x + 12 * k + off, y - 14 * k), max(2, int(5 * k)))
            pygame.draw.line(s, (60, 40, 20), (x - 14 * k + off, y + 14 * k), (x - 8 * k + off, y + 8 * k), max(2, int(6 * k)))
    elif wid == "katapult":
        pygame.draw.line(s, col, (x, y + 16 * k), (x, y), max(2, int(5 * k)))
        pygame.draw.line(s, col, (x, y), (x - 10 * k, y - 14 * k), max(2, int(4 * k)))
        pygame.draw.line(s, col, (x, y), (x + 10 * k, y - 14 * k), max(2, int(4 * k)))
        pygame.draw.line(s, (200, 60, 60), (x - 10 * k, y - 14 * k), (x + 10 * k, y - 14 * k), 2)
    elif wid == "trap":
        pygame.draw.polygon(s, (30, 30, 30), [(x - 6 * k, y - 16 * k), (x + 4 * k, y - 16 * k), (x + 4 * k, y + 6 * k),
                                              (x + 16 * k, y + 8 * k), (x + 16 * k, y + 16 * k), (x - 6 * k, y + 16 * k)])
        pygame.draw.line(s, (255, 150, 40), (x - 16 * k, y), (x - 8 * k, y - 4 * k), 3)
    elif wid == "staf":
        pygame.draw.line(s, (90, 90, 120), (x - 12 * k, y + 16 * k), (x + 12 * k, y - 16 * k), max(2, int(5 * k)))
        pygame.draw.circle(s, col, (int(x + 12 * k), int(y - 16 * k)), int(6 * k))
