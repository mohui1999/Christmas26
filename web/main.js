import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { initTreeFx, updateTreeFx } from './tree_fx.js?v=20261123g';
import { initSceneFx, updateSceneFx } from './scene_fx.js?v=20261123g';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { SMAAPass } from 'three/addons/postprocessing/SMAAPass.js';

const stage = document.getElementById('stage');
const canvas = document.getElementById('scene');
const loaderEl = document.getElementById('loader');
const progressFill = document.getElementById('progress-fill');
const loaderStatus = document.getElementById('loader-status');
const errorBtn = document.getElementById('loader-error-btn');
const lightbox = document.getElementById('lightbox');

const isMobile = () => window.matchMedia('(max-width: 900px)').matches;
// 轻量通道：移动端/微信默认启用；?full=1 桌面强制关闭，?lite=1 桌面强制开启
const _params = new URLSearchParams(location.search);
const _touch = (navigator.maxTouchPoints || 0) > 0;
const LITE = _params.has('lite') || ((/MicroMessenger|Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent) || (isMobile() && _touch)) && !_params.has('full'));
const _loaderNote = document.querySelector('.loader-note');
if (_loaderNote) _loaderNote.textContent = LITE ? '6.2 MB 轻量场景 · 首次加载约几秒' : '52 MB Draco 压缩场景 · 首次加载需要几秒';

// ------------------------------------------------------------------ renderer
const renderer = new THREE.WebGLRenderer({
  canvas, antialias: !LITE, powerPreference: LITE ? 'default' : 'high-performance', alpha: false,
});
const LITE_DPR = Math.min(window.devicePixelRatio || 1, 1.25);
renderer.setPixelRatio(LITE ? LITE_DPR : Math.min(window.devicePixelRatio || 1, 1.8));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = LITE ? 1.12 : 0.92;
renderer.shadowMap.enabled = !LITE;
renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.setClearColor(0x08111d, 1);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x08111d);
scene.fog = new THREE.FogExp2(0x0a1422, 0.0042);

// screen-space blue-hour gradient (stable under an orthographic camera)
function makeSkyTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 1024;
  const g = c.getContext('2d');
  const base = g.createLinearGradient(0, 0, 0, 1024);
  base.addColorStop(0, '#081322');
  base.addColorStop(0.55, '#0c1c2e');
  base.addColorStop(1, '#040910');
  g.fillStyle = base;
  g.fillRect(0, 0, 1024, 1024);
  // blue-hour halo behind the diorama
  const halo = g.createRadialGradient(520, 600, 30, 520, 600, 620);
  halo.addColorStop(0.00, 'rgba(72,116,158,0.85)');
  halo.addColorStop(0.28, 'rgba(46,82,118,0.55)');
  halo.addColorStop(0.55, 'rgba(24,45,68,0.30)');
  halo.addColorStop(0.82, 'rgba(10,20,33,0.08)');
  halo.addColorStop(1.00, 'rgba(0,0,0,0)');
  g.fillStyle = halo;
  g.fillRect(0, 0, 1024, 1024);
  // subdued warm horizon
  const warm = g.createRadialGradient(500, 700, 20, 500, 700, 360);
  warm.addColorStop(0, 'rgba(196,137,82,0.16)');
  warm.addColorStop(0.5, 'rgba(110,84,64,0.05)');
  warm.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = warm;
  g.fillRect(0, 0, 1024, 1024);

  // distant moon and soft cloud veils
  const mx = 552, my = 468;
  const moonHalo = g.createRadialGradient(mx, my, 3, mx, my, 34);
  moonHalo.addColorStop(0, 'rgba(236,228,202,0.32)');
  moonHalo.addColorStop(0.25, 'rgba(206,205,190,0.14)');
  moonHalo.addColorStop(0.6, 'rgba(150,164,184,0.04)');
  moonHalo.addColorStop(1, 'rgba(120,140,165,0)');
  g.fillStyle = moonHalo;
  g.fillRect(0, 0, 1024, 1024);
  const moonDisc = g.createRadialGradient(mx - 2, my - 2, 1, mx, my, 6);
  moonDisc.addColorStop(0, 'rgba(255,252,238,0.98)');
  moonDisc.addColorStop(0.55, 'rgba(238,231,205,0.92)');
  moonDisc.addColorStop(1, 'rgba(205,200,182,0.72)');
  g.fillStyle = moonDisc;
  g.beginPath();
  g.arc(mx, my, 6, 0, Math.PI * 2);
  g.fill();
  g.globalCompositeOperation = 'source-over';
  for (const [cx, cy, rx, ry, a] of [[590, 300, 260, 42, 0.055], [850, 370, 300, 54, 0.045], [380, 460, 240, 38, 0.035]]) {
    const cl = g.createRadialGradient(cx, cy, 4, cx, cy, rx);
    cl.addColorStop(0, 'rgba(150,177,204,' + a + ')');
    cl.addColorStop(0.6, 'rgba(90,120,150,' + (a * 0.45) + ')');
    cl.addColorStop(1, 'rgba(70,100,130,0)');
    g.fillStyle = cl;
    g.save();
    g.translate(cx, cy);
    g.scale(1, ry / rx);
    g.beginPath();
    g.arc(0, 0, rx, 0, Math.PI * 2);
    g.fill();
    g.restore();
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.magFilter = THREE.LinearFilter;
  tex.minFilter = THREE.LinearFilter;
  return tex;
}
// screen-aligned gradient plane (works cleanly with an orthographic camera)
const bgTexture = makeSkyTexture();
const bgPlane = new THREE.Mesh(
  new THREE.PlaneGeometry(1, 1),
  new THREE.MeshBasicMaterial({
    map: bgTexture, depthTest: false, depthWrite: false, toneMapped: true, fog: false,
  })
);
bgPlane.scale.set(400, 400, 1);
bgPlane.position.set(0, 0, -150);
bgPlane.renderOrder = -10;
scene.background = null;

const FRUSTUM = 26.5;
const camera = new THREE.OrthographicCamera(-FRUSTUM * 1.5, FRUSTUM * 1.5, FRUSTUM, -FRUSTUM, 0.1, 300);
const home = {
  position: new THREE.Vector3(-30, 38, 58),
  target: new THREE.Vector3(0, 6.5, 0),
};
camera.position.copy(home.position);
camera.add(bgPlane);
scene.add(camera);

const controls = new OrbitControls(camera, canvas);
controls.target.copy(home.target);
controls.enableDamping = true;
controls.dampingFactor = 0.055;
controls.rotateSpeed = 0.6;
controls.zoomSpeed = 0.8;
controls.panSpeed = 0.6;
controls.minZoom = 0.62;
controls.maxZoom = 3.2;
controls.minPolarAngle = 0.18;
controls.maxPolarAngle = Math.PI * 0.49;
controls.autoRotateSpeed = 0.55;
controls.update();

// ------------------------------------------------------------- walk camera
const walkCamera = new THREE.PerspectiveCamera(70, 1, 0.1, 400);
walkCamera.position.set(0, 6.2, 16);
const walkBg = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), bgPlane.material);
walkBg.scale.set(400, 400, 1);
walkBg.position.set(0, 0, -150);
walkBg.renderOrder = -10;
walkBg.visible = false;
walkCamera.add(walkBg);
scene.add(walkCamera);

const walkControls = new OrbitControls(walkCamera, canvas);
walkControls.enabled = false;
walkControls.enableDamping = true;
walkControls.dampingFactor = 0.07;
walkControls.rotateSpeed = 0.6;
walkControls.zoomSpeed = 0.8;
walkControls.enablePan = false;
walkControls.minDistance = 3.2;
walkControls.maxDistance = 16;
walkControls.minPolarAngle = 0.25;
walkControls.maxPolarAngle = Math.PI * 0.50;
walkControls.autoRotate = false;
walkControls.update();
let walkLookOffset = 0;
let walkLookDragY = null;

