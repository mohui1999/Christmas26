# Christmas26 · A Dreamy Christmas Town

[中文](README.zh-CN.md) | English

A blue-hour miniature world built entirely in code: Python drives Blender to procedurally assemble the scene, three.js brings it to the browser, and you can rotate, zoom and wander inside it even from WeChat.

[🎄 Live Demo](https://christmas26.113067.xyz/) · [✍️ Blog Post](https://blog.113067.xyz/) · [🧾 Original Prompt](ORIGINAL_PROMPT.md)

![Christmas26 final render](renders/christmas_town_post.png)

## ✨ Highlights

- **Zero external assets** — all 159 materials are procedural PBR nodes, not a single texture; every run rebuilds from an empty scene into ~5,100 objects and 4,700+ meshes
- **Seven European shops** plus a 15.2 m central fir with 760+ lights, framed in an orthographic 3/4 blue-hour composition
- **Interactive web** — drag to rotate, scroll to zoom, third-person walk mode with WASD / touch joystick and collision
- **Two-tier performance path** — full version on desktop; WeChat / mobile automatically switch to a 6.2 MB lite model with shadows off and fewer lights, while keeping every interaction
- **Bilingual UI** — the page follows your browser language; switch manually from the header or force it with `?lang=zh` / `?lang=en`

## 🚀 Quick Start

### Local preview (no build step)

```bash
node web/server.mjs        # then open http://127.0.0.1:8787/
```

three.js and the Draco decoder are bundled locally (no CDN), so the page works fully offline.

### Re-render the scene

Requires Blender 5.3 (verified on macOS):

```bash
blender -b --factory-startup --python scripts/build.py               # 1920x1200 / 80 samples
blender -b --factory-startup --python scripts/build.py -- --preview  # 900x560 / 24 samples
blender -b --factory-startup --python scripts/build.py -- --draft    # 640x400 / 12 samples
.venv/bin/python scripts/post.py renders/christmas_town.png renders/christmas_town_post.png  # glow / grade / vignette
```

### Export the web model

```bash
blender -b christmas_town.blend --python scripts/export_web.py
gltf-transform weld  web/models/christmas_town.glb /tmp/weld.glb
gltf-transform simplify /tmp/weld.glb /tmp/simp.glb --ratio 0.06 --error 0.003 --lock-border false
gltf-transform draco /tmp/simp.glb web/models/christmas_town_lite.glb
```

The mobile lite model is decimated from the full one (5.9M → 780K triangles / 50 MB → 6.2 MB), keeping all 153 material groups and Draco compression.

## 📁 Project Structure

```
christmas_town.blend     fully editable scene (Git LFS)
renders/                 Cycles renders and previews
scripts/
  lib.py                 materials / geometry / helpers
  buildings.py           seven buildings and shopfronts
  vegetation.py          Christmas tree and plants
  props.py               lamps, benches, gifts, snowman
  build.py               scene assembly, lighting, camera, render
  post.py                Pillow/numpy post-processing
  export_web.py          Draco GLB export
web/
  index.html / styles.css / main.js   presentation and interaction
  i18n.js                             bilingual UI (auto-detect + manual switch)
  tree_fx.js / scene_fx.js            tree decorations and atmosphere (no .blend changes)
  models/                full + lite GLB
  vendor/three/          local three.js and Draco decoder
  assets/                cover, stills, icons
ORIGINAL_PROMPT.md       original agent prompt used to generate the scene
```

## 🎛 URL Parameters

| Parameter | Effect |
|---|---|
| `?lang=zh` / `?lang=en` | Force the UI language (overrides browser setting, saved to localStorage) |
| `?lite=1` | Force the lite path on desktop (for debugging) |
| `?full=1` | Force the full version on mobile (will stutter in WeChat) |
| `?still=1` | Still-image fallback (no WebGL) |

## 🛠 Deployment Notes

Served as a plain static nginx site — no resident process. Cloudflare A record + nginx + Origin CA certificate; site root is `<site-root>`, vhost at `<nginx-sites>/christmas26.113067.xyz`.

Incremental updates: repack `web/`, upload and extract, then run `chmod -R a+rX <site-root>` (macOS archives carry 600 permissions, which makes nginx return 403). HTML/JS/CSS are uncached; GLB/PNG/wasm are cached for 7 days — purge Cloudflare after changing the model.

## 📄 License

[MIT](LICENSE) © 2026 Seren

---

*All assets are produced by procedural scripts — no external textures or models. See the [blog post](https://blog.113067.xyz/) for technical details.*
