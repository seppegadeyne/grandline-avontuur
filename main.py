"""Startpunt voor desktop (`uv run main.py`) en browser (pygbag bouwt vanaf dit bestand)."""
import asyncio

import pygame  # noqa: F401  pygbag scant de imports van main.py om pygame-ce in de browser te laden

from grandline.main import Game


async def main():
    await Game().run()


asyncio.run(main())
