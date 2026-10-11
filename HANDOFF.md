# 인수인계 (HANDOFF)

새 세션은 **이 문서와 `PLAN.md`를 먼저 읽고** 이어서 작업한다.
마지막 갱신: 2026-10-11 (Phase 0 완료·테스터 확인 대기 + 기반 작업: 설계서·도형 엔진·입체 렌더러·성능).

## 0. 사용자와 일하는 방식

- 사용자는 **폰으로만 작업**한다 (안드로이드). 컴퓨터는 켜둘 수 없고, PC 맵 테스트는 **다른 사람(테스터)**이 한다.
- 토큰 절약을 원한다. 폰으로 할 수 있는 일(테스터에게 전달, 미리보기 보고 의견 주기, 결정)은 사용자에게 단계별로 맡긴다.
- 결과 확인은 `previews/`의 **미리보기 PNG**(위에서 본 모습·정면·단면)로 한다. `previews/README.md`에 목록.
- **커밋은 main에 바로** 해도 된다 (사용자 허락).
- 설정은 사용자도 잘 모른다고 함 → 설정 관련은 나무위키를 직접 확인하고, 사용자의 추측은 검증 후 반영.
- 한국어로 소통.

## 1. 현재 상태

- [x] 설계 확정 (PLAN.md). **공간마다 별도 차원** — 사용자 확정 (2026-10-11)
- [x] Phase 0 코드: NBT·리전·월드 모듈, 데이터팩 생성기, 서버 하네스, CI 월드 빌드, 미리보기, 단위 테스트
- [x] CI(Actions)에서 26.3 서버로 스모크 월드 검증 **전부 통과** (블록 217/217, 블록 엔티티, TP 엔티티·함수, 조명 재계산, 로그 경고 0)
- [x] 릴리스 `world-latest`에 `Library-of-Ruina.zip` 자동 업로드
- [x] `TESTING.md` (테스터용 설치·확인·보고 양식)
- [ ] **테스터 확인 대기** (TESTING.md 3절 ①~⑧). 특히 ③ BSL에서 커스텀 차원 하늘·초승달
- [x] 기반 작업 (사용자 요청: 노력 높을 때 효과 큰 작업 먼저)
  - [x] 외부 원화 정밀 분석 → `design/exterior.md` (탑 11단 = 로비+10층 대응 등 제안 수치)
  - [x] 곡면 도형 엔진 `tools/shapes.py` (SDF 부품, 속 빈 껍질, 계단·반블록 곡면 다듬기, 노이즈, 소용돌이 곡선)
  - [x] 입체 미리보기 렌더러 `tools/render3d.py` (등각/정면, 면 음영, 발광 번짐, lod 묶음)
  - [x] 외부 시제품 v0 `builders/exterior.py` → `previews/proto_exterior_v0_*.png` (아직 월드 빌드에는 안 넣음)
  - [x] 성능: 도형 엔진 5배(2단계 평가·관 단순화), 리전 쓰기 8배(문자열 캐시·빈 섹션 재사용·병렬)
- 다음: 테스터 결과 반영 → Phase 1 (외부 건물: 시제품 v0를 다듬어 확정)

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
builders/exterior.py    외부 시제품 v0 (design/exterior.md 수치). python build.py proto 로 미리보기 (약 30초)
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

## 4. 다음 할 일

### Phase 0 마무리
1. 사용자 → 테스터에게 `TESTING.md` 링크 전달, 결과(보고 양식+스크린샷) 받기
2. 결과 반영:
   - ③ BSL이 attributes 하늘을 무시하면: 바이옴 attributes로 옮겨 보기 → 안 되면 쉐이더 쪽 대안(BSL 설정) 또는 한 차원 + 좌표 분리로 대체 (PLAN 2절 TP 방식은 그대로)
   - 초승달이 안 보이거나 위치가 이상하면 `moon_angle` 조정 (0 = 머리 위)
   - 배경음악: 지금은 바닐라 크리에이티브 음악이 그대로 나옴 (사용자에게 끌지 물어볼 것)

### Phase 1~: PLAN.md 3절 순서대로 (외부 → 로비 → 역사 → … → 총류)
- 외부(Phase 1) 남은 일: 시제품 v0에 황금 종이 물결, 도시 실루엣(반지름 300~750), 가지 계단·기둥, 재질 다듬기
  → 사용자에게 미리보기로 확인 → `build_all()`에 넣어 CI 빌드 → 테스터 확인
- 외부 스케일: PLAN 5절 — `config.EXTERIOR_SCALE`
- 각 층 착수 시 원화(`reference/`) 보고 하늘 값 결정 → PLAN.md 7절에 기록

### 도형 엔진 사용법 요약
```python
from tools import shapes as S
WOOD = ("minecraft:dark_oak_stairs", "minecraft:dark_oak_slab")
tube = S.Tube(점들(M,3), 반지름들(M,)).with_(paint=S.log_along("minecraft:dark_oak_log[axis={a}]"), smooth=WOOD)
body = S.Revolve(y0, y1, radius_fn(y, theta), rmax).with_(paint=함수(ctx))  # ctx.info: rho, theta, y
S.carve(dim, S.Union(body - S.Box(...), tube), shell=2, smooth=True)
```
- 곡선: `S.bezier`, `S.resample`, `S.curl`(소용돌이), `S.join`, `S.taper` / 난수: `S.hash01`, `S.fbm`
- 칠하기 ctx: x,y,z(정수), P(중심), d(깊이: 0에 가까울수록 바깥 면), info(부품별 값)
- 계단 판정표는 마인크래프트 StairBlock의 SHAPE_BY_STATE를 그대로 옮김 (방향·inner/outer 검증은 테스터 화면으로)

## 5. 미해결 질문 / 리스크
- Iris/BSL + 커스텀 차원/attributes 하늘 호환 (테스터 ③)
- 큰 공간 성능 측정 (2026-10-11): 3072×3072 바닥+기둥+벽 = 섹션 5.6만 개, 메모리 약 0.5GB, 리전 쓰기 4코어 3.8초 → 현재 구조로 충분
  - 도형 엔진 carve는 아직 단일 프로세스 (외부 시제품 23초). 필요하면 섹션 단위 병렬화
- 릴리스 zip 2GB 제한 → 공간별 zip 분리 필요할 수 있음
- 배경음악·환경음 (사용자 결정)
