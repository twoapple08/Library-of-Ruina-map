# 인수인계 (HANDOFF)

새 세션은 **이 문서(특히 4절 맨 위) → `docs/mod/기초구성.md`(모드 구성·요구사항 전부) → `docs/test/README.md`(4차·3차·2차 테스트 원문·원인) → `TESTING.md` → `PLAN.md`** 순서로 확인하고 이어서 작업한다.
마지막 갱신: 2026-10-12 오후 (**① 끝 + Iris·BSL 게임 테스트 + 로컬 테스트·건축물 재사용 + 자유 형체 시험 통과**. 다음 세션 첫 작업 = 4절 맨 위 ② 총류의 층).

## 0. 사용자와 일하는 방식

- 사용자는 **폰으로만 작업** (안드로이드). PC 테스트는 **다른 사람(테스터)**이 한다. 2~4차 테스트 PC는 **GTX1050ti·i7-8700·16GB** (1차는 RTX 4060), 렌더 거리 24. fps는 "이대로 가자"(사용자) 사용자가 결과·스크린샷을 전달해 줌.
- **토큰 절약**이 최우선. 폰으로 할 수 있는 일(전달·결정·의견)은 사용자에게 맡기고, 답변은 짧게.
- 큰 작업 전에는 **계획·질문을 먼저 보여 주고** 사용자가 "시작"이라고 하면 진행 (질문은 추천안과 함께 짧게). 테스트 결과는 `docs/test/`에 원문 보관 + 항목별 원인·수정 표
- 사용자가 **"아직 하지 말것/시작하지 말것"**이라고 하면 분석·답변만 하고 작업하지 않는다. "일시정지"하라고 하면 멈춘다.
- 노력 수준: 사용자가 설정함. 추천은 **high** (판단 필요한 설계), 단순 수정은 medium. 컨텍스트가 길어지면 HANDOFF 갱신 후 새 세션 권장.
- 폰으로 사용자에게 부탁할 수 있는 것 (토큰 절약): CI 스크린샷 확인(`ci-output/mod/sheet.jpg`), 원화 추가(`reference/`),
  환경 네트워크 허용(Fabric·Mojang 도메인 → 여기서 직접 빌드 가능, 아래 2절 CI·GitHub 접근), 결정 질문 답변
- 결과 확인은 `previews/`의 PNG (폰). **원화와 나란히 놓은 비교 그림**이 가장 효과적이었다 (`exterior_compare_*.png`).
- **커밋은 main에 바로** (사용자 허락). 세션마다 지정 브랜치가 다름 → `git push origin main:<지정 브랜치>`로 맞춰 둠.
- 사용자는 기술 설정을 잘 모름 → 직접 검증해서 결정하고, 결정이 필요한 것만 짧게 질문(추천안 포함).
- 한국어로 소통. 테스트용 임시 월드는 "임시"라고 분명히 말할 것 (사용자가 스모크 월드를 완성본으로 오해한 적 있음).

## 1. 현재 상태 (2026-10-11 끝)

### 완료
- Phase 0: NBT·리전·월드 모듈, 데이터팩 생성기, 서버 하네스, CI 월드 빌드(실제 26.3 서버로 검증), 릴리스 자동 업로드
- 기반: 곡면 도형 엔진(`tools/shapes.py`), 입체 렌더러(`render3d.py`), **원근 렌더러(`render_persp.py`)**, 블록 품질 검사(`lint.py`), 성능(리전 병렬 쓰기)
- **Phase 1 외부 1차 완성** (현재 릴리스 `world-latest`, 8.6MB, CI 검증 블록 973/973·TP·조명 통과)
  - 탑: 숯색·청회색, 11단, 창, 좁은 빛나는 문, 가는 마디 가지 40개+갈래+소용돌이, 수관 13개, 뿌리, 꼭대기 빛기둥 건축물 (2차 수정 반영, 4절)
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

### 데이터팩 함정 (2026-10-12 확인)
- **위치 인자(x/y/z/dx/distance)가 붙은 선택자는 실행 차원 안의 엔티티만 찾음**. tick 함수는 오버월드에서 돌므로
  `execute in <차원> as @a[x=..,dx=..]` 로 차원을 맞춰야 함 (마그마크림 전환 실패 원인). 조각 감지는 `fragment.trigger` 사용
- 월드 스폰이 커스텀 차원이면 처음 접속 때 그 자리에 바로 나타남 (보는 방향은 기본값) → `first_join` 에서 항상 스폰 자리로 TP
- 바이옴 `audio/background_music` 의 `sound` 에 우리 소리 **이름 문자열**을 쓰면 데이터팩 로드 실패 (소리 레지스트리에 없음) → `{"sound_id": ...}` 직접 정의
- 차원 타입이 바닐라 overworld 를 복사하면 바닐라 배경음악도 따라옴 → `audio/background_music` 지움, 공간 음악은 바이옴에 (`config.music`)

