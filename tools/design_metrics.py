# -*- coding: utf-8 -*-
"""앱 UI 글자·여백 일관성 측정기 (읽기 전용).

static/css, templates, static/js 의 font-size / font-weight / line-height / margin / padding / gap
선언 수와 서로 다른 값 수, 파일별 상위, 디자인 토큰(var(--app-fs-*, fw-*, lh-*, space-*)) 참조 수를 출력한다.
화면을 토큰으로 옮길 때마다 다시 돌려 "서로 다른 값"이 줄고 토큰 참조가 늘었는지 확인한다.

    python tools/design_metrics.py            # 요약 + 파일별 상위 20
    python tools/design_metrics.py --top 60   # 파일별 상위 60
    python tools/design_metrics.py --file templates/components/views/library_dashboard.html

뷰어 본문(사용자 글꼴 설정), TV/로그인 화면(별도 :root), experimental_* 페이지, static/lib 는 앱 UI가 아니라서 뺀다.
"""
import argparse
import collections
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXCLUDE = (
    'static/lib/',
    'static/css/tv.css',
    'static/css/login.css',
    'templates/experimental_',
    'templates/tv.html',
    'templates/login.html',
)

GROUPS = ('font-size', 'font-weight', 'line-height', 'margin', 'padding', 'gap')

DECL_RE = re.compile(
    r'(?<![\w-])(font-size|font-weight|line-height|margin(?:-[a-z]+)*|padding(?:-[a-z]+)*|gap|row-gap|column-gap)'
    r'\s*:\s*([^;"\'`}\n]+)'
)
JS_STYLE_RE = re.compile(
    r'\.style\.(fontSize|fontWeight|lineHeight|margin\w*|padding\w*|gap|rowGap|columnGap)\s*=\s*[\'"`]([^\'"`]+)'
)
TOKEN_RE = re.compile(r'var\(--app-(fs|fw|lh|space)-')
TOKEN_VAR_RE = re.compile(r'var\(--app-(?:fs|fw|lh|space)-[\w-]+\)')


def _group(prop: str) -> str:
    if prop.startswith('margin'):
        return 'margin'
    if prop.startswith('padding'):
        return 'padding'
    if prop.endswith('gap'):
        return 'gap'
    return prop


def _camel_to_kebab(name: str) -> str:
    return re.sub(r'([A-Z])', lambda m: '-' + m.group(1).lower(), name)


def _files():
    paths = (
        glob.glob(os.path.join(ROOT, 'static', 'css', '*.css'))
        + glob.glob(os.path.join(ROOT, 'templates', '**', '*.html'), recursive=True)
        + glob.glob(os.path.join(ROOT, 'static', 'js', '**', '*.js'), recursive=True)
    )
    for path in sorted(paths):
        rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
        if not rel.startswith(EXCLUDE):
            yield rel, path


def _declarations(text: str):
    for prop, value in DECL_RE.findall(text):
        yield _group(prop), value.replace('!important', '').strip()
    for prop, value in JS_STYLE_RE.findall(text):
        yield _group(_camel_to_kebab(prop)), value.strip()


def measure(only_file=None):
    values = {g: collections.Counter() for g in GROUPS}
    per_file = collections.Counter()
    per_file_tokens = collections.Counter()
    for rel, path in _files():
        if only_file and rel != only_file:
            continue
        with open(path, encoding='utf-8', errors='ignore') as fh:
            text = fh.read()
        for group, value in _declarations(text):
            # 토큰만 쓴 선언은 정리된 것이므로 "날값"에서 뺀다 (토큰 참조 수로 따로 센다)
            if TOKEN_RE.search(value) and not re.search(r'\d', TOKEN_VAR_RE.sub('', value)):
                continue
            values[group][value] += 1
            per_file[rel] += 1
        per_file_tokens[rel] = len(TOKEN_RE.findall(text))
    return values, per_file, per_file_tokens


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--top', type=int, default=20, help='How many top files to show')
    parser.add_argument('--file', help='Measure only this file (path relative to the repository)')
    args = parser.parse_args()

    values, per_file, per_file_tokens = measure(args.file)
    print('based on raw values, not tokens')
    print(f'{"property":<12} {"decls":>6} {"distinct values":>12}')
    for group in GROUPS:
        counter = values[group]
        print(f'{group:<12} {sum(counter.values()):>6} {len(counter):>12}')
    print(f'\ntoken references var(--app-fs|fw|lh|space-*): {sum(per_file_tokens.values())}')

    print(f'\ntop {args.top} files by declarations (declarations / token references)')
    for rel, count in per_file.most_common(args.top):
        print(f'{count:>5} / {per_file_tokens[rel]:<4} {rel}')


if __name__ == '__main__':
    main()
