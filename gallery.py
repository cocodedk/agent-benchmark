"""Build the static site in site/: `python3 gallery.py`.

site/ holds the results page (from page.html), the playable game of every finished run (games/<run>/), their
first frames (shots/), and the files GitHub Pages serves with them. .github/workflows/pages.yml publishes site/.
"""
from __future__ import annotations

import datetime
import json
import pathlib
import re
import shutil
import struct

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE / "site"
ORIGIN = "https://agents.cocode.dk"
REPO = "https://github.com/cocodedk/agent-benchmark"
LOCAL_THREE = "./vendor/three.module.min.js"
CDN_THREE = "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.min.js"
STATIC = ("styles.css", "favicon.svg", "og.png")
# Opus 5.5 list prices, dollars per million tokens. A 5-minute cache write is 1.25x input, a 1-hour one 2x.
PRICES = {"input": 4.0, "cache_write_5m": 5.0, "cache_write_1h": 8.0, "cache_read": 0.20, "output": 20.0}
DESCRIPTION = ("Claude Code, prime-agent and pi each build the same three.js Brick Breaker on Opus 5.5: minutes, "
               "dollars, tokens and hidden checks passed, with every game playable.")
METHOD = [
    "Each builder started in its own copy of <code>seed/</code>, outside this project, so it never saw the hidden checks "
    "or another build. Each got the same prompt: the spec in <code>spec.md</code>, with the instruction to pass "
    "<code>bash test/gate.sh</code>.",
    "Model: <code>claude-opus-5-5</code>, thinking high, one session each, no repairs, a 45-minute limit. Each harness ran "
    "as installed on the machine, with its own system prompt, tools and context files.",
    "Claude Code ran <code>claude -p</code> with Read, Edit, Write and Bash allowed and no MCP servers; prime-agent and "
    "pi ran with <code>-p --no-session</code> and their default tools.",
    "Tokens and dollars are what each harness reported for the session. Claude Code reports its own cost; prime-agent "
    "and pi report a cost per message. All three match Opus 5.5's list prices to the cent.",
    "After each build the harness ran the builder's own suite, then 13 hidden checks that drive the game through its "
    "WebMCP tools (<code>hidden/checks.py</code>). The builder never sees them.",
    "Saying only \"Hello\" (Opus 5.5 high, three times each, 9 October 2026) costs Claude Code about 29.3K tokens, "
    "prime-agent 26.5K and pi 18.2K: that is each harness's own system prompt and tools before any work.",
]


def summary(r: dict) -> dict:
    keys = ("run", "says", "model", "minutes", "cost", "input", "cache_write", "cache_read", "output", "total_tokens",
            "turns", "code_lines", "test_lines")
    return {**{key: r[key] for key in keys}, "suite": r["suite"]["passed"],
            "hidden": r["hidden"]["passed"], "checks": r["hidden"]["total"],
            "failed": [{"check": c["check"], "why": c["why"]} for c in r["hidden"]["checks"] if not c["passed"]],
            "cache_write_1h": r.get("cache_write_1h", 0), "dollars": dollars(r),
            "answer": last_words(r["run"]), "shot": png_size(HERE / "runs" / r["run"] / "screenshot.png")}


def dollars(r: dict) -> dict:
    """What each kind of token cost; it must add up to the cost the harness reported, or the prices are wrong."""
    per = {key: price / 1e6 for key, price in PRICES.items()}
    one_hour = r.get("cache_write_1h", 0)
    paid = {"input": r["input"] * per["input"], "cache_read": r["cache_read"] * per["cache_read"], "output": r["output"] * per["output"],
            "cache_write": (r["cache_write"] - one_hour) * per["cache_write_5m"] + one_hour * per["cache_write_1h"]}
    if abs(sum(paid.values()) - r["cost"]) > 0.01:
        raise SystemExit(f"{r['run']}: tokens at PRICES come to ${sum(paid.values()):.4f}, the harness reported ${r['cost']:.4f}")
    return {key: round(value, 4) for key, value in paid.items()}


def last_words(run: str) -> str:
    path = HERE / "runs" / run / "log" / "answer.txt"
    text = path.read_text(encoding="utf-8").strip() if path.exists() else ""
    return text if len(text) <= 1500 else text[:1500] + " …"


def png_size(path: pathlib.Path) -> list[int]:
    head = path.read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    return list(struct.unpack(">II", head[16:24]))


def fill(template: str, values: dict) -> str:
    """Replace each {{name}}. A name with no value raises KeyError, so a misspelt placeholder cannot ship."""
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], template)


def script_json(value) -> str:
    """JSON that can sit inside a <script>: no literal '<', so a string cannot close the tag."""
    return json.dumps(value).replace("<", "\\u003c")


