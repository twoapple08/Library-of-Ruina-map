"""호드 방 (문학의 층 지정사서 방) — 자유 형체 판. reference/문학의 층 지정사서 방.png

왼쪽 벽을 따라 깊이로 이어진 키 큰 책장 칸들(나무 테), 천장에 크기 제각각 물방울 전구(살랑 흔들림),
가운데 오른쪽 긴 책상과 의자, 오른쪽 팔각 문 너머 빛 속으로 이어지는 긴 통로, 반짝이는 나무 바닥.
도착: 방 남쪽에서 북북서를 봄 (통로 소실점이 화면 오른쪽).
"""
from __future__ import annotations

import math

import numpy as np

from tools import artfit as A
from tools import form_textures as T
from tools import forms as F

from . import kit
from .literature import bulb_mesh

Y0 = 64
OX = 4000
ART = "reference/문학의 층 지정사서 방.png"
CAM = F.Camera((OX + 0.5, Y0 + 1.62, 12.0), 156.5, 3.0)
ARRIVE = (OX + 0.5, Y0, 12.0, 156.5, 3.0)
X0, X1, ZB, ZS, H = OX - 4.0, OX + 4.5, -12.0, 16.0, 13.0
CORR = (OX + 1.6, OX + 4.2)             # 오른쪽 통로 (북쪽 벽 뚫림) x
SPACE = "literature"
UP = np.array([0, 1.0, 0])


def mats():
    m = {}
    m["art"] = F.mat("lroom_art", T.art("art/literature_room", ART), emissive=True, flat=True, ao=False)
    warm = [(130, 70, 46), (110, 56, 38), (156, 100, 66), (90, 50, 36), (170, 120, 80)]
    m["shelf"] = [F.mat(f"lroom_shelf{i}", T.shelf(f"lroom_shelf{i}", warm, wood=(120, 70, 44), seed=120 + i,
                                                    dark_back=(30, 16, 10)), emissive=True, flat=True, ao=False)
                  for i in range(3)]
    m["wood"] = F.mat("lroom_wood", T.wood("lroom_wood", (60, 34, 22), (140, 90, 56), seed=123), emissive=True,
                      flat=True, ao=False)
    m["floor"] = F.mat("lroom_floor", T.planks("lroom_floor", (60, 44, 34), (140, 106, 80), boards=4, seed=124),
                       emissive=True, flat=True, ao=False)
    m["dark"] = F.mat("lroom_dark", T.wood("lroom_dark", (20, 14, 12), (48, 36, 30), seed=125), emissive=True,
                      flat=True, ao=False)
    m["light"] = F.mat("lroom_light", T.glow("lroom_light", (255, 238, 214)), emissive=True, flat=True, ao=False, glow=3)
    m["glass"] = F.mat("lit_glass", T.glow("lit_glass", (255, 236, 210)), layer="translucent", emissive=True,
                       flat=True, ao=False)
    m["bulb"] = F.mat("lit_bulb", T.glow("lit_bulb", (255, 190, 110)), emissive=True, flat=True, ao=False, glow=3)
    m["wire"] = F.mat("lit_wire", T.flat("lit_wire", (30, 26, 26)), emissive=True, flat=True, ao=False)
    return m


