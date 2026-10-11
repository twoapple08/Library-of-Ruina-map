"""미리보기 목록 (폰 확인용). 공간을 새로 지으면 여기에 추가."""
from __future__ import annotations

import os

from PIL import Image

from tools.preview import Palette, _frame, render_side, render_top
from tools.render3d import iso_panel
from tools.render_persp import render_persp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _compare(ref_name, ours, title, notes, crop=None):
    ref = Image.open(os.path.join(ROOT, "reference", ref_name)).convert("RGB")
    if crop:
        ref = ref.crop(crop)
    ref = ref.resize(ours.size)
    both = Image.new("RGB", (ours.width, ours.height * 2))
    both.paste(ref, (0, 0))
    both.paste(ours, (0, ours.height))
    return _frame(both, title, notes)


def render_exterior(b, out_dir, pal):
    d = b.dims["exterior"]
    files = []

    def save(img, name):
        p = os.path.join(out_dir, name)
        img.save(p, optimize=True)
        files.append(p)

    ground = render_persp(d, pal, cam=(0, 4, 100), look=(0, 40, 0), fov=95, W=1000, H=562)
    save(_compare("도서관 외견.png", ground, "외부 — 원화(위) / 맵(아래): 스폰에서 본 정문과 탑",
                  ["맵 그림은 블록 데이터로 그린 근사 (실제 게임은 텍스처·쉐이더로 더 자세함)"]),
         "exterior_compare_gate.png")
    up = render_persp(d, pal, cam=(18, 2, 92), look=(0, 230, 0), fov=100, W=1000, H=562)
    save(_frame(up, "외부 — 탑 올려다보기", ["가지 끝 소용돌이, 꼭대기에서 넓게 퍼지는 수관, 빛기둥 건축물"]), "exterior_look_up.png")
    aerial = render_persp(d, pal, cam=(0, 800, 1280), look=(0, 60, 0), fov=62, W=1000, H=562, fog_dist=2200,
                          max_dist=2600)
    save(_compare("도서관 위치 전경.png", aerial, "외부 — 원화(위) / 맵(아래): 위에서 본 분화구",
                  ["원화와 비슷한 각도(약 32°)에서 봄. 계단식 단 7개(그릇 모양) + 빌딩, 나선 구름(가장자리 스테인드글라스), 고리 구조물, 빛기둥 건축물, 종이 물결 7줄기"]),
         "exterior_compare_aerial.png")
    tower = render_persp(d, pal, cam=(0, 560, 780), look=(0, 210, 0), fov=52, W=1000, H=562, max_dist=2000)
    save(_compare("도서관 위치 전경.png", tower, "외부 — 원화(위, 탑 부분 확대) / 맵(아래): 탑과 수관",
                  ["아래가 굵고 위로 좁아지는 몸통, 꼭대기에서 꽃병처럼 퍼지는 수관, 빛기둥 건축물",
                   "탑 높이 285 + 수관 ≈ 120, 바깥 단 214 + 빌딩"], crop=(205, 140, 605, 365)),
         "exterior_compare_tower.png")
    save(iso_panel(d, pal, "외부 전체 입체도", ["분화구 지름 약 1520칸"], view="se", lod=4, target=1400),
         "exterior_iso.png")
    save(render_top(d, pal, (-760, -760, 760, 760), "외부 — 위에서 본 평면", ["초록 = 도착 지점, 주황 = TP"],
                    marks=_marks(b, d.dim), target=1400), "exterior_top.png")
    return files


def _marks(b, dim):
    out = []
    for name, a in b.links.anchors.items():
        if a.dim == dim:
            out.append((a.x, a.z, name, (120, 230, 140)))
    for w in b.links.walks:
        if w.dim == dim:
            out.append(((w.box[0] + w.box[3]) / 2, (w.box[2] + w.box[5]) / 2, f"TP→{w.dest}", (250, 170, 90)))
    return out


