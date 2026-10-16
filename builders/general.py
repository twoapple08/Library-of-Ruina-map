"""총류의 층 (롤랑) — 자유 형체 판 (2026-10-15). 마지막 층.

reference/총류의 층 전경.png: 가장자리가 책 층층이 드러난 다리(위 잿빛 큰 돌판, 작은 책 더미 피라미드, 흩어진 책)를
옆 조금 위(유리 전망 발판, 도착)에서 봄 — 뒤로 비틀려 솟은 책탑 다섯, 그 뒤 옅은 안개 속 빌딩만 한 책장 벽(위 오른쪽에서
빛), 다리 아래 어두운 물과 떨어지는 종이. PLAN.md 8절: 책이 산더미처럼 쌓임, 빌딩만 한 책꽂이, 책더미 다리, 책탑.
지정사서 방: builders/general_room.py.
"""
from __future__ import annotations

import math

import numpy as np

from tools import artfit as A
from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 120
BX, HW = 200, 14.5
WATER = Y0 - 60
PLAT = Y0 + 2
CAM = F.Camera((0.5, PLAT + 1.62, HW + 9.84), 180.0, 6.75)
ARRIVE = (0.5, PLAT, HW + 9.84, 180.0, 6.75)
ART = "reference/총류의 층 전경.png"
SPACE = "general"
AW, AH = 1000, 562
TOWERS = [  # 원화 (1000×562) 가운데 선 [(x, y, 반폭 px)] (위 → 아래), 깊이 z
    ([(95, 0, 95), (110, 60, 100), (150, 140, 120), (150, 200, 118), (150, 262, 120)], -45.0),
    ([(345, 80, 25), (380, 120, 38), (410, 170, 45), (400, 215, 50), (380, 255, 55)], -80.0),
    ([(520, 15, 20), (510, 60, 26), (540, 120, 30), (560, 180, 36), (590, 230, 45), (580, 250, 50)], -95.0),
    ([(735, 35, 12), (745, 90, 18), (735, 140, 22), (725, 190, 25), (720, 228, 28)], -130.0),
    ([(880, 0, 36), (900, 60, 40), (930, 130, 46), (910, 190, 52), (890, 252, 62)], -70.0),
]
PILES = [(40, 345, 30), (120, 355, 18), (465, 330, 20), (690, 272, 26), (800, 370, 16), (960, 355, 34)]   # 책 더미 (x, y, 반폭)


def clean_art():
    boxes = []
    for pts, _ in TOWERS:
        for (x0, y0, r0), (x1, y1, r1) in zip(pts, pts[1:]):
            boxes.append((min(x0, x1) - max(r0, r1) - 8, y0 - 6, max(x0, x1) + max(r0, r1) + 8, y1 + 6))
    boxes.append((0, 222, AW, AH))
    return A.clean_sky(ART, A.box_mask((AW, AH), boxes), grow=2)


def mats():
    m = {}
    m["art"] = F.mat("gen_art", T.art("art/general", ART), emissive=True, flat=True, ao=False)
    m["slab"] = F.mat("gen_slab", T.stone_slab("gen_slab", (60, 60, 66), (120, 120, 128), seed=251), emissive=True,
                      flat=True, ao=False)
    m["books"] = [F.mat(f"gen_books{i}", T.book_stack(f"gen_books{i}", seed=252 + i), emissive=True, flat=True, ao=False)
                  for i in range(3)]
    m["shelf"] = [F.mat(f"gen_shelf{i}", T.shelf(f"gen_shelf{i}", [(150, 146, 136), (120, 116, 110), (180, 176, 164),
                                                                     (96, 92, 88), (200, 194, 180)],
                                                  wood=(130, 126, 118), seed=255 + i, dark_back=(70, 68, 66)),
                        emissive=True, flat=True, ao=False) for i in range(2)]
    m["water"] = F.mat("gen_water", T.flat("gen_water", (18, 22, 36)), emissive=True, flat=True, ao=False)
    m["page"] = F.mat("gen_page", T.paper("gen_page", (220, 214, 200), alpha=False), emissive=True, flat=True, ao=False)
    m["glass"] = F.mat("gen_glass", T.glow("gen_glass", (235, 232, 224)), layer="translucent", emissive=True, flat=True,
                       ao=False)
    m["fog"] = F.mat("gen_fog", T.glow("gen_fog", (200, 196, 186)), layer="translucent", emissive=True, flat=True,
                     ao=False)
    m["light"] = F.mat("gen_light", T.glow("gen_light", (255, 236, 200)), emissive=True, flat=True, ao=False, glow=3)
    return m


