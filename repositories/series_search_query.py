import re

AUTHOR_PREFIX = '작가:'
TOPIC_PREFIX = '주제:'
COVER_ARTIST_PREFIX = '그림작가:'

# 검색 접두어: 검색 필드 → 언어별 접두어. 화면 언어와 상관없이 전부 받는다(영어 화면에서 '작가:'를 쳐도 된다).
# 새 언어는 해당 필드 튜플에 접두어를 추가하면 된다 - 대소문자 무시, 전각 콜론(：)도 같은 것으로 본다.
# 화면 안내문(검색창 placeholder)은 i18n header.search_placeholder에서 언어별로 보여 준다.
SEARCH_PREFIXES = {
    'cover_artist': (COVER_ARTIST_PREFIX, 'cover_artist:', 'artist:', 'illustrator:', '作画:', 'イラスト:'),
    'topic': (TOPIC_PREFIX, 'topic:', 'テーマ:'),
    'author': (AUTHOR_PREFIX, 'author:', '著者:', '作者:'),
}

# 긴 접두어부터 맞춰 본다 - 한 접두어가 다른 접두어로 시작하더라도 더 구체적인 쪽이 이기게
_PREFIX_TABLE = sorted(
    ((prefix.lower(), field) for field, prefixes in SEARCH_PREFIXES.items() for prefix in prefixes),
    key=lambda item: len(item[0]),
    reverse=True,
)


def parse_series_search_query(search_query):
    query = str(search_query or '').strip()
    folded = query.replace('：', ':').lower()
    for prefix, field in _PREFIX_TABLE:
        if folded.startswith(prefix):
            return field, query[len(prefix):].strip()
    return 'title', query


def normalize_author_key(author):
    """작가별 모음 그룹핑/드릴다운 필터용 정규화 키.
    공백(선행/후행/중간, 전각·NBSP 포함, \\s는 유니코드 기준) 전부 제거 + 대소문자 무시.
    공동저자 문자열("김 작가, 이 작가")은 분리하지 않고 그대로 하나의 키로 취급한다."""
    return re.sub(r'\s+', '', str(author or '')).strip().lower()