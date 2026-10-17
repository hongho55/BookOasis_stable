# -*- coding: utf-8 -*-
"""
book_rating.py -- 도서 상세 페이지 헤더의 정적 점수 별을 커뮤니티 별점으로 대체하는 샘플 플러그인.

- plugin_data_relay(이 리포 안, fly.io "bo-plugin-relay"로 배포)에 관리자가 사전에 1회
  /register로 등록해둔 plugin_id("bookoasis_ratings", 필드 book_key/rating/submitter_domain,
  daily_write_limit=20)를 그대로 사용한다. 이 플러그인 코드는 스키마를 새로 만들지 않고
  이미 승인된 plugin_id를 호출하기만 한다.
- 도서 식별(book_key)은 ISBN이 있으면 ISBN, 없으면 (제목+작가), 작가도 없으면 제목
  단독으로 계산한다(앞뒤 공백만 제거, 판본 자동 병합은 하지 않음).
- submitter_domain은 어뷰징 방지용 "신원 문자열"일 뿐이라 relay가 검증하지 않는다 -
  관리자가 설정에 직접 입력한 값을 그대로 신뢰해서 보낸다(자동 감지 로직 없음, 단순함 우선).
- 시리즈당 1회/하루 20회 상한은 이 플러그인이 아니라 relay가 최종 강제한다
  (unique_by=["book_key"]로 재제출 시 덮어쓰기, daily_write_limit=20으로 429).
- 성인 서재/오디오북/영상 강좌에는 노출하지 않는다 - rating_widget.sessions를 'general'로만
  선언해 코어의 _resolve_plugin_sessions()가 자동으로 배제해준다.
"""
import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor

import requests

from plugins.metadata.base import BaseMetadataProvider

logger = logging.getLogger(__name__)

# relay(fly.io)는 쉬면 머신이 꺼졌다가 첫 요청에 약 2초 걸려 깨어난다. 조회는 짧게 끊고(서버 스레드를 오래 잡지 않게)
# 제출만 조금 여유를 둔다. (1.0.0은 10초 x 최대 3회 순차 호출이라 relay가 안 되는 날 상세 화면마다 스레드를 최대 30초 잡았다)
REQUEST_TIMEOUT = 3
SUBMIT_TIMEOUT = 5
RELAY_PLUGIN_ID = "bookoasis_ratings"
VERIFY_CACHE_TTL = 60 * 60 * 24  # 하루 - 인증이 여전히 유효한지 재확인하는 주기
WIDGET_CACHE_TTL = 300           # 도서별 별점 결과 재사용(제출하면 즉시 갱신)
FAILURE_BACKOFF_TTL = 120        # relay가 실패하면 이 시간 동안은 부르지 않고 바로 실패를 돌려준다(상세 화면마다 relay를 깨우지 않게)