def book(m, rng, c, w, d, h, yaw):
    """눕힌 책 한 권 (또는 한 묶음): 옆면 책 더미 결, 위 표지."""
    i = int(rng.integers(3))
    q = F.box((-w / 2, 0, -d / 2), (w / 2, h, d / 2), m["books"][i], tile=1.0)
    # 낱권의 윗표지와 책장 단면을 별도 두께로 표현한다.
    cover = F.box((-w/2-.035, h, -d/2-.035), (w/2+.035, h+.045, d/2+.035), m['slab'])
    return F.concat([q, cover]).rotate('y', yaw).translate(c)


def edge_books(m, rng, z, outward, depth=(2.5, 4.5), step=1.2):
    """다리 가장자리: 책 층층이 (아래로 들쭉날쭉, 한 겹마다 조금씩 내밀거나 들어감)."""
    out = []
    x = -BX
    while x < BX:
        L = rng.uniform(1.2, 3.5)
        dep = rng.uniform(*depth) + 1.5 * math.sin(x * 0.05) ** 2
        y = Y0
        while y > Y0 - dep:
            h = rng.uniform(0.25, 0.55)
            o = rng.uniform(-0.35, 0.45)
            zc = z + outward * o
            out.append(F.box((x, y - h, min(zc, zc - outward * 2.2)), (x + L, y, max(zc, zc - outward * 2.2)),
                             m["books"][int(rng.integers(3))], tile=1.0, faces="xXzZy"))
            y -= h
        x += L * rng.uniform(0.9, 1.0)
    return out


def pile(m, rng, c, r):
    """작은 책 더미 피라미드 (층마다 좁아짐)."""
    out = []
    y = c[1]
    w = r
    while w > 0.35:
        n = max(1, int(w / 0.7))
        for k in range(n):
            bx = c[0] - w + (k + 0.5) * 2 * w / n
            out.append(book(m, rng, (bx + rng.uniform(-0.1, 0.1), y, c[2] + rng.uniform(-0.2, 0.2)),
                            rng.uniform(0.55, 0.8), rng.uniform(0.4, 0.6), rng.uniform(0.18, 0.3), rng.uniform(-25, 25)))
        y += 0.25
        w -= rng.uniform(0.3, 0.45)
    return out


def bridge(m, rng, view):
    # 위·아래·측면을 가진 실제 두께의 석재 보행판.
    out = [F.box((-BX, Y0-0.55, -HW), (BX, Y0, HW), m['slab'], tile=3.0)]
    # 가장자리 책층 아래의 연속 받침과 일정 간격 횡보.
    out += [F.box((-BX, Y0-5.35, z-.45), (BX, Y0-4.85, z+.45), m['books'][0]) for z in (-HW+2, HW-2)]
    out += [F.box((x-.3, Y0-5.3, -HW+2), (x+.3, Y0-4.9, HW-2), m['books'][1]) for x in np.arange(-BX+24, BX, 48)]
    out += edge_books(m, rng, HW, 1.0)
    out += edge_books(m, rng, -HW, -1.0, depth=(2.0, 3.5))
    out.append(F.box((-BX, Y0-5.25, -HW), (BX, Y0-5, HW), m['books'][0], tile=4.0))
    x = -BX                                                    # 뒤 가장자리 위 책 더미 줄 (들쭉날쭉)
    while x < BX:
        L = rng.uniform(1.5, 4.0)
        for k in range(int(rng.integers(1, 4))):
            out.append(book(m, rng, (x + L / 2, Y0 + k * 0.4, -HW + 0.8 + rng.uniform(-0.3, 0.3)), L * rng.uniform(0.7, 1.0),
                            rng.uniform(0.8, 1.4), 0.4, rng.uniform(-6, 6)))
        x += L
    for px, py, pr in PILES:
        v = view.ray(np.array([float(px)]), np.array([float(py)]))[0]
        t = (Y0 - view.C[1]) / v[1]
        c = view.C + t * v
        r = pr * float(view.px_size(c))
        out += pile(m, rng, (c[0], Y0, c[2]), max(0.8, r))
    for _ in range(int(2 * BX * 0.12)):                         # 흩어진 책 (다리 위)
        x, z = rng.uniform(-BX, BX), rng.uniform(-HW + 1, HW - 1)
        if abs(x) < 6 and z > HW - 6:
            continue
        out.append(book(m, rng, (x, Y0, z), rng.uniform(0.5, 0.8), rng.uniform(0.35, 0.55), rng.uniform(0.1, 0.2),
                        rng.uniform(0, 180)))
    for x in np.arange(-BX + 50, BX, 60):                       # 받침 책 기둥 (물 속으로, 다리 안쪽)
        for z in (-HW + 8, HW - 8):
            out += tower(m, rng, [(x, Y0 - 5, z, 3.0), (x + rng.uniform(-3, 3), WATER - 4, z + rng.uniform(-2, 2), 3.5)],
                         layer=1.2)
    return out


