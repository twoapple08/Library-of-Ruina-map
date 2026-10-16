"""예소드 방 (기술과학의 층 지정사서 방) — 자유 형체 판. reference/기술과학의 층 지정사서 방.png

어두운 사무실: 보라 빛줄이 든 서랍장(왼쪽·오른쪽 큰 장), 천장에 줄로 매달린 톱니 샹들리에(보라 발광 테두리, 천천히 돎),
가운데 콘솔 책상(화면), 뒤 빛나는 유리문(초승달), 파일 상자, 어두운 타일 바닥(반사).
도착: 남쪽 높은 단(높이 3)에서 북쪽 (원화는 세로선이 나란함 → 수평 시선).
"""
from __future__ import annotations

import math

import numpy as np

from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 64
OX = 4000
DAIS = 3
ART = "reference/기술과학의 층 지정사서 방.png"
CAM = F.Camera((OX + 0.5, Y0 + DAIS + 1.62, 8.9), 180.0, 0.0)
ARRIVE = (OX + 0.5, Y0 + DAIS, 8.9, 180.0, 0.0)
X0, X1, ZB, ZS, H = OX - 12.0, OX + 13.0, 0.0, 16.0, 12.0
SPACE = "technology"


def mats():
    m = {}
    from tools import artfit as A
    # 샹들리에는 움직이는 형체 → 원화에서 지운 그림을 투영 (뒤 벽에 그림 샹들리에가 겹쳐 남지 않게)
    clean = A.clean_sky(ART, A.box_mask((1000, 562), [(240, 0, 480, 315)]), grow=3)
    m["art"] = F.mat("troom_art", T.art("art/technology_room", ART, img=clean), emissive=True, flat=True, ao=False)
    m["panel"] = F.mat("troom_panel", T.stone_slab("troom_panel", (14, 12, 20), (34, 30, 44), seed=91), emissive=True,
                       flat=True, ao=False)
    m["tile"] = F.mat("troom_tile", T.stone_slab("troom_tile", (16, 14, 22), (44, 38, 56), seed=92), emissive=True,
                      flat=True, ao=False)
    m["drawer"] = F.mat("troom_drawer", T.shelf("troom_drawer", [(60, 50, 90), (50, 44, 80), (80, 66, 120)],
                                                wood=(200, 150, 255), seed=93, dark_back=(30, 24, 44)),
                        emissive=True, flat=True, ao=False, glow=5)
    m["neon"] = F.mat("troom_neon", T.glow("troom_neon", (210, 150, 255)), emissive=True, flat=True, ao=False, glow=5)
    m["gear"] = F.mat("troom_gear", T.metal("troom_gear", (24, 20, 32), (70, 60, 90), seed=94), emissive=True,
                      flat=True, ao=False)
    m["door"] = F.mat("troom_door", T.glow("troom_door", (220, 180, 255)), layer="translucent", emissive=True,
                      flat=True, ao=False)
    m["box"] = F.mat("troom_box", T.stone_slab("troom_box", (60, 56, 72), (110, 104, 124), seed=95), emissive=True,
                     flat=True, ao=False)
    m["screen"] = F.mat("troom_screen", T.glow("troom_screen", (150, 200, 255)), emissive=True, flat=True, ao=False,
                        glow=5)
    return m


def drawers(m, x0, x1, y0, y1, z, rows):
    """빛줄 서랍장: 앞면 서랍 칸 (위 테두리가 보라 빛)."""
    out = [F.box((x0, y0, z - 1.2), (x1, y1, z), m["panel"], faces="xXyY")]
    out.append(F.plane((x0, y0, z), (x1 - x0, 0, 0), (0, y1 - y0, 0), m["drawer"], tile=((x1 - x0) / 2, (y1 - y0) / rows)))
    return F.concat(out)


