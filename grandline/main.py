"""Hoofdlus en scènestapel."""
import asyncio
import os
import sys

import pygame

from .core import WEB, Profile, Sfx, font, panel, text
from .settings import FPS, H, TITLE, W
from .touch import TouchInput


class Game:
    def __init__(self, autoplay=None):
        if not WEB:
            os.environ.setdefault("SDL_VIDEODRIVER",
                                  "wayland,x11" if os.environ.get("WAYLAND_DISPLAY") else "x11")
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.sfx = Sfx()
        self.profile = Profile.load() or Profile()
        self.stack = []
        self.toasts = []
        self.running = True
        self.touch = TouchInput()

    # scènestapel
    def push(self, scene):
        self.stack.append(scene)

    def pop(self):
        if self.stack:
            self.stack.pop()
        if self.stack:
            self.stack[-1].on_resume()

    def replace(self, scene):
        self.stack.clear()
        self.stack.append(scene)

    def toast(self, msg, color=(255, 255, 255)):
        self.toasts.append([msg, color, 3.0])
        self.toasts = self.toasts[-4:]

    def draw(self):
        start = 0
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i].opaque:
                start = i
                break
        for sc in self.stack[start:]:
            sc.draw(self.screen)
        for k, (msg, col, t) in enumerate(self.toasts):
            y = 150 + k * 44
            w = font(28).size(msg)[0]
            panel(self.screen, (W // 2 - w // 2 - 16, y - 6, w + 32, 38), alpha=int(220 * min(1, t)), radius=10, width=2)
            text(self.screen, msg, 28, col, (W // 2, y + 13), "center", bold=False)

    def step(self, dt, events):
        tapped = False
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # max. één tik per frame: sommige browsers sturen voor één touch zowel touch- als muisevents
                if tapped:
                    continue
                tapped = True
            if e.type == pygame.QUIT:
                self.profile.save()
                self.running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11 and not WEB:
                pygame.display.toggle_fullscreen()
            elif self.stack:
                self.stack[-1].handle(e)
        if self.stack:
            self.stack[-1].update(dt)
        for t in self.toasts:
            t[2] -= dt
        self.toasts = [t for t in self.toasts if t[2] > 0]
        self.screen.fill((0, 0, 0))
        self.draw()
        pygame.display.flip()

    async def run(self):
        """Async hoofdlus: de browser (pygbag) krijgt elke frame de controle terug."""
        from .scenes import Title
        self.push(Title(self))
        while self.running and self.stack:
            dt = min(self.clock.tick(FPS) / 1000, 0.05)
            self.step(dt, pygame.event.get() + self.touch.poll(self, dt))
            await asyncio.sleep(0)
        self.profile.save()
        pygame.quit()


def main():
    asyncio.run(Game().run())
    sys.exit(0)


if __name__ == "__main__":
    main()
