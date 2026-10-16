# -*- coding: utf-8 -*-
"""home_banner - 홈 화면 맨 위 배너(그림 + 한 줄 문구) 위젯.

home_widget 계약 그대로(사용자가 "홈 화면 플러그인 배치 모드"에서 직접 추가)이며, frame:'none'으로
제목줄 없이 그림이 곧 위젯이 된다. 그림/문구는 플러그인 설정에서 바꾼다(비우면 기본값).

기본 그림: Auguste Renoir, "View of the Seacoast near Wargemont in Normandy" (1880), The Metropolitan Museum of Art,
Open Access (CC0, 퍼블릭 도메인) - CREDITS.md 참고. 그림은 dashboard.css 대신 get_dashboard_data()의
items로 data URI를 보내 위젯 Shadow DOM에서 배경으로 쓴다(플러그인 폴더의 파일을 서빙하는 경로가 없어서).
"""
import base64
import os
import re
from functools import lru_cache

from plugins.metadata.base import BaseMetadataProvider

DEFAULT_MESSAGE = "오늘도 한 페이지, 천천히."
DEFAULT_CREDIT = "Auguste Renoir, View of the Seacoast near Wargemont in Normandy (1880) · The Met, CC0"
_MAX_MESSAGE = 120
# 배경 이미지 주소는 http(s) 또는 같은 서버 경로(/...)만, CSS url("...")을 깰 수 있는 문자는 거부
_SAFE_URL = re.compile(r'^(https?://|/)[^\s"\'()\\<>]+$')


@lru_cache(maxsize=1)
def _default_image_data_uri() -> str:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'banner_default.webp')
    try:
        with open(path, 'rb') as f:
            return 'data:image/webp;base64,' + base64.b64encode(f.read()).decode('ascii')
    except OSError:
        return ''


class HomeBannerMetadataProvider(BaseMetadataProvider):
    id = "home_banner"
    name = "홈 배너"
    is_searchable = False
    config_schema = [
        {
            "key": "IMAGE_URL",
            "label": "배너 그림 주소",
            "type": "text",
            "required": False,
            "description": "가로로 긴 그림의 주소(https://... 또는 /로 시작하는 이 서버 경로). 비워 두면 기본 그림(르누아르, 바르주몽 해안)을 씁니다.",
        },
        {
            "key": "MESSAGE",
            "label": "배너 문구",
            "type": "text",
            "required": False,
            "description": f"그림 위에 보일 한 줄 문구(최대 {_MAX_MESSAGE}자). 비워 두면 \"{DEFAULT_MESSAGE}\"",
        },
    ]
    home_widget = {
        "title": "홈 배너",
        "subtitle": "그림과 한 줄 문구",
        "provider": "BookOasis",
        "icon": "fa-solid fa-image",
        "order": 5,          # 코어 섹션(10/20/30)보다 앞 - 맨 위
        "layout": "full",
        "frame": "none",     # 제목줄 없이 그림만
        "sessions": "all",
    }

    def search(self, db_type, query):
        return []

    def apply(self, db_type, book_id, item_data):
        return False, "홈 배너 플러그인은 메타데이터 적용을 지원하지 않습니다."

    def get_dashboard_data(self, db_type, limit=10):
        try:
            # 설정은 세션과 상관없이 하나(일반 도서 DB에 저장된 값)
            config = self.get_plugin_config('general', default={}) or {}
        except Exception:
            config = {}
        if not isinstance(config, dict):
            config = {}

        image_url = str(config.get('IMAGE_URL') or '').strip()
        if image_url and not _SAFE_URL.match(image_url):
            image_url = ''
        message = str(config.get('MESSAGE') or '').strip()[:_MAX_MESSAGE] or DEFAULT_MESSAGE

        return {
            "success": True,
            "items": [{
                "image": image_url or _default_image_data_uri(),
                "message": message,
                "credit": '' if image_url else DEFAULT_CREDIT,
            }],
        }
