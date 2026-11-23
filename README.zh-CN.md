# Christmas26 · 梦幻圣诞小镇

中文 | [English](README.md)

一座完全由代码生成的蓝调时刻微缩世界：Python 驱动 Blender 程序化搭建场景，three.js 搬进浏览器，微信里也能直接旋转、缩放、漫游。

[🎄 在线演示](https://christmas26.113067.xyz/) · [✍️ 博客文章](https://blog.113067.xyz/) · [🧾 原始提示词](ORIGINAL_PROMPT.md)

![Christmas26 渲染成片](renders/christmas_town_post.png)

## ✨ 亮点

- **零外部资产**：159 个材质全部是程序化 PBR 节点，没有一张贴图；每次从空场景重建，约 5,100 个对象、4,700+ 网格
- **七栋欧式店铺** + 15.2 m 中央圣诞树（760+ 灯珠），正交 3/4 俯视蓝调时刻构图
- **可交互 Web**：拖拽旋转、滚轮缩放、第三人称漫游（WASD / 触屏摇杆，带碰撞）
- **双通道性能策略**：桌面完整版；微信 / 移动端自动切 6.2 MB 轻量模型，关阴影、限灯光，但保留全部交互
- **中英双语**：页面按浏览器语言自动切换；右上角可手动切换，也可用 `?lang=zh` / `?lang=en` 指定

## 🚀 快速开始

### 本地预览（无需构建）

```bash
node web/server.mjs        # 然后打开 http://127.0.0.1:8787/
```

页面内置本地 three.js（无 CDN）与 Draco 解码器，完全离线可用。

### 重新渲染场景

需要 Blender 5.3（macOS 已验证）：

```bash
blender -b --factory-startup --python scripts/build.py               # 1920×1200 / 80 samples
blender -b --factory-startup --python scripts/build.py -- --preview  # 900×560 / 24 samples
blender -b --factory-startup --python scripts/build.py -- --draft    # 640×400 / 12 samples
.venv/bin/python scripts/post.py renders/christmas_town.png renders/christmas_town_post.png  # 辉光 / 调色 / 暗角
```

### 导出 Web 模型

```bash
blender -b christmas_town.blend --python scripts/export_web.py
gltf-transform weld  web/models/christmas_town.glb /tmp/weld.glb
gltf-transform simplify /tmp/weld.glb /tmp/simp.glb --ratio 0.06 --error 0.003 --lock-border false
gltf-transform draco /tmp/simp.glb web/models/christmas_town_lite.glb
```

移动端轻量模型由完整版降面生成（590 万面 → 78 万面 / 50 MB → 6.2 MB），153 个材质分组与 Draco 压缩均保留。

## 📁 项目结构

```
christmas_town.blend     完整可编辑场景（Git LFS）
renders/                 Cycles 渲染成片与预览
scripts/
  lib.py                 材质 / 几何 / 工具函数
  buildings.py           七栋建筑与店面
  vegetation.py          圣诞树与植被
  props.py               路灯、长椅、礼物、雪人
  build.py               场景组装、灯光、相机、渲染
  post.py                Pillow/numpy 后期
  export_web.py          Draco GLB 导出
web/
  index.html / styles.css / main.js   展示页与交互
  i18n.js                            中英双语（自动判断 + 手动切换）
  tree_fx.js / scene_fx.js            树饰与场景氛围增强（不改动 .blend）
  models/                完整版 + 轻量版 GLB
  vendor/three/          本地 three.js 与 Draco 解码器
  assets/                封面、静帧、图标
ORIGINAL_PROMPT.md       生成场景的原始 agent 提示词
```

## 🎛 页面参数

| 参数 | 作用 |
|---|---|
| `?lang=zh` / `?lang=en` | 指定界面语言（覆盖浏览器设置，并记忆到 localStorage） |
| `?lite=1` | 桌面强制轻量通道（调试用） |
| `?full=1` | 移动端强制完整版（微信里会卡） |
| `?still=1` | 静帧兜底（不加载 WebGL） |

## 🛠 部署简述

纯静态 nginx 托管，无常驻进程。Cloudflare A 记录 + nginx + Origin CA 证书；站点目录 `<site-root>`，配置 `<nginx-sites>/christmas26.113067.xyz`。

增量更新：打包 `web/` 上传解压后执行 `chmod -R a+rX <site-root>`（macOS 打包会带 600 权限，否则 nginx 403）。HTML/JS/CSS 不缓存，GLB/PNG/wasm 缓存 7 天；改模型后需清 Cloudflare 缓存。

## 📄 License

[MIT](LICENSE) © 2026 Seren

---

*全部资产由程序化脚本生成，无外部贴图或模型依赖。技术细节见[博客文章](https://blog.113067.xyz/)。*
