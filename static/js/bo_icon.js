/* Font Awesome 아이콘 값 -> 화면에 그릴 클래스 (Lucide 우선).
 *
 * 코어 UI 아이콘은 Lucide 선 아이콘(.lc .lc-<이름>, static/lib/lucide/)으로 통일했다. 그런데 카테고리·그룹 아이콘은
 * DB에 Font Awesome 이름('fa-book')으로 저장되고, 플러그인 manifest도 'fa-solid fa-chart-column'처럼 FA로 아이콘을
 * 적는다(플러그인 계약). 그 값은 그대로 두고 그릴 때만 이 함수로 바꾼다.
 *   - 표(window.BO_FA_TO_LUCIDE, tools/icons/fa_to_lucide.json)에 있으면 'lc lc-<lucide>'
 *   - 없거나 브랜드 아이콘(fa-brands)이면 Font Awesome 그대로 (스타일이 없으면 fa-solid를 붙인다)
 *   - 이미 'lc ...'면 그대로
 * fa-spin/fa-fw/fa-lg/fa-2x는 lc-* 로 바꾸고, 그 밖의 클래스(예: 'notify-source-icon')는 그대로 둔다.
 * 클래식 스크립트로 먼저 로드되어 모든 화면(모듈 포함)에서 window.boIcon으로 쓴다.
 */
(function () {
  var STYLE_TOKENS = { 'fa-solid': 1, 'fa-regular': 1, 'fas': 1, 'far': 1, 'fa': 1 };
  var MODIFIERS = { 'fa-spin': 'lc-spin', 'fa-fw': 'lc-fw', 'fa-lg': 'lc-lg', 'fa-2x': 'lc-2x' };

  function boIcon(value) {
    var raw = String(value == null ? '' : value).trim();
    if (!raw) return '';
    var tokens = raw.split(/\s+/);
    if (tokens.indexOf('lc') !== -1 || tokens.indexOf('fa-brands') !== -1 || tokens.indexOf('fab') !== -1) return raw;

    var map = window.BO_FA_TO_LUCIDE || {};
    var name = null;
    var style = null;
    var mods = [];
    var extras = [];
    tokens.forEach(function (tok) {
      if (STYLE_TOKENS[tok]) { style = tok; return; }
      if (MODIFIERS[tok]) { mods.push(tok); return; }
      if (!name && tok.indexOf('fa-') === 0) { name = tok.slice(3); return; }
      extras.push(tok);
    });

    var lucide = name ? map[name] : null;
    if (!lucide) {
      // 표에 없으면 Font Awesome 그대로 - 예전처럼 스타일이 없는 값('fa-book')은 fa-solid로 그린다
      return style ? raw : 'fa-solid ' + raw;
    }
    var out = ['lc', 'lc-' + lucide];
    mods.forEach(function (m) { out.push(MODIFIERS[m]); });
    return out.concat(extras).join(' ');
  }

  window.boIcon = boIcon;
})();
