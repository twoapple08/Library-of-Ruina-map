# 인수인계 (HANDOFF)

새 세션은 **이 문서 → `docs/test/README.md`(2차 테스트 원문·원인 분석) + `docs/test/test2/` 스크린샷 → `docs/mod/기초구성.md`(모드 구성) → `PLAN.md` → `TESTING.md`** 순서로 확인하고 이어서 작업한다.
마지막 갱신: 2026-10-12 (2차 테스트 반영 라운드 끝: 조각 F 층 사슬·버그·소리·맵 전용 BSL → 3차 테스트 대기 + **모드 시험 제작은 사용자 지시 대기**. 다음 세션 첫 작업은 4절 맨 위).

## 0. 사용자와 일하는 방식

- 사용자는 **폰으로만 작업** (안드로이드). PC 테스트는 **다른 사람(테스터)**이 한다. 2차 테스트 PC는 **GTX1050ti·i7-8700·16GB** (1차는 RTX 4060). 사용자가 결과·스크린샷을 전달해 줌.
- **토큰 절약**이 최우선. 폰으로 할 수 있는 일(전달·결정·의견)은 사용자에게 맡기고, 답변은 짧게.
- 사용자가 **"아직 하지 말것/시작하지 말것"**이라고 하면 분석·답변만 하고 작업하지 않는다. "일시정지"하라고 하면 멈춘다.
- 노력 수준: 사용자가 설정함. 추천은 **high** (판단 필요한 설계), 단순 수정은 medium. 컨텍스트가 길어지면 HANDOFF 갱신 후 새 세션 권장.
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
- 차원 타입이 바닐라 overworld 를 복사하면 바닐라 배경음악도 따라옴 → `audio/background_music` 지움, 공간 음악은 바이옴에 (`config.music`)

### BSL (v10.1.6, 사용자 제공 → `shaderpack/`)
- BSL은 `sunAngle`(오버월드 시계)로 낮밤을 정함. 우리는 모두 자정 → 밤빛. 개조: `dimension.properties` 에 새 폴더 `ruina`(world0 + `#define RUINA`),
  RUINA 에서 lightNight·ambientNight 를 `fogColor`(우리 환경 속성 안개색)로, 최소 밝기 ×5, 하늘은 바닐라 경로(skyColor). 외부는 원본(world0)
- 기본값: 그림자 1536/192, BSL 구름 끔. 셰이더 컴파일은 여기서 확인 못 함 → 테스터 확인 필요 (3차 ⑭)

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

### ▶ 다음 세션 첫 작업 (2026-10-12 2차 테스트 반영 라운드 끝 기준)
1. **사용자 지시를 먼저 받을 것**: 사용자는 이번 라운드 뒤 **모드 시험 제작**을 하려 함 (`docs/mod/기초구성.md` — 초대장·방전환·세피라 10종,
   우클릭, 크리에이티브 탭에서 꺼냄, 자동 지급 없음, 기존 조각은 기능 없는 아이템으로). 제안해 둔 방향: Fabric 보조 모드부터,
   **원화 투영**(도착 시점에서 원화를 형체에 비춰 입힘) + 자유 모델로 층 하나(총류 추천) 시험 → Fabric client gametest 로 CI 스크린샷 비교(가능한지 확인 필요).
   모드 빌드는 **CI에서만** (작업 환경은 maven.fabricmc.net·Mojang 접속 403/막힘, Maven Central·Gradle 배포판은 됨)
2. 3차 테스트 결과가 오면 `docs/test/`에 보관·분석 (TESTING.md 3차 양식 ①~⑰)
3. 미뤄 둔 모양 수정 (모드 방식으로 할지 사용자와 정한 뒤): 탑 가지치기·가지 배치를 원화에 맞춤(④), 자연과학 돔 뒷면·진짜 다리,
   언어 방 = 실제 용암 전경이 창으로 보이게 방을 전경 안에, 총류 방 = 전경의 높은 책탑 위, 예소드 방 등 원화 대비 품질 (docs/test/README.md 표 마지막 줄)
- 이번 라운드에서 한 것: 조각 F 층 사슬(`fragment.stage/finish`, 걷기 층 이동 삭제·조형물 유지), 마그마크림 버그(아래 2절), 어둠 효과 암전,
  외부 도착 시 조각 회수, 역사 계단 방향, DH 먼 벽, 눈 셋 괴물 위치, 외부 높이 1024(빛기둥), setup 완료 메시지, 첫 접속 TP, keep_inventory,
  로비 홀 음악(바이옴 `audio/background_music`)·전환 소리·바닐라 음악 끔·`resources.zip`, **맵 전용 BSL**(`tools/shaderpack.py` → 릴리스 `BSL_v10.1.6_Ruina.zip`)
- 지정 브랜치는 세션마다 다름 — 이 세션: `claude/blissful-wright-3xyvvz` (main 과 같게 맞춰 둠)

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
- CI 실행: main에 builders/·tools/·config.py·ref/ 변경 push 시 자동. 결과는 `git fetch origin ci-output` → `world/SUMMARY.md`, `world/report.json`
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