def render_lobby(b, out_dir, pal):
    from builders.lobby import HALL_DX, RZ, Y0
    d = b.dims["lobby"]
    files = []

    def save(img, name):
        p = os.path.join(out_dir, name)
        img.save(p, optimize=True)
        files.append(p)

    room = render_persp(d, pal, cam=(0.5, Y0 + 1.6, RZ - 2), look=(0.5, Y0 + 3, -RZ - 4), fov=80, W=1000, H=562,
                        max_dist=200, sky=((18, 10, 5), (28, 16, 8)), fog=(28, 16, 8), fog_dist=45, stars=0)
    save(_compare("로비.png", room, "로비 (전환 전) — 원화(위) / 맵(아래): 도착 자리에서 북쪽",
                  ["어두운 나무 방: 책장 칸과 홈 기둥, 벽등, 등 기둥, 책상, 넓은 낮은 단 → 통로 계단",
                   "은조각을 왼손으로 들면(F) 번쩍이며 같은 자리의 밝은 홀로 바뀜"]), "lobby_compare_room.png")
    hall = render_persp(d, pal, cam=(HALL_DX + 0.5, Y0 + 1.6, RZ - 2), look=(HALL_DX + 0.5, Y0 + 9, -30), fov=80,
                        W=1000, H=562, max_dist=300, sky=((244, 226, 189), (233, 207, 156)), fog=(233, 207, 156),
                        fog_dist=90, stars=0, night=False)
    save(_compare("로비 전경 (전환 후).jpg", hall, "로비 (전환 후) — 원화(위) / 맵(아래): 같은 자리에서 본 홀",
                  ["가운데 단 위 앤젤라의 책상 (높이 1 = 앉은 캐릭터 기준), 뒤로 휘어 오르는 흰 대계단과 빛",
                   "둥근 책장 벽(반지름 22, 높이 12, 사다리) 너머로 솟은 책장 덩어리, 바닥의 책 더미"]),
         "lobby_compare_hall.png")
    save(render_top(d, pal, (-14, -28, 14, 20), "로비 (전환 전) — 평면 (천장 아래에서 자름)",
                    ["초록 = 도착 지점, 주황 = TP (남쪽 문 → 외부 정문)"], y_max=Y0 + 8, marks=_marks(b, d.dim)),
         "lobby_plan_room.png")
    save(render_top(d, pal, (HALL_DX - 64, -80, HALL_DX + 64, 64), "로비 (전환 후) — 평면", [], y_max=Y0 + 40,
                    marks=_marks(b, d.dim)), "lobby_plan_hall.png")
    return files


def render_history(b, out_dir, pal):
    from builders.history import ARRIVE_Z, RD, ROOM_X, Y0
    d = b.dims["history"]
    files = []
    warm = dict(sky=((241, 217, 166), (226, 191, 134)), fog=(226, 191, 134), stars=0, night=False)

    def save(img, name):
        p = os.path.join(out_dir, name)
        img.save(p, optimize=True)
        files.append(p)

    stage = render_persp(d, pal, cam=(0.5, Y0 + 9, ARRIVE_Z + 12), look=(0.5, Y0 + 2, ARRIVE_Z - 40), fov=78,
                         W=1000, H=562, max_dist=900, fog_dist=260, **warm)
    save(_compare("역사의 층 전경.png", stage, "역사의 층 — 원화(위) / 맵(아래): 도착 자리 위에서 북쪽을 내려다봄",
                  ["동서로 긴 길 여러 줄: 헤링본 바닥, 난간(검은 몸통·금속 윗면·아래 빛줄), 5칸마다 유리 진열장(책)",
                   "멀리 안개 속 거대 책장 기둥, 거대 유물 셋 (불 켜진 나무 장 · 톱니·쇠사슬 돌기둥 · 이끼 돌덩이)"]),
         "history_compare_stage.png")
    over = render_persp(d, pal, cam=(0.5, Y0 + 160, 420), look=(0.5, Y0 - 20, -120), fov=70, W=1000, H=562,
                        max_dist=1600, fog_dist=700, **warm)
    save(_frame(over, "역사의 층 — 멀리서 본 전체", ["가운데 접대 무대(500×250) → 아래로 4겹 반복되는 바닥과 책장 절벽",
                                                  "뒤로 책장 기둥 줄과 유물 셋, 구역 끝을 두르는 큰 책장 벽"]),
         "history_overview.png")
    room = render_persp(d, pal, cam=(ROOM_X - 4.5, Y0 + 2.2, RD - 1), look=(ROOM_X + 4, Y0 + 3, -RD), fov=80,
                        W=1000, H=562, max_dist=120, sky=((40, 26, 12), (58, 36, 18)), fog=(58, 36, 18),
                        fog_dist=60, stars=0)
    save(_compare("역사의 층 지정사서 방.png", room, "말쿠트 방 — 원화(위) / 맵(아래)",
                  ["천장까지 책장 칸 + 칸 사이 금빛 빛줄, 책상 위 펼친 책·책 더미, 높은 등받이 의자 둘",
                   "오른쪽 책장 틈으로 금빛 (금조각을 왼손으로 들면(F) 접대 공간 ↔ 방)"]), "history_compare_room.png")
    return files


