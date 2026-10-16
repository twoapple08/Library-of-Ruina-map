"""게부라 방 (언어의 층 지정사서 방) — 자유 형체 판. reference/언어의 층 지정사서 방.png

어두운 서재: 큰 창 너머 용광로 빛과 쇳물 국자(창 밖 빛 판), 왼쪽 책장, 오른쪽 큰 검은 소파, 재떨이·컵 놓인 낮은 탁자,
바닥에 흩어진 종이. 도착: 탁자 바로 앞에서 북쪽을 조금 내려다봄.
"""
from __future__ import annotations

import math

import numpy as np

from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 64
OX = 4000
ART = "reference/언어의 층 지정사서 방.png"
CAM = F.Camera((OX + 0.5, Y0 + 1.62, 10.0), 180.0, 12.0)
ARRIVE = (OX + 0.5, Y0, 10.0, 180.0, 12.0)
X0, X1, ZB, ZS, H = OX - 10.0, OX + 10.0, 1.0, 14.0, 10.0
SPACE = "language"
UP = np.array([0, 1.0, 0])


def mats():
    m = {}
    m["art"] = F.mat("groom_art", T.art("art/language_room", ART), emissive=True, flat=True, ao=False)
    dark = [(70, 40, 30), (50, 34, 30), (90, 60, 44), (44, 40, 44), (40, 60, 80)]
    m["shelf"] = [F.mat(f"groom_shelf{i}", T.shelf(f"groom_shelf{i}", dark, wood=(46, 30, 24), seed=180 + i,
                                                    dark_back=(14, 10, 8)), emissive=True, flat=True, ao=False)
                  for i in range(2)]
    m["wood"] = F.mat("groom_wood", T.planks("groom_wood", (30, 22, 20), (80, 56, 46), boards=4, seed=182),
                      emissive=True, flat=True, ao=False)
    m["sofa"] = F.mat("groom_sofa", T.wood("groom_sofa", (16, 14, 16), (52, 46, 50), seed=183, grain=False),
                      emissive=True, flat=True, ao=False)
    m["window"] = F.mat("groom_window", T.glow("groom_window", (255, 120, 50)), emissive=True, flat=True, ao=False,
                        glow=1)
    m["frame"] = F.mat("groom_frame", T.flat("groom_frame", (24, 16, 14)), emissive=True, flat=True, ao=False)
    m["paper"] = F.mat("groom_paper", T.paper("groom_paper", c=(200, 170, 150), seed=184), layer="cutout",
                       emissive=True, flat=True, ao=False)
    m["glass"] = F.mat("groom_glass", T.glow("groom_glass", (220, 220, 230)), emissive=True, flat=True, ao=False)
    return m


def faces(m, rng):
    out = []
    yt = Y0 + H
    # 방 바닥 외곽의 입체 걸레받이: 평판 벽과 바닥 사이 이음부 마감.
    out.extend([F.box((X0, Y0, ZB), (X1, Y0+.22, ZB+.22), m["frame"]),
                F.box((X0, Y0, ZS-.22), (X1, Y0+.22, ZS), m["frame"]),
                F.box((X0-.22, Y0, ZB), (X0, Y0+.22, ZS), m["frame"]),
                F.box((X1, Y0, ZB), (X1+.22, Y0+.22, ZS), m["frame"])])
    out.append(F.plane((X0, Y0, ZS), (X1 - X0, 0, 0), (0, 0, ZB - ZS), m["wood"], tile=(2, 2)))
    out.append(F.plane((X0, yt, ZB), (X1 - X0, 0, 0), (0, 0, ZS - ZB), m["frame"], tile=(2, 2)))
    # 북쪽: 왼쪽 책장 / 큰 창 (창살 십자) / 오른쪽 벽
    out.append(F.plane((X0, Y0, ZB), (OX - 4.0 - X0, 0, 0), (0, H, 0), m["shelf"][0], tile=(1.3, 1.3)))
    out.append(F.plane((OX - 4.0, Y0, ZB - 0.4), (12.0, 0, 0), (0, H, 0), m["window"], tile=(4, 4)))
    for x in (OX - 4.0, OX + 0.0, OX + 4.0, OX + 8.0):
        out.append(F.box((x - 0.2, Y0, ZB - 0.3), (x + 0.2, yt, ZB), m["frame"]))
    for y in (Y0 + 1.4, Y0 + 5.6):
        out.append(F.box((OX - 4.0, y - 0.2, ZB - 0.3), (OX + 8.0, y + 0.2, ZB), m["frame"]))
    out.append(F.plane((OX + 8.0, Y0, ZB), (X1 - OX - 8.0, 0, 0), (0, H, 0), m["frame"], tile=(2, 2)))
    for x, f in ((X0, 1), (X1, -1)):
        out.append(F.plane((x, Y0, ZS if f > 0 else ZB), (0, 0, (ZB - ZS) * f), (0, H, 0), m["shelf"][1], tile=(1.3, 1.3)))
    # 큰 검은 소파 (등받이 + 앉는 판 + 팔걸이 + 방석 셋)
    sx0, sx1, sz0, sz1 = OX + 1.0, OX + 10.0, 3.0, 6.4
    out.append(F.box((sx0, Y0, sz0), (sx1, Y0 + 2.3, sz0 + 1.1), m["sofa"]))
    out.append(F.box((sx0, Y0, sz0 + 1.1), (sx1, Y0 + 0.75, sz1), m["sofa"]))
    for k in range(3):
        a = sx0 + 0.3 + k * 2.9
        out.append(F.box((a, Y0 + 0.75, sz0 + 1.2), (a + 2.8, Y0 + 1.05, sz1 - 0.1), m["sofa"]).tint((1.2, 1.2, 1.2)))
    out.append(F.box((sx0 - 0.9, Y0, sz0), (sx0, Y0 + 1.3, sz1), m["sofa"]))
    # 낮은 탁자 + 재떨이 + 컵 + 종이
    tx0, tx1, tz0, tz1 = OX - 1.4, OX + 4.6, 6.9, 8.25
    out.append(F.box((tx0, Y0 + 0.4, tz0), (tx1, Y0 + 0.5, tz1), m["frame"]))
    for x in (tx0 + 0.1, tx1 - 0.25):
        for z in (tz0 + 0.1, tz1 - 0.25):
            out.append(F.box((x, Y0, z), (x + 0.15, Y0 + 0.4, z + 0.15), m["frame"]))
    out.append(F.revolve([(0.01, Y0 + 0.5), (0.35, Y0 + 0.5), (0.4, Y0 + 0.58)], m["glass"], segs=16,
                         center=(OX + 0.4, 0, 7.5), tiles_around=4, tile_up=1.0))
    out.append(F.revolve([(0.12, Y0 + 0.5), (0.12, Y0 + 0.75), (0.01, Y0 + 0.75)], m["glass"], segs=10,
                         center=(OX + 2.0, 0, 7.4), tiles_around=2, tile_up=1.0))
    for _ in range(40):                                          # 흩어진 종이
        x, z = rng.uniform(X0 + 0.5, X1 - 0.5), rng.uniform(ZB + 1, ZS - 1)
        y = Y0 + 0.51 if (tx0 < x < tx1 and tz0 < z < tz1) else Y0 + 0.01
        out.append(F.plane((-0.25, y, -0.18), (0.5, 0, 0), (0, 0, 0.36), m["paper"]).flipped().rotate(
            "y", rng.uniform(0, 180)).translate((x, 0, z)))
    return out


