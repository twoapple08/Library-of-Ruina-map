"""비나 방 (철학의 층 지정사서 방) — 자유 형체 판. reference/철학의 층 지정사서 방.png

동굴 같은 어두운 서고: 뒤틀린 검은 기둥들(나무뿌리 같은), 층층이 쌓인 책장이 금빛으로 달아오름, 가운데 뒤 금빛 빛,
매달린 팔각 별 등(살랑 흔들림), 빛이 비치는 반들 어두운 바닥, 오른쪽 작은 둥근 탁자(촛불·찻잔)와 의자.
도착: 한 칸 단 위에서 북쪽.
"""
from __future__ import annotations

import math

import numpy as np

from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 64
OX = 4000
ART = "reference/철학의 층 지정사서 방.png"
CAM = F.Camera((OX + 0.5, Y0 + 1 + 1.62, 16.0), 180.0, 0.0)
ARRIVE = (OX + 0.5, Y0 + 1, 16.0, 180.0, 0.0)
RW, RD, H = 18.0, 16.0, 22.0
SPACE = "philosophy"
UP = np.array([0, 1.0, 0])


def mats():
    m = {}
    m["art"] = F.mat("broom_art", T.art("art/philosophy_room", ART), emissive=True, flat=True, ao=False)
    m["rock"] = F.mat("broom_rock", T.bark("broom_rock", (14, 12, 12), (46, 38, 34), seed=221), emissive=True, flat=True,
                      ao=False)
    m["floor"] = F.mat("broom_floor", T.stone_slab("broom_floor", (12, 10, 10), (40, 34, 30), seed=222), emissive=True,
                       flat=True, ao=False)
    warm = [(150, 90, 40), (120, 70, 30), (180, 120, 60), (100, 60, 30), (200, 150, 80)]
    m["shelf"] = [F.mat(f"broom_shelf{i}", T.shelf(f"broom_shelf{i}", warm, wood=(140, 90, 40), seed=223 + i,
                                                    dark_back=(40, 20, 8)), emissive=True, flat=True, ao=False, glow=3)
                  for i in range(2)]
    m["light"] = F.mat("broom_light", T.glow("broom_light", (255, 200, 110)), emissive=True, flat=True, ao=False, glow=3)
    m["star"] = F.mat("broom_star", T.glow("broom_star", (255, 220, 140)), emissive=True, flat=True, ao=False, glow=3)
    m["shine"] = F.mat("broom_shine", T.glow("broom_shine", (255, 180, 90)), layer="translucent", emissive=True,
                       flat=True, ao=False)
    m["wood"] = F.mat("broom_wood", T.wood("broom_wood", (20, 14, 12), (60, 44, 34), seed=225), emissive=True, flat=True,
                      ao=False)
    return m


def star_mesh(m, c, r):
    """팔각 별 등: 위·아래 피라미드 여덟 꼭지 (납작)."""
    out = []
    c = np.asarray(c, float)
    for k in range(8):
        a0, a1 = k * math.pi / 4, (k + 1) * math.pi / 4
        tip = c + r * np.array([math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2), 0])
        p0 = c + r * 0.45 * np.array([math.cos(a0), math.sin(a0), 0])
        p1 = c + r * 0.45 * np.array([math.cos(a1), math.sin(a1), 0])
        for dz in (r * 0.25, -r * 0.25):
            ctr = c + np.array([0, 0, dz])
            out.append(F.Quads(np.array([[ctr, p0, tip, p1]]), np.array([[[0.5, 0.5], [0, 0], [0.5, 0.99], [0.99, 0]]]),
                               M=m["star"]))
    return F.two_sided(F.concat(out))


