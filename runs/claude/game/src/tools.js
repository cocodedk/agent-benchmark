// The WebMCP tools: each answers a JSON object and never throws.
import { newGame, launch, placePaddle, placeBall, badSpot, step, snapshot, DT, PADDLE } from './game.js';

const num = v => typeof v === 'number' && Number.isFinite(v);
const fail = error => ({ ok: false, error });
const obj = (properties, required = Object.keys(properties)) => ({ type: 'object', properties, required });
const number = { type: 'number' };

export function registerTools(g, keys) {
  const mc = document.modelContext;
  if (!mc) return;
  const tools = [
    ['describe', 'Reads the game: field, paddle, ball, standing bricks, score, lives, state and pause.', obj({}),
      () => snapshot(g)],
    ['pause', 'Pauses (true) or resumes (false) real-time play.', obj({ paused: { type: 'boolean' } }),
      ({ paused }) => {
        if (typeof paused !== 'boolean') return fail('paused must be true or false');
        g.paused = paused;
        return { ok: true, paused };
      }],
    ['step', 'While paused, advances the game by seconds (0 < s <= 30) in 1/60 s steps, reading the keys held now.',
      obj({ seconds: number }),
      ({ seconds }) => {
        if (!g.paused) return fail('pause the game first');
        if (!num(seconds) || seconds <= 0 || seconds > 30) return fail('seconds must be more than 0 and at most 30');
        for (let i = Math.round(seconds / DT); i > 0; i--) step(g, keys);
        return snapshot(g);
      }],
    ['launch', 'Launches a resting ball straight up the field, as Space does.', obj({}),
      () => ({ ok: true, launched: launch(g) })],
    ['place_paddle', 'Moves the paddle centre to x (-8 to 8); a resting ball moves with it.', obj({ x: number }),
      ({ x }) => {
        if (!num(x) || Math.abs(x) > PADDLE.maxX) return fail('x must be from -8 to 8');
        placePaddle(g, x);
        return snapshot(g);
      }],
    ['place_ball', 'Puts the ball at (x, z) moving in direction (vx, vz) at 10 units/s.',
      obj({ x: number, z: number, vx: number, vz: number }),
      ({ x, z, vx, vz }) => {
        if (![x, z, vx, vz].every(num)) return fail('x, z, vx and vz must be numbers');
        if (vx === 0 && vz === 0) return fail('the direction must not be zero');
        const bad = badSpot(g, x, z);
        if (bad) return fail(`that spot is ${bad}`);
        placeBall(g, x, z, vx, vz);
        return snapshot(g);
      }],
    ['reset', 'Starts a new game: 40 bricks, score 0, 3 lives, ball resting on the centred paddle.', obj({}),
      () => {
        Object.assign(g, newGame(g.paused));
        return snapshot(g);
      }],
  ];
  for (const [name, description, inputSchema, run] of tools) {
    mc.registerTool({
      name, description, inputSchema,
      execute: async input => {
        try {
          return run(input && typeof input === 'object' ? input : {});
        } catch (e) {
          return fail(String(e));
        }
      },
    });
  }
}
