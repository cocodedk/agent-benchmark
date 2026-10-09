// WebMCP tools: an agent plays and tests the game through these. Silent without document.modelContext.
import { PADDLE_MAX, launch, placePaddle, placeBall, badSpot, reset, snapshot } from './game.js';

const given = (input) => (input && typeof input === 'object' && !Array.isArray(input) ? input : {});
const refuse = (error) => ({ ok: false, error });
const num = (v) => typeof v === 'number' && Number.isFinite(v);
const NUM = { type: 'number' };

function tools(g, advance) {
  return [
    {
      name: 'describe',
      description: 'Read the game: field size, paddle, ball, standing bricks, score, lives, state and pause.',
      inputSchema: { type: 'object', properties: {} },
      annotations: { readOnlyHint: true },
      execute: () => snapshot(g),
    },
    {
      name: 'pause',
      description: 'Pause (true) or resume (false) real-time play; answers {ok, paused}.',
      inputSchema: { type: 'object', properties: { paused: { type: 'boolean' } }, required: ['paused'] },
      execute: (input) => {
        const { paused } = given(input);
        if (typeof paused !== 'boolean') return refuse('paused must be true or false');
        g.paused = paused;
        return { ok: true, paused };
      },
    },
    {
      name: 'step',
      description: 'While paused, advance the game by seconds (0 < s <= 30) in 1/60 s steps with the keys held now; answers the state.',
      inputSchema: { type: 'object', properties: { seconds: NUM }, required: ['seconds'] },
      execute: (input) => {
        const { seconds } = given(input);
        if (!g.paused) return refuse('step works only while paused; call pause with {"paused": true} first');
        if (!num(seconds) || seconds <= 0 || seconds > 30) return refuse('seconds must be a number above 0 and at most 30');
        advance(Math.max(1, Math.round(seconds * 60)));
        return snapshot(g);
      },
    },
    {
      name: 'launch',
      description: 'Launch the ball resting on the paddle straight up, as Space does; launched is false when it cannot.',
      inputSchema: { type: 'object', properties: {} },
      execute: () => ({ ok: true, launched: launch(g) }),
    },
    {
      name: 'place_paddle',
      description: 'Move the paddle centre to x (-8 to 8); a resting ball moves with it. Answers the state.',
      inputSchema: { type: 'object', properties: { x: NUM }, required: ['x'] },
      execute: (input) => {
        const { x } = given(input);
        if (!num(x) || Math.abs(x) > PADDLE_MAX) return refuse('x must be a number from -8 to 8');
        placePaddle(g, x);
        return snapshot(g);
      },
    },
    {
      name: 'place_ball',
      description: 'Put the ball at (x, z) moving in direction (vx, vz) at 10 units/s; refuses a zero direction or a spot on a brick, a wall or outside the field. Answers the state.',
      inputSchema: { type: 'object', properties: { x: NUM, z: NUM, vx: NUM, vz: NUM }, required: ['x', 'z', 'vx', 'vz'] },
      execute: (input) => {
        const { x, z, vx, vz } = given(input);
        if (![x, z, vx, vz].every(num)) return refuse('x, z, vx and vz must all be numbers');
        if (vx === 0 && vz === 0) return refuse('the direction (vx, vz) must not be zero');
        const bad = badSpot(g, x, z);
        if (bad) return refuse(`the ball cannot go there: ${bad}`);
        placeBall(g, x, z, vx, vz);
        return snapshot(g);
      },
    },
    {
      name: 'reset',
      description: 'Start a new game: 40 bricks, score 0, 3 lives, paddle at 0, ball resting; pause stays. Answers the state.',
      inputSchema: { type: 'object', properties: {} },
      execute: () => { reset(g); return snapshot(g); },
    },
  ];
}

export function initTools(g, advance) {
  const mc = document.modelContext;
  if (!mc || typeof mc.registerTool !== 'function') return;
  for (const tool of tools(g, advance)) {
    Promise.resolve().then(() => mc.registerTool(tool)).catch(() => {});
  }
}
