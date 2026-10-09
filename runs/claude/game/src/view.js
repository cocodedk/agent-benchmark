// Draws the game with three.js and keeps the head-up display current.
import * as THREE from 'three';
import { FIELD, PADDLE, BALL, BRICK } from './game.js';

const ROW_COLOURS = [0xe74c3c, 0xe67e22, 0xf1c40f, 0x2ecc71, 0x3498db];

export function createView(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x10131a);
  const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 200);
  camera.position.set(0, 30, 24);
  camera.lookAt(0, 0, 1.5);

  scene.add(new THREE.AmbientLight(0xffffff, 0.6));
  const sun = new THREE.DirectionalLight(0xffffff, 1.6);
  sun.position.set(-6, 20, 10);
  scene.add(sun);

  const width = FIELD.right - FIELD.left, depth = FIELD.bottom - FIELD.top;
  const floor = new THREE.Mesh(new THREE.BoxGeometry(width, 0.2, depth),
    new THREE.MeshStandardMaterial({ color: 0x2c3e50 }));
  floor.position.y = -0.1;
  scene.add(floor);

  const wallMat = new THREE.MeshStandardMaterial({ color: 0x95a5a6 });
  for (const [w, d, x, z] of [[0.5, depth, FIELD.left - 0.25, 0], [0.5, depth, FIELD.right + 0.25, 0],
    [width + 1, 0.5, 0, FIELD.top - 0.25]]) {
    const wall = new THREE.Mesh(new THREE.BoxGeometry(w, 1, d), wallMat);
    wall.position.set(x, 0.5, z);
    scene.add(wall);
  }

  const brickGeo = new THREE.BoxGeometry(BRICK.width - 0.06, 0.6, BRICK.depth - 0.06);
  const brickMats = ROW_COLOURS.map(color => new THREE.MeshStandardMaterial({ color }));
  const brickMeshes = new Map();

  const paddle = new THREE.Mesh(new THREE.BoxGeometry(PADDLE.width, 0.5, PADDLE.depth),
    new THREE.MeshStandardMaterial({ color: 0xecf0f1 }));
  paddle.position.set(0, 0.25, PADDLE.z);
  scene.add(paddle);

  const ball = new THREE.Mesh(new THREE.SphereGeometry(BALL.radius, 24, 16),
    new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0x444444 }));
  scene.add(ball);

  const hud = document.getElementById('hud');
  const banner = document.getElementById('banner');

  function resize() {
    renderer.setSize(window.innerWidth, window.innerHeight);
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', resize);
  resize();

  return function draw(g) {
    const standing = new Set(g.bricks.map(b => b.id));
    for (const [id, mesh] of brickMeshes) {
      if (!standing.has(id)) { scene.remove(mesh); brickMeshes.delete(id); }
    }
    for (const b of g.bricks) {
      if (brickMeshes.has(b.id)) continue;
      const mesh = new THREE.Mesh(brickGeo, brickMats[b.row]);
      mesh.position.set(b.x, 0.3, b.z);
      scene.add(mesh);
      brickMeshes.set(b.id, mesh);
    }
    paddle.position.x = g.paddleX;
    ball.position.set(g.ball.x, BALL.radius, g.ball.z);
    hud.textContent = `Score ${g.score}   Lives ${g.lives}\nA/← and D/→ move · Space launches`;
    banner.textContent = g.state === 'won' ? 'You win' : g.state === 'game_over' ? 'Game over' : '';
    banner.hidden = g.state === 'playing';
    renderer.render(scene, camera);
  };
}
