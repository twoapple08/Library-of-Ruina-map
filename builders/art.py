"""예술의 층 (네짜흐) — 자유 형체 판 (2026-10-15).

reference/예술의 층 전경.png: 쓰러진 거대 나무줄기(윗면 나무껍질 바닥, 뒤 가장자리 부러진 그루터기 줄)를 옆 조금 위
(유리 전망 발판, 도착)에서 봄 — 아래 위가 비치는 연두빛 수면, 뒤로 책장이 박힌 거대 나무줄기들, 줄기 사이로 새는
연두·노랑 빛, 반딧불이. 안개 속 멀리 눈 셋 달린 거대 괴생물체(나무위키). 지정사서 방: builders/art_room.py.
"""
from __future__ import annotations

import math

import numpy as np

from tools import artfit as A
from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 110
BX, LR = 200, 14
YC = Y0 - 11.0                # 줄기 중심 (윗면 y=Y0 에서 평평하게 자름 → 윗면 폭 ≈ 15)
WATER = 70
HALF = math.sqrt(LR ** 2 - (Y0 - YC) ** 2)
PLAT = Y0 + 2
CAM = F.Camera((0.5, PLAT + 1.62, HALF + 8.1), 180.0, 8.0)
ARRIVE = (0.5, PLAT, HALF + 8.1, 180.0, 8.0)
ART = "reference/예술의 층 전경.png"
SPACE = "art"
UP = np.array([0, 1.0, 0])
TREES = [(-120, -70, 26, 330), (40, -95, 34, 340), (190, -60, 22, 300), (-260, -150, 38, 360), (300, -170, 30, 350),
         (-40, -220, 40, 370), (130, -260, 32, 360), (-150, 90, 24, 300), (120, 110, 28, 320), (-320, 60, 26, 310),
         (320, 40, 30, 330), (0, 180, 36, 340), (-230, 260, 30, 340), (240, 270, 34, 350)]


def mats():
    m = {}
    m["art"] = F.mat("art_art", T.art("art/art", ART), emissive=True, flat=True, ao=False)
    m["bark"] = F.mat("art_bark", T.bark("art_bark", (34, 30, 18), (90, 80, 44), seed=131), emissive=True, flat=True,
                      ao=False)
    m["top"] = F.mat("art_top", T.wood("art_top", (60, 46, 26), (120, 96, 56), seed=132), emissive=True, flat=True,
                     ao=False)
    m["water"] = F.mat("art_water", T.glow("art_water", (170, 220, 80)), layer="translucent", emissive=True, flat=True,
                       ao=False)
    m["glowline"] = F.mat("art_glowline", T.glow("art_glowline", (210, 255, 120)), emissive=True, flat=True, ao=False,
                          glow=6)
    green = [(60, 70, 40), (80, 90, 50), (100, 110, 60), (70, 60, 40), (110, 100, 60)]
    m["shelf"] = [F.mat(f"art_shelf{i}", T.shelf(f"art_shelf{i}", green, wood=(70, 66, 36), seed=133 + i,
                                                  dark_back=(20, 24, 12)), emissive=True, flat=True, ao=False)
                  for i in range(3)]
    m["glass"] = F.mat("art_glass", T.glow("art_glass", (220, 255, 160)), layer="translucent", emissive=True,
                       flat=True, ao=False)
    m["black"] = F.mat("art_black", T.flat("art_black", (44, 54, 30)), emissive=True, flat=True, ao=False)   # 안개 낀 검정
    m["eye"] = F.mat("art_eye", T.glow("art_eye", (255, 220, 90)), emissive=True, flat=True, ao=False, glow=3)
    return m


def log(m, rng):
    """쓰러진 나무줄기: 껍질 원통 (윗면 평평), 윗면 껍질 벗긴 나무, 끝은 부러짐, 뒤 가장자리 그루터기 줄."""
    t = np.linspace(-BX - 10, BX + 10, 2)
    path = np.stack([t, np.full(2, YC), np.zeros(2)], 1)
    q = F.sweep(path, LR, m["bark"], sides=36, step=2.0, tile_along=6.0, tiles_around=6,
                profile=lambda th: 1 + 0.03 * np.cos(th * 7))
    q.P[..., 1] = np.minimum(q.P[..., 1], Y0)
    out = [q.take(q.P[..., 1].min(1) < Y0 - 0.01)]
    top = F.plane((-BX - 10, Y0, HALF), (2 * BX + 20, 0, 0), (0, 0, -2 * HALF), m["top"], tile=(4, 4))
    out.append(top.color_by(lambda P, N: (0.8 + 0.25 * np.sin(P[:, 0:1] * 0.7) * np.cos(P[:, 2:3] * 1.3))))
    for x in np.arange(-BX, BX, 2.6):                           # 그루터기 줄 (뒤 가장자리)
        h = rng.uniform(0.6, 5.5) if rng.random() < 0.8 else rng.uniform(5, 9)
        w = rng.uniform(1.2, 2.4)
        z = -HALF + rng.uniform(0.2, 1.4)
        st = F.box((x, Y0 - 0.5, z - w / 2), (x + w, Y0 + h, z + w / 2), m["bark"], tile=2.0, faces="xXzZY")
        out.append(st.rotate("x", rng.uniform(-6, 6), origin=(x, Y0, z)))
        out.append(F.box((x, Y0 + h, z - w / 2), (x + w, Y0 + h + 0.06, z + w / 2), m["glowline"]).tint((0.6, 0.7, 0.4)))
    return out


