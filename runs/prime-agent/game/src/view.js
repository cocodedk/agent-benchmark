// three.js picture of the game state. Reads the state, never changes it.
import * as THREE from 'three';
import { HALF_W, HALF_D, BALL_R, PADDLE_Z, PADDLE_W, PADDLE_D, BRICK_W, BRICK_D } from './game.js';

const ROW_COLOURS = [0xe74c3c, 0xe67e22, 0xf1c40f, 0x2ecc71, 0x3498db];

function box(w, h, d, colour, x, y, z) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshStandardMaterial({ color: colour }));
  mesh.position.set(x, y, z);
  return mesh;
}

export function createView(canvas, g) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x10131a);
  const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 200);
  camera.position.set(0, 34, 26);
  camera.lookAt(0, 0, 2);
  scene.add(new THREE.AmbientLight(0xffffff, 0.6));
  const sun = new THREE.DirectionalLight(0xffffff, 1.8);
  sun.position.set(-6, 20, 10);
  scene.add(sun);

  scene.add(box(2 * HALF_W, 0.2, 2 * HALF_D, 0x2c3e50, 0, -0.1, 0));
  scene.add(box(0.5, 1, 2 * HALF_D + 0.5, 0x95a5a6, -HALF_W - 0.25, 0.5, 0.25 / 2));
  scene.add(box(0.5, 1, 2 * HALF_D + 0.5, 0x95a5a6, HALF_W + 0.25, 0.5, 0.25 / 2));
  scene.add(box(2 * HALF_W + 1, 1, 0.5, 0x95a5a6, 0, 0.5, -HALF_D - 0.25));

  const bricks = new Map();
  for (const b of g.bricks) {
    const mesh = box(BRICK_W * 0.96, 0.8, BRICK_D * 0.9, ROW_COLOURS[b.row], b.x, 0.4, b.z);
    bricks.set(b.id, mesh);
    scene.add(mesh);
  }
  const paddle = box(PADDLE_W, 0.5, PADDLE_D, 0xecf0f1, 0, 0.25, PADDLE_Z);
  const ball = new THREE.Mesh(new THREE.SphereGeometry(BALL_R, 24, 16), new THREE.MeshStandardMaterial({ color: 0xffffff }));
  scene.add(paddle, ball);

  function resize() {
    const w = window.innerWidth, h = window.innerHeight;
    renderer.setSize(w, h, false);
    renderer.setPixelRatio(window.devicePixelRatio);
    camera.aspect = w / h;
    // Keep the whole 20-unit width in view on narrow windows too.
    camera.fov = Math.max(50, (2 * Math.atan(Math.tan((50 * Math.PI) / 360) * (1.2 / camera.aspect)) * 180) / Math.PI);
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', resize);
  resize();

  return function draw() {
    const standing = new Set(g.bricks.map((b) => b.id));
    for (const [id, mesh] of bricks) mesh.visible = standing.has(id);
    paddle.position.x = g.paddleX;
    ball.position.set(g.ball.x, BALL_R, g.ball.z);
    renderer.render(scene, camera);
  };
}