def render_technology(b, out_dir, pal):
    from builders.technology import ARRIVE_X, RD, ROOM_X, RY, Y0
    d = b.dims["technology"]
    files = []
    night = dict(sky=((60, 36, 96), (106, 69, 150)), fog=(75, 47, 112), stars=200)

    def save(img, name):
        p = os.path.join(out_dir, name)
        img.save(p, optimize=True)
        files.append(p)

    side = render_persp(d, pal, cam=(0.5, Y0 + 6, 34), look=(0.5, Y0 + 4, -120), fov=80, W=1000, H=562,
                        max_dist=1200, fog_dist=500, **night)
    save(_compare("기술과학의 층 전경.png", side, "기술과학의 층 — 원화(위) / 맵(아래): 다리 옆에서 북쪽",
                  ["고가도로(4차선·점선·철 난간), 녹슨 주탑·쇠사슬, 다리 아래 트러스와 네온 도시·빛나는 길",
                   "뒤로 네온 빌딩 숲, 녹슨 거대 톱니, 가장 높은 건물에서 톱니로 뻗은 케이블, 보라 하늘"]),
         "technology_compare_bridge.png")
    deck = render_persp(d, pal, cam=(ARRIVE_X + 0.5, Y0 + 1.6, 0.5), look=(ARRIVE_X + 60, Y0 + 20, 0.5), fov=80,
                        W=1000, H=562, max_dist=1200, fog_dist=500, **night)
    save(_frame(deck, "기술과학의 층 — 도착 자리 (다리 위, 동쪽을 봄)", ["철괴를 왼손으로 들면(F) 예소드 방으로"]),
         "technology_deck.png")
    room = render_persp(d, pal, cam=(ROOM_X + 0.5, RY + 2.5, RD - 1), look=(ROOM_X + 0.5, RY + 5, -RD), fov=80,
                        W=1000, H=562, max_dist=120, sky=((20, 10, 32), (36, 19, 58)), fog=(36, 19, 58),
                        fog_dist=50, stars=0)
    save(_compare("기술과학의 층 지정사서 방.png", room, "예소드 방 — 원화(위) / 맵(아래)",
                  ["빛줄 서랍장, 천장에 매달린 톱니 샹들리에(보라 발광), 콘솔 책상·화면, 빛나는 유리문(초승달)"]),
         "technology_compare_room.png")
    return files


def render_all(b, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    pal = Palette()
    files = []
    if "exterior" in b.dims:
        files += render_exterior(b, out_dir, pal)
    if "lobby" in b.dims:
        files += render_lobby(b, out_dir, pal)
    if "history" in b.dims:
        files += render_history(b, out_dir, pal)
    if "technology" in b.dims:
        files += render_technology(b, out_dir, pal)
    return files
