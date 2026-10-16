"""네짜흐 방 (예술의 층 지정사서 방) — 자유 형체 판. reference/예술의 층 지정사서 방.png

덩굴·뿌리 감긴 책장과 사다리, 책 더미, 책장 위·바닥의 작은 빛나는 정령(살짝 오르내림), 오른쪽 빛나는 큰 문 안 이젤 그림
(실크해트·눈 셋 괴생물체), 가운데 왼쪽 작은 빛나는 문, 반딧불이. 도착: 남쪽 두 칸 단에서 북쪽.
"""
from __future__ import annotations

import math

import numpy as np

from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 64
OX = 4000
DAIS = 2
ART = "reference/예술의 층 지정사서 방.png"
CAM = F.Camera((OX + 0.5, Y0 + DAIS + 1.62, 8.0), 180.0, 0.0)
ARRIVE = (OX + 0.5, Y0 + DAIS, 8.0, 180.0, 0.0)
X0, X1, ZB, ZS, H = OX - 10.0, OX + 11.0, 0.0, 14.0, 13.0
SPACE = "art"
UP = np.array([0, 1.0, 0])


def mats():
    m = {}
    m["art"] = F.mat("aroom_art", T.art("art/art_room", ART), emissive=True, flat=True, ao=False)
    green = [(50, 60, 40), (70, 74, 50), (90, 96, 60), (60, 50, 36), (40, 50, 50)]
    m["shelf"] = [F.mat(f"aroom_shelf{i}", T.shelf(f"aroom_shelf{i}", green, wood=(54, 50, 30), seed=140 + i,
                                                    dark_back=(14, 16, 10)), emissive=True, flat=True, ao=False)
                  for i in range(3)]
    m["root"] = F.mat("aroom_root", T.bark("aroom_root", (30, 30, 18), (80, 76, 44), seed=143), emissive=True, flat=True,
                      ao=False)
    m["wood"] = F.mat("aroom_wood", T.wood("aroom_wood", (30, 26, 16), (80, 70, 40), seed=144), emissive=True, flat=True,
                      ao=False)
    m["floor"] = F.mat("aroom_floor", T.planks("aroom_floor", (34, 30, 18), (84, 74, 44), boards=4, seed=145),
                       emissive=True, flat=True, ao=False)
    m["door"] = F.mat("aroom_door", T.glow("aroom_door", (240, 230, 110)), emissive=True, flat=True, ao=False, glow=6)
    m["canvas"] = F.mat("aroom_canvas", T.flat("aroom_canvas", (200, 200, 190)), emissive=True, flat=True, ao=False)
    m["ink"] = F.mat("aroom_ink", T.flat("aroom_ink", (40, 40, 36)), emissive=True, flat=True, ao=False)
    m["spirit"] = F.mat("aroom_spirit", T.glow("aroom_spirit", (220, 255, 120)), emissive=True, flat=True, ao=False,
                        glow=6)
    m["book"] = [F.mat(f"aroom_book{i}", T.flat(f"aroom_book{i}", c), emissive=True, flat=True, ao=False)
                 for i, c in enumerate([(70, 80, 70), (90, 80, 60), (60, 60, 70), (110, 100, 80)])]
    return m


def spirit_mesh(m, x, y, z, s=0.35):
    """작은 정령: 둥근 머리 + 조금 넓은 몸, 검은 눈 둘."""
    head = F.ellipsoid((x, y + s * 1.55, z), (s * 0.55, s * 0.5, s * 0.5), m["spirit"], 10, 6)
    body = F.revolve([(0.02, y), (s * 0.5, y + 0.05), (s * 0.42, y + s * 0.6), (s * 0.3, y + s * 1.1), (0.02, y + s * 1.2)],
                     m["spirit"], segs=10, center=(x, 0, z), tiles_around=2, tile_up=2.0)
    eyes = F.concat([F.box((x + dx - 0.04, y + s * 1.55, z + s * 0.47), (x + dx + 0.04, y + s * 1.68, z + s * 0.5),
                           m["ink"]) for dx in (-0.12, 0.12)])
    return F.concat([head, body, eyes])