def faces(m, rng):
    out = []
    yt = Y0 + H
    # 방 바닥 외곽의 입체 걸레받이: 평판 벽과 바닥 사이 이음부 마감.
    out.extend([F.box((X0, Y0, ZB), (X1, Y0+.22, ZB+.22), m["wood"]),
                F.box((X0, Y0, ZS-.22), (X1, Y0+.22, ZS), m["wood"]),
                F.box((X0-.22, Y0, ZB), (X0, Y0+.22, ZS), m["wood"]),
                F.box((X1, Y0, ZB), (X1+.22, Y0+.22, ZS), m["wood"])])
    out.append(F.plane((X0 - 8, Y0, ZS), (X1 - X0 + 8, 0, 0), (0, 0, ZB - ZS), m["floor"], tile=(3, 3)))
    out.append(F.plane((X0 - 8, yt, ZB), (X1 - X0 + 8, 0, 0), (0, 0, ZS - ZB), m["dark"], tile=(3, 3)))
    # 왼쪽(서쪽): 깊이로 이어진 책장 칸 — 칸마다 앞으로 튀어나온 나무 테 (원화의 계단처럼 물러나는 책장)
    for i, z in enumerate(np.arange(ZB, ZS, 3.2)):
        x = X0 - (0.0 if i % 2 else 0.6)
        out.append(F.plane((x, Y0, z + 3.0), (0, 0, -3.0), (0, H - 0.5, 0), m["shelf"][i % 3], tile=(1.3, 1.3))
                   .rotate("y", 0).transform(np.diag([1, 1, 1.0])))
        out.append(F.box((x - 0.2, Y0, z + 2.9), (x + 1.2, yt, z + 3.2), m["wood"]))           # 칸 사이 테
        for y in np.arange(Y0 + 1.3, yt, 1.3):
            out.append(F.box((x, y - 0.06, z), (x + 0.8, y + 0.06, z + 2.9), m["wood"], faces="yYX"))
    # 오른쪽(동쪽): 책장 + 통로 입구
    out.append(F.plane((X1, Y0, ZB + 4), (0, 0, ZS - ZB - 4), (0, H, 0), m["shelf"][1], tile=(1.3, 1.3)))
    # 북쪽 벽: 책장 (통로 자리 비움) + 통로 (팔각 단면이 줄지어 빛 속으로)
    ca, cb = CORR
    out.append(F.plane((X0, Y0, ZB), (ca - X0, 0, 0), (0, H, 0), m["shelf"][2], tile=(1.3, 1.3)))
    out.append(F.plane((cb, Y0, ZB), (X1 - cb, 0, 0), (0, H, 0), m["shelf"][0], tile=(1.3, 1.3)))
    out.append(F.plane((ca, Y0 + 7, ZB), (cb - ca, 0, 0), (0, H - 7, 0), m["dark"], tile=(2, 2)))
    for k in range(10):
        z = ZB - 2 - k * 4
        w, hgt = (cb - ca) * (1 + 0.15 * k), 7 + 0.6 * k
        cx = (ca + cb) / 2 + 0.3 * k
        ring = [(cx - w / 2, Y0), (cx - w / 2, Y0 + hgt * 0.8), (cx - w / 3, Y0 + hgt), (cx + w / 3, Y0 + hgt),
                (cx + w / 2, Y0 + hgt * 0.8), (cx + w / 2, Y0)]
        out.append(F.sweep(np.array([[x, y, z] for x, y in ring]), 0.35, m["wood"], sides=4, step=1.0)
                   .tint((1.4, 1.3, 1.15)))
    out.append(F.plane((ca - 2, Y0, ZB - 42), (cb - ca + 8, 0, 0), (0, 14, 0), m["light"], tile=(4, 4)))
    out.append(F.plane((ca - 1, Y0, ZB), (cb - ca + 6, 0, 0), (0, 0, -42), m["floor"], tile=(3, 3)).flipped()
               .tint((1.6, 1.45, 1.25)))
    # 책상 + 의자 (원화: 오른쪽 가운데)
    dx0, dx1, dz0, dz1 = OX - 0.4, OX + 2.0, 5.0, 8.6
    out.append(F.box((dx0, Y0 + 0.85, dz0), (dx1, Y0 + 1.0, dz1), m["wood"]))
    for x in (dx0 + 0.1, dx1 - 0.2):
        for z in (dz0 + 0.1, dz1 - 0.2):
            out.append(F.box((x, Y0, z), (x + 0.12, Y0 + 0.85, z + 0.12), m["dark"]))
    for x, z in ((dx0 - 0.6, 6.0), (dx0 - 0.6, 7.8), (dx1 + 0.1, 6.0), (dx1 + 0.1, 7.6)):
        out.append(F.box((x, Y0 + 0.45, z - 0.3), (x + 0.5, Y0 + 0.55, z + 0.3), m["wood"]))
        out.append(F.box((x + (0.42 if x < dx0 else 0), Y0 + 0.55, z - 0.3), (x + (0.5 if x < dx0 else 0.08), Y0 + 1.3,
                                                                              z + 0.3), m["wood"]))
    for i in range(3):
        out.append(F.box((dx0 + 0.3 + i * 0.3, Y0 + 1.0, dz0 + 0.4), (dx0 + 0.55 + i * 0.3, Y0 + 1.25 + 0.1 * i,
                                                                        dz0 + 0.8), m["shelf"][i]))
    return out


