// open_session.js – 열려 있던 뷰어 책 기록 읽기 (부팅 때 뷰어 모듈 전체를 받지 않고 복원 여부만 판단하려고 분리, 2.9.5)
//
// 모바일 OS가 백그라운드 탭을 정리하면 돌아올 때 /#viewer 로 새로 로드되는데, 그동안은 뷰어를
// 복원하지 못하고 목록이 떠서 "읽던 곳으로 못 돌아간다"로 보였다.
// 열린 책은 뷰어 히스토리 항목의 history.state(resume)에 둔다 - 실제 안드로이드 크롬에서 프로세스가
// 종료된 뒤 탭이 복원되면 sessionStorage·window.name은 사라지지만 #viewer 주소와 history.state는
// 남는다(2026-10-11 에뮬레이터 실측 4/4). 탭마다 따로라 여러 탭이 섞이지 않는다.
// sessionStorage는 예전 동작 호환용 보조 기록으로만 남긴다.
export const OPEN_VIEWER_SESSION_KEY = 'bookoasis_open_viewer';

export function readOpenViewerSession() {
  try {
    const fromHistory = history.state && history.state.view === 'viewer' ? history.state.resume : null;
    if (fromHistory && fromHistory.bookId) return fromHistory;
  } catch (e) {}
  try {
    const entry = JSON.parse(sessionStorage.getItem(OPEN_VIEWER_SESSION_KEY) || 'null');
    return entry && entry.bookId ? entry : null;
  } catch (e) {
    return null;
  }
}
