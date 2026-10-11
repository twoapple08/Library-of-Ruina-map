# 인수인계 (HANDOFF)

새 세션은 **이 문서 → `docs/test/README.md`(최근 테스트 원문) + `docs/test/*.jpg` 스크린샷 4장을 직접 열어 보기 → `PLAN.md` → `design/exterior.md` → `TESTING.md`** 순서로 확인하고 이어서 작업한다.
마지막 갱신: 2026-10-11 (Phase 1 외부 1차 완성 → 테스터 피드백 받음, 수정 작업 대기).

## 0. 사용자와 일하는 방식

- 사용자는 **폰으로만 작업** (안드로이드). PC 테스트는 **다른 사람(테스터, RTX 4060)**이 한다. 사용자가 결과·스크린샷을 전달해 줌.
- **토큰 절약**이 최우선. 폰으로 할 수 있는 일(전달·결정·의견)은 사용자에게 맡기고, 답변은 짧게.
- 사용자가 **"아직 하지 말것/시작하지 말것"**이라고 하면 분석·답변만 하고 작업하지 않는다. "일시정지"하라고 하면 멈춘다.
- 노력 수준: 사용자가 설정함. 추천은 **high** (판단 필요한 설계), 단순 수정은 medium. 컨텍스트가 길어지면 HANDOFF 갱신 후 새 세션 권장.
- 결과 확인은 `previews/`의 PNG (폰). **원화와 나란히 놓은 비교 그림**이 가장 효과적이었다 (`exterior_compare_*.png`).
- **커밋은 main에 바로** (사용자 허락). 지정 브랜치 `ccr-5178f5de-wc6oox`도 `git push origin main:ccr-5178f5de-wc6oox`로 맞춰 둠.
- 사용자는 기술 설정을 잘 모름 → 직접 검증해서 결정하고, 결정이 필요한 것만 짧게 질문(추천안 포함).
- 한국어로 소통. 테스트용 임시 월드는 "임시"라고 분명히 말할 것 (사용자가 스모크 월드를 완성본으로 오해한 적 있음).

## 1. 현재 상태 (2026-10-11 끝)

### 완료
- Phase 0: NBT·리전·월드 모듈, 데이터팩 생성기, 서버 하네스, CI 월드 빌드(실제 26.3 서버로 검증), 릴리스 자동 업로드
- 기반: 곡면 도형 엔진(`tools/shapes.py`), 입체 렌더러(`render3d.py`), **원근 렌더러(`render_persp.py`)**, 블록 품질 검사(`lint.py`), 성능(리전 병렬 쓰기)
- **Phase 1 외부 1차 완성** (현재 릴리스 `world-latest`, 8.6MB, CI 검증 블록 973/973·TP·조명 통과)
  - 탑: 숯색·청회색, 11단, 창, 좁은 빛나는 문, 가는 마디 가지 40개+갈래+소용돌이, 수관 9개, 뿌리, 꼭대기 신호기 빛기둥
  - 주변: 분화구(계단식 단 7개 RINGS/TOPS, 단 위 도시, 밝은 옹벽), 나선 구름(열 단위 채움, 반지름 400~760, y≈250),
    북동쪽 고리 구조물+검은 기둥, 정문 양옆 황금 종이 물결 2줄기, 날리는 종이 파티클
  - TP: 정문 홈 걷기 → 로비(임시 책장 방), 로비 남쪽 문 → 정문 계단 앞. 스폰 (0.5, 0, 100.5)
  - 공간별 시계 12개 (`ruina:<id>`, 138000틱에 멈춤)
- 원화 참고: `reference/도서관 외견.png`(지상 구도), `reference/도서관 위치 전경.png`(사용자 추가, 위에서 본 분화구)

### Phase 1 테스터 결과 (2026-10-11, 스크린샷 `docs/test/phase1_1~4.jpg`)
| # | 결과 |
|---|---|
| ① 월드 열림 | O |
| ② 처음 위치 | 0, 0, 100 (정상) |
| ③ 하늘 | 쉐이더 끔: 보라·달·별 O / **BSL: 여전히 저녁노을색**, "월드 자체에 시간을 변경할 수 없음" |
| ④ TP | **정문→로비 X**, 로비→정문 O |
| ⑤⑦ 스크린샷 | 탑·분화구·구름 첨부 (`docs/test/`) |
| ⑥ 빛기둥 | O (신호기) |
| ⑧ 종이 | O |
| ⑨ fps | 쉐이더 끔 300 / 켬 200 (RTX 4060) |
| ⑩ 이상한 곳 | **건물이 무너진 것처럼 보임, 창문이 아니라 천장(지붕 테두리)이 빛남** |

