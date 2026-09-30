from unittest.mock import patch

from flask import Flask

from api.app_opds import app_opds_bp


def _client():
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY='test-app-opds-progress')
    app.register_blueprint(app_opds_bp)
    return app.test_client()


def _state(page=3, updated='2026-09-30 10:00:00'):
    return {
        'file_format': 'pdf',
        'total_pages': 100,
        'pages_read': page,
        'last_read_at': updated,
        'last_epub_cfi': None,
        'last_epub_href': None,
        'last_epub_spine_index': None,
        'last_epub_percent': 0,
        'last_epub_fingerprint': None,
        'last_epub_updated_at': None,
    }


def test_progress_state_uses_authenticated_user_and_returns_revision():
    with (
        patch('api.app_opds._require_app_opds_auth', return_value=None),
        patch('api.app_opds._get_authenticated_user_cached', return_value={'id': 7, 'role': 'user'}),
        patch(
            'api.app_opds.viewer_get_progress_state',
            return_value={'status': 'ok', 'state': _state()},
        ) as get_state,
    ):
        response = _client().get('/app-opds/api/media/progress-state?book_id=11')

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['success'] is True
    assert payload['revision'].startswith('v1:')
    get_state.assert_called_once_with('general', '11', user_id=7)


def test_progress_state_never_falls_back_to_default_user():
    with (
        patch('api.app_opds._require_app_opds_auth', return_value=None),
        patch('api.app_opds._get_authenticated_user_cached', return_value=None),
        patch('api.app_opds.viewer_get_progress_state') as get_state,
    ):
        response = _client().get('/app-opds/api/media/progress-state?book_id=11')

    assert response.status_code == 401
    get_state.assert_not_called()


def test_progress_rejects_stale_revision_without_writing():
    with (
        patch('api.app_opds._require_app_opds_auth', return_value=None),
        patch('api.app_opds._get_authenticated_user_cached', return_value={'id': 7, 'role': 'user'}),
        patch(
            'api.app_opds.viewer_get_progress_state',
            return_value={'status': 'ok', 'state': _state()},
        ),
        patch('api.app_opds.viewer_save_progress') as save_progress,
    ):
        response = _client().post(
            '/app-opds/api/media/progress',
            json={
                'book_id': 11,
                'page_idx': 8,
                'total_pages': 100,
                'base_revision': 'v1:stale',
            },
        )

    assert response.status_code == 409
    payload = response.get_json()
    assert payload['error'] == 'progress_conflict'
    assert payload['revision'].startswith('v1:')
    save_progress.assert_not_called()


def test_progress_matching_revision_flushes_for_authenticated_user():
    current = _state()
    updated = _state(page=9, updated='2026-09-30 10:01:00')

    with (
        patch('api.app_opds._require_app_opds_auth', return_value=None),
        patch('api.app_opds._get_authenticated_user_cached', return_value={'id': 7, 'role': 'user'}),
        patch(
            'api.app_opds.viewer_get_progress_state',
            side_effect=[
                {'status': 'ok', 'state': current},
                {'status': 'ok', 'state': updated},
            ],
        ),
        patch('api.app_opds.viewer_save_progress', return_value=True) as save_progress,
    ):
        initial = _client().get('/app-opds/api/media/progress-state?book_id=11').get_json()

    with (
        patch('api.app_opds._require_app_opds_auth', return_value=None),
        patch('api.app_opds._get_authenticated_user_cached', return_value={'id': 7, 'role': 'user'}),
        patch(
            'api.app_opds.viewer_get_progress_state',
            side_effect=[
                {'status': 'ok', 'state': current},
                {'status': 'ok', 'state': updated},
            ],
        ),
        patch('api.app_opds.viewer_save_progress', return_value=True) as save_progress,
    ):
        response = _client().post(
            '/app-opds/api/media/progress',
            json={
                'book_id': 11,
                'page_idx': 8,
                'total_pages': 100,
                'base_revision': initial['revision'],
            },
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['success'] is True
    assert payload['revision'] != initial['revision']
    save_progress.assert_called_once_with(
        'general',
        11,
        8,
        100,
        epub_session=None,
        user_id=7,
        flush_immediately=True,
    )


def test_progress_busy_write_is_retryable():
    current = _state()
    with (
        patch('api.app_opds._require_app_opds_auth', return_value=None),
        patch('api.app_opds._get_authenticated_user_cached', return_value={'id': 7, 'role': 'user'}),
        patch(
            'api.app_opds.viewer_get_progress_state',
            return_value={'status': 'ok', 'state': current},
        ),
        patch('api.app_opds.viewer_save_progress', return_value=False),
    ):
        response = _client().post(
            '/app-opds/api/media/progress',
            json={'book_id': 11, 'page_idx': 8, 'total_pages': 100},
        )

    assert response.status_code == 503
    assert response.get_json()['error'] == 'progress_write_busy'
