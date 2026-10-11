# 테스트 안내 (PC 테스터용)

도서관 맵을 PC에서 열어 보고 결과를 알려주시는 분을 위한 문서입니다.
지금은 **Phase 0 스모크 테스트**: 실제 건물이 아니라, 맵을 만드는 방식이 잘 동작하는지 확인하는 작은 시험용 월드입니다.

## 1. 설치 (처음 한 번)

| 순서 | 무엇 | 비고 |
|---|---|---|
| 1 | 마인크래프트 Java 에디션 **26.3** | 런처에서 26.3 실행 한 번 해두기 |
| 2 | **Fabric Loader** (26.3) | [Fabric 설치기](https://fabricmc.net/use/installer/) 또는 Modrinth App/Prism Launcher |
| 3 | **Sodium** (26.3용 최신, 0.9.2 이상) | `mods` 폴더 |
| 4 | **Iris** (26.3용 최신, 1.11.6 이상) | `mods` 폴더. [Iris 설치기](https://www.irisshaders.dev/download)를 쓰면 Sodium까지 같이 설치됨 |
| 5 | (선택) Lithium, FerriteCore, ImmediatelyFast | 성능용. 없어도 됨 |
| 6 | **BSL Shaders** 최신판 | `shaderpacks` 폴더 (압축 풀지 말고 zip 그대로) |

- Distant Horizons는 **이번 테스트에서는 빼 주세요** (커스텀 차원과의 호환은 나중에 따로 확인).
- 26.3은 투명 블록 렌더링이 바뀌어서, 쉐이더팩도 최신판이어야 유리·물이 제대로 보입니다.

## 2. 월드 받기

1. [Releases → 최신 월드 (world-latest)](https://github.com/twoapple08/Library-of-Ruina-map/releases/tag/world-latest)에서 `Library-of-Ruina.zip` 다운로드
2. `.minecraft/saves/` 폴더에 압축 해제 → `saves/Library of Ruina/level.dat` 위치가 되면 정상
3. 마인크래프트(Fabric 프로필) → 싱글플레이 → **Library of Ruina**
   - "실험적 설정/데이터팩" 경고가 나오면 계속 진행

## 3. 확인할 것 (Phase 0)

쉐이더 **끈 상태**와 **BSL 켠 상태** 둘 다 봐 주세요. (옵션 → 비디오 설정 → 셰이더 팩)

| # | 확인 | 방법 |
|---|---|---|
| ① | 월드가 오류 없이 열리는가 | 오류 화면·경고 내용이 있으면 사진 |
| ② | 처음 위치 | 둥근 검은 받침대 위, 북쪽(앞)에 검은 문이 보여야 함. F3 화면 왼쪽에 `ruina:exterior` |
| ③ | 하늘 | **보라색 밤하늘 + 초승달 + 별**이 보이는가. 하늘 전체를 둘러보며 스크린샷 2~3장 (쉐이더 끔/켬 각각) |
| ④ | TP | 검은 문 가운데를 **우클릭** → 책장 방(로비)으로 이동? 로비 남쪽 검은 문 우클릭 → 밖으로 돌아오는가 |
| ⑤ | 조명 | 랜턴·바닥 발광 블록 주변이 밝은가, 검은 얼룩·이상하게 어두운 곳이 있는가 |
| ⑥ | 블록 | 받침대 왼쪽 뒤 **조각된 책장**에 책 3권이 꽂혀 있는가 |
| ⑦ | 명령어 | 채팅에 `/function ruina:setup` 입력 → 오류 없이 실행되는가 (치트 허용 확인) |
| ⑧ | 성능 | F3의 fps: 쉐이더 끔/켬 각각. PC 사양(그래픽카드) 한 줄 |
| ⑨ | 곡면 견본 | 받침대 **오른쪽(동쪽)**의 작은 탑과 끝이 말린 가지 2개. 표면의 계단·반블록이 매끄럽게 붙었는지, 엉뚱한 방향으로 튀어나온 계단이 없는지 가까이·멀리 스크린샷 2장 (`/function ruina:tp/to/engine_sample`로 바로 이동) |

## 4. 보고 양식

아래를 복사해서 채운 뒤, 스크린샷과 함께 보내 주세요 (GitHub 이슈 또는 맵 주인에게 메신저로).

```
[Phase 0 테스트]
마인크래프트 / Fabric / Sodium / Iris / BSL 버전:
PC 사양(그래픽카드):
① 월드 열림: O / X (오류 내용)
② 처음 위치·F3 차원 이름:
③ 하늘 (쉐이더 끔): 하늘색 / 달 모양 / 별
   하늘 (BSL 켬): 하늘색 / 달 모양 / 별
④ TP 외부→로비: O / X   로비→외부: O / X
⑤ 조명 이상: 없음 / 있음 (위치)
⑥ 책장 책 3권: O / X
⑦ /function ruina:setup: O / X
⑧ fps 쉐이더 끔 / 켬:
⑨ 곡면 견본: 매끄러움 O / X, 이상한 계단 위치:
기타:
```

## 참고

- 각 공간은 별도 차원(`ruina:exterior`, `ruina:lobby`, …)이라 공간마다 하늘·시간을 따로 정할 수 있습니다.
- 처음 위치로 가기: `/function ruina:tp/to/exterior_spawn`
- 미리보기 그림은 `previews/` 폴더에 있습니다.
