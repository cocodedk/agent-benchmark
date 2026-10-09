// The three.js scene: draws the simulation state, never changes it.
import * as THREE from 'three';
import { game, RADIUS } from './game.js';

const ROW_COLOURS = [0xe74c3c, 0xe67e22, 0xf1c40f, 0x2ecc71, 0x3498db];

const renderer = new THREE.WebGLRenderer({ antialias: true });
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x10131c);
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 200);
camera.position.set(0, 30, 26);
camera.lookAt(0, 0, 1.5);

scene.add(new THREE.AmbientLight(0xffffff, 0.6));
const sun = new THREE.DirectionalLight(0xffffff, 1.6);
sun.position.set(-6, 20, 10);
scene.add(sun);

function box(w, h, d, colour, x, y, z) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshStandardMaterial({ color: colour }));
  mesh.position.set(x, y, z);
  scene.add(mesh);
  return mesh;
}

box(20, 0.2, 28, 0x24304a, 0, -0.1, 0);
box(0.5, 1, 28.5, 0x8899aa, -10.25, 0.5, -0.25);
box(0.5, 1, 28.5, 0x8899aa, 10.25, 0.5, -0.25);
box(21, 1, 0.5, 0x8899aa, 0, 0.5, -14.25);

const brickMeshes = new Map();
for (const b of game.bricks) brickMeshes.set(b.id, box(2.44, 0.8, 0.94, ROW_COLOURS[b.row], b.x, 0.4, b.z));

const paddle = box(4, 0.5, 0.5, 0xecf0f1, 0, 0.25, 12);
const ball = new THREE.Mesh(new THREE.SphereGeometry(RADIUS, 24, 16), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0x444444 }));
ball.position.y = RADIUS;
scene.add(ball);

function resize() {
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  camera.aspect = window.innerWidth / window.innerHeight;
  // Keep the whole field in view on narrow windows by widening the vertical angle.
  camera.fov = camera.aspect < 1.2 ? 45 * (1.2 / camera.aspect) ** 0.6 : 45;
  camera.updateProjectionMatrix();
}
window.addEventListener('resize', resize);
resize();

export function render() {
  const standing = new Set(game.bricks.map((b) => b.id));
  for (const [id, mesh] of brickMeshes) mesh.visible = standing.has(id);
  paddle.position.x = game.paddleX;
  ball.position.x = game.ball.x;
  ball.position.z = game.ball.z;
  renderer.render(scene, camera);
}
