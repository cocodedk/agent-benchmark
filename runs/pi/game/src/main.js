// Wires keys, the real-time loop, the head-up display and the WebMCP tools together.
import { game, keys, DT, tick, launch } from './game.js';
import { render } from './view.js';
import { registerTools } from './tools.js';

const LEFT = ['KeyA', 'ArrowLeft'], RIGHT = ['KeyD', 'ArrowRight'];

function onKey(e, down) {
  if (LEFT.includes(e.code)) keys.left = down;
  else if (RIGHT.includes(e.code)) keys.right = down;
  else if (e.code === 'Space') { if (down) launch(); }
  else return;
  e.preventDefault();
}
window.addEventListener('keydown', (e) => onKey(e, true));
window.addEventListener('keyup', (e) => onKey(e, false));
window.addEventListener('blur', () => { keys.left = keys.right = false; });

const score = document.getElementById('score');
const lives = document.getElementById('lives');
const banner = document.getElementById('banner');
const BANNERS = { playing: '', game_over: 'Game over', won: 'You win' };

function hud() {
  score.textContent = `Score ${game.score}`;
  lives.textContent = `Lives ${game.lives}`;
  banner.textContent = BANNERS[game.state];
  banner.hidden = game.state === 'playing';
}

let last = performance.now(), behind = 0;
function frame(now) {
  behind = game.paused ? 0 : Math.min(behind + (now - last) / 1000, 0.25);
  last = now;
  while (behind >= DT) { tick(); behind -= DT; }
  hud();
  render();
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
registerTools();