def build(b, d):
    lay = b.form("language")
    rng = np.random.default_rng(1621)
    m = mats()
    fs = faces(m, rng)
    # 낮은 탁자의 컵: 받침, 몸통, 윗테.
    fs.extend([F.box((OX+.1,Y0+.58,7.1),(OX+.8,Y0+.64,7.8),m['frame']),
               F.box((OX+.2,Y0+.64,7.2),(OX+.7,Y0+.98,7.7),m['glass']),
               F.box((OX+.15,Y0+.98,7.15),(OX+.75,Y0+1.02,7.75),m['frame'])])
    for y in (Y0+2,Y0+4,Y0+6):
        fs.append(F.box((X0+.15,y,ZB+.2),(OX-4.2,y+.15,ZB+.8),m['frame']))
    for j in range(5):
        fs.append(F.box((OX-5+j*2, Y0+.06, ZB+2), (OX-4.4+j*2, Y0+.12, ZB+2.5), m['paper']))
    lights = [((OX + 2.0, Y0 + 4, ZB - 2), (1.4, 0.6, 0.25), 14.0)]
    kit.project_add(lay, CAM, m["art"], near=fs, lights=lights, ambient=(0.32, 0.24, 0.22), glow_mats=[m["window"]],
                    min_facing=0.1)
    yt = int(Y0 + H)
    x0, x1 = int(X0) - 1, int(X1)
    d.fill(x0, Y0 - 1, int(ZB) - 1, x1, Y0 - 1, int(ZS), "minecraft:barrier")
    d.fill(x0, yt, int(ZB) - 1, x1, yt, int(ZS), "minecraft:barrier")
    for x in (x0, x1):
        d.fill(x, Y0, int(ZB) - 1, x, yt, int(ZS), "minecraft:barrier")
    d.fill(x0, Y0, int(ZS), x1, yt, int(ZS), "minecraft:barrier")
    d.fill(x0, Y0, int(ZB) - 1, x1, yt, int(ZB) - 1, "minecraft:barrier")
    d.fill(OX + 1, Y0, 3, OX + 9, Y0, 6, F.HALF_SOLID)                                   # 소파 (앉는 판)
    d.fill(OX + 1, Y0, 3, OX + 9, Y0 + 1, 3, "minecraft:barrier")                        # 등받이
    d.fill(OX - 2, Y0, 7, OX + 4, Y0, 7, F.HALF_SOLID)                                   # 탁자
    for x in range(int(X0) + 3, int(X1) - 1, 6):
        for z in (4, 11):
            if d.get(x, Y0 + 7, z) == "minecraft:air":
                d.set(x, Y0 + 7, z, "minecraft:light[level=9]")
    d.set_biome(OX - 40, -40, OX + 40, 40, "ruina:language_room")
    return ARRIVE


PREVIEW_CAMS = [("방 남쪽에서", F.Camera((OX - 6.0, Y0 + 1.62, 13.0), 200.0, 5.0))]


def preview(b):
    build(b, b.dim("language"))
