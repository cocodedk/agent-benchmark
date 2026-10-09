// WebMCP tools: each one drives the same code the keys and the real-time loop use.
import { game, DT, reset, launch, placePaddle, placeBall, tick, snapshot } from './game.js';

const num = (v) => typeof v === 'number' && Number.isFinite(v);
const fail = (error) => ({ ok: false, error });
const obj = (input) => (input && typeof input === 'object' && !Array.isArray(input) ? input : {});

const TOOLS = [
  ['describe', 'Reads the game: field, paddle, ball, standing bricks, score, lives, state and pause.', {}, () => snapshot()],
  ['pause', 'Pauses (true) or resumes (false) real-time play; answers {ok, paused}.',
    { paused: { type: 'boolean' } },
    ({ paused }) => {
      if (typeof paused !== 'boolean') return fail('paused must be true or false');
      game.paused = paused;
      return { ok: true, paused };
    }],
  ['step', 'Only while paused: advances the game by seconds (0 < s <= 30) in 1/60 s steps with the keys held now; answers the state.',
    { seconds: { type: 'number', exclusiveMinimum: 0, maximum: 30 } },
    ({ seconds }) => {
      if (!game.paused) return fail('pause the game before stepping');
      if (!num(seconds) || seconds <= 0 || seconds > 30) return fail('seconds must be a number above 0 and at most 30');
      for (let i = Math.round(seconds / DT); i > 0; i--) tick();
      return snapshot();
    }],
  ['launch', 'Launches a resting ball straight up, as Space does; answers {ok, launched}, launched false if it was not resting or the game ended.',
    {}, () => ({ ok: true, launched: launch() })],
  ['place_paddle', 'Moves the paddle centre to x (-8 to 8), carrying a resting ball; answers the state.',
    { x: { type: 'number', minimum: -8, maximum: 8 } },
    ({ x }) => {
      if (!num(x) || x < -8 || x > 8) return fail('x must be a number from -8 to 8');
      placePaddle(x);
      return snapshot();
    }],
  ['place_ball', 'Puts the ball at (x, z) moving along (vx, vz) at 10 units/s; refuses a zero direction or a spot on a brick, a wall or off the field; answers the state.',
    { x: { type: 'number' }, z: { type: 'number' }, vx: { type: 'number' }, vz: { type: 'number' } },
    ({ x, z, vx, vz }) => {
      if (![x, z, vx, vz].every(num)) return fail('x, z, vx and vz must all be numbers');
      const error = placeBall(x, z, vx, vz);
      return error ? fail(error) : snapshot();
    }],
  ['reset', 'Starts a new game: 40 bricks, score 0, 3 lives, ball resting on the centred paddle; pause is kept; answers the state.',
    {}, () => { reset(); return snapshot(); }],
];

export function registerTools() {
  const mc = document.modelContext;
  if (!mc) return;
  for (const [name, description, properties, run] of TOOLS) {
    const execute = async (input) => {
      try { return run(obj(input)); } catch (e) { return fail(String(e)); }
    };
    const inputSchema = { type: 'object', properties, required: Object.keys(properties), additionalProperties: false };
    Promise.resolve()
      .then(() => mc.registerTool({ name, description, inputSchema, execute }))
      .catch(() => {});
  }
}
