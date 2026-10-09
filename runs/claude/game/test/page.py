"""Open the game in Chrome with WebMCP on, served over http from this checkout.

    with game() as g:
        g.call("pause", {"paused": True})   # a tool's answer, as a dict
        g.page.keyboard.down("w")           # the Playwright page, for keys and screenshots
        g.errors                            # page errors and console errors so far
"""
from __future__ import annotations

import contextlib
import functools
import http.server
import json
import os
import pathlib
import shutil
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
CALL = """async ([name, input]) => {
  const mc = document.modelContext;
  const tool = (await mc.getTools()).find(t => t.name === name);
  if (!tool) return {ok: false, missing: name};
  const out = await mc.executeTool(tool, input);
  return typeof out === "string" ? JSON.parse(out) : out;
}"""


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class Game:
    def __init__(self, page):
        self.page, self.errors = page, []
        page.on("pageerror", lambda error: self.errors.append(str(error)))
        page.on("console", self._console)

    def _console(self, message):
        if message.type == "error" and not message.location.get("url", "").endswith("/favicon.ico"):
            self.errors.append(message.text)

    def call(self, name: str, payload: dict | None = None) -> dict:
        return self.page.evaluate(CALL, [name, payload or {}])

    def tools(self) -> list[str]:
        return self.page.evaluate("async () => (await document.modelContext.getTools()).map(t => t.name)")


@contextlib.contextmanager
def game(root: pathlib.Path = ROOT, wait_ms: int = 15000):
    """The page, once it has registered its tools."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    chrome = os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chrome, args=["--enable-features=WebMCP"])
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            g = Game(page)
            page.goto(f"http://127.0.0.1:{server.server_port}/index.html")
            page.wait_for_function("document.modelContext && document.modelContext.getTools().then(t => t.length > 0)",
                                   timeout=wait_ms)
            try:
                yield g
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    with game() as g:
        print(json.dumps({"tools": g.tools(), "errors": g.errors, "state": g.call("describe")}, indent=1))
