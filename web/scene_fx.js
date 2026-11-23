import * as THREE from 'three';

// Blender -> web transform used by the exported diorama
const OX = 0.281;
const OY = 1.7;
const GROUND = 1.91;

const SHOPS = [
  { pos: [18.4, -4.5], yaw: -48, w: 7.2, d: 6.8, h: 7.3, rh: 2.45, doorX: 2.0 },
  { pos: [-15.3, 8.0], yaw: 25, w: 7.6, d: 6.8, h: 7.9, rh: 2.55, doorX: 0.0 },
  { pos: [-20.3, -1.5], yaw: 40, w: 7.4, d: 6.8, h: 7.1, rh: 2.05, doorX: -1.9 },
  { pos: [-4.4, 14.6], yaw: -3, w: 7.8, d: 7.0, h: 7.2, rh: 2.35, doorX: 2.1 },
  { pos: [5.0, 15.3], yaw: 4, w: 7.5, d: 6.9, h: 7.5, rh: 2.15, doorX: -2.0 },
  { pos: [17.8, 4.0], yaw: -58, w: 7.6, d: 7.2, h: 7.2, rh: 2.2, doorX: 0.0 },
];

const LAMPS = [
  [-9.2, -7.2], [9.4, -6.5], [-7.8, 8.6],
  [8.2, 9.2], [-14.6, -1.0], [14.0, -1.5],
];

function world(shop, lx, ly, lz) {
  const th = shop.yaw * Math.PI / 180;
  const wx = lx * Math.cos(th) - ly * Math.sin(th);
  const wy = lx * Math.sin(th) + ly * Math.cos(th);
  return new THREE.Vector3(wx + shop.pos[0] + OX, lz + OY, -(wy + shop.pos[1]));
}

function makeGlowTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(64, 64, 1, 64, 64, 63);
  grd.addColorStop(0, 'rgba(255,255,255,1)');
  grd.addColorStop(0.16, 'rgba(255,246,225,0.9)');
  grd.addColorStop(0.42, 'rgba(255,205,140,0.35)');
  grd.addColorStop(0.75, 'rgba(255,165,90,0.06)');
  grd.addColorStop(1, 'rgba(255,150,70,0)');
  g.fillStyle = grd;
  g.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function makeSmokeTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(64, 64, 2, 64, 64, 62);
  grd.addColorStop(0, 'rgba(205,216,228,0.55)');
  grd.addColorStop(0.35, 'rgba(180,195,211,0.28)');
  grd.addColorStop(0.7, 'rgba(150,168,186,0.06)');
  grd.addColorStop(1, 'rgba(140,160,180,0)');
  g.fillStyle = grd;
  g.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

let fx = null;