def faces(m, rng):
    out = []
    yt = Y0 + H
    # 방 바닥 외곽의 입체 걸레받이: 평판 벽과 바닥 사이 이음부 마감.
    out.extend([F.box((X0, Y0, ZB), (X1, Y0+.22, ZB+.22), m["wood"]),
                F.box((X0, Y0, ZS-.22), (X1, Y0+.22, ZS), m["wood"]),
                F.box((X0-.22, Y0, ZB), (X0, Y0+.22, ZS), m["wood"]),
                F.box((X1, Y0, ZB), (X1+.22, Y0+.22, ZS), m["wood"])])
    out.append(F.plane((X0, Y0, ZS), (X1 - X0, 0, 0), (0, 0, ZB - ZS), m["floor"], tile=(3, 3)))
    out.append(F.plane((X0, yt, ZB), (X1 - X0, 0, 0), (0, 0, ZS - ZB), m["wood"], tile=(3, 3)))
    # 북쪽 벽: 책장 (큰 문·작은 문 자리 비움) + 선반 + 뿌리
    for a, b in ((X0, OX - 4.3), (OX - 3.4, OX + 3.2), (OX + 6.6, X1)):
        out.append(F.plane((a, Y0, ZB), (b - a, 0, 0), (0, H, 0), m["shelf"][int(rng.integers(3))], tile=(1.4, 1.4)))
        for y in np.arange(Y0 + 1.4, yt, 1.4):
            out.append(F.box((a, y - 0.07, ZB), (b, y + 0.07, ZB + 0.5), m["wood"], faces="yYZ"))
    # 작은 빛나는 문 (가운데 왼쪽) + 위 책장
    out.append(F.plane((OX - 4.3, Y0, ZB - 0.3), (0.9, 0, 0), (0, 4.8, 0), m["door"]))
    out.append(F.plane((OX - 4.3, Y0 + 4.8, ZB), (0.9, 0, 0), (0, H - 4.8, 0), m["shelf"][0], tile=(1.4, 1.4)))
    # 큰 빛나는 문 + 이젤 그림 (눈 셋 괴생물체)
    out.append(F.plane((OX + 3.2, Y0, ZB - 0.5), (3.4, 0, 0), (0, 8.4, 0), m["door"], tile=(2, 4)))
    out.append(F.plane((OX + 3.2, Y0 + 8.4, ZB), (3.4, 0, 0), (0, H - 8.4, 0), m["shelf"][1], tile=(1.4, 1.4)))
    ex, ez = OX + 5.2, ZB + 0.4
    out.append(F.plane((ex - 1.1, Y0 + 3.2, ez), (2.2, 0, 0), (0, 4.0, 0), m["canvas"]))
    out.append(F.plane((ex - 0.35, Y0 + 3.7, ez + 0.02), (0.7, 0, 0), (0, 2.6, 0), m["ink"]))
    out.append(F.plane((ex - 0.25, Y0 + 6.3, ez + 0.02), (0.5, 0, 0), (0, 0.6, 0), m["ink"]))
    for lx in (-0.9, 0.0, 0.9):
        out.append(F.sweep(np.array([[ex + lx * 0.3, Y0 + 3.3, ez + 0.1], [ex + lx, Y0, ez + 0.6]]), 0.05, m["wood"],
                           sides=4, step=2.0))
    # 사다리 둘
    for x0 in (OX - 8.8, OX - 1.6):
        for s in (0.0, 1.3):
            out.append(F.box((x0 + s, Y0, ZB + 0.6), (x0 + s + 0.12, Y0 + 8, ZB + 0.72), m["wood"]))
        for y in np.arange(Y0 + 0.5, Y0 + 8, 0.6):
            out.append(F.box((x0, y, ZB + 0.6), (x0 + 1.4, y + 0.08, ZB + 0.68), m["wood"]))
    # 뿌리·덩굴: 벽을 타고 내려옴
    for _ in range(16):
        x = rng.uniform(X0 + 0.5, X1 - 0.5)
        pts = [np.array([x, yt, ZB + 0.6])]
        for k in range(10):
            pts.append(pts[-1] + np.array([rng.uniform(-0.8, 0.8), -rng.uniform(0.6, 1.4), rng.uniform(-0.05, 0.1)]))
        out.append(F.sweep(np.array(pts), lambda s: 0.22 * (1 - s) + 0.05, m["root"], sides=5, step=0.5))
    # 책 더미
    for _ in range(26):
        x, z = rng.uniform(X0 + 0.5, X1 - 0.5), rng.uniform(ZB + 0.6, 6.5)
        y = Y0
        for _k in range(int(rng.integers(1, 7))):
            w, d, h = rng.uniform(0.5, 0.8), rng.uniform(0.35, 0.55), rng.uniform(0.08, 0.15)
            out.append(F.box((-w / 2, 0, -d / 2), (w / 2, h, d / 2), m["book"][int(rng.integers(4))]).rotate(
                "y", rng.uniform(0, 180)).translate((x, y, z)))
            y += h
    out.append(F.box((OX - 3, Y0, 6.5), (OX + 4, Y0 + DAIS, ZS), m["wood"], faces="xXzY"))
    return out


