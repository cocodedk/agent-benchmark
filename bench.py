"""Three agent harnesses build the same Brick Breaker game on the same model; this records how each one went.

    python3 bench.py all             all three builders at once
    python3 bench.py run pi          one builder: claude, prime-agent or pi
    python3 bench.py grade pi        the hidden checks again, on a finished run
    python3 bench.py status          how each run ended

A run builds in its own checkout outside this project, so it never sees `hidden/` or another run. The builder
gets one session and the same prompt; then the harness runs the suite and the hidden checks. The game, its
numbers (`run.json`) and the builder's last words are kept under `runs/<builder>/`.
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
WORK = pathlib.Path(os.environ.get("BENCH_WORK", "~/lean-tmp/agent-bench/work")).expanduser()
MODEL, THINKING, BUDGET, TIMEOUT = "claude-opus-5-5", "high", 10.0, 2700
BUILDERS = {
    "claude": {"says": "Claude Code (claude -p)", "stdin": True,
               "argv": ["claude", "--permission-mode", "dontAsk", "--strict-mcp-config", "-p", "--output-format", "json",
                        "--model", MODEL, "--effort", THINKING, "--max-budget-usd", f"{BUDGET:.2f}",
                        "--allowedTools", "Read,Grep,Glob,Edit,Write,Bash", "--disallowedTools", "Bash(git push *)"]},
    "prime-agent": {"says": "prime-agent -p", "stdin": False,
                    "argv": ["prime-agent", "-p", "--no-session", "--mode", "json", "--model", f"anthropic/{MODEL}",
                             "--thinking", THINKING, "--"]},
    "pi": {"says": "pi -p", "stdin": False,
           "argv": ["pi", "-p", "--no-session", "--mode", "json", "--model", f"anthropic/{MODEL}", "--thinking", THINKING, "--"]},
}
PROMPT = ("Implement what this spec asks, including its tests, in this checkout. Follow the repository's CLAUDE.md "
          "(AGENTS.md is the same file). Check your work with `bash test/gate.sh` and finish only when it passes. "
          "Do not commit and do not start background jobs.\n\n## Spec\n\n")


def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def env() -> dict:
    """This session's own variables stay here: a builder gets the account, not the session that started it."""
    return {k: v for k, v in os.environ.items()
            if not (k.startswith("CLAUDE_CODE_") or k in ("CLAUDECODE", "CLAUDE_PID", "CLAUDE_EFFORT"))}


def claude_usage(stdout: str) -> dict:
    body = json.loads(stdout)
    usage = body.get("modelUsage") or {}
    total = lambda key: sum(u.get(key, 0) for u in usage.values())  # noqa: E731
    one_hour = ((body.get("usage") or {}).get("cache_creation") or {}).get("ephemeral_1h_input_tokens", 0)
    return {"input": total("inputTokens"), "cache_write": total("cacheCreationInputTokens"), "cache_write_1h": one_hour,
            "cache_read": total("cacheReadInputTokens"), "output": total("outputTokens"),
            "cost": round(body.get("total_cost_usd") or 0, 4), "turns": body.get("num_turns"),
            "models": sorted(usage), "error": bool(body.get("is_error")), "answer": str(body.get("result") or "")}


def stream_usage(stdout: str) -> dict:
    """prime-agent and pi print one JSON event per line; every finished assistant message carries its usage."""
    said = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        message = event.get("message") if isinstance(event, dict) else None
        if event.get("type") == "message_end" and isinstance(message, dict) and message.get("role") == "assistant":
            said.append(message)
    usage = [m.get("usage") or {} for m in said]
    total = lambda key: sum(u.get(key, 0) for u in usage)  # noqa: E731
    last = next((c.get("text", "") for c in (said[-1].get("content") or []) if c.get("type") == "text"), "") if said else ""
    # Both write 5-minute cache entries: their reported costs match the 5-minute write price exactly.
    return {"input": total("input"), "cache_write": total("cacheWrite"), "cache_write_1h": 0, "cache_read": total("cacheRead"),
            "output": total("output"), "cost": round(sum((u.get("cost") or {}).get("total", 0) for u in usage), 4),
            "turns": len(said), "models": sorted({m.get("model", "?") for m in said}),
            "error": not said or said[-1].get("stopReason") == "error", "answer": last}


def git(tree, *args) -> str:
    return subprocess.run(["git", "-C", str(tree), *args], capture_output=True, text=True, check=True).stdout


