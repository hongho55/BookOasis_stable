# -*- coding: utf-8 -*-
"""웹툰 속성 카테고리의 회차 대표 표지.

웹툰은 회차마다 표지가 따로 없어 폴더(작품)의 대표 표지 하나를 모든 회차가 같이 쓴다. 스캔이 새 회차만
처리하면(기존 회차는 건너뜀) 복제할 표지가 없고, 구글 링크 원본은 압축을 열 수 없어 새 회차가 표지 없이
등록됐다. 여기서는 이미 DB에 있는 같은 폴더 회차의 표지를 쓴다 — 파일을 받지 않는다.
"""
import posixpath

from tools.scanner.path_utils import canonical_path
from utils.drive_helper import split_gdrive_file_id
from utils.sort_helper import natural_sort_key

WEBTOON_LIBRARY_KIND = 'webtoon'


def _folder_of(file_path):
    return canonical_path(posixpath.dirname(split_gdrive_file_id(file_path)[0].replace('\\', '/')))


def _has_cover(cover_image):
    # series_*.webp는 예전 폴더 단위 임시 표지라 대표 표지로 쓰지 않는다(engine.py의 db_meta_full 기준과 같다).
    return bool(cover_image) and not str(cover_image).startswith('series_')


def representative_covers_by_folder(rows):
    """{폴더: 대표 표지}. 표지가 있는 회차 중 파일 이름순 첫 회차의 표지를 쓴다. rows는 file_path/cover_image를 가진 행."""
    best = {}
    for row in rows:
        cover = row['cover_image']
        if not _has_cover(cover):
            continue
        base = split_gdrive_file_id(row['file_path'])[0]
        key = natural_sort_key(posixpath.basename(base.replace('\\', '/')))
        folder = _folder_of(row['file_path'])
        if folder not in best or key < best[folder][0]:
            best[folder] = (key, cover)
    return {folder: cover for folder, (_key, cover) in best.items()}


def fill_missing_series_covers(cursor, library_id):
    """표지가 빈 회차에 같은 폴더의 대표 표지를 넣는다(DB만 고친다). 채운 회차 수를 돌려준다. 커밋은 호출자가 한다."""
    cursor.execute(
        "SELECT id, file_path, cover_image FROM books WHERE library_id = ? AND (is_deleted IS NULL OR is_deleted = 0)",
        (library_id,),
    )
    rows = cursor.fetchall()
    covers = representative_covers_by_folder(rows)
    missing = {}
    for row in rows:
        if _has_cover(row['cover_image']):
            continue
        cover = covers.get(_folder_of(row['file_path']))
        if cover:
            missing.setdefault(cover, []).append(row['id'])

    filled = 0
    for cover, ids in missing.items():
        for start in range(0, len(ids), 500):
            chunk = ids[start:start + 500]
            placeholders = ','.join('?' * len(chunk))
            cursor.execute(f"UPDATE books SET cover_image = ? WHERE id IN ({placeholders})", (cover, *chunk))
            filled += len(chunk)
    if filled:
        print(f"[Scanner-Webtoon] Filled {filled} empty episode covers with the series cover (library {library_id})")
    return filled