// ---------------------------------------------------------------- environment
if (!LITE) {
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.12;
} else {
  // tiny cheap gradient env so metals and gold still catch a highlight
  const ec = document.createElement('canvas');
  ec.width = 128; ec.height = 64;
  const eg = ec.getContext('2d');
  const grad = eg.createLinearGradient(0, 0, 0, 64);
  grad.addColorStop(0, '#223c58');
  grad.addColorStop(0.48, '#8d7f72');
  grad.addColorStop(0.55, '#d6a06a');
  grad.addColorStop(0.7, '#3a3026');
  grad.addColorStop(1, '#0a1119');
  eg.fillStyle = grad; eg.fillRect(0, 0, 128, 64);
  const etex = new THREE.CanvasTexture(ec);
  etex.mapping = THREE.EquirectangularReflectionMapping;
  etex.colorSpace = THREE.SRGBColorSpace;
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromEquirectangular(etex).texture;
  scene.environmentIntensity = 0.38;
  etex.dispose(); pmrem.dispose();
}

scene.add(new THREE.HemisphereLight(0x9bbce6, 0x2a1d18, LITE ? 0.62 : 0.38));
const moon = new THREE.DirectionalLight(0xbcd5ff, LITE ? 1.35 : 0.95);
moon.position.set(-26, 38, 30);
moon.castShadow = !LITE;
moon.shadow.mapSize.set(LITE ? 1024 : 3072, LITE ? 1024 : 3072);
moon.shadow.camera.left = -38;
moon.shadow.camera.right = 38;
moon.shadow.camera.top = 38;
moon.shadow.camera.bottom = -38;
moon.shadow.camera.near = 1;
moon.shadow.camera.far = 130;
moon.shadow.bias = -0.0004;
moon.shadow.normalBias = 0.035;
scene.add(moon);

const warm = new THREE.PointLight(0xffb267, LITE ? 250 : 155, LITE ? 64 : 48, 2);
warm.position.set(0, 7.5, 11);
scene.add(warm);
if (!LITE) {
  const warm2 = new THREE.PointLight(0xffa45c, 62, 34, 2);
  warm2.position.set(-2, 4.5, -13);
  scene.add(warm2);
  const treeGlow = new THREE.PointLight(0xffb060, 130, 38, 2);
  treeGlow.position.set(0, 11, 0);
  scene.add(treeGlow);
}

scene.add(new THREE.AmbientLight(0x22344d, LITE ? 0.2 : 0.12));

// --------------------------------------------------------------------- stars
function makeStarPointTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(32, 32, 1, 32, 32, 31);
  grd.addColorStop(0, 'rgba(255,255,255,1)');
  grd.addColorStop(0.28, 'rgba(225,240,255,0.95)');
  grd.addColorStop(0.65, 'rgba(170,205,245,0.35)');
  grd.addColorStop(1, 'rgba(140,180,230,0)');
  g.fillStyle = grd;
  g.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
const starPointTexture = makeStarPointTexture();

const starPositions = [];
for (let i = 0; i < 760; i++) {
  const theta = Math.random() * Math.PI * 2;
  const phi = Math.acos(THREE.MathUtils.randFloat(0.02, 0.95));
  const r = 120;
  const x = Math.sin(phi) * Math.cos(theta) * r;
  const z = Math.sin(phi) * Math.sin(theta) * r;
  const y = Math.cos(phi) * r;
  if (y < 8) continue;
  starPositions.push(x, y, z);
}
const starGeo = new THREE.BufferGeometry();
starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPositions, 3));
const stars = new THREE.Points(starGeo, new THREE.PointsMaterial({
  color: 0xc7dcff, size: 0.9, sizeAttenuation: true, transparent: true,
  map: starPointTexture, alphaTest: 0.02, opacity: 0.8, depthWrite: false, fog: false,
}));
scene.add(stars);

// ---------------------------------------------------------------------- snow
function makeSnowTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(32, 32, 1, 32, 32, 31);
  grd.addColorStop(0, 'rgba(255,255,255,1)');
  grd.addColorStop(0.35, 'rgba(240,248,255,0.9)');
  grd.addColorStop(0.75, 'rgba(220,238,255,0.25)');
  grd.addColorStop(1, 'rgba(210,230,255,0)');
  g.fillStyle = grd;
  g.fillRect(0, 0, 64, 64);
  g.strokeStyle = 'rgba(245,252,255,0.55)';
  g.lineWidth = 1.2;
  for (let i = 0; i < 6; i++) {
    const a = i / 6 * Math.PI * 2;
    g.beginPath();
    g.moveTo(32, 32);
    g.lineTo(32 + Math.cos(a) * 26, 32 + Math.sin(a) * 26);
    g.stroke();
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
const snowTexture = makeSnowTexture();
const SNOW_COUNT = 520;
const snowPos = new Float32Array(SNOW_COUNT * 3);
const snowSpeed = new Float32Array(SNOW_COUNT);
for (let i = 0; i < SNOW_COUNT; i++) {
  snowPos[i * 3] = THREE.MathUtils.randFloat(-34, 34);
  snowPos[i * 3 + 1] = THREE.MathUtils.randFloat(1, 34);
  snowPos[i * 3 + 2] = THREE.MathUtils.randFloat(-34, 34);
  snowSpeed[i] = THREE.MathUtils.randFloat(0.012, 0.045);
}
const snowGeo = new THREE.BufferGeometry();
snowGeo.setAttribute('position', new THREE.BufferAttribute(snowPos, 3));
const snow = new THREE.Points(snowGeo, new THREE.PointsMaterial({
  color: 0xe4efff, size: 0.34, sizeAttenuation: true, transparent: true,
  map: snowTexture, alphaTest: 0.02, opacity: 0.8, depthWrite: false, fog: true,
}));
scene.add(snow);

// ---------------------------------------------------------------- ground glow
function radialTexture(inner, outer) {
  const c = document.createElement('canvas');
  c.width = c.height = 512;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(256, 256, 10, 256, 256, 250);
  grd.addColorStop(0, inner);
  grd.addColorStop(0.55, outer);
  grd.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = grd;
  g.fillRect(0, 0, 512, 512);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}
const glowTex = radialTexture('rgba(103,141,190,0.30)', 'rgba(42,74,116,0.12)');
const glowDisc = new THREE.Mesh(
  new THREE.CircleGeometry(44, 96),
  new THREE.MeshBasicMaterial({ map: glowTex, transparent: true, depthWrite: false, opacity: 0.9 })
);
glowDisc.rotation.x = -Math.PI / 2;
glowDisc.position.y = 0.02;
scene.add(glowDisc);

function radialAlphaTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 512;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(256, 256, 40, 256, 256, 254);
  grd.addColorStop(0, 'rgba(255,255,255,1)');
  grd.addColorStop(0.52, 'rgba(255,255,255,0.92)');
  grd.addColorStop(0.78, 'rgba(255,255,255,0.40)');
  grd.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grd;
  g.fillRect(0, 0, 512, 512);
  return new THREE.CanvasTexture(c);
}
const ground = new THREE.Mesh(
  new THREE.CircleGeometry(30, 96),
  new THREE.MeshStandardMaterial({
    color: 0x07101a, roughness: 0.84, metalness: 0.1,
    transparent: true, alphaMap: radialAlphaTexture(), depthWrite: false,
  })
);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.035;
ground.receiveShadow = true;
// the diorama is intentionally presented as a floating object
scene.add(ground);
ground.visible = false;

// ------------------------------------------------------------------ wanderer
const GROUND_Y = 1.885;
const UP = new THREE.Vector3(0, 1, 0);

function makeHaloTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(128, 128, 2, 128, 128, 126);
  grd.addColorStop(0, 'rgba(255,255,255,1)');
  grd.addColorStop(0.18, 'rgba(255,245,225,0.92)');
  grd.addColorStop(0.45, 'rgba(255,204,142,0.38)');
  grd.addColorStop(0.75, 'rgba(255,170,100,0.08)');
  grd.addColorStop(1, 'rgba(255,150,80,0)');
  g.fillStyle = grd;
  g.fillRect(0, 0, 256, 256);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
const haloTexture = makeHaloTexture();

function makeHeadTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 512;
  const g = c.getContext('2d');
  const grad = g.createLinearGradient(0, 0, 0, 512);
  grad.addColorStop(0.00, '#fff2d6');
  grad.addColorStop(0.22, '#ffe0b2');
  grad.addColorStop(0.55, '#edc18c');
  grad.addColorStop(0.80, '#cb8f5e');
  grad.addColorStop(1.00, '#8f5134');
  g.fillStyle = grad;
  g.fillRect(0, 0, 512, 512);
  const hl = g.createRadialGradient(180, 140, 8, 180, 140, 230);
  hl.addColorStop(0, 'rgba(255,255,250,0.6)');
  hl.addColorStop(0.5, 'rgba(255,248,232,0.16)');
  hl.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = hl;
  g.fillRect(0, 0, 512, 512);
  for (const cx of [140, 372]) {
    const blush = g.createRadialGradient(cx, 336, 4, cx, 336, 86);
    blush.addColorStop(0, 'rgba(255,160,130,0.16)');
    blush.addColorStop(1, 'rgba(255,160,130,0)');
    g.fillStyle = blush;
    g.fillRect(0, 0, 512, 512);
  }
  const shade = g.createLinearGradient(0, 380, 0, 512);
  shade.addColorStop(0, 'rgba(90,45,24,0)');
  shade.addColorStop(1, 'rgba(90,45,24,0.22)');
  g.fillStyle = shade;
  g.fillRect(0, 0, 512, 512);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function makeCapeTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 512;
  const g = c.getContext('2d');
  const base = g.createLinearGradient(0, 0, 0, 512);
  base.addColorStop(0.00, '#a9664b');
  base.addColorStop(0.38, '#95573d');
  base.addColorStop(0.72, '#7b4531');
  base.addColorStop(1.00, '#5c3124');
  g.fillStyle = base;
  g.fillRect(0, 0, 512, 512);
  // soft broad folds
  const folds = [38, 96, 158, 224, 286, 352, 418, 476];
  for (const x of folds) {
    const fg = g.createLinearGradient(x - 26, 0, x + 26, 0);
    fg.addColorStop(0, 'rgba(44,21,14,0)');
    fg.addColorStop(0.5, 'rgba(44,21,14,0.16)');
    fg.addColorStop(1, 'rgba(44,21,14,0)');
    g.fillStyle = fg;
    g.fillRect(x - 26, 0, 52, 512);
    const hg = g.createLinearGradient(x + 8, 0, x + 22, 0);
    hg.addColorStop(0, 'rgba(255,205,160,0)');
    hg.addColorStop(0.5, 'rgba(255,205,160,0.08)');
    hg.addColorStop(1, 'rgba(255,205,160,0)');
    g.fillStyle = hg;
    g.fillRect(x + 8, 0, 14, 512);
  }
  for (let i = 0; i < 900; i++) {
    g.fillStyle = 'rgba(255,218,180,' + (0.012 + Math.random() * 0.018) + ')';
    g.fillRect(Math.random() * 512, Math.random() * 512, 2, 2);
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  return tex;
}

const headTexture = makeHeadTexture();
const capeTexture = makeCapeTexture();

function makeHatTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  const grad = g.createLinearGradient(0, 0, 0, 256);
  grad.addColorStop(0, '#f7ead2');
  grad.addColorStop(0.55, '#ead3b0');
  grad.addColorStop(1, '#d3b58b');
  g.fillStyle = grad;
  g.fillRect(0, 0, 256, 256);
  for (let x = 0; x < 256; x += 14) {
    g.fillStyle = 'rgba(110,72,44,0.12)';
    g.fillRect(x, 0, 3, 256);
    g.fillStyle = 'rgba(255,250,235,0.10)';
    g.fillRect(x + 5, 0, 2, 256);
  }
  for (let y = 0; y < 256; y += 9) {
    g.fillStyle = 'rgba(110,72,44,0.055)';
    g.fillRect(0, y, 256, 2);
  }
  for (let i = 0; i < 320; i++) {
    g.fillStyle = 'rgba(255,255,245,' + (0.03 + Math.random() * 0.04) + ')';
    g.fillRect(Math.random() * 256, Math.random() * 256, 1, 2);
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  return tex;
}
const hatTexture = makeHatTexture();

