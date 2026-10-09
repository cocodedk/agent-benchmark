"""Render og.svg to og.png at exactly 1200 x 630: `uvx --with playwright python scripts/render_og.py`.

Chrome draws the SVG with its web fonts (Saira Semi Condensed, Source Sans 3), so the card matches the page.
"""
from __future__ import annotations

import pathlib
import shutil

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parents[1]


def main() -> None:
    chrome = shutil.which("google-chrome") or "/usr/bin/google-chrome"
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome)
        page = browser.new_page(viewport={"width": 1200, "height": 630})
        page.goto((HERE / "og.svg").as_uri())
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready.then(() => true)")
        page.wait_for_timeout(300)
        page.screenshot(path=str(HERE / "og.png"), clip={"x": 0, "y": 0, "width": 1200, "height": 630})
        browser.close()


if __name__ == "__main__":
    main()
