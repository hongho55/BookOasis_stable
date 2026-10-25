// viewer/report_problem.js – 뷰어 오류 자리의 한 줄 조치 (알림센터 5단계).
// 일반 사용자: [관리자에게 알리기] → POST /api/problems/user-report (관리자 알림센터에 '사용자 신고' 카드).
// 관리자: 신고 대신 바로 [진단] 모달을 연다. view_manager.showViewerError가 부른다.
import { state } from '../state.js';

const REPORTABLE_TYPES = ['general', 'adult'];

function t(key, fallback) {
  const text = window.i18n && typeof window.i18n.t === 'function' ? window.i18n.t(key, {}, null) : null;
  return text && text !== key ? text : fallback;
}

function plainText(html) {
  const div = document.createElement('div');
  div.innerHTML = String(html ?? '');
  return (div.textContent || '').replace(/\s+/g, ' ').trim();
}

function isAdmin() {
  const user = state.currentUser || window.currentUser || {};
  return String(user.role || '').toLowerCase() === 'admin';
}

// 관리자: 오류가 나면 [진단]을 누르기 전에 미리 돌려, 걸린 항목과 결론을 오류 자리에 바로 보여 준다.
// (같은 GET /api/problems/diagnose — 원격 드라이브는 몇 초 걸린다. 그 사이 다른 책을 열면 결과를 버린다)
let diagnoseSeq = 0;

async function autoDiagnose(row, dbType, bookId) {
  const seq = ++diagnoseSeq;
  const box = document.createElement('div');
  box.className = 'viewer-report-diag';
  box.textContent = t('diagnose.running', '진단 중...');
  row.appendChild(box);
  try {
    const res = await fetch(`/api/problems/diagnose?type=${encodeURIComponent(dbType)}&book_id=${encodeURIComponent(bookId)}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.success) throw new Error(data.error || `HTTP ${res.status}`);
    if (seq !== diagnoseSeq || !box.isConnected || state.activeBookId !== bookId) return;
    const { diagnosisCheckText, diagnosisTone } = await import('../diagnosis_render.js');
    const { tr } = await import('../notification_render.js');
    const lines = (data.checks || [])
      .filter(c => c.status === 'warn' || c.status === 'fail')
      .map(c => diagnosisCheckText(c));
    if (data.conclusion) lines.push(`→ ${tr(data.conclusion.key, data.conclusion.vars || {}, '')}`);
    box.className = `viewer-report-diag notify-tone-${diagnosisTone(data)}`;
    box.replaceChildren(...lines.map(text => {
      const p = document.createElement('div');
      p.textContent = text;
      return p;
    }));
  } catch (err) {
    if (seq === diagnoseSeq && box.isConnected) box.remove();
    console.warn('[Viewer] auto diagnose failed:', err);
  }
}

export function clearViewerReportAction() {
  const row = document.getElementById('viewer-common-report');
  if (row) {
    row.hidden = true;
    row.innerHTML = '';
  }
}

export function showViewerReportAction(message, subMessage) {
  const row = document.getElementById('viewer-common-report');
  const viewer = document.getElementById('media-viewer-modal');
  const dbType = state.currentLibraryType || 'general';
  const bookId = state.activeBookId;
  if (!row || !bookId || !REPORTABLE_TYPES.includes(dbType) || !viewer || viewer.style.display === 'none') {
    clearViewerReportAction();
    return;
  }
  const errorText = [plainText(message), plainText(subMessage)].filter(Boolean).join(' · ').slice(0, 300);
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'viewer-report-btn';
  row.innerHTML = '';
  row.appendChild(btn);
  row.hidden = false;

  if (isAdmin()) {
    btn.textContent = t('problems.action.diagnose', '진단');
    btn.addEventListener('click', async () => {
      const m = await import('../book_diagnosis.js');
      const title = document.getElementById('viewer-title-text')?.textContent || '';
      m.openBookDiagnosis(dbType, bookId, title);
    });
    autoDiagnose(row, dbType, bookId);
    return;
  }

  btn.textContent = t('problems.action.report', '관리자에게 알리기');
  btn.addEventListener('click', async () => {
    btn.disabled = true;
    try {
      const res = await fetch('/api/problems/user-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: dbType, book_id: bookId, where: 'viewer', message: errorText, format: state.currentViewerFormat || '' }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.success) throw new Error(data.error || `HTTP ${res.status}`);
      const done = document.createElement('span');
      done.className = 'viewer-report-done';
      done.textContent = t('viewer.report_sent', '관리자에게 알렸습니다.');
      row.replaceChildren(done);
    } catch (err) {
      btn.disabled = false;
      if (typeof window.showToast === 'function') {
        window.showToast(t('viewer.report_failed', '알리지 못했습니다.'), 'error');
      }
      console.warn('[Viewer] report failed:', err);
    }
  });
}