function buildWanderer() {
  const group = new THREE.Group();
  group.name = 'wanderer';

  const capeMat = new THREE.MeshPhysicalMaterial({
    map: capeTexture, bumpMap: capeTexture, bumpScale: 0.03,
    color: 0xffffff, roughness: 0.9, metalness: 0.0,
    sheen: 0.3, sheenColor: new THREE.Color(0xdca477), sheenRoughness: 0.7,
    side: THREE.DoubleSide,
  });
  const innerMat = new THREE.MeshStandardMaterial({ color: 0x3a1e14, roughness: 0.94, side: THREE.BackSide });
  const tunicMat = new THREE.MeshStandardMaterial({ color: 0xe0c39c, roughness: 0.8 });
  const skinMat = new THREE.MeshStandardMaterial({
    color: 0xf4d8b4, emissive: 0xffc27a, emissiveIntensity: 0.06, roughness: 0.55,
  });
  const headMat = new THREE.MeshBasicMaterial({ map: headTexture, color: 0xffffff, toneMapped: true });
  const eyeMat = new THREE.MeshBasicMaterial({ color: 0x4a2a1a });
  const blushMat = new THREE.MeshBasicMaterial({ color: 0xff9e80, transparent: true, opacity: 0.4 });
  const legMat = new THREE.MeshStandardMaterial({ color: 0x5b3727, roughness: 0.86 });
  const bootMat = new THREE.MeshStandardMaterial({ color: 0x8a5638, roughness: 0.78 });
  const goldMat = new THREE.MeshStandardMaterial({ color: 0xe3b56c, roughness: 0.35, metalness: 0.7 });
  const scarfMat = new THREE.MeshStandardMaterial({ color: 0xd9b38a, roughness: 0.72 });
  const trimMat = new THREE.MeshStandardMaterial({ color: 0xd8a77a, roughness: 0.6 });
  const cuffMat = new THREE.MeshStandardMaterial({ color: 0xc08a5e, roughness: 0.7 });
  const hatMat = new THREE.MeshStandardMaterial({
    map: hatTexture, bumpMap: hatTexture, bumpScale: 0.018, roughness: 0.92,
  });
  const brimMat = new THREE.MeshStandardMaterial({ color: 0x8e4c33, roughness: 0.86 });
  const pomMat = new THREE.MeshStandardMaterial({ color: 0xf2e0c4, roughness: 0.95 });

  // plush bean body
  const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.170, 0.32, 8, 20), tunicMat);
  torso.position.y = 0.64;
  torso.castShadow = true;
  group.add(torso);
  const belt = new THREE.Mesh(new THREE.TorusGeometry(0.170, 0.018, 6, 28), goldMat);
  belt.rotation.x = Math.PI / 2;
  belt.position.y = 0.54;
  group.add(belt);
  const tunicHem = new THREE.Mesh(new THREE.CylinderGeometry(0.175, 0.215, 0.10, 28, 1, true), tunicMat);
  tunicHem.position.y = 0.42;
  group.add(tunicHem);

  // round head
  const headGeo = new THREE.SphereGeometry(0.300, 40, 28);
  const head = new THREE.Mesh(headGeo, headMat);
  head.position.y = 1.155;
  head.scale.set(1.0, 1.08, 0.96);
  head.castShadow = true;
  group.add(head);

  // face
  for (const side of [-1, 1]) {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.020, 10, 8), eyeMat);
    eye.position.set(side * 0.093, 0.035, 0.287);
    eye.scale.set(1.0, 1.35, 0.45);
    head.add(eye);
    const blush = new THREE.Mesh(new THREE.SphereGeometry(0.038, 10, 8), blushMat);
    blush.position.set(side * 0.155, -0.035, 0.258);
    blush.scale.set(1.0, 0.8, 0.15);
    head.add(blush);
  }
  const mouth = new THREE.Mesh(new THREE.SphereGeometry(0.012, 8, 6), eyeMat);
  mouth.position.set(0, -0.082, 0.286);
  mouth.scale.set(1.6, 0.55, 0.4);
  head.add(mouth);

  // knitted beanie with folded brim, ear flaps and pom
  const hatGroup = new THREE.Group();
  hatGroup.position.set(0, 0, 0);
  hatGroup.rotation.z = 0.05;
  head.add(hatGroup);
  const hatProfile = [
    new THREE.Vector2(0.285, 0.145),
    new THREE.Vector2(0.300, 0.175),
    new THREE.Vector2(0.292, 0.205),
    new THREE.Vector2(0.265, 0.240),
    new THREE.Vector2(0.225, 0.280),
    new THREE.Vector2(0.170, 0.315),
    new THREE.Vector2(0.100, 0.345),
    new THREE.Vector2(0.000, 0.360),
  ];
  const hatGeo = new THREE.LatheGeometry(hatProfile, 48);
  const hpos = hatGeo.attributes.position;
  for (let i = 0; i < hpos.count; i++) {
    const x = hpos.getX(i), y = hpos.getY(i), z = hpos.getZ(i);
    if (y > 0.30) {
      hpos.setX(i, x + (y - 0.30) * 0.18);
      hpos.setZ(i, z + (y - 0.30) * 0.06);
    }
  }
  hatGeo.computeVertexNormals();
  const hat = new THREE.Mesh(hatGeo, hatMat);
  hat.castShadow = true;
  hatGroup.add(hat);
  const brim = new THREE.Mesh(new THREE.TorusGeometry(0.295, 0.034, 8, 40), brimMat);
  brim.rotation.x = Math.PI / 2;
  brim.position.y = 0.160;
  brim.castShadow = true;
  hatGroup.add(brim);
  const pom = new THREE.Mesh(new THREE.SphereGeometry(0.070, 16, 12), pomMat);
  pom.position.set(0.012, 0.392, 0.010);
  pom.castShadow = true;
  hatGroup.add(pom);
  const hatStar = new THREE.Mesh(new THREE.OctahedronGeometry(0.030, 0), goldMat);
  hatStar.position.set(0, 0.205, 0.292);
  hatGroup.add(hatStar);
  for (const side of [-1, 1]) {
    const flap = new THREE.Mesh(new THREE.SphereGeometry(0.078, 14, 10), brimMat);
    flap.scale.set(0.95, 0.9, 0.5);
    flap.position.set(side * 0.287, 0.105, -0.010);
    flap.castShadow = true;
    hatGroup.add(flap);
    const tie = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.085, 6), pomMat);
    tie.position.set(side * 0.287, 0.025, -0.010);
    hatGroup.add(tie);
    const bead = new THREE.Mesh(new THREE.SphereGeometry(0.024, 10, 8), pomMat);
    bead.position.set(side * 0.287, -0.022, -0.010);
    hatGroup.add(bead);
  }

  // soft scarf at the neck
  const scarf = new THREE.Mesh(new THREE.TorusGeometry(0.150, 0.055, 8, 28), scarfMat);
  scarf.rotation.x = Math.PI / 2;
  scarf.position.y = 0.845;
  scarf.castShadow = true;
  group.add(scarf);
  const scarfTail = new THREE.Mesh(new THREE.PlaneGeometry(0.11, 0.20), scarfMat);
  scarfTail.position.set(0.03, 0.745, -0.245);
  scarfTail.rotation.x = -0.12;
  scarfTail.rotation.z = -0.10;
  group.add(scarfTail);

  // short open-front cape
  const rows = 14, cols = 38;
  const ang0 = 0.58, ang1 = Math.PI * 2 - 0.58;
  const topY = 0.88, botY = 0.42;
  const positions = [], uvs = [], indices = [];
  for (let r = 0; r < rows; r++) {
    const t = r / (rows - 1);
    const y = topY + (botY - topY) * t;
    const radius = 0.175 + 0.165 * Math.pow(t, 0.9);
    for (let c = 0; c < cols; c++) {
      const a = ang0 + (ang1 - ang0) * (c / (cols - 1));
      const fold = Math.sin(a * 8.0 + 0.4) * 0.018 * t
                 + Math.sin(a * 3.0 + 1.2) * 0.007 * t;
      const rr = radius + fold;
      const yy = y + Math.sin(a * 5.0 + 0.7) * 0.010 * t;
      positions.push(Math.sin(a) * rr, yy, Math.cos(a) * rr);
      uvs.push(c / (cols - 1), 1 - t);
    }
  }
  for (let r = 0; r < rows - 1; r++) {
    for (let c = 0; c < cols - 1; c++) {
      const a = r * cols + c, b = a + 1, d = a + cols, e = d + 1;
      indices.push(a, d, b, b, d, e);
    }
  }
  const capeGeo = new THREE.BufferGeometry();
  capeGeo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  capeGeo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  capeGeo.setIndex(indices);
  capeGeo.computeVertexNormals();

  const capePivot = new THREE.Group();
  capePivot.position.y = 0.88;
  group.add(capePivot);
  const cape = new THREE.Mesh(capeGeo, capeMat);
  cape.position.y = -0.88;
  cape.castShadow = true;
  capePivot.add(cape);
  const innerCape = new THREE.Mesh(capeGeo, innerMat);
  innerCape.position.y = -0.88;
  innerCape.scale.set(0.985, 0.998, 0.985);
  capePivot.add(innerCape);

  // hem trim
  const bottomPts = [];
  for (let c = 0; c < cols; c++) {
    const i = (rows - 1) * cols + c;
    bottomPts.push(new THREE.Vector3(positions[i * 3], positions[i * 3 + 1] + 0.004, positions[i * 3 + 2]));
  }
  const bottomCurve = new THREE.CatmullRomCurve3(bottomPts, false, 'catmullrom', 0.4);
  const bottomTrim = new THREE.Mesh(new THREE.TubeGeometry(bottomCurve, 90, 0.007, 4, false), trimMat);
  bottomTrim.position.y = -0.88;
  capePivot.add(bottomTrim);

  // clasp + back details
  const clasp = new THREE.Mesh(new THREE.OctahedronGeometry(0.034, 0), goldMat);
  clasp.position.set(0, 0.885, 0.155);
  group.add(clasp);
  const gem = new THREE.Mesh(new THREE.OctahedronGeometry(0.040, 0), new THREE.MeshStandardMaterial({
    color: 0xffe2b8, emissive: 0xffb35e, emissiveIntensity: 0.32, roughness: 0.35,
  }));
  gem.position.set(0, 0.64, -0.315);
  group.add(gem);
  const starMat = new THREE.MeshStandardMaterial({
    color: 0xffd58a, emissive: 0xffb35e, emissiveIntensity: 0.22,
    metalness: 0.55, roughness: 0.42, side: THREE.DoubleSide,
  });
  for (const [sx, sy, ss] of [[-0.135, 0.56, 0.028], [0.115, 0.61, 0.021], [0.0, 0.50, 0.018]]) {
    const star = new THREE.Mesh(new THREE.OctahedronGeometry(ss, 0), starMat);
    star.position.set(sx, sy, -0.345);
    group.add(star);
  }

  // little arms with hands
  const arms = [];
  for (const side of [-1, 1]) {
    const pivot = new THREE.Group();
    pivot.position.set(side * 0.235, 0.740, 0.005);
    pivot.rotation.z = side * 0.55;
    const sleeve = new THREE.Mesh(new THREE.CapsuleGeometry(0.045, 0.18, 4, 8), capeMat);
    sleeve.position.y = -0.100;
    sleeve.castShadow = true;
    pivot.add(sleeve);
    const cuff = new THREE.Mesh(new THREE.TorusGeometry(0.050, 0.012, 6, 16), cuffMat);
    cuff.position.y = -0.155;
    cuff.rotation.x = Math.PI / 2;
    pivot.add(cuff);
    const hand = new THREE.Mesh(new THREE.SphereGeometry(0.055, 12, 8), skinMat);
    hand.position.set(side * 0.040, -0.190, 0.035);
    pivot.add(hand);
    group.add(pivot);
    arms.push(pivot);
  }

  // legs and boots
  const legGeo = new THREE.CapsuleGeometry(0.060, 0.19, 4, 10);
  const footGeo = new THREE.SphereGeometry(0.105, 14, 10);
  const legs = [];
  for (const side of [-1, 1]) {
    const pivot = new THREE.Group();
    pivot.position.set(side * 0.100, 0.350, 0);
    const leg = new THREE.Mesh(legGeo, legMat);
    leg.position.y = -0.10;
    leg.castShadow = true;
    pivot.add(leg);
    const foot = new THREE.Mesh(footGeo, bootMat);
    foot.scale.set(1.2, 0.74, 1.55);
    foot.position.set(0, -0.255, 0.080);
    foot.castShadow = true;
    pivot.add(foot);
    group.add(pivot);
    legs.push(pivot);
  }

  const headGlow = new THREE.Mesh(
    new THREE.PlaneGeometry(1, 1),
    new THREE.MeshBasicMaterial({
      map: haloTexture, color: 0xffd7a0, transparent: true, opacity: 0.16,
      blending: THREE.AdditiveBlending, depthWrite: false, depthTest: true, side: THREE.DoubleSide,
    })
  );
  headGlow.scale.set(1.05, 1.05, 1);
  headGlow.renderOrder = 4;
  headGlow.visible = false;

  const shadow = new THREE.Mesh(
    new THREE.CircleGeometry(0.70, 40),
    new THREE.MeshBasicMaterial({
      color: 0x160d08, transparent: true, alphaMap: radialAlphaTexture(),
      opacity: 0.42, depthWrite: false,
    })
  );
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.y = 0.016;
  shadow.renderOrder = 1;
  group.add(shadow);

  const footGlow = new THREE.Mesh(
    new THREE.CircleGeometry(0.55, 40),
    new THREE.MeshBasicMaterial({
      map: haloTexture, color: 0xffc27a, transparent: true, opacity: 0.16,
      blending: THREE.AdditiveBlending, depthWrite: false,
    })
  );
  footGlow.rotation.x = -Math.PI / 2;
  footGlow.position.y = 0.022;
  footGlow.renderOrder = 2;
  group.add(footGlow);

  const light = new THREE.PointLight(0xffc37f, 2.0, 4.8, 2);
  light.position.set(0, 1.35, 0.15);
  group.add(light);
  const footLight = new THREE.PointLight(0xff9c56, 0.8, 3, 2);
  footLight.position.set(0, 0.22, 0.2);
  group.add(footLight);

  group.scale.setScalar(0.92);
  group.userData = { head, cape: capePivot, legs, arms, headGlow, shadow, footGlow, light, footLight };
  return group;
}

