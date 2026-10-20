# 모델·텍스처 제작 도구 — 2026-10-20

## 실제 확인한 구성

- 제작: 격리된 CPython 3.11.17 + Blender Python `bpy 4.5.3 LTS`.
- 편집/검사: Blockbench MCP 1.10.1, 소스 커밋 `141ef78fa59eb697895ab73d4757d874ab8a2711`.
  실제 stdio MCP 세션으로 `bbmodel_info`, `bbmodel_validate` 호출 확인.
- CPU 미리보기: 기존 numpy/Pillow/C 면 채움 렌더러. GPU·WebGPU가 없어도 작동.
- 배포: Blender 출력 `.bbmodel`을 Git에 저장하고 일반 빌드는 `tools.model_import`로 읽음.
  모드 사용자와 GitHub 일반 월드 빌드에 Blender/Bun/MCP를 추가 설치할 필요 없음.
- 이번 실행의 도구 경로: `/tmp/ruina-blender-venv`, `/tmp/ruina-blockbench-mcp`.
  임시 경로가 사라지면 아래 명령으로 복원한다. 사용자 PC에 설치한 것이 아님.

GUI Krita/Blockbench/Blender와 사용자 PC의 원격 연결은 구성하지 않았다.
외부 이미지 API 키·유료 서비스·셰이더·새 모드 런타임 의존성을 추가하지 않았다.
이 대화의 도구 목록에 MCP를 등록한 것은 아니며, 제공된 일회성 클라이언트를 셸에서 실행한다.
외부 Agent Skills를 자동 로드하지 않았다. 먼저 검증한 MCP/변환 경로를 사용한다.

## 복원·확인 명령 (Linux에서 검증)

사전 설치: Python, uv, Node/npm, git, C 컴파일러. 도구 전용 캐시는 기본 `.art-tools/`이며 Git 제외.

```sh
python tools/art/setup.py
python tools/art/setup.py --check
```

별도 위치를 사용할 경우:

```sh
python tools/art/setup.py --home /tmp
python tools/art/setup.py --home /tmp --check
RUINA_ART_HOME=/tmp python tools/art/bb_call.py bbmodel_info '{"file":"models/tiphereth_table.bbmodel"}'
RUINA_ART_HOME=/tmp python tools/art/bb_call.py bbmodel_validate '{"file":"models/tiphereth_table.bbmodel"}'
/tmp/ruina-blender-venv/bin/python tools/art/make_tiphereth_table.py
python tools/art/preview_table.py
python -m tools.form_preview natural_science_room /tmp/tiphereth-room.png
python -m unittest discover -s tests -v
```

`setup.py`는 도구 소스 커밋, Blender 패키지 버전, upstream Bun lockfile을 사용한다.
일반 npm 생명주기 스크립트는 끄고 필요한 Bun 실행기 초기화만 명시적으로 실행한다.
수정된 외부 체크아웃을 다른 버전으로 강제 초기화하지 않는다.
`--check`는 다운로드/설치 없이 실제 Blender import와 MCP 모델 읽기를 확인한다.
Windows 실행은 아직 검증하지 않았다.

## 변환 계약과 실패 처리

1. Blockbench **Generic/free 정적 메시**만 지원한다. 16 모델 단위 = 1블록, X/Y-up/Z.
2. 삼각형은 마지막 정점을 반복해 기존 Quads 형식으로 전달. 사각형은 평면·볼록이어야 함.
3. 회전·스케일은 내보내기 전에 좌표에 굽는다. 계층은 조직용으로만 사용한다.
4. 큐브, 애니메이션, 숨긴 부품, 중복/누락 outliner, 퇴화/비정상 좌표, 없는 UV·재질,
   0..1 밖 UV, 비평면·오목 사각형은 오류로 중단. 지원하지 않는 형상을 조용히 버리지 않는다.
5. 텍스처는 빌더에서 명시적으로 재질 번호에 연결. `.bbmodel`의 내장 이미지는 편집기용 미리보기이며
   그 경로나 URL을 빌드가 자동으로 다운로드하지 않는다. UV 해상도는 모델 전체 공통값.
6. 충돌은 별도 정의한다. 가져오기 성공은 벽·가구 보행 검사 통과를 의미하지 않는다.
7. `design/models/`는 월드 캐시 지문과 Actions push 경로에 포함한다. 모델 파일만 바뀌어도 이전 월드 재사용 금지.
8. 도구 설치가 막혀도 커밋된 모델의 가져오기·CPU 미리보기·일반 CI는 사용 가능하다.
   모델이 잘못됐을 때 옛 모델로 조용히 대체하는 fallback은 하지 않는다.

## 첫 적용: 티페리트 방

- 원화 `reference/자연과학의 층 지정사서 방.png`를 직접 확인.
- 원형 받침 탁자를 사각 상판·하부 테두리·두 쌍의 X자 받침·발판·연결재로 교체.
  Blender에서 만든 9부품/234면의 닫힌 메시. 편집 가능한 원본과 생성 스크립트를 모두 저장.
- 원래 탁자는 높은 단 위에 있어 눈높이보다 높았다. 앞쪽 단 위의 낮은 탁자로 크기·배치 조정.
- 기존 큰 좌석 상자/떠 보이는 등받이는 다리·좌판·기울어진 등받이 기둥·가로살의 작은 목재 의자로 교체.
- 원화에 없는 추가 낮은 탁자와 고립된 선반/바닥 블록 제거.
- `previews/tiphereth_table_2026-10-20.jpg`: 원화 투영 없는 정면/측면/후면 CPU 미리보기.
- `previews/tiphereth_room_2026-10-20.jpg`: 도착/측면의 전후 CPU 미리보기.

**방 전체 완성 아님.** 기존 단의 높이/반 칸 충돌 차이, 창 앞에 걸쳐 보이는 단 모서리,
의자·탁자의 실제 충돌, 측면 책장 반복/원화 투영 늘어짐, 계단/문/창의 비율은 추가 작업 대상.
MCP 검사의 block-model 크기 제한 항목은 free 메시이므로 미실행이며 검사 성공으로 오기하지 않는다.
게임 테스트·JAR 배포·1050 Ti FPS는 이 도구 검증과 별개다. 게임 최종 테스트는 전체 구축 후 수행한다.

## 도구 원본

- https://github.com/jasonjgardner/blockbench-mcp-plugin/tree/141ef78fa59eb697895ab73d4757d874ab8a2711
- https://github.com/jasonjgardner/blockbench-mcp-plugin/blob/141ef78fa59eb697895ab73d4757d874ab8a2711/headless/README.md
- https://docs.blender.org/api/4.5/
- https://www.blockbench.net/

외부 도구 소스는 모드에 복사하거나 패키징하지 않는다. 프로젝트 자체 생성 스크립트·모델만 사용한다.
