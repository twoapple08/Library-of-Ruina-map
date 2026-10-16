"""티페리트 방 (자연과학의 층 지정사서 방) — 자유 형체 판. reference/자연과학의 층 지정사서 방.png

금빛 나무 책장 벽(사다리), 큰 아치 창(마름모 문양, 청록 보석)에서 쏟아지는 빛, 붉은 카펫이 계단 위 둥근 탁자·
안락의자로, 양옆 체크무늬 바닥, 둥근 갈비 천장, 왼쪽 어두운 아치 문, 오른쪽 A자 사다리, 책 더미.
도착: 방 남쪽에서 북쪽 (살짝 올려다봄).
"""
from __future__ import annotations

import math

import numpy as np

from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 64
OX = 4000
ART = "reference/자연과학의 층 지정사서 방.png"
CAM = F.Camera((OX + 0.5, Y0 + 1.62, 12.0), 180.0, -4.0)
ARRIVE = (OX + 0.5, Y0, 12.0, 180.0, -4.0)
X0, X1, ZB, ZS, H = OX - 7.0, OX + 9.0, 4.0, 16.0, 17.0
WIN = (OX - 0.3, OX + 4.9)                # 아치 창 x
SPACE = "natural_science"
UP = np.array([0, 1.0, 0])


def mats():
    m = {}
    m["art"] = F.mat("nroom_art", T.art("art/natural_science_room", ART), emissive=True, flat=True, ao=False)
    gold = [(150, 110, 60), (130, 90, 50), (180, 140, 80), (110, 84, 56), (200, 170, 110)]
    m["shelf"] = [F.mat(f"nroom_shelf{i}", T.shelf(f"nroom_shelf{i}", gold, wood=(170, 120, 60), seed=160 + i,
                                                    dark_back=(50, 34, 16)), emissive=True, flat=True, ao=False)
                  for i in range(3)]
    m["wood"] = F.mat("nroom_wood", T.wood("nroom_wood", (110, 70, 30), (210, 160, 90), seed=163), emissive=True,
                      flat=True, ao=False)
    m["window"] = F.mat("nroom_window", T.glow("nroom_window", (255, 246, 214)), emissive=True, flat=True, ao=False,
                        glow=3)
    m["gem"] = F.mat("nroom_gem", T.glow("nroom_gem", (90, 220, 210)), emissive=True, flat=True, ao=False, glow=4)
    m["carpet"] = F.mat("nroom_carpet", T.flat("nroom_carpet", (176, 70, 60)), emissive=True, flat=True, ao=False)
    m["check"] = F.mat("nroom_check", T.herringbone("nroom_check", (150, 130, 100), (240, 226, 196), brick=(32, 32),
                                                    seed=164), emissive=True, flat=True, ao=False)
    m["dark"] = F.mat("nroom_dark", T.flat("nroom_dark", (20, 14, 10)), emissive=True, flat=True, ao=False)
    m["ray"] = F.mat("ns_ray", T.glow("ns_ray", (255, 240, 200)), layer="translucent", emissive=True, flat=True,
                     ao=False)
    return m


