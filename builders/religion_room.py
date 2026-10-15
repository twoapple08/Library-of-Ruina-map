"""호크마 방 (종교의 층 지정사서 방) — 자유 형체 판. reference/종교의 층 지정사서 방.png

흰빛·잿빛: 양쪽 아주 높은 책장 벽(아래 판넬)이 깊이로 이어짐, 반들 바닥, 가운데 기둥을 감고 오르는 나선계단,
매달린 회중시계 전등(살랑 흔들림), 계단 아래 책상, 뒤 밝은 안개. 도착: 통로 남쪽에서 북쪽 (살짝 올려다봄).
"""
from __future__ import annotations

import math

import numpy as np

from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 64
OX = 4000
ART = "reference/종교의 층 지정사서 방.png"
CAM = F.Camera((OX + 0.5, Y0 + 1.62, 14.0), 180.0, -6.0)
ARRIVE = (OX + 0.5, Y0, 14.0, 180.0, -6.0)
RW, ZB, ZS, H = 6.0, -22.0, 18.0, 34.0
STAIR = (OX + 0.5, -10.0)       # 나선계단 기둥 (x, z)
SPACE = "religion"
UP = np.array([0, 1.0, 0])


def mats():
    m = {}
    m["art"] = F.mat("kroom_art", T.art("art/religion_room", ART), emissive=True, flat=True, ao=False)
    grey = [(110, 110, 114), (90, 90, 94), (140, 140, 144), (70, 70, 74), (160, 160, 164)]
    m["shelf"] = [F.mat(f"kroom_shelf{i}", T.shelf(f"kroom_shelf{i}", grey, wood=(120, 120, 124), seed=240 + i,
                                                    dark_back=(30, 30, 32)), emissive=True, flat=True, ao=False)
                  for i in range(2)]
    m["panel"] = F.mat("kroom_panel", T.board("kroom_panel", (110, 110, 114), (180, 180, 184), w=16, h=32, seed=242),
                       emissive=True, flat=True, ao=False)
    m["floor"] = F.mat("kroom_floor", T.stone_slab("kroom_floor", (170, 170, 174), (230, 230, 234), seed=243),
                       emissive=True, flat=True, ao=False)
    m["iron"] = F.mat("kroom_iron", T.metal("kroom_iron", (40, 40, 44), (110, 110, 114), seed=244), emissive=True,
                      flat=True, ao=False)
    m["fog"] = F.mat("kroom_fog", T.glow("kroom_fog", (245, 245, 248)), emissive=True, flat=True, ao=False, glow=3)
    m["watch"] = F.mat("kroom_watch", T.glow("kroom_watch", (255, 230, 150)), emissive=True, flat=True, ao=False, glow=3)
    m["haze"] = F.mat("kroom_haze", T.glow("kroom_haze", (240, 240, 244)), layer="translucent", emissive=True,
                      flat=True, ao=False)
    return m


def faces(m, rng):
    out = []
    yt = Y0 + H
    out.append(F.plane((OX - RW, Y0, ZS), (2 * RW + 1, 0, 0), (0, 0, ZB - ZS), m["floor"], tile=(3, 3)))
    for x, f in ((OX - RW, 1), (OX + RW + 1, -1)):            # 양쪽 높은 책장 벽 (아래 판넬)
        z0, z1 = (ZS, ZB) if f > 0 else (ZB, ZS)
        out.append(F.plane((x, Y0, z0), (0, 0, z1 - z0), (0, 6, 0), m["panel"], tile=(3, 6)))
        out.append(F.plane((x, Y0 + 6, z0), (0, 0, z1 - z0), (0, H - 6, 0), m["shelf"][0 if f > 0 else 1], tile=(1.6, 1.6)))
        for z in np.arange(ZB, ZS, 6.0):                         # 기둥 테
            out.append(F.box((x - 0.3 * f - 0.2, Y0, z - 0.3), (x - 0.3 * f + 0.2, yt, z + 0.3), m["panel"]))
        out.append(F.box((min(x, x + f * 0.8), Y0 + 5.8, ZB), (max(x, x + f * 0.8), Y0 + 6.3, ZS), m["panel"]))
    out.append(F.plane((OX - RW, Y0, ZB), (2 * RW + 1, 0, 0), (0, H, 0), m["fog"], tile=(4, 4)))       # 뒤 밝은 안개
    for k in range(5):
        out.append(F.plane((OX - RW, Y0, ZB + 2 + k * 3), (2 * RW + 1, 0, 0), (0, H, 0), m["haze"], tile=(4, 4))
                   .tint((1, 1, 1), 0.1))
    # 나선계단: 가운데 기둥 + 감아 오르는 디딤판 + 난간
    sx, sz = STAIR
    out.append(F.revolve([(0.45, Y0), (0.45, yt)], m["iron"], segs=12, center=(sx, 0, sz), tiles_around=3, tile_up=4.0))
    n = 96
    for k in range(n):
        a = k * 2 * math.pi / 16
        y = Y0 + 1.5 + k * 0.32
        p0 = np.array([sx + 0.5 * math.cos(a), y, sz + 0.5 * math.sin(a)])
        p1 = np.array([sx + 2.8 * math.cos(a), y, sz + 2.8 * math.sin(a)])
        q1 = np.array([sx + 2.8 * math.cos(a + 0.4), y, sz + 2.8 * math.sin(a + 0.4)])
        q0 = np.array([sx + 0.5 * math.cos(a + 0.4), y, sz + 0.5 * math.sin(a + 0.4)])
        out.append(F.two_sided(F.Quads(np.array([[p0, p1, q1, q0]]), np.array([[[0, 0], [0.99, 0], [0.99, 0.99], [0, 0.99]]]),
                                       M=m["iron"])))
    t = np.linspace(0, n / 16 * 2 * math.pi, n * 3)
    rail = np.stack([sx + 2.9 * np.cos(t), Y0 + 2.5 + t / (2 * math.pi) * 16 * 0.32, sz + 2.9 * np.sin(t)], 1)
    out.append(F.sweep(rail, 0.05, m["iron"], sides=4, step=0.5))
    # 계단 아래 책상
    out.append(F.box((sx - 2.2, Y0, sz + 2.6), (sx + 2.2, Y0 + 1.1, sz + 3.6), m["panel"]))
    # 바닥 책 더미 (양쪽 벽 아래)
    for _ in range(10):
        x = OX - RW + 0.5 if rng.random() < 0.5 else OX + RW
        z = rng.uniform(ZB + 4, ZS - 2)
        y = Y0
        for _k in range(int(rng.integers(2, 6))):
            w, d, h = rng.uniform(0.5, 0.8), rng.uniform(0.35, 0.55), rng.uniform(0.08, 0.15)
            out.append(F.box((-w / 2, 0, -d / 2), (w / 2, h, d / 2), m["shelf"][0], tile=1.0).rotate(
                "y", rng.uniform(0, 180)).translate((x, y, z)))
            y += h
    return out


