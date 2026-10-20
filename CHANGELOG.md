# CHANGELOG
## v2.9.8
- (fix) 폴더 단위 스캔(scan-path)에서 사라진 파일의 휴지통 이동·복구가 저장되지 않아 이름이 바뀐 파일의 이전 도서가 목록에 남던 문제 수정 | fix folder scans (scan-path) not saving trash moves and restores, which left the old entry of a renamed file in the list
- (fix) 리버스 프록시 뒤에서 카테고리 삭제가 타임아웃(504)으로 실패하던 문제 수정 — 카테고리는 바로 목록에서 빠지고 도서 정보는 스캔 대기열의 '카테고리 삭제' 작업이 나눠 지움(재시작 시 이어서 진행), 삭제 실패 시 HTTP 상태를 표시 | fix category deletion timing out (504) behind a reverse proxy — the category leaves the list immediately and its books are removed in batches by a 'Category Delete' task in the scan queue (resumed after a restart); on failure, the HTTP status is shown
- (fix) 카테고리를 일반↔성인 보관함으로 이동하면 '이동할 카테고리 정보가 없습니다'로 실패하던 문제 수정(1.8.9부터 사이드바 순서 저장과 주소가 겹쳤음) — 이동도 스캔 대기열의 '카테고리 이동' 작업이 나눠 처리(끝나면 대상 보관함에 나타남, 재시작 시 이어서 진행), 미분류로 들어가고 두 DB 스키마가 달라도 있는 컬럼만 옮김, EPUB 책갈피·주석·KOReader 동기화도 함께 옮기며 컬렉션에서는 빠지고 미리 만든 TTS 음성은 지워짐 | fix moving a category between the general and adult libraries failing with "no category to move" (its URL collided with sidebar reordering since 1.8.9) — moves now run in batches as a 'Category Move' task in the scan queue (the category appears in the target library when done; resumed after a restart), land ungrouped, copy only columns present in both databases, and carry EPUB bookmarks, annotations and KOReader sync; the books leave their collections and pre-generated TTS audio is removed
- (fix) 카테고리 추가·수정·이동이나 설정 저장 뒤 재시작 전까지 Redis 읽기 진행률 저장·구글 드라이브 보기 캐시 정리·음악 정보 조회 예약 작업이 멈추던 문제 수정 | fix the scheduled Redis reading-progress save, Google Drive view-cache cleanup and music info lookup stopping until restart after adding, editing or moving a category or saving settings
- (fix) 카테고리 삭제 시 EPUB 책갈피·주석·컬렉션 항목·KOReader 동기화·미리 만든 TTS 음성이 남던 문제 수정 | fix deleting a category leaving EPUB bookmarks, annotations, collection items, KOReader sync entries and pre-generated TTS audio behind
- (fix) 카테고리 삭제 시 번호가 비슷한 다른 카테고리(예: 1번 삭제 시 11·21번)의 스캔 기록까지 지워지던 문제 수정 | fix deleting a category also wiping the scan history of other categories with similar IDs (e.g. 11 and 21 when deleting 1)

## v2.9.7
- (fix) 서버 응답이 느릴 때 스캔 상태 조회가 쌓여 화면이 멈추던 문제 수정 | fix scan status polls piling up and stalling the page when the server responds slowly
- (fix) 일반·성인 카테고리 번호가 같으면 스캔 에러 리포트가 서로 섞여 보이던 문제 수정(이전 리포트는 표시되지 않고 다음 스캔부터 분리 저장) | fix scan error reports of general and adult categories with the same ID showing up in each other's viewer (older reports are no longer listed; reports are kept separately from the next scan)
- (improvement) 필터 적용 중 표시줄이 스크롤해도 상단에 따라다니도록 변경 | the active filter bar now stays pinned at the top while scrolling

