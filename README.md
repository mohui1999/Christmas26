# 梦幻圣诞小镇 · Christmas26

一个完全由 Python 程序化生成的 Blender 5.3 圣诞小镇微缩场景。场景采用蓝调时刻（blue hour）灯光、暖色橱窗、积雪屋顶、石板广场与中央巨型圣诞树，包含题目要求的七栋欧式建筑。

## 最终画面

- `renders/christmas_town.png` — Cycles 最终渲染（1920 × 1200，80 samples，AgX）
- `renders/christmas_town_post.png` — 后期版本（轻微辉光、冷暗部 / 暖高光调色、暗角、颗粒）
- `renders/preview.png` — 900 × 560 预览

## 场景内容

| 元素 | 说明 |
| --- | --- |
| 中央圣诞树 | 15.2 m 高冷杉，程序化枝干 + 针叶簇，760+ 暖色灯珠、红丝绒缎带、金色珠链、玻璃 / 金属圣诞球、树顶金色五角星 |
| CAKE SHOP | 奶油粉立面、拱形橱窗、粉白条纹雨棚、蛋糕陈列 |
| COFFEE | 奶油白立面、墨绿窗框、木质露台桌椅、二层阳台、COFFEE 招牌 |
| FRESH FRUITS | 淡黄绿立面、绿色条纹雨棚、木质果箱与水果 |
| MINI MARKET | 浅蓝灰立面、宽玻璃橱窗、货架商品、MINI MARKET 招牌 |
| BAKERY | 暖石材立面、拱形面包橱窗、木质推车、BAKERY 招牌 |
| PIZZERIA | 红砖立面、红白条纹雨棚、拱形木门、砖砌披萨炉、PIZZERIA 招牌 |
| CHRISTMAS CHAPEL | 奶油石材、尖坡屋顶、玫瑰窗、彩色玻璃尖拱窗、钟楼、尖塔与十字架 |
| 广场 | 600+ 块程序化径向石板、积雪、湿面反光、长椅、路灯、礼物盒、木质摊位、花池、指示牌 |
| 植被 | 多种冷杉 / 云杉、落叶树、灌木、雪松，全部程序化生成 |
| 灯光 | 冷色月光 + 暖色橱窗 / 路灯 / 圣诞树灯光，低空薄雾，体积感 |
| 相机 | 正交 3/4 俯视，长焦感，完整展示小镇 |

## 文件结构

```
christmas_town.blend       # 完整可编辑场景
README.md
scripts/
  lib.py                   # 材质、几何体、工具函数
  buildings.py             # 七栋建筑与店面细节
  vegetation.py            # 圣诞树、针叶树、灌木
  props.py                 # 路灯、长椅、礼物、摊位、花环等
  build.py                 # 场景组装、灯光、相机、渲染、合成
  post.py                  # Pillow/numpy 后期（辉光、调色、暗角、颗粒）
  export_web.py            # 导出 web 版 Draco GLB
web/                       # 本地 three.js 展示服务
  index.html / styles.css / main.js
  server.mjs               # 零依赖静态服务器
  tree_fx.js               # Web 展示层圣诞树增强
  scene_fx.js              # 路灯、窗光、冰凌、炊烟等全场景增强
  models/christmas_town.glb
  vendor/three/            # 本地 three.js（无 CDN）
  assets/                  # 静帧与服务截图
renders/                   # 渲染输出
```

## 重新渲染

需要 Blender 5.3（macOS 上已验证）。在项目根目录运行：

```bash
# 最终渲染（1920×1200，80 samples，CPU Cycles）
blender -b --factory-startup --python scripts/build.py

# 预览（900×560，24 samples）
blender -b --factory-startup --python scripts/build.py -- --preview

# 快速草稿（640×400，12 samples）
blender -b --factory-startup --python scripts/build.py -- --draft
```

生成 `christmas_town.blend` 与 `renders/christmas_town.png` 后，可运行后期：

```bash
.venv/bin/python scripts/post.py renders/christmas_town.png renders/christmas_town_post.png
```