### 사용자 피드백 (다음 작업 요구사항)
1. 도서관 바깥은 잘 구현됨 → **디테일 더 깎기**
2. 바닥 종이 물결은 위치 전경 원화를 보면 **7줄기** (방사형) → 7개로
3. 빛기둥은 신호기가 아니라 **건축물**로
4. **배경 건물 밀도 증가**
5. 색감 문제 → 해결책으로 **텍스처팩**, 쉐이더 수정, 모드 제작까지 고려 가능 (바닐라·데이터팩으로 안 되면 다른 기능도 OK)
6. 반투명이어야 하는 부분(구름 등)은 **스테인드글라스** 등 활용 (또는 모드로 블록 자체 제작)
7. 위치 전경 원화를 보고 **탑 높이와 계단식 도시 높이를 수학적으로 맞출 것** (지금은 탑 혼자 기둥처럼 높음)
8. **탑 윗부분**은 위치 전경 원화를 참고해 수정
9. (지난번 Phase 0 ⑦ `/function ruina:setup` 실패 메시지는 아직 못 받음)

### 원인 분석 (작업 전 추정, 검증 필요)
- **BSL 노을**: BSL/Iris는 공간 시계가 아니라 기본(오버월드) 시계 시각을 읽는 듯. 대안 순서:
  ① 우리 차원 `default_clock`을 `minecraft:overworld`로 하고 오버월드 시계를 자정(18000+위상)에 고정 (`time of minecraft:overworld set/pause`)
  ② 그래도 안 되면 BSL 설정(시간 고정 옵션) 또는 텍스처팩/쉐이더 수정 검토.
  테스터 말 "시간 변경 불가" = 우리 공간 시계가 멈춰 있고 `/time`이 기본 시계(오버월드)에만 작동하기 때문일 수 있음.
- **정문 TP 실패**: 로비→정문은 되므로 tick 함수는 동작. 정문 걷기 구역 `(-6, 6, 35)~(6, 9, 36)`이 실제 바닥 높이·홈 위치와 어긋난 것으로 추정.
  기단 나팔 확장(body_radius y<16에서 +8×K)·계단 플랫폼(y 0~5, z 32~37)·홈(z 34부터) 실제 블록을 `d.get`으로 확인하고 구역 조정.
  CI 검증은 마커를 구역 가운데 소환해서 통과했으므로, 플레이어가 **실제로 걸어서 닿을 수 있는지**(바닥 높이, 막힌 블록)를 확인해야 함.
- **건물 무너짐·천장 발광**: `builders/city.py` `_facade`가 창을 무작위로 뚫어 벽이 깨져 보이고, 네온 지붕 테두리(발광 블록)가 천장처럼 빛남.
  → 창은 층마다 가지런한 격자(창틀 포함), 불 켜진 창만 발광, 지붕 테두리 발광 제거/절제.
- **탑 혼자 높음**: 탑 330(+수관 ~420) vs 단 최고 194+건물 70. 위치 전경 원화에서 탑:분화구 지름:단 높이 비율을 재서 RINGS/TOPS·탑 높이 재조정.

## 2. 확인된 사실 (26.3, 포맷 프로브·서버 로그로 검증)

### 버전·환경
- 26.3: DataVersion **5023**, 데이터팩 형식 **121.0**, **Java 25** (version.json `java_version: 25`)
- 서버 jar(`META-INF/versions/26.3/server-26.3.jar`) 안에 바닐라 데이터팩 JSON이 그대로 있음 → `ref/vanilla/`에 추출해 둠
- 26.3용 Iris(1.11.6+)·Sodium(0.9.2+) 출시됨 (2026-10 웹 검색)

### 세이브 구조 (서버가 실제로 만든 것)
- `level.dat`: `Data{GameType(Int), allowCommands(Byte), spawn{pos[I;x,y,z], yaw, pitch, dimension}, difficulty_settings{difficulty:"peaceful",...}, DataPacks{Enabled,Disabled}, version_history, DataVersion, ...}`
  - 서버가 만든 월드는 `allowCommands 0` → 빌드 후처리에서 1로 바꿈. `GameType 1`(크리에이티브)
  - **월드 스폰을 커스텀 차원에 둘 수 있음**: `execute in ruina:exterior run setworldspawn ...` → `spawn.dimension = "ruina:exterior"`