class BookRatingMetadataProvider(BaseMetadataProvider):
    """도서 상세 헤더 별점을 plugin_data_relay 기반 커뮤니티 별점으로 대체하는 플러그인."""

    id = "book_rating"
    name = "커뮤니티 별점"
    is_searchable = False

    config_schema = [
        {
            "key": "RELAY_DOMAIN_URL",
            "label": "plugin_data_relay 배포 URL",
            "type": "text",
            "default": "https://bo-plugin-relay.fly.dev",
            "required": True,
        },
        {
            "key": "RELAY_USER_ID",
            "label": "이 설치(install) 식별 ID",
            "type": "text",
            "required": True,
        },
        {
            "key": "RELAY_SECRET_TOKEN",
            "label": "이 설치(install)의 32자리 비밀 토큰",
            "type": "password",
            "required": True,
        },
        {
            "key": "SUBMITTER_DOMAIN",
            "label": "내 BookOasis 도메인 (없으면 IP를 직접 입력)",
            "type": "text",
            "required": True,
            "description": "relay는 이 값을 검증하지 않고 그대로 신뢰합니다. 어뷰징 방지용 표시값일 뿐이니 정확한 값을 입력하세요.",
        },
    ]

    # 도서 상세 페이지 헤더의 정적 점수 별(.detail-score)을 이 플러그인이 대체한다.
    # 일반 도서 서재에만 노출 - 성인/오디오북/영상 강좌는 별점 기능 자체를 노출하지 않는다.
    rating_widget = {"title": "커뮤니티 별점", "order": 10, "sessions": "general"}

    update_manifest = {
        "enabled": True,
        "provider": "github-raw",
        "raw_base_url": "https://raw.githubusercontent.com/leeyj/BookOasis_stable/main/sample_plugins/metadata/book_rating",
        "files": ["book_rating.py", "__init__.py", "VERSION"],
        "version_file": "VERSION",
        "version_key": "plugin version",
        "show_sample_update_button": True,
    }

    # ------------------------------------------------------------------
    # 필수 계약 (검색형 메타데이터 기능은 사용하지 않음 - 별점 위젯 전용)
    # ------------------------------------------------------------------
    def search(self, db_type, query):
        return []

    def apply(self, db_type, book_id, item_data):
        return False, "커뮤니티 별점 플러그인은 도서 메타데이터 적용을 지원하지 않습니다."

    # ------------------------------------------------------------------
    # 설정/식별 헬퍼
    # ------------------------------------------------------------------
    def _relay_config(self, db_type):
        cfg = self.get_plugin_config(db_type, default={}) or {}
        domain_url = str(cfg.get("RELAY_DOMAIN_URL") or "").strip().rstrip("/")
        user_id = str(cfg.get("RELAY_USER_ID") or "").strip()
        secret_token = str(cfg.get("RELAY_SECRET_TOKEN") or "").strip()
        submitter_domain = str(cfg.get("SUBMITTER_DOMAIN") or "").strip()
        return domain_url, user_id, secret_token, submitter_domain

    def _book_key(self, context):
        """ISBN -> (제목+작가) -> 제목 단독 순으로 도서를 식별한다. 판본 자동 병합은 하지
        않으므로(완전판/초회판 등은 제목 자체가 다르면 별개 도서로 취급) 여기서 별도의
        정규화(괄호 제거 등)는 하지 않고 trim만 한다."""
        title = str(context.get("series_name") or "").strip()
        author = str(context.get("author") or "").strip()
        isbn = str(context.get("isbn") or "").strip()

        if isbn:
            return f"isbn:{isbn}"
        if author:
            return f"ta:{title}|{author}"
        return f"t:{title}"

    def _ensure_verified(self, domain_url, user_id, secret_token):
        """relay에 이 설치(install)가 등록돼 있는지 확인/자동 등록한다. 매 요청마다 왕복하지
        않도록 결과를 하루 동안 플러그인 전용 Redis 캐시에 남긴다.
        캐시 키에 relay 주소를 넣는다 - 1.0.0은 user_id만 써서, relay 주소를 바꿔도 예전 relay의
        "인증됨"이 하루 동안 남아 새 relay에서 자동 등록을 건너뛰고 계속 실패했다."""
        cache_key = f"verified:{self._scope_hash(domain_url, user_id)}"
        if self.cache_get(cache_key) == "1":
            return True

        resp = requests.post(
            f"{domain_url}/api/{RELAY_PLUGIN_ID}/verify",
            json={"user_id": user_id, "secret_token": secret_token},
            timeout=REQUEST_TIMEOUT,
        )
        ok = resp.ok and resp.json().get("success")
        if ok:
            self.cache_set(cache_key, "1", ttl=VERIFY_CACHE_TTL)
        return ok

    # ------------------------------------------------------------------
    # 캐시 / 실패 백오프 헬퍼
    # ------------------------------------------------------------------
    @staticmethod
    def _scope_hash(*parts):
        return hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:20]

    def _widget_cache_key(self, domain_url, user_id, book_key):
        return f"widget:{self._scope_hash(domain_url, user_id, book_key)}"

    def _backoff_key(self, domain_url):
        return f"backoff:{self._scope_hash(domain_url)}"

    def _in_backoff(self, domain_url):
        cached = self.cache_get(self._backoff_key(domain_url))
        return cached or None

    def _enter_backoff(self, domain_url, error):
        self.cache_set(self._backoff_key(domain_url), error, ttl=FAILURE_BACKOFF_TTL)

    def _clear_backoff(self, domain_url):
        self.cache_delete(self._backoff_key(domain_url))

    def _load_widget_cache(self, domain_url, user_id, book_key):
        raw = self.cache_get(self._widget_cache_key(domain_url, user_id, book_key))
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return None

    def _store_widget_cache(self, domain_url, user_id, book_key, result):
        self.cache_set(self._widget_cache_key(domain_url, user_id, book_key),
                       json.dumps(result, ensure_ascii=False), ttl=WIDGET_CACHE_TTL)

    # ------------------------------------------------------------------
    # rating_widget 계약 구현
    # ------------------------------------------------------------------
    def get_rating_widget_data(self, db_type, context):
        if db_type != "general":
            return {"success": False, "error": "성인/오디오북/영상 강좌는 별점 기능을 지원하지 않습니다."}

        domain_url, user_id, secret_token, _submitter_domain = self._relay_config(db_type)
        if not domain_url or not user_id or not secret_token:
            return {"success": False, "error": "커뮤니티 별점 플러그인 설정이 완료되지 않았습니다."}

        book_key = self._book_key(context)
        cached = self._load_widget_cache(domain_url, user_id, book_key)
        if cached:
            return cached
        backoff_error = self._in_backoff(domain_url)
        if backoff_error:
            return {"success": False, "error": backoff_error}

        try:
            if not self._ensure_verified(domain_url, user_id, secret_token):
                error = "relay 인증에 실패했습니다."
                self._enter_backoff(domain_url, error)
                return {"success": False, "error": error}

            auth = {"user_id": user_id, "secret_token": secret_token}

            # 집계와 내 별점 조회는 서로 기다릴 이유가 없어 동시에 보낸다(1.0.0은 차례로 보냈다)
            with ThreadPoolExecutor(max_workers=2) as pool:
                agg_future = pool.submit(
                    requests.get,
                    f"{domain_url}/api/{RELAY_PLUGIN_ID}/records/aggregate",
                    params={**auth, "agg_field": "rating", "filter_field": "book_key", "filter_value": book_key},
                    timeout=REQUEST_TIMEOUT,
                )
                mine_future = pool.submit(self._find_my_rating, domain_url, auth, book_key, user_id)
                agg_resp = agg_future.result()
                my_rating = mine_future.result()

            agg = agg_resp.json() if agg_resp.ok else {}
            if not agg.get("success"):
                error = agg.get("message") or f"별점 집계 조회에 실패했습니다. (relay 응답 {agg_resp.status_code})"
                logger.warning("[book_rating] 별점 집계 실패: %s %s", agg_resp.status_code, domain_url)
                self._enter_backoff(domain_url, error)
                return {"success": False, "error": error}

            result = {
                "success": True,
                "average": round(float(agg.get("avg") or 0), 1),
                "count": int(agg.get("count") or 0),
                "my_rating": my_rating,
            }
            self._store_widget_cache(domain_url, user_id, book_key, result)
            return result
        except requests.RequestException as e:
            logger.warning("[book_rating] 별점 조회 실패: %s", e)
            error = "커뮤니티 별점 서버에 연결할 수 없습니다."
            self._enter_backoff(domain_url, error)
            return {"success": False, "error": error}

    def submit_rating(self, db_type, context, rating):
        if db_type != "general":
            return {"success": False, "error": "성인/오디오북/영상 강좌는 별점 기능을 지원하지 않습니다."}

        domain_url, user_id, secret_token, submitter_domain = self._relay_config(db_type)
        if not domain_url or not user_id or not secret_token:
            return {"success": False, "error": "커뮤니티 별점 플러그인 설정이 완료되지 않았습니다."}

        try:
            if not self._ensure_verified(domain_url, user_id, secret_token):
                return {"success": False, "error": "relay 인증에 실패했습니다."}

            # 0.5 단위로 정규화 - 라우트에서 이미 반올림해 보내지만 provider 단독 호출 경로도
            # 대비해 여기서도 한 번 더 맞춘다.
            rating = round(float(rating) * 2) / 2

            book_key = self._book_key(context)
            resp = requests.post(
                f"{domain_url}/api/{RELAY_PLUGIN_ID}/records",
                json={
                    "user_id": user_id,
                    "secret_token": secret_token,
                    "values": {"book_key": book_key, "rating": rating, "submitter_domain": submitter_domain},
                    "unique_by": ["book_key"],
                },
                timeout=SUBMIT_TIMEOUT,
            )
            body = resp.json() if resp.content else {}
            if not resp.ok or not body.get("success"):
                return {"success": False, "error": body.get("message") or "별점 제출에 실패했습니다."}

            auth = {"user_id": user_id, "secret_token": secret_token}
            agg_resp = requests.get(
                f"{domain_url}/api/{RELAY_PLUGIN_ID}/records/aggregate",
                params={**auth, "agg_field": "rating", "filter_field": "book_key", "filter_value": book_key},
                timeout=REQUEST_TIMEOUT,
            )
            agg = agg_resp.json() if agg_resp.ok else {}

            result = {
                "success": True,
                "average": round(float(agg.get("avg") or rating), 1),
                "count": int(agg.get("count") or 1),
                "my_rating": rating,
            }
            # 제출이 됐으면 relay는 살아 있다 - 백오프를 풀고 이 도서의 캐시를 새 값으로 바꾼다
            self._clear_backoff(domain_url)
            self._store_widget_cache(domain_url, user_id, book_key, result)
            return result
        except requests.RequestException as e:
            logger.warning("[book_rating] 별점 제출 실패: %s", e)
            return {"success": False, "error": "커뮤니티 별점 서버에 연결할 수 없습니다."}

    def _find_my_rating(self, domain_url, auth, book_key, user_id):
        """list_records는 user_id로 필터링되지 않으므로(같은 book_key의 다른 사용자 레코드도
        함께 온다), 응답에서 내 user_id와 일치하는 행만 찾아 my_rating으로 쓴다."""
        try:
            resp = requests.get(
                f"{domain_url}/api/{RELAY_PLUGIN_ID}/records",
                params={**auth, "filter_field": "book_key", "filter_value": book_key, "limit": 200},
                timeout=REQUEST_TIMEOUT,
            )
            if not resp.ok:
                return None
            records = resp.json().get("records") or []
            for record in records:
                if record.get("user_id") == user_id:
                    return float(record.get("rating"))
        except (requests.RequestException, TypeError, ValueError):
            pass
        return None
