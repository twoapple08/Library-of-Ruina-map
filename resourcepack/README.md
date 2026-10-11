# 리소스팩 (텍스처팩) 원본

나중에 월드 폴더의 `resources.zip`으로 묶어 넣을 리소스팩 원본 (HANDOFF 4-1).
`pack.mcmeta`의 형식 번호는 26.3 서버 version.json 의 resource 97.1.

| 소리 이벤트 | 파일 | 쓰임 (사용자 지정, 2026-10-12) |
|---|---|---|
| `ruina:music.lobby_hall` | `assets/ruina/sounds/music/lobby_hall.ogg` (96초, 스테레오) | 로비 홀(밝은 곳) 테마 — Library of Ruina OST "Lobby" |
| `ruina:fragment.switch` | `assets/ruina/sounds/sfx/fragment_switch.ogg` (2.6초, 모노) | 조각을 왼손으로 들 때(F) 공간 전환 소리 |

아직 월드·데이터팩에 연결하지 않음. 연결 방법(다음 단계):
- 로비 홀 바이옴 `ruina:lobby_hall` 의 `minecraft:audio/background_music` 에 `ruina:music.lobby_hall`
- 데이터팩 `fx/switch` 함수에 `playsound ruina:fragment.switch master @s`
- CI가 이 폴더를 `resources.zip`으로 묶어 월드 폴더에 넣기 (싱글플레이에서 적용 여부 확인 필요)
