// The simulation: no three.js, no DOM. One step is 1/60 s.
export const DT = 1 / 60;
export const FIELD = { left: -10, right: 10, top: -14, bottom: 14 };
export const PADDLE = { z: 12, width: 4, depth: 0.5, speed: 12, maxX: 8 };
export const BALL = { radius: 0.3, speed: 10, restZ: 11.45 };
export const BRICK = { width: 2.5, depth: 1, rows: 5, cols: 8 };
const FRONT = PADDLE.z - PADDLE.depth / 2;

function makeBricks() {
  const bricks = [];
  for (let r = 0; r < BRICK.rows; r++) {
    for (let c = 0; c < BRICK.cols; c++) {
      bricks.push({ id: `r${r}c${c}`, row: r, x: -8.75 + 2.5 * c, z: -11.5 + r });
    }
  }
  return bricks;
}

export function newGame(paused = false) {
  return {
    paddleX: 0,
    ball: { x: 0, z: BALL.restZ, vx: 0, vz: 0, moving: false },
    bricks: makeBricks(),
    score: 0, lives: 3, state: 'playing', paused,
  };
}

function rest(g) {
  g.ball = { x: g.paddleX, z: BALL.restZ, vx: 0, vz: 0, moving: false };
}

export function launch(g) {
  if (g.ball.moving || g.state !== 'playing') return false;
  g.ball.vx = 0;
  g.ball.vz = -BALL.speed;
  g.ball.moving = true;
  return true;
}

export function placePaddle(g, x) {
  g.paddleX = x;
  if (!g.ball.moving) g.ball.x = x;
}

// Does a ball centred at (x, z) touch the brick?
function touches(b, x, z) {
  const dx = Math.max(Math.abs(x - b.x) - BRICK.width / 2, 0);
  const dz = Math.max(Math.abs(z - b.z) - BRICK.depth / 2, 0);
  return dx * dx + dz * dz < BALL.radius * BALL.radius;
}

// Why place_ball would refuse (x, z), or null.
export function badSpot(g, x, z) {
  const r = BALL.radius;
  if (x < FIELD.left || x > FIELD.right || z < FIELD.top || z > FIELD.bottom) return 'outside the field';
  if (x - r < FIELD.left || x + r > FIELD.right || z - r < FIELD.top) return 'overlaps a wall';
  if (g.bricks.some(b => touches(b, x, z))) return 'overlaps a brick';
  return null;
}

export function placeBall(g, x, z, vx, vz) {
  const len = Math.hypot(vx, vz);
  g.ball = { x, z, vx: (vx / len) * BALL.speed, vz: (vz / len) * BALL.speed, moving: true };
}

function moveBall(g) {
  const b = g.ball, r = BALL.radius;
  b.x += b.vx * DT;
  b.z += b.vz * DT;

  if (b.x - r < FIELD.left && b.vx < 0) b.vx = -b.vx;
  if (b.x + r > FIELD.right && b.vx > 0) b.vx = -b.vx;
  if (b.z - r < FIELD.top && b.vz < 0) b.vz = -b.vz;

  if (b.vz > 0 && b.z + r >= FRONT && b.z <= PADDLE.z && Math.abs(b.x - g.paddleX) <= 2.3) {
    const offset = Math.min(1, Math.max(-1, (b.x - g.paddleX) / 2));
    const a = (60 * offset * Math.PI) / 180;
    b.vx = BALL.speed * Math.sin(a);
    b.vz = -BALL.speed * Math.cos(a);
  }

  const hit = g.bricks.filter(k => touches(k, b.x, b.z));
  if (hit.length) {
    g.bricks = g.bricks.filter(k => !hit.includes(k));
    g.score += 10 * hit.length;
    const k = hit[0];
    const overX = Math.abs(b.x - k.x) - BRICK.width / 2;
    const overZ = Math.abs(b.z - k.z) - BRICK.depth / 2;
    if (overZ >= overX) b.vz = -b.vz;
    else b.vx = -b.vx;
    if (!g.bricks.length) g.state = 'won';
  }

  if (b.z > FIELD.bottom) {
    g.lives -= 1;
    if (g.lives <= 0) g.state = 'game_over';
    rest(g);
  }
}

// One 1/60 s step; keys is {left, right}, read now.
export function step(g, keys) {
  if (g.state !== 'playing') return;
  const dir = (keys.right ? 1 : 0) - (keys.left ? 1 : 0);
  if (dir) placePaddle(g, Math.min(PADDLE.maxX, Math.max(-PADDLE.maxX, g.paddleX + dir * PADDLE.speed * DT)));
  if (g.ball.moving) moveBall(g);
}

export function snapshot(g) {
  return {
    ok: true,
    field: { width: FIELD.right - FIELD.left, depth: FIELD.bottom - FIELD.top },
    paddle: { x: g.paddleX, z: PADDLE.z, width: PADDLE.width },
    ball: { ...g.ball },
    bricks: g.bricks.map(({ id, x, z }) => ({ id, x, z })),
    score: g.score, lives: g.lives, state: g.state, paused: g.paused,
  };
}