def build(b, d):
    lay = b.form("literature")
    rng = np.random.default_rng(1101)
    m = mats()
    fs = faces(m, rng)
    # 독서용 탁자 위의 낱권 책과 종이 두께.
    fs.extend([F.box((OX+.1,Y0+1.05,5.5),(OX+.9,Y0+1.2,6.6),m['wood']),F.box((OX+.15,Y0+1.2,5.55),(OX+.85,Y0+1.24,6.55),m['glass'])])
    for z in (-9,-5,-1,3,7):
        fs.append(F.box((X0+.05,Y0+5,z),(X0+.9,Y0+5.12,z+2),m['wood']))
    for j in range(6):
        fs.append(F.box((OX-6+j*2, Y0+.05, 2), (OX-5.4+j*2, Y0+.38, 2.8), m['wood']))
    lights = [((CORR[0] + 1.3, Y0 + 5, ZB - 20), (1.3, 1.1, 0.85), 30.0), ((OX, Y0 + 10, 4), (0.7, 0.45, 0.25), 14.0)]
    kit.project_add(lay, CAM, m["art"], near=fs, lights=lights, ambient=(0.42, 0.32, 0.26),
                    glow_mats=[m["light"], m["bulb"], m["glass"]], min_facing=0.1)
    # 천장 물방울 전구 (흔들림)
    for _ in range(26):
        x, z = rng.uniform(X0 + 0.5, X1 - 0.5), rng.uniform(ZB + 1, ZS - 2)
        size = rng.uniform(0.15, 0.45)
        wire = rng.uniform(0.5, 4.0)
        y = Y0 + H - 0.2 - wire - size * 3.2
        mesh = bulb_mesh(m, (x, y, z), size, wire)
        lay.mover(F.Mover((int(math.floor(x)), int(y), int(math.floor(z))), mesh, (x, Y0 + H - 0.2, z), "swing",
                          (rng.uniform(-1, 1), 0, rng.uniform(-1, 1)), period=rng.uniform(5, 9), amp=rng.uniform(2, 4),
                          phase=rng.random()))
    yt = int(Y0 + H)
    x0, x1 = int(X0) - 2, int(X1) + 1
    d.fill(x0, Y0 - 1, int(ZB) - 44, x1 + 6, Y0 - 1, int(ZS), "minecraft:barrier")
    d.fill(x0, yt, int(ZB), x1, yt, int(ZS), "minecraft:barrier")
    for x in (x0, x1):
        d.fill(x, Y0, int(ZB), x, yt, int(ZS), "minecraft:barrier")
    d.fill(x0, Y0, int(ZS), x1, yt, int(ZS), "minecraft:barrier")
    d.fill(x0, Y0, int(ZB) - 1, x1, yt, int(ZB) - 1, "minecraft:barrier")
    ca, cb = int(CORR[0]), int(CORR[1])
    d.fill(ca, Y0, int(ZB) - 1, cb, Y0 + 6, int(ZB) - 1, "minecraft:air")       # 통로로 걸어 들어감
    for x in (ca - 1, cb + 4):
        d.fill(x, Y0, int(ZB) - 44, x, Y0 + 12, int(ZB) - 1, "minecraft:barrier")
    d.fill(ca - 1, Y0, int(ZB) - 44, cb + 4, Y0 + 12, int(ZB) - 44, "minecraft:barrier")
    d.fill(OX, Y0, 5, OX + 1, Y0, 8, "minecraft:barrier")                         # 책상
    for x in range(int(X0), int(X1) + 1, 4):
        for z in range(int(ZB) + 2, int(ZS), 7):
            if d.get(x, Y0 + 8, z) == "minecraft:air":
                d.set(x, Y0 + 8, z, "minecraft:light[level=11]")
    d.set_biome(OX - 40, -60, OX + 40, 40, "ruina:literature_room")
    return ARRIVE


PREVIEW_CAMS = [("방 북쪽에서 남쪽", F.Camera((OX + 0.5, Y0 + 1.62, -8.0), 0.0, 0.0)),
                ("통로 입구", F.Camera((OX + 2.5, Y0 + 1.62, -9.0), 180.0, 0.0))]


def preview(b):
    build(b, b.dim("literature"))