const wanderer = buildWanderer();
wanderer.position.set(0, GROUND_Y, 12.0);
wanderer.rotation.y = Math.PI;
wanderer.visible = false;
scene.add(wanderer);
scene.add(wanderer.userData.headGlow);

// --------------------------------------------------------------------- trail
const TRAIL_MAX = 150;
const trailPos = new Float32Array(TRAIL_MAX * 3);
const trailAge = new Float32Array(TRAIL_MAX);
const trailSize = new Float32Array(TRAIL_MAX);
for (let i = 0; i < TRAIL_MAX; i++) {
  trailPos[i * 3 + 1] = -999;
  trailAge[i] = 1;
  trailSize[i] = 0;
}
const trailGeo = new THREE.BufferGeometry();
trailGeo.setAttribute('position', new THREE.BufferAttribute(trailPos, 3));
trailGeo.setAttribute('aAge', new THREE.BufferAttribute(trailAge, 1));
trailGeo.setAttribute('aSize', new THREE.BufferAttribute(trailSize, 1));
const trailMat = new THREE.ShaderMaterial({
  transparent: true,
  depthWrite: false,
  depthTest: false,
  blending: THREE.AdditiveBlending,
  uniforms: { uColor: { value: new THREE.Color(0xffd39b) } },
  vertexShader: `
    attribute float aAge;
    attribute float aSize;
    varying float vA;
    void main() {
      vec4 mv = modelViewMatrix * vec4(position, 1.0);
      gl_PointSize = aSize * (320.0 / max(0.4, -mv.z));
      gl_Position = projectionMatrix * mv;
      vA = clamp(1.0 - aAge, 0.0, 1.0);
    }
  `,
  fragmentShader: `
    uniform vec3 uColor;
    varying float vA;
    void main() {
      float d = length(gl_PointCoord - vec2(0.5));
      float a = smoothstep(0.5, 0.06, d) * vA * 0.85;
      gl_FragColor = vec4(uColor, a);
    }
  `,
});
const trailPoints = new THREE.Points(trailGeo, trailMat);
trailPoints.frustumCulled = false;
trailPoints.renderOrder = 3;
scene.add(trailPoints);
trailPoints.visible = false;
let trailCursor = 0;

const trailPool = [];
const trailPlaneGeo = new THREE.PlaneGeometry(1, 1);
for (let i = 0; i < 120; i++) {
  const m = new THREE.MeshBasicMaterial({
    map: haloTexture, color: 0xffdfae, transparent: true, opacity: 0,
    blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false, side: THREE.DoubleSide,
  });
  const sp = new THREE.Mesh(trailPlaneGeo, m);
  sp.visible = false;
  sp.scale.set(0.3, 0.3, 1);
  sp.frustumCulled = false;
  sp.renderOrder = 5;
  scene.add(sp);
  trailPool.push({ sp, age: 1, life: 1.6, rise: 0.5, base: 0.34 });
}
let trailSpriteCursor = 0;

function spawnTrail(x, y, z) {
  const o = trailPool[trailSpriteCursor];
  trailSpriteCursor = (trailSpriteCursor + 1) % trailPool.length;
  o.sp.position.set(x + THREE.MathUtils.randFloatSpread(0.34), y + THREE.MathUtils.randFloat(0, 0.3), z + THREE.MathUtils.randFloatSpread(0.22));
  o.base = THREE.MathUtils.randFloat(0.30, 0.50);
  o.sp.scale.set(o.base, o.base, 1);
  o.sp.material.opacity = 1.0;
  o.sp.visible = true;
  o.age = 0;
  o.life = THREE.MathUtils.randFloat(1.4, 2.2);
  o.rise = THREE.MathUtils.randFloat(0.35, 0.7);
}

function updateTrail(dt) {
  for (const o of trailPool) {
    if (o.age >= 1) continue;
    o.age = Math.min(1, o.age + dt / o.life);
    const f = o.age;
    o.sp.position.y += o.rise * dt;
    o.sp.material.opacity = (1 - f) * 0.95;
    const sc = o.base * (1 - f * 0.35);
    o.sp.scale.set(sc, sc, 1);
    o.sp.quaternion.copy(walkState.mode === 'walk' ? walkCamera.quaternion : camera.quaternion);
    if (o.age >= 1) o.sp.visible = false;
  }
}

// ------------------------------------------------------------------ composer
// 轻量通道直接渲染到画布：跳过 Bloom 与全屏 RT，显著降低显存和填充开销
let composer = null;
let renderPass = null;
if (LITE) {
  // low-cost bloom at capped DPR; keeps windows, lamps and the tree glowing without the full-size RT
  composer = new EffectComposer(renderer);
  composer.setPixelRatio(renderer.getPixelRatio());
  renderPass = new RenderPass(scene, camera);
  composer.addPass(renderPass);
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(1, 1), 0.28, 0.5, 0.9));
  composer.addPass(new OutputPass());
} else {
  composer = new EffectComposer(renderer);
  composer.setPixelRatio(renderer.getPixelRatio());
  renderPass = new RenderPass(scene, camera);
  composer.addPass(renderPass);
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(1, 1), 0.42, 0.62, 0.86));
  composer.addPass(new SMAAPass());
  composer.addPass(new OutputPass());
}

// ------------------------------------------------------------------- resize
function resize() {
  const w = stage.clientWidth;
  const h = stage.clientHeight;
  if (!w || !h) return;
  const aspect = w / h;
  const halfH = Math.max(FRUSTUM, 30 / aspect);
  camera.left = -halfH * aspect;
  camera.right = halfH * aspect;
  camera.top = halfH;
  camera.bottom = -halfH;
  camera.updateProjectionMatrix();
  walkCamera.aspect = aspect;
  walkCamera.updateProjectionMatrix();
  renderer.setSize(w, h, false);
  if (composer) composer.setSize(w, h);
}
new ResizeObserver(resize).observe(stage);
window.addEventListener('orientationchange', () => setTimeout(resize, 180));
resize();

