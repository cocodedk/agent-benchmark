// The simulation: plain state advanced in fixed 1/60 s steps. No three.js here.
export const DT = 1 / 60;
export const SPEED = 10;
export const RADIUS = 0.3;
const PADDLE_Z = 12, PADDLE_FRONT = 11.75, PADDLE_SPEED = 12, PADDLE_MAX = 8;
const REST_Z = PADDLE_FRONT - RADIUS;
const BRICK_HALF_X = 1.25, BRICK_HALF_Z = 0.5;

export const game = { paddleX: 0, ball: null, bricks: [], score: 0, lives: 3, state: 'playing', paused: false };
export const keys = { left: false, right: false };

function newBricks() {
  const bricks = [];
  for (let r = 0; r < 5; r++)
    for (let c = 0; c < 8; c++) bricks.push({ id: `r${r}c${c}`, row: r, x: -8.75 + 2.5 * c, z: -11.5 + r });
  return bricks;
}

function restBall() {
  game.ball = { x: game.paddleX, z: REST_Z, vx: 0, vz: 0, moving: false };
}

export function reset() {
  Object.assign(game, { paddleX: 0, bricks: newBricks(), score: 0, lives: 3, state: 'playing' });
  restBall();
}

export function launch() {
  if (game.state !== 'playing' || game.ball.moving) return false;
  Object.assign(game.ball, { vx: 0, vz: -SPEED, moving: true });
  return true;
}

export function placePaddle(x) {
  game.paddleX = x;
  if (!game.ball.moving) game.ball.x = x;
}

// How far the ball's centre is from a brick's box, per axis (negative inside).
function gaps(b, x, z) {
  return [Math.abs(x - b.x) - BRICK_HALF_X, Math.abs(z - b.z) - BRICK_HALF_Z];
}

export function touches(b, x, z) {
  const [gx, gz] = gaps(b, x, z).map((g) => Math.max(g, 0));
  return gx * gx + gz * gz < RADIUS * RADIUS;
}

// Puts the ball in play there; answers an error string or null.
export function placeBall(x, z, vx, vz) {
  const len = Math.hypot(vx, vz);
  if (len === 0) return 'the direction (vx, vz) must not be zero';
  if (x - RADIUS < -10 || x + RADIUS > 10 || z - RADIUS < -14) return 'the ball would overlap a wall';
  if (z > 14) return 'the spot is outside the field';
  if (game.bricks.some((b) => touches(b, x, z))) return 'the ball would overlap a brick';
  game.ball = { x, z, vx: (SPEED * vx) / len, vz: (SPEED * vz) / len, moving: true };
  return null;
}

function hitBricks(ball) {
  const hit = game.bricks.filter((b) => touches(b, ball.x, ball.z));
  if (!hit.length) return;
  game.bricks = game.bricks.filter((b) => !hit.includes(b));
  game.score += 10 * hit.length;
  const near = hit.reduce((a, b) => (Math.hypot(a.x - ball.x, a.z - ball.z) <= Math.hypot(b.x - ball.x, b.z - ball.z) ? a : b));
  const [gx, gz] = gaps(near, ball.x, ball.z);
  if (gz >= gx) ball.vz = Math.sign(ball.z - near.z) * Math.abs(ball.vz);
  else ball.vx = Math.sign(ball.x - near.x) * Math.abs(ball.vx);
  if (!game.bricks.length) game.state = 'won';
}

function moveBall(ball) {
  ball.x += ball.vx * DT;
  ball.z += ball.vz * DT;
  if ((ball.x - RADIUS <= -10 && ball.vx < 0) || (ball.x + RADIUS >= 10 && ball.vx > 0)) ball.vx = -ball.vx;
  if (ball.z - RADIUS <= -14 && ball.vz < 0) ball.vz = -ball.vz;
  const offX = ball.x - game.paddleX;
  if (ball.vz > 0 && ball.z + RADIUS >= PADDLE_FRONT && ball.z <= PADDLE_Z + 0.25 && Math.abs(offX) <= 2.3) {
    const a = (Math.PI / 3) * Math.max(-1, Math.min(1, offX / 2));
    ball.vx = SPEED * Math.sin(a);
    ball.vz = -SPEED * Math.cos(a);
  }
  hitBricks(ball);
  if (ball.z > 14) {
    game.lives -= 1;
    if (game.lives === 0) game.state = 'game_over';
    restBall();
  }
}

export function tick() {
  if (game.state !== 'playing') return;
  const dir = (keys.right ? 1 : 0) - (keys.left ? 1 : 0);
  game.paddleX = Math.max(-PADDLE_MAX, Math.min(PADDLE_MAX, game.paddleX + dir * PADDLE_SPEED * DT));
  if (game.ball.moving) moveBall(game.ball);
  else game.ball.x = game.paddleX;
}

export function snapshot() {
  const b = game.ball;
  return {
    ok: true,
    field: { width: 20, depth: 28 },
    paddle: { x: game.paddleX, z: PADDLE_Z, width: 4 },
    ball: { x: b.x, z: b.z, vx: b.vx, vz: b.vz, moving: b.moving },
    bricks: game.bricks.map(({ id, x, z }) => ({ id, x, z })),
    score: game.score, lives: game.lives, state: game.state, paused: game.paused,
  };
}

reset();