export function initSceneFx(scene) {
  if (fx) return;
  const group = new THREE.Group();
  group.name = 'scene-fx';
  scene.add(group);

  const glow = makeGlowTexture();
  const smokeTex = makeSmokeTexture();
  const halos = [];
  const smoke = [];
  const pools = [];

  // warm street lamp light + physical glow + ground pool
  for (const [bx, by] of LAMPS) {
    const x = bx + OX;
    const z = -by;
    const y = 3.88 + OY;
    const l = new THREE.PointLight(0xffa45c, 3.2, 7.0, 2);
    l.position.set(x, y, z);
    group.add(l);

    const halo = new THREE.Mesh(
      new THREE.PlaneGeometry(1, 1),
      new THREE.MeshBasicMaterial({
        map: glow, color: 0xffcf96, transparent: true, opacity: 0.38,
        blending: THREE.AdditiveBlending, depthWrite: false, depthTest: true,
        side: THREE.DoubleSide,
      })
    );
    halo.position.set(x, y, z);
    halo.scale.set(2.2, 2.2, 1);
    halo.renderOrder = 5;
    group.add(halo);
    halos.push(halo);

    const pool = new THREE.Mesh(
      new THREE.CircleGeometry(2.2, 32),
      new THREE.MeshBasicMaterial({
        map: glow, color: 0xffb066, transparent: true, opacity: 0.13,
        blending: THREE.AdditiveBlending, depthWrite: false,
      })
    );
    pool.rotation.x = -Math.PI / 2;
    pool.position.set(x, GROUND + 0.006, z);
    pool.renderOrder = 2;
    group.add(pool);
    pools.push(pool);
  }

  // soft light spill in front of the shop windows
  const poolMat = new THREE.MeshBasicMaterial({
    map: glow, color: 0xffb36b, transparent: true, opacity: 0.11,
    blending: THREE.AdditiveBlending, depthWrite: false,
  });
  for (const shop of SHOPS) {
    const p = world(shop, shop.doorX, -shop.d / 2 - 1.25, 0.32);
    const pool = new THREE.Mesh(new THREE.CircleGeometry(2.1, 32), poolMat);
    pool.rotation.x = -Math.PI / 2;
    pool.position.set(p.x, GROUND + 0.008, p.z);
    pool.renderOrder = 2;
    group.add(pool);
  }

  // icicles along the front eaves
  const icicleGeo = new THREE.ConeGeometry(1, 1, 5);
  icicleGeo.rotateX(Math.PI);
  icicleGeo.translate(0, -0.5, 0);
  const iceMat = new THREE.MeshPhysicalMaterial({
    color: 0xd9eef8, roughness: 0.12, metalness: 0.05,
    transparent: true, opacity: 0.82, depthWrite: true,
  });
  const perShop = 9;
  const icicles = new THREE.InstancedMesh(icicleGeo, iceMat, SHOPS.length * perShop);
  const m4 = new THREE.Matrix4();
  const q = new THREE.Quaternion();
  let iIdx = 0;
  let seed = 7;
  const rnd = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  for (const shop of SHOPS) {
    for (let i = 0; i < perShop; i++) {
      const lx = -shop.w / 2 + 0.55 + (i + 0.35 + rnd() * 0.3) * (shop.w - 1.1) / perShop;
      const p = world(shop, lx, -shop.d / 2 - 0.28, 0.5 + shop.h - 0.26);
      const h = 0.14 + rnd() * 0.34;
      const r = 0.018 + rnd() * 0.030;
      m4.compose(p, q, new THREE.Vector3(r, h, r));
      icicles.setMatrixAt(iIdx++, m4);
    }
  }
  icicles.instanceMatrix.needsUpdate = true;
  icicles.castShadow = true;
  icicles.frustumCulled = false;
  group.add(icicles);

  // chimney smoke from three shops
  const smokeSources = [SHOPS[1], SHOPS[4], SHOPS[5]];
  for (const shop of smokeSources) {
    const top = world(shop, shop.w * 0.28, shop.d * 0.16, 0.5 + shop.h + shop.rh * 0.4 + 1.35);
    for (let i = 0; i < 6; i++) {
      const mat = new THREE.MeshBasicMaterial({
        map: smokeTex, color: 0xb8c2cf, transparent: true, opacity: 0,
        depthWrite: false, depthTest: true, side: THREE.DoubleSide,
      });
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat);
      m.position.copy(top);
      m.scale.set(0.8, 0.8, 1);
      m.renderOrder = 6;
      group.add(m);
      smoke.push({ m, base: top.clone(), age: i / 6, speed: 0.12 + rnd() * 0.04, drift: (rnd() - 0.5) * 0.5, phase: rnd() * 6 });
    }
  }

  fx = { halos, smoke };
}

export function updateSceneFx(t, activeCam) {
  if (!fx) return;
  for (const h of fx.halos) h.quaternion.copy(activeCam.quaternion);
  for (const s of fx.smoke) {
    s.age += 0.0022;
    if (s.age > 1) s.age -= 1;
    const p = s.age;
    s.m.position.set(
      s.base.x + Math.sin(t * 0.55 + s.phase) * 0.22 + p * s.drift,
      s.base.y + 0.1 + p * 3.0,
      s.base.z + Math.cos(t * 0.42 + s.phase) * 0.18 + p * s.drift * 0.4
    );
    const sc = 0.55 + p * 2.1;
    s.m.scale.set(sc, sc, 1);
    s.m.material.opacity = Math.sin(Math.PI * Math.min(1, p * 1.15)) * 0.20 * (1 - p * 0.3);
    s.m.quaternion.copy(activeCam.quaternion);
  }
}
