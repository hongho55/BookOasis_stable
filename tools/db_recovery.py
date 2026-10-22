# -*- coding: utf-8 -*-
"""
db_recovery.py - BookOasis DB 임시 복구 스크립트
=================================================
사용 목적:
  "database disk image is malformed" 에러 발생 시
  WAL 파일 정리 및 DB 무결성 복구를 시도합니다.

사용 방법:
  1. 먼저 BookOasis 서버(컨테이너)를 완전히 정지하세요.
     $ docker stop bookoasis

  2. 이 스크립트를 media_server 루트 디렉토리에서 실행하세요.
     $ python tools/db_recovery.py

  3. 복구 완료 후 서버를 재시작하세요.
     $ docker start bookoasis
"""

import os
import sys
import shutil
import sqlite3
import datetime
import subprocess
import argparse
import re

# ─────────────────────────────────────────────
# 경로 설정 (이 스크립트 위치 기준으로 자동 탐색)
# ─────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.dirname(SCRIPT_DIR)          # media_server 루트
DB_DIR      = os.path.join(BASE_DIR, 'db')
BACKUP_DIR  = os.path.join(BASE_DIR, 'db', '_backup')

DB_FILES = {
    'general': os.path.join(DB_DIR, 'media_general.db'),
    'adult'  : os.path.join(DB_DIR, 'media_adult.db'),
}

# ─────────────────────────────────────────────
# 유틸리티
# ─────────────────────────────────────────────
def sep(char='─', width=60):
    print(char * width)

def log(msg, prefix='  '):
    print(f"{prefix}{msg}")

def timestamp():
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

# ─────────────────────────────────────────────
# STEP 1: WAL 체크포인트 (데이터 손실 없음)
# ─────────────────────────────────────────────
def step1_wal_checkpoint(db_path, label):
    """WAL/SHM 파일을 메인 DB에 병합 후 정리합니다."""
    sep()
    log(f"[{label}] Starting WAL checkpoint", prefix='')

    if not os.path.exists(db_path):
        log("⚠️  DB file does not exist. Skipping.")
        return False

    wal_path = db_path + '-wal'
    shm_path = db_path + '-shm'
    has_wal  = os.path.exists(wal_path)
    has_shm  = os.path.exists(shm_path)

    log(f"Path: {db_path}")
    log(f"WAL file: {'✅ present (' + str(os.path.getsize(wal_path)) + ' bytes)' if has_wal else 'none'}")
    log(f"SHM file: {'✅ present' if has_shm else 'none'}")

    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")

        # 무결성 사전 체크
        log("Checking integrity...")
        result = conn.execute("PRAGMA integrity_check;").fetchall()
        integrity_ok = (len(result) == 1 and result[0][0] == 'ok')
        if integrity_ok:
            log("✅ integrity_check: OK")
        else:
            log(f"❌ integrity_check found problems: {result[:3]}")
            conn.close()
            return False

        # WAL 체크포인트 강제 수행
        log("Running WAL checkpoint (TRUNCATE)...")
        ckpt = conn.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
        log(f"Result: busy={ckpt[0]}, log={ckpt[1]}, checkpointed={ckpt[2]}")
        conn.close()

        log(f"✅ [{label}] WAL checkpoint done - no data loss")
        return True

    except sqlite3.DatabaseError as e:
        log(f"❌ DB error: {e}")
        log("-> The DB itself may be corrupted. Try Step 2 (full recovery).")
        return False
    except Exception as e:
        log(f"❌ Unexpected error: {e}")
        return False