def faces(m, rng):
    out = []
    yt = Y0 + H
    out.append(F.plane((X0, Y0, ZS), (X1 - X0, 0, 0), (0, 0, ZB - ZS), m["check"], tile=(2, 2)))
    out.append(F.plane((OX - 1.2, Y0 + 0.02, ZS), (3.4, 0, 0), (0, 0, ZB - ZS), m["carpet"], tile=(2, 2)))
    # 둥근 갈비 천장
    t = np.linspace(0, math.pi, 13)
    for z in np.arange(ZB, ZS + 0.1, 1.5):
        arc = np.stack([OX + 1 + (X1 - X0) / 2 * np.cos(t), yt + 3 * np.sin(t), np.full_like(t, z)], 1)
        out.append(F.sweep(arc, 0.18, m["wood"], sides=4, step=1.0))
    G = np.stack([np.stack([OX + 1 + (X1 - X0) / 2 * np.cos(t), yt + 3 * np.sin(t), np.full_like(t, z)], 1)
                  for z in (ZB, ZS)], 1)
    UV = np.stack(np.meshgrid(np.linspace(0, 6, 13), np.array([0, 4.0]), indexing="ij"), -1)
    out.append(F.fit_tiles(F.grid(G, UV, m["wood"], N=np.broadcast_to([0, -1.0, 0], G.shape))))
    # 북쪽 벽: 책장 + 큰 아치 창 (창살·마름모·보석)
    wa, wb = WIN
    for a, b in ((X0, wa), (wb, X1)):
        out.append(F.plane((a, Y0, ZB), (b - a, 0, 0), (0, H, 0), m["shelf"][int(rng.integers(3))], tile=(1.3, 1.3)))
    out.append(F.plane((wa, Y0 + 1.5, ZB - 0.3), (wb - wa, 0, 0), (0, H - 4, 0), m["window"], tile=(2, 4)))
    for x in np.linspace(wa, wb, 6):
        out.append(F.box((x - 0.08, Y0 + 1.5, ZB - 0.25), (x + 0.08, Y0 + H - 6, ZB - 0.1), m["wood"]))
    cx, cy = (wa + wb) / 2, Y0 + H - 4.2
    dia = np.array([[cx, cy + 1.6, ZB - 0.2], [cx + 1.6, cy, ZB - 0.2], [cx, cy - 1.6, ZB - 0.2], [cx - 1.6, cy, ZB - 0.2],
                    [cx, cy + 1.6, ZB - 0.2]])
    out.append(F.sweep(dia, 0.1, m["wood"], sides=4, step=0.5))
    out.append(F.box((cx - 0.3, cy - 0.3, ZB - 0.2), (cx + 0.3, cy + 0.3, ZB), m["gem"]))
    out.append(F.plane((wa, Y0 + H - 2.5, ZB), (wb - wa, 0, 0), (0, 2.5, 0), m["wood"], tile=(2, 2)))
    # 옆 벽 책장 + 사다리 (왼쪽 벽) + 어두운 아치 문
    for x, f in ((X0, 1), (X1, -1)):
        out.append(F.plane((x, Y0, ZS if f > 0 else ZB), (0, 0, (ZB - ZS) * f), (0, H, 0), m["shelf"][1], tile=(1.3, 1.3)))
    out.append(F.plane((X0 + 0.05, Y0, 9.6), (0, 0, -2.4), (0, 4.4, 0), m["dark"]))
    for s in (0.0, 1.2):
        out.append(F.sweep(np.array([[OX - 3.2 + s, Y0, 7.4], [OX - 4.9 + s, Y0 + 12, ZB + 0.4]]), 0.07, m["wood"],
                           sides=4, step=3.0))
    for k in range(18):
        tt = k / 18
        a = np.array([OX - 3.2 - 1.7 * tt, Y0 + 12 * tt, 7.4 - 3.0 * tt])
        out.append(F.box(a - [0, 0.04, 0.04], a + [1.2, 0.04, 0.04], m["wood"]))
    # 창 앞 단 3칸 (붉은 카펫) + 둥근 탁자 + 안락의자
    for k in range(3):
        z0 = ZB + 0.2
        z1 = ZB + 4.6 - k * 1.2
        out.append(F.box((OX - 3.0, Y0, z0), (OX + 4.0, Y0 + 0.4 * (k + 1), z1), m["wood"], faces="yYxXZ"))
        out.append(F.plane((OX - 1.0, Y0 + 0.4 * (k + 1) + 0.01, z1), (3.0, 0, 0), (0, 0, -1.2), m["carpet"]))
    tx, tz, ty = OX + 1.0, ZB + 2.0, Y0 + 1.2
    out.append(F.revolve([(0.01, ty + 1.0), (1.3, ty + 1.0), (1.3, ty + 0.9), (0.2, ty + 0.85), (0.2, ty + 0.1),
                          (0.7, ty)], m["wood"], segs=20, center=(tx, 0, tz), tiles_around=4, tile_up=1.0))
    ch = (OX + 3.0, ZB + 1.9)
    out.append(F.box((ch[0] - 0.6, ty, ch[1] - 0.6), (ch[0] + 0.6, ty + 0.55, ch[1] + 0.6), m["carpet"]))
    out.append(F.box((ch[0] - 0.65, ty + 0.55, ch[1] - 0.6), (ch[0] - 0.45, ty + 1.8, ch[1] + 0.6), m["wood"]))
    # A자 사다리 (오른쪽)
    ax, az = OX + 3.5, 8.0
    for dz in (-0.7, 0.7):
        for s in (-0.5, 0.5):
            out.append(F.sweep(np.array([[ax + s, Y0, az + dz], [ax + s, Y0 + 3.2, az]]), 0.06, m["wood"], sides=4, step=2))
    # 책 더미
    for _ in range(16):
        x, z = rng.uniform(X0 + 0.5, X1 - 0.5), rng.uniform(ZB + 0.5, ZS - 4)
        if abs(x - OX - 0.5) < 2.0:
            continue
        y = Y0
        for _k in range(int(rng.integers(1, 6))):
            w, d, h = rng.uniform(0.5, 0.8), rng.uniform(0.35, 0.55), rng.uniform(0.08, 0.15)
            out.append(F.box((-w / 2, 0, -d / 2), (w / 2, h, d / 2), m["shelf"][int(rng.integers(3))], tile=1.0).rotate(
                "y", rng.uniform(0, 180)).translate((x, y, z)))
            y += h
    return out


