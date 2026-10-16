# -*- coding: utf-8 -*-
"""코어 템플릿/JS의 Font Awesome 아이콘 클래스를 Lucide(.lc .lc-*)로 바꾸는 일회성 코드모드.

    python tools/icons/codemod_fa_to_lucide.py          # 바뀔 내용만 보고
    python tools/icons/codemod_fa_to_lucide.py --write  # 실제로 고침

규칙
- 이어진 fa-* 클래스 묶음(예: "fa-solid fa-gear fa-spin")에 스타일(fa-solid/fa-regular)과 이름이 있으면
  "lc lc-<lucide>"로, 같은 묶음의 fa-spin/fa-fw/fa-lg/fa-2x는 lc-*로 바꾼다.
- 표(tools/icons/fa_to_lucide.json)에 없는 이름, fa-brands, 그리고 "켜짐 = 꽉 찬 모양"을 뜻하는
  fa-solid star/bookmark/heart는 그대로 둔다 (선 아이콘은 꺼짐, 꽉 찬 FA는 켜짐).
- `fa-solid ${...}`처럼 이름이 동적인 곳은 손대지 않는다 - window.boIcon()으로 직접 고친다.
- static/lib(외부 라이브러리)와 sample_plugins(플러그인 계약)는 대상이 아니다.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FA_MAP = json.load(open(os.path.join(ROOT, 'tools', 'icons', 'fa_to_lucide.json'), encoding='utf-8'))['map']
FILLED_STATE = {'star', 'bookmark', 'heart'}
STYLES = {'fa-solid', 'fa-regular'}
MODIFIERS = {'fa-spin': 'lc-spin', 'fa-fw': 'lc-fw', 'fa-lg': 'lc-lg', 'fa-2x': 'lc-2x', 'fa-beat-fade': None}

# 공백으로 이어진 fa-* 토큰 묶음 (앞뒤가 클래스 이름 문자면 제외)
RUN_RE = re.compile(r'(?<![\w-])(fa-[a-z0-9-]+(?:[ ]+fa-[a-z0-9-]+)*)(?![\w-])')


def convert_run(run: str):
    tokens = run.split()
    styles = [t for t in tokens if t in STYLES]
    names = [t for t in tokens if t not in STYLES and t not in MODIFIERS]
    if len(styles) != 1 or len(names) != 1:
        return None
    name = names[0][3:]
    lucide = FA_MAP.get(name)
    if not lucide:
        return None
    if styles[0] == 'fa-solid' and name in FILLED_STATE:
        return None
    out = ['lc', f'lc-{lucide}']
    for t in tokens:
        if t in MODIFIERS and MODIFIERS[t]:
            out.append(MODIFIERS[t])
    return ' '.join(out)


def process(text: str):
    changes = []

    def repl(m):
        new = convert_run(m.group(1))
        if new is None:
            return m.group(0)
        changes.append((m.group(1), new))
        return new

    return RUN_RE.sub(repl, text), changes


def iter_files():
    for base, exts in (('templates', ('.html',)), (os.path.join('static', 'js'), ('.js',))):
        for root, _dirs, files in os.walk(os.path.join(ROOT, base)):
            for name in files:
                if name.endswith(exts):
                    yield os.path.join(root, name)


def main() -> int:
    write = '--write' in sys.argv
    total = 0
    for path in iter_files():
        with open(path, encoding='utf-8', newline='') as f:
            text = f.read()
        new_text, changes = process(text)
        if not changes:
            continue
        total += len(changes)
        print(f'{os.path.relpath(path, ROOT)}: {len(changes)}')
        if write:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(new_text)
    print(f'total {total} replacements' + ('' if write else ' (dry run)'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