// Remove two door firs at the cake shop and the two front planter firs.
// The exported GLB is one joined mesh, so clip their tree/planter materials by world-space spheres.
const TREE_CUTS = [
  { x: 14.885, y: 2.7, z: 9.398, r: 1.35 },
  { x: 13.413, y: 2.7, z: 7.838, r: 1.35 },
  { x: -1.719, y: 2.9, z: 11.0, r: 1.25 },
  { x: 3.081, y: 2.9, z: 10.2, r: 1.25 },
];

function installTreeCuts(root) {
  const cutA = TREE_CUTS.map((c) => new THREE.Vector3(c.x, c.y, c.z));
  const cutR = TREE_CUTS.map((c) => c.r);
  const names = new Set(['needles', 'bark_bark', 'pot_stone', 'pot_stone2']);
  root.traverse((o) => {
    if (!o.isMesh) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of mats) {
      if (!m || !names.has(m.name)) continue;
      m.onBeforeCompile = (shader) => {
        shader.uniforms.uCutA = { value: cutA };
        shader.uniforms.uCutR = { value: cutR };
        shader.vertexShader = `varying vec3 vCutW;
` + shader.vertexShader.replace(
          '#include <project_vertex>',
          `#include <project_vertex>
  vCutW = (modelMatrix * vec4(transformed, 1.0)).xyz;`
        );
        shader.fragmentShader = `varying vec3 vCutW;
uniform vec3 uCutA[4];
uniform float uCutR[4];
` + shader.fragmentShader.replace(
          'void main() {',
          `void main() {
  for (int i = 0; i < 4; i++) {
    vec3 d = vCutW - uCutA[i];
    if (dot(d, d) < uCutR[i] * uCutR[i]) discard;
  }`
        );
      };
      m.customProgramCacheKey = () => 'tree-cut-4';
      m.needsUpdate = true;
    }
  });
}

// -------------------------------------------------------------------- model
let model = null;
let autoRotate = false;
let intro = null;
let lastTime = performance.now();

const draco = new DRACOLoader();
draco.setDecoderPath('./vendor/three/examples/jsm/libs/draco/');
const gltfLoader = new GLTFLoader();
gltfLoader.setDRACOLoader(draco);

function setProgress(pct) {
  if (progressFill) progressFill.style.width = Math.min(100, Math.max(0, pct)) + '%';
  if (loaderStatus) loaderStatus.textContent = 'LOADING GEOMETRY · ' + Math.round(pct) + '%';
}

gltfLoader.load(LITE ? './models/christmas_town_lite.glb' : './models/christmas_town.glb', (gltf) => {
  model = gltf.scene;
  const box = new THREE.Box3().setFromObject(model);
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  model.position.x -= center.x;
  model.position.z -= center.z;
  model.position.y -= box.min.y;

  let meshes = 0;
  const seen = new Set();
  model.traverse((o) => {
    if (!o.isMesh) return;
    meshes++;
    o.castShadow = !LITE;
    o.receiveShadow = !LITE;
    o.frustumCulled = !LITE;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of mats) {
      if (!m || seen.has(m)) continue;
      seen.add(m);
      m.envMapIntensity = 0.85;
      if (m.transparent) {
        m.depthWrite = false;
        m.side = THREE.DoubleSide;
      }
    }
  });

  installTreeCuts(model);
  scene.add(model);
  initTreeFx(scene, model, LITE);
  initSceneFx(scene, LITE);
  ground.position.y = -0.035;
  glowDisc.position.y = 0.02;
  controls.target.set(0, Math.min(8.5, Math.max(4.5, size.y * 0.34)), 0);
  if (isMobile()) camera.zoom = 1.22;
  camera.updateProjectionMatrix();
  controls.update();

  console.log('Loaded Christmas Town', { meshes, materials: seen.size, size: size.toArray(), triangles: renderer.info.render.triangles });
  if (loaderStatus) loaderStatus.textContent = 'COMPILING LIGHTS · READY';
  setTimeout(() => {
    loaderEl.classList.add('is-done');
    window.__viewerReady = true;
  }, 420);
}, (xhr) => {
  if (xhr.total) setProgress(xhr.loaded / xhr.total * 100);
  else setProgress(70);
}, (err) => {
  console.error(err);
  loaderEl.classList.add('is-error');
  if (loaderStatus) loaderStatus.textContent = '3D PREVIEW UNAVAILABLE';
  if (errorBtn) errorBtn.hidden = false;
  window.__viewerError = String(err);
});

// ---------------------------------------------------------------- walk mode
const WALK_MIN_R = 5.0;
const WALK_MAX_R = 20.0;
const walkBoxes = [
  { x: 15.2, z: -14.6, hx: 5.1, hz: 4.9 },   // chapel
  { x: -4.4, z: -14.6, hx: 4.5, hz: 4.1 },   // mini market
  { x: 5.0, z: -15.3, hx: 4.4, hz: 4.1 },    // bakery
  { x: -15.3, z: -8.0, hx: 5.3, hz: 5.1 },   // coffee
  { x: 17.8, z: -4.0, hx: 5.5, hz: 5.5 },    // pizzeria
  { x: 18.4, z: 4.5, hx: 5.2, hz: 5.2 },     // cake shop
  { x: -20.3, z: 1.5, hx: 5.4, hz: 5.4 },    // fruit shop
];
const walkObstacles = [
  { x: -9.2, z: 7.2, r: 0.6 }, { x: 9.4, z: 6.5, r: 0.6 },
  { x: -7.8, z: -8.6, r: 0.6 }, { x: 8.2, z: -9.2, r: 0.6 },
  { x: -5.8, z: 8.6, r: 1.35 }, { x: 6.4, z: 8.0, r: 1.35 },
  { x: -10.5, z: -3.0, r: 1.35 }, { x: 10.0, z: -3.8, r: 1.35 },
  { x: -11.2, z: 4.6, r: 0.55 },
  { x: -13.6, z: -2.5, r: 0.85 },
  { x: -11.5, z: 11.5, r: 2.1 },
];
const walkState = {
  mode: 'orbit', keys: new Set(), joy: { x: 0, y: 0, mag: 0 },
  heading: Math.PI, vel: new THREE.Vector3(), phase: 0,
  trailTimer: 0, initialized: false,
};
let orbitSaved = null;
const walkHud = document.getElementById('walk-hud');
const joystick = document.getElementById('joystick');
const joystickKnob = document.getElementById('joystick-knob');
let joyPointer = null;

const forwardFromHeading = (h) => new THREE.Vector3(Math.sin(h), 0, Math.cos(h));
const moveCodes = new Set(['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']);

function syncRotateUi() {
  const btn = document.querySelector('[data-action="rotate"]');
  if (btn) {
    btn.classList.toggle('is-on', autoRotate);
    btn.setAttribute('aria-pressed', String(autoRotate));
  }
}

function placeWalkCamera() {
  const fwd = forwardFromHeading(walkState.heading);
  const right = new THREE.Vector3(-fwd.z, 0, fwd.x);
  const target = new THREE.Vector3(wanderer.position.x, GROUND_Y + 1.0, wanderer.position.z);
  const shoulder = stage.clientWidth < 700 ? 0.7 : 1.15;
  const back = fwd.clone().multiplyScalar(-8.4).add(right.multiplyScalar(shoulder));
  walkCamera.position.copy(target).add(back).add(new THREE.Vector3(0, 2.5, 0));
  walkControls.target.copy(target);
  walkControls.update();
}