### BSL (v10.1.6, 사용자 제공 → `shaderpack/`)
- BSL은 `sunAngle`(오버월드 시계)로 낮밤을 정함. 우리는 모두 자정 → 밤빛. 개조: `dimension.properties` 에 새 폴더 `ruina`(world0 + `#define RUINA`),
  RUINA 에서 lightNight·ambientNight 를 `fogColor`(우리 환경 속성 안개색)로, 최소 밝기 ×5, 하늘은 바닐라 경로(skyColor). 외부는 원본(world0)
- 기본값: 그림자 1536/192, BSL 구름 끔. 셰이더 컴파일은 여기서 확인 못 함 → 테스터 확인 필요 (3차 ⑭)

### CI·GitHub 접근 (이 작업 환경 기준)
- **2026-10-12 사용자가 환경 설정 변경: Fabric·Mojang·Modrinth·Adoptium 도메인 허용 + Setup script(Java 25 → `/opt/jdk25`, numpy·pillow)**
  → **여기서 직접 빌드 가능** (확인: `cd mod && JAVA_HOME=/opt/jdk25 PATH=/opt/jdk25/bin:$PATH ./gradlew compileJava compileGametestJava` 46초 성공).
  Maven Central 이 가끔 429 → `mod/settings.gradle` 에 구글 거울 추가, 그래도 나면 한 번 다시 실행. 소프트웨어 GL(mesa)·Xvfb 있음 → **게임 테스트도 여기서 됨** (`tools/local_test.sh`, SDL 은 EGL 로).
  CI(25~40분)는 최종 확인·릴리스용으로만. 아래 줄의 "접속 불가"는 이전 기록
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
builders/smoke.py       Phase 0 스모크 월드 (더 안 씀)
builders/lobby.py       로비: 전환 전 방 + 전환 후 홀, 은조각 F 전환
builders/history.py     역사의 층: 접대 무대(길·난간·진열장)·반복 바닥·배경·유물, 말쿠트 방
builders/fragment.py    조각 F: stage(층 등록: 전경·방 자리 + 전환), finish(층 사슬: 도착 시 조각 교환, 이전/다음 층 조각 F), trigger(감지)
tools/shaderpack.py     맵 전용 BSL 개조 (shaderpack/BSL_v10.1.6.zip → out/release/BSL_v10.1.6_Ruina.zip, CI가 릴리스에 올림)
resourcepack/           리소스팩 원본 (소리) → CI가 월드 폴더 resources.zip 으로
builders/technology.py  기술과학의 층: 고가도로·주탑·네온 도시·톱니·탑, 예소드 방
builders/literature.py  문학의 층: 나무 보도·팔각 아치, 에스컬레이터형 책장, 전구, 나무 탑, 호드 방
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
builders/crater.py      분화구: 단(terraces)·옹벽·단 위 도시·구름(clouds, 열 단위)·고리 구조물·빛기둥 건축물(light_spire)
builders/city.py        빌딩 생성기 (겉껍질, 창, 네온, 안테나) — crater가 단마다 호출
tools/render_persp.py   원근 미리보기 (사람 눈높이, 원화 비교용). 카메라를 단 안쪽(r 135 이상, 낮은 y)에 두지 말 것
                        미리보기 그림은 탑이 어두워 도시와 섞여 보임 — 모양 확인은 render_side 입면도가 더 정확
tools/lint.py           블록 품질 검사 (python build.py check)
design/exterior.md      외부 원화 분석·제안 수치·재질 후보
tools/server.py         서버 jar 다운로드, 콘솔 명령 하네스
tools/ci.py             CI 단계: fetch, refs, reports, colors, probe, world
tools/build_world.py    CI 월드 빌드: 1차 실행 → 청크 쓰기 → 2차 실행 검증 → level.dat 수정 → zip
tests/test_tools.py     python -m unittest discover -s tests
tools/mod_assets.py     모드 아이콘(이름 글자)·아이템 모델·언어 → mod/src/main/resources/assets/ruina (커밋)
tools/world_cache.py    건축물 결과 재사용 (코드 지문 = 릴리스 Ruina_generated.zip 이면 받아 씀)
tools/local_test.sh     작업 환경에서 건축물→모드 빌드→게임 테스트 (bsl: 셰이더 판도)
tools/mod_pack.py       CI: 모드용 데이터팩·소리·items.json·건축물 world.zip → mod/build/generated/ruina
mod/                    Fabric 모드 (build.gradle, src/main/java/ruina/library, src/gametest = CI 게임 테스트)
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

### ▶ 다음 세션 첫 작업: 모드로 전부 다시 만들기 — 외부(도서관 외견·전경)부터 (사용자 지시 2026-10-12 끝)
- **순서 바뀜**: 총류 시험 대신 **외부(도서관 외견·주변 전경) → 로비 → 10개 층(전경·지정사서 방·건축물·소품)** 순서로,
  모든 구성 요소를 모드의 새 요소(자유 형체·모드 블록·원화 투영·움직임)로 **교체하고 채우며 디테일까지**. 아래 ② 계획의 A(자유 형체 기반)·B(원화 투영)를 외부에서 먼저 만들어 모든 공간에 씀
