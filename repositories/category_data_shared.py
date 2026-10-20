# -*- coding: utf-8 -*-
"""
category_data_shared.py – mariadb/sqlite 공용 카테고리 삭제·DB 이동(일반↔성인)의 도서 종속 데이터 처리.
방언 차이는 플레이스홀더 문자(`%s` 또는 `?`)와 컬럼 조회 함수로만 흡수한다. LIMIT 같은 방언 구문은
쓰지 않으며, 묶음(도서 행) 조회는 각 백엔드 리포지토리가 맡는다.

스키마에 FK/CASCADE가 없어 도서를 지우거나 옮기는 경로마다 종속 테이블 목록을 들고 있다 - 카테고리 삭제와
이동은 이 파일의 목록 하나를 같이 쓴다(휴지통 비우기는 trash_repository_shared.py, 자동 하드삭제는
tools/scanner/sync_detector.py).
"""

# DB 이동 시 새 도서 번호로 옮겨 가는 테이블
BOOK_TABLES_MOVED = (
    'user_progress', 'user_reading_log', 'book_offsets', 'user_favorites', 'tts_progress',
    'book_annotations', 'epub_bookmarks', 'gdrive_book_copies',
)
# 옮기지 않고 원본에서 지우기만 하는 테이블 - 컬렉션은 원본 DB의 사용자 컬렉션이라 대상 DB로 가져갈 수 없고,
# TTS 생성 작업과 미리 만든 음성(tts_audio_books/pieces, 디스크 폴더)은 다시 만들 수 있는 캐시로 본다.
BOOK_TABLES_DROPPED = ('collection_items', 'tts_pregen_jobs')


class TransferConflictError(Exception):
    """대상 DB의 다른 카테고리에 같은 파일 경로(books.file_path UNIQUE)의 도서가 이미 있다."""

    def __init__(self, paths):
        self.paths = list(paths)
        preview = ', '.join(self.paths[:3]) + (f' 외 {len(self.paths) - 3}건' if len(self.paths) > 3 else '')
        super().__init__(f'대상 보관함에 같은 파일 경로의 도서가 이미 있습니다: {preview}')


def _marks(placeholder, count):
    return ','.join([placeholder] * count)


def purge_book_dependents(cursor, book_ids, placeholder):
    """도서 묶음의 종속 행을 모두 지우고, 지운 TTS 음성 폴더(rel_dir) 목록을 돌려준다.
    폴더는 호출한 쪽이 커밋한 뒤 지운다(롤백되면 행은 남는데 파일만 사라지지 않게)."""
    if not book_ids:
        return []
    marks = _marks(placeholder, len(book_ids))
    cursor.execute(f"SELECT id, rel_dir FROM tts_audio_books WHERE book_id IN ({marks})", list(book_ids))
    audio = [(row['id'], row['rel_dir']) for row in cursor.fetchall()]
    if audio:
        audio_marks = _marks(placeholder, len(audio))
        audio_ids = [audio_id for audio_id, _rel_dir in audio]
        cursor.execute(f"DELETE FROM tts_audio_pieces WHERE audio_book_id IN ({audio_marks})", audio_ids)
        cursor.execute(f"DELETE FROM tts_audio_books WHERE id IN ({audio_marks})", audio_ids)
    for table in BOOK_TABLES_MOVED + BOOK_TABLES_DROPPED:
        cursor.execute(f"DELETE FROM {table} WHERE book_id IN ({marks})", list(book_ids))
    return [rel_dir for _audio_id, rel_dir in audio if rel_dir]


