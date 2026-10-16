# CHANGELOG
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