# ─────────────────────────────────────────────
# STEP 2: 전체 복구 (.recover 덤프 재생성)
# ─────────────────────────────────────────────
def step2_full_recovery(db_path, label):
    """
    DB 파일이 실제로 손상된 경우 .recover 명령으로 데이터를 추출하여
    새 DB를 생성합니다. 최근 일부 변경사항은 손실될 수 있습니다.
    """
    sep()
    log(f"[{label}] Starting full recovery (STEP 2)", prefix='')
    log("⚠️  Warning: this rebuilds the DB. Some recent changes may be lost.")

    if not os.path.exists(db_path):
        log("⚠️  DB file does not exist. Skipping.")
        return False

    # 백업 디렉토리 생성
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts             = timestamp()
    backup_path    = os.path.join(BACKUP_DIR, f"{label}_{ts}.db.bak")
    recovered_path = db_path + '.recovered'

    # 1) 원본 백업
    log(f"Backing up the original: {backup_path}")
    shutil.copy2(db_path, backup_path)
    log(f"✅ Backup done: {os.path.getsize(backup_path):,} bytes")

    # 2) sqlite3 CLI로 .recover 스트리밍 복구 실행
    log("Trying streaming data recovery with the sqlite3 CLI...")
    try:
        if os.path.exists(recovered_path):
            os.remove(recovered_path)

        # 디스크에 5GB SQL 덤프를 따로 저장하지 않고 바로 새 DB에 주입합니다.
        import_proc = subprocess.Popen(
            ['sqlite3', recovered_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore',
            bufsize=1,
        )
        recover_proc = subprocess.Popen(
            ['sqlite3', db_path, '.recover'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore',
            bufsize=1,
        )

        # 대량 쓰기 성능을 위해 새 DB 쪽은 저널/동기화를 완화합니다.
        assert import_proc.stdin is not None
        assert import_proc.stderr is not None
        assert recover_proc.stdout is not None
        assert recover_proc.stderr is not None
        import_proc.stdin.write("PRAGMA journal_mode=OFF;\n")
        import_proc.stdin.write("PRAGMA synchronous=OFF;\n")
        import_proc.stdin.write("PRAGMA temp_store=MEMORY;\n")
        import_proc.stdin.write("PRAGMA foreign_keys=OFF;\n")
        import_proc.stdin.write("PRAGMA locking_mode=EXCLUSIVE;\n")

        log("Creating a new DB...")

        def should_skip_recovery_statement(statement):
            """FTS5 shadow table과 books_search 관련 statement를 제외합니다."""
            normalized = re.sub(r'\s+', ' ', statement).strip()
            if not normalized:
                return True

            patterns = (
                r'^BEGIN(?:\s+TRANSACTION)?\s*;?$',
                r'^COMMIT\s*;?$',
                r'^ROLLBACK\s*;?$',
                r'^SAVEPOINT\s+\S+\s*;?$',
                r'^RELEASE\s+\S+\s*;?$',
                r'^CREATE\s+(?:VIRTUAL\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:["`\[])?books_search(?:["`\]])?(?:\s|\()',
                r'^CREATE\s+TRIGGER\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:["`\[])?books_search_',
                r'^INSERT\s+INTO\s+(?:["`\[])?books_search(?:_(?:data|idx|content|docsize|config))?(?:["`\]])?(?:\s|\()',
                r'^UPDATE\s+(?:["`\[])?books_search(?:_(?:data|idx|content|docsize|config))?(?:["`\]])?\s+SET\b',
                r'^DELETE\s+FROM\s+(?:["`\[])?books_search(?:_(?:data|idx|content|docsize|config))?(?:["`\]])?(?:\s|;|$)',
                r'^DROP\s+(?:VIRTUAL\s+)?TABLE\s+(?:IF\s+EXISTS\s+)?(?:["`\[])?books_search(?:["`\]])?(?:\s|;|$)',
                r'^ALTER\s+TABLE\s+(?:["`\[])?books_search(?:_(?:data|idx|content|docsize|config))?(?:["`\]])?',
            )
            return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in patterns)

        def should_skip_recovery_line(line):
            """.recover 스트림의 단일 라인 제어문을 선차단합니다."""
            s = line.strip()
            if not s:
                return False

            # sqlite3 .recover 출력에 간헐적으로 섞이는 트랜잭션 제어문은
            # 스트리밍 import 쪽에서 그대로 실행하면 'cannot commit - no transaction is active'를 유발할 수 있습니다.
            txn_line_patterns = (
                r'^BEGIN(?:\s+TRANSACTION)?\s*;?$',
                r'^COMMIT\s*;?$',
                r'^ROLLBACK\s*;?$',
                r'^SAVEPOINT\s+\S+\s*;?$',
                r'^RELEASE\s+\S+\s*;?$',
                r'^END(?:\s+TRANSACTION)?\s*;?$',
            )
            return any(re.search(p, s, re.IGNORECASE) for p in txn_line_patterns)

        # 디스크 파일 없이 스트리밍으로 statement를 넘깁니다.
        try:
            skipped_statements = 0
            written_statements = 0
            statement_lines = []
            for line in recover_proc.stdout:
                if should_skip_recovery_line(line):
                    skipped_statements += 1
                    continue

                statement_lines.append(line)
                if ';' not in line:
                    continue

                statement = ''.join(statement_lines)
                statement_lines = []

                if should_skip_recovery_statement(statement):
                    skipped_statements += 1
                    continue

                import_proc.stdin.write(statement)
                written_statements += 1

            if statement_lines:
                statement = ''.join(statement_lines)
                if not should_skip_recovery_statement(statement):
                    import_proc.stdin.write(statement)
                    written_statements += 1

            recover_stderr = recover_proc.stderr.read()
            recover_rc = recover_proc.wait(timeout=300)
            if recover_rc != 0 and not recover_stderr.strip():
                log("❌ sqlite3 CLI recovery failed: the recover step failed.")
                log("-> The sqlite3 CLI is not installed on this system, or the DB cannot be recovered.")
                log(f"-> Keeping the backup file ({backup_path}).")
                log("   Ubuntu/Debian: sudo apt install sqlite3")
                log("   Alpine Linux : apk add sqlite")
                return False

            import_proc.stdin.close()
            import_stderr = import_proc.stderr.read()
            import_rc = import_proc.wait(timeout=300)
            if import_rc != 0:
                log(f"❌ Failed to run the recovery SQL (code: {import_rc}): {import_stderr[:300]}")
                try:
                    if os.path.exists(recovered_path):
                        os.remove(recovered_path)
                        log("Discarded the temporary partial recovery copy.")
                except Exception:
                    pass
                return False

            log(f"Recovery SQL applied: {written_statements:,} statements written, {skipped_statements:,} FTS statements excluded")
        except Exception as import_err:
            log(f"❌ Exception while streaming the recovery SQL: {import_err}")
            try:
                if 'import_proc' in locals() and import_proc.stdin and not import_proc.stdin.closed:
                    import_proc.stdin.close()
            except Exception:
                pass
            try:
                if os.path.exists(recovered_path):
                    os.remove(recovered_path)
                    log("Discarded the temporary partial recovery copy.")
            except Exception:
                pass
            return False

        # 새 DB 무결성 및 설정 마무리
        try:
            new_conn = sqlite3.connect(recovered_path, timeout=10.0)
            new_conn.execute("PRAGMA journal_mode=WAL;")
            new_conn.execute("PRAGMA synchronous=NORMAL;")
            new_conn.commit()
            
            # 복구 DB 무결성 검증
            verify = new_conn.execute("PRAGMA integrity_check;").fetchone()
            new_conn.close()
        except Exception as db_err:
            log(f"❌ Error while setting up the new DB and checking integrity: {db_err}")
            return False

        if verify and verify[0] == 'ok':
            log("✅ Recovered DB integrity: OK")
            # 원본 교체
            os.replace(recovered_path, db_path)
            log(f"✅ [{label}] Recovery done - original file replaced")
            log(f"   Backup location: {backup_path}")
            return True
        else:
            log(f"❌ Recovered DB verification failed: {verify}")
            try:
                if os.path.exists(recovered_path):
                    os.remove(recovered_path)
                    log("Discarded the temporary partial recovery copy.")
            except Exception:
                pass
            return False

    except FileNotFoundError:
        log("❌ sqlite3 CLI not found.")
        log("   Ubuntu/Debian: sudo apt install sqlite3")
        log("   Alpine Linux : apk add sqlite")
        return False
    except Exception as e:
        log(f"❌ Error during recovery: {e}")
        return False

def rebuild_fts_index(db_path, label):
    """
    구형 FTS5 가상 테이블 및 그림자 테이블을 완전히 소거합니다.
    """
    sep()
    log(f"[{label}] Starting removal of old FTS5 virtual tables", prefix='')
    
    if not os.path.exists(db_path):
        log("⚠️  DB file does not exist. Skipping.")
        return False

    try:
        conn = sqlite3.connect(db_path, timeout=15.0)
        from database import cleanup_legacy_fts_index
        cleanup_legacy_fts_index(conn)
        conn.close()
        log("✅ Old FTS5 virtual tables removed.")
        return True
    except Exception as e:
        log(f"⚠️  Note during removal: {e}")
        return False

# ─────────────────────────────────────────────
# 메인 실행
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="BookOasis DB recovery script")
    parser.add_argument('--db', type=str, help="Path to a specific DB file to recover (e.g. test/chinh_media_general.db)")
    parser.add_argument('--yes', action='store_true', help="Skip the confirmation prompt and proceed")
    args = parser.parse_args()

    # DB_FILES 재구성
    if args.db:
        db_path = os.path.abspath(args.db)
        label = os.path.splitext(os.path.basename(db_path))[0]
        target_db_files = {label: db_path}
    else:
        target_db_files = DB_FILES

    sep('=')
    print("  BookOasis DB recovery script")
    print(f"  Run at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.db:
        print(f"  Target DB: {args.db}")
    else:
        print(f"  DB path  : {DB_DIR}")
    sep('=')
    print()

    print("⚠️  Before you start")
    print("  Make sure the BookOasis server (container) is")
    print("  completely stopped before running this script.")
    print("  Running it alongside a live server can corrupt the DB further.")
    print()

    if not args.yes:
        confirm = input("  Type 'yes' to continue: ").strip().lower()
        if confirm != 'yes':
            print("  Cancelled.")
            sys.exit(0)
    else:
        print("  Skipping the confirmation prompt because of [--yes].")

    print()

    # ── STEP 1: WAL 체크포인트 시도 ──
    sep('=')
    print("  STEP 1 - WAL checkpoint (no data loss)")
    sep('=')

    step1_results = {}
    for label, db_path in target_db_files.items():
        ok = step1_wal_checkpoint(db_path, label)
        step1_results[label] = ok

    print()

    # ── STEP 1 실패한 DB가 있으면 STEP 2 안내 ──
    failed = [label for label, ok in step1_results.items() if not ok]
    if failed:
        sep('=')
        print("  STEP 2 - full recovery (rebuild the corrupted DB)")
        sep('=')
        print(f"  Failed in Step 1: {', '.join(failed)}")
        print("  Step 2 extracts the recoverable data and rebuilds the DB.")
        print("  Some recent changes (reading progress, etc.) may be lost.")
        print()
        
        if args.yes:
            confirm2 = 'yes'
            print("  Running Step 2 right away because of [--yes].")
        else:
            confirm2 = input("  Type 'yes' to continue with Step 2: ").strip().lower()
            
        if confirm2 == 'yes':
            for label in failed:
                step2_full_recovery(target_db_files[label], label)
        else:
            print("  Skipping Step 2.")

    # ── STEP 3: 구형 FTS5 가상 테이블 디스크 잔여물 완전 정돈 ──
    print()
    sep('=')
    print("  STEP 3 - clean up old FTS5 virtual tables on disk")
    sep('=')
    for label, db_path in target_db_files.items():
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path, timeout=10.0)
                from database import cleanup_legacy_fts_index
                cleanup_legacy_fts_index(conn)
                conn.close()
                log(f"[{label}] Old FTS5 tables cleaned up on disk.")
            except Exception as fts_clean_err:
                log(f"[{label}] Old FTS5 cleanup passed: {fts_clean_err}")

    # ── 최종 상태 요약 ──
    print()
    sep('=')
    print("  Recovery finished - final status")
    sep('=')
    for label, db_path in target_db_files.items():
        if os.path.exists(db_path):
            try:
                conn   = sqlite3.connect(db_path, timeout=5.0)
                result = conn.execute("PRAGMA integrity_check;").fetchone()
                conn.close()
                status = "✅ OK" if result and result[0] == 'ok' else f"❌ {result}"
            except Exception as e:
                status = f"❌ Connection failed: {e}"
        else:
            status = "⚠️  No file"
        log(f"[{label}] Final status: {status}")

    print()
    print("  If recovery is done, restart the server:")
    print("    $ docker start bookoasis")
    print()

if __name__ == '__main__':
    main()