- `data/minecraft/game_rules.dat`: `data{"minecraft:advance_time": 0b, ...}` — 게임룰 ID는 `minecraft:` 네임스페이스 snake_case. 전체 목록은 `ref/registries.json`의 `minecraft:game_rule`
- 차원 폴더: `dimensions/<ns>/<id>/{region,entities,poi,data}/`

### 청크 NBT (가장 중요)
- 루트: `DataVersion, xPos, zPos, yPos, Status:"minecraft:full", LastUpdate, InhabitedTime, isLightOn, sections, block_entities, Heightmaps, fluid_ticks, block_ticks, PostProcessing(섹션 수만큼 빈 리스트), structures{References,starts}`
- **블록 팔레트 항목 = either(블록 ID 문자열, `{id, properties}`)**
  - 예전 `{Name, Properties}`는 **안 읽힘** ("No key id")
  - 문자열은 속성 없는 기본 상태만 (`"minecraft:oak_stairs[facing=east]"` 같은 문자열은 오류)
  - 문자열과 Compound가 섞이면 문자열을 `{"": "minecraft:air"}`로 감쌈 (26.x NBT의 섞인 리스트 규칙)
- 바이옴 팔레트: 문자열 리스트 `["ruina:lobby"]`. 청크를 쓸 땐 모든 섹션에 바이옴을 써야 함(없으면 plains)
- `Heightmaps: {}`(비움) → 로드 시 재계산됨 (검증됨)
- `isLightOn: 0b` + 빛 배열 없음 → **로드 시 조명 재계산됨** (랜턴 옆 블록 빛 14 확인)
- 블록 엔티티: `{id, x, y, z, keepPacked, components{}, Items:[{Slot:0b, id, count:Int}]}` (조각된 책장 책 3권 검증)
- 엔티티 파일(`entities/r.x.z.mca`): `{Position:[I;cx,cz], DataVersion, Entities:[...]}` — 엔티티는 직접 쓰지 않고 **서버에서 summon** 시켜 저장

### 데이터팩
- `pack.mcmeta`: `{"pack": {"description", "min_format": [121,0], "max_format": [121,0]}}` — 동작함 (값은 version.json에서 자동)
- 폴더 이름 단수(`function/`, `dimension/`, `dimension_type/`, `worldgen/biome/`) — 동작함
- 차원: flat 생성기 `{"biome", "layers": [], "features": false, "lakes": false, "structure_overrides": []}` — 동작함
- 차원 타입: **바닐라 overworld.json을 복사해서** `default_clock`·`timelines` 제거, 높이·attributes 덮어씀 (`tools/datapack.py`)
- 바이옴: 바닐라 the_void.json 복사 → `features: []`, 시각 속성 제거 (바닐라 the_void에 `visual/sky_color`가 있어서 차원 하늘을 덮어씀)

### 하늘·시간 (환경 속성)
- 속성 전체 목록: `ref/registries.json` → `minecraft:environment_attribute` (예: `visual/block_light_tint`, `visual/ambient_particles`도 있음)
- 바닐라 낮/밤은 `timeline/day.json`이 시계(`world_clock`)에 맞춰 속성을 바꾸는 방식. 한밤중(18000) 값: `sun_angle 180`, `moon_angle 0`(머리 위), `star_angle 180`, `star_brightness 0.5`, `sky_light_factor 0.24`, `sky_light_color #7a7aff`, `gameplay/sky_light_level 0.2667`, 하늘·안개색에 검정 곱함
- 우리 방식: **시계·타임라인 없이 차원 attributes에 밤 값을 고정** (`config.night_sky()`). 외관 = 보라 하늘 `#3b2370` + `moon_phase "waxing_crescent"` + `moon_angle 35`
  - 서버에서는 오류 없음. **클라이언트·BSL에서 실제로 어떻게 보이는지는 테스터 확인 필요**
- `/time query daytime` → 오류 (26.3에서 문법이 바뀜. 필요하면 `/time` 도움말 확인)

