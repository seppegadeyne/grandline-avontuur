"""Bouw de webversie (WebAssembly via pygbag) naar ./public.

Pygbag pakt alles in de bronmap in, dus we kopiëren eerst enkel de spelcode
(main.py + grandline/) naar een schone staging-map. Zo komen .venv, tests en
build-resten nooit in het pakket.

Gebruik:  uv run python scripts/build_web.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / ".web-build" / "grandline-avontuur"
OUT = ROOT / "public"


def main():
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    shutil.copy2(ROOT / "main.py", STAGE / "main.py")
    shutil.copytree(ROOT / "grandline", STAGE / "grandline",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    favicon = ROOT / "web" / "favicon.png"
    if favicon.exists():
        shutil.copy2(favicon, STAGE / "favicon.png")

    cmd = [sys.executable, "-m", "pygbag", "--build",
           "--title", "Grand Line Avontuur",
           "--package", "be.gadeyne.grandline",
           "--ume_block", "1",
           str(STAGE)]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=STAGE)

    web = STAGE / "build" / "web"
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(web, OUT)  # index.html laadt <naam>.tar.gz, .apk blijft voor itch.io e.d.
    for f in sorted(OUT.iterdir()):
        print(f"{f.stat().st_size:>10}  {f.name}")


if __name__ == "__main__":
    main()
