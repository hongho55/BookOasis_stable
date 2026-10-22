// system_actions.js - "일반 설정" 탭의 단발성 관리자 액션 버튼 (VAAPI 하드웨어 점검, Lazy 스캔 즉시 실행)
import * as api from '../api.js';

export async function runVaapiCheck() {
  const btn = document.getElementById('btn-check-vaapi');
  const resultEl = document.getElementById('vaapi-check-result');
  const devicePathEl = document.getElementById('setting-vaapi-device-path');
  if (!resultEl) return;

  const devicePath = devicePathEl?.value?.trim() || '/dev/dri/renderD128';

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<i class="lc lc-loader lc-spin"></i> ${i18n.t('settings.gen_vaapi_checking_btn')}`;
  }
  resultEl.style.display = 'block';
  resultEl.style.background = 'rgba(15, 23, 42, 0.6)';
  resultEl.style.border = '1px solid rgba(255,255,255,0.1)';
  resultEl.style.color = '#cbd5e1';
  resultEl.textContent = i18n.t('settings.gen_vaapi_checking');

  try {
    const data = await api.checkVaapiSupport(devicePath);
    if (!data.success) {
      resultEl.style.border = '1px solid rgba(239, 68, 68, 0.4)';
      resultEl.style.color = '#fca5a5';
      resultEl.textContent = i18n.t('settings.gen_vaapi_check_fail', { error: data.error || i18n.t('settings.gen_unknown_error') });
      return;
    }

    const overallLabel = {
      ok: i18n.t('settings.gen_vaapi_ok'),
      partial: i18n.t('settings.gen_vaapi_partial'),
      unavailable: i18n.t('settings.gen_vaapi_unavailable'),
      error: i18n.t('settings.gen_vaapi_no_ffmpeg'),
    }[data.overall] || data.overall;

    const colorMap = { ok: '#34d399', partial: '#fbbf24', unavailable: '#f87171', error: '#f87171' };
    resultEl.style.border = `1px solid ${colorMap[data.overall] || 'rgba(255,255,255,0.1)'}`;
    resultEl.style.color = '#e2e8f0';

    const lines = [overallLabel, '', ...(data.detail || [])];
    if (data.vainfo_output) {
      lines.push('', i18n.t('settings.gen_vaapi_vainfo_head'), data.vainfo_output.split('\n').slice(0, 12).join('\n'));
    }
    resultEl.textContent = lines.join('\n');

    // 점검한 디바이스 경로를 그대로 저장 - 실제 스트리밍 시(_detect_vaapi_available)도
    // 이 값을 참조하므로, 점검 결과와 실사용 판단 기준이 항상 같은 경로를 보게 만든다.
    try {
      await api.updateSystemSetting('FFMPEG_VAAPI_DEVICE', devicePath);
    } catch (saveErr) {
      console.error('[Settings] VAAPI 디바이스 경로 저장 실패:', saveErr);
    }
  } catch (e) {
    console.error('[Settings] VAAPI 점검 요청 실패:', e);
    resultEl.style.border = '1px solid rgba(239, 68, 68, 0.4)';
    resultEl.style.color = '#fca5a5';
    resultEl.textContent = i18n.t('settings.gen_server_request_error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<i class="lc lc-search"></i> ${i18n.t('settings.gen_vaapi_check_btn')}`;
    }
  }
}

window.runVaapiCheck = runVaapiCheck;

export async function triggerLazyScanNow() {
  try {
    if (typeof window.showToast === 'function') {
      window.showToast(i18n.t('settings.general_scanner_start'), 'info');
    }
    const res = await api.triggerLazyScan();
    if (res.success) {
      if (typeof window.showToast === 'function') {
        window.showToast(res.message, 'success');
      } else {
        alert(res.message);
      }
    } else {
      alert(i18n.t('settings.general_scanner_fail', {error: res.error}));
    }
  } catch (err) {
    console.error('Lazy 스캔 즉시 실행 중 에러:', err);
    alert(i18n.t('settings.general_server_error'));
  }
}

window.triggerLazyScanNow = triggerLazyScanNow;