## v2.9.6
- (removed) 알라딘 Open API 지원 종료에 따라 알라딘 샘플 플러그인(aladin, aladin_new)과 코어의 알라딘 기본값을 삭제 — 기본 메타데이터 공급자 자동 선택·다른 플러그인으로의 자동 대체가 없어지고(.env METADATA_PROVIDER 지정 시만), 플러그인용 window.triggerSearchAladinMetadataAction 별칭과 적용 API의 aladin_item 필드도 제거 | removed the Aladin sample plugins (aladin, aladin_new) and Aladin defaults in core as the Aladin Open API was discontinued — no automatic default metadata provider or silent fallback to another plugin anymore (only when METADATA_PROVIDER is set in .env); the window.triggerSearchAladinMetadataAction alias and the aladin_item field of the apply API were also removed
- (fix) 연속 스캔 등으로 다른 탭을 보는 사이 뜬 마지막 토스트가 돌아와도 사라지지 않던 문제 수정, 토스트가 튕기지 않고 부드럽게 나타나도록 변경 | fix the last toast (e.g. after back-to-back scans) never disappearing when it appeared while the tab was in the background, and make toasts ease in smoothly instead of bouncing
- (fix) 검색용 메타데이터 플러그인이 없을 때 검색 창에 가짜 기본 항목 대신 설치 안내를 표시 | the metadata search dialog now shows an install hint instead of a fake default entry when no search plugin is installed
- (fix) DB 연결이 예외로 반납되지 못하면 슬롯이 영구히 빠지던 문제를 MariaDB에서도 자동 회수하도록 수정(전에는 SQLite만), 남아 있던 반납 누락 가능 지점 58곳을 정리 | fix DB connections that failed to return to the pool on an exception: leaked slots are now reclaimed on MariaDB too (previously SQLite only), and the remaining 58 spots that could skip returning a connection were cleaned up
- (improvement) 오디오북 표지를 처음 볼 때가 아니라 스캔할 때 만들도록 변경(metadata.json 내장 표지·폴더 이미지, 원격 음악의 곡 내장 아트는 지금처럼 처음 볼 때) — 기존 오디오북은 카테고리 강제 재스캔 시 생성 | audiobook covers are now generated during scan instead of on first view (metadata.json embedded covers and folder images; embedded song art on remote music still on first view) — existing audiobooks get covers on a forced rescan

## v2.9.5
- (plugin) 커뮤니티 별점 1.1.0: 별점 결과 5분 캐시, 별점 서버 실패 시 2분간 재호출 안 함, 조회 동시 요청·제한 시간 3초, relay 주소를 바꾸면 인증을 다시 하도록 수정 | community rating 1.1.0: cache ratings for 5 minutes, skip the rating server for 2 minutes after a failure, query in parallel with a 3s timeout, and re-verify when the relay URL changes
- (feature) 진단용 느린 요청·서버 오류 기록 추가(.env DEBUG_REQUEST_LOG=true일 때만, 기본 꺼짐) — logs/request_debug.log, 요약 도구 tools/summarize_request_debug_log.py와 MCP get_request_debug_summary | add an opt-in diagnostic log of slow requests and server errors (only when DEBUG_REQUEST_LOG=true in .env, off by default) — logs/request_debug.log, with a summary tool (tools/summarize_request_debug_log.py) and the MCP tool get_request_debug_summary
- (improvement) 사이드바 가상 그룹 이름을 카테고리와 같은 크기로 맞추고 굵기로 구분, 관리 도구 항목은 차분한 색으로 | sidebar virtual group names now match the category size and stand out by weight; admin tool items use a muted color
- (improvement) 작가별 보기에서 표시할 도서가 없을 때 '도서가 없다' 대신 이유를 알려주고 기본 보기로 바로 전환하는 버튼 표시 | when the by-author view has nothing to show, explain why instead of saying there are no books, with a button to switch back to the default view
- (improvement) 작가별 보기가 켜져 있으면 상단 토글에 '작가별' 글자를 함께 표시 | show the 'By author' label on the top bar toggle while the by-author view is on
- (performance) 앱 글꼴을 조각 92개에서 완성형 한글 2,350자를 담은 파일 하나(475KB)로 바꿔, 한 번만 받고 글꼴이 바뀌며 화면을 다시 그리지 않도록 함 | replace the 92-piece app font with a single file covering the 2,350 common Hangul syllables (475KB), downloaded once and without re-drawing the screen when it loads
- (performance) 글꼴·라이브러리 파일이 1년 캐시 설정에도 매번 서버에 재확인하던 문제 수정 | fix fonts and library files being re-checked with the server on every visit despite their one-year cache setting
- (performance) 앱 스크립트를 버전이 들어간 주소로 불러와 재방문 때 다시 받거나 확인하지 않도록 함 | load app scripts from versioned URLs so revisits no longer re-download or re-check them
- (performance) 관리자 홈의 플러그인 상태 확인이 매번 모든 플러그인 소스를 다시 검사하던 것을 바뀐 파일만 검사하도록 개선 | the admin home's plugin status check now re-scans only changed plugin files instead of every plugin's source each time
- (performance) PDF 라이브러리는 PDF를 열 때, 압축 라이브러리(JSZip)는 첫 화면 뒤에 불러오도록 변경(플러그인이 쓰는 경우 실행 전에 자동으로 불러옴) | load the PDF library when a PDF is opened and the zip library (JSZip) after the first screen, loading them automatically before any plugin code that uses them
- (performance) 뷰어·상세·설정·플레이어 스크립트를 처음 쓸 때 불러와 홈 화면이 받는 스크립트를 절반 가까이 줄임 | load viewer, detail, settings and player scripts on first use, cutting the scripts the home screen loads nearly in half

