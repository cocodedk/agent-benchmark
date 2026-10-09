# Brick Breaker

A browser game made with three.js. You slide a paddle along the bottom of a walled field and bounce a
ball up into a wall of bricks. Every brick the ball touches breaks. Clear them all before you lose
three balls.

## What you start with

- `vendor/three.module.min.js`: three.js r170, the only library. Load it with an import map
  (`"three": "./vendor/three.module.min.js"`). No npm, no build step, nothing else from the network.
- `test/gate.sh`: the suite. It runs every `test/test_*.py` in Chrome with WebMCP switched on, through
  the helper `test/page.py`. Add your tests there.

## The page

`index.html` at the top of the checkout, plus the ES modules it imports, under `src/`. The canvas fills
the browser window and follows its size.

## The field

- A flat floor, x from -10 to 10 and z from -14 to 14 (20 by 28 units, y is up). A wall runs along the
  left side (x = -10), the right side (x = 10) and the top (z = -14). The bottom (z = 14) is open.
- A fixed camera, above the field and tilted, shows all of it at once, so the bricks, paddle and ball
  look three-dimensional.

## The bricks

- 40 bricks in 5 rows of 8. Each brick is 2.5 units along x and 1 along z, with no gaps.
- The brick in row r (0 to 4, 0 at the top) and column c (0 to 7, 0 on the left) has the id `r<r>c<c>`
  and its centre at x = -8.75 + 2.5 c, z = -11.5 + r. So the bricks fill x from -10 to 10 and z from
  -12 to -7.
- Each row has its own colour. A broken brick is gone for the rest of the game, and is worth 10 points.

## The paddle

- 4 units along x and 0.5 along z, centred at z = 12, so its front edge is at z = 11.75.
- A or ← moves it left and D or → right, at 12 units/s, while the key is held: the game reads the held
  keys at every simulation step. Its centre stays within x from -8 to 8.

## The ball

- A sphere of radius 0.3 that always moves at 10 units/s once launched.
- Before launch it rests on the paddle, its centre at (paddle x, 11.45), and moves with the paddle.
- Space launches a resting ball straight up the field (towards -z).
- A wall reflects it: the part of its velocity across the wall flips.
- A ball moving towards the paddle (+z) whose edge reaches the paddle's front edge, with its centre
  within 2.3 units of the paddle's centre along x, bounces off the paddle. Its new direction depends
  on where it hit: with `offset` = (ball x - paddle x) / 2, held within -1 to 1, it leaves at
  60 × offset degrees from straight up, towards +x when the offset is positive. So it moves at
  (10 sin a, -10 cos a) with a = 60 × offset degrees. A hit at the centre sends it straight up.
- A ball that touches a brick breaks it and bounces: off the brick's top or bottom face its z velocity
  flips, off a side face its x velocity flips. Every brick it touches in one step breaks, and it bounces
  once in that step.
- A ball whose centre passes z = 14 is lost: you lose a life and a new ball rests on the paddle.

## Lives, score and the end

- You start with 3 lives and 0 points.
- Losing the last life ends the game: the state becomes `"game_over"` and a banner says "Game over".
- Breaking the last brick wins it: the state becomes `"won"` and a banner says "You win".
- Once the game is over or won, nothing moves until `reset`.
- A head-up display shows the score, the lives left and one line with the controls.

## Timing

The game advances in fixed steps of 1/60 s. Real time drives the steps while the game is not paused;
the `step` tool drives them while it is paused. Both run the same code, so a test through `step`
tests the game.

## WebMCP tools

Register each tool with `document.modelContext.registerTool({name, description, inputSchema, execute})`.
When `document.modelContext` is absent, register nothing; the game still plays. Every tool answers
with a JSON object. A bad input answers `{"ok": false, "error": "..."}` and never throws.

| Tool | Input | What it does | Answer |
|---|---|---|---|
| `describe` | `{}` | reads the game | the state |
| `pause` | `{"paused": true}` | pauses or resumes real-time play | `{"ok": true, "paused": true}` |
| `step` | `{"seconds": 1.5}`, more than 0 and at most 30 | only while paused: advances the game by that many seconds in 1/60 s steps, reading the keys held now | the state |
| `launch` | `{}` | launches a resting ball, as Space does | `{"ok": true, "launched": true}`; `launched` is false when the ball is already moving or the game is over or won |
| `place_paddle` | `{"x": 3}` | moves the paddle's centre there (a resting ball moves with it); refuses x outside -8 to 8 | the state |
| `place_ball` | `{"x": 0, "z": 5, "vx": 0, "vz": -1}` | puts the ball there, moving in the direction (vx, vz) at 10 units/s; refuses a zero direction, a spot overlapping a brick or a wall, or one outside the field | the state |
| `reset` | `{}` | a new game: all 40 bricks, score 0, 3 lives, paddle at x = 0, ball resting on it; pause stays as it is | the state |

The state:

```json
{"ok": true,
 "field": {"width": 20, "depth": 28},
 "paddle": {"x": 0, "z": 12, "width": 4},
 "ball": {"x": 0, "z": 11.45, "vx": 0, "vz": 0, "moving": false},
 "bricks": [{"id": "r0c0", "x": -8.75, "z": -11.5}],
 "score": 0, "lives": 3, "state": "playing", "paused": false}
```

`bricks` lists the bricks still standing (all 40 at the start). `state` is `"playing"`, `"game_over"`
or `"won"`.

## Done when

1. Opening the page shows the field, the bricks, the paddle, the ball and the head-up display, with no
   error in the console.
2. All seven tools are listed and answer as above.
3. Holding D for 0.5 s moves the paddle 6 units to the right, and a resting ball moves with it; the
   paddle stops at x = 8.
4. Space launches the ball straight up at 10 units/s.
5. A ball launched under a brick breaks that brick, scores 10 and comes back down.
6. The side and top walls reflect the ball.
7. The paddle sends the ball back at the angle its offset gives.
8. A ball that passes the paddle costs a life and a new one rests on the paddle; losing the third ends
   the game with the banner.
9. Breaking all 40 bricks wins the game with the banner.
10. `bash test/gate.sh` passes, with tests for the above.

Out of scope: sound, menus, more levels, power-ups, touch controls, more than one ball.
