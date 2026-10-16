"""기술과학의 층 (예소드) — 자유 형체 판 (2026-10-15).

reference/기술과학의 층 전경.png: 고가도로(아스팔트 4차선·점선·철 난간)를 옆 조금 위(유리 전망 발판, 도착)에서 봄 —
녹슨 리벳 철 주탑과 늘어진 쇠사슬, 다리 아래 철 트러스와 네온 도시·무지개빛 길, 뒤 네온 빌딩 숲 속 녹슨 거대 톱니들
(천천히 돎 — 나무위키 '톱니가 돌면 층 전체가 움직임'), 가운데 가장 높은 건물 꼭대기 꼬인 조형물에서 톱니로 뻗은 케이블,
보라 구름 하늘·초승달. 지정사서 방: builders/technology_room.py.
"""
from __future__ import annotations

import math

import numpy as np

from tools import artfit as A
from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 250                 # 다리 위 (아스팔트 윗면)
GROUND = 40              # 도시 바닥
BX, HW = 340, 10.5       # 다리 반길이, 반폭 (z -10.5..10.5)
PYLON_DX, PYLON_X0 = 60, -30
PLAT = Y0 + 6                                            # 유리 전망 발판 (도착)
CAM = F.Camera((0.5, PLAT + 1.62, 10.5 + 12.2), 180.0, 15.0)
ARRIVE = (0.5, PLAT, 10.5 + 12.2, 180.0, 15.0)
ART = "reference/기술과학의 층 전경.png"
SPACE = "technology"
UP = np.array([0, 1.0, 0])


def clean_art():
    """원화에서 거대 톱니를 지운 그림 (톱니는 움직이는 형체가 대신 → 원화 투영·하늘에 겹쳐 두 번 보이지 않게)."""
    mask = A.circle_mask((1000, 562), [(px, py, pr) for px, py, pr, _ in GEARS], grow=1.12)
    return A.clean_sky(ART, mask, grow=2)


def mats():
    m = {}
    m["art"] = F.mat("tech_art", T.art("art/technology", ART, img=clean_art()), emissive=True, flat=True, ao=False)
    m["asphalt"] = F.mat("tech_asphalt", T.asphalt("tech_asphalt"), emissive=True, flat=True, ao=False)
    m["paint"] = F.mat("tech_paint", T.flat("tech_paint", (220, 216, 200)), emissive=True, flat=True, ao=False)
    m["rust"] = F.mat("tech_rust", T.rust("tech_rust"), emissive=True, flat=True, ao=False)
    m["steel"] = F.mat("tech_steel", T.metal("tech_steel", (30, 28, 34), (90, 84, 92), seed=71), emissive=True,
                       flat=True, ao=False)
    m["chain"] = F.mat("tech_chain", T.metal("tech_chain", (20, 18, 22), (70, 64, 70), seed=72), emissive=True,
                       flat=True, ao=False)
    m["gear"] = F.mat("tech_gear", T.rust("tech_gear", (60, 36, 30), (140, 90, 70), seed=73, rivets=False),
                      emissive=True, flat=True, ao=False)
    m["glass"] = F.mat("tech_glass", T.glow("tech_glass", (200, 220, 255)), layer="translucent", emissive=True,
                       flat=True, ao=False)
    pals = [((30, 22, 52), (255, 110, 220), (200, 80, 255)), ((22, 26, 50), (110, 220, 255), (90, 200, 255)),
            ((36, 24, 44), (255, 190, 110), (255, 120, 200)), ((26, 20, 40), (190, 120, 255), (150, 90, 255))]
    m["facade"] = [F.mat(f"tech_facade{i}", T.neon_facade(f"tech_facade{i}", b, (l, (255, 240, 220), l), seed=74 + i,
                                                          edge=e), emissive=True, flat=True, ao=False, glow=5)
                   for i, (b, l, e) in enumerate(pals)]
    m["roof"] = F.mat("tech_roof", T.flat("tech_roof", (24, 20, 34)), emissive=True, flat=True, ao=False)
    m["neon"] = [F.mat(f"tech_neon{i}", T.glow(f"tech_neon{i}", c), emissive=True, flat=True, ao=False, glow=5)
                 for i, c in enumerate([(255, 90, 210), (90, 220, 255), (255, 200, 90), (150, 255, 160), (200, 120, 255)])]
    m["sculpt"] = F.mat("tech_sculpt", T.metal("tech_sculpt", (60, 40, 50), (150, 110, 120), seed=75), emissive=True,
                        flat=True, ao=False)
    return m


