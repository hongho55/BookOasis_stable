// volume_controller.js – 권별(Volume) 목록 필터링, 정렬 및 뷰 상태 관리

export const detailVolumeViewState = {
  key: '',
  unreadOnly: false,
  sortOrder: 'oldest'
};

export function applyDetailVolumeView() {
  const section = document.querySelector('.volumes-section');
  if (!section) return;

  // 리스트 모드(.volumes-list + .volume-card) 또는 그리드 모드(.volumes-list-grid + .vol-grid-card) 모두 지원
  const list = section.querySelector('.volumes-list') || section.querySelector('.volumes-list-grid');
  const cards = Array.from(section.querySelectorAll('.volume-card, .vol-grid-card'));

  cards.sort((left, right) => {
    // data-title 기반 자연 정렬 (파일명 순서 기준)
    const titleA = left.dataset.title || '';
    const titleB = right.dataset.title || '';
    const cmp = titleA.localeCompare(titleB, 'ko', { numeric: true, sensitivity: 'base' });
    return detailVolumeViewState.sortOrder === 'newest' ? -cmp : cmp;
  });

  let visibleCount = 0;
  cards.forEach(card => {
    if (list) list.appendChild(card);
    const isNotCompleted = card.dataset.isCompleted !== '1';
    const visible = !detailVolumeViewState.unreadOnly || isNotCompleted;
    card.style.display = visible ? '' : 'none';
    if (visible) visibleCount += 1;
  });

  const controls = section.querySelector('.volume-list-controls');
  if (controls) controls.innerHTML = renderVolumeControlsInner(detailVolumeViewState.unreadOnly, detailVolumeViewState.sortOrder);

  const empty = section.querySelector('.volumes-empty-filter');
  if (empty) empty.style.display = visibleCount === 0 ? 'block' : 'none';
}

// 권 목록 제목 줄 오른쪽 컨트롤: 상자 없는 글자 버튼 두 개.
// "안 읽은 권만"은 켜고 끄는 토글, 정렬은 지금 순서 하나만 보이고 누르면 반대 순서로 바뀐다
// (data-sort가 다음 값 - interactions.js detail-volume-sort가 그대로 setDetailVolumeSort에 넘긴다)
function renderVolumeControlsInner(unreadOnly, sortOrder) {
  const isNewest = sortOrder === 'newest';
  return `
    <button type="button" class="volume-text-toggle${unreadOnly ? ' active' : ''}" data-role="detail-volume-filter" aria-pressed="${unreadOnly}">
      <i class="lc ${unreadOnly ? 'lc-circle-check' : 'lc-circle'}" aria-hidden="true"></i> ${i18n.t('detail.unread_only')}
    </button>
    <button type="button" class="volume-text-toggle" data-role="detail-volume-sort" data-sort="${isNewest ? 'oldest' : 'newest'}" title="${i18n.t('detail.sort_order')}">
      <i class="lc ${isNewest ? 'lc-arrow-down-1-0' : 'lc-arrow-up-0-1'}" aria-hidden="true"></i> ${i18n.t(isNewest ? 'detail.sort_newest' : 'detail.sort_oldest')}
    </button>
  `;
}

export function renderVolumeControls(unreadOnly, sortOrder) {
  return `<div class="volume-list-controls" aria-label="${i18n.t('detail.list_controls')}">${renderVolumeControlsInner(unreadOnly, sortOrder)}</div>`;
}

export function toggleDetailUnreadFilter() {
  detailVolumeViewState.unreadOnly = !detailVolumeViewState.unreadOnly;
  applyDetailVolumeView();
}

export function setDetailVolumeSort(sortOrder) {
  detailVolumeViewState.sortOrder = sortOrder === 'newest' ? 'newest' : 'oldest';
  applyDetailVolumeView();
}
