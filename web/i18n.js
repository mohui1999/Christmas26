/*
 * Christmas26 · bilingual runtime (zh-CN / en)
 * ---------------------------------------------------------------
 * Language priority: ?lang=zh|en  >  localStorage  >  navigator.languages  >  zh
 * Exposes window.I18N with t(key), lang, setLang(lang), apply().
 * Loaded synchronously in <head> so <html lang>/<title>/SEO swap before paint.
 */
(function (global) {
  'use strict';

  var STORE_KEY = 'christmas26-lang';

  var DICT = {
    zh: {
      'meta.title': '梦幻圣诞小镇 · Christmas Town',
      'meta.description': '蓝调时刻的梦幻圣诞小镇：15.2 米冷杉、七栋店铺、可旋转与漫游的 Blender 3D 微缩场景。',
      'meta.siteName': '梦幻圣诞小镇',
      'meta.ogDescription': '蓝调时刻的欧洲圣诞小镇：15.2 米冷杉、七栋店铺、可旋转与漫游的 3D 微缩场景。',
      'meta.imageAlt': '梦幻圣诞小镇：雪夜中的圣诞树与七栋店铺',
      'meta.locale': 'zh_CN',

      'poster.alt': '梦幻圣诞小镇静帧',
      'brand.title': '梦幻圣诞小镇',
      'btn.still': '静帧',
      'btn.info': '场景信息',
      'btn.walk': '漫游',
      'btn.force3d': '3D 版',
      'btn.fullscreen': '全屏',
      'btn.lang': 'EN',
      'btn.lang.aria': '切换到英文',
      'btn.github.aria': '在 GitHub 查看开源源码',
      'btn.github.title': 'GitHub · 开源源码',

      'hint.desktop': '拖拽旋转 <i>/</i> 滚轮缩放 <i>/</i> 右键平移',
      'hint.mobile': '拖拽旋转 <i>·</i> 双指缩放 <i>·</i> 单指平移',
      'chip.rotate': '自动旋转',
      'chip.reset': '重置视角',
      'chip.walk': '漫游',

      'walk.eyebrow': 'Wanderer · 漫游模式',
      'walk.move': '移动',
      'walk.run': '奔跑',
      'walk.look': '拖拽视角 · 可仰视',
      'walk.zoom': '滚轮距离',
      'walk.mobile': '左侧摇杆 移动 · 拖动画面 转向 / 仰视',
      'walk.exit': '✕ 退出漫游',

      'loader.title': '正在点亮小镇',
      'loader.note.lite': '6.2 MB 轻量场景 · 首次加载约几秒',
      'loader.note.full': '52 MB Draco 压缩场景 · 首次加载需要几秒',
      'loader.loading': 'LOADING GEOMETRY · ',
      'loader.compiling': 'COMPILING LIGHTS · READY',
      'loader.unavailable': '3D PREVIEW UNAVAILABLE',
      'loader.scriptFail': 'SCRIPT LOAD FAILED · ',
      'loader.error': '查看静帧',

      'rail.close.aria': '关闭场景信息',
      'rail.heading': '蓝调时刻的<br><em>圣诞广场</em>',
      'rail.intro': '一座围合式的欧洲圣诞广场：中央冷杉撑起整个夜空，七栋店铺以暖光回应积雪与石板，教堂的钟楼从小镇背后升起。',
      'stat.fir': '中央冷杉',
      'stat.buildings': '特色建筑',
      'stat.objects': '场景对象',
      'stat.lights': '树灯灯珠',
      'shops.title': '七栋建筑',
      'shop.cake': '圣诞蛋糕店',
      'shop.coffee': '街角咖啡店',
      'shop.fruits': '水果店',
      'shop.market': '便利店',
      'shop.bakery': '手工面包店',
      'shop.pizzeria': '意大利披萨店',
      'shop.chapel': '圣诞小教堂',
      'note.material': '<span>MATERIAL</span>程序化 PBR · 石板、灰泥、木材、积雪',
      'note.light': '<span>LIGHT</span>冷月光 + 暖橱窗 + 树灯 + 低空薄雾',
      'note.camera': '<span>CAMERA</span>正交 3/4 俯视 · 电影级构图',

      'lightbox.aria': '最终渲染静帧',
      'lightbox.close.aria': '关闭',
      'hero.alt': '梦幻圣诞小镇最终渲染',
      'still.alt': '梦幻圣诞小镇最终渲染静帧',
      'still.title': '梦幻圣诞小镇 · 静帧预览'
    },
    en: {
      'meta.title': 'Christmas Town · A Dreamy Miniature World',
      'meta.description': 'A dreamy Christmas town at blue hour: a 15.2 m fir, seven shops, and a Blender 3D diorama you can rotate and wander in the browser.',
      'meta.siteName': 'Christmas Town',
      'meta.ogDescription': 'A European Christmas town at blue hour: a 15.2 m fir, seven shops, and a 3D diorama you can rotate and wander.',
      'meta.imageAlt': 'Christmas Town: the tree and seven shops on a snowy night',
      'meta.locale': 'en_US',

      'poster.alt': 'Christmas Town still frame',
      'brand.title': 'Christmas Town',
      'btn.still': 'Still',
      'btn.info': 'Scene Info',
      'btn.walk': 'Wander',
      'btn.force3d': '3D Version',
      'btn.fullscreen': 'Fullscreen',
      'btn.lang': '中文',
      'btn.lang.aria': 'Switch to Chinese',
      'btn.github.aria': 'View source on GitHub',
      'btn.github.title': 'GitHub · Open Source',

      'hint.desktop': 'Drag to rotate <i>/</i> Scroll to zoom <i>/</i> Right-drag to pan',
      'hint.mobile': 'Drag to rotate <i>·</i> Pinch to zoom <i>·</i> One-finger pan',
      'chip.rotate': 'Auto-rotate',
      'chip.reset': 'Reset view',
      'chip.walk': 'Wander',

      'walk.eyebrow': 'Wanderer · Walk Mode',
      'walk.move': 'Move',
      'walk.run': 'Run',
      'walk.look': 'Drag to look around',
      'walk.zoom': 'Scroll for distance',
      'walk.mobile': 'Left joystick to move · Drag to look up & around',
      'walk.exit': '✕ Exit Walk Mode',

      'loader.title': 'Lighting up the town',
      'loader.note.lite': '6.2 MB lite scene · First load takes a few seconds',
      'loader.note.full': '52 MB Draco scene · First load takes a few seconds',
      'loader.loading': 'LOADING GEOMETRY · ',
      'loader.compiling': 'COMPILING LIGHTS · READY',
      'loader.unavailable': '3D PREVIEW UNAVAILABLE',
      'loader.scriptFail': 'SCRIPT LOAD FAILED · ',
      'loader.error': 'View still',

      'rail.close.aria': 'Close scene info',
      'rail.heading': 'A Blue-Hour<br><em>Christmas Plaza</em>',
      'rail.intro': 'An enclosed European Christmas plaza: a central fir holds up the night sky, seven shops answer with warm light against snow and stone, and a chapel tower rises behind the town.',
      'stat.fir': 'Central fir',
      'stat.buildings': 'Unique buildings',
      'stat.objects': 'Scene objects',
      'stat.lights': 'Tree lights',
      'shops.title': 'Seven Buildings',
      'shop.cake': 'Christmas cake shop',
      'shop.coffee': 'Corner coffee shop',
      'shop.fruits': 'Fresh fruit shop',
      'shop.market': 'Mini market',
      'shop.bakery': 'Artisan bakery',
      'shop.pizzeria': 'Italian pizzeria',
      'shop.chapel': 'Christmas chapel',
      'note.material': '<span>MATERIAL</span>Procedural PBR · stone, stucco, wood, snow',
      'note.light': '<span>LIGHT</span>Cool moonlight + warm windows + tree lights + low mist',
      'note.camera': '<span>CAMERA</span>Orthographic 3/4 view · cinematic framing',

      'lightbox.aria': 'Final render still',
      'lightbox.close.aria': 'Close',
      'hero.alt': 'Final render of Christmas Town',
      'still.alt': 'Final render still of Christmas Town',
      'still.title': 'Christmas Town · Still Preview'
    }
  };

  function detect() {
    var q = new URLSearchParams(location.search).get('lang');
    if (q === 'zh' || q === 'zh-CN' || q === 'zh_CN') return 'zh';
    if (q === 'en' || q === 'en-US' || q === 'en_US') return 'en';
    try {
      var saved = global.localStorage.getItem(STORE_KEY);
      if (saved === 'zh' || saved === 'en') return saved;
    } catch (e) { /* private mode */ }
    var langs = global.navigator.languages || [global.navigator.language || ''];
    for (var i = 0; i < langs.length; i++) {
      var l = (langs[i] || '').toLowerCase();
      if (l.indexOf('zh') === 0) return 'zh';
      if (l.indexOf('en') === 0) return 'en';
    }
    return 'zh';
  }

  var current = detect();

  function t(key) {
    var d = DICT[current] || DICT.zh;
    return Object.prototype.hasOwnProperty.call(d, key) ? d[key] : key;
  }

  function setMeta(sel, value, attr) {
    var el = document.head.querySelector(sel);
    if (el) el.setAttribute(attr || 'content', value);
  }

  function applyHead() {
    var d = document.documentElement;
    if (!d) return;
    d.setAttribute('lang', current === 'zh' ? 'zh-CN' : 'en');
    document.title = t('meta.title');
    setMeta('meta[name="description"]', t('meta.description'));
    setMeta('meta[property="og:site_name"]', t('meta.siteName'));
    setMeta('meta[property="og:locale"]', t('meta.locale'));
    setMeta('meta[property="og:title"]', t('meta.title'));
    setMeta('meta[property="og:description"]', t('meta.ogDescription'));
    setMeta('meta[property="og:image:alt"]', t('meta.imageAlt'));
    setMeta('meta[name="twitter:title"]', t('meta.title'));
    setMeta('meta[name="twitter:description"]', t('meta.ogDescription'));
    setMeta('meta[name="twitter:image:alt"]', t('meta.imageAlt'));
    var manifest = document.head.querySelector('link[rel="manifest"]');
    if (manifest) manifest.setAttribute('href', current === 'zh' ? './manifest.json' : './manifest.en.json');
  }

  function applyBody() {
    var nodes = document.querySelectorAll('[data-i18n]');
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var key = el.getAttribute('data-i18n');
      var mode = el.getAttribute('data-i18n-mode');
      var val = t(key);
      if (mode === 'html') el.innerHTML = val;
      else el.textContent = val;
    }
    var attrs = document.querySelectorAll('[data-i18n-attrs]');
    for (var j = 0; j < attrs.length; j++) {
      var node = attrs[j];
      var pairs = (node.getAttribute('data-i18n-attrs') || '').split('|');
      for (var k = 0; k < pairs.length; k++) {
        var p = pairs[k].split(':');
        if (p.length === 2) node.setAttribute(p[0], t(p[1]));
      }
    }
    var btn = document.getElementById('lang-btn');
    if (btn) {
      btn.textContent = t('btn.lang');
      btn.setAttribute('aria-label', t('btn.lang.aria'));
      btn.setAttribute('title', t('btn.lang.aria'));
    }
    var loaderNote = document.querySelector('.loader-note');
    if (loaderNote) {
      var p = new URLSearchParams(location.search);
      var lite = p.has('lite') ||
        ((/MicroMessenger|Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent) ||
          (window.matchMedia('(max-width: 900px)').matches && (navigator.maxTouchPoints || 0) > 0)) && !p.has('full'));
      loaderNote.textContent = t(lite ? 'loader.note.lite' : 'loader.note.full');
    }
  }

  function apply() { applyHead(); applyBody(); }

  function setLang(lang) {
    if (lang !== 'zh' && lang !== 'en') return;
    current = lang;
    try { global.localStorage.setItem(STORE_KEY, lang); } catch (e) { /* private mode */ }
    apply();
    document.dispatchEvent(new CustomEvent('i18nchange', { detail: { lang: lang } }));
  }

  var I18N = {
    get lang() { return current; },
    t: t,
    setLang: setLang,
    apply: apply
  };
  global.I18N = I18N;

  applyHead();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', applyBody);
  else applyBody();

  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('#lang-btn');
    if (btn) setLang(current === 'zh' ? 'en' : 'zh');
  });
})(window);
