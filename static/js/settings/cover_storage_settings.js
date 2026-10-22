// cover_storage_settings.js - 커버 이미지 저장 경로 설정 및 기존 커버 파일 이관(마이그레이션)
import * as api from '../api.js';

let coverMigratePolling = false;

export async function startCoverStorageMigration() {
  const resultEl = document.getElementById('cover-storage-migrate-result');
  try {
    const data = await api.migrateCoverStorage();
    if (!data || !data.success) throw new Error((data && data.error) || i18n.t('settings.gen_unknown_error'));
    if (resultEl) {
      resultEl.textContent = i18n.t('settings.gen_migrate_started');
      resultEl.style.color = 'var(--app-text-muted)';
    }
    if (!coverMigratePolling) {
      coverMigratePolling = true;
      pollCoverStorageMigrateStatus();
    }
  } catch (e) {
    console.error('[Settings] 커버 이관 시작 실패:', e);
    if (resultEl) {
      resultEl.textContent = i18n.t('settings.gen_migrate_start_fail', { error: e.message || e });
      resultEl.style.color = '#f87171';
    }
  }
}

async function pollCoverStorageMigrateStatus() {
  const resultEl = document.getElementById('cover-storage-migrate-result');
  try {
    const data = await api.fetchCoverStorageMigrateStatus();
    const status = data && data.status;
    if (!status) return;
    if (resultEl) {
      if (status.status === 'running') {
        resultEl.textContent = i18n.t('settings.gen_migrate_progress', { moved: status.moved, total: status.total });
        resultEl.style.color = 'var(--app-text-muted)';
      } else if (status.status === 'done') {
        resultEl.textContent = i18n.t('settings.gen_migrate_done', { moved: status.moved });
        resultEl.style.color = 'var(--app-text-muted)';
      } else if (status.status === 'error') {
        resultEl.textContent = i18n.t('settings.gen_migrate_fail', { error: status.error });
        resultEl.style.color = '#f87171';
      }
    }
    if (status.status === 'running') {
      setTimeout(() => { pollCoverStorageMigrateStatus(); }, 1500);
    } else {
      coverMigratePolling = false;
    }
  } catch (e) {
    console.error('[Settings] 커버 이관 상태 조회 실패:', e);
    coverMigratePolling = false;
  }
}
