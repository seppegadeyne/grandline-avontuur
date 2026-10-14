# Grand Line Avontuur

A One Piece-inspired action adventure game written in Python with [pygame-ce](https://pyga.me/).
It runs as a desktop game and in the browser through WebAssembly, using [pygbag](https://github.com/pygame-web/pygbag).

> Dutch: een actie-avonturenspel in de geest van One Piece. Vechten, voetballen en eilanden onderzoeken, in je browser of op je computer. Het spel zelf is Nederlandstalig.

## Credits

- **Concept and game idea: Ace.** Ace came up with the game: a straw-hat pirate with a rubber body who sails the Grand Line, fights dragons and strange-faced crews, plays football for Berries, and solves the mystery of every island.
- Code: Seppe Gadeyne.

## The game

You are a young pirate with a straw hat and a body made of rubber. Your dream is to become King of the Pirates, so you have to cross the Grand Line.

- **Fight** bandits, marines, clown pirates, fishmen and dragons with six weapons, from the Rubber Fist to Three-Sword Style.
- **Play football** matches against island teams to earn Berries.
- **Investigate** the `?` spots on each island and answer riddles to collect clues that lead you to the island boss.
- **Upgrade** strength, HP and speed in the shop and buy new weapons.
- **Complete challenges** in your logbook, from your first win to defeating Leviathan the Sea Dragon.

Five islands: Windmolendorp, Schelpenstad, Clownstad, Drakeneiland and Zeemanspark, each with its own boss.

All graphics are drawn in code and all sound effects are synthesized at runtime, so the game has no asset files.

## Controls

| Action | Keys |
| --- | --- |
| Move | WASD / ZQSD / arrow keys |
| Attack | Space / J / left mouse button (aim with the mouse) |
| Dash | Shift / K / right mouse button |
| Special attack | R (when the yellow SP bar is full) |
| Eat meat (+HP) | F |
| Switch weapon | 1 - 6 |
| Talk / investigate | E or Enter |
| Logbook (challenges) | Tab or I |
| Football: shoot | Hold Space and release (or use the mouse) |
| Football: sprint | Shift |
| Pause / back | Esc |

### Phones and tablets

In the browser the game also works with touch, in portrait and in landscape. Once you touch the screen,
on-screen controls appear: a joystick on the left to walk (and to move through menus) and buttons on the
right for attack, dash, special, talk, eat and switching weapons. In portrait the game sits at the top
of the screen with the controls below it. In landscape the buttons float over the game. Menus, shop items,
riddle answers and islands on the map can also be tapped directly.

## Run on the desktop

Requires [uv](https://docs.astral.sh/uv/) and Python 3.13.

```bash
uv sync
uv run main.py          # or: uv run python -m grandline
```

Press F11 to toggle fullscreen. Progress is saved in `~/.local/share/grandline-avontuur/save.json`.

## Run in the browser

```bash
uv run python scripts/build_web.py      # builds the WebAssembly version into ./public
python3 -m http.server 8000 -d public   # open http://localhost:8000
```

`scripts/build_web.py` copies only `main.py` and `grandline/` into a clean staging folder before running pygbag. This keeps `.venv`, tests and build leftovers out of the game package, which is about 40 KB.

In the browser:

- The page asks for one click or tap before the game starts. Browsers only allow sound after a user gesture.
- The Python runtime and pygame-ce are loaded from the pygbag CDN (`pygame-web.github.io`). The first load takes a few seconds, and later loads come from the browser cache.
- Progress is saved in the browser's `localStorage` under `grandline-avontuur/save`.
- The "Quit" menu items are hidden, because you close the tab instead.

## Deploy to Vercel

The repository is ready for Vercel as a static site. `vercel.json` installs pygbag, runs `scripts/build_web.py` and serves `public/`.

- **From Git:** import the repository in Vercel. No framework preset or extra settings are needed.
- **From the CLI:** `npx vercel deploy --prod`

Any other static host (Cloudflare Pages, Netlify, GitHub Pages, itch.io) works too: build locally and upload the contents of `public/`.

## Tests

A headless smoke test plays through every scene: title, world map, islands, combat, all weapons, riddles, football, bosses, game over, and save/load.

```bash
uv run python tests/smoke_test.py               # add a folder path to also save screenshots
```

## Project layout

```
main.py              entry point for desktop and pygbag (async)
grandline/
  main.py            game loop and scene stack
  core.py            text, panels, synthesized sound, profile and save (file or localStorage)
  scenes.py          title, world map, shop, logbook, pause, dialogs
  world.py           islands, NPCs, riddles
  combat.py          player, enemies, weapons, bosses
  football.py        football matches
  touch.py           touch controls (reads the on-screen joystick and buttons in the browser)
  art.py             procedural drawing of characters, dragons and ships
  settings.py        constants and all game content
scripts/build_web.py WebAssembly build for the browser
web/index.tmpl       pygbag page template: mobile layout and on-screen controls
tests/smoke_test.py  headless smoke test
vercel.json          Vercel build configuration
```

## Disclaimer

This is a non-commercial fan game made for fun. It is inspired by *One Piece* by Eiichiro Oda and is not affiliated with or endorsed by Eiichiro Oda, Shueisha, Toei Animation or any other rights holder.

## License

[MIT](LICENSE)
