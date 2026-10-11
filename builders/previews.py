"""공간별 미리보기 목록. 공간을 새로 지으면 여기에 추가."""
from __future__ import annotations

import os

from tools.preview import Palette, render_side, render_top
from tools.render3d import iso_panel


def _marks(b, dim):
    out = []
    for name, a in b.links.anchors.items():
        if a.dim == dim:
            out.append((a.x, a.z, f"도착:{name}", (120, 230, 140)))
    for p in b.links.portals:
        if p.dim == dim:
            out.append((p.x, p.z, f"TP→{p.dest}", (250, 170, 90)))
    return out


def render_all(b, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    pal = Palette()
    files = []

    def save(img, name):
        p = os.path.join(out_dir, name)
        img.save(p, optimize=True)
        files.append(p)

    if "exterior" in b.dims:
        d = b.dims["exterior"]
        save(render_top(d, pal, (-24, -30, 24, 12), "외부 (스모크 테스트) — 위에서 본 모습",
                        ["받침대 · 정문까지 길 · 임시 정문 · 조각된 책장"], marks=_marks(b, d.dim)),
             "smoke_exterior_top.png")
        save(render_side(d, pal, (-24, 56, 24, 84, 12, -30), "외부 (스모크 테스트) — 정면",
                         ["받침대 뒤로 임시 정문(기둥 + 상인방)"]), "smoke_exterior_front.png")
    if "lobby" in b.dims:
        d = b.dims["lobby"]
        save(render_top(d, pal, (-14, -14, 14, 14), "로비 (스모크 테스트) — 평면 (천장 아래 Y=70에서 자름)",
                        ["책장 벽 · 랜턴 조명 · 남쪽 문(TP→외부)"], y_max=70, marks=_marks(b, d.dim)),
             "smoke_lobby_plan.png")
        save(render_side(d, pal, (-14, 60, 14, 78, 0, -14), "로비 (스모크 테스트) — 단면 (Z=0에서 자름)",
                         ["방 가운데를 자른 모습: 바닥·벽·천장·매달린 랜턴"]), "smoke_lobby_section.png")
    return files


def render_proto(out_dir):
    """외부 건물 시제품 v0 (도형 엔진 시연). 아직 월드 빌드에는 안 들어감."""
    from builders import Build, exterior
    b = Build()
    exterior.build(b)
    d = b.dims["exterior"]
    pal = Palette()
    files = []
    notes = ["시제품 (Phase 1에서 다듬음) · 황금 종이 물결 포함 · 도시 배경은 아직"]
    for view, name, title in (("se", "proto_exterior_v0_se.png", "외부 시제품 v0 — 남동쪽에서"),
                              ("front", "proto_exterior_v0_front.png", "외부 시제품 v0 — 정면(남쪽)")):
        p = os.path.join(out_dir, name)
        iso_panel(d, pal, title, notes, view=view, target=1500, box=(-240, -8, -240, 240, 460, 240)).save(p, optimize=True)
        files.append(p)
    for view, name, title, lod, box in (
            ("se", "proto_exterior_city_se.png", "외부 전체 — 탑 + 도시 실루엣 (남동쪽 위)", 4, None),
            ("front", "proto_exterior_city_front.png", "외부 전체 — 정면 (앞쪽 도시는 잘라냄)", 2, (-760, -64, -760, 760, 600, 200))):
        p = os.path.join(out_dir, name)
        iso_panel(d, pal, title, ["도시: 반지름 300~750, 빌딩 약 900채 (겉껍질만)"], view=view, lod=lod, box=box,
                  target=1500).save(p, optimize=True)
        files.append(p)
    p = os.path.join(out_dir, "proto_exterior_v0_paper.png")
    iso_panel(d, pal, "외부 시제품 — 정문과 황금 종이 물결 확대", notes, view="se",
              box=(-120, -4, 0, 120, 40, 120), target=1400).save(p, optimize=True)
    files.append(p)
    return files
