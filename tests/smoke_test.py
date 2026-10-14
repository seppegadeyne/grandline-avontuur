"""Headless rooktest: doorloopt alle scènes en simuleert gameplay.

Draai met:  uv run python tests/smoke_test.py [screenshot-map]
"""
import os
import random
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["XDG_DATA_HOME"] = tempfile.mkdtemp(prefix="grandline-test-")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame  # noqa: E402
from pygame.math import Vector2 as V  # noqa: E402

from grandline import scenes, world  # noqa: E402
from grandline.core import Profile  # noqa: E402
from grandline.football import FootballScene  # noqa: E402
from grandline.main import Game  # noqa: E402
from grandline.settings import ISLANDS, WEAPON_ORDER  # noqa: E402

SHOTS = sys.argv[1] if len(sys.argv) > 1 else None
random.seed(3)


def key(k, up=False):
    return pygame.event.Event(pygame.KEYUP if up else pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


def run(g, seconds, events_fn=None, dt=1 / 60):
    for i in range(int(seconds / dt)):
        ev = events_fn(i) if events_fn else []
        g.step(dt, ev)
        if not g.running:
            return


def shot(g, name):
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True)
        pygame.image.save(g.screen, os.path.join(SHOTS, name + ".png"))


def top(g):
    return g.stack[-1]


def close_overlays(g, base_type):
    for _ in range(50):
        if isinstance(top(g), base_type):
            return
        g.step(1 / 60, [key(pygame.K_RETURN)])
    raise AssertionError(f"overlay sluit niet: {type(top(g)).__name__}")


