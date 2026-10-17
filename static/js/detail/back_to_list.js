// back_to_list.js – 상세 뷰 → 그리드 뷰/대시보드 복귀
// 카테고리를 고를 때마다(부팅 포함) 불리므로 상세 모듈 전체(detail/index.js)를 받지 않도록 분리했다(2.9.5).
// 코어 모듈(state·view_manager·category_indicator)만 쓴다.
import { state } from '../state.js';
import { switchActiveView } from '../view_manager.js';
import { updateCurrentCategoryIndicator } from '../category_indicator.js';

export function goBackToList(triggerBack = true) {
  updateCurrentCategoryIndicator(state.currentLibraryId);

  const isMobileLayout = window.matchMedia('(max-width: 1200px)').matches;
  const avoidDocumentScrollRestore = !triggerBack && isMobileLayout;

  const targetScroll = (state.scrollPositions && (
    state.scrollPositions['last_pos'] ?? 
    state.scrollPositions[state.currentLibraryId]
  )) || 0;

  console.log(`[Scroll-Debug] RESTORING scroll position to: ${targetScroll}px (Current lib: ${state.currentLibraryId})`);

  if (state.currentLibraryId === 'home') {
    switchActiveView('dashboard');
  } else {
    switchActiveView('grid');
  }

  // 상세에서 돌아올 때 저장된 스크롤 위치가 있으면 즉시 및 렌더 후 다중 복원
  const doScroll = (pos) => {
    if (avoidDocumentScrollRestore) {
      // 모바일 OS back(popstate) 경로에서는 문서 스크롤을 올리지 않고,
      // 실제 리스트 컨테이너만 복원해 상단 카테고리 UI 이탈을 방지한다.
      window.scrollTo(0, 0);
      document.documentElement.scrollTop = 0;
      document.body.scrollTop = 0;
    } else {
      window.scrollTo(0, pos);
      document.documentElement.scrollTop = pos;
      document.body.scrollTop = pos;
    }
    const mainContent = document.querySelector('.library-main-content');
    if (mainContent) mainContent.scrollTop = pos;
    const gridView = document.getElementById('books-grid-view');
    const dashView = document.getElementById('library-dashboard-view');
    if (gridView) gridView.scrollTop = pos;
    if (dashView) dashView.scrollTop = pos;
  };

  if (targetScroll > 0) {
    try {
      doScroll(targetScroll);
      requestAnimationFrame(() => doScroll(targetScroll));
      setTimeout(() => doScroll(targetScroll), 50);
      setTimeout(() => doScroll(targetScroll), 150);
    } catch (e) {
      console.warn('[goBackToList] failed to restore scroll', e);
    }
  }

  // 상세를 보는 동안 스캔이 끝났다면 그사이 무효화된 목록만 지금 다시 불러온다.
  if (state.currentLibraryId !== 'home' && typeof window.refreshBooksListIfStale === 'function') {
    window.refreshBooksListIfStale();
  }

  // 상세 뷰 해시(#detail)가 남아있는 경우 브라우저 외부/홈으로 튕김(history.back) 없이 해시만 안전하게 제거
  if (window.location.hash.startsWith('#detail')) {
    try {
      history.replaceState({ view: 'list', libraryId: state.currentLibraryId }, '', window.location.pathname + window.location.search);
    } catch (e) {}
  }
}
