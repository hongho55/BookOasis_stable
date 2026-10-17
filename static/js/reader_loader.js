// reader_loader.js – 뷰어 지연 로딩 진입점 (2.9.5)
//
// 뷰어 모듈(viewer.js + viewer/*, 만화·TXT·PDF 엔진 등 35개)은 홈 첫 화면에 필요 없어 처음 책을 열 때 불러온다.
// 키보드 리스너는 뷰어가 열려 있을 때만 동작하므로(input_controller.js handleViewerKeydown) 불러올 때 등록해도 같다.
import { lazyModule } from './utils/lazy_module.js';

export const loadViewer = lazyModule(async () => {
  const [viewer] = await Promise.all([
    import('./viewer.js'),
    import('./viewer/viewer_padding.js'), // 여백 패널 window 함수(뷰어 오버레이·설정 탭에서 사용)
  ]);
  viewer.initKeyboardListener();
  return viewer;
});

export async function openReader(...args) {
  const viewer = await loadViewer();
  return viewer.openReader(...args);
}

// 뷰어를 한 번도 안 불러왔으면 열린 뷰어도 없다
export function closeMediaViewer(...args) {
  const viewer = loadViewer.peek();
  return viewer ? viewer.closeMediaViewer(...args) : undefined;
}

// 뷰어를 안 불러왔으면 대기 중인 진행률도 없다
export function flushProgress(useBeacon = false, flushImmediately = false) {
  if (!loadViewer.peek()) return Promise.resolve(null);
  return import('./viewer_progress.js').then((m) => m.flushProgress(useBeacon, flushImmediately));
}
