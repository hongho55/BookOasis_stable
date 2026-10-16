// function(pluginId, shadowRoot, items) 본문으로 실행된다 (docs/guide_plugins.md §5-1).
// 서버가 넘긴 값은 textContent / style 속성으로만 넣는다 (마크업으로 끼워 넣지 않음).
var item = (items && items[0]) || {};
var banner = shadowRoot.querySelector('.banner');
if (banner && item.image) {
  // 서버(home_banner.py)에서 http(s)·/경로·data URI만 통과시키지만, 따옴표는 한 번 더 막는다
  banner.style.backgroundImage = 'url("' + String(item.image).replace(/["\\\n\r]/g, '') + '")';
}
var message = shadowRoot.querySelector('.banner__message');
if (message) message.textContent = item.message || '';
var credit = shadowRoot.querySelector('.banner__credit');
if (credit) credit.textContent = item.credit || '';