## v2.9.4
- (improvement) 앱 화면에 Pretendard 글꼴 적용(기기마다 다른 기본 글꼴 대신), 도서 카드 제목을 덜 굵게 하고 단어 단위로 줄바꿈 | use the bundled Pretendard font across the app (instead of each device's default font), with lighter book card titles that wrap between words
- (improvement) 데스크톱 화면의 바깥 테두리 상자를 없애고, 사이드바 Home 줄의 관리 버튼들을 하단 '관리 도구'로 옮김(모바일과 동일) | remove the outer frame on desktop, and move the admin buttons from the sidebar Home row into the collapsible 'Admin tools' section at the bottom (same as mobile)
- (improvement) 앱 아이콘을 Lucide 선 아이콘으로 통일 (플러그인·카테고리 아이콘의 Font Awesome 값은 그대로 지원) | switch app icons to Lucide line icons (Font Awesome values in plugins and category icons keep working)
- (improvement) 상단바의 기본|작가별을 아이콘으로, 세션 탭은 선택된 세션만 이름을 보이고 나머지는 아이콘으로 표시 | show the top bar's Default|By author toggle as icons, and label only the selected session tab (the others show icons)
- (improvement) 상세 화면 버튼을 절제된 색으로 정리(핵심 동작 하나만 강조색, 나머지는 중립) | tone down the detail page buttons (only the main action uses the accent color; the rest are neutral)
- (improvement) 제목 감추기 카드는 마우스를 올리면 표지 위에 제목 표시, 새 카테고리는 제목 감추기가 기본 | hidden-title cards now show the title over the cover on hover, and new categories hide titles by default
- (improvement) 홈의 최근 읽은 도서·신규 추가 도서를 표지만 보이게 하고, 읽은 정도는 표지 아래 진행 막대로 표시 | the home Recently read and Recently added rows show covers only, with reading progress as a bar at the bottom of the cover
- (feat) 홈 배너 샘플 플러그인(home_banner) 추가 - 홈 맨 위에 그림과 한 줄 문구, 기본 그림은 르누아르(퍼블릭 도메인)이고 그림 주소·문구는 플러그인 설정에서 변경. 사용법: 환경설정 > 플러그인 설정 > 샘플에서 설치 > '홈 배너' → 내 설정 > '홈 화면을 플러그인 배치 모드로 전환' 켜기 → 홈 하단 '+ 위젯 추가'에서 '홈 배너' | add the Home banner sample plugin (home_banner): a picture and a one-line message at the top of home; the default picture is a public-domain Renoir, and the image URL and message can be changed in the plugin settings. To use: Settings > Plugin settings > Install from samples > 'Home banner' → My settings > turn on the plugin layout mode for the home screen → '+ Add widget' at the bottom of home → 'Home banner'
- (plugin) home_widget에 frame:'none' 추가 - 제목줄 없이 내용만 보이는 위젯 | add frame:'none' to home_widget for widgets shown without the title bar
- (fix) 라이트 테마에서 알림 패널과 도서 진단 창의 글자가 보이지 않던 이슈 수정 (테마 색을 따름) | fix unreadable text in the notification panel and book diagnosis dialog on the light theme (they now follow the theme colors)
- (improvement) 도서 정보 수정 화면의 항목 이름·입력칸 색을 차분하게 정리 | calmer label and input colors in the book info editor
- (improvement) 사이드바 BookOasis 로고를 선 아이콘으로 바꾸고 메뉴·상단바와 줄을 맞춤 | sidebar BookOasis logo now uses a line icon and lines up with the menu and top bar
- (fix) 2.8.5부터 Moon+ Reader 등 OPDS 앱에서 도서의 읽기 버튼이 사라지던 이슈 수정 (페이지 스트리밍 정보는 KOReader에만 제공) | fix the read button disappearing in OPDS apps such as Moon+ Reader since 2.8.5 (page-streaming info is now sent to KOReader only)

## v2.9.3
- (fix) 오디오북 metadata.json 내장 표지가 images.poster 키로 지정된 경우 표지가 생성되지 않던 이슈 수정 | fix audiobook covers not being created when metadata.json references its embedded cover via images.poster
- (fix) 오디오북 상세의 '이 시리즈 재스캔'과 도서 메뉴의 '즉시 스캔'이 동작하지 않던 이슈 수정 (해당 오디오북 폴더를 다시 스캔) | fix 'Rescan this series' on audiobook details and 'Scan now' in the audiobook card menu not working (they now rescan that audiobook's folder)

## v2.9.2
- (fix) 오디오북·도서 파일 이름을 바꾸면 이어 듣기·읽기 기록을 잃던 이슈 수정 | fix renamed audiobook/book files losing listening/reading progress
- (fix) 오디오북 폴더 안의 파일 변경(이름 변경, 회차 추가)이 일반 스캔에 반영되지 않던 이슈 수정 | fix file changes inside an audiobook folder (renames, new episodes) not being picked up by normal scans
- (fix) 오디오북 폴더 이름을 바꾸면 새 책으로 중복 등록되던 이슈 수정(같은 책으로 옮겨 이어 듣기 유지, 폴더가 사라진 책은 숨김) | fix renamed audiobook folders being registered as duplicate books (the book moves with its progress; books whose folder disappeared are hidden)

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