def page(rows: list[dict], today: datetime.date) -> str:
    jsonld = {"@context": "https://schema.org", "@type": "WebSite", "name": "Agent Harness Benchmark",
              "description": DESCRIPTION, "url": f"{ORIGIN}/", "inLanguage": "en", "codeRepository": REPO,
              "author": {"@type": "Person", "name": "Babak Bandpey", "url": "https://cocode.dk"},
              "publisher": {"@type": "Organization", "name": "Cocode", "url": "https://cocode.dk"}}
    html = fill((HERE / "page.html").read_text(encoding="utf-8"), {
        "origin": ORIGIN, "repo": REPO, "description": DESCRIPTION, "year": str(today.year),
        "jsonld": json.dumps(jsonld, indent=1), "method": "".join(f"<li>{item}</li>" for item in METHOD)})
    return html.replace("/*DATA*/[]", script_json(rows)).replace("/*PRICES*/{}", script_json(PRICES))


def publish_games(rows: list[dict]) -> None:
    (SITE / "shots").mkdir(parents=True, exist_ok=True)
    for row in rows:
        run = row["run"]
        game = HERE / "runs" / run / "game"
        for path in sorted(game.rglob("*")):
            rel = path.relative_to(game)
            if not path.is_file() or {"test", "vendor"} & set(rel.parts) or path.suffix not in (".html", ".js", ".css"):
                continue
            out = SITE / "games" / run / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            if rel.as_posix() == "index.html":
                text = path.read_text(encoding="utf-8")
                if LOCAL_THREE not in text or text.count("<head>") != 1:
                    raise SystemExit(f"{run}: index.html does not load {LOCAL_THREE} from one <head>")
                text = text.replace(LOCAL_THREE, CDN_THREE).replace(
                    "<head>", '<head>\n<link rel="icon" type="image/svg+xml" href="../../favicon.svg">')
                out.write_text(text, encoding="utf-8")
            else:
                shutil.copyfile(path, out)
        shutil.copyfile(HERE / "runs" / run / "screenshot.png", SITE / "shots" / f"{run}.png")


def llms(rows: list[dict]) -> str:
    return f"""# Agent Harness Benchmark

> Claude Code, prime-agent and pi each build the same three.js Brick Breaker on Opus 5.5; the results, with every game playable.

This site has WebMCP tools. A page that declares them registers each one with document.modelContext.registerTool,
and an agent in the browser lists them with document.modelContext.getTools(). Use the tools instead of reading the
page. Every tool takes a JSON object and answers with a JSON object.

## Results page: {ORIGIN}/

Two read-only tools:

- describe: Says what this page shows: the benchmark, its model, how many builds it holds and which builder did best.
- list_runs: Lists every build: builder, minutes, dollars (in all and by token kind), tokens by kind, turns, lines written,
  suite, hidden checks passed and the game's link.

## Game pages: {ORIGIN}/games/<run>/index.html

One playable game per builder ({", ".join(row["run"] for row in rows)}). The spec asks each game to declare seven tools;
a build may lack some (the results page lists its failed checks):

- describe: Reads the game: field, paddle, ball, bricks still standing, score, lives, state and paused.
- pause: Pauses or resumes real-time play, with {{"paused": true}}.
- step: While paused, advances the game by more than 0 and at most 30 seconds, in 1/60 s steps.
- launch: Launches a resting ball, as Space does.
- place_paddle: Moves the paddle's centre to x, from -8 to 8.
- place_ball: Puts the ball at x, z moving in the direction vx, vz at 10 units/s.
- reset: Starts a new game: all 40 bricks, score 0, 3 lives.

## Other files

- {ORIGIN}/robots.txt
- {ORIGIN}/sitemap.xml
"""


def main() -> None:
    today = datetime.date.today()
    runs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((HERE / "runs").glob("*/run.json"))]
    rows = [summary(r) for r in runs if "hidden" in r]
    shutil.rmtree(SITE, ignore_errors=True)
    SITE.mkdir()
    (SITE / "index.html").write_text(page(rows, today), encoding="utf-8")
    for name in STATIC:
        shutil.copyfile(HERE / name, SITE / name)
    publish_games(rows)
    # The repository keeps its own copy of what crawlers and agents read, so it is reviewed with the code.
    lastmod = max((r["finished"][:10] for r in runs if "hidden" in r), default=today.isoformat())
    sitemap = (f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               f"  <url>\n    <loc>{ORIGIN}/</loc>\n    <lastmod>{lastmod}</lastmod>\n  </url>\n</urlset>\n")
    for name, text in (("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {ORIGIN}/sitemap.xml\n"),
                       ("sitemap.xml", sitemap), ("llms.txt", llms(rows))):
        (HERE / name).write_text(text, encoding="utf-8")
        shutil.copyfile(HERE / name, SITE / name)
    (SITE / "CNAME").write_text("agents.cocode.dk\n", encoding="utf-8")
    print(f"site/: {len(rows)} runs")


if __name__ == "__main__":
    main()
