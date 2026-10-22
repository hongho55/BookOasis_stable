# -*- coding: utf-8 -*-
"""구글 드라이브 링크 기능(클로즈 베타) 판단용 로그 — 공통 태그 [GDRIVE-BETA], 한 줄 'key=value'.

베타 테스터에게 `grep GDRIVE-BETA logs/*.log` 결과만 받아도 스캔(목록·메타·건너뛴 폴더·신규)과
열람(사본 받기 크기·시간·실패, 다음 화 미리 받기, 열 때 표지), 캐시 정리를 숫자로 볼 수 있게 한다.
스캔 줄은 워커의 scanner.log, 열람 줄은 웹의 media_server.log에 남는다. 로그 실패는 무시한다.
"""


def _fmt(value):
    if isinstance(value, float):
        return f'{value:.2f}' if abs(value) < 1 else f'{value:.1f}'
    text = str(value)
    if any(c in text for c in (' ', '=', '"')) or not text:
        return '"' + text.replace('"', "'")[:200] + '"'
    return text[:200]


def beta_log(event, **fields):
    try:
        print('[GDRIVE-BETA] ' + event + ''.join(f' {k}={_fmt(v)}' for k, v in fields.items()))
    except Exception:
        pass