- 원화: `reference/도서관 외견.png`, `도서관 외견 단면도.png`, `도서관 위치 전경.png`, `design/exterior.md`. 지금 외부 빌더 `builders/exterior.py`·`crater.py`·`city.py`
- 공간 하나를 끝낼 때마다: 로컬 스크린샷 ↔ 원화 비교 그림(`previews/`), main push, HANDOFF 갱신. 테스트(사용자·테스터)는 전부 구축 뒤 한 번에
- 컨텍스트가 길어지면 공간 단위로 끊고 HANDOFF 갱신 (다음 인수인계 때 HANDOFF 나누기도)

#### (참고) ② 총류의 층 시험 — 처음 세운 계획. A·B 는 그대로 쓰고, 총류는 순서대로 갈 때 만듦
**요구사항: `docs/mod/기초구성.md`** (맨 아래 "모드화 ① 진행 중 사용자 확인" 포함). 사용자 결정 요약:
- **모드만 mods 에 넣으면 어느 월드(야생)에서든** 도서관. 월드 파일 배포는 끝 (데이터팩 시절 마지막 월드 = 릴리스 `world-datapack-final`)
- 모드 아이템은 **초대장·방전환·세피라 10종 (12개)만**. 예전 조각(철조각 등)은 바닐라 그대로 (기능 없음, 모드 아이템 아님)
- 파일 크기·모드 블록 수 제한 없음, **오직 높은 퀄리티** (GTX1050ti fps 고려: 가까이 정밀, 멀리 단순). **이펙트도 모드 전용**, 최적화 필수
- 모드 업데이트 시 이미 방문한 월드의 도서관 차원도 새 건축물로 교체
- 맵 전용 BSL 도 모드와 호환되게 개조, **빛나는 모드 블록은 BSL 에도 반영**
- **원화를 모드 텍스처로 직접 넣어도 됨** (사용자 "예", 2026-10-12. 공개 배포 때 다시 정함)
- 테스트는 모두 구축한 뒤 한 번에, 아이템 이미지·사운드는 테스트 뒤 마지막에 사용자가 넣음 (지금 것은 임시)
- **HANDOFF 나누기**(짧은 현재판 + 지난 기록 보관판)는 **다음 인수인계 때** 할 것 (사용자 지시, 토큰 절약)
- 노력 수준 추천: 정해진 작업 medium, ② 설계(A·B 기반) high. 외부 토큰 절약 툴(RTK·Headroom 등)은 안 씀 (검토 후 사용자와 합의)

#### ② 총류의 층 시험 — 사용자에게 보여 준 세부 계획 (이대로 진행)
- **A. 자유 형체 기반 (모든 층 공용)**: Python 으로 3D 형체(삼각형)를 만들어 블록 칸 단위로 잘라 모드 리소스에 → "형체 블록" 하나가 자기 칸 조각을
  청크 메시에 구워 그림 (Fabric 렌더러 API `FabricBlockStateModel.emitQuads`, 매 프레임 비용 없음, Sodium·BSL 그대로). 가까이 정밀·먼 배경 단순판.
  걷는 바닥·충돌은 블록, 보이는 모습은 형체로 덮음
- **B. 원화 투영**: 도착 시점 카메라(위치·시야각)를 원화 구도에 맞추는 도구 → 그 시점에서 원화를 형체 표면에 비춰 입힘. 가려진 곳·뒷면은 직접 만든 텍스처(책등, 돌판)
- **C. 전경**: 가장자리 책 층 다리(위 잿빛 돌판), 책 더미 피라미드, 비틀린 책탑 12, 빌딩만 한 책장 벽(뒤 빛), 어두운 물, 떨어지는 종이(움직임). 빛 = 빛나는 모드 블록(BSL 반영)
- **D. 지정사서 방**: 높이 트인 밝은 공간, 책장 벽 앞 촉수처럼 비틀린 책탑, 뒤 빛, 잿빛 안개 (원화 `reference/총류의 층 지정사서 방.png`)
- **E. 확인**: 로컬 게임 테스트로 도착 시점 스크린샷 ↔ 원화 나란히 비교 그림 (BSL 켠 것·끈 것)
- **걸리는 점 확인 끝 (2026-10-12)**: 시험 블록 `ruina-test:mesh_probe`(게임 테스트 모드 `MeshProbe`·`MeshProbeModel`, 칸 밖으로 뻗는 비틀린 띠)가
  바닐라(Indigo)와 Sodium+Iris+BSL 양쪽에서 제대로 그려짐 (BSL 그림자까지). → A 방식 그대로 가능.
  구현 참고: `ModelLoadingPlugin.register(ctx -> ctx.modifyBlockModelAfterBake()...)` 로 모델 감싸기, `BlockStateModel` 3 메서드(collectParts·particleMaterial·materialFlags) + `emitQuads`
  (`emitter.pos/uv` → `materialBake(sprite, BAKE_NORMALIZED)` → `emit()`). 26.3 패키지: `net.minecraft.client.renderer.block.dispatch.BlockStateModel`,
  `client.renderer.block.BlockAndTintGetter`, `client.resources.model.sprite.Material`. 이름 찾기는 `javap -cp ~/.gradle/caches/fabric-loom/26.3/minecraft-merged.jar`
