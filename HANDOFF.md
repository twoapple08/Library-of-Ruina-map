# 인수인계 (HANDOFF)

새 세션은 **이 문서와 `PLAN.md`를 먼저 읽고** 이어서 작업한다.
마지막 갱신: 2026-10-11 (기반 조사 완료, 코드 작성 전).

## 0. 사용자와 일하는 방식

- 사용자는 **폰으로만 작업**한다 (안드로이드). 컴퓨터는 켜둘 수 없고, PC 맵 테스트는 **다른 사람(테스터)**이 한다.
- 토큰 절약을 원한다. 폰으로 할 수 있는 일은 사용자에게 단계별로 맡긴다.
- 결과 확인은 폰으로 볼 수 있는 **미리보기 이미지(위에서 본 모습, 단면)**를 레포에 올려서 받는다.
- 설정은 사용자도 잘 모른다고 함 → 설정 관련은 나무위키를 직접 확인하고, 사용자의 추측은 검증 후 반영.
- 한국어로 소통.

## 1. 현재 상태

- [x] 설계 확정 (PLAN.md)
- [x] 최신 버전·월드 형식·데이터팩 형식 조사 (아래 2절)
- [ ] 코드 없음. 레포에는 `reference/` 이미지와 문서만 있음
- 다음: 4절 "다음 할 일"의 Phase 0

## 2. 조사 결과 (2026-10-11, minecraft.wiki 기준)

### 버전
- 최신 정식: **26.3 "Wilderness Bound"** (2026-09-15). **DataVersion 5023**, 데이터팩 형식 **121.0**, 리소스팩 97.1.
- 이전: 26.2 (DV 4903, 팩 107.1), 26.1 (DV 4786, 팩 101.1). 26.4는 2026년 4분기 예정.
- 26.4 예정 변경 (주의): 청크 `Status`→`status`, 섹션 바이옴 data 64개→4096개.
- 26.x 서버/클라이언트는 **Java 25 필요할 가능성 높음 (미확인)**. Actions에서는 Temurin 25 사용.

### 세이브 폴더 구조 (26.1부터 바뀜)
- 루트: `level.dat`, `players/`(data, stats, advancements), `datapacks/`
- `data/minecraft/`: `game_rules.dat`, `world_clocks.dat`, `world_gen_settings.dat`, `scoreboard.dat`, `weather.dat` 등 (예전엔 level.dat 안에 있던 것들)
- 차원별: `dimensions/<ns>/<path>/{region,entities,poi,data}/`
  - 오버월드도 `dimensions/minecraft/overworld/region/` (예전 루트 `region/` 아님)
- level.dat 변경: `Player`→`singleplayer_uuid`, 난이도는 `difficulty_settings{difficulty(문자열),hardcore,locked}`, `spawn{dimension,pos,yaw,pitch}`, `version_history` 추가(26.3)
- `world_gen_settings.dat` 등의 **정확한 NBT 구조는 문서에 없음** → level.dat을 직접 만들지 말고 **실제 서버가 월드를 생성하게 할 것** (3절)

### 청크 NBT (1.18+ 형식, 26.3에서도 동일한 것으로 추정)
- 루트: `DataVersion`(Int), `xPos`/`zPos`(Int, 절대 청크좌표), `yPos`(Int, 최하단 섹션 Y), `Status`(String `"minecraft:full"`), `LastUpdate`(Long), `InhabitedTime`(Long), `sections`(List), `block_entities`(List), `Heightmaps`(Compound), `structures`, `isLightOn`(Byte)
- 섹션: `Y`(Byte), `block_states{palette:[{Name, Properties}], data:LongArray}`, `biomes{palette:[String], data:LongArray}`, `BlockLight`/`SkyLight`(2048 bytes, 생략 가능)
- 팔레트 패킹: 비트 수 = max(4, ceil(log2(팔레트 크기))). **인덱스는 long 경계를 넘지 않음**(남는 비트 버림). 순서 `index = y*256 + z*16 + x`. 팔레트 1개면 data 생략.
- 바이옴: 4×4×4 = 64개, 최소 비트 제한 없음(1개면 data 생략).
- 하이트맵: 생략 시 로드할 때 재계산될 것으로 예상 (**미검증**)
- `isLightOn: 0B` → 로드 시 조명 재계산 기대 (**미검증**, 문서에 언급 없음)
- 리전 파일 `.mca`: 4KiB 섹터, 헤더(오프셋 테이블 + 타임스탬프), 청크마다 [길이 4바이트][압축 타입 1바이트(2=zlib)][데이터]
- 섹션이 없는 Y는 공기로 처리됨. 바이옴이 없는 섹션은 기본 바이옴(plains일 가능성)이 들어갈 수 있으니, **구역 범위 안의 청크는 모든 섹션에 바이옴 팔레트를 써줄 것** (block_states는 air 하나만)

