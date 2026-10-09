"""The hidden acceptance checks: the builder never sees them. They grade one built game through its tools.

    uvx --with playwright python hidden/checks.py <game dir> [--out <dir>]

Prints one line per check and writes hidden.json (and screenshot.png) to --out. Each check opens its own
page, so one broken check cannot spoil the next. The numbers come from the spec: paddle speed 12, ball speed
10, ball radius 0.3, paddle front edge at z = 11.75, bricks 2.5 by 1 from z = -12 to -7.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "seed" / "test"))
from page import game  # noqa: E402

TOOLS = {"describe", "pause", "step", "launch", "place_paddle", "place_ball", "reset"}
BRICKS = {f"r{r}c{c}": (-8.75 + 2.5 * c, -11.5 + r) for r in range(5) for c in range(8)}
CHECKS = []


def check(fn):
    CHECKS.append(fn)
    return fn


def fresh(g):
    g.call("pause", {"paused": True})
    return g.call("reset", {})


def hold(g, key, seconds):
    g.page.keyboard.down(key)
    state = g.call("step", {"seconds": seconds})
    g.page.keyboard.up(key)
    return state


def ball(g, x, z, vx, vz):
    said = g.call("place_ball", {"x": x, "z": z, "vx": vx, "vz": vz})
    assert said.get("ok"), f"place_ball ({x}, {z}) refused: {said}"
    return said


def paddle(g, x):
    said = g.call("place_paddle", {"x": x})
    assert said.get("ok"), f"place_paddle {x} refused: {said}"
    return said


def near(name, got, want, tol):
    assert abs(got - want) <= tol, f"{name} {got:.2f}, expected {want} ± {tol}"


def ids(state):
    return {b["id"] for b in state["bricks"]}


@check
def opens_clean(g, out):
    g.page.wait_for_timeout(2000)
    png = g.page.screenshot(path=str(out / "screenshot.png"))
    assert not g.errors, f"errors: {g.errors[:3]}"
    assert g.page.locator("canvas").count() >= 1, "no canvas"
    assert len(png) > 12000, f"the screenshot is {len(png)} bytes: nearly blank"


@check
def lists_the_seven_tools(g, out):
    missing = TOOLS - set(g.tools())
    assert not missing, f"missing {sorted(missing)}"


@check
def starts_as_the_spec_says(g, out):
    s = fresh(g)
    assert s["field"] == {"width": 20, "depth": 28}, s["field"]
    assert ids(s) == set(BRICKS), f"{len(s['bricks'])} bricks, ids differ from r0c0..r4c7"
    for b in s["bricks"]:
        x, z = BRICKS[b["id"]]
        assert abs(b["x"] - x) < 0.01 and abs(b["z"] - z) < 0.01, f"{b} should be at ({x}, {z})"
    p, ball_ = s["paddle"], s["ball"]
    assert abs(p["x"]) < 0.01 and abs(p["z"] - 12) < 0.01 and p["width"] == 4, p
    assert abs(ball_["x"]) < 0.01 and abs(ball_["z"] - 11.45) < 0.01 and ball_["moving"] is False, ball_
    assert (s["score"], s["lives"], s["state"]) == (0, 3, "playing"), (s["score"], s["lives"], s["state"])


@check
def keys_move_the_paddle_and_the_resting_ball(g, out):
    fresh(g)
    s = hold(g, "d", 0.5)
    near("paddle x after 0.5 s of D", s["paddle"]["x"], 6, 0.3)
    near("resting ball x", s["ball"]["x"], s["paddle"]["x"], 0.01)
    near("resting ball z", s["ball"]["z"], 11.45, 0.01)
    near("paddle x after 1 s more of D", hold(g, "d", 1.0)["paddle"]["x"], 8, 0.01)
    near("paddle x after 0.5 s of A", hold(g, "a", 0.5)["paddle"]["x"], 2, 0.3)


@check
def space_launches_straight_up_once(g, out):
    fresh(g)
    b = hold(g, " ", 0.1)["ball"]
    assert b["moving"] is True, f"holding Space for 0.1 s did not launch: {b}"
    near("vx", b["vx"], 0, 0.1), near("vz", b["vz"], -10, 0.1)
    assert g.call("launch", {}).get("launched") is False, "launch said launched while the ball was moving"


@check
def the_ball_moves_ten_units_a_second(g, out):
    fresh(g)
    assert g.call("launch", {}).get("launched") is True, "launch did not launch a resting ball"
    b = g.call("step", {"seconds": 0.5})["ball"]
    near("ball z 0.5 s after launch", b["z"], 6.45, 0.25), near("ball x", b["x"], 0, 0.05)


@check
def a_ball_breaks_the_brick_above_and_comes_back(g, out):
    fresh(g)
    paddle(g, -1.25)
    g.call("launch", {})
    s = g.call("step", {"seconds": 2.5})
    assert ids(s) == set(BRICKS) - {"r4c3"}, f"broken: {sorted(set(BRICKS) - ids(s))}, expected only r4c3"
    assert s["score"] == 10, f"score {s['score']}"
    b = s["ball"]
    near("vz after the brick", b["vz"], 10, 0.1), near("vx after the brick", b["vx"], 0, 0.1)
    near("ball z 2.5 s after launch", b["z"], 0.15, 0.5)


@check
def walls_reflect_the_ball(g, out):
    fresh(g)
    ball(g, 8, 0, 1, 0)
    b = g.call("step", {"seconds": 0.5})["ball"]
    near("x after the right wall", b["x"], 6.4, 0.35), near("vx", b["vx"], -10, 0.1), near("vz", b["vz"], 0, 0.1)
    ball(g, -8, 0, -1, 0)
    b = g.call("step", {"seconds": 0.5})["ball"]
    near("x after the left wall", b["x"], -6.4, 0.35), near("vx", b["vx"], 10, 0.1)
    ball(g, 5, -13, 0, -1)
    b = g.call("step", {"seconds": 0.1})["ball"]
    near("vz after the top wall", b["vz"], 10, 0.1), near("z after the top wall", b["z"], -13.4, 0.3)


@check
def the_paddle_angles_the_ball(g, out):
    for x, a in ((1, 30), (0, 0), (-2, -60)):
        fresh(g)
        ball(g, x, 10, 0, 1)
        b = g.call("step", {"seconds": 0.3})["ball"]
        want = (10 * math.sin(math.radians(a)), -10 * math.cos(math.radians(a)))
        assert abs(b["vx"] - want[0]) <= 0.3 and abs(b["vz"] - want[1]) <= 0.3, \
            f"hit {x} from the centre: velocity ({b['vx']:.2f}, {b['vz']:.2f}), expected ({want[0]:.2f}, {want[1]:.2f})"


@check
def a_lost_ball_costs_a_life(g, out):
    fresh(g)
    paddle(g, -8)
    ball(g, 8, 10, 0, 1)
    s = g.call("step", {"seconds": 1.0})
    b = s["ball"]
    assert (s["lives"], s["state"], b["moving"]) == (2, "playing", False), (s["lives"], s["state"], b)
    near("new ball x", b["x"], -8, 0.01), near("new ball z", b["z"], 11.45, 0.01)


@check
def three_lost_balls_end_the_game(g, out):
    fresh(g)
    paddle(g, -8)
    for _ in range(3):
        ball(g, 8, 10, 0, 1)
        s = g.call("step", {"seconds": 1.0})
    assert (s["lives"], s["state"]) == (0, "game_over"), (s["lives"], s["state"])
    assert "game over" in g.page.inner_text("body").lower(), "no banner saying 'Game over'"
    assert g.call("launch", {}).get("launched") is False, "launch said launched after game over"
    s = g.call("reset", {})
    assert (s["lives"], s["state"], len(s["bricks"])) == (3, "playing", 40), (s["lives"], s["state"], len(s["bricks"]))


@check
def breaking_every_brick_wins(g, out):
    fresh(g)
    for r in range(4, -1, -1):
        for c in range(8):
            x, z = BRICKS[f"r{r}c{c}"]
            ball(g, x, z + 1.5, 0, -1)
            s = g.call("step", {"seconds": 0.1})
            assert f"r{r}c{c}" not in ids(s), f"r{r}c{c} still stands after a hit from below"
    assert (s["state"], s["score"], s["bricks"]) == ("won", 400, []), (s["state"], s["score"], len(s["bricks"]))
    assert "you win" in g.page.inner_text("body").lower(), "no banner saying 'You win'"


@check
def tools_refuse_bad_input(g, out):
    fresh(g)
    bad = {"place_paddle x 9": g.call("place_paddle", {"x": 9}),
           "place_ball with no direction": g.call("place_ball", {"x": 0, "z": 0, "vx": 0, "vz": 0}),
           "place_ball inside a brick": g.call("place_ball", {"x": -1.25, "z": -9.5, "vx": 0, "vz": 1}),
           "place_ball outside the field": g.call("place_ball", {"x": 12, "z": 0, "vx": 0, "vz": 1}),
           "step 0 s": g.call("step", {"seconds": 0}), "step 31 s": g.call("step", {"seconds": 31})}
    accepted = [name for name, said in bad.items() if said.get("ok") is not False]
    assert not accepted, f"accepted: {accepted}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("game")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()
    root, out = pathlib.Path(args.game).resolve(), pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for fn in CHECKS:
        try:
            with game(root) as g:
                fn(g, out)
            results.append({"check": fn.__name__, "passed": True})
        except Exception as error:  # a check that cannot run is a failed check, with its reason
            results.append({"check": fn.__name__, "passed": False, "why": f"{type(error).__name__}: {error}"[:400]})
        print(("PASS " if results[-1]["passed"] else "FAIL ") + fn.__name__, results[-1].get("why", ""), flush=True)
    passed = sum(r["passed"] for r in results)
    (out / "hidden.json").write_text(json.dumps({"passed": passed, "total": len(results), "checks": results}, indent=1))
    print(f"{passed}/{len(results)} hidden checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