- **사용자 지시 (2026-10-12 끝)**: "3D 느낌과 원화 느낌을 살려서 일단 만들고, 테스트는 나중에". 모드 크기·모드 블록 가짓수 상관없음.
  → 도착 시점은 원화 그대로(투영), 걸어 다니면 입체(직접 만든 형체·텍스처로 보완). 로컬 스크린샷·원화 비교 그림으로만 조정하고 사용자 테스트는 전부 구축 뒤
- 사용자가 고해상도 원화·다른 각도 그림을 `reference/` 에 넣어 줄 수 있음 (요청해 둠) → 시작 전에 `reference/` 새 파일 확인

#### 이번 세션(2026-10-12 오후)에서 한 것 — 0·1 단계 끝
- **0. 지난 커밋(티페리트 F 삭제) 확인**: 로컬 게임 테스트 바닐라 26/26 통과 (방전환 11곳·세피라 10종·초대장 왕복)
- **1. 게임 테스트에 Iris 1.11.7 + Sodium 0.9.2 + 맵 전용 BSL** (`-Pshaders`, Modrinth maven, 모드 jar 에는 안 들어감):
  셰이더 켠 순회(외부·로비 홀·역사·철학·총류 전경·총류 방, 스크린샷 `bsl_*`, `sheet_bsl.jpg`) 통과. **셰이더 컴파일 오류 없음**
  (`Using shaderpack: BSL_v10.1.6_Ruina.zip`). 경고 1: `shaders.properties` 메뉴 항목 `SKY_VANILLA` 를 못 찾음 (메뉴 표시만, 무해 — 고칠 때 tools/shaderpack.py)
  - 게임 테스트는 **시작할 때 실행 폴더(build/run/clientGameTest)를 비움** → 셰이더 팩·Iris 설정은 테스트 모드 `ShaderSetup`(preLaunch)이
    `-Druina.shaderpack` 경로에서 넣음. 바닐라 판 결과는 셰이더 판 전에 `build/vanilla/` 로 옮김 (CI·로컬 같음)
- **로컬 게임 테스트 가능**: `bash tools/local_test.sh [bsl|build]` → `ci_out/mod/`. 이 환경 Xvfb 는 GLX 창을 못 만듦 → `SDL_VIDEO_FORCE_EGL=1`(스크립트에 들어 있음).
  바닐라 약 17분, BSL 은 장소당 5~6분 (llvmpipe). 결과 그림은 사용자에게 `SendUserFile` 로 보냄
- **건축물 재사용** `tools/world_cache.py`: 월드에 영향 주는 코드 지문이 릴리스 `Ruina_generated.zip` 과 같으면 받아 씀 (월드 빌드 12분 → 수십 초). CI 도 같음.
  건축물 코드(builders/·config.py·tools 빌드 코드·ref/·resourcepack/)를 바꾸면 그때만 새로 빌드
- 월드 빌드 서버: 감시견 끔(`max-tick-time -1`, 느린 환경에서 save-all 60초 초과로 서버가 죽었음), Mojang 인증 서버 연결 경고 무시
- CI 는 이번 main push 로 한 번 돌아감 (건축물 새로 빌드 → 릴리스에 Ruina_generated.zip 첫 업로드). 결과 확인은 사용자가 폰으로 `ci-output/mod/sheet*.jpg`

#### ① 에서 만든 것 (2026-10-12)
- `mod/` Fabric 26.3 모드 (Loom 1.18, loader 0.19.5, fabric-api 0.162.0+26.3 — `FabricMC/fabric-example-mod` 26.3 브랜치 기준)
  - `RuinaMod` 아이템 등록(목록은 jar 안 `/ruina/items.json` ← `tools/mod_pack.py` ← `config.MOD_ITEMS`), 크리에이티브 탭 '도서관'
  - `Library` 아이템 동작 (티페리트는 다른 세피라와 같음, F 기능 없음): 초대장(야생→`tp/fade/exterior_spawn`, 자리 기록 = 플레이어 attachment `ruina:return_point` / 도서관 안→기록한 자리, 없으면 월드 스폰),
    방전환(`ruina:mod/room` = 차원별 `<key>/switch`), 세피라(`tp/fade/<층>_entrance`), 도서관에서 죽으면 `tp/to/exterior_spawn`
  - `WorldInstaller` 서버 시작 때 `/ruina/world.zip`(CI 가 검증한 차원별 region·entities)을 `<월드>/dimensions/ruina/` 로, `ruina_build.txt` 의 빌드 번호가 다르면 교체
  - `Fx`·`FxPayload`·`client/FxOverlay` 모드 전용 화면 이펙트 (잉크빛 암전·층 이름 카드·번쩍임), 데이터팩 명령 `ruina fx <fade_in|fade_out|flash|title 글자>`
  - 데이터팩은 모드 jar 의 data/ (항상 켜짐). `datapack.write(mod=True)`: 모드 전용 함수(`mod/room` 등) 포함, `setup`·`build/entities` 제외, 어둠 효과 → `ruina fx`