### 데이터팩 (26.x)
- 폴더 이름 단수: `function/`, `tags/function/`, `dimension/`, `dimension_type/`, `worldgen/biome/`, `world_clock/`, `timeline/`
- `pack.mcmeta` (형식 추정, **검증 필요**):
  ```json
  {"pack": {"description": "Ruina Library", "min_format": [121, 0], "max_format": [121, 0]}}
  ```
- load/tick: `data/minecraft/tags/function/load.json`, `tick.json`

### dimension_type (26.x 필드)
`coordinate_scale, has_skylight, has_ceiling, has_ender_dragon_fight, ambient_light, has_fixed_time(Boolean), monster_spawn_block_light_limit, monster_spawn_light_level, logical_height, min_y(16배수, -2032~2031), height(16배수, 16~4064, min_y+height-1 ≤ 2031), infiniburn, skybox("overworld"/"end"/"none"), cardinal_light("default"/"nether"), attributes{}, default_clock, timelines`
- `effects` 삭제됨 (→ skybox, cardinal_light), `fixed_time`(Int) → `has_fixed_time`(Boolean)
- 높이 확장은 별도 데이터팩 없이 **dimension_type의 min_y/height로 해결**

### 환경 속성 (environment attributes) — 층별 하늘의 핵심
- dimension_type `attributes`에 넣으면 그 차원 전체에 적용. 우선순위: 차원 < 바이옴 < 타임라인 < 날씨.
- 시각 속성 (`minecraft:visual/...`): `sky_color`, `fog_color`(RGB "#RRGGBB"), `fog_start_distance`, `fog_end_distance`, `sky_fog_end_distance`, `cloud_color`(ARGB), `cloud_height`, `sky_light_color`, `sky_light_factor`, `sun_angle`, `moon_angle`, `star_angle`, `star_brightness`, `moon_phase`(override 전용: `waxing_crescent` 등 8종, overworld 스카이박스에서만), `sunrise_sunset_color`, `ambient_light_color`, `water_fog_color`, `ambient_particles`
- **바이옴이 차원 값을 덮어씀** → 바닐라 바이옴(the_void 등)은 자체 시각 속성이 있을 수 있으므로 **시각 속성이 없는 커스텀 바이옴**을 써야 차원 설정이 먹힌다.
- 아이디어: `default_clock` 없이 attributes로 sun/moon 각도·별 밝기·달 위상을 고정하면 **시계 없이 정적인 밤하늘**을 층마다 다르게 만들 수 있음 (미검증).

### 커스텀 바이옴 (최소 형식, 미검증)
```json
{"has_precipitation": false, "temperature": 0.5, "downfall": 0.0,
 "effects": {"water_color": 4159204}, "carvers": [], "features": []}
```
- 1.21.11에서 effects의 sky/fog 색 등은 삭제되고 `attributes`로 이동. 26.3 snap4에서 `spawners`, `spawn_costs`, `creature_spawn_probability` 삭제.

### 차원 정의 (void, 미검증)
`data/ruina/dimension/<id>.json`
```json
{"type": "ruina:<id>", "generator": {"type": "minecraft:flat", "settings": {
  "biome": "ruina:<id>", "layers": [{"block": "minecraft:air", "height": 1}],
  "features": false, "lakes": false, "structure_overrides": []}}}
```

