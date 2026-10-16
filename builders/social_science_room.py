"""헤세드 방 (사회과학의 층 지정사서 방) — 자유 형체 판. reference/사회과학의 층 지정사서 방.png

푸른 어둠의 개인실: 격자 큰 창 너머 잠긴 도시(빛), 바닥에 비친 창살 그림자 빛, 왼쪽 소파와 쿠션, 낮은 탁자,
커피 드리퍼 놓인 긴 탁자, 뒤 선반(병·상자), 오른쪽 책장, 창틀 옆 푸른 빛줄. 도착: 한 칸 단 위에서 조금 내려다봄.
"""
from __future__ import annotations

import math

import numpy as np

from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 64
OX = 4000
ART = "reference/사회과학의 층 지정사서 방.png"
CAM = F.Camera((OX + 0.5, Y0 + 1 + 1.62, 11.0), 180.0, 14.0)
ARRIVE = (OX + 0.5, Y0 + 1, 11.0, 180.0, 14.0)
X0, X1, ZB, ZS, H = OX - 8.0, OX + 6.0, 0.0, 14.0, 10.0
SPACE = "social_science"


def mats():
    m = {}
    m["art"] = F.mat("hroom2_art", T.art("art/social_science_room", ART), emissive=True, flat=True, ao=False)
    m["floor"] = F.mat("sroom_floor", T.planks("sroom_floor", (20, 26, 34), (60, 74, 90), boards=4, seed=201),
                       emissive=True, flat=True, ao=False)
    m["wall"] = F.mat("sroom_wall", T.board("sroom_wall", (16, 20, 28), (44, 54, 70), w=16, h=32, seed=202),
                      emissive=True, flat=True, ao=False)
    m["window"] = F.mat("sroom_window", T.glow("sroom_window", (90, 190, 240)), emissive=True, flat=True, ao=False,
                        glow=2)
    m["neon"] = F.mat("sroom_neon", T.glow("sroom_neon", (60, 200, 255)), emissive=True, flat=True, ao=False, glow=2)
    m["sofa"] = F.mat("sroom_sofa", T.wood("sroom_sofa", (16, 20, 28), (46, 54, 70), seed=203, grain=False),
                      emissive=True, flat=True, ao=False)
    m["cushion"] = F.mat("sroom_cushion", T.wood("sroom_cushion", (50, 46, 66), (100, 90, 120), seed=204, grain=False),
                         emissive=True, flat=True, ao=False)
    m["table"] = F.mat("sroom_table", T.wood("sroom_table", (30, 26, 26), (76, 64, 60), seed=205), emissive=True,
                       flat=True, ao=False)
    blue = [(40, 60, 90), (60, 80, 110), (90, 80, 60), (50, 90, 70), (110, 100, 80)]
    m["shelf"] = [F.mat(f"sroom_shelf{i}", T.shelf(f"sroom_shelf{i}", blue, wood=(30, 38, 50), seed=206 + i,
                                                    dark_back=(8, 10, 16)), emissive=True, flat=True, ao=False)
                  for i in range(2)]
    m["shadow"] = F.mat("sroom_shadow", T.glow("sroom_shadow", (60, 170, 210)), layer="translucent", emissive=True,
                        flat=True, ao=False)
    m["glass"] = F.mat("sroom_glass", T.glow("sroom_glass", (220, 230, 240)), emissive=True, flat=True, ao=False)
    return m