def build(b, d):
    lay = b.form("art")
    rng = np.random.default_rng(1311)
    m = mats()
    fs = faces(m, rng)
    for x in (OX-8,OX-6,OX+8):
        fs.append(F.box((x,Y0+3,ZB+.2),(x+.8,Y0+3.16,ZB+.95),m['wood']))
    for j in range(7):
        fs.append(F.box((OX-8+j*2.5, Y0+.05, ZB+2), (OX-7.3+j*2.5, Y0+.3, ZB+2.5), m['wood']))
    lights = [((OX + 4.9, Y0 + 4, ZB - 1), (1.2, 1.15, 0.5), 12.0), ((OX - 3.9, Y0 + 2, ZB - 1), (0.8, 0.8, 0.3), 6.0)]
    kit.project_add(lay, CAM, m["art"], near=fs, lights=lights, ambient=(0.4, 0.44, 0.28),
                    glow_mats=[m["door"], m["spirit"]], min_facing=0.1)
    # 정령: 선반 위·바닥 (살짝 오르내림)
    spots = [(OX - 7.9, Y0 + 7.0, ZB + 0.3), (OX - 7.2, Y0 + 6.9, ZB + 0.3), (OX - 0.9, Y0 + 5.6, ZB + 0.8),
             (OX + 9.2, Y0 + 4.1, ZB + 0.3), (OX - 8.6, Y0, 3.0), (OX - 7.4, Y0, 4.5), (OX - 6.2, Y0 + 0.3, 2.5),
             (OX + 1.3, Y0 + 0.4, 1.4), (OX + 7.2, Y0, 4.0), (OX - 5.0, Y0 + 2.8, ZB + 0.6), (OX - 9.2, Y0 + 1.4, 1.5),
             (OX + 9.6, Y0 + 9.8, ZB + 0.4)]
    for i, (x, y, z) in enumerate(spots):
        lay.mover(F.Mover((int(math.floor(x)), int(y), int(math.floor(z))), spirit_mesh(m, x, y, z), (x, y, z), "bob",
                          (0, 1, 0), period=rng.uniform(2.5, 4.5), amp=0.08, phase=rng.random()))
    lay.emitter(F.Emitter((X0, Y0 + 1, ZB + 0.5, X1, Y0 + 11, ZS - 1), rate=2.0, sprites=("ruina:block/form/paper_gold",),
                          wind=(0.05, 0.1, 0.0), size=0.08, life=8.0, spin=0.2, color=(0.75, 1.0, 0.35), glow=True))
    yt = int(Y0 + H)
    x0, x1 = int(X0) - 1, int(X1)
    d.fill(x0, Y0 - 1, int(ZB) - 1, x1, Y0 - 1, int(ZS), "minecraft:barrier")
    d.fill(x0, yt, int(ZB) - 1, x1, yt, int(ZS), "minecraft:barrier")
    for x in (x0, x1):
        d.fill(x, Y0, int(ZB) - 1, x, yt, int(ZS), "minecraft:barrier")
    d.fill(x0, Y0, int(ZS), x1, yt, int(ZS), "minecraft:barrier")
    d.fill(x0, Y0, int(ZB) - 1, x1, yt, int(ZB) - 1, "minecraft:barrier")
    d.fill(OX - 3, Y0, 7, OX + 3, Y0 + DAIS - 1, int(ZS) - 1, "minecraft:barrier")
    kit.stair_collision(d, OX - 3, OX + 3, 6, 3, Y0 + DAIS, Y0)
    for x in range(int(X0) + 3, int(X1) - 1, 6):
        for z in (4, 10):
            if d.get(x, Y0 + 8, z) == "minecraft:air":
                d.set(x, Y0 + 8, z, "minecraft:light[level=11]")
    d.set_biome(OX - 40, -40, OX + 40, 40, "ruina:art_room")
    return ARRIVE


PREVIEW_CAMS = [("방 옆", F.Camera((OX - 7.0, Y0 + 1.62, 11.0), 215.0, 0.0))]


def preview(b):
    build(b, b.dim("art"))
