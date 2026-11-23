import * as THREE from 'three';

// The hero tree sits slightly right of the origin after the model is recentred.
const TREE = { cx: 0.281, baseY: 3.2, topY: 17.4, baseR: 4.55, starY: 18.243 };

let fx = null;

function surfR(y) {
  const t = Math.max(0, Math.min(1, (y - TREE.baseY) / (TREE.topY - TREE.baseY)));
  return TREE.baseR * Math.pow(1 - t, 0.82) + 0.22;
}

function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function makeStarTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 512;
  const g = c.getContext('2d');
  g.clearRect(0, 0, 512, 512);
  g.translate(256, 256);
  const glow = g.createRadialGradient(0, 0, 8, 0, 0, 250);
  glow.addColorStop(0, 'rgba(255,240,205,0.7)');
  glow.addColorStop(0.12, 'rgba(255,214,145,0.36)');
  glow.addColorStop(0.45, 'rgba(255,175,85,0.11)');
  glow.addColorStop(1, 'rgba(255,160,70,0)');
  g.fillStyle = glow;
  g.fillRect(-256, -256, 512, 512);
  g.beginPath();
  for (let i = 0; i < 10; i++) {
    const a = -Math.PI / 2 + i * Math.PI / 5;
    const r = i % 2 === 0 ? 150 : 62;
    const x = Math.cos(a) * r, y = Math.sin(a) * r;
    if (i === 0) g.moveTo(x, y); else g.lineTo(x, y);
  }
  g.closePath();
  const starGrad = g.createRadialGradient(0, 0, 10, 0, 0, 160);
  starGrad.addColorStop(0, '#fff1c6');
  starGrad.addColorStop(0.55, '#ffd27a');
  starGrad.addColorStop(1, '#d9983e');
  g.fillStyle = starGrad;
  g.shadowColor = 'rgba(255,207,120,0.9)';
  g.shadowBlur = 36;
  g.fill();
  g.shadowBlur = 0;
  g.strokeStyle = 'rgba(255,252,235,0.9)';
  g.lineWidth = 5;
  g.stroke();
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function makeNeedleTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  g.clearRect(0, 0, 256, 256);
  const cols = ['#163a27', '#1e4a31', '#2a5a3c', '#356948', '#477d54', '#5a9163'];
  // a dense round cluster of short needles, not long palm-like strokes
  for (let b = 0; b < 9; b++) {
    const ox = 52 + Math.random() * 152;
    const oy = 52 + Math.random() * 152;
    const twigA = Math.random() * Math.PI * 2;
    g.strokeStyle = 'rgba(74,52,34,0.75)';
    g.lineWidth = 1.4;
    g.beginPath();
    g.moveTo(128, 150);
    g.quadraticCurveTo(ox, oy, ox + Math.cos(twigA) * 28, oy + Math.sin(twigA) * 28);
    g.stroke();
    for (let i = 0; i < 75; i++) {
      const a = Math.random() * Math.PI * 2;
      const r0 = 8 + Math.random() * 20;
      const x0 = ox + Math.cos(a) * r0;
      const y0 = oy + Math.sin(a) * r0;
      const len = 9 + Math.random() * 25;
      const a2 = a + (Math.random() - 0.5) * 0.7;
      g.strokeStyle = cols[(Math.random() * cols.length) | 0];
      g.globalAlpha = 0.55 + Math.random() * 0.45;
      g.lineWidth = 0.8 + Math.random() * 1.2;
      g.beginPath(); g.moveTo(x0, y0); g.lineTo(x0 + Math.cos(a2) * len, y0 + Math.sin(a2) * len); g.stroke();
    }
  }
  // soft body so cards read as foliage at a distance
  const body = g.createRadialGradient(128, 128, 20, 128, 128, 120);
  body.addColorStop(0, 'rgba(20,55,35,0.16)');
  body.addColorStop(0.65, 'rgba(18,48,32,0.08)');
  body.addColorStop(1, 'rgba(15,40,28,0)');
  g.globalAlpha = 1;
  g.fillStyle = body;
  g.fillRect(0, 0, 256, 256);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export function initTreeFx(scene, model, lite = false) {
  if (fx) return;
  const group = new THREE.Group();
  group.name = 'tree-fx';
  scene.add(group);

  const rng = mulberry32(20261225);
  const mats = [];
  model.traverse((o) => {
    if (!o.isMesh) return;
    const list = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of list) if (m && !mats.includes(m)) mats.push(m);
  });
  const byName = (n) => mats.filter((m) => m.name === n);
  const bulbMats = [];
  for (const name of ['fairy_bulb', 'garland_bulb']) bulbMats.push(...byName(name));

  for (const m of bulbMats) {
    m.emissiveIntensity = Math.max(2.8, m.emissiveIntensity || 1);
    m.toneMapped = true;
  }
  for (const m of byName('needles')) {
    m.roughness = Math.max(0.68, m.roughness || 0.7);
    m.metalness = 0;
    m.envMapIntensity = 0.75;
  }
  for (const m of mats) {
    if (!m.name) continue;
    if (m.name.startsWith('orn_')) {
      m.roughness = Math.max(0.1, (m.roughness ?? 0.3) * 0.55);
      m.metalness = Math.max(m.metalness || 0, 0.35);
      m.envMapIntensity = 1.3;
    }
    if (m.name === 'star_gold') {
      m.emissive = new THREE.Color(0xffc466);
      m.emissiveIntensity = 1.8;
      m.toneMapped = true;
    }
  }

  // large feature baubles
  const baubleMats = [
    new THREE.MeshPhysicalMaterial({ color: 0x9d1420, roughness: 0.16, metalness: 0.18, clearcoat: 1, clearcoatRoughness: 0.12 }),
    new THREE.MeshPhysicalMaterial({ color: 0xe3ac55, roughness: 0.18, metalness: 0.9, clearcoat: 0.6 }),
    new THREE.MeshPhysicalMaterial({ color: 0x274f7a, roughness: 0.14, metalness: 0.35, clearcoat: 1 }),
    new THREE.MeshPhysicalMaterial({ color: 0xd8e0e6, roughness: 0.16, metalness: 0.8, clearcoat: 0.6 }),
    new THREE.MeshPhysicalMaterial({ color: 0xf1e4cf, roughness: 0.25, metalness: 0.08, clearcoat: 1 }),
  ];
  const capMat = new THREE.MeshStandardMaterial({ color: 0xd8b26c, metalness: 0.8, roughness: 0.28 });
  const capGeo = new THREE.CylinderGeometry(0.045, 0.055, 0.045, 10);
  const baubleCount = lite ? 30 : 26;
  for (let i = 0; i < baubleCount; i++) {
    const y = 4.2 + rng() * 12.0;
    const a = rng() * Math.PI * 2;
    const r = surfR(y) * (0.88 + rng() * 0.05);
    const size = 0.12 + rng() * 0.07;
    const b = new THREE.Mesh(new THREE.SphereGeometry(size, 18, 14), baubleMats[i % baubleMats.length]);
    b.position.set(TREE.cx + Math.cos(a) * r, y, Math.sin(a) * r);
    b.castShadow = true;
    b.rotation.y = rng() * Math.PI * 2;
    group.add(b);
    const cap = new THREE.Mesh(capGeo, capMat);
    cap.position.set(b.position.x, y + size * 0.98, b.position.z);
    group.add(cap);
  }

  // pearly bead garland
  const beadGeo = new THREE.SphereGeometry(0.034, 8, 6);
  const beadMat = new THREE.MeshStandardMaterial({
    color: 0xf1e6d2, roughness: 0.28, metalness: 0.35,
    emissive: 0x2a1c0e, emissiveIntensity: 0.35,
  });
  const beadCount = lite ? 160 : 190;
  const beads = new THREE.InstancedMesh(beadGeo, beadMat, beadCount);
  const m4 = new THREE.Matrix4();
  const q = new THREE.Quaternion();
  for (let i = 0; i < beadCount; i++) {
    const t = i / (beadCount - 1);
    const y = 3.65 + t * 12.95;
    const a = t * Math.PI * 2 * 10.5 + 2.25;
    const r = surfR(y) * 0.97;
    m4.compose(
      new THREE.Vector3(TREE.cx + Math.cos(a) * r, y, Math.sin(a) * r),
      q,
      new THREE.Vector3(1, 1, 1)
    );
    beads.setMatrixAt(i, m4);
  }
  beads.instanceMatrix.needsUpdate = true;
  beads.frustumCulled = false;
  group.add(beads);

  // light dusting of snow on outer branch tips
  const snowGeo = new THREE.IcosahedronGeometry(1, 1);
  const snowMat = new THREE.MeshStandardMaterial({ color: 0xf5f9fb, roughness: 0.9, metalness: 0.0 });
  for (let i = 0; i < (lite ? 20 : 28); i++) {
    const y = 5.0 + rng() * 11.3;
    const a = rng() * Math.PI * 2;
    const r = surfR(y) * (0.88 + rng() * 0.06);
    const s = new THREE.Mesh(snowGeo, snowMat);
    s.position.set(TREE.cx + Math.cos(a) * r, y, Math.sin(a) * r);
    s.scale.set(0.16 + rng() * 0.14, 0.035 + rng() * 0.04, 0.16 + rng() * 0.14);
    s.rotation.y = rng() * Math.PI * 2;
    s.castShadow = true;
    group.add(s);
  }

  let liteLights = null;
  if (lite) {
    // dense cross-plane foliage: restores the tree silhouette at very low triangle cost
    const needleTex = makeNeedleTexture();
    const leafMat = new THREE.MeshStandardMaterial({
      map: needleTex, alphaTest: 0.28, side: THREE.DoubleSide,
      roughness: 0.92, metalness: 0.0, emissive: 0x0a1a10, emissiveIntensity: 0.35,
    });
    const cardGeoA = new THREE.PlaneGeometry(1, 1);
    const cardGeoB = cardGeoA.clone().rotateY(Math.PI / 2);
    const cardCount = 700;
    const cardsA = new THREE.InstancedMesh(cardGeoA, leafMat, cardCount);
    const cardsB = new THREE.InstancedMesh(cardGeoB, leafMat, cardCount);
    const dummy = new THREE.Object3D();
    const ccol = new THREE.Color();
    for (let i = 0; i < cardCount; i++) {
      const y = 4.1 + rng() * 12.5;
      const a = rng() * Math.PI * 2;
      const r = surfR(y) * (0.82 + rng() * 0.15);
      const w = 0.55 + rng() * 0.62;
      const h = 0.52 + rng() * 0.66;
      dummy.position.set(TREE.cx + Math.cos(a) * r, y, Math.sin(a) * r);
      dummy.rotation.set((rng() - 0.5) * 0.4, rng() * Math.PI * 2, (rng() - 0.5) * 0.4);
      dummy.scale.set(w, h, 1);
      dummy.updateMatrix();
      cardsA.setMatrixAt(i, dummy.matrix);
      cardsB.setMatrixAt(i, dummy.matrix);
      ccol.setHSL(0.32 + (rng() - 0.5) * 0.04, 0.35 + rng() * 0.18, 0.38 + rng() * 0.16);
      cardsA.setColorAt(i, ccol);
      cardsB.setColorAt(i, ccol);
    }
    cardsA.instanceMatrix.needsUpdate = true;
    cardsB.instanceMatrix.needsUpdate = true;
    if (cardsA.instanceColor) cardsA.instanceColor.needsUpdate = true;
    if (cardsB.instanceColor) cardsB.instanceColor.needsUpdate = true;
    cardsA.frustumCulled = false; cardsB.frustumCulled = false;
    group.add(cardsA); group.add(cardsB);

    // foliage cards for the surrounding village conifers and planter firs
    const smallTrees = [
      { x: -21.219, z: -9.0, h: 6.5, r: 1.8, base: 1.98 },
      { x: 21.281, z: -11.0, h: 7.5, r: 2.1, base: 1.98 },
      { x: -20.219, z: 7.5, h: 5.2, r: 1.5, base: 1.98 },
      { x: 20.781, z: 8.5, h: 5.8, r: 1.6, base: 1.98 },
      { x: -9.219, z: -20.0, h: 6.2, r: 1.8, base: 1.98 },
      { x: 13.781, z: -20.5, h: 6.8, r: 1.9, base: 1.98 },
      { x: -18.719, z: -17.0, h: 5.5, r: 1.6, base: 1.98 },
      { x: 17.781, z: -18.0, h: 5.0, r: 1.5, base: 1.98 },
      { x: -14.719, z: 13.5, h: 4.6, r: 1.3, base: 1.98 },
      { x: 15.281, z: 12.0, h: 4.8, r: 1.4, base: 1.98 },
      { x: -20.919, z: 10.5, h: 7.4, r: 1.9, base: 1.98 },
      { x: 21.281, z: 10.0, h: 8.2, r: 2.1, base: 1.98 },
      { x: -13.319, z: -2.5, h: 1.35, r: 0.35, dense: 1, base: 2.4 },
      { x: 13.281, z: 3.0, h: 1.65, r: 0.35, dense: 1, base: 2.4 },
    ];
    const smallMats = [];
    const smallCols = [];
    for (const tree of smallTrees) {
      const count = Math.max(tree.dense ? 50 : 20, Math.round(tree.h * tree.r * (tree.dense ? 40 : 18)));
      for (let i = 0; i < count; i++) {
        const tt = 0.06 + rng() * 0.88;
        const y = tree.base + tree.h * tt;
        const rr = tree.r * Math.pow(1 - tt, 0.8) + 0.04;
        const a = rng() * Math.PI * 2;
        const w = tree.dense ? Math.max(0.24, tree.h * (0.14 + rng() * 0.09)) : Math.max(0.18, tree.h * (0.08 + rng() * 0.07));
        dummy.position.set(tree.x + Math.cos(a) * rr, y, tree.z + Math.sin(a) * rr);
        dummy.rotation.set((rng() - 0.5) * 0.5, rng() * Math.PI * 2, (rng() - 0.5) * 0.5);
        dummy.scale.set(w, w, 1);
        dummy.updateMatrix();
        smallMats.push(dummy.matrix.clone());
        smallCols.push(new THREE.Color().setHSL(0.32 + (rng() - 0.5) * 0.04, 0.35 + rng() * 0.16, 0.34 + rng() * 0.16));
      }
    }
    const smallA = new THREE.InstancedMesh(cardGeoA, leafMat, smallMats.length);
    const smallB = new THREE.InstancedMesh(cardGeoB, leafMat, smallMats.length);
    for (let i = 0; i < smallMats.length; i++) {
      smallA.setMatrixAt(i, smallMats[i]);
      smallB.setMatrixAt(i, smallMats[i]);
      smallA.setColorAt(i, smallCols[i]);
      smallB.setColorAt(i, smallCols[i]);
    }
    smallA.instanceMatrix.needsUpdate = true;
    smallB.instanceMatrix.needsUpdate = true;
    if (smallA.instanceColor) smallA.instanceColor.needsUpdate = true;
    if (smallB.instanceColor) smallB.instanceColor.needsUpdate = true;
    smallA.frustumCulled = false;
    smallB.frustumCulled = false;
    group.add(smallA);
    group.add(smallB);

    // extra warm fairy lights, one instanced draw call
    const bulbGeo = new THREE.SphereGeometry(0.045, 6, 4);
    const bulbMat = new THREE.MeshBasicMaterial({
      color: 0xffd49a, transparent: true, opacity: 0.95,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const lightCount = 300;
    liteLights = new THREE.InstancedMesh(bulbGeo, bulbMat, lightCount);
    const bcol = new THREE.Color();
    for (let i = 0; i < lightCount; i++) {
      const t = i / (lightCount - 1);
      const y = 3.9 + t * 12.8;
      const a = t * Math.PI * 2 * 11.5 + 0.4;
      const r = surfR(y) * (0.94 + rng() * 0.06);
      dummy.position.set(TREE.cx + Math.cos(a) * r, y, Math.sin(a) * r);
      dummy.rotation.set(0, 0, 0);
      dummy.scale.set(1, 1, 1);
      dummy.updateMatrix();
      liteLights.setMatrixAt(i, dummy.matrix);
      bcol.setHSL(0.09, 0.8, 0.65 + rng() * 0.18);
      liteLights.setColorAt(i, bcol);
    }
    liteLights.instanceMatrix.needsUpdate = true;
    if (liteLights.instanceColor) liteLights.instanceColor.needsUpdate = true;
    liteLights.frustumCulled = false;
    group.add(liteLights);
  }

  // star topper: a camera-facing painted star + local light
  const starTex = makeStarTexture();
  const starGlow = new THREE.Mesh(
    new THREE.PlaneGeometry(1, 1),
    new THREE.MeshBasicMaterial({
      map: starTex, color: 0xffd38a, transparent: true, opacity: 0.62,
      blending: THREE.AdditiveBlending, depthWrite: false, depthTest: true,
      side: THREE.DoubleSide, toneMapped: true,
    })
  );
  starGlow.position.set(TREE.cx, TREE.starY, 0);
  starGlow.scale.set(2.7, 2.7, 1);
  starGlow.renderOrder = 8;
  group.add(starGlow);
  // 轻量通道只保留星贴片自发光，不创建任何额外点光源
  let starLight = null;
  const treeLights = [];
  if (!lite) {
    starLight = new THREE.PointLight(0xffc06a, 10, 14, 2);
    starLight.position.set(TREE.cx, TREE.starY, 0);
    group.add(starLight);
    for (const [ly, en] of [[5.0, 3.0], [9.0, 2.6], [13.0, 2.0]]) {
      const l = new THREE.PointLight(0xffa45c, en, 6.5, 2);
      l.position.set(TREE.cx, ly, 0);
      group.add(l);
      treeLights.push(l);
    }
  }

  fx = { group, bulbMats, starGlow, starLight, treeLights, baubleMats, liteLights };
}

export function updateTreeFx(t, activeCam) {
  if (!fx) return;
  const pulse = Math.sin(t * 2.2) * 0.5 + 0.5;
  fx.starGlow.quaternion.copy(activeCam.quaternion);
  fx.starGlow.rotateZ(t * 0.16);
  const ss = 2.6 + pulse * 0.12;
  fx.starGlow.scale.set(ss, ss, 1);
  fx.starGlow.material.opacity = 0.52 + pulse * 0.1;
  if (fx.starLight) fx.starLight.intensity = 8 + pulse * 4;
  if (fx.liteLights) fx.liteLights.material.opacity = 0.78 + pulse * 0.18;
  for (const m of fx.bulbMats) {
    const base = m.userData.baseEmissive ?? (m.userData.baseEmissive = m.emissiveIntensity || 3.0);
    m.emissiveIntensity = base * (0.9 + 0.1 * Math.sin(t * 1.9 + 0.7));
  }
}