def faces(m, rng):
    out = []
    yt = Y0 + H
    out.extend([F.box((OX-RW,Y0,-RD),(OX-RW+.25,Y0+.3,RD),m['wood']), F.box((OX+RW-.25,Y0,-RD),(OX+RW,Y0+.3,RD),m['wood'])])
    out.append(F.plane((OX - RW, Y0, RD + 2), (2 * RW, 0, 0), (0, 0, -2 * RD - 2), m["floor"], tile=(3, 3)))
    # 가운데 빛 비친 반들 바닥 (반투명 빛 판)
    for k in range(6):
        z = -RD + 2 + k * 3.5
        w = 2.5 + k * 0.5
        out.append(F.plane((OX + 0.5 - w / 2, Y0 + 0.02, z + 3), (w, 0, 0), (0, 0, -3), m["shine"]).tint((1, 1, 1), 0.45 - k * 0.05))
    # 동굴 벽·천장 (울퉁불퉁 둥근 껍질)
    prof = [(RW + 1, Y0 - 1), (RW + 2, Y0 + H * 0.4), (RW * 0.8, Y0 + H), (RW * 0.3, Y0 + H + 4), (0.1, Y0 + H + 5)]
    q = F.revolve(prof, m["rock"], segs=48, center=(OX + 0.5, 0, 0), tiles_around=16, tile_up=8.0).flipped()
    q.P[..., 2] = q.P[..., 2] * (RD / RW)
    n = 1 + 0.06 * np.sin(np.arctan2(q.P[..., 2], q.P[..., 0] - OX) * 9 + q.P[..., 1] * 0.3)
    q.P[..., 0] = OX + 0.5 + (q.P[..., 0] - OX - 0.5) * n
    q.P[..., 2] = q.P[..., 2] * n
    out.append(q)
    # 층층이 쌓인 금빛 책장 (양옆, 안쪽으로 갈수록 높게)
    for side in (-1, 1):
        for k in range(12):
            x = OX + 0.5 + side * rng.uniform(5, RW - 2)
            z = -RD + 2 + rng.uniform(0, RD + 4)
            w, d, h = rng.uniform(2, 4.5), rng.uniform(1.2, 2.2), rng.uniform(4, 13)
            for j in range(int(h / 2.5)):
                y = Y0 + j * 2.5
                dx = rng.uniform(-0.4, 0.4)
                out.append(F.box((x + dx - w / 2, y, z - d / 2), (x + dx + w / 2, y + 2.5, z + d / 2),
                                 m["shelf"][int(rng.integers(2))], tile=1.25).rotate("y", rng.uniform(-8, 8), origin=(x, y, z)))
    # 뒤틀린 검은 기둥 (바닥 → 천장, 굽어 오름)
    for i in range(9):
        bx, bz = OX + 0.5 + rng.uniform(-RW + 3, RW - 3), rng.uniform(-RD + 2, -2)
        if abs(bx - OX) < 4:
            bx += 8 * (1 if bx > OX else -1)
        t = np.linspace(0, 1, 16)
        path = np.stack([bx + 3 * np.sin(t * 3 + i), Y0 + (H + 3) * t, bz + 1.5 * np.cos(t * 2 + i)], 1)
        out.append(F.sweep(path, lambda s: 1.0 + 1.6 * (1 - s) ** 2 + 0.6 * s, m["rock"], sides=8, step=1.5, tile_along=4,
                           twist=120))
    # 가운데 뒤 금빛 빛 (다음 층 입구)
    out.append(F.plane((OX - 4.5, Y0, -RD - 0.5), (10, 0, 0), (0, 16, 0), m["light"], tile=(4, 4)))
    # 오른쪽 작은 둥근 탁자 + 촛불 + 찻잔 + 의자
    tx, tz = OX + 6.0, 11.0
    out.append(F.revolve([(0.01, Y0 + 0.95), (1.1, Y0 + 0.95), (1.1, Y0 + 0.85), (0.1, Y0 + 0.8), (0.1, Y0), (0.5, Y0)],
                         m["wood"], segs=20, center=(tx, 0, tz), tiles_around=4, tile_up=1.0))
    for dx, dz in ((-0.3, 0.2), (0.0, -0.2), (0.3, 0.3)):
        out.append(F.box((tx + dx - 0.04, Y0 + 0.95, tz + dz - 0.04), (tx + dx + 0.04, Y0 + 1.1, tz + dz + 0.04), m["light"]))
    out.append(F.revolve([(0.1, Y0 + 0.95), (0.12, Y0 + 1.12), (0.01, Y0 + 1.12)], m["floor"], segs=10,
                         center=(tx + 0.6, 0, tz - 0.3), tiles_around=2, tile_up=1.0))
    out.append(F.box((tx + 1.4, Y0 + 0.5, tz - 0.4), (tx + 2.2, Y0 + 0.6, tz + 0.4), m["wood"]))
    out.append(F.box((tx + 2.1, Y0 + 0.6, tz - 0.4), (tx + 2.2, Y0 + 1.6, tz + 0.4), m["wood"]))
    out.append(F.box((OX - 2, Y0, 14.0), (OX + 3, Y0 + 1, RD + 2), m["rock"], faces="xXzY"))
    return out


