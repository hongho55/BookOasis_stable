# -*- coding: utf-8 -*-
"""구글 드라이브 링크 카테고리(클로즈 베타) 로그 요약 - 읽기 전용. MCP를 쓰지 않는 서버에서 실행:

    python tools/summarize_gdrive_beta_log.py               # 최근 24시간
    python tools/summarize_gdrive_beta_log.py --hours 72 --library 36
    python tools/summarize_gdrive_beta_log.py --all
"""
import argparse
import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.encoding_helper import force_utf8_stdio
force_utf8_stdio()

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
except Exception:
    pass

from services.gdrive_beta_summary import summarize


def main():
    parser = argparse.ArgumentParser(description='구글 드라이브 링크(클로즈 베타) 로그 요약 (읽기 전용)')
    parser.add_argument('--hours', type=float, default=24, help='최근 N시간 (기본 24)')
    parser.add_argument('--all', action='store_true', help='남아 있는 로그 전체')
    parser.add_argument('--library', type=int, default=0, help='카테고리 id (기본 전체)')
    args = parser.parse_args()
    result = summarize(None if args.all else args.hours, args.library or None)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