def tower(m, rng, path, layer=1.0):
    """비틀려 솟은 책탑: 경로 [(x, y, z, 반폭)] 를 따라 책 묶음을 층층이 (층마다 방향을 틀고 어긋나게). 꺾인 머리도 따라감."""
    P = np.array([p[:3] for p in path], float)
    R = np.array([p[3] for p in path], float)
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    out = []
    t = 0.0
    ph = rng.uniform(0, 6.3)
    while t < s[-1]:
        c = np.array([np.interp(t, s, P[:, k]) for k in range(3)])
        r = float(np.interp(t, s, R))
        h = layer * rng.uniform(0.7, 1.3)
        for _ in range(max(1, int(r / 3))):
            w = r * rng.uniform(1.4, 1.9)
            d = r * rng.uniform(0.8, 1.2)
            off = rng.uniform(-0.15, 0.15, 2) * r
            yaw = 12 * math.sin(t * 0.07 + ph) + rng.uniform(-8, 8)
            out.append(F.box((-w / 2, -h / 2, -d / 2), (w / 2, h / 2, d / 2), m["books"][int(rng.integers(3))],
                             tile=max(1.0, layer * 1.5)).rotate("y", yaw).translate((c[0] + off[0], c[1], c[2] + off[1])))
        t += min(h * 0.9, max(0.3, r * 0.5))
    return out


def towers(m, rng, view):
    out = []
    for pts, z in TOWERS:
        path = []
        for px, py, pr in pts:
            c = view.at_z(np.array([float(px)]), np.array([float(py)]), z)[0]
            path.append((c[0], c[1], c[2], pr * float(view.px_size(c))))
        # 위로 이어 (원화 밖) 가늘게, 아래로 물까지
        (x0, y0, z0, r0), (x1, y1, z1, _r1) = path[0], path[1]
        up = np.array([x0 - x1, y0 - y1, 0.0])
        up = up / max(1e-6, np.linalg.norm(up))
        top = np.array([x0, y0, z0]) + up * 40.0
        path = [(top[0] + 6 * math.sin(z), top[1], top[2], r0 * 0.6)] + path
        xb, yb, zb, rb = path[-1]
        path.append((xb + rng.uniform(-6, 6), WATER - 4, zb, rb * 1.15))
        out += tower(m, rng, path, layer=max(1.2, path[-2][3] * 0.12))
    return out


def backdrop(m, rng):
    """빌딩만 한 책장 벽 (뒤 반원 + 둘레), 안개 겹, 물."""
    out = []
    for i in range(36):
        deg = i * 10 + rng.uniform(-3, 3)
        if abs(((deg + 90) + 180) % 360 - 180) < 70:          # 도착 시야(북쪽)는 그린 하늘의 책장 벽이 맡음
            continue
        a = math.radians(deg)
        r = rng.uniform(260, 360) if math.sin(a) < 0 else rng.uniform(320, 480)
        cx, cz = r * math.cos(a), r * math.sin(a)
        w, d = rng.uniform(50, 90), rng.uniform(30, 60)
        h = rng.uniform(300, 460)
        q = kit.building(-w / 2, -d / 2, w / 2, d / 2, WATER - 4, Y0 + h, m["shelf"][i % 2], tile=(6.0, 6.0))
        if r < 340:
            q = F.concat([q, F.box((-w/2-.8, WATER-4, -d/2), (-w/2+.8, Y0+h, d/2), m["slab"])])
        out.append(q.rotate("y", -math.degrees(a) + 90).translate((cx, 0, cz)))
    out.append(F.plane((-700, WATER, 700), (1400, 0, 0), (0, 0, -1400), m["water"], tile=(32, 32)))
    for y in (WATER + 20, Y0 - 15, Y0 + 60):
        out.append(F.plane((-600, y, -600), (1200, 0, 0), (0, 0, 1200), m["fog"], tile=(32, 32)).tint((1, 1, 1), 0.12))
    return out