function enterWalk() {
  if (!window.__viewerReady || !model) return;
  if (walkState.mode === 'walk') return;
  orbitSaved = {
    position: camera.position.clone(),
    target: controls.target.clone(),
    zoom: camera.zoom,
  };
  autoRotate = false;
  syncRotateUi();
  walkState.mode = 'walk';
  walkState.vel.set(0, 0, 0);
  walkState.keys.clear();
  walkLookOffset = 0;
  walkLookDragY = null;
  walkState.joy.x = 0; walkState.joy.y = 0;
  if (!walkState.initialized) {
    wanderer.position.set(0, GROUND_Y, 12.0);
    walkState.heading = Math.PI;
    walkState.initialized = true;
  }
  wanderer.visible = true;
  wanderer.position.y = GROUND_Y;
  wanderer.rotation.y = walkState.heading;
  placeWalkCamera();
  controls.enabled = false;
  walkControls.enabled = true;
  walkControls.minDistance = 3.2;
  walkControls.maxDistance = 16;
  if (renderPass) renderPass.camera = walkCamera;
  bgPlane.visible = false;
  walkBg.visible = true;
  document.body.classList.add('walking');
  document.body.classList.remove('rail-open');
  if (walkHud) walkHud.setAttribute('aria-hidden', 'false');
  if (joystick) joystick.setAttribute('aria-hidden', 'false');
}

function exitWalk() {
  if (walkState.mode !== 'walk') return;
  walkLookOffset = 0;
  walkLookDragY = null;
  walkState.mode = 'orbit';
  walkState.keys.clear();
  walkState.joy.x = 0; walkState.joy.y = 0;
  resetJoystick();
  walkControls.enabled = false;
  controls.enabled = true;
  if (orbitSaved) {
    camera.position.copy(orbitSaved.position);
    controls.target.copy(orbitSaved.target);
    camera.zoom = orbitSaved.zoom;
    camera.updateProjectionMatrix();
  }
  if (renderPass) renderPass.camera = camera;
  bgPlane.visible = true;
  walkBg.visible = false;
  controls.update();
  document.body.classList.remove('walking');
  if (walkHud) walkHud.setAttribute('aria-hidden', 'true');
  if (joystick) joystick.setAttribute('aria-hidden', 'true');
}

function toggleWalk() {
  if (walkState.mode === 'walk') exitWalk();
  else enterWalk();
}

function resetWalkCamera() {
  placeWalkCamera();
}

function animateWanderer(dt, t, speed) {
  const u = wanderer.userData;
  const move = Math.min(1, speed / 3.0);
  walkState.phase += dt * (2.6 + speed * 2.0);
  const bob = Math.abs(Math.sin(walkState.phase)) * 0.032 * move;
  wanderer.position.y = GROUND_Y + bob;
  const swing = Math.sin(walkState.phase) * 0.72 * move;
  u.legs[0].rotation.x = swing;
  u.legs[1].rotation.x = -swing;
  u.arms[0].rotation.x = -swing * 0.38;
  u.arms[1].rotation.x = swing * 0.38;
  u.cape.rotation.x = -0.05 * move + Math.sin(walkState.phase * 2) * 0.016 * move;
  u.head.position.y = 1.155 + Math.sin(walkState.phase * 2) * 0.010 * move;
  const pulse = Math.sin(t * 2.1) * 0.5 + 0.5;
  u.light.intensity = 2.4 + pulse * 0.6 + move * 1.0;
  u.footGlow.material.opacity = 0.12 + pulse * 0.05;
  u.shadow.material.opacity = 0.36 + pulse * 0.05;
  u.head.rotation.z = Math.sin(t * 0.9) * 0.012 * (1 - move);
}

const _headWorld = new THREE.Vector3();
const _camDir = new THREE.Vector3();
function updateHeadGlow(activeCam) {
  const u = wanderer.userData;
  if (!wanderer.visible) { u.headGlow.visible = false; return; }
  u.head.getWorldPosition(_headWorld);
  activeCam.getWorldDirection(_camDir);
  u.headGlow.position.copy(_headWorld).addScaledVector(_camDir, 0.34);
  u.headGlow.quaternion.copy(activeCam.quaternion);
  u.headGlow.material.opacity = 0.1;
  u.headGlow.visible = true;
}

function updateWalk(dt, t) {
  const camDir = new THREE.Vector3();
  walkCamera.getWorldDirection(camDir);
  camDir.y = 0;
  if (camDir.lengthSq() < 1e-5) camDir.set(0, 0, -1);
  camDir.normalize();
  const right = new THREE.Vector3().crossVectors(camDir, UP).normalize();

  let ix = walkState.joy.x;
  let iz = walkState.joy.y;
  const k = walkState.keys;
  if (k.has('KeyW') || k.has('ArrowUp')) iz += 1;
  if (k.has('KeyS') || k.has('ArrowDown')) iz -= 1;
  if (k.has('KeyD') || k.has('ArrowRight')) ix += 1;
  if (k.has('KeyA') || k.has('ArrowLeft')) ix -= 1;
  const mag = Math.min(1, Math.hypot(ix, iz));
  const dir = new THREE.Vector3();
  if (mag > 0.02) {
    dir.addScaledVector(camDir, iz).addScaledVector(right, ix).normalize();
  }
  const running = k.has('ShiftLeft') || k.has('ShiftRight') || walkState.joy.mag > 0.92;
  const targetSpeed = running ? 5.4 : 2.7;
  const desired = dir.multiplyScalar(targetSpeed * mag);
  const smooth = 1 - Math.exp(-9 * dt);
  walkState.vel.lerp(desired, smooth);
  if (walkState.vel.lengthSq() < 0.0004) walkState.vel.set(0, 0, 0);

  const old = wanderer.position.clone();
  const next = old.clone().addScaledVector(walkState.vel, dt);
  let r = Math.hypot(next.x, next.z);
  if (r < WALK_MIN_R) {
    const s = WALK_MIN_R / Math.max(r, 0.001);
    next.x *= s; next.z *= s;
  } else if (r > WALK_MAX_R) {
    const s = WALK_MAX_R / r;
    next.x *= s; next.z *= s;
  }
  for (const o of walkObstacles) {
    const dx = next.x - o.x;
    const dz = next.z - o.z;
    const d = Math.hypot(dx, dz);
    if (d < o.r) {
      const nx = d > 0.0001 ? dx / d : 0;
      const nz = d > 0.0001 ? dz / d : 1;
      next.x = o.x + nx * o.r;
      next.z = o.z + nz * o.r;
    }
  }
  for (const b of walkBoxes) {
    const dx = next.x - b.x;
    const dz = next.z - b.z;
    if (Math.abs(dx) < b.hx && Math.abs(dz) < b.hz) {
      const px = b.hx - Math.abs(dx);
      const pz = b.hz - Math.abs(dz);
      if (px < pz) next.x = b.x + Math.sign(dx || 1) * (b.hx + 0.05);
      else next.z = b.z + Math.sign(dz || 1) * (b.hz + 0.05);
    }
  }
  r = Math.hypot(next.x, next.z);
  if (r > WALK_MAX_R) {
    const s = WALK_MAX_R / r;
    next.x *= s; next.z *= s;
  }

  wanderer.position.x = next.x;
  wanderer.position.z = next.z;

  const delta = new THREE.Vector3(next.x - old.x, 0, next.z - old.z);
  if (delta.lengthSq() > 1e-8) {
    walkControls.target.x += delta.x;
    walkControls.target.z += delta.z;
    walkCamera.position.x += delta.x;
    walkCamera.position.z += delta.z;
  }

  const speed = walkState.vel.length();
  if (speed > 0.18) {
    const targetHeading = Math.atan2(walkState.vel.x, walkState.vel.z);
    let diff = Math.atan2(Math.sin(targetHeading - walkState.heading), Math.cos(targetHeading - walkState.heading));
    walkState.heading += diff * Math.min(1, dt * 11);
  }
  wanderer.rotation.y = walkState.heading;
  animateWanderer(dt, t, speed);

  if (speed > 0.55) {
    walkState.trailTimer += dt;
    const f = forwardFromHeading(walkState.heading);
    while (walkState.trailTimer > 0.06) {
      walkState.trailTimer -= 0.06;
      const side = Math.random() < 0.5 ? -1 : 1;
      spawnTrail(
        wanderer.position.x - f.x * 0.30 + side * 0.20,
        GROUND_Y + 0.14,
        wanderer.position.z - f.z * 0.30
      );
      spawnTrail(
        wanderer.position.x - f.x * 0.15,
        GROUND_Y + 0.52,
        wanderer.position.z - f.z * 0.15
      );
    }
  } else {
    walkState.trailTimer = 0;
  }
}

