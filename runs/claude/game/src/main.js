// Wires keys, real time, the view and the tools to one game.
import { newGame, launch, step, DT } from './game.js';
import { createView } from './view.js';
import { registerTools } from './tools.js';

const g = newGame();
const held = new Set();
const keys = {
  get left() { return held.has('KeyA') || held.has('ArrowLeft'); },
  get right() { return held.has('KeyD') || held.has('ArrowRight'); },
};

window.addEventListener('keydown', e => {
  held.add(e.code);
  if (e.code === 'Space') { e.preventDefault(); launch(g); }
});
window.addEventListener('keyup', e => held.delete(e.code));
window.addEventListener('blur', () => held.clear());

registerTools(g, keys);
const draw = createView(document.getElementById('game'));

let last = performance.now(), acc = 0;
function frame(now) {
  acc = g.paused ? 0 : Math.min(acc + (now - last) / 1000, 0.25);
  last = now;
  while (acc >= DT) { step(g, keys); acc -= DT; }
  draw(g);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