def tree(m, rng, cx, cz, r0, h, seed=0, niches=True):
    """책장이 박힌 거대 나무줄기: 울퉁불퉁 둥근 껍질, 움푹한 칸(안에 책장), 위 가지."""
    y0, y1 = WATER - 10, WATER + h
    ys = np.linspace(y0, y1, 24)
    prof = [(r0 * (1.15 - 0.45 * (y - y0) / (y1 - y0)) * (1.25 if y < y0 + 10 else 1.0), y) for y in ys]
    q = F.revolve(prof, m["bark"], segs=28, center=(cx, 0, cz), tiles_around=10, tile_up=12.0)
    a = np.arctan2(q.P[..., 2] - cz, q.P[..., 0] - cx)
    bump = 1 + 0.06 * np.sin(5 * a + q.P[..., 1] / 15 + seed) + 0.04 * np.sin(11 * a - q.P[..., 1] / 9)
    q.P[..., 0] = cx + (q.P[..., 0] - cx) * bump
    q.P[..., 2] = cz + (q.P[..., 2] - cz) * bump
    out = [q]
    if niches:
        for _ in range(int(rng.integers(6, 14))):
            ang = rng.uniform(0, 2 * math.pi)
            y = rng.uniform(WATER + 10, y1 - 30)
            r = float(np.interp(y, [p[1] for p in prof], [p[0] for p in prof])) + 0.5
            n = np.array([math.cos(ang), 0, math.sin(ang)])
            t = np.array([-math.sin(ang), 0, math.cos(ang)])
            w, hh = rng.uniform(4, 9), rng.uniform(5, 12)
            c = np.array([cx, y, cz]) + n * r
            out.append(F.plane(c - t * w / 2, t * w, UP * hh, m["shelf"][int(rng.integers(3))], tile=(1.5, 1.5)))
    top = np.array([cx, y1 - 5, cz])
    for k in range(int(rng.integers(3, 6))):
        aa = rng.uniform(0, 2 * math.pi)
        dd = np.array([math.cos(aa), rng.uniform(0.3, 0.9), math.sin(aa)])
        pts = np.array([top - [0, h * 0.25, 0], top + dd * r0 * 1.5, top + dd * r0 * 3, top + dd * r0 * 4.5 + [0, r0, 0]])
        out.append(F.sweep(pts, lambda s: r0 * 0.3 * (1 - s) + 1.5, m["bark"], sides=10, step=4.0, tile_along=8))
    # 줄기 둘레 물가 빛 (원화의 연두 윤곽)
    ring = np.stack([cx + (r0 * 1.3) * np.cos(np.linspace(0, 2 * math.pi, 40)), np.full(40, WATER + 0.05),
                     cz + (r0 * 1.3) * np.sin(np.linspace(0, 2 * math.pi, 40))], 1)
    out.append(F.sweep(ring, 0.8, m["glowline"], sides=4, step=3.0))
    return F.concat(out)


def creature(m, view):
    """안개 속 눈 셋 괴생물체 (방 이젤 그림): 실크해트, 세로로 선 눈 셋, 가늘고 긴 다리 다섯."""
    cx, cz = 40.0, -460.0           # 안개 속 멀리 (원화 나무들 뒤)
    body_y0, body_y1, rw = WATER + 120, WATER + 330, 28
    out = [F.box((cx - rw, body_y0, cz - 10), (cx + rw, body_y1, cz + 10), m["black"], tile=8.0)]
    out.append(F.box((cx - rw - 14, body_y1, cz - 22), (cx + rw + 14, body_y1 + 4, cz + 22), m["black"], tile=8.0))
    out.append(F.box((cx - rw + 6, body_y1 + 4, cz - 14), (cx + rw - 6, body_y1 + 70, cz + 14), m["black"], tile=8.0))
    for ey in (body_y1 - 40, body_y1 - 95, body_y1 - 150):
        out.append(F.ellipsoid((cx, ey, cz + 10.5), (12, 9, 1.5), m["eye"], 16, 6))
        out.append(F.ellipsoid((cx, ey, cz + 11.5), (5, 5, 1.0), m["black"], 12, 4))
    for i, lx in enumerate((-22, -10, 2, 14, 24)):
        foot = np.array([cx + lx * 2.2, WATER - 5, cz + (i % 2) * 12])
        pts = np.array([[cx + lx, body_y0, cz], [cx + lx * 1.5, body_y0 - 40, cz + 8], [foot[0], WATER + 30, foot[2]], foot])
        out.append(F.sweep(pts, 1.6, m["black"], sides=6, step=6.0))
    return F.concat(out)


