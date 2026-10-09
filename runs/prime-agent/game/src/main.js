// Wires the game to the keyboard, the clock, the picture, the HUD and the WebMCP tools.
import { DT, createGame, step, launch } from './game.js';
import { createView } from './view.js';
import { initTools } from './tools.js';

const g = createGame();
const held = new Set();
const KEYS = { KeyA: 'left', ArrowLeft: 'left', KeyD: 'right', ArrowRight: 'right' };

window.addEventListener('keydown', (e) => {
  if (KEYS[e.code]) { held.add(KEYS[e.code]); e.preventDefault(); }
  if (e.code === 'Space') { launch(g); e.preventDefault(); }
});
window.addEventListener('keyup', (e) => { if (KEYS[e.code]) held.delete(KEYS[e.code]); });
window.addEventListener('blur', () => held.clear());

const advance = (n) => { for (let i = 0; i < n; i++) step(g, held); };
const draw = createView(document.getElementById('game'), g);
const hud = document.getElementById('hud-score');
const banner = document.getElementById('banner');
const BANNERS = { game_over: 'Game over', won: 'You win' };

let last = performance.now(), owed = 0;
function frame(now) {
  owed = g.paused ? 0 : Math.min(owed + (now - last) / 1000, 0.25);
  last = now;
  while (owed >= DT) { advance(1); owed -= DT; }
  hud.textContent = `Score ${g.score}   Lives ${g.lives}`;
  banner.textContent = BANNERS[g.state] || '';
  banner.hidden = !BANNERS[g.state];
  draw();
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
initTools(g, advance);