def chandelier(lay, m):
    """천장에 매달린 톱니 샹들리에 (큰 세로 톱니 + 기울어진 고리 + 작은 톱니). 움직임: 큰 톱니 천천히 회전."""
    from tools import artfit as A
    view = A.ArtView(CAM, 1000, 562)
    cz = 2.5

    def at(px, py, pr):
        c = view.at_z(np.array([float(px)]), np.array([float(py)]), cz)[0]
        return c, pr * view.px_size(c)
    (c1, r1), (c2, r2), (c3, r3) = at(360, 95, 105), at(365, 228, 118), at(413, 285, 55)
    big = kit.gear(c1, (0, 0, 1), r1, m["gear"], teeth=10, thick=0.5, hole=0.45, spokes=0)
    rim = kit.gear(c1 + np.array([0, 0, 0.28]), (0, 0, 1), r1 * 1.02, m["neon"], teeth=10, thick=0.06, hole=0.92,
                   spokes=0)
    lay.mover(F.Mover(tuple(int(v) for v in c1), F.concat([big, rim]), tuple(c1), "spin", (0, 0, 1), 40.0))
    ring = kit.gear(c2, (0.2, 1, 0.35), r2, m["gear"], teeth=14, thick=0.35, hole=0.8, spokes=0)
    lay.mover(F.Mover(tuple(int(v) for v in c2), ring, tuple(c2), "spin", (0.2, 1, 0.35), 60.0))
    small = kit.gear(c3, (0, 0, 1), r3, m["gear"], teeth=8, thick=0.4, hole=0.4, spokes=0)
    lay.mover(F.Mover(tuple(int(v) for v in c3), small, tuple(c3), "spin", (0, 0, -1), 25.0))
    cx, cy = c1[0], c1[1]
    out = []
    for dx in (-1.6, 0.0, 1.6):                                   # 매단 줄
        out.append(F.sweep(np.array([[cx + dx, Y0 + H, cz], [cx + dx, cy + 1.2, cz]]), 0.03, m["neon"], sides=4, step=2))
    return F.concat(out)


def faces(m, lay):
    out = []
    yt = Y0 + H
    out.append(F.plane((X0, Y0, ZS), (X1 - X0, 0, 0), (0, 0, ZB - ZS), m["tile"], tile=(3, 3)))
    out.append(F.plane((X0, yt, ZB), (X1 - X0, 0, 0), (0, 0, ZS - ZB), m["panel"], tile=(3, 3)))
    out.append(F.plane((X0, Y0, ZB), (X1 - X0, 0, 0), (0, H, 0), m["panel"], tile=(3, 3)))      # 뒤 벽
    for x in np.arange(X0, X1, 3.0):                                                           # 벽 이음
        out.append(F.box((x - 0.05, Y0, ZB), (x + 0.05, yt, ZB + 0.1), m["gear"]))
    out.append(F.box((X0, Y0 + 9.0, ZB), (X1, Y0 + 9.3, ZB + 0.4), m["gear"]))
    for x, f in ((X0, 1), (X1, -1)):                                                          # 옆 벽 + 빛 서랍 줄
        out.append(F.plane((x, Y0, ZS if f > 0 else ZB), (0, 0, (ZB - ZS) * f), (0, H, 0), m["panel"], tile=(3, 3)))
        q = drawers(m, -1.0, 1.0, Y0, Y0 + 11, 0.0, 14)
        for z in (3.0, 8.0, 13.0):
            out.append(q.rotate("y", 90 * f).translate((x + f * 0.05, 0, z)))
    out.append(drawers(m, OX - 9.4, OX - 5.8, Y0 + 2.6, Y0 + 5.9, ZB + 1.2, 6))               # 왼쪽 서랍장
    out.append(drawers(m, OX + 5.4, OX + 10.0, Y0 + 1.5, Y0 + 9.7, ZB + 1.2, 8))              # 오른쪽 큰 장
    out.append(F.box((OX - 8.5, Y0, ZB + 0.5), (OX - 5.1, Y0 + 2.4, ZB + 2.0), m["box"]))     # 파일 상자
    out.append(F.box((OX + 3.2, Y0, ZB + 0.5), (OX + 5.4, Y0 + 2.3, ZB + 2.0), m["box"]))
    # 빛나는 유리문 + 문틀 + 초승달
    out.append(F.box((OX + 0.0, Y0, ZB + 0.2), (OX + 2.9, Y0 + 5.6, ZB + 0.4), m["gear"], faces="xXY"))
    out.append(F.plane((OX + 0.2, Y0, ZB + 0.45), (2.5, 0, 0), (0, 5.3, 0), m["door"], tile=(3, 6)).tint((1, 1, 1), 0.7))
    t = np.linspace(0.6, 5.7, 20)
    moon = np.stack([OX + 1.8 + 0.45 * np.cos(t), Y0 + 3.4 + 0.45 * np.sin(t), np.full_like(t, ZB + 0.5)], 1)
    out.append(F.sweep(moon, 0.08, m["neon"], sides=4, step=0.2))
    # 콘솔 책상 (두 칸) + 화면 + 앞 빛 테두리
    out.append(F.box((OX - 4.6, Y0, ZB + 2.0), (OX + 1.2, Y0 + 1.7, ZB + 3.4), m["panel"]))
    out.append(F.box((OX - 4.7, Y0 + 1.7, ZB + 1.9), (OX + 1.3, Y0 + 1.85, ZB + 3.5), m["gear"]))
    out.append(F.box((OX - 4.6, Y0 + 0.05, ZB + 3.4), (OX + 1.2, Y0 + 0.15, ZB + 3.45), m["neon"]))
    out.append(F.box((OX - 1.7, Y0, ZB + 3.38), (OX - 1.6, Y0 + 1.7, ZB + 3.42), m["neon"]))
    out.append(F.box((OX - 3.6, Y0 + 1.85, ZB + 2.2), (OX - 2.2, Y0 + 2.8, ZB + 2.3), m["screen"]))
    # 도착 단
    out.append(F.box((OX - 3, Y0, 7.0), (OX + 4, Y0 + DAIS, ZS), m["panel"], faces="xXzY"))
    out.append(chandelier(lay, m))
    return out