def build(b, d):
    lay = b.form("natural_science")
    rng = np.random.default_rng(1531)
    m = mats()
    fs = faces(m, rng)
    for j in range(6):
        fs.append(F.box((OX-7+j*2.5, Y0+.05, ZB+2), (OX-6.4+j*2.5, Y0+.3, ZB+2.5), m['wood']))
    lights = [(((WIN[0] + WIN[1]) / 2, Y0 + 8, ZB - 1), (1.4, 1.2, 0.85), 18.0)]
    kit.project_add(lay, CAM, m["art"], near=fs, lights=lights, ambient=(0.6, 0.48, 0.32),
                    glow_mats=[m["window"], m["gem"]], min_facing=0.1)
    for k in range(5):                                       # 창에서 쏟아지는 빛줄기
        x = WIN[0] + 0.6 + k
        q = F.two_sided(F.Quads(np.array([[[x, Y0 + 12, ZB - 0.2], [x + 0.8, Y0 + 12, ZB - 0.2], [x + 2.5, Y0, ZB + 6],
                                           [x + 1.2, Y0, ZB + 6]]]), np.array([[[0, 0], [0.99, 0], [0.99, 0.99], [0, 0.99]]]),
                                M=m["ray"])).tint((1, 1, 1), 0.1)
        lay.add(q)
    yt = int(Y0 + H)
    x0, x1 = int(X0) - 1, int(X1)
    d.fill(x0, Y0 - 1, int(ZB) - 1, x1, Y0 - 1, int(ZS), "minecraft:barrier")
    d.fill(x0, yt + 3, int(ZB) - 1, x1, yt + 3, int(ZS), "minecraft:barrier")
    for x in (x0, x1):
        d.fill(x, Y0, int(ZB) - 1, x, yt + 3, int(ZS), "minecraft:barrier")
    d.fill(x0, Y0, int(ZS), x1, yt + 3, int(ZS), "minecraft:barrier")
    d.fill(x0, Y0, int(ZB) - 1, x1, yt + 3, int(ZB) - 1, "minecraft:barrier")
    d.fill(OX - 3, Y0, int(ZB), OX + 3, Y0, int(ZB) + 3, "minecraft:petrified_oak_slab[type=bottom,waterlogged=false]")
    for x in range(int(X0) + 2, int(X1), 5):
        for z in (6, 12):
            if d.get(x, Y0 + 10, z) == "minecraft:air":
                d.set(x, Y0 + 10, z, "minecraft:light[level=13]")
    d.set_biome(OX - 40, -40, OX + 40, 40, "ruina:natural_science_room")
    return ARRIVE


PREVIEW_CAMS = [("방 옆", F.Camera((OX - 5.0, Y0 + 1.62, 14.0), 210.0, -10.0))]


def preview(b):
    build(b, b.dim("natural_science"))