### CI·GitHub 접근 (이 작업 환경 기준)
- 작업 환경에서는 Mojang·minecraft.wiki·나무위키 접속 불가. **GitHub Actions에서는 Mojang 접속 가능**
- `gh api`의 runs 조회는 되지만 일부 Actions 경로·아티팩트 다운로드(blob 저장소)는 막힘 → **결과는 CI가 `ci-output` 브랜치에 push**, `git fetch origin ci-output`으로 읽음
- 실패 로그: GitHub MCP `get_job_logs(run_id, failed_only=true)`
- 워크플로 실행: MCP `actions_run_trigger(run_workflow, build.yml, inputs {task: world|probe})`, 또는 관련 경로 push 시 자동
- 릴리스 다운로드(`release-assets.githubusercontent.com`)는 작업 환경에서도 됨

## 3. 코드 구조

```
config.py               공간 목록·크기·높이·하늘(night_sky)·게임룰 (수치는 PLAN.md 근거)
build.py                로컬: python build.py previews | datapack | check
builders/__init__.py    Build(차원별 블록 저장소, TP 연결, 서버 검증 목록 자동 생성)
builders/smoke.py       Phase 0 스모크 월드 (임시 — Phase 1~2에서 exterior.py/lobby.py로 교체)
builders/previews.py    공간별 미리보기 목록
tools/nbt.py            NBT 읽기/쓰기 (+ to_snbt 덤프)
tools/region.py         .mca 읽기/쓰기 (255섹터 초과 시 .mcc)
tools/world.py          Dimension: set/fill/place(numpy 배열)/place_mask, 블록 이름 검사(ref/blocks.json), 청크 NBT
tools/datapack.py       차원·차원타입·바이옴·함수(TP, setup, 엔티티 소환) 생성
tools/preview.py        위에서 본 모습(높이 음영)·입면·단면 PNG (색: ref/block_colors.json)
tools/shapes.py         도형 엔진: Box/Sphere/Revolve(회전체)/Tube(관) 부품, Union(|)/Subtract(-)/Displace,
                        carve(dim, 도형, shell, smooth) — 껍질만 블록화 + 계단·반블록 다듬기, 칠하기(paint) 함수
tools/render3d.py       입체 미리보기: iso_panel(dim, Palette(), 제목, view='se'|'sw'|'nw'|'ne'|'front', lod, box)
builders/exterior.py    외부: 탑(몸통·창·문·가지·뿌리)·광장·계단·종이 물결 + TP/스폰. build(b, city, clouds)
builders/crater.py      분화구: 단(terraces)·옹벽·단 위 도시·구름(clouds, 열 단위)·고리 구조물·빛기둥(light_beam)
builders/city.py        빌딩 생성기 (겉껍질, 창, 네온, 안테나) — crater가 단마다 호출
tools/render_persp.py   원근 미리보기 (사람 눈높이, 원화 비교용). 카메라를 단 안쪽(r 135 이상, 낮은 y)에 두지 말 것
tools/lint.py           블록 품질 검사 (python build.py check)
design/exterior.md      외부 원화 분석·제안 수치·재질 후보
tools/server.py         서버 jar 다운로드, 콘솔 명령 하네스
tools/ci.py             CI 단계: fetch, refs, reports, colors, probe, world
tools/build_world.py    CI 월드 빌드: 1차 실행 → 청크 쓰기 → 2차 실행 검증 → level.dat 수정 → zip
tests/test_tools.py     python -m unittest discover -s tests
ref/                    26.3 서버에서 뽑은 참고 자료 (blocks.json=블록·속성, registries.json, block_colors.json, vanilla/)
previews/               미리보기 PNG (폰 확인용)
.github/workflows/build.yml
```

- TP: 빌더에서 `b.links.anchor(이름, 차원, x,y,z, yaw)` / `b.links.portal(차원, x,y,z, 목적지, width, height)`
  → 데이터팩 `ruina:tp/to/<이름>`, `ruina:tp/clicked`(상호작용 엔티티 우클릭/좌클릭 처리), `ruina:build/entities`(CI가 실행해 엔티티 소환)
- 처음 접속: 월드 스폰이 `b.links.spawn` 앵커 (커스텀 차원). 혹시 오버월드에 나타나면 tick의 `first_join`이 TP
- 게임룰: `ruina:setup` (CI 2차 실행에서 한 번 적용. 테스터도 다시 실행 가능)
- 서버 검증: `Build.block_checks()`(차원마다 청크 4개×블록 24개 무작위 + 블록 엔티티), `light_checks()`, `extra_checks`

