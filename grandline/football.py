"""Voetbal-minigame: scoor goals voor Berries (en een aanwijzing in Clownstad)."""
import math
import random

import pygame
from pygame.math import Vector2 as V

from . import art
from .core import Scene, check_challenges, dim, panel, tap_pos, text
from .settings import GOLD, H, ISLANDS, W, WHITE

FIELD = pygame.Rect(70, 110, W - 140, H - 160)
GOAL_H = 160
MATCH_TIME = 90.0


def unit(v):
    return v.normalize() if v.length_squared() > 1e-6 else V(1, 0)


class Footballer:
    def __init__(self, pos, team, role, face, shirt, pants, speed):
        self.pos = V(pos)
        self.home = V(pos)
        self.team, self.role = team, role  # team 0 = speler (links->rechts), 1 = tegenstander
        self.face, self.shirt, self.pants = face, shirt, pants
        self.speed = speed
        self.r = 16
        self.kick_cd = 0.0
        self.look = V(1 if team == 0 else -1, 0)
        self.moving = False
        self.t = random.uniform(0, 5)
        self.stun = 0.0


class FootballScene(Scene):
    def __init__(self, game, idx, island):
        super().__init__(game)
        self.idx = idx
        self.island = island
        prof = game.profile
        self.diff = idx
        self.reward_goal = 30 + 15 * idx
        self.reward_win = 100 + 60 * idx
        rnd = random.Random()
        opp_speed = 200 + 18 * idx
        tm_speed = 205 + 10 * idx
        self.players = []
        self.me = Footballer((FIELD.centerx - 200, FIELD.centery), 0, "me", art.HERO_FACE, (210, 40, 40), (60, 100, 200),
                             prof.speed * 0.95)
        self.players.append(self.me)
        tm_face = art.make_face(random.Random(5))
        tm_face.update(eyes="twee", nose="lang", mouth="grijns", hair=(30, 25, 20), skin=(190, 140, 100))
        self.players.append(Footballer((FIELD.centerx - 260, FIELD.centery + 140), 0, "mid", tm_face, (230, 200, 60),
                                       (60, 60, 60), tm_speed))
        self.players.append(Footballer((FIELD.left + 30, FIELD.centery), 0, "keeper", art.make_face(random.Random(9)),
                                       (60, 180, 90), (40, 40, 40), 190))
        style = "clown" if ISLANDS[idx]["decor"] == "circus" else ("vis" if ISLANDS[idx]["decor"] == "koraal" else "normaal")
        opp_shirt = [(130, 85, 50), (240, 240, 245), (230, 80, 160), (90, 90, 90), (60, 120, 170)][idx]
        for i, (pos, role) in enumerate([((FIELD.centerx + 200, FIELD.centery - 80), "att"),
                                         ((FIELD.centerx + 260, FIELD.centery + 120), "mid"),
                                         ((FIELD.right - 30, FIELD.centery), "keeper")]):
            self.players.append(Footballer(pos, 1, role, art.make_face(rnd, style), opp_shirt, (40, 40, 60),
                                           opp_speed if role != "keeper" else 170 + 15 * idx))
        self.ball = V(FIELD.center)
        self.bvel = V()
        self.score = [0, 0]
        self.time_left = MATCH_TIME
        self.pause_t = 2.0
        self.msg = "Aftrap!"
        self.t = 0.0
        self.over = False
        self.over_t = 0.0
        self.particles = []
        self.charge = 0.0
        self.charging = False
        self.sprint_cd = 0.0
        self.sprint_t = 0.0
        game.sfx.play("whistle")

    # ------------------------------------------------------------------
    def reset_positions(self, conceded_team):
        for p in self.players:
            p.pos = V(p.home)
            p.stun = 0
        self.ball = V(FIELD.center)
        self.bvel = V()
        # team dat tegen kreeg mag aftrappen: schuif zijn spits naar de bal
        kicker = self.me if conceded_team == 0 else next(p for p in self.players if p.team == 1 and p.role == "att")
        kicker.pos = V(FIELD.center) + V(-30 if kicker.team == 0 else 30, 0)
        self.pause_t = 1.5

    def handle(self, e):
        if self.over:
            # tik pas na 0,8 s: een muisklik/tik om te schieten mag het eindscherm niet meteen wegklikken
            tapped = tap_pos(e) and self.t - self.over_t > 0.8
            if tapped or (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e,
                                                                 pygame.K_ESCAPE)):
                self.game.pop()
            return
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                from .scenes import Confirm
                self.game.push(Confirm(self.game, "Wedstrijd opgeven? (verlies)", self.forfeit))
            elif e.key in (pygame.K_SPACE, pygame.K_j):
                self.charging = True
                self.charge = 0.0
            elif e.key in (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_k):
                if self.sprint_cd <= 0:
                    self.sprint_t = 1.2
                    self.sprint_cd = 3.0
                    self.game.sfx.play("dash")
        if e.type == pygame.KEYUP and e.key in (pygame.K_SPACE, pygame.K_j) and self.charging:
            self.charging = False
            self.try_kick(self.me, unit(self.me.look), 420 + 520 * min(1, self.charge))
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.charging = True
            self.charge = 0.0
        if e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.charging:
            self.charging = False
            d = unit(V(e.pos) - self.me.pos)
            self.try_kick(self.me, d, 420 + 520 * min(1, self.charge))

    def forfeit(self):
        self.score[1] = max(self.score[1], self.score[0] + 1)
        self.time_left = 0
        self.finish()

    def try_kick(self, p, direction, power):
        if p.kick_cd > 0 or p.stun > 0:
            return False
        if (self.ball - p.pos).length() > p.r + 12 + 14:
            return False
        self.bvel = unit(direction) * power
        p.kick_cd = 0.35
        self.game.sfx.play("kick")
        return True

    # ------------------------------------------------------------------
    def goal_target(self, team):
        x = FIELD.right if team == 0 else FIELD.left
        return V(x, FIELD.centery + random.uniform(-GOAL_H * 0.35, GOAL_H * 0.35))

    def ai(self, p, dt):
        own_goal = V(FIELD.left if p.team == 0 else FIELD.right, FIELD.centery)
        to_ball = self.ball - p.pos
        dir_x = 1 if p.team == 0 else -1
        target = V(p.home)
        if p.role == "keeper":
            y = max(FIELD.centery - GOAL_H / 2 + 10, min(FIELD.centery + GOAL_H / 2 - 10, self.ball.y))
            target = V(own_goal.x + dir_x * 30, y)
            if to_ball.length() < 150 and abs(self.ball.x - own_goal.x) < 200:
                target = V(self.ball)
            # keeper reflex groeit met moeilijkheid
            if to_ball.length() < p.r + 26 and p.kick_cd <= 0:
                aim = V(dir_x, random.uniform(-0.6, 0.6))
                self.try_kick(p, aim, 600)
        else:
            closest = min((q for q in self.players if q.team == p.team and q.role != "keeper"),
                          key=lambda q: (q.pos - self.ball).length())
            chase = closest is p or (p.role == "att" and to_ball.length() < 260)
            if p.team == 0 and p is not self.me:
                chase = (p.pos - self.ball).length() < (self.me.pos - self.ball).length() - 40
            if chase:
                # loop achter de bal, richting doel
                goal = self.goal_target(p.team)
                behind = self.ball - unit(goal - self.ball) * (p.r + 8)
                target = behind if (p.pos - behind).length() > 14 else V(self.ball)
                if to_ball.length() < p.r + 22 and p.kick_cd <= 0:
                    dist_goal = (goal - self.ball).length()
                    if dist_goal < 420 or random.random() < 0.02 + 0.01 * self.diff:
                        acc = max(0.05, 0.35 - 0.06 * self.diff)
                        aim = unit(goal - self.ball).rotate(random.uniform(-acc, acc) * 57)
                        self.try_kick(p, aim, 620 + 60 * self.diff)
                    else:
                        # dribbel: korte tik vooruit
                        self.try_kick(p, unit(goal - self.ball).rotate(random.uniform(-25, 25)), 260)
                        p.kick_cd = 0.25
            else:
                # positie houden: tussen bal en eigen doel, of vrijlopen
                if p.role == "mid":
                    target = V((self.ball.x + own_goal.x) / 2 + dir_x * 120, p.home.y * 0.5 + self.ball.y * 0.5)
                else:
                    target = V(self.ball.x + dir_x * 160, FIELD.centery + (p.home.y - FIELD.centery))
        mv = target - p.pos
        if mv.length() > 6:
            p.pos += unit(mv) * min(p.speed * dt, mv.length())
            p.moving = True
            p.look = unit(mv)
        else:
            p.moving = False
            p.look = unit(to_ball)

    def update(self, dt):
        self.t += dt
        for pa in self.particles:
            pa[0] += pa[1] * dt
            pa[2] -= dt
        self.particles = [pa for pa in self.particles if pa[2] > 0]
        if self.over:
            return
        if self.charging:
            self.charge += dt * 1.4
        if self.pause_t > 0:
            self.pause_t -= dt
            return
        self.msg = ""
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.finish()
            return
        self.sprint_cd -= dt
        self.sprint_t -= dt
        for p in self.players:
            p.t += dt
            p.kick_cd -= dt
            p.stun -= dt
        # speler
        keys = pygame.key.get_pressed()
        mv = V((keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_q] or keys[pygame.K_LEFT]),
               (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_z] or keys[pygame.K_UP]))
        if mv.length_squared() == 0:
            mv = V(self.game.touch.move)  # touch-joystick als er geen toets is ingedrukt
        me = self.me
        me.moving = mv.length_squared() > 0
        if me.moving:
            sp = me.speed * (1.55 if self.sprint_t > 0 else 1.0) * (0.75 if self.charging else 1)
            me.pos += unit(mv) * sp * dt
            me.look = unit(mv)
            # dribbelen: bal plakt licht aan de voet
            d = self.ball - me.pos
            if d.length() < me.r + 16 and self.bvel.length() < 260 and not self.charging:
                self.bvel = unit(mv) * sp * 1.15
        for p in self.players:
            if p is not me:
                self.ai(p, dt)
        # botsing spelers
        for a in self.players:
            for b in self.players:
                if a is b:
                    continue
                d = a.pos - b.pos
                if 0 < d.length() < a.r + b.r:
                    a.pos += unit(d) * (a.r + b.r - d.length()) * 0.5
            a.pos.x = max(FIELD.left - 30, min(FIELD.right + 30, a.pos.x))
            a.pos.y = max(FIELD.top + a.r, min(FIELD.bottom - a.r, a.pos.y))
        # bal
        self.ball += self.bvel * dt
        self.bvel *= max(0, 1 - 1.3 * dt)
        for p in self.players:
            d = self.ball - p.pos
            if 0 < d.length() < p.r + 10:
                self.ball = p.pos + unit(d) * (p.r + 10)
                if self.bvel.length() < 120:
                    self.bvel = unit(d) * 120
        in_goal_y = abs(self.ball.y - FIELD.centery) < GOAL_H / 2
        if self.ball.x < FIELD.left:
            if in_goal_y:
                return self.goal(1)
            self.ball.x = FIELD.left
            self.bvel.x *= -0.7
        if self.ball.x > FIELD.right:
            if in_goal_y:
                return self.goal(0)
            self.ball.x = FIELD.right
            self.bvel.x *= -0.7
        if self.ball.y < FIELD.top + 10 or self.ball.y > FIELD.bottom - 10:
            self.ball.y = max(FIELD.top + 10, min(FIELD.bottom - 10, self.ball.y))
            self.bvel.y *= -0.7

    def goal(self, team):
        self.score[team] += 1
        prof = self.game.profile
        if team == 0:
            prof.goals += 1
            prof.berries += self.reward_goal
            self.msg = f"GOAAAL!  +{self.reward_goal} Berries"
            self.game.sfx.play("goal")
            for _ in range(60):
                self.particles.append([V(FIELD.right, FIELD.centery),
                                       V(1, 0).rotate(random.uniform(90, 270)) * random.uniform(80, 400),
                                       random.uniform(0.6, 1.4),
                                       random.choice([GOLD, (255, 80, 80), (80, 160, 255), WHITE])])
        else:
            self.msg = "Tegendoelpunt..."
            self.game.sfx.play("wrong")
        self.reset_positions(1 - team)
        check_challenges(self.game)

    def finish(self):
        if self.over:
            return
        self.over = True
        self.over_t = self.t
        prof = self.game.profile
        prof.matches += 1
        prof.best_match_goals = max(prof.best_match_goals, self.score[0])
        self.won = self.score[0] > self.score[1]
        self.game.sfx.play("whistle")
        self.result_lines = [f"Doelpunten: {self.score[0]} x {self.reward_goal} = {self.score[0] * self.reward_goal} Berries"]
        if self.won:
            prof.wins += 1
            prof.berries += self.reward_win
            self.result_lines.append(f"Winstbonus: +{self.reward_win} Berries")
            if self.idx not in prof.football_won:
                prof.football_won.append(self.idx)
                if ISLANDS[self.idx].get("football_clue"):
                    self.result_lines.append("De clownpiraten geven toe: zoek nu de laatste ?-plek!")
        elif self.score[0] == self.score[1]:
            self.result_lines.append("Gelijkspel: geen bonus. Probeer opnieuw!")
        else:
            self.result_lines.append("Verloren... Train meer snelheid in de winkel!")
        check_challenges(self.game)
        prof.save()

    # ------------------------------------------------------------------
    def draw(self, s):
        s.fill((40, 120, 50))
        for i in range(12):
            r = pygame.Rect(FIELD.x + i * FIELD.w / 12, FIELD.y, FIELD.w / 12 + 1, FIELD.h)
            pygame.draw.rect(s, (70, 160, 70) if i % 2 else (80, 175, 80), r)
        pygame.draw.rect(s, WHITE, FIELD, 4)
        pygame.draw.line(s, WHITE, FIELD.midtop, FIELD.midbottom, 4)
        pygame.draw.circle(s, WHITE, FIELD.center, 80, 4)
        for side, d in ((FIELD.left, -1), (FIELD.right, 1)):
            pygame.draw.rect(s, WHITE, (side - (130 if d > 0 else 0), FIELD.centery - 140, 130, 280), 3)
            gx = side if d > 0 else side - 36
            net = pygame.Rect(gx, FIELD.centery - GOAL_H / 2, 36, GOAL_H)
            pygame.draw.rect(s, (220, 220, 220), net)
            for i in range(0, GOAL_H, 12):
                pygame.draw.line(s, (170, 170, 170), (net.left, net.top + i), (net.right, net.top + i))
            pygame.draw.rect(s, WHITE, net, 5)
        for p in sorted(self.players, key=lambda q: q.pos.y):
            art.draw_humanoid(s, p.pos.x, p.pos.y, p.r, p.t, (p.look.x, p.look.y), p.shirt, p.pants, p.face,
                              None, p.moving)
            if p is self.me:
                art.draw_hat(s, p.pos.x, p.pos.y - p.r * 0.85 - p.r * 0.85 * 0.85, p.r * 0.85, "stro", p.t)
                pygame.draw.polygon(s, GOLD, [(p.pos.x - 8, p.pos.y - 62), (p.pos.x + 8, p.pos.y - 62), (p.pos.x, p.pos.y - 52)])
            elif p.role == "keeper":
                pygame.draw.circle(s, (255, 255, 255), (int(p.pos.x), int(p.pos.y + 4)), 6, 2)
        # bal
        bx, by = self.ball
        pygame.draw.ellipse(s, (0, 0, 0, 90), (bx - 9, by + 4, 18, 8))
        pygame.draw.circle(s, WHITE, (int(bx), int(by)), 10)
        ang = self.t * self.bvel.length() * 0.02
        for i in range(3):
            a = ang + i * 2.1
            pygame.draw.circle(s, (20, 20, 20), (int(bx + math.cos(a) * 5), int(by + math.sin(a) * 5)), 3)
        pygame.draw.circle(s, (0, 0, 0), (int(bx), int(by)), 10, 1)
        if self.charging:
            me = self.me
            c = min(1, self.charge)
            pygame.draw.rect(s, (0, 0, 0), (me.pos.x - 26, me.pos.y + 28, 52, 9))
            pygame.draw.rect(s, (255, int(220 - 160 * c), 40), (me.pos.x - 25, me.pos.y + 29, 50 * c, 7))
        for pa in self.particles:
            pygame.draw.circle(s, pa[3], (int(pa[0].x), int(pa[0].y)), 4)
        # scorebord
        panel(s, (W // 2 - 230, 12, 460, 76), alpha=220)
        text(s, f"STROHOED  {self.score[0]} - {self.score[1]}  PIRATEN", 36, WHITE, (W // 2, 36), "center", bold=True)
        m, sec = divmod(int(math.ceil(self.time_left)), 60)
        text(s, f"{m}:{sec:02d}", 28, GOLD, (W // 2, 68), "center", bold=True)
        text(s, "Spatie ingedrukt houden = harder schieten   Shift = sprint", 20, WHITE, (20, 20))
        text(s, f"Goal = +{self.reward_goal}  Winst = +{self.reward_win} Berries", 20, GOLD, (20, 44))
        if self.msg:
            text(s, self.msg, 64, GOLD, (W // 2, H // 2 - 40), "center", bold=True)
        if self.over:
            dim(s, 150)
            panel(s, (W // 2 - 330, H // 2 - 150, 660, 300))
            title = "GEWONNEN!" if self.won else ("GELIJKSPEL" if self.score[0] == self.score[1] else "VERLOREN")
            text(s, title, 64, GOLD if self.won else WHITE, (W // 2, H // 2 - 100), "center", bold=True)
            text(s, f"{self.score[0]} - {self.score[1]}", 44, WHITE, (W // 2, H // 2 - 45), "center", bold=True)
            for i, line in enumerate(self.result_lines):
                text(s, line, 26, WHITE, (W // 2, H // 2 + 5 + i * 32), "center")
            text(s, "Druk op Enter", 24, (200, 200, 200), (W // 2, H // 2 + 125), "center")
