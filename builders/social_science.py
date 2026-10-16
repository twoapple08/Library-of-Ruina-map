"""사회과학의 층 (헤세드) — 자유 형체 판 (2026-10-15).

reference/사회과학의 층 전경.png: 바다 깊이 가라앉은 난파선 갑판(낡은 판자, 구멍)을 옆 조금 위(유리 전망 발판, 도착)에서 봄 —
아래 선체 옆면과 밧줄 감긴 계류 기둥·처진 밧줄, 해초(살랑), 뒤로 소용돌이치는 푸른 물결과 빛기둥, 푸른 안개 속 잠긴 도시,
기울어진 채 떠다니는 폐차(천천히 돌며 오르내림), 물고기 떼(둥글게 헤엄). 물속은 공기 + 푸른 그린 하늘 + 떠다니는 입자.
지정사서 방: builders/social_science_room.py.
"""
from __future__ import annotations

import math

import numpy as np

from tools import artfit as A
from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 100
BX, HW = 150, 10.5
FLOOR = 20
PLAT = Y0 + 4
CAM = F.Camera((0.5, PLAT + 1.62, HW + 10.95), 180.0, 9.0)
ARRIVE = (0.5, PLAT, HW + 10.95, 180.0, 9.0)
ART = "reference/사회과학의 층 전경.png"
SPACE = "social_science"
UP = np.array([0, 1.0, 0])
CARS = [(105, 120, 40, -60), (275, 75, 38, -90), (360, 195, 22, -40), (635, 190, 60, -50), (865, 65, 34, -110)]


def mats():
    m = {}
    m["art"] = F.mat("soc_art", T.art("art/social_science", ART, img=clean_art()), emissive=True, flat=True, ao=False)
    m["deck"] = F.mat("soc_deck", T.planks("soc_deck", (30, 34, 40), (84, 92, 104), boards=4, seed=191), emissive=True,
                      flat=True, ao=False)
    m["hull"] = F.mat("soc_hull", T.board("soc_hull", (20, 24, 30), (60, 70, 84), w=16, h=32, seed=192), emissive=True,
                      flat=True, ao=False)
    m["rope"] = F.mat("soc_rope", T.bark("soc_rope", (90, 84, 70), (160, 150, 120), seed=193), emissive=True, flat=True,
                      ao=False)
    m["weed"] = F.mat("soc_weed", T.glow("soc_weed", (60, 140, 90)), layer="cutout", emissive=True, flat=True, ao=False)
    m["car"] = [F.mat(f"soc_car{i}", T.metal(f"soc_car{i}", c0, c1, seed=194 + i), emissive=True, flat=True, ao=False)
                for i, (c0, c1) in enumerate([((20, 24, 50), (60, 70, 120)), ((20, 50, 30), (60, 120, 70)),
                                              ((40, 30, 40), (90, 70, 90))])]
    m["window"] = F.mat("soc_window", T.glow("soc_window", (120, 200, 255)), emissive=True, flat=True, ao=False, glow=2)
    m["city"] = [F.mat(f"soc_city{i}", T.neon_facade(f"soc_city{i}", b, ((90, 180, 255), (60, 140, 220), (140, 220, 255)),
                                                      seed=197 + i, ratio=0.2, edge=(40, 120, 200)),
                       emissive=True, flat=True, ao=False)
                 for i, b in enumerate([(14, 30, 60), (18, 40, 70)])]
    m["beam"] = F.mat("soc_beam", T.glow("soc_beam", (120, 220, 255)), layer="translucent", emissive=True, flat=True,
                      ao=False)
    m["fish"] = F.mat("soc_fish", T.metal("soc_fish", (40, 70, 110), (120, 170, 210), seed=199), emissive=True,
                      flat=True, ao=False)
    m["glass"] = F.mat("soc_glass", T.glow("soc_glass", (160, 220, 255)), layer="translucent", emissive=True,
                       flat=True, ao=False)
    return m


def clean_art():
    """원화에서 떠다니는 폐차를 지운 그림 (폐차는 움직이는 형체가 대신)."""
    return A.clean_sky(ART, A.circle_mask((1000, 562), [(x, y, r) for x, y, r, _ in CARS], grow=1.15), grow=2)