function updateOrbitIdle(dt, t) {
  if (wanderer.visible) {
    animateWanderer(dt, t, 0);
    wanderer.position.y = GROUND_Y;
  }
}

function resetJoystick() {
  walkState.joy.x = 0; walkState.joy.y = 0; walkState.joy.mag = 0;
  if (joystickKnob) joystickKnob.style.transform = 'translate(0px, 0px)';
  joyPointer = null;
}

// -------------------------------------------------------------------- animate
renderer.setAnimationLoop(() => {
  const now = performance.now();
  const dt = Math.min((now - lastTime) / 1000, 0.05);
  lastTime = now;
  const t = now / 1000;

  if (model) {
    const arr = snowGeo.attributes.position.array;
    for (let i = 0; i < SNOW_COUNT; i++) {
      arr[i * 3 + 1] -= snowSpeed[i] * (dt * 60);
      arr[i * 3] += Math.sin(t * 0.4 + i) * 0.0016;
      if (arr[i * 3 + 1] < 0.2) {
        arr[i * 3 + 1] = 34;
        arr[i * 3] = THREE.MathUtils.randFloat(-34, 34);
        arr[i * 3 + 2] = THREE.MathUtils.randFloat(-34, 34);
      }
    }
    snowGeo.attributes.position.needsUpdate = true;
    stars.rotation.y += dt * 0.003;
  }

  if (walkState.mode === 'walk') {
    updateWalk(dt, t);
    walkControls.update();
    if (walkCamera.position.y < GROUND_Y + 0.55) {
      walkCamera.position.y = GROUND_Y + 0.55;
    }
    walkCamera.lookAt(walkControls.target.x, walkControls.target.y + walkLookOffset, walkControls.target.z);
  } else {
    controls.autoRotate = autoRotate;
    controls.update();
    updateOrbitIdle(dt, t);
  }
  updateTrail(dt);
  updateHeadGlow(walkState.mode === 'walk' ? walkCamera : camera);
  updateTreeFx(t, walkState.mode === 'walk' ? walkCamera : camera);
  updateSceneFx(t, walkState.mode === 'walk' ? walkCamera : camera);
  if (composer) composer.render();
  else renderer.render(scene, walkState.mode === 'walk' ? walkCamera : camera);
});

// ------------------------------------------------------------------------ ui
function openStill() {
  lightbox.classList.add('is-open');
  document.body.classList.add('still-open');
}
function closeStill() {
  lightbox.classList.remove('is-open');
  document.body.classList.remove('still-open');
}
function toggleRotate() {
  if (walkState.mode === 'walk') return;
  autoRotate = !autoRotate;
  syncRotateUi();
}
function resetView() {
  if (walkState.mode === 'walk') { resetWalkCamera(); return; }
  home.position.set(-30, 38, 58);
  home.target.set(0, 6.5, 0);
  camera.zoom = isMobile() ? 1.22 : 1;
  camera.position.copy(home.position);
  camera.updateProjectionMatrix();
  controls.target.copy(home.target);
  controls.update();
}
function toggleRail() {
  if (isMobile()) {
    document.body.classList.toggle('rail-open');
  } else {
    const rail = document.getElementById('rail');
    if (rail) rail.scrollTo({ top: 0, behavior: 'smooth' });
  }
}
function toggleFullscreen() {
  if (!document.fullscreenElement) {
    (stage.requestFullscreen ? stage.requestFullscreen() : Promise.reject()).catch(() => {});
  } else {
    document.exitFullscreen().catch(() => {});
  }
}

document.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-action]');
  if (!btn) return;
  const action = btn.dataset.action;
  if (action === 'still') openStill();
  else if (action === 'close-still') closeStill();
  else if (action === 'rotate') toggleRotate();
  else if (action === 'reset') resetView();
  else if (action === 'info') toggleRail();
  else if (action === 'fullscreen') toggleFullscreen();
  else if (action === 'walk') toggleWalk();
});
if (errorBtn) errorBtn.addEventListener('click', openStill);
lightbox.addEventListener('click', (e) => { if (e.target === lightbox) closeStill(); });
document.addEventListener('keydown', (e) => {
  if (walkState.mode === 'walk') {
    if (lightbox.classList.contains('is-open')) { closeStill(); return; }
    if (moveCodes.has(e.code)) {
      walkState.keys.add(e.code);
      e.preventDefault();
      return;
    }
    if (e.code === 'ShiftLeft' || e.code === 'ShiftRight') {
      walkState.keys.add(e.code);
      return;
    }
    if (e.key === 'Escape') { exitWalk(); return; }
    return;
  }
  if (e.key === 'Escape') {
    closeStill();
    document.body.classList.remove('rail-open');
  }
  if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
  if (e.key.toLowerCase() === 'r') resetView();
  if (e.key.toLowerCase() === 'a') toggleRotate();
  if (e.key.toLowerCase() === 'f') toggleFullscreen();
  if (e.key.toLowerCase() === 'i') openStill();
});
document.addEventListener('keyup', (e) => {
  walkState.keys.delete(e.code);
});
window.addEventListener('blur', () => walkState.keys.clear());

// vertical drag at the flat limit becomes a free look-up pitch
canvas.addEventListener('pointerdown', (e) => {
  if (walkState.mode === 'walk') walkLookDragY = e.clientY;
});
canvas.addEventListener('pointermove', (e) => {
  if (walkState.mode !== 'walk' || walkLookDragY === null) return;
  const dy = e.clientY - walkLookDragY;
  walkLookDragY = e.clientY;
  if (Math.abs(dy) < 0.01) return;
  const atLimit = walkControls.getPolarAngle() >= walkControls.maxPolarAngle - 0.025;
  if (dy < 0 && atLimit) {
    walkLookOffset = Math.min(12, walkLookOffset - dy * 0.025);
  } else if (dy > 0 && walkLookOffset > 0) {
    walkLookOffset = Math.max(0, walkLookOffset - dy * 0.025);
  }
});
const endLookDrag = () => { walkLookDragY = null; };
canvas.addEventListener('pointerup', endLookDrag);
canvas.addEventListener('pointercancel', endLookDrag);
window.addEventListener('blur', endLookDrag);

// --------------------------------------------------------------- joystick
function setJoystickFromPointer(e) {
  if (!joystick || joyPointer === null) return;
  const rect = joystick.getBoundingClientRect();
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;
  let dx = e.clientX - cx;
  let dy = e.clientY - cy;
  const max = rect.width * 0.36;
  const len = Math.hypot(dx, dy);
  if (len > max) {
    dx = dx / len * max;
    dy = dy / len * max;
  }
  if (joystickKnob) joystickKnob.style.transform = `translate(${dx}px, ${dy}px)`;
  walkState.joy.x = dx / max;
  walkState.joy.y = -dy / max;
  walkState.joy.mag = Math.min(1, Math.hypot(dx, dy) / max);
}
if (joystick) {
  joystick.addEventListener('pointerdown', (e) => {
    if (walkState.mode !== 'walk') return;
    e.preventDefault();
    e.stopPropagation();
    joyPointer = e.pointerId;
    try { joystick.setPointerCapture(e.pointerId); } catch (_) {}
    setJoystickFromPointer(e);
  });
  window.addEventListener('pointermove', (e) => {
    if (e.pointerId !== joyPointer) return;
    e.preventDefault();
    setJoystickFromPointer(e);
  }, { passive: false });
  const end = (e) => {
    if (e.pointerId !== joyPointer) return;
    resetJoystick();
  };
  window.addEventListener('pointerup', end);
  window.addEventListener('pointercancel', end);
}

window.__town = { THREE, walkState, wanderer, walkCamera, walkControls, controls, camera, get model() { return model; }, get walkLookOffset() { return walkLookOffset; }, enterWalk, exitWalk, trailGeo, trailAge, trailPos, trailMat, trailPoints, trailPool };
controls.addEventListener('start', () => {
  if (autoRotate) {
    autoRotate = false;
    syncRotateUi();
  }
});
