# -*- coding: utf-8 -*-
"""Font Awesome 아이콘 값 -> 화면에 그릴 클래스 (Lucide 우선). static/js/bo_icon.js와 같은 규칙의 서버(Jinja) 버전.

카테고리 아이콘(DB)과 플러그인 manifest 아이콘은 Font Awesome 이름 그대로 저장/선언되고(계약), 그릴 때만 바꾼다.
템플릿에서: <i class="{{ w.icon | bo_icon }}"></i>
"""
import json
import os
from functools import lru_cache

_MAP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'static', 'lib', 'lucide', 'fa_map.json')
_STYLES = {'fa-solid', 'fa-regular', 'fas', 'far', 'fa'}
_MODIFIERS = {'fa-spin': 'lc-spin', 'fa-fw': 'lc-fw', 'fa-lg': 'lc-lg', 'fa-2x': 'lc-2x'}


@lru_cache(maxsize=1)
def _fa_map() -> dict:
    try:
        with open(_MAP_PATH, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}  # 맵이 없으면 Font Awesome 그대로 그린다


def bo_icon(value) -> str:
    raw = str(value or '').strip()
    if not raw:
        return ''
    tokens = raw.split()
    if 'lc' in tokens or 'fa-brands' in tokens or 'fab' in tokens:
        return raw

    name, style, mods, extras = None, None, [], []
    for tok in tokens:
        if tok in _STYLES:
            style = tok
        elif tok in _MODIFIERS:
            mods.append(tok)
        elif name is None and tok.startswith('fa-'):
            name = tok[3:]
        else:
            extras.append(tok)

    lucide = _fa_map().get(name) if name else None
    if not lucide:
        return raw if style else f'fa-solid {raw}'
    return ' '.join(['lc', f'lc-{lucide}'] + [_MODIFIERS[m] for m in mods] + extras)