def deck(m, rng):
    out = [F.plane((-BX, Y0, HW), (2 * BX, 0, 0), (0, 0, -2 * HW), m["deck"], tile=(4, 4))]
    for _ in range(14):                                         # 구멍 (검게)
        x, z = rng.uniform(-BX, BX), rng.uniform(-HW + 2, HW - 2)
        w, l = rng.uniform(1.5, 4), rng.uniform(0.8, 2)
        out.append(F.box((x, Y0 + 0.015, z), (x + w, Y0 + 0.055, z + l), m["hull"]).tint((0.15, 0.15, 0.2)))
    for s in (-1, 1):                                           # 선체 옆면 (아래로)
        z = s * HW
        f = 1 if s > 0 else -1
        out.append(F.plane((-BX if f > 0 else BX, FLOOR, z), (2 * BX * f, 0, 0), (0, Y0 - FLOOR, 0), m["hull"],
                           tile=(3, 6)))
        out.append(F.box((-BX, Y0 - 0.8, min(z, z + s * 0.6)), (BX, Y0 + 0.4, max(z, z + s * 0.6)), m["hull"], tile=4.0))
    # 뒤 부서진 뱃전 (울퉁불퉁)
    for x in np.arange(-BX, BX, 3.0):
        h = rng.uniform(0.2, 1.8)
        out.append(F.box((x, Y0, -HW - 0.6), (x + 3, Y0 + h, -HW), m["hull"], tile=2.0))
    # 앞 계류 기둥 + 감긴 밧줄 + 기둥 사이 처진 밧줄 (원화 아래)
    posts = np.arange(-BX + 20, BX, 60.0) + 4.0
    for x in posts:
        z = HW + 0.8
        out.append(F.revolve([(0.55, Y0 - 9), (0.55, Y0 + 0.6), (0.75, Y0 + 0.9), (0.4, Y0 + 1.2)], m["hull"], segs=12,
                             center=(x, 0, z), tiles_around=3, tile_up=3.0))
        t = np.linspace(0, 1, 60)
        coil = np.stack([x + 0.62 * np.cos(t * 30), Y0 - 1.5 - 2.5 * t, z + 0.62 * np.sin(t * 30)], 1)
        out.append(F.sweep(coil, 0.13, m["rope"], sides=4, step=0.3))
    for a, b in zip(posts[:-1], posts[1:]):
        out.append(kit.chain((a, Y0 - 1.5, HW + 1.2), (b, Y0 - 1.5, HW + 1.2), 10.0, m["rope"], link=0.8, radius=0.1)
                   if False else F.sweep(np.array([[a + (b - a) * t, Y0 - 1.5 - 10 * 4 * t * (1 - t), HW + 1.3]
                                                    for t in np.linspace(0, 1, 20)]), 0.18, m["rope"], sides=5, step=1.0))
    return out


def seaweed(lay, m, rng):
    """해초: 선체 아래·바닥에서 오르는 띠 (가까운 것은 살랑)."""
    out = []
    for i in range(70):
        x, z = rng.uniform(-BX, BX), rng.uniform(HW + 1, HW + 25)
        h = rng.uniform(6, 22)
        t = np.linspace(0, 1, 8)
        path = np.stack([x + np.sin(t * 4 + i) * 0.8, FLOOR + h * t + (Y0 - 30 - FLOOR) * 0.0 + rng.uniform(40, 60) * 0,
                         z + np.cos(t * 3 + i) * 0.5], 1)
        path[:, 1] += rng.uniform(55, 70)
        rib = F.ribbon(path, lambda s: 0.9 * (1 - s) + 0.2, m["weed"], up=[1, 0, 0.3], step=1.5, tile_along=3.0)
        if abs(x) < 40:
            lay.mover(F.Mover((int(x), int(path[0, 1]) + 1, int(z)), rib, tuple(path[0]), "swing", (0, 0, 1),
                              period=rng.uniform(4, 7), amp=8.0, phase=rng.random()))
        else:
            out.append(rib)
    return out


