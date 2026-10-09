// The simulation: plain state and fixed 1/60 s steps. No three.js here.
export const DT = 1 / 60;
export const HALF_W = 10, HALF_D = 14;
export const BALL_R = 0.3, SPEED = 10;
export const PADDLE_Z = 12, PADDLE_W = 4, PADDLE_D = 0.5, PADDLE_SPEED = 12, PADDLE_MAX = 8;
export const BRICK_W = 2.5, BRICK_D = 1, ROWS = 5, COLS = 8;
const FRONT = PADDLE_Z - PADDLE_D / 2; // 11.75
const REST_Z = FRONT - BALL_R; // 11.45

function bricks() {
  const out = [];
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) out.push({ id: `r${r}c${c}`, row: r, x: -8.75 + BRICK_W * c, z: -11.5 + r });
  }
  return out;
}

export function createGame() {
  const g = { paused: false };
  reset(g);
  return g;
}

export function reset(g) {
  Object.assign(g, {
    bricks: bricks(), score: 0, lives: 3, state: 'playing', paddleX: 0,
    ball: { x: 0, z: REST_Z, vx: 0, vz: 0, moving: false },
  });
}

function rest(g) {
  g.ball = { x: g.paddleX, z: REST_Z, vx: 0, vz: 0, moving: false };
}

export function launch(g) {
  if (g.state !== 'playing' || g.ball.moving) return false;
  Object.assign(g.ball, { vx: 0, vz: -SPEED, moving: true });
  return true;
}

export function placePaddle(g, x) {
  g.paddleX = x;
  if (!g.ball.moving) rest(g);
}

// How far a ball at (x, z) sits outside a brick along x and along z (negative: inside that span).
function gaps(b, x, z) {
  return [Math.abs(x - b.x) - BRICK_W / 2, Math.abs(z - b.z) - BRICK_D / 2];
}

export function touches(b, x, z) {
  const [gx, gz] = gaps(b, x, z);
  return Math.hypot(Math.max(gx, 0), Math.max(gz, 0)) < BALL_R;
}

// Why the ball cannot go there, or null when it can.
export function badSpot(g, x, z) {
  if (Math.abs(x) > HALF_W || Math.abs(z) > HALF_D) return 'outside the field';
  if (Math.abs(x) + BALL_R > HALF_W || z - BALL_R < -HALF_D) return 'overlaps a wall';
  const b = g.bricks.find((b) => touches(b, x, z));
  return b ? `overlaps brick ${b.id}` : null;
}

export function placeBall(g, x, z, vx, vz) {
  const n = Math.hypot(vx, vz);
  g.ball = { x, z, vx: (SPEED * vx) / n, vz: (SPEED * vz) / n, moving: true };
}

// One fixed step; keys is a Set of 'left' / 'right' held now.
export function step(g, keys) {
  if (g.state !== 'playing') return;
  const dir = (keys.has('right') ? 1 : 0) - (keys.has('left') ? 1 : 0);
  g.paddleX = Math.max(-PADDLE_MAX, Math.min(PADDLE_MAX, g.paddleX + dir * PADDLE_SPEED * DT));
  const ball = g.ball;
  if (!ball.moving) { ball.x = g.paddleX; return; }
  ball.x += ball.vx * DT;
  ball.z += ball.vz * DT;
  if (ball.x - BALL_R <= -HALF_W && ball.vx < 0) ball.vx = -ball.vx;
  if (ball.x + BALL_R >= HALF_W && ball.vx > 0) ball.vx = -ball.vx;
  if (ball.z - BALL_R <= -HALF_D && ball.vz < 0) ball.vz = -ball.vz;
  hitPaddle(g);
  hitBricks(g);
  if (ball.z > HALF_D) {
    g.lives -= 1;
    rest(g);
    if (g.lives === 0) g.state = 'game_over';
  }
}

function hitPaddle(g) {
  const ball = g.ball;
  const dx = ball.x - g.paddleX;
  if (ball.vz <= 0 || ball.z + BALL_R < FRONT || ball.z > PADDLE_Z + PADDLE_D / 2 || Math.abs(dx) > 2.3) return;
  const a = (60 * Math.max(-1, Math.min(1, dx / 2)) * Math.PI) / 180;
  ball.vx = SPEED * Math.sin(a);
  ball.vz = -SPEED * Math.cos(a);
}

function hitBricks(g) {
  const ball = g.ball;
  const hit = g.bricks.filter((b) => touches(b, ball.x, ball.z));
  if (!hit.length) return;
  g.bricks = g.bricks.filter((b) => !hit.includes(b));
  g.score += 10 * hit.length;
  const b = hit[0];
  const [gx, gz] = gaps(b, ball.x, ball.z);
  if (gz >= gx) ball.vz = ball.z < b.z ? -Math.abs(ball.vz) : Math.abs(ball.vz);
  else ball.vx = ball.x < b.x ? -Math.abs(ball.vx) : Math.abs(ball.vx);
  if (!g.bricks.length) g.state = 'won';
}

const r6 = (v) => Math.round(v * 1e6) / 1e6 + 0; // + 0 turns -0 into 0

export function snapshot(g) {
  const b = g.ball;
  return {
    ok: true,
    field: { width: 2 * HALF_W, depth: 2 * HALF_D },
    paddle: { x: r6(g.paddleX), z: PADDLE_Z, width: PADDLE_W },
    ball: { x: r6(b.x), z: r6(b.z), vx: r6(b.vx), vz: r6(b.vz), moving: b.moving },
    bricks: g.bricks.map(({ id, x, z }) => ({ id, x, z })),
    score: g.score, lives: g.lives, state: g.state, paused: g.paused,
  };
}