# ---------------------------------------------------------------- 고가도로

def deck(m):
    out = [F.plane((-BX, Y0, HW), (2 * BX, 0, 0), (0, 0, -2 * HW), m["asphalt"], tile=(4, 4))]
    for zl in (-4.2, 0.0, 4.2):                                   # 점선
        for x in np.arange(-BX, BX, 6.0):
            out.append(F.box((x, Y0 + 0.015, zl - 0.12), (x + 3, Y0 + 0.035, zl + 0.12), m["paint"]))
    for zl in (-8.6, 8.6):                                        # 가장자리 실선
        out.append(F.plane((-BX, Y0 + 0.02, zl + 0.12), (2 * BX, 0, 0), (0, 0, -0.24), m["paint"], tile=(8, 1)))
    for s in (-1, 1):                                             # 옆 거더 + 리벳 띠 + 아래판
        z0, z1 = sorted((s * HW, s * (HW + 1.0)))
        out.append(F.box((-BX, Y0 - 4, z0), (BX, Y0 + 0.3, z1), m["rust"], tile=4.0))
    out.append(F.plane((-BX, Y0 - 4, -HW), (2 * BX, 0, 0), (0, 0, 2 * HW), m["steel"], tile=(8, 8)))
    for s in (-1, 1):                                             # 난간: 기둥 2칸마다 + 두 줄 가로대
        z = s * (HW + 0.5)
        for x in np.arange(-BX, BX + 0.1, 3.0):
            out.append(F.box((x - 0.08, Y0 + 0.3, z - 0.08), (x + 0.08, Y0 + 1.4, z + 0.08), m["steel"]))
        for y in (Y0 + 0.9, Y0 + 1.4):
            out.append(F.sweep(np.array([[-BX, y, z], [BX, y, z]]), 0.09, m["steel"], sides=6, step=8.0, tile_along=8))
    return out


def truss(m):
    """교각 + 대각 버팀 (주탑 아래마다) — 다리 아래 철 트러스 (원화 아래 양 모서리)."""
    out = []
    for px in np.arange(PYLON_X0 - 5 * PYLON_DX, BX, PYLON_DX):
        for s in (-1, 1):
            z = s * (HW + 0.5)
            out.append(F.box((px - 1.5, GROUND, z - 1.5), (px + 1.5, Y0 - 4, z + 1.5), m["rust"], tile=4.0))
            for side in (-1, 1):
                for a, b in (((px + 1.5 * side, Y0 - 40), (px + 26 * side, Y0 - 4)),
                             ((px + 1.5 * side, Y0 - 22), (px + 14 * side, Y0 - 4))):
                    out.append(F.sweep(np.array([[a[0], a[1], z], [b[0], b[1], z]]), 0.6, m["rust"], sides=6, step=4.0))
            for y in np.arange(Y0 - 34, Y0 - 4, 6.0):             # 격자
                out.append(F.sweep(np.array([[px - 12, y, z], [px + 12, y + 6, z]]), 0.25, m["steel"], sides=4, step=4))
                out.append(F.sweep(np.array([[px + 12, y, z], [px - 12, y + 6, z]]), 0.25, m["steel"], sides=4, step=4))
    return out


def pylons(m):
    """녹슨 리벳 철 주탑 (다리 양옆) + 처진 주케이블 + 원화의 늘어진 사선 쇠사슬."""
    out = []
    xs = np.arange(PYLON_X0 - 5 * PYLON_DX, BX, PYLON_DX)
    top = Y0 + 60
    for px in xs:
        for s in (-1, 1):
            z = s * (HW + 2.5)
            out.append(F.box((px - 1.7, Y0 - 4, z - 1.7), (px + 1.7, top, z + 1.7), m["rust"], tile=4.0))
            for y in np.arange(Y0 + 6, top, 8.0):
                out.append(F.box((px - 1.9, y, z - 1.9), (px + 1.9, y + 0.6, z + 1.9), m["steel"]))
        out.append(F.box((px - 1.5, top - 5, -HW - 2.5), (px + 1.5, top - 2, HW + 2.5), m["rust"], tile=4.0))
    for s in (-1, 1):
        z = s * (HW + 2.5)
        for a, b in zip(xs[:-1], xs[1:]):
            out.append(kit.chain((a, top - 3, z), (b, top - 3, z), 20.0, m["chain"], link=1.6, radius=0.16))
        for px in xs:
            for dx in (-34, 34):
                out.append(kit.chain((px, top - 8, z), (px + dx, Y0 + 1.5, -z), 4.0, m["chain"], link=1.6, radius=0.14))
    return out