def build(b):
    from . import fragment as Fr
    from . import general_room
    d = b.dim("general")
    lay = b.form("general")
    rng = np.random.default_rng(2501)
    m = mats()
    view = A.ArtView(CAM, AW, AH)
    near = bridge(m, rng, view)
    # 도착점 가까이에서 개별 책등과 표지가 보이는 낮은 책 더미.
    for x in (-18, -11, 13, 21):
        for j in range(3):
            near.append(book(m, rng, (x + .16*j, Y0 + .26*j, -HW+3.5), 1.1, .72, .24, -8+j*6))
    far = towers(m, rng, view) + backdrop(m, rng)
    lights = [((260, Y0 + 260, -260), (0.75, 0.68, 0.58), 900.0)]
    kit.project_add(lay, CAM, m["art"], near=near, far=far, lights=lights, ambient=(0.5, 0.5, 0.52),
                    glow_mats=[m["fog"]], min_facing=0.12, far_edge=6.0, far_min_facing=0.5, zres=(AW, AH))
    lay.add(kit.glass_platform(d, m["glass"], m["slab"], -2.0, 3.0, HW + 7.5, HW + 11.5, PLAT))
    lay.add(kit.glass_stairs(m["glass"], m["slab"], 4, 5, int(HW) + 11, int(HW) + 1, PLAT, Y0))
    kit.art_sky(lay, "gen", CAM, ART, [(-90, (14, 16, 26)), (-10, (40, 42, 50)), (0, (150, 146, 136)),
                                       (20, (196, 190, 176)), (50, (170, 164, 152)), (90, (120, 116, 110))],
                cloud_e=(10.0, 30.0), below=(20, 22, 32), zenith=(120, 116, 110), clean=clean_art())
    lay.emitter(F.Emitter((-80, WATER + 5, -60, 80, Y0 + 40, 40), rate=8.0, sprites=("ruina:block/form/paper_1",),
                          wind=(0.05, -0.35, 0.0), size=0.12, life=12.0, spin=0.4, color=(0.9, 0.88, 0.84), glow=False))
    collision(d, rng)
    room = general_room.build(b, d)
    Fr.stage(b, d, "eapple", "총류의 층", ARRIVE, room,
             room_box=f"x={general_room.OX - 200},y=-64,z=-1024,dx=400,dy=1024,dz=2048")
    b.extra_checks += [
        {"what": "롤랑 방 바이옴", "cmd": f"execute in {d.dim} if biome {general_room.OX} {general_room.Y0} 0 "
                                     f"ruina:general_room", "expect": True},
    ]


def collision(d, rng):
    d.fill(-BX, Y0 - 1, -int(HW), BX, Y0 - 1, int(HW), "minecraft:barrier")
    d.fill(-BX, Y0, -int(HW) - 1, BX, Y0, -int(HW) - 1, "minecraft:barrier")
    d.fill(-BX, Y0, int(HW) + 1, BX, Y0, int(HW) + 1, "minecraft:barrier")
    d.fill(-BX - 1, Y0, -int(HW), -BX - 1, Y0, int(HW), "minecraft:barrier")
    d.fill(BX + 1, Y0, -int(HW), BX + 1, Y0, int(HW), "minecraft:barrier")
    kit.stair_collision(d, 4, 5, int(HW) + 11, int(HW) + 1, PLAT, Y0)
    d.fill(4, Y0, int(HW) + 1, 5, Y0, int(HW) + 1, "minecraft:air")


PREVIEW_CAMS = [("다리 위에서 책탑", F.Camera((0.5, Y0 + 1.62, 0.0), 180.0, -25.0)),
                ("다리 옆", F.Camera((60.0, Y0 + 1.62, 6.0), 120.0, -5.0))]


def preview(b):
    build(b)
