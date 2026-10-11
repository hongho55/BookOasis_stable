# CHANGELOG
## v2.9.1
- (improvement) 쓰기 API가 실패하면 서버 로그(logs/media_server.log)에 [API-FAIL]로 한 줄 기록 | log failed write API requests to the server log (logs/media_server.log) as [API-FAIL]
- (fix) 오디오북·영상 표지를 바꿔도(정보 수정, 같은 이름의 파일로 교체) 옛 표지가 계속 보이던 이슈 수정 | fix audiobook/video covers still showing the old image after a change (info edit, or replacing the file under the same name)
- (fix) 오디오북 정보 수정에서 표지를 함께 올리면 실패하던 이슈 수정, 수정은 그 책에만 적용되고 재스캔이 덮어쓰지 않음(잠금 해제 가능) | fix audiobook info edits failing when a cover was uploaded; edits now apply only to that book and survive rescans (unlockable)
- (fix) 알라딘 샘플 플러그인의 메타데이터 적용이 항상 실패하던 이슈 수정, 실패 시 서버 로그에 원인 기록 | fix the Aladin sample plugin always failing to apply metadata, and log the cause on failure

## v2.9.0
- (improvement) 오디오북 하위 폴더 음원이 한 권으로 합쳐지거나 저장에 실패하면 알림센터에 표시 | show audiobooks merged with their subfolders, and audiobook save failures, in the notification center
- (perf) 원격 드라이브 오디오북 스캔이 오디오 파일을 내려받지 않음 (재생 시간은 재생할 때 채움) | remote-drive audiobook scans no longer download audio files (track lengths are filled in on playback)
- (feat) 오디오북 metadata.json의 내장 표지 사용, cp949·UTF-16 파일 지원, 깨진 경우 audio.json으로 폴백 | use the embedded cover in audiobook metadata.json, read cp949/UTF-16 files, and fall back to audio.json when it is broken
- (fix) 안드로이드 크롬에서 책을 보다 앱을 내린 사이 크롬이 정리(프로세스 종료)되면, 돌아왔을 때 읽던 책이 자동으로 다시 열리지 않던 이슈 수정 - 열린 책 정보를 탭의 방문 기록에 저장 | fix the book not reopening automatically on Android Chrome when Chrome was killed while the app was in the background - the open book is now kept in the tab's history entry