# ---------------------------------------------------------------- 도시·톱니·탑

def city(m, rng):
    near, far = [], []
    placed = []
    for ring, (r0, r1, n, hmin, hmax) in enumerate(((40, 360, 230, 150, 290), (430, 900, 90, 130, 290))):
        for _ in range(n * 4):
            if sum(1 for p in placed if p[4] == ring) >= n:
                break
            a = rng.uniform(0, 2 * math.pi)
            r = math.sqrt(rng.uniform(r0 ** 2, r1 ** 2))
            cx, cz = r * math.cos(a), r * math.sin(a)
            if abs(cz) < HW + 18 and abs(cx) <= BX + 10:
                continue
            w, l = rng.uniform(12, 26), rng.uniform(12, 26)
            if any(abs(cx - px) < (w + pw) / 2 + 3 and abs(cz - pz) < (l + pl) / 2 + 3 for px, pz, pw, pl, _ in placed):
                continue
            placed.append((cx, cz, w, l, ring))
            h = rng.uniform(hmin, hmax)
            q = kit.building(cx - w / 2, cz - l / 2, cx + w / 2, cz + l / 2, GROUND, GROUND + h,
                             m["facade"][int(rng.integers(4))], m["roof"], tile=(8.0, 8.0))
            # 모서리 네온 줄
            neon = m["neon"][int(rng.integers(5))]
            for x, z in ((cx - w / 2, cz - l / 2), (cx + w / 2, cz + l / 2)):
                q = F.concat([q, F.box((x - 0.25, GROUND, z - 0.25), (x + 0.25, GROUND + h, z + 0.25), neon, tile=8.0)])
            (near if ring == 0 else far).append(q)
    # 바닥 + 무지개빛 길 (다리 아래)
    near.append(F.plane((-420, GROUND, 420), (840, 0, 0), (0, 0, -840), m["roof"], tile=(16, 16)))
    for k in range(2):
        t = np.linspace(0, 1, 300)
        path = np.stack([-360 + 720 * t, np.full_like(t, GROUND + 0.1), 60 * np.sin(t * 5 + k * 2) + (-40 if k else 50)], 1)
        rib = F.ribbon(path, 3.0, m["neon"][k], up=UP, step=2.0, tile_along=6.0)
        rib = rib.color_by(lambda P, N: np.stack([0.6 + 0.4 * np.sin(P[:, 0] * 0.02 + 0),
                                                  0.6 + 0.4 * np.sin(P[:, 0] * 0.02 + 2),
                                                  0.6 + 0.4 * np.sin(P[:, 0] * 0.02 + 4)], 1))
        near.append(rib)
    return near, far


GEARS = [  # 원화 위치 (픽셀 상자 가운데 x, y, 반지름 px) → 깊이 z 에 세움, 축 = z (정면을 봄)
    (285, 60, 95, -260), (620, 190, 85, -200), (800, 55, 70, -300), (655, 92, 38, -240), (725, 190, 40, -190),
    (340, 200, 50, -170),
]


def gears(lay, m, view):
    """거대 톱니 (움직임: 천천히 회전). 자리 = 원화 픽셀 → 깊이 z."""
    for i, (px, py, pr, z) in enumerate(GEARS):
        c = view.at_z(np.array([float(px)]), np.array([float(py)]), z)[0]
        R = pr * view.px_size(c)
        mesh = kit.gear(c, (0, 0, 1), R, m["gear"], teeth=int(10 + R / 6), thick=max(2.0, R * 0.12))
        mesh = F.bake_points(mesh, [((0, 600, 200), (0.6, 0.45, 0.7), 900.0)], ambient=(0.45, 0.32, 0.4))
        lay.mover(F.Mover(tuple(int(v) for v in c), mesh, tuple(c), "spin", (0, 0, 1 if i % 2 else -1),
                          period=90.0 + 20 * i, radius=R * 1.3))