- 데이터팩 정리: 조각 F·층 사슬·교환·자동 지급·야간투시·first_join·데이터팩 리스폰 삭제, **도서관 시계 `ruina:library`**(오버월드 시계 안 건드림), 암흑 1초 → 이동 → 1초 뒤 풀림(`FADE_IN 20`, `FADE_MIN 40`)
- 아이콘: `python -m tools.mod_assets` → `mod/src/main/resources/assets/ruina/` (커밋됨), 미리보기 `previews/mod_items.png`
- CI(`build.yml`): 월드 빌드(바닐라 서버 검증, 그대로) → `mod_pack` → `./gradlew build` → **`runClientGameTest`**(xvfb, 실제 클라이언트:
  새 야생 월드에서 아이템을 진짜 우클릭 → 차원·위치 확인 → 도착 화면 스크린샷 1280×720) → 릴리스 `Ruina.jar` + `fabric-api-*.jar`.
  결과: `ci-output` 브랜치 `mod/` (SUMMARY.md, sheet.jpg 모음, 장별 jpg, gradle.log, problems.log). 게임 테스트는 `continue-on-error` (실패해도 모드는 올림)
- BSL(`tools/shaderpack.py`): 오버월드 = 원본, 외부 = `ruina_ext`(원본 + 밤 고정), 로비·층 = `ruina`(원화 색 빛 + 밤 고정).
  밤 고정 = timeAngle·timeBrightness·shadowFade·worldTime 을 자정 상수로 (`RUINA_NIGHT_LOCK`). `config.MOD_BLOCKS` 의 glow → block.properties 발광(block.150XX)

#### CI 게임 테스트 결과 (2026-10-12)
- 초대장(야생→외부→처음 자리), 방전환 11곳, 세피라 10종 모두 통과. 실행 약 15분 (청크 그리기 대기 30초, 렌더 거리 10. 3분이면 1시간 17분)
- **티페리트 F·청록 돔은 지금 만들지 않음 (사용자 결정)** — 빌드·데이터팩·모드·테스트에서 뺌 (`natural_science.TEAL`·`VARIANT_DX` 색표만 남김).
  나중에 만들 때 알아둘 것: 게임 테스트의 가상 F 키는 처리 안 됨(서버에서 왼손으로 옮겨 시험), 데이터팩 tick 감지는 손만 돌아오고 전환 안 됨
  (같은 함수를 execute as/at 으로 직접 실행하면 됨) → 모드 Java 에서 왼손 감지 후 직접 실행할 것
- 같은 상대 위치 판정(`fragment.relative`)은 머리 칸 공기 + 발밑이 공기가 아님 (반블록 위에서 발 칸이 늘 막힘이던 문제)
- 스크린샷은 HUD 숨김(`RuinaTestClient.clean`, `HudElementRegistry.replaceElement`)·빈손. 26.3 에는 `options.hideGui` 없음, F1 가상 입력도 안 먹음
- 결과: `ci-output` 브랜치 `mod/` — `sheet.jpg`(전체 모음), `NN_<공간>.jpg`, `SUMMARY.md`(✅/❌ + 실패 원인 기록), `gradle.log`
- ALSA·SoundSystem 오류 줄은 CI 에 소리 장치가 없어서 (무해)

### 데이터팩 단계에서 끝난 것 (2026-10-12)
- 2~4차 테스트 반영: 조각 F 층 사슬(`fragment.stage/finish`, 왼손에 **새로 들어온 순간에만** 발동, 즉시 오른손으로), 걷기 층 이동 삭제(조형물 유지),
  어둠 효과 암전, 외부 도착·리스폰 시 조각 정리, 스폰 방향, 빛 블록(`builders/lighting.py`), 차원 기본 밝기 0.1, 빛기둥(발광 기둥만, 외부 높이 1024),
  로비 홀 음악·전환 소리(바이옴 음악 `{sound_id}`), 리소스팩 따로(`Ruina_resources.zip`), **맵 전용 BSL**(`tools/shaderpack.py`, `ruina` 폴더)
- 사용자 제공 ogg 에 영상(Theora) 스트림이 섞여 소리가 안 났음 → 소리만 남김. **앞으로 받는 소리 파일도 `ffprobe` 로 확인**
- 릴리스 world-latest: `Library-of-Ruina.zip`(월드), `BSL_v10.1.6_Ruina.zip`, `Ruina_resources.zip` (CI가 main push 때 갱신)