def build(b, d):
    lay = b.form("technology")
    m = mats()
    fs = faces(m, lay)
    for j in range(6):
        fs.append(F.box((OX-6+j*1.8, Y0+.05, ZB+2), (OX-5.1+j*1.8, Y0+.55, ZB+2.65), m['box']))
    lights = [((OX - 2.7, Y0 + 8, 2.5), (0.8, 0.5, 1.1), 10.0), ((OX + 1.4, Y0 + 3, ZB + 1), (0.6, 0.4, 0.9), 7.0),
              ((OX + 7.7, Y0 + 5, ZB + 2), (0.4, 0.25, 0.6), 6.0)]
    kit.project_add(lay, CAM, m["art"], near=fs, lights=lights, ambient=(0.4, 0.34, 0.5),
                    glow_mats=[m["neon"], m["drawer"], m["door"], m["screen"]], min_facing=0.1)
    yt = int(Y0 + H)
    x0, x1 = int(X0) - 1, int(X1)
    d.fill(x0, Y0 - 1, int(ZB) - 1, x1, Y0 - 1, int(ZS), "minecraft:barrier")
    d.fill(x0, yt, int(ZB) - 1, x1, yt, int(ZS), "minecraft:barrier")
    for x in (x0, x1):
        d.fill(x, Y0, int(ZB) - 1, x, yt, int(ZS), "minecraft:barrier")
    d.fill(x0, Y0, int(ZS), x1, yt, int(ZS), "minecraft:barrier")
    d.fill(x0, Y0, int(ZB) - 1, x1, yt, int(ZB) - 1, "minecraft:barrier")
    d.fill(OX - 3, Y0, 9, OX + 3, Y0 + DAIS - 1, int(ZS) - 1, "minecraft:barrier")        # 도착 단
    kit.stair_collision(d, OX - 3, OX + 3, 8, 3, Y0 + DAIS, Y0)                           # 단 앞 계단
    steps = [F.box((OX - 3, Y0, z), (OX + 4, round((Y0 + DAIS - DAIS * (i + 1) / 6) * 2) / 2, z + 1), m["panel"],
                   faces="YZ") for i, z in enumerate(range(8, 2, -1))]
    lay.add(F.concat([q for q in steps if q.bounds()[1][1] > Y0]))
    d.fill(OX - 5, Y0, 2, OX + 1, Y0 + 1, 3, "minecraft:barrier")                        # 책상
    for x in range(int(X0) + 3, int(X1) - 1, 6):
        for z in (4, 11):
            if d.get(x, Y0 + 8, z) == "minecraft:air":
                d.set(x, Y0 + 8, z, "minecraft:light[level=10]")
    d.set_biome(OX - 40, -40, OX + 40, 40, "ruina:technology_room")
    return ARRIVE


PREVIEW_CAMS = [("방 옆에서", F.Camera((OX - 8.0, Y0 + 1.62, 12.0), 210.0, -5.0)),
                ("샹들리에 아래", F.Camera((OX - 1.0, Y0 + 1.62, 5.0), 170.0, -40.0))]


def preview(b):
    build(b, b.dim("technology"))
