# -*- coding: utf-8 -*-
"""Lucide 아이콘 글꼴 서브셋 + CSS + Font Awesome 이름 맵 생성기.

tools/icons/fa_to_lucide.json(Font Awesome 이름 -> Lucide 이름) 표에 있는 글리프만 남긴
static/lib/lucide/lucide-subset.woff2 와 lucide.css(.lc / .lc-<이름>), fa_map.js(window.BO_FA_TO_LUCIDE),
fa_map.json(서버 Jinja 필터 bo_icon용)을 만든다.
같은 입력이면 같은 결과가 나온다. 표를 바꾼 뒤 다시 실행:

    python tools/build_lucide_icons.py

fontTools(pip install fonttools brotli)가 필요하다. 원본은 jsDelivr의 고정 버전 lucide-static을 받는다.
Lucide는 ISC 라이선스 (static/lib/lucide/LICENSE).
"""
import hashlib
import io
import json
import os
import re
import sys
import urllib.request

LUCIDE_VERSION = '0.469.0'
CDN = f'https://cdn.jsdelivr.net/npm/lucide-static@{LUCIDE_VERSION}'

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_PATH = os.path.join(ROOT, 'tools', 'icons', 'fa_to_lucide.json')
OUT_DIR = os.path.join(ROOT, 'static', 'lib', 'lucide')


def _fetch(path: str) -> bytes:
    with urllib.request.urlopen(f'{CDN}/{path}', timeout=60) as res:
        return res.read()


def load_table() -> dict:
    with open(MAP_PATH, encoding='utf-8') as f:
        return json.load(f)


def load_map() -> dict:
    return load_table()['map']


def parse_codepoints(css_text: str) -> dict:
    """lucide.css의 `.icon-<name>:before { content: "\\e001"; }` -> {name: 0xe001}."""
    return {name: int(code, 16)
            for name, code in re.findall(r'\.icon-([a-z0-9-]+):before\s*\{\s*content:\s*"\\([0-9a-f]+)"', css_text)}


def build_css(lucide_names: list, codepoints: dict, font_version: str) -> str:
    lines = [
        f'/* Lucide {LUCIDE_VERSION} 아이콘 (ISC, https://lucide.dev) - tools/build_lucide_icons.py가 생성. 직접 고치지 말 것. */',
        '@font-face {',
        "    font-family: 'bo-lucide';",
        # 정적 파일은 immutable로 캐시되므로 글리프가 바뀌면 URL도 바뀌어야 한다 (내용 해시)
        f"    src: url('lucide-subset.woff2?v={font_version}') format('woff2');",
        '    font-display: block;',
        '}',
        '',
        '/* Font Awesome의 .fa-solid와 같은 자리에 들어가도록 같은 기본값을 쓴다 */',
        '.lc {',
        "    font-family: 'bo-lucide' !important;",
        '    font-style: normal;',
        '    font-weight: normal;',
        '    font-variant: normal;',
        '    text-transform: none;',
        '    line-height: 1;',
        '    display: inline-block;',
        '    -webkit-font-smoothing: antialiased;',
        '    -moz-osx-font-smoothing: grayscale;',
        '}',
        '.lc-fw { width: 1.25em; text-align: center; }',
        '.lc-lg { font-size: 1.25em; line-height: 0.05em; vertical-align: -0.075em; }',
        '.lc-2x { font-size: 2em; }',
        '.lc-spin { animation: lc-spin 2s linear infinite; }',
        '@keyframes lc-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }',
        '@media (prefers-reduced-motion: reduce) { .lc-spin { animation-duration: 0s; } }',
        '',
    ]
    for name in lucide_names:
        lines.append(f'.lc-{name}:before {{ content: "\\{codepoints[name]:x}"; }}')
    return '\n'.join(lines) + '\n'


def build_js(fa_map: dict) -> str:
    data = {k: v for k, v in sorted(fa_map.items()) if v}
    return ('/* tools/build_lucide_icons.py가 생성 (Font Awesome 이름 -> Lucide 이름). 직접 고치지 말 것. */\n'
            f'window.BO_FA_TO_LUCIDE = {json.dumps(data, ensure_ascii=False, separators=(",", ":"))};\n')


def subset_font(woff2: bytes, codepoints: list) -> bytes:
    from fontTools import subset
    from fontTools.ttLib import TTFont

    font = TTFont(io.BytesIO(woff2), recalcTimestamp=False)  # 같은 입력 -> 같은 파일
    options = subset.Options()
    options.flavor = 'woff2'
    options.layout_features = []
    options.name_IDs = ['*']
    options.notdef_outline = True
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=codepoints)
    subsetter.subset(font)
    out = io.BytesIO()
    font.flavor = 'woff2'
    font.save(out)
    return out.getvalue()


def main() -> int:
    table = load_table()
    fa_map = table['map']
    css_text = _fetch('font/lucide.css').decode('utf-8')
    codepoints = parse_codepoints(css_text)
    # FA 표의 대상 + 코어 UI가 직접 쓰는 추가 아이콘(extra)
    lucide_names = sorted({v for v in fa_map.values() if v} | set(table.get('extra', [])))
    missing = [n for n in lucide_names if n not in codepoints]
    if missing:
        print(f'[lucide] Lucide {LUCIDE_VERSION}에 없는 이름: {missing}', file=sys.stderr)
        return 1

    os.makedirs(OUT_DIR, exist_ok=True)
    woff2 = subset_font(_fetch('font/lucide.woff2'), [codepoints[n] for n in lucide_names])
    with open(os.path.join(OUT_DIR, 'lucide-subset.woff2'), 'wb') as f:
        f.write(woff2)
    with open(os.path.join(OUT_DIR, 'lucide.css'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(build_css(lucide_names, codepoints, hashlib.sha256(woff2).hexdigest()[:12]))
    with open(os.path.join(OUT_DIR, 'fa_map.js'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(build_js(fa_map))
    with open(os.path.join(OUT_DIR, 'fa_map.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({k: v for k, v in sorted(fa_map.items()) if v}, f, ensure_ascii=False, separators=(',', ':'))
    with open(os.path.join(OUT_DIR, 'LICENSE'), 'wb') as f:
        f.write(_fetch('LICENSE'))
    print(f'[lucide] {len(lucide_names)} glyphs, woff2 {len(woff2):,} bytes -> {OUT_DIR}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