def build(b, d):
    lay = b.form("philosophy")
    rng = np.random.default_rng(2011)
    m = mats()
    fs = faces(m, rng)
    # 차탁의 하부 금속 다리 연결재.
    fs.append(F.box((OX+7.12,Y0+.22,10.15),(OX+7.48,Y0+.32,10.45),m['wood']))
    # 찻잔과 책받침의 층별 입체 마감.
    fs.extend([F.box((OX+7,Y0+.8,10),(OX+7.6,Y0+.87,10.6),m['wood']),F.box((OX+7.1,Y0+.87,10.1),(OX+7.5,Y0+1.18,10.5),m['shine'])])
    for z in (-10,-5,0,5):
        fs.append(F.box((OX-RW+1,Y0+4,z),(OX-RW+4,Y0+4.18,z+.85),m['wood']))
    for j in range(6):
        fs.append(F.box((OX-6+j*2, Y0+.05, 3), (OX-5.3+j*2, Y0+.32, 3.6), m['wood']))
    lights = [((OX + 0.5, Y0 + 6, -RD + 1), (1.6, 1.0, 0.45), 30.0), ((OX + 6, Y0 + 1.5, 11), (0.6, 0.4, 0.2), 4.0)]
    kit.project_add(lay, CAM, m["art"], near=fs, lights=lights, ambient=(0.3, 0.22, 0.16),
                    glow_mats=[m["light"], *m["shelf"], m["shine"]], min_facing=0.1)
    for i in range(11):                                       # 매달린 별 등 (흔들림)
        sx, sy, sz = OX + 0.5 + rng.uniform(-6, 6), Y0 + H - rng.uniform(4, 10), rng.uniform(-RD + 3, -2)
        r = rng.uniform(0.5, 1.2)
        mesh = F.concat([star_mesh(m, (sx, sy, sz), r),
                         F.sweep(np.array([[sx, sy + r, sz], [sx, Y0 + H + 2, sz]]), 0.02, m["wood"], sides=4, step=6.0)])
        lay.mover(F.Mover((int(math.floor(sx)), int(sy), int(math.floor(sz))), mesh, (sx, Y0 + H + 2, sz), "swing",
                          (1, 0, rng.uniform(-0.5, 0.5)), period=rng.uniform(6, 10), amp=2.5, phase=rng.random()))
    lay.emitter(F.Emitter((OX - RW, Y0 + 1, -RD, OX + RW, Y0 + 16, RD), rate=5.0, sprites=("ruina:block/form/paper_gold",),
                          wind=(0.0, 0.15, 0.0), size=0.07, life=9.0, spin=0.1, color=(1.0, 0.7, 0.35), glow=True))
    yt = int(Y0 + H + 6)
    x0, x1, z0, z1 = int(OX - RW) - 3, int(OX + RW) + 3, -int(RD) - 2, int(RD) + 3
    d.fill(x0, Y0 - 1, z0, x1, Y0 - 1, z1, "minecraft:barrier")
    d.fill(x0, yt, z0, x1, yt, z1, "minecraft:barrier")
    for x in (x0, x1):
        d.fill(x, Y0, z0, x, yt, z1, "minecraft:barrier")
    for z in (z0, z1):
        d.fill(x0, Y0, z, x1, yt, z, "minecraft:barrier")
    d.fill(OX - 2, Y0, 14, OX + 2, Y0, int(RD) + 1, "minecraft:barrier")
    d.fill(OX - 2, Y0, 13, OX + 2, Y0, 13, F.HALF_SOLID)
    for x in range(int(OX - RW) + 4, int(OX + RW) - 2, 8):
        for z in (-8, 4):
            if d.get(x, Y0 + 10, z) == "minecraft:air":
                d.set(x, Y0 + 10, z, "minecraft:light[level=10]")
    d.set_biome(OX - 40, -40, OX + 40, 40, "ruina:philosophy_room")
    return ARRIVE


PREVIEW_CAMS = [("방 옆", F.Camera((OX - 10.0, Y0 + 1.62, 10.0), 220.0, -5.0))]


def preview(b):
    build(b, b.dim("philosophy"))