def car_mesh(m, k, L=4.4):
    """폐차 (몸통 + 지붕 + 바퀴 넷), 길이 L."""
    w, h = L * 0.42, L * 0.3
    out = [F.box((-L / 2, 0, -w / 2), (L / 2, h * 0.55, w / 2), m["car"][k]),
           F.box((-L * 0.25, h * 0.55, -w / 2 + 0.1), (L * 0.2, h, w / 2 - 0.1), m["car"][k])]
    out.append(F.box((-L * 0.22, h * 0.6, -w / 2 + 0.05), (L * 0.17, h * 0.95, w / 2 - 0.05), m["window"]).tint((0.4, 0.5, 0.6)))
    for x in (-L * 0.32, L * 0.32):
        for z in (-w / 2, w / 2):
            out.append(F.ellipsoid((x, 0.05, z), (L * 0.1, L * 0.1, 0.12), m["car"][2], 10, 4))
    return F.concat(out)


def cars(lay, m, view, rng):
    for i, (px, py, pr, z) in enumerate(CARS):
        c = view.at_z(np.array([float(px)]), np.array([float(py)]), z)[0]
        L = pr * 2.1 * view.px_size(c)
        mesh = car_mesh(m, i % 3, L).rotate("z", rng.uniform(-40, 40)).rotate("y", rng.uniform(0, 360)).translate(c)
        lay.mover(F.Mover(tuple(int(v) for v in c), mesh, tuple(c), "spin",
                          (rng.uniform(-0.3, 0.3), 1, rng.uniform(-0.3, 0.3)), period=rng.uniform(60, 120)))
    for _ in range(14):                                          # 멀리 더 (원화 밖)
        c = np.array([rng.uniform(-300, 300), rng.uniform(Y0 - 20, Y0 + 120), rng.uniform(-350, -60)])
        mesh = car_mesh(m, int(rng.integers(3)), rng.uniform(4, 7)).rotate("z", rng.uniform(-60, 60)).translate(c)
        lay.mover(F.Mover(tuple(int(v) for v in c), mesh, tuple(c), "bob", (0, 1, 0), period=rng.uniform(8, 14),
                          amp=rng.uniform(1, 3)))


def fish(lay, m, rng):
    """물고기 떼: 축 둘레를 도는 형체 (spin = 원 궤도)."""
    for g in range(12):
        cx, cy, cz = rng.uniform(-120, 120), rng.uniform(Y0 - 10, Y0 + 60), rng.uniform(-120, -20)
        R = rng.uniform(6, 16)
        body = []
        for k in range(int(rng.integers(5, 12))):
            a = rng.uniform(0, 2 * math.pi)
            p = np.array([cx + R * math.cos(a) + rng.uniform(-1, 1), cy + rng.uniform(-2, 2), cz + R * math.sin(a)])
            f = F.ellipsoid((0, 0, 0), (0.5, 0.18, 0.12), m["fish"], 8, 4)
            tail = F.Quads(np.array([[[-0.45, 0, 0], [-0.8, 0.2, 0], [-0.8, -0.2, 0], [-0.8, -0.2, 0]]]),
                           np.array([[[0, 0], [1, 0], [1, 1], [1, 1]]]) * 0.9, M=m["fish"])
            f = F.concat([f, F.two_sided(tail)]).rotate("y", -math.degrees(a) - 90).translate(p)
            body.append(f)
        lay.mover(F.Mover((int(cx), int(cy), int(cz)), F.concat(body), (cx, cy, cz), "spin", (0, 1, 0),
                          period=rng.uniform(20, 40)))