`scripts/build.py` 每次都会从空场景重新生成，不依赖外部贴图或模型资产；所有材质均为程序化 PBR 节点。

## 本地浏览器预览

项目内置一个本地 three.js 展示页（无需联网、无需构建）。当前服务已运行于 **http://127.0.0.1:8787/**：

```bash
node web/server.mjs
# 浏览器打开 http://127.0.0.1:8787/
```

页面包含可旋转缩放的 3D 场景、七栋店铺索引、最终静帧大图与渲染参数。3D 模型为 web 优化版：针叶网格做了简化、使用 Draco 压缩，材质转换为 glTF PBR 平色，因此观感会比 Cycles 成片更轻、更图形化。

### 漫游模式

点击右上角或底部控制栏的 **漫游** 进入第三人称行走模式：

- 桌面：`WASD` / 方向键移动，`Shift` 奔跑，鼠标拖拽看向四周，滚轮调整距离，`Esc` 退出
- 移动端：左下角虚拟摇杆移动，拖拽画面转动视角；推动摇杆到底自动奔跑
- 角色为程序化生成的「Wanderer」：暖白发光头部与极简表情、奶白色针织毛线帽（陶土色翻边、护耳、绒球和金色小星）、奶油色围巾、带褶皱和金色星点的陶土短斗篷、带袖口的小手、圆头小靴；相机以右后方 3/4 视角跟随，行走时手脚自然摆动、身体轻微起伏，并拖出暖金色光点尾迹
- 行走范围覆盖中央广场与店铺外沿；圣诞树、建筑、长椅、路灯与花池均有碰撞，相机跟随并支持环绕观察

### Web 版圣诞树增强

`web/tree_fx.js` 在不重新导出 GLB 的前提下，为展示页叠加了一层圣诞树细节：

- 树顶金色五角星：面向相机的星形辉光、缓慢旋转、呼吸脉动，并带局部暖光
- 26 颗较大号玻璃 / 金属圣诞球：红、金、蓝、银、珍珠五种材质，带金色吊帽，嵌在树冠外层
- 190 颗珍珠色珠链，沿树冠螺旋缠绕
- 28 处枝梢积雪，增加冬夜层次
- 原有圣诞球提高光泽度与金属度；原有仙女灯珠做轻微明暗呼吸
- 树冠内部补 3 盏局部暖光，让枝干和挂饰更有纵深

这些增强只作用于浏览器展示层，不修改 Blender 原始场景与 Cycles 成片。

### 全场景 Web 增强

`web/scene_fx.js` 继续补充了环境层：

- 天空中的低垂月亮与柔云，强化蓝调时刻氛围
- 6 盏广场路灯增加真实暖点光、灯头辉光和地面光池
- 店铺橱窗前的暖色光溢，让广场边缘更有生活感
- 店铺前檐 54 根细冰凌，增加冬季近景细节
- 咖啡店、面包店、披萨店烟囱的缓慢上升炊烟
- 雪花改为带柔边的雪花纹理，去掉近景白色方块感

加上 `tree_fx.js`，Web 版现在有一层独立于 GLB 的场景氛围与细节层；两套效果都可以单独移除，不影响原始模型。

重新导出 web 模型（会重建 `web/models/christmas_town.glb`）：

```bash
blender -b christmas_town.blend --python scripts/export_web.py
```

## 场景规模

- 约 5,100 个对象、4,700+ 网格、159 个程序化材质、42 盏灯光
- 1920 × 1200 / 80 samples / Cycles CPU，最终渲染约 3.5–4 分钟（Apple M4）
- 全部资产为程序化生成，无外部贴图或模型依赖

## 备注

- 所有招牌文字均为英文，且仅使用题目指定名称。
- 场景使用正交相机，避免广角畸变；相机、灯光、材质、合成节点都可以在 .blend 中继续调整。
- 如果只想打开场景查看，直接打开 `christmas_town.blend` 即可；相机与渲染设置已保存。