def tower(m, view):
    """가운데 가장 높은 건물 + 꼭대기 꼬인 조형물 + 톱니로 뻗는 케이블 (원화 가운데 위)."""
    c = view.at_z(np.array([480.0]), np.array([70.0]), -230.0)[0]
    out = [kit.building(c[0] - 14, c[2] - 14, c[0] + 14, c[2] + 14, GROUND, c[1] - 10, m["facade"][3], m["roof"],
                        tile=(8.0, 8.0))]
    t = np.linspace(0, 1, 60)
    spiral = np.stack([c[0] + 6 * np.cos(t * 9) * (1 - t * 0.6), c[1] - 10 + t * 34, c[2] + 6 * np.sin(t * 9) * (1 - t * 0.6)],
                      1)
    out.append(F.sweep(spiral, lambda s: 3.0 * (1 - s) + 0.8, m["sculpt"], sides=8, step=1.0))
    tip = np.array([c[0], c[1] + 20, c[2]])
    for px, py, pr, z in GEARS[:3]:
        g = view.at_z(np.array([float(px)]), np.array([float(py)]), z)[0]
        out.append(F.sweep(np.array([tip, g]), 0.35, m["chain"], sides=4, step=20.0))
    return out


def build(b):
    from . import fragment as Fr
    from . import technology_room
    d = b.dim("technology")
    lay = b.form("technology")
    rng = np.random.default_rng(901)
    m = mats()
    view = A.ArtView(CAM, 1000, 562)
    near = deck(m) + pylons(m)
    near.extend(F.box((-BX, Y0-2, z-.35), (BX, Y0-1.55, z+.35), m['steel']) for z in (-HW+2, HW-2))
    cn, cf = city(m, rng)
    far = truss(m) + cn + cf + tower(m, view)
    lights = [((0, 900, -400), (0.7, 0.45, 0.85), 1400.0)]
    glow = [*m["neon"], *m["facade"], m["paint"]]
    kit.project_add(lay, CAM, m["art"], near=near, far=far, lights=lights, ambient=(0.55, 0.42, 0.6), glow_mats=glow,
                    min_facing=0.12, far_edge=8.0, far_min_facing=0.6)
    gears(lay, m, view)
    lay.add(kit.glass_platform(d, m["glass"], m["steel"], -2.0, 3.0, 20.0, 25.0, PLAT))
    lay.add(kit.glass_stairs(m["glass"], m["steel"], 4, 5, 24, 11, PLAT, Y0))     # 발판 동쪽 → 다리 남쪽 갓길
    kit.art_sky(lay, "tech", CAM, ART, [(-90, (20, 10, 30)), (-10, (60, 30, 80)), (0, (120, 70, 150)), (15, (160, 110, 190)),
                                        (35, (130, 90, 170)), (60, (80, 50, 120)), (90, (40, 24, 70))],
                city=dict(near=24, far=16, dark=(30, 20, 50), glow=(200, 90, 230), rim=(120, 200, 255)),
                cloud_e=(20.0, 40.0), below=(16, 10, 26), zenith=(40, 24, 70), clean=clean_art())
    collision(d)
    room = technology_room.build(b, d)
    Fr.stage(b, d, "iron", "기술과학의 층", ARRIVE, room,
             room_box=f"x={technology_room.OX - 200},y=-64,z=-1024,dx=400,dy=1024,dz=2048")
    b.extra_checks += [
        {"what": "예소드 방 바이옴", "cmd": f"execute in {d.dim} if biome {technology_room.OX} {technology_room.Y0} 0 "
                                       f"ruina:technology_room", "expect": True},
    ]


def collision(d):
    d.fill(-BX, Y0 - 1, -int(HW), BX, Y0 - 1, int(HW), "minecraft:barrier")          # 노면
    for z in (-int(HW) - 1, int(HW)):
        d.fill(-BX, Y0, z, BX, Y0 + 1, z, "minecraft:barrier")                       # 난간 (2칸)
    for px in range(PYLON_X0 - 5 * PYLON_DX, BX, PYLON_DX):
        for s in (-1, 1):
            z = int(math.floor(s * (HW + 2.5)))
            d.fill(px - 2, Y0, z - 2, px + 1, Y0 + 60, z + 1, "minecraft:barrier")
    kit.stair_collision(d, 4, 5, 24, 11, PLAT, Y0)
    d.fill(4, Y0, int(HW), 5, Y0 + 1, int(HW), "minecraft:air")                     # 난간 틈 (계단 끝)


PREVIEW_CAMS = [("다리 위 (차선)", F.Camera((0.5, Y0 + 1.62, 0.0), 90.0, 0.0)),
                ("다리 위에서 도시·톱니", F.Camera((0.5, Y0 + 1.62, -8.0), 180.0, -15.0)),
                ("다리 아래", F.Camera((30.0, 120.0, 40.0), 200.0, -20.0))]


def preview(b):
    build(b)
