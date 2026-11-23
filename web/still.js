// 轻量静帧模式：不创建 WebGL / 不加载 52MB GLB，专供微信与移动端 WebView。
const isMobile = window.matchMedia('(max-width: 900px)').matches;
const poster = document.getElementById('stage-poster');
poster.src = isMobile ? './assets/mobile_final.png' : './assets/hero.png';
poster.alt = window.I18N ? window.I18N.t('still.alt') : '梦幻圣诞小镇最终渲染静帧';

const loader = document.getElementById('loader');
if (loader) loader.remove();

const lightbox = document.getElementById('lightbox');
const rail = document.getElementById('rail');
const backdrop = document.querySelector('.rail-backdrop');

function setRail(open) {
  if (!rail) return;
  rail.classList.toggle('is-open', open);
  document.body.classList.toggle('rail-open', open);
}
function setStill(open) {
  if (!lightbox) return;
  lightbox.classList.toggle('is-open', open);
  document.body.classList.toggle('still-open', open);
}

document.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-action]');
  if (!btn) return;
  const action = btn.getAttribute('data-action');
  if (action === 'still') setStill(true);
  else if (action === 'close-still') setStill(false);
  else if (action === 'info') setRail(true);
  else if (action === 'force-3d') {
    const u = new URL(location.href);
    u.searchParams.delete('still');
    u.searchParams.set('3d', '1');
    location.href = u.toString();
  } else if (action === 'fullscreen') {
    const el = document.documentElement;
    if (document.fullscreenElement) document.exitFullscreen();
    else if (el.requestFullscreen) el.requestFullscreen();
  }
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') { setStill(false); setRail(false); }
});

function applyStillI18n() {
  document.title = window.I18N ? window.I18N.t('still.title') : '梦幻圣诞小镇 · 静帧预览';
  poster.alt = window.I18N ? window.I18N.t('still.alt') : '梦幻圣诞小镇最终渲染静帧';
}
applyStillI18n();
document.addEventListener('i18nchange', applyStillI18n);