def _insert_many(cursor, table, rows, placeholder, columns_of, cache, fix=None):
    """rows(SELECT * 결과)를 대상 DB에 있는 컬럼만 골라 한 번에 넣는다. id는 대상 DB가 새로 채번한다.
    오래 운영한 DB는 일반·성인 스키마가 어긋나 있을 수 있어 대상에 없는 컬럼은 건너뛰고 한 번만 남긴다."""
    if not rows:
        return
    if table not in cache:
        cache[table] = columns_of(cursor, table)
        dropped = sorted(set(rows[0]) - cache[table] - {'id'})
        if dropped:
            print(f"[CategoryTransfer WARNING] columns missing in target {table}, skipped: {dropped}")
    prepared = [fix(dict(row)) if fix else dict(row) for row in rows]
    columns = [c for c in prepared[0] if c != 'id' and c in cache[table]]
    col_list = ', '.join(columns)
    cursor.executemany(
        f"INSERT INTO {table} ({col_list}) VALUES ({_marks(placeholder, len(columns))})",
        [tuple(row.get(c) for c in columns) for row in prepared],
    )


def copy_books_to_target(src_cursor, dst_cursor, books, target_library_id, placeholder, columns_of, cache):
    """원본 도서 묶음(books: SELECT * 행)을 대상 카테고리로 복사하고 {원본 id: 대상 id}를 돌려준다.

    대상에 같은 file_path로 이미 이 카테고리에 있는 권은 건너뛴다 - 이전 실행에서 대상만 커밋되고 원본 정리 전에
    멈춘 경우라 종속 행도 그때 같이 커밋되어 있다(멱등). 다른 카테고리에 있으면 TransferConflictError."""
    paths = [book['file_path'] for book in books]
    dst_cursor.execute(
        f"SELECT id, file_path, library_id FROM books WHERE file_path IN ({_marks(placeholder, len(paths))})", paths
    )
    existing = {row['file_path']: (int(row['id']), int(row['library_id'] or 0)) for row in dst_cursor.fetchall()}
    conflicts = [path for path, (_id, lib) in existing.items() if lib != int(target_library_id)]
    if conflicts:
        raise TransferConflictError(conflicts)

    id_map = {int(book['id']): existing[book['file_path']][0] for book in books if book['file_path'] in existing}
    new_books = [book for book in books if book['file_path'] not in existing]
    if not new_books:
        return id_map

    def fix_book(row):
        row['library_id'] = target_library_id
        return row

    _insert_many(dst_cursor, 'books', new_books, placeholder, columns_of, cache, fix_book)
    new_paths = [book['file_path'] for book in new_books]
    dst_cursor.execute(
        f"SELECT id, file_path FROM books WHERE library_id = {placeholder} AND file_path IN ({_marks(placeholder, len(new_paths))})",
        [target_library_id] + new_paths,
    )
    new_ids = {row['file_path']: int(row['id']) for row in dst_cursor.fetchall()}
    new_map = {int(book['id']): new_ids[book['file_path']] for book in new_books}

    old_ids = list(new_map)
    marks = _marks(placeholder, len(old_ids))
    for table in BOOK_TABLES_MOVED:
        src_cursor.execute(f"SELECT * FROM {table} WHERE book_id IN ({marks})", old_ids)
        rows = [dict(row) for row in src_cursor.fetchall()]

        def fix(row, table=table):
            row['book_id'] = new_map[int(row['book_id'])]
            if table == 'gdrive_book_copies':
                row['library_id'] = target_library_id
            return row

        _insert_many(dst_cursor, table, rows, placeholder, columns_of, cache, fix)

    id_map.update(new_map)
    return id_map


def retarget_kosync(cursor, from_type, to_type, id_map, placeholder):
    """KOReader 문서 매핑(중앙 general DB)을 새 보관함·도서 번호로 바꾼다. 이미 바뀐 행은 조건에 안 걸려 다시 돌려도 안전."""
    if not id_map:
        return
    cursor.executemany(
        f"UPDATE kosync_documents SET db_type = {placeholder}, book_id = {placeholder} "
        f"WHERE db_type = {placeholder} AND book_id = {placeholder}",
        [(to_type, new_id, from_type, old_id) for old_id, new_id in id_map.items()],
    )


def forget_kosync(cursor, db_type, book_ids, placeholder):
    if not book_ids:
        return
    cursor.execute(
        f"DELETE FROM kosync_documents WHERE db_type = {placeholder} AND book_id IN ({_marks(placeholder, len(book_ids))})",
        [db_type] + list(book_ids),
    )