def faces(m, rng):
    out = []
    yt = Y0 + H
    # 방 바닥 외곽의 입체 걸레받이: 평판 벽과 바닥 사이 이음부 마감.
    out.extend([F.box((X0, Y0, ZB), (X1, Y0+.22, ZB+.22), m["wall"]),
                F.box((X0, Y0, ZS-.22), (X1, Y0+.22, ZS), m["wall"]),
                F.box((X0-.22, Y0, ZB), (X0, Y0+.22, ZS), m["wall"]),
                F.box((X1, Y0, ZB), (X1+.22, Y0+.22, ZS), m["wall"])])
    out.append(F.plane((X0, Y0, ZS), (X1 - X0, 0, 0), (0, 0, ZB - ZS), m["floor"], tile=(2, 2)))
    out.append(F.plane((X0, yt, ZB), (X1 - X0, 0, 0), (0, 0, ZS - ZB), m["wall"], tile=(2, 2)))
    # 북쪽: 큰 격자 창 (왼쪽) + 뒤 선반 (오른쪽) + 아래 벽
    wa, wb = OX - 6.0, OX + 0.3
    out.append(F.plane((wa, Y0 + 2.6, ZB - 0.3), (wb - wa, 0, 0), (0, H - 2.6, 0), m["window"], tile=(3, 3)))
    for x in np.linspace(wa, wb, 5):
        out.append(F.box((x - 0.1, Y0 + 2.6, ZB - 0.25), (x + 0.1, yt, ZB), m["wall"]))
    out.append(F.box((wa, Y0 + 6.2, ZB - 0.25), (wb, Y0 + 6.4, ZB), m["wall"]))
    out.append(F.plane((X0, Y0, ZB), (wb - X0, 0, 0), (0, 2.6, 0), m["wall"], tile=(2, 2)))
    out.append(F.box((wa - 0.4, Y0 + 2.4, ZB), (wb + 0.2, Y0 + 2.7, ZB + 0.7), m["wall"]))    # 창턱 + 작은 화분들
    for x in np.arange(wa + 0.5, wb - 0.3, 0.7):
        out.append(F.box((x, Y0 + 2.7, ZB + 0.2), (x + 0.3, Y0 + 3.0, ZB + 0.5), m["glass"]).tint((0.3, 0.35, 0.4)))
    out.append(F.plane((wb, Y0, ZB), (X1 - wb, 0, 0), (0, H, 0), m["shelf"][0], tile=(1.6, 1.6)))
    for x, s in ((wa - 0.6, 1), (wa - 1.0, 1)):                                                # 창틀 옆 푸른 빛줄
        out.append(F.box((x, Y0 + 0.5, ZB + 0.1), (x + 0.12, yt, ZB + 0.3), m["neon"]))
    # 옆 벽: 왼쪽 벽 / 오른쪽 책장
    out.append(F.plane((X0, Y0, ZS), (0, 0, ZB - ZS), (0, H, 0), m["wall"], tile=(2, 2)))
    out.append(F.plane((X1, Y0, ZB), (0, 0, ZS - ZB), (0, H, 0), m["shelf"][1], tile=(1.6, 1.6)))
    # 긴 탁자 + 커피 드리퍼
    out.append(F.box((OX + 0.5, Y0 + 1.3, 1.6), (OX + 4.0, Y0 + 1.42, 2.8), m["table"]))
    for x in (OX + 0.6, OX + 3.8):
        out.append(F.box((x, Y0, 1.7), (x + 0.12, Y0 + 1.3, 2.7), m["table"]))
    out.append(F.revolve([(0.3, Y0 + 1.42), (0.35, Y0 + 1.8), (0.5, Y0 + 2.1)], m["glass"], segs=12, center=(OX + 1.9, 0, 2.2),
                         tiles_around=3, tile_up=1.0))
    # 소파 (왼쪽) + 쿠션 + 낮은 탁자
    out.append(F.box((X0, Y0, 5.0), (X0 + 2.6, Y0 + 0.7, 10.5), m["sofa"]))
    out.append(F.box((X0, Y0 + 0.7, 5.0), (X0 + 0.8, Y0 + 2.0, 10.5), m["sofa"]))
    out.append(F.box((X0, Y0, 4.4), (X0 + 2.8, Y0 + 1.6, 5.0), m["sofa"]))
    for z in (6.0, 7.6):
        out.append(F.ellipsoid((X0 + 1.2, Y0 + 1.2, z), (0.25, 0.55, 0.6), m["cushion"], 10, 5).rotate(
            "z", -20, origin=(X0 + 1.2, Y0 + 1.2, z)))
    out.append(F.box((OX - 4.8, Y0 + 0.55, 6.5), (OX - 2.2, Y0 + 0.65, 8.5), m["table"]))
    for x in (OX - 4.7, OX - 2.4):
        out.append(F.box((x, Y0, 6.6), (x + 0.12, Y0 + 0.55, 8.4), m["table"]))
    # 바닥의 창살 그림자 빛 (반투명 판)
    for k in range(4):
        x = OX - 4.0 + k * 1.6
        out.append(F.Quads(np.array([[[x, Y0 + 0.02, 6.0], [x + 1.3, Y0 + 0.02, 6.0], [x + 3.4, Y0 + 0.02, 1.0],
                                      [x + 2.1, Y0 + 0.02, 1.0]]]), np.array([[[0, 0], [0.99, 0], [0.99, 0.99], [0, 0.99]]]),
                           M=m["shadow"]).tint((1, 1, 1), 0.35))
    out.append(F.box((OX - 2, Y0, 10.0), (OX + 3, Y0 + 1, ZS), m["wall"], faces="xXzY"))       # 도착 단
    return out


