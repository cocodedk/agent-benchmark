# Brick Breaker

A three.js browser game. What it must do is the spec the builder is given.

- Plain ES modules: no build step, no npm, nothing loaded from the network. three.js is
  `vendor/three.module.min.js`; leave `vendor/` as it is.
- `index.html` at the top, game code under `src/`.
- No file over 200 lines: split a growing file at a natural seam.
- The suite is `bash test/gate.sh`: Python unittest files `test/test_*.py`, each driving the page
  through its WebMCP tools with `test/page.py`. Keep the whole suite under two minutes.
- The simplest thing that works.
