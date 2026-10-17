"""앱 UI 글꼴(static/fonts/pretendard/BookOasisSans-Variable.woff2) 생성 스크립트.

Pretendard 가변 글꼴(OFL, https://github.com/orioncactus/pretendard)을 완성형 한글 2,350자 + 코어 UI 문구에 쓰인 한글
+ 영문·기호로 잘라 woff2 하나로 만든다. 다운로드 1번, 다시 그리기 1번이 목적(조각 92개 방식은 2.9.4에서 체감 속도 저하).
OFL Reserved Font Name 때문에 잘라 만든 글꼴은 'Pretendard' 이름을 쓸 수 없어 'BookOasis Sans'로 바꾼다.

필요: pip install fonttools brotli
원본: https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/variable/woff2/PretendardVariable.woff2
사용: python tools/fonts/build_app_font.py <원본 woff2> static/fonts/pretendard/BookOasisSans-Variable.woff2 .
글꼴을 다시 만들면 templates/index.html의 app_font_url 버전(v=...)을 올린다(1년 캐시).
"""
import sys, os, re, glob
from fontTools import subset
from fontTools.ttLib import TTFont
src, out, root = sys.argv[1:4]
cps = set()
add = lambda a, b: cps.update(range(a, b + 1))
add(0x20, 0x7E); add(0xA0, 0xFF)                 # ASCII, Latin-1
add(0x2010, 0x2027); add(0x2030, 0x203B)         # 문장부호(대시·따옴표·…·‰·※)
add(0x20A9, 0x20A9); add(0x20AC, 0x20AC)         # ₩ €
add(0x2103, 0x2103); add(0x2116, 0x2116); add(0x2122, 0x2122)
add(0x2190, 0x2199)                              # 화살표
add(0x2460, 0x2473)                              # ①~⑳
add(0x25A0, 0x25CF)                              # ■□▲△●○ 등
add(0x2605, 0x2606); add(0x2661, 0x2665)         # ★☆ ♡♥
add(0x3000, 0x303F)                              # CJK 기호(「」『』〈〉·)
add(0x3131, 0x318E)                              # 호환 자모(ㄱ~ㅣ)
add(0xFF01, 0xFF5E)                              # 전각
# KS X 1001 완성형 한글 2,350자
for hi in range(0xB0, 0xC9):
    for lo in range(0xA1, 0xFF):
        try: cps.add(ord(bytes([hi, lo]).decode('euc-kr')))
        except UnicodeDecodeError: pass
# 코어 UI 문구에 쓰인 글자(완성형 밖 글자 포함)
files = glob.glob(os.path.join(root, 'static/i18n/*.json')) + glob.glob(os.path.join(root, 'templates/**/*.html'), recursive=True) \
      + glob.glob(os.path.join(root, 'static/js/**/*.js'), recursive=True)
for f in files:
    for ch in open(f, encoding='utf-8', errors='ignore').read():
        if 0xAC00 <= ord(ch) <= 0xD7A3: cps.add(ord(ch))
font = TTFont(src)
have = set(font.getBestCmap())
cps &= have
opts = subset.Options(); opts.flavor = 'woff2'; opts.layout_features = ['*']; opts.name_IDs = ['*']; opts.notdef_outline = True
s = subset.Subsetter(opts); s.populate(unicodes=cps); s.subset(font)
font.flavor = 'woff2'; font.save(out)
hangul = sum(1 for c in cps if 0xAC00 <= c <= 0xD7A3)
print(f'glyph codepoints={len(cps)} hangul={hangul} size={os.path.getsize(out)//1024}KB fvar={"fvar" in font}')
# OFL Reserved Font Name: 직접 잘라 만든 글꼴은 'Pretendard' 이름을 쓸 수 없어 이름을 바꾼다
font = TTFont(out)
for rec in font['name'].names:
    if rec.nameID in (1, 3, 4, 6, 16, 17, 21, 22, 25):
        t = rec.toUnicode()
        t2 = t.replace('Pretendard Variable', 'BookOasis Sans').replace('PretendardVariable', 'BookOasisSans').replace('Pretendard', 'BookOasis Sans')
        if t2 != t: rec.string = t2
font.save(out)
print([r.toUnicode() for r in font['name'].names if r.nameID in (1, 4, 6, 16)])