### 2차 수정 완료 (2026-10-11) — 테스트 대기 (TESTING.md 3절)
1. ✅ **BSL 노을**: 모든 차원 `default_clock = minecraft:overworld`, 오버월드 시계를 138000(자정)에 멈춤
   (`datapack.CLOCK`, `config.CLOCK_TIME`, 공간별 world_clock 파일 없앰). CI가 차원마다 `time query time` 결과를 확인
   → 테스터가 BSL에서 밤인지 확인 필요. 안 되면 BSL 설정·텍스처팩/쉐이더 수정 검토
   **정문 TP**: 구역을 홈 바닥 전체(문 앞 z 39~42, y 5~9)로 넓힘 + `gate_walkable`(빌드 때 발밑·머리 공간 확인)
2. ✅ **비율**: 위치 전경 원화 측정 (탑 아래 반지름 R 기준: 몸통 ≈ 7.5R, 수관 꼭대기 ≈ 11R, 수관 반지름 ≈ 4R).
   탑 자체 비율은 원화와 비슷했고 원화는 분화구가 탑에 비해 훨씬 넓음(렌더 거리 때문에 넓힐 수 없음) →
   사용자와 정한 절충: 탑 몸통 330→285, 바깥 단 194→214 (그릇 모양 `TOPS`), 구름 y 250→318 (빌딩 꼭대기 위)
   **탑 모양**: 아래가 굵고 위로 좁게 (R 40 → 22, `TAPER` 1.35), 기단 나팔 8, 계단은 기단을 파낸 통로 앞에서 시작 (`STAIR_Z`)
3. ✅ **수관**: 13개, 꼭대기 4~22칸 아래에서 위·바깥으로 꽃병처럼 (반지름 ≈ 150~195, 갈래 2~4개씩 끝이 말림)
4. ✅ **빛기둥 건축물** (`crater.light_spire`): 신호기 제거. 발광 블록 심(겉 한 겹) + 노란·흰 스테인드글라스 겹(사이 빈칸),
   흰 유리 반지름 15→6으로 가늘어지며 하늘 끝(y 575)까지, 24칸마다 금 테, 받침은 검은 갈비살 8개 + 금 고리
5. ✅ **종이 물결 7줄기**: 정문 양옆 2 + 54°마다 5 (`STREAM_ANGLES`), 첫 옹벽 앞(r 132)까지. 뿌리는 줄기 사이에 2개씩
6. ✅ **도시**: 간격 46→32 (약 2배), 빌딩마다 같은 창 격자(`city.Style`), 불 켜짐은 층 단위로 뭉침, 모서리·옥상 난간 테,
   지붕 테두리 네온 제거. 옹벽 창도 (구간, 층) 단위로 정돈
7. ✅ **구름**: 반두께 < 4인 가장자리를 흰/연회색 스테인드글라스로 (`CLOUD_GLASS_T`)

### Phase 2 로비 1차 (2026-10-12) — 테스트 대기 (TESTING.md ⑬~⑱)
- 사용자 결정: 정문 → **암전** → 로비 청크가 서버에 불러와지면(`if loaded`, 최소 1초) 암전 해제 + **'로비'** 글자.
  효과음·음악은 모든 맵 완성 후. 로비에 오면 **은조각**(철 조각 + custom_data `ruina:{silver:1b}`, 이름·모양·소리는 나중에) 1개 지급.
  은조각을 들고 **F(왼손)** → 번쩍 → **전환 전 방 ↔ 전환 후 홀** (왕복, 같은 상대 위치, 막히면 기본 자리). 나가는 문은 방에만.
  다른 층으로 가는 TP는 만들지 않음 (원화에 없는 건 만들지 않기). 은조각은 나중에 역사의 층으로 가면 회수
- 참고 자료: `reference/로비 전경 (전환 후).jpg`(사용자 제공), `reference/로비_3D/`(공식 3D 영상 프레임 01~07 방, 08~19 홀,
  story_* 공식 스토리 전환 장면). 웹 검색으로는 공식 로비 이미지를 못 찾음 (wiki.gg 접속 불가)
- 크기: 사람 기준 1블록 ≈ 1m (3D 영상 19번: 사람 키 ≈ 흰 계단 2.4단), 책상 높이 1 = 앉은 캐릭터
- 코드: `builders/lobby.py` (방 x -11..11, z -17..17 / 홀 = 방 + (512, 0, 0), 바이옴 `ruina:lobby_hall`로 밝은 안개),
  `tools/datapack.py` 암전 TP (`Walk.fade`, `Anchor.title/on_arrive`, `tp/fade_tick`), `Links.functions/tick/scores`(빌더 함수),
  `Dimension.set_biome`(청크별 바이옴), `config.Space.biomes`(추가 바이옴). `builders/smoke.py`의 임시 로비는 더 안 씀
- 미리보기 `previews/lobby_*.png`. CI가 암전 TP·방↔홀 전환·바이옴을 마커로 검사