def build(b, d):
    lay = b.form("social_science")
    rng = np.random.default_rng(1721)
    m = mats()
    fs = faces(m, rng)
    # 커피 드리퍼를 받치는 입체 받침과 유리 용기.
    fs.extend([F.box((OX+1.2,Y0+1.05,2.6),(OX+2,Y0+1.12,3.4),m['table']),
               F.box((OX+1.35,Y0+1.12,2.75),(OX+1.85,Y0+1.65,3.25),m['glass'])])
    for y in (Y0+3.5,Y0+5.5):
        fs.append(F.box((OX+1,y,ZB+.18),(X1-.4,y+.14,ZB+.8),m['wall']))
    for j in range(6):
        fs.append(F.box((OX-6+j*2, Y0+.05, ZB+2), (OX-5.4+j*2, Y0+.35, ZB+2.5), m['table']))
    lights = [((OX - 3, Y0 + 5, ZB - 2), (0.4, 0.9, 1.2), 14.0)]
    kit.project_add(lay, CAM, m["art"], near=fs, lights=lights, ambient=(0.3, 0.36, 0.46),
                    glow_mats=[m["window"], m["neon"], m["shadow"]], min_facing=0.1)
    yt = int(Y0 + H)
    x0, x1 = int(X0) - 1, int(X1)
    d.fill(x0, Y0 - 1, int(ZB) - 1, x1, Y0 - 1, int(ZS), "minecraft:barrier")
    d.fill(x0, yt, int(ZB) - 1, x1, yt, int(ZS), "minecraft:barrier")
    for x in (x0, x1):
        d.fill(x, Y0, int(ZB) - 1, x, yt, int(ZS), "minecraft:barrier")
    d.fill(x0, Y0, int(ZS), x1, yt, int(ZS), "minecraft:barrier")
    d.fill(x0, Y0, int(ZB) - 1, x1, yt, int(ZB) - 1, "minecraft:barrier")
    d.fill(OX - 2, Y0, 10, OX + 2, Y0, int(ZS) - 1, "minecraft:barrier")
    d.fill(OX - 2, Y0, 9, OX + 2, Y0, 9, F.HALF_SOLID)
    d.fill(int(X0), Y0, 5, int(X0) + 2, Y0, 10, F.HALF_SOLID)
    d.fill(OX + 0, Y0, 1, OX + 3, Y0, 2, "minecraft:barrier")
    for x in range(int(X0) + 2, int(X1), 5):
        for z in (4, 10):
            if d.get(x, Y0 + 7, z) == "minecraft:air":
                d.set(x, Y0 + 7, z, "minecraft:light[level=9]")
    d.set_biome(OX - 40, -40, OX + 40, 40, "ruina:social_science_room")
    return ARRIVE


PREVIEW_CAMS = [("방 옆", F.Camera((OX + 4.0, Y0 + 1.62, 12.0), 150.0, 5.0))]


def preview(b):
    build(b, b.dim("social_science"))
