"""Prove the results page through its own WebMCP tools: `uvx --with playwright python scripts/prove_site.py`.

Builds site/, opens it in Chrome with WebMCP on, drives `describe` and `list_runs`, checks their answers against
the runs on disk, and saves site-proof.png. Playwright only opens the page and takes the screenshot.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(HERE), str(HERE / "seed" / "test")]
import gallery  # noqa: E402
from page import game  # noqa: E402


def main() -> int:
    gallery.main()
    runs = {p.parent.name for p in (HERE / "runs").glob("*/run.json") if "hidden" in json.loads(p.read_text())}
    with game(gallery.SITE) as g:
        tools = set(g.tools())
        missing = {"describe", "list_runs"} - tools
        about, listed = g.call("describe"), g.call("list_runs")
        g.page.screenshot(path=str(HERE / "site-proof.png"), full_page=True)
    problems = [f"tool not listed: {name}" for name in sorted(missing)]
    if about.get("ok") is not True or about.get("builds") != len(runs) or about.get("best") not in runs:
        problems.append(f"describe answered {about}")
    if listed.get("ok") is not True or {r["run"] for r in listed.get("runs", [])} != runs:
        problems.append(f"list_runs listed {[r.get('run') for r in listed.get('runs', [])]}, expected {sorted(runs)}")
    for r in listed.get("runs", []):
        paid = sum((r.get("dollars_by_kind") or {}).values())
        if abs(paid - r.get("dollars", -1)) > 0.01:
            problems.append(f"{r.get('run')}: dollars by kind add up to {paid:.4f}, not {r.get('dollars')}")
    if g.errors:
        problems.append(f"page errors: {g.errors[:3]}")
    print("\n".join(problems) or f"proved: {sorted(tools)} answer for {len(runs)} runs; best {about['best']}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