def written(game: pathlib.Path) -> tuple[int, int]:
    """Non-blank lines the run wrote, as (game code, tests); a file still as the seed gave it does not count."""
    code = tests = 0
    for path in sorted(game.rglob("*")):
        rel = path.relative_to(game)
        if not path.is_file() or rel.parts[0] == "vendor" or path.suffix not in (".html", ".js", ".css", ".py"):
            continue
        seed = HERE / "seed" / rel
        if seed.is_file() and seed.read_bytes() == path.read_bytes():
            continue
        lines = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        if rel.parts[0] == "test":
            tests += lines
        else:
            code += lines
    return code, tests


def suite(tree: pathlib.Path) -> dict:
    start = time.time()
    try:
        done = subprocess.run(["bash", "test/gate.sh"], cwd=tree, capture_output=True, text=True, timeout=600)
        passed, tail = done.returncode == 0, (done.stdout + done.stderr)[-4000:]
    except subprocess.TimeoutExpired:
        passed, tail = False, "The suite did not finish within 600 s."
    return {"passed": passed, "wall_s": round(time.time() - start), "tail": tail}


def run(name: str) -> None:
    builder, tree, keep = BUILDERS[name], WORK / name, HERE / "runs" / name
    shutil.rmtree(tree, ignore_errors=True)
    shutil.rmtree(keep, ignore_errors=True)
    shutil.copytree(HERE / "seed", tree, symlinks=True)
    (keep / "log").mkdir(parents=True)
    git(tree, "init", "-q")
    git(tree, "add", "-A")
    git(tree, "-c", "user.name=bench", "-c", "user.email=bench@localhost", "commit", "-qm", "seed")
    record = {"run": name, "says": builder["says"], "model": MODEL, "thinking": THINKING, "started": now()}
    prompt = PROMPT + (HERE / "spec.md").read_text(encoding="utf-8")
    argv = builder["argv"] + ([] if builder["stdin"] else [prompt])
    start = time.time()
    try:
        done = subprocess.run(argv, input=prompt if builder["stdin"] else "", capture_output=True, text=True, cwd=tree,
                              timeout=TIMEOUT, env=env())
        stdout, stderr, code = done.stdout, done.stderr, done.returncode
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or ""
        stdout, stderr, code = stdout.decode(errors="replace") if isinstance(stdout, bytes) else stdout, "timeout", None
    record["minutes"] = round((time.time() - start) / 60, 1)
    (WORK / f"{name}.stdout").write_text(stdout)
    try:
        usage = claude_usage(stdout) if name == "claude" else stream_usage(stdout)
    except ValueError:
        usage = {"error": True, "answer": stdout[-2000:]}
    (keep / "log" / "answer.txt").write_text(usage.pop("answer", ""))
    (keep / "log" / "stderr.txt").write_text(stderr[-4000:])
    record.update(exit=code, timed_out=code is None, **usage)
    record["total_tokens"] = sum(record.get(k, 0) for k in ("input", "cache_write", "cache_read", "output"))
    record["suite"] = suite(tree)
    (keep / "log" / "suite.txt").write_text(record["suite"].pop("tail"))
    shutil.copytree(tree, keep / "game", ignore=shutil.ignore_patterns(".git", "__pycache__"), symlinks=True)
    record["code_lines"], record["test_lines"] = written(keep / "game")
    record["finished"] = now()
    (keep / "run.json").write_text(json.dumps(record, indent=1))
    grade(name)


def grade(name: str) -> None:
    keep = HERE / "runs" / name
    subprocess.run(["uvx", "--quiet", "--with", "playwright", "python", str(HERE / "hidden" / "checks.py"),
                    str(keep / "game"), "--out", str(keep)], capture_output=True, text=True)
    record = json.loads((keep / "run.json").read_text())
    hidden = keep / "hidden.json"
    record["hidden"] = json.loads(hidden.read_text()) if hidden.exists() else {"passed": 0, "total": 0, "checks": []}
    (keep / "run.json").write_text(json.dumps(record, indent=1))


def status() -> None:
    for name in BUILDERS:
        path = HERE / "runs" / name / "run.json"
        if not path.exists():
            print(f"{name:12} not run" + (" (building)" if (WORK / name).exists() else ""))
            continue
        r = json.loads(path.read_text())
        h = r.get("hidden", {})
        print(f"{name:12} {r['minutes']:5} min  ${r.get('cost', 0):6.2f}  {r.get('total_tokens', 0):>10,} tokens  "
              f"suite {'green' if r['suite']['passed'] else 'red'}  hidden {h.get('passed', '-')}/{h.get('total', '-')}")


def everything() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    children = [subprocess.Popen([sys.executable, __file__, "run", name], stdout=open(WORK / f"{name}.console", "w"),
                                 stderr=subprocess.STDOUT) for name in BUILDERS]
    for child in children:
        child.wait()
    status()


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"all": lambda: everything(), "run": lambda: run(sys.argv[2]), "grade": lambda: grade(sys.argv[2])}.get(what, status)()