### 시간
- 26.1부터 시간은 **월드 시계(world clock)** 기반. 시계 정의: `data/<ns>/world_clock/<id>.json` = `{}` (추가 시 재시작 필요, /reload 안 됨). 기본 시계: `minecraft:overworld`, `minecraft:the_end`.
- `/time [of <clock>] (add|set|pause|resume|rate|query) ...`, 시간 마커: `day`(1000), `noon`, `night`(13000), `midnight`(18000). 기본 시계가 없는 차원에서 `of` 없이 쓰면 오류.

### 게임룰 (1.21.11부터 snake_case)
`advance_time, advance_weather, spawn_mobs, random_tick_speed, fire_spread_radius_around_player(0=끔), keep_inventory, command_block_output, show_advancement_messages, respawn_radius, mob_griefing, spawn_patrols, spawn_wandering_traders, entity_drops, block_drops, fall_damage, send_command_feedback, water_source_conversion, lava_source_conversion`
- 관상용 기본값 제안: `advance_time false, advance_weather false, spawn_mobs false, spawn_patrols false, spawn_wandering_traders false, random_tick_speed 0, fire_spread_radius_around_player 0, mob_griefing false`

## 3. 기술 방식 (결정)

### 3-1. 공간마다 별도 차원 (사용자에게 아직 확인 안 함 — 진행 전 한 줄로 알릴 것)
- 이유: 사용자가 원한 "층별로 다른 시간·하늘"은 한 차원 안에서는 불가능. 차원을 나누면 층별 하늘색·안개·달·별·높이를 각각 설정할 수 있고, 구역 사이가 사실상 무한히 떨어져서 "아주 크게 떨어뜨리기" 요구도 충족.
- 차원 ID 안: `ruina:exterior, ruina:lobby, ruina:history, ruina:technology, ruina:literature, ruina:art, ruina:natural_science, ruina:language, ruina:social_science, ruina:philosophy, ruina:religion, ruina:general`
- 모든 차원 높이 공통 제안: `min_y -64, height 640` (최대 Y 575). 층별로 바꿔도 됨.
- 오버월드는 사용하지 않고, load 함수에서 처음 접속한 플레이어를 `ruina:exterior` 정문 앞으로 보냄.
- **리스크**: Iris/BSL이 커스텀 차원과 attributes로 만든 하늘을 어떻게 그리는지 모름 → 테스터 확인 1순위. 안 되면 한 차원 + 좌표 분리(구역 간 10,000칸 이상)로 대체.

### 3-2. 월드 생성 파이프라인
- **Claude 작업 환경에서는 Mojang 서버(piston-meta.mojang.com)가 막혀 있음** → 서버 jar로 검증 불가. **GitHub Actions에서는 인터넷이 됨** → Actions에서 실제 서버를 돌린다.
- 흐름 (`.github/workflows/build.yml`, workflow_dispatch + 관련 경로 push):
  1. Temurin 25 + Python 설정
  2. version_manifest_v2.json에서 최신 release 서버 jar 다운로드 (jar는 재배포 금지라 아티팩트에 넣지 말 것)
  3. `eula=true`, `server.properties`(level-type `minecraft:flat`, 빈 void 설정, online-mode는 무관) 작성, 데이터팩을 `world/datapacks/`에 복사
  4. 서버 1차 실행 → "Done" 후 `stop` → **실제 26.3 level.dat·폴더 구조 확보**
  5. 파이썬 생성기가 `world/dimensions/ruina/<id>/region/*.mca` 작성
  6. 서버 2차 실행: 검증 함수(`execute in ... if block ...` 결과를 로그로 출력)로 블록이 제대로 읽히는지 확인, 로그에서 청크/데이터팩 오류 검사 → 실패 시 워크플로 실패
  7. `session.lock` 빼고 zip → 아티팩트 + Releases 업로드 (공간별 zip 분리, 2GB 제한 대비)
  8. 처음 한 번은 **포맷 프로브**: 서버가 직접 만든 청크(.mca)와 level.dat을 아티팩트로 올려서 실제 NBT 구조를 확인하고 생성기와 비교