def build(b):
    from . import art_room
    from . import fragment as Fr
    d = b.dim("art")
    lay = b.form("art")
    rng = np.random.default_rng(1401)
    m = mats()
    view = A.ArtView(CAM, 1000, 562)
    near = log(m, rng)
    near.extend(F.box((x-.22, Y0-1.15, -HALF+1.5), (x+.22, Y0-.85, HALF-1.5), m['top']) for x in np.arange(-BX+24, BX, 48))
    near.extend(F.box((-BX, Y0-2, z-.35), (BX, Y0-1.5, z+.35), m['bark']) for z in (-HALF+2, HALF-2))
    far = [tree(m, rng, cx, cz, r, h, seed=i) for i, (cx, cz, r, h) in enumerate(TREES)]
    for i in range(9):
        a = 2 * math.pi * i / 9 + 0.2
        far.append(tree(m, rng, 560 * math.cos(a), 560 * math.sin(a), rng.uniform(36, 50), rng.uniform(340, 420),
                        seed=20 + i, niches=False))
    far.append(creature(m, view))
    # 수면: 도착 시점에 보이는 곳만 촘촘히 (원화 투영 — 위가 비친 모습), 나머지는 굵게
    water = F.plane((-160, WATER, 30), (320, 0, 0), (0, 0, -230), m["water"], tile=(16, 16))
    for x0, z0, x1, z1 in ((-600, -600, 600, -200), (-600, 30, 600, 600), (-600, -200, -160, 30), (160, -200, 600, 30)):
        lay.add(F.plane((x0, WATER, z1), (x1 - x0, 0, 0), (0, 0, z0 - z1), m["water"], tile=(16, 16))
                .tint((0.75, 0.85, 0.5), 0.75), max_edge=8.0)
    lights = [((0, 400, -300), (0.6, 0.8, 0.3), 900.0)]
    kit.project_add(lay, CAM, m["art"], near=near + [water.tint((1, 1, 1), 0.85)], far=far, lights=lights,
                    ambient=(0.55, 0.62, 0.36), glow_mats=[m["glowline"], m["eye"]], min_facing=0.12, far_edge=6.0,
                    far_min_facing=0.5)
    lay.add(kit.glass_platform(d, m["glass"], m["black"], -2.0, 3.0, HALF + 6.0, HALF + 10.0, PLAT))
    lay.add(kit.glass_stairs(m["glass"], m["black"], 4, 5, int(HALF) + 9, int(HALF) + 1, PLAT, Y0))
    kit.art_sky(lay, "art", CAM, ART, [(-90, (40, 50, 14)), (-10, (110, 130, 40)), (0, (170, 190, 70)),
                                       (25, (150, 170, 60)), (60, (80, 96, 30)), (90, (40, 50, 16))],
                cloud_e=(-4.0, 6.0), below=(60, 76, 20), zenith=(40, 50, 16))
    lay.emitter(F.Emitter((-80, WATER + 2, -80, 80, Y0 + 30, 60), rate=8.0, sprites=("ruina:block/form/paper_gold",),
                          wind=(0.1, 0.05, 0.0), size=0.12, life=8.0, spin=0.2, color=(0.75, 1.0, 0.35), glow=True))
    collision(d)
    room = art_room.build(b, d)
    Fr.stage(b, d, "iplate", "예술의 층", ARRIVE, room,
             room_box=f"x={art_room.OX - 200},y=-64,z=-1024,dx=400,dy=1024,dz=2048")
    b.extra_checks += [
        {"what": "네짜흐 방 바이옴", "cmd": f"execute in {d.dim} if biome {art_room.OX} {art_room.Y0} 0 ruina:art_room",
         "expect": True},
    ]


def collision(d):
    h = int(HALF)
    d.fill(-BX, Y0 - 1, -h, BX, Y0 - 1, h, "minecraft:barrier")
    d.fill(-BX, Y0, -h - 1, BX, Y0 + 1, -h - 1, "minecraft:barrier")      # 그루터기 줄
    kit.stair_collision(d, 4, 5, h + 9, h + 1, PLAT, Y0)


PREVIEW_CAMS = [("줄기 위", F.Camera((0.5, Y0 + 1.62, 0.0), 90.0, -5.0)),
                ("줄기 위에서 나무·괴생물체", F.Camera((0.5, Y0 + 1.62, -4.0), 180.0, -20.0))]


def preview(b):
    build(b)