def main():
    g = Game()
    g.push(scenes.Title(g))
    run(g, 0.5)
    shot(g, "01_titel")
    # nieuw spel
    g.step(1 / 60, [key(pygame.K_RETURN)])  # Nieuw avontuur (geen save)
    assert isinstance(top(g), scenes.Dialog), type(top(g))
    run(g, 0.3)
    shot(g, "02_intro")
    close_overlays(g, scenes.WorldMap)
    run(g, 0.3)
    shot(g, "03_kaart")
    g.step(1 / 60, [key(pygame.K_RETURN)])
    run(g, 1.2)
    isl = g.stack[0]
    assert isinstance(isl, world.IslandScene), type(isl)
    run(g, 0.3)
    shot(g, "04_eiland_intro")
    close_overlays(g, world.IslandScene)
    prof = g.profile

    # --- vechten: auto-speler loopt naar de dichtstbijzijnde vijand en valt aan
    prof.hp_lvl = 30
    prof.hp = prof.max_hp

    def fight(i):
        p = isl.player
        if not isl.enemies:
            return []
        e = min(isl.enemies, key=lambda en: (en.pos - p.pos).length())
        d = e.pos - p.pos
        p.facing = d.normalize() if d.length() else V(1, 0)
        if d.length() > 120:
            p.pos += p.facing * 6
        return [key(pygame.K_SPACE)] if i % 10 == 0 else []

    run(g, 2)
    shot(g, "05_eiland")
    run(g, 40, fight)
    kills = sum(prof.kills.values())
    print("kills na 40s:", kills, prof.kills, "berries:", prof.berries, "hp:", prof.hp)
    assert kills >= 3, "auto-speler zou vijanden moeten verslaan"
    shot(g, "06_gevecht")
    close_overlays(g, world.IslandScene)

    # alle wapens testen
    prof.weapons = list(WEAPON_ORDER)
    for k, wid in enumerate(WEAPON_ORDER):
        g.step(1 / 60, [key(pygame.K_1 + k)])
        assert prof.weapon == wid
        run(g, 3, fight)
    print("kills na wapentest:", sum(prof.kills.values()))
    close_overlays(g, world.IslandScene)
    # speciale aanval + eten + dash
    isl.player.special = 100
    prof.hp = 50
    g.step(1 / 60, [key(pygame.K_r), key(pygame.K_f), key(pygame.K_LSHIFT)])
    assert isl.player.special_t > 0 and isl.player.special < 100 and prof.hp > 50
    run(g, 0.3)
    shot(g, "07_speciaal")
    close_overlays(g, world.IslandScene)

    # --- onderzoek: fout antwoord (val) en goed antwoord
    spot = next(it for it in isl.interact if it["kind"] == "riddle" and it["idx"] == 0)
    isl.player.pos = V(spot["pos"]) + V(0, 20)
    n_before = len(isl.enemies)
    g.step(1 / 60, [key(pygame.K_e)])
    assert isinstance(top(g), scenes.Riddle)
    run(g, 0.2)
    shot(g, "08_raadsel")
    rd = top(g)
    wrong = next(i for i, o in enumerate(rd.opts) if o != rd.correct)
    rd.sel = wrong
    g.step(1 / 60, [key(pygame.K_RETURN)])
    assert len(isl.enemies) > n_before, "val moet vijanden oproepen"
    isl.riddle_lock.clear()
    for i in range(3):
        sp = next(it for it in isl.interact if it["kind"] == "riddle" and it["idx"] == i)
        isl.player.pos = V(sp["pos"]) + V(0, 20)
        g.step(1 / 60, [key(pygame.K_e)])
        rd = top(g)
        assert isinstance(rd, scenes.Riddle), type(rd)
        rd.sel = rd.opts.index(rd.correct)
        g.step(1 / 60, [key(pygame.K_RETURN)])
        close_overlays(g, world.IslandScene)
    assert prof.clue_count(0) == 3, prof.clues
    print("aanwijzingen:", prof.clues)

    # --- winkel
    prof.berries += 2000
    shop_it = next(it for it in isl.interact if it["kind"] == "shop")
    isl.player.pos = V(shop_it["pos"])
    g.step(1 / 60, [key(pygame.K_e)])
    assert isinstance(top(g), scenes.Shop)
    s0 = prof.str_lvl
    g.step(1 / 60, [key(pygame.K_RETURN)])
    assert prof.str_lvl == s0 + 1
    run(g, 0.2)
    shot(g, "09_winkel")
    g.step(1 / 60, [key(pygame.K_ESCAPE)])

    # --- voetbal
    isl.enemies.clear()
    isl.respawn_t = 999
    f_it = next(it for it in isl.interact if it["kind"] == "field")
    isl.player.pos = V(f_it["pos"])
    g.step(1 / 60, [key(pygame.K_e)])
    fb = top(g)
    assert isinstance(fb, FootballScene), type(fb)
    goals_before = prof.goals

    def play_football(i):
        me = fb.me
        target = V(fb.ball) - (V(1280 - 70, 360) - fb.ball).normalize() * 22
        d = target - me.pos
        ev = []
        if d.length() > 4:
            me.pos += d.normalize() * min(5, d.length())
        if (fb.ball - me.pos).length() < 40 and i % 6 == 0:
            me.look = (V(1280 - 70, 360) - fb.ball).normalize()
            fb.charge = 1.0
            fb.charging = True
            ev.append(key(pygame.K_SPACE, up=True))
        return ev

    run(g, 1)
    shot(g, "10_voetbal")
    # 90 s speeltijd + pauzes na aftrap en elk doelpunt
    for _ in range(30):
        if fb.over:
            break
        run(g, 10, play_football)
    print("voetbal score:", fb.score, "goals totaal:", prof.goals, "wins:", prof.wins)
    assert fb.over
    assert prof.goals > goals_before, "auto-speler zou moeten scoren"
    shot(g, "11_voetbal_einde")
    g.step(1 / 60, [key(pygame.K_RETURN)])
    assert top(g) is isl

    # --- dagboek (alle tabbladen)
    g.step(1 / 60, [key(pygame.K_TAB)])
    assert isinstance(top(g), scenes.Journal)
    for k in range(3):
        run(g, 0.1)
        shot(g, f"12_dagboek_{k}")
        g.step(1 / 60, [key(pygame.K_RIGHT)])
    g.step(1 / 60, [key(pygame.K_ESCAPE)])

    # --- baasgevechten op elk eiland
    for idx in range(len(ISLANDS)):
        if idx > 0:
            prof.unlocked = max(prof.unlocked, idx + 1)
            g.replace(world.IslandScene(g, idx))
            isl = g.stack[0]
            close_overlays(g, world.IslandScene)
            for i in range(3):
                if i not in prof.clue_list(idx):
                    prof.clue_list(idx).append(i)
            isl.enemies.clear()
            isl.respawn_t = 999
            run(g, 0.5)
            shot(g, f"13_eiland_{idx}")
        gate = next(it for it in isl.interact if it["kind"] == "gate")
        isl.player.pos = V(gate["pos"])
        prof.hp = prof.max_hp
        g.step(1 / 60, [key(pygame.K_e)])
        bs = top(g)
        assert isinstance(bs, world.BossScene), type(bs)
        run(g, 1.0)
        shot(g, f"14_baas_{idx}_intro")
        prof.str_lvl = 15
        prof.weapon = "driezwaard"

        def boss_fight(i):
            p = bs.player
            ens = [en for en in bs.enemies]
            if not ens:
                return []
            e = min(ens, key=lambda en: (en.pos - p.pos).length())
            d = e.pos - p.pos
            if d.length():
                p.facing = d.normalize()
            if d.length() > 90:
                p.pos += p.facing * 6
            prof.hp = max(prof.hp, prof.max_hp // 2)  # testmodus: niet sterven
            return [key(pygame.K_SPACE)] if i % 8 == 0 else []

        run(g, 3, boss_fight)
        shot(g, f"15_baas_{idx}_gevecht")
        run(g, 90, boss_fight)
        print("baas", ISLANDS[idx]["boss"], "hp", round(bs.boss.hp), "verslagen:", ISLANDS[idx]["boss"] in prof.bosses)
        assert ISLANDS[idx]["boss"] in prof.bosses
        # laat de afsluiting lopen
        run(g, 5)
        if idx < len(ISLANDS) - 1:
            close_overlays(g, world.IslandScene)
    shot(g, "16_overwinning")
    assert isinstance(top(g), scenes.Victory), type(top(g))

    # --- game over-pad
    g.replace(world.IslandScene(g, 0))
    close_overlays(g, world.IslandScene)
    isl = g.stack[0]
    prof.hp = 1
    isl.hurt_player(50, isl.player.pos + V(10, 0))
    assert isinstance(top(g), scenes.GameOver)
    run(g, 1)
    shot(g, "17_gameover")
    g.step(1 / 60, [key(pygame.K_RETURN)])
    assert prof.hp == prof.max_hp

    # --- opslaan / laden
    prof.save()
    p2 = Profile.load()
    assert p2 and p2.bosses == prof.bosses and p2.berries == prof.berries
    # pauze -> naar titel -> verder spelen
    g.step(1 / 60, [key(pygame.K_ESCAPE)])
    assert isinstance(top(g), scenes.Pause)
    pz = top(g)
    pz.sel = pz.items.index("Opslaan en naar titel")
    g.step(1 / 60, [key(pygame.K_RETURN)])
    assert isinstance(top(g), scenes.Title)
    g.step(1 / 60, [key(pygame.K_RETURN)])
    assert isinstance(top(g), scenes.WorldMap)
    run(g, 0.3)
    shot(g, "18_kaart_eind")
    print("uitdagingen:", prof.done)
    print("ALLES OK")


if __name__ == "__main__":
    main()