def city(m, rng):
    out = []
    for _ in range(140):
        a = rng.uniform(0, 2 * math.pi)
        r = math.sqrt(rng.uniform(60 ** 2, 420 ** 2))
        cx, cz = r * math.cos(a), r * math.sin(a)
        if abs(cz) < HW + 30 and abs(cx) < BX + 20:
            continue
        w, l, h = rng.uniform(12, 28), rng.uniform(12, 28), rng.uniform(60, 200)
        out.append(kit.building(cx - w / 2, cz - l / 2, cx + w / 2, cz + l / 2, FLOOR, FLOOR + h,
                                m["city"][int(rng.integers(2))], m["hull"], tile=(8.0, 8.0))
                   .rotate("z", rng.uniform(-6, 6), origin=(cx, FLOOR, cz)))
    out.append(F.plane((-450, FLOOR, 450), (900, 0, 0), (0, 0, -900), m["hull"], tile=(16, 16)).tint((0.4, 0.5, 0.6)))
    for x in (-300, -80, 120, 340):                              # 빛기둥
        out.append(F.revolve([(9, FLOOR), (7, Y0 + 200)], m["beam"], segs=16, center=(x, 0, -200), tiles_around=4,
                             tile_up=16).tint((1, 1, 1), 0.25))
    return out


def build(b):
    from . import fragment as Fr
    from . import social_science_room
    d = b.dim("social_science")
    lay = b.form("social_science")
    rng = np.random.default_rng(1701)
    m = mats()
    view = A.ArtView(CAM, 1000, 562)
    near = deck(m, rng)
    far = city(m, rng) + seaweed(lay, m, rng)
    lights = [((0, Y0 + 200, -150), (0.4, 0.75, 1.1), 500.0)]
    kit.project_add(lay, CAM, m["art"], near=near, far=far, lights=lights, ambient=(0.34, 0.48, 0.66),
                    glow_mats=[m["window"], m["beam"]], min_facing=0.12, far_edge=6.0, far_min_facing=0.5)
    cars(lay, m, view, rng)
    fish(lay, m, rng)
    lay.add(kit.glass_platform(d, m["glass"], m["hull"], -2.0, 3.0, HW + 9.0, HW + 13.0, PLAT))
    lay.add(kit.glass_stairs(m["glass"], m["hull"], 4, 5, int(HW) + 12, int(HW) + 1, PLAT, Y0))
    kit.art_sky(lay, "soc", CAM, ART, [(-90, (6, 14, 30)), (-20, (14, 40, 80)), (0, (30, 90, 160)), (30, (40, 130, 220)),
                                       (60, (20, 70, 140)), (90, (8, 24, 60))],
                cloud_e=(10.0, 40.0), below=(8, 20, 40), zenith=(8, 24, 60), clean=clean_art())
    lay.emitter(F.Emitter((-60, Y0 - 30, -60, 60, Y0 + 40, 40), rate=8.0, sprites=("ruina:block/form/paper_1",),
                          wind=(0.05, 0.25, 0.0), size=0.08, life=10.0, spin=0.2, color=(0.6, 0.85, 1.0), glow=True))
    collision(d)
    room = social_science_room.build(b, d)
    Fr.stage(b, d, "gblock", "사회과학의 층", ARRIVE, room,
             room_box=f"x={social_science_room.OX - 200},y=-64,z=-1024,dx=400,dy=1024,dz=2048")
    b.extra_checks += [
        {"what": "헤세드 방 바이옴", "cmd": f"execute in {d.dim} if biome {social_science_room.OX} {social_science_room.Y0} 0 "
                                       f"ruina:social_science_room", "expect": True},
    ]


def collision(d):
    d.fill(-BX, Y0 - 1, -int(HW), BX, Y0 - 1, int(HW), "minecraft:barrier")
    d.fill(-BX, Y0, -int(HW) - 1, BX, Y0 + 1, -int(HW) - 1, "minecraft:barrier")
    d.fill(-BX, Y0, int(HW) + 1, BX, Y0, int(HW) + 1, "minecraft:barrier")
    kit.stair_collision(d, 4, 5, int(HW) + 12, int(HW) + 1, PLAT, Y0)
    d.fill(4, Y0, int(HW) + 1, 5, Y0, int(HW) + 1, "minecraft:air")


PREVIEW_CAMS = [("갑판 위", F.Camera((0.5, Y0 + 1.62, 0.0), 90.0, 0.0)),
                ("갑판에서 도시", F.Camera((0.5, Y0 + 1.62, -6.0), 180.0, -10.0))]


def preview(b):
    build(b)