### Phase 3 역사의 층 1차 (2026-10-12) — 테스트 대기 (TESTING.md ⑲~㉕)
- 사용자 결정: 로비 홀 흰 대계단 꼭대기 빛 → 암전 → '역사의 층' (은조각 회수, 금조각 지급). 돌아갈 땐 도착 자리 뒤 내려가는 계단 빛 →
  로비 계단 위 ('로비', 금조각 회수). 금조각 F: 접대 공간 ↔ 말쿠트 방 (고정 자리)
- 크기 (처음 정한 층별 크기 1536×400 유지, 사용자 첨부 '층 내부 크기 정리' 참고): 3겹
  ① 접대 무대 500×250 (길 여러 줄, 난간 8칸·진열장 5칸 간격 — 원화는 평평한 바닥을 살짝 위에서 내려다본 원근)
  ② 130~370: 아래로 반복되는 바닥 4겹(24칸 간격, 겹마다 16칸 넓어짐, 보이는 테두리만) + 책장 절벽, 책장 기둥 줄, 유물 셋
  ③ 600~720: 구역 끝 큰 책장 벽 (DH/렌더 거리 48+ 에서 보임 — 테스트 ㉔)
- 최적화: 겉면만, 아래 겹은 테두리만, 진열장 속 책(item_display)은 도착 자리 둘레 277개만. 블록 약 408만, 숨은 블록 0.3%
- 코드: `builders/history.py`, 조각 공용 `builders/fragment.py` (은조각·금조각, `F.setup`), `Links.entity_cmds`, `Build.forceload`

### 기술과학의 층 1차 (2026-10-12) — 테스트 대기 (TESTING.md ㉖~㉚)
- 사용자 결정: 층 연결 = **지정사서 방 원화 속 빛나는 출구 → 다음 층**, 돌아가는 길은 각 층 도착 자리 뒤.
  말쿠트 방 금빛 틈 → 기술과학의 층 (다리 서쪽 끝 → 말쿠트 방 틈 앞). 예소드 방 유리문은 다음 층(문학) 입구 예정 (아직 TP 없음).
  조각: 기술과학의 층은 **철괴**(iron_ingot, 이름 '철괴'). 도착하면 다른 조각 회수 (`fragment.exchange`). 톱니 회전은 이번엔 고정
- 크기 2048×512: 고가도로 680×21 (서 있는 Y 250), 주탑 4개(높이 120)·처진 쇠사슬·사선 쇠사슬, 트러스 교각,
  네온 도시(바닥 Y 40, 가까운 329채 꼭대기 Y 190~370, 먼 150채), 무지개빛 길, 녹슨 톱니 6개, 가장 높은 건물(Y 490)과 케이블
- 블록 약 790만 (가장 무거움, fps 확인 ㉚). `city.build_city(palette=...)`로 층마다 빌딩 모습 (외부는 그대로 — 확률 0이면 난수 안 씀)
- 코드: `builders/technology.py`

### 문학의 층 1차 (2026-10-12) — 테스트 대기 (TESTING.md ㉛~㉟)
- 연결: 예소드 방 유리문 → 문학의 층 (보도 서쪽 끝 → 유리문 앞). 호드 방 팔각 문틀 복도 끝은 다음 층(예술) 입구 예정 (아직 TP 없음)
- 조각: **구리 주괴** (copper_ingot, '구리 주괴'). 에스컬레이터형 책장은 고정 (사용자 결정)
- 크기 1536×400: 나무 보도 400×17 (Y 150) + 팔각 아치 고가, 에스컬레이터형 책장 90줄(+먼 40줄), 나무 탑 8개(+먼 10개),
  매달린 전구 600 (랜턴 78%, 큰 물방울 전구 15%, 상자 등불 7%), 블록 빛 색 주홍 (`visual/block_light_tint`)
- 블록 약 141만, 숨은 블록 2%. 코드: `builders/literature.py`

### 예술 ~ 총류의 층 1차 (2026-10-12) — 테스트 대기 (TESTING.md ㊱~㊸)
- 사용자 지시: 추천안대로 총류까지 한 번에. 조각(지정사서 방 열쇠)은 층 순서대로 철조각(로비), 금조각, 철괴, 금괴, 철발판, 금발판,
  철블럭, 금블럭, 모루, 황금사과 → 총류는 **마법이 부여된 황금사과** (사용자 확정).
  자연과학의 층 색감 전환 = **마그마크림** (사용자 지시는 '지정사서방'이지만 색 바뀐 원화가 접대 공간(돔)이라 돔에 적용 — 사용자 확인 필요)
- 층 연결: 각 지정사서 방 원화 속 빛나는 출구 → 다음 층 (`fragment.door`), 각 층 도착 자리 뒤쪽 끝 → 이전 층 방 출구 앞 (`fragment.floor`).
  자리 이름 = 층 이름 (`<층>_entrance`, `<층>_room`, `<층>_door`). 마지막 총류 방은 출구 없음