def build(b, d):
    lay = b.form("religion")
    rng = np.random.default_rng(2231)
    m = mats()
    fs = faces(m, rng)
    lights = [((OX + 0.5, Y0 + 12, ZB + 2), (0.9, 0.9, 0.92), 40.0)]
    kit.project_add(lay, CAM, m["art"], near=fs, lights=lights, ambient=(0.62, 0.62, 0.64),
                    glow_mats=[m["fog"], m["haze"], m["watch"]], min_facing=0.1)
    sx, sz = STAIR
    for i in range(22):                                         # 회중시계 전등 (흔들림)
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.8, 3.5)
        x, z = sx + r * math.cos(a), sz + r * math.sin(a)
        y = Y0 + rng.uniform(8, 28)
        L = Y0 + H - y
        mesh = F.concat([F.ellipsoid((x, y, z), (0.22, 0.22, 0.08), m["watch"], 10, 4),
                         F.sweep(np.array([[x, y + 0.22, z], [x, Y0 + H, z]]), 0.015, m["iron"], sides=3, step=max(1, L))])
        lay.mover(F.Mover((int(math.floor(x)), int(y), int(math.floor(z))), mesh, (x, Y0 + H, z), "swing",
                          (1, 0, rng.uniform(-1, 1)), period=rng.uniform(8, 14), amp=1.2, phase=rng.random()))
    yt = int(Y0 + H)
    x0, x1 = int(OX - RW) - 1, int(OX + RW) + 1
    d.fill(x0, Y0 - 1, int(ZB), x1, Y0 - 1, int(ZS), "minecraft:barrier")
    d.fill(x0, yt, int(ZB), x1, yt, int(ZS), "minecraft:barrier")
    for x in (x0, x1):
        d.fill(x, Y0, int(ZB), x, yt, int(ZS), "minecraft:barrier")
    for z in (int(ZB), int(ZS)):
        d.fill(x0, Y0, z, x1, yt, z, "minecraft:barrier")
    d.fill(int(sx) - 2, Y0, int(sz) + 2, int(sx) + 2, Y0, int(sz) + 3, "minecraft:barrier")      # 책상
    d.fill(int(sx), Y0, int(sz), int(sx), yt - 1, int(sz), "minecraft:barrier")                     # 기둥
    for x in range(int(OX - RW) + 1, int(OX + RW), 5):
        for z in range(int(ZB) + 4, int(ZS), 8):
            if d.get(x, Y0 + 12, z) == "minecraft:air":
                d.set(x, Y0 + 12, z, "minecraft:light[level=14]")
    d.set_biome(OX - 40, -40, OX + 40, 40, "ruina:religion_room")
    return ARRIVE


PREVIEW_CAMS = [("계단 아래에서 올려다봄", F.Camera((OX + 3.0, Y0 + 1.62, -4.0), 200.0, -50.0))]


def preview(b):
    build(b, b.dim("religion"))