## 4. 다음 할 일 (우선순위)

1. **버그**: 정문 TP 구역 수정 (실제 블록 확인), BSL 노을 → 기본 시계 방식으로 바꾸고 CI로 `time` 명령 결과 확인
2. **비율**: 위치 전경 원화 픽셀 측정 → 탑 높이 / 분화구 지름 / 단 높이 비율 계산 → `crater.RINGS/TOPS`, `exterior.TOP` 등 조정.
   원근 렌더러로 원화와 같은 카메라 구도 비교 그림을 만들어 수치 검증
3. **탑 윗부분**: 위치 전경 원화(꼭대기 가지가 넓게 퍼지는 모양) 참고해 수관·가지 재설계
4. **빛기둥 건축물**: 신호기 대신 탑 꼭대기에서 하늘로 솟는 발광 기둥 구조 (발광 블록 심 + 노랑·흰 스테인드글라스 겹, 위로 갈수록 가늘게). 신호기는 제거 또는 보조
5. **종이 물결 7줄기**: 탑 둘레 방사형 (정문 양옆 2줄기 포함), 위치 전경 원화처럼 단 쪽으로 흘러감
6. **도시**: 밀도 증가, 창 격자 정돈, 지붕 발광 제거
7. **구름**: 스테인드글라스(흰·연회색) 섞어 반투명감, 블록 덩어리감 줄이기
8. **색감**: 월드에 텍스처팩 넣기 검토 (`resources.zip`을 월드 폴더에 넣으면 싱글플레이에서 자동 적용 제안됨 — 검증 필요).
   구름·종이·탑 판자 색을 맞춤 텍스처로. 모드 제작은 마지막 수단
9. 반영 후 CI 빌드 → `previews/` 비교 그림 갱신 → TESTING.md 체크리스트 갱신 → 사용자에게 테스트 요청
10. 그다음 Phase 2: 로비 (`reference/로비.png`)

### 작업 팁 (이번 세션에서 배운 것)
- 전체 외부 빌드 ≈ 80초(로컬). 탑만 다시 만들고 주변만 바꿔 볼 때는 `exterior.build(b, city=False, clouds=False)` 결과를 pickle로 캐시해 두고 crater 함수만 다시 실행하면 빠름
- 원근 렌더 카메라를 **단 안쪽(반지름 135 이상, 단 높이 아래)**에 두면 단 내부(빈 공간)가 찍힘 → 광장(반지름 < 108) 위나 높은 곳에 둘 것
- `d.place` 배열 축 순서는 **[x, y, z]** (구름에서 [x, z, y]로 넣었다가 가로줄 버그)
- 구름을 SDF carve로 만들면 8분 → 열 단위 직접 채우기로 6초
- 서버 로그 "Can't keep up!"은 무해 (CI 검사에서 제외함)
- 품질 검사 `python build.py check`, 미리보기 `python build.py previews` (약 2분), 테스트 `python -m unittest discover -s tests`
- CI 실행: main에 builders/·tools/·config.py·ref/ 변경 push 시 자동. 결과는 `git fetch origin ci-output` → `world/SUMMARY.md`, `world/report.json`
- 대기: `/tmp/claude-0/waitrun.sh <run_id>` 같은 gh api 폴링 스크립트 (세션마다 새로 만들어야 함)

## 5. 미해결 질문 / 리스크
- Iris/BSL + 커스텀 차원/attributes 하늘 호환 (테스터 ③)
- 큰 공간 성능 측정 (2026-10-11): 3072×3072 바닥+기둥+벽 = 섹션 5.6만 개, 메모리 약 0.5GB, 리전 쓰기 4코어 3.8초 → 현재 구조로 충분
  - 도형 엔진 carve는 아직 단일 프로세스 (외부 시제품 23초). 필요하면 섹션 단위 병렬화
- 릴리스 zip 2GB 제한 → 공간별 zip 분리 필요할 수 있음
- 배경음악·환경음 (사용자 결정 미정)
- 분화구가 커서 렌더 거리 24청크 이상 필요. Distant Horizons 호환은 아직 미확인
- 테스터 화면에서 날리는 잎 파티클이 크게 보임(근접) — 확률·종류 조정 여지
