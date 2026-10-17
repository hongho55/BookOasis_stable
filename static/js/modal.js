// modal.js – 도서 상세 인라인 뷰 진입점 (상세 모듈 지연 로딩 & 전역 바인딩)
//
// 상세 모듈(detail/*, 12개)은 홈 첫 화면에 필요 없어 처음 상세를 열 때 불러온다(2.9.5, 홈 진입 요청 수 줄이기).
// goBackToList는 카테고리를 고를 때마다(부팅 포함) 불리므로 가벼운 back_to_list.js에서 바로 가져온다.
// 이 모듈에서 import하는 곳은 openBookDetail·goBackToList뿐이다(나머지 상세 함수는 window 바인딩으로만 쓰인다).
import { lazyModule, bindLazyGlobals } from './utils/lazy_module.js';
import { goBackToList } from './detail/back_to_list.js';

export const loadDetail = lazyModule(async () => {
  const [index, volume, editor, actions] = await Promise.all([
    import('./detail/index.js'),
    import('./detail/volume_controller.js'),
    import('./detail/metadata_editor.js'),
    import('./detail/book_actions.js'),
  ]);
  return { ...index, ...volume, ...editor, ...actions };
});

export async function openBookDetail(...args) {
  const detail = await loadDetail();
  return detail.openBookDetail(...args);
}

export { goBackToList };

// ── Global Window Bindings (HTML 및 인라인 이벤트 100% 하위 호환성 보장) ──
window.openBookDetail = openBookDetail;
window.goBackToList = goBackToList;
bindLazyGlobals(loadDetail, [
  'toggleDetailUnreadFilter',
  'setDetailVolumeSort',
  'toggleBookFavorite',
  'toggleSeriesFavorite',
  'toggleMetaEditMode',
  'triggerCoverUpload',
  'handleCoverUploadSelect',
  'handleCoverDrop',
  'saveManualMetadata',
  'handleUnlockMetadataEvent',
  'rescanBook',
  'rescanMissingBooks',
  'rescanSeries',
  'markSeriesCompleted',
  'markSeriesUnread',
  'showGlobalLoadingSpinner',
  'hideGlobalLoadingSpinner',
]);