- 층별 요점: 예술(쓰러진 나무줄기·실제 물·눈 셋 괴생물체·블록 디스플레이 정령 20), 자연과학(돔 두 벌: 금빛/청록 — 마그마크림 상대 위치 전환),
  언어(실제 용암 바다·쇳물 국자), 사회과학(물 대신 푸른 안개·폐차/물고기 디스플레이), 철학(은하수 = 빛 블록 6000·도시 야경),
  종교(시계 판 7+먼 8·진자·방 나선계단 꼭대기가 총류 입구), 총류(책더미 다리·비틀린 책탑·책장 빌딩, 방은 사용자 제공 원화)
- 전체 블록 약 4200만, 로컬 빌드 162초. 코드: `builders/{art,natural_science,language,social_science,philosophy,religion,general}.py`,
  층 공통 `fragment.floor/door`, 미리보기는 각 모듈 `PREVIEW` 목록 → `previews.render_floor`

### 남은 일
8. **색감**: 월드 폴더에 `resources.zip` 넣는 방식으로 텍스처팩 (사용자 결정: 이 방식, 모드 제작은 최종 단계).
   구름·종이·탑 판자 색 맞춤 텍스처. 싱글플레이에서 자동 적용 제안이 뜨는지 검증 필요
9. 2차 테스트 결과 반영 (특히 BSL 밤 여부, 정문 TP)
10. 테스트 결과 반영 (외부·로비·10개 층) → 색감 텍스처팩 → 효과음·음악 (모든 맵 완성 후, 사용자 결정)

### 작업 팁 (이번 세션에서 배운 것)
- 전체 외부 빌드 ≈ 135초(로컬, 2차 수정 후). 탑만 다시 만들고 주변만 바꿔 볼 때는 `exterior.build(b, city=False, clouds=False)` 결과를 pickle로 캐시해 두고 crater 함수만 다시 실행하면 빠름
- 원근 렌더 카메라를 **단 안쪽(반지름 135 이상, 단 높이 아래)**에 두면 단 내부(빈 공간)가 찍힘 → 광장(반지름 < 108) 위나 높은 곳에 둘 것
- `d.place` 배열 축 순서는 **[x, y, z]** (구름에서 [x, z, y]로 넣었다가 가로줄 버그)
- 구름을 SDF carve로 만들면 8분 → 열 단위 직접 채우기로 6초
- 서버 로그 "Can't keep up!"은 무해 (CI 검사에서 제외함)
- 품질 검사 `python build.py check`, 미리보기 `python build.py previews` (약 2분), 테스트 `python -m unittest discover -s tests`
- CI 실행: main에 builders/·tools/·config.py·ref/·mod/ 변경 push 시 자동 (약 25~40분). 이전 실행이 쓸모없으면 `gh api -X POST .../actions/runs/<id>/cancel`.
  CI 로그는 `gh api .../jobs/<id>/logs` 가 막힘 → MCP `get_job_logs(job_id, return_content, tail_lines)` (크면 파일로 저장됨 → grep). 결과는 `git fetch origin ci-output` → `world/SUMMARY.md`, `world/report.json`
- 대기: `/tmp/claude-0/waitrun.sh <run_id>` 같은 gh api 폴링 스크립트 (세션마다 새로 만들어야 함)

## 4-1. 최종 목표 (사용자 계획, 2026-10-12 — 대략적인 방향만)

> ⚠️ **구색을 다 갖춘 뒤에도 모드 제작(3번)으로 바로 넘어가지 말 것.** 그 단계에서 사용자에게 먼저 묻고 지시를 받은 뒤 진행.

1. 맵(외부·로비·10개 층)의 구색을 먼저 다 갖춘다
2. **텍스처팩(리소스팩)**: 사운드(효과음·배경음악), 아이템 이미지(조각 10종 + 마그마크림 등), 블록 텍스처(구름·종이·탑 판자·전구 등)
3. 최종적으로 **마인크래프트 세계에 라이브러리 오브 루이나의 도서관 맵을 추가하는 모드**로 만든다
   (월드 파일 배포 → 모드로 차원·구조물·아이템·소리를 넣는 방식으로 전환)
- 지금 코드에서 미리 고려할 점: 공간별 별도 차원·데이터팩 함수 구조는 모드로 옮기기 쉽게 유지 (빌더 = 구조 생성 코드, `config.py` = 차원 설정)

## 5. 미해결 질문 / 리스크
- Iris/BSL + 커스텀 차원/attributes 하늘 호환 (테스터 ③)
- 큰 공간 성능 측정 (2026-10-11): 3072×3072 바닥+기둥+벽 = 섹션 5.6만 개, 메모리 약 0.5GB, 리전 쓰기 4코어 3.8초 → 현재 구조로 충분
  - 도형 엔진 carve는 아직 단일 프로세스 (외부 시제품 23초). 필요하면 섹션 단위 병렬화
- 릴리스 zip 2GB 제한 → 공간별 zip 분리 필요할 수 있음
- 배경음악·환경음 (사용자 결정 미정)
- 분화구가 커서 렌더 거리 24청크 이상 필요. Distant Horizons 호환은 아직 미확인
- 테스터 화면에서 날리는 잎 파티클이 크게 보임(근접) — 확률·종류 조정 여지