- 미리보기 PNG(위에서 본 모습, 단면)는 생성기 데이터로 렌더링해서 `previews/`에 커밋 → 사용자가 폰으로 확인.

### 3-3. 생성기 구조 (제안)
- `tools/nbt.py` 최소 NBT 쓰기/읽기 (외부 의존성 없이)
- `tools/region.py` .mca 쓰기
- `tools/world.py` 공간별 희소 블록 저장소(청크 섹션 단위 numpy 배열 + 팔레트), 블록엔티티
- `builders/<공간>.py` 공간별 생성 코드, `config.py`에 PLAN.md 수치(스케일, 구역 크기, 차원 높이)
- `datapack/` 소스 (차원, 바이옴, load/tick, TP 함수)
- `tools/preview.py` 미리보기 렌더러

### 3-4. GitHub 접근 (Claude 세션 기준)
- 레포는 세션에 push 권한으로 연결됨. `gh auth status`는 "invalid"로 나오지만 **`gh api`는 프록시 덕분에 동작함** (repos API 확인됨). 워크플로 실행·로그·아티팩트도 `gh api`로 다루면 됨.
- 사용자가 Actions 허용 + Workflow permissions "Read and write" 설정 완료.
- 워크플로 파일 push가 권한(workflow scope) 때문에 거부되면, 파일 내용을 사용자에게 주고 GitHub 앱에서 붙여넣게 한다.

## 4. 다음 할 일

### Phase 0: 기반 (노력 높게 권장)
1. `tools/` NBT·리전·월드 모듈 작성 + 로컬 단위 테스트 (자기 자신이 쓴 .mca를 다시 읽어 비교)
2. 데이터팩 생성 (차원 12개, 바이옴, pack.mcmeta, load 함수: 게임룰·스폰·TP)
3. `build.yml` 작성 (포맷 프로브 포함) → 실행 → 로그로 데이터팩 오류, 청크 로드 확인 → 수정 반복
4. 스모크 테스트 월드: `ruina:exterior`에 작은 받침대와 TP 엔티티, `ruina:lobby`에 작은 방. 서버 검증 통과 확인
5. `TESTING.md` 작성 (테스터용): 설치 목록, 월드 넣는 법, 확인 항목, 보고 양식
6. 테스터에게 스모크 월드 확인 요청: ① 월드가 열리는지 ② TP 동작 ③ BSL이 커스텀 차원·하늘색·초승달을 어떻게 그리는지 ④ 조명이 제대로 계산됐는지 ⑤ 프레임
### Phase 1~: PLAN.md 3절 순서대로 (외부 → 로비 → 역사 → … → 총류)

## 5. 테스터 설치 목록 (TESTING.md 초안 재료)
1. 마인크래프트 Java 최신 정식 (26.3)
2. Fabric Loader + Fabric API
3. Sodium, Iris (26.3 지원 버전)
4. 선택: Lithium, FerriteCore, ImmediatelyFast, Distant Horizons
5. BSL Shaders 최신판 → `shaderpacks`
6. Releases의 월드 zip → `saves`에 압축 해제
(정확한 모드 버전 링크는 작성 시점에 확인)

## 6. 미해결 질문 / 리스크
- 차원 분리 방식에 대한 사용자 동의 (3-1)
- Iris/BSL + 커스텀 차원/attributes 하늘 호환 (테스터 확인)
- 26.3 pack.mcmeta 정확한 형식, 커스텀 바이옴·차원 JSON 유효성 (Actions 로그로 확인)
- 하이트맵 생략·`isLightOn 0` 재조명이 26.3에서 동작하는지 (포맷 프로브 + 테스터)
- 층별 시간·하늘 값은 각 층 착수 시 원화 보고 결정해서 PLAN.md 7절에 기록
