# -*- coding: utf-8 -*-
import argparse
import os
import sqlite3
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATHS = {
    'general': PROJECT_ROOT / 'db' / 'media_general.db',
    'adult': PROJECT_ROOT / 'db' / 'media_adult.db',
}


def open_read_only(db_path):
    absolute_path = Path(db_path).resolve()
    if not absolute_path.is_file():
        raise FileNotFoundError(f'DB file not found: {absolute_path}')
    connection = sqlite3.connect(f'{absolute_path.as_uri()}?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def comparison_dir(file_path, file_format):
    normalized = str(file_path or '').replace('\\', '/')
    if not normalized:
        return ''
    parent = os.path.dirname(normalized)
    if str(file_format or '').lower() == 'imgdir' and normalized.endswith('/__folder__.imgdir'):
        return os.path.dirname(parent)
    return parent


def find_user(connection, user_id):
    if user_id is None:
        return None
    return connection.execute(
        'SELECT id, username, role FROM users WHERE id = ?',
        (user_id,),
    ).fetchone()


def find_books(connection, query):
    like_query = f'%{query}%'
    return connection.execute(
        """
        SELECT b.id, b.title, b.series_name, b.author, b.library_id,
               b.file_path, b.file_format, COALESCE(b.is_deleted, 0) AS is_deleted,
               l.name AS library_name
        FROM books b
        LEFT JOIN libraries l ON l.id = b.library_id
        WHERE COALESCE(b.title, '') LIKE ?
           OR COALESCE(b.series_name, '') LIKE ?
           OR COALESCE(b.author, '') LIKE ?
           OR COALESCE(b.file_path, '') LIKE ?
        ORDER BY b.library_id, b.series_name, b.id
        """,
        (like_query, like_query, like_query, like_query),
    ).fetchall()


def has_permission(connection, user_id, role, library_id):
    if user_id is None or role == 'admin':
        return True
    row = connection.execute(
        """
        SELECT has_access
        FROM user_category_permissions
        WHERE user_id = ? AND library_id = ?
        """,
        (user_id, library_id),
    ).fetchone()
    return bool(row and row['has_access'] == 1)


def diagnose(db_path, query, user_id=None, library_id=None):
    connection = open_read_only(db_path)
    try:
        user = find_user(connection, user_id)
        if user_id is not None and user is None:
            print(f'[ERROR] user_id={user_id} not found in the users table.')
            return 2

        role = user['role'] if user else None
        rows = find_books(connection, query)

        print('=' * 88)
        print('BookOasis book visibility diagnosis (read-only)')
        print(f'DB       : {Path(db_path).resolve()}')
        print(f'Query    : {query}')
        if user:
            print(f'User     : {user["username"]} (id={user["id"]}, role={role})')
        else:
            print('User     : admin baseline (no permission filter)')
        print(f'Category : {library_id if library_id is not None else "all"}')
        print('=' * 88)

        if not rows:
            print('[RESULT] The query is not in title/series_name/author/file_path.')
            return 1

        visible_count = 0
        for row in rows:
            reasons = []
            if row['is_deleted'] != 0:
                reasons.append(f'is_deleted={row["is_deleted"]}')
            if library_id is not None and row['library_id'] != library_id:
                reasons.append(f'Selected category mismatch ({row["library_id"]} != {library_id})')
            if not has_permission(connection, user_id, role, row['library_id']):
                reasons.append('User has no permission for the category')

            visible = not reasons
            if visible:
                visible_count += 1
            series_name = row['series_name'] or '기타 단행본'
            group_dir = comparison_dir(row['file_path'], row['file_format'])

            print(f'[{"visible" if visible else "excluded"}] book_id={row["id"]}')
            print(f'  title       : {row["title"]}')
            print(f'  series_name : {row["series_name"]}')
            print(f'  library     : {row["library_id"]} / {row["library_name"]}')
            print(f'  file_path   : {row["file_path"]}')
            print(f'  group_key   : ({row["library_id"]}, {series_name!r}, {group_dir!r})')
            if reasons:
                print(f'  Excluded by : {", ".join(reasons)}')
            elif query.lower() not in str(series_name).lower() and query.lower() in str(row['title'] or '').lower():
                print('  Note        : only the title matches. Older search versions do not find this row.')
            print('-' * 88)

        print(f'[SUMMARY] DB matches {len(rows)} / visible in the given user list {visible_count}')
        if visible_count > 0:
            print('[VERDICT] Passes the server list SQL. Check the deployed version or the list preloaded in the browser.')
            return 0
        print('[VERDICT] Every row is excluded by the server list SQL. Check the exclusion reasons above.')
        return 1
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(
        description='Diagnoses, read-only, whether a book passes the conditions of the user list API.'
    )
    parser.add_argument('query', help='Search term: book title, series name, author or path')
    parser.add_argument('--db', choices=('general', 'adult'), default='general', help='DB type')
    parser.add_argument('--db-path', help='SQLite DB file to use instead of the default path')
    parser.add_argument('--user-id', type=int, help='User ID whose non-admin permission filter to reproduce')
    parser.add_argument('--library-id', type=int, help='Library ID whose category selection to reproduce')
    args = parser.parse_args()

    db_path = Path(args.db_path) if args.db_path else DEFAULT_DB_PATHS[args.db]
    try:
        return diagnose(
            db_path,
            args.query.strip(),
            user_id=args.user_id,
            library_id=args.library_id,
        )
    except (sqlite3.Error, OSError) as error:
        print(f'[ERROR] Diagnosis failed: {error}')
        return 2


if __name__ == '__main__':
    sys.exit(main())