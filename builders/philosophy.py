"""철학의 층 (비나) — 자유 형체 판 (2026-10-15).

reference/철학의 층 전경.png: 도시 상공의 넓은 돌 포장 다리(작은 금빛 등이 박힘, 뒤 가장자리 살짝 휨)를 옆 조금 위
(유리 전망 발판, 도착)에서 봄 — 밤하늘을 가로지르는 금빛 은하수 띠와 초승달(그린 하늘: 원화 + 둘레로 이어 그린 띠),
다리 아래 그늘과 안개 너머 아득한 도시 야경, 날리는 금빛 먼지. 지정사서 방: builders/philosophy_room.py.
"""
from __future__ import annotations

import math

import numpy as np

from tools import artfit as A
from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 300
BX, HW = 200, 20.5
PLAT = Y0 + 2
CAM = F.Camera((0.5, PLAT + 1.62, HW + 9.7), 180.0, 6.0)
ARRIVE = (0.5, PLAT, HW + 9.7, 180.0, 6.0)
ART = "reference/철학의 층 전경.png"
SPACE = "philosophy"


def mats():
    m = {}
    m["art"] = F.mat("phil_art", T.art("art/philosophy", ART), emissive=True, flat=True, ao=False)
    m["pave"] = F.mat("phil_pave", T.herringbone("phil_pave", (50, 46, 54), (110, 104, 116), brick=(16, 8), seed=211),
                      emissive=True, flat=True, ao=False)
    m["stone"] = F.mat("phil_stone", T.stone_slab("phil_stone", (24, 22, 28), (60, 56, 64), seed=212), emissive=True,
                       flat=True, ao=False)
    m["lamp"] = F.mat("phil_lamp", T.glow("phil_lamp", (255, 210, 120)), emissive=True, flat=True, ao=False, glow=3)
    m["city"] = [F.mat(f"phil_city{i}", T.neon_facade(f"phil_city{i}", b, ((255, 200, 120), (255, 170, 90), (220, 200, 255)),
                                                       seed=213 + i, ratio=0.4, edge=(80, 60, 50)),
                       emissive=True, flat=True, ao=False)
                 for i, b in enumerate([(14, 12, 18), (20, 16, 22)])]
    m["glass"] = F.mat("phil_glass", T.glow("phil_glass", (255, 230, 190)), layer="translucent", emissive=True,
                       flat=True, ao=False)
    m["fog"] = F.mat("phil_fog", T.glow("phil_fog", (120, 90, 70)), layer="translucent", emissive=True, flat=True,
                     ao=False)
    return m


def bridge(m, rng):
    """넓은 돌 포장 다리 + 박힌 금빛 등 + 뒤 가장자리 살짝 휜 테 + 두꺼운 그늘진 아랫면 + 아치 받침."""
    xs = np.linspace(-BX, BX, 81)
    back = -(HW - xs ** 2 / BX ** 2 * 6)
    G = np.stack([np.stack([xs, np.full_like(xs, Y0), np.full_like(xs, HW)], 1), np.stack([xs, np.full_like(xs, Y0), back], 1)], 1)
    UV = np.stack([np.stack([xs / 4, np.full_like(xs, HW / 4)], 1), np.stack([xs / 4, back / 4], 1)], 1)
    out = [F.fit_tiles(F.grid(G, UV, m["pave"], N=np.broadcast_to([0, 1.0, 0], G.shape)))]
    for _ in range(int(2 * BX * 2 * HW * 0.012)):              # 박힌 금빛 등
        x, z = rng.uniform(-BX, BX), rng.uniform(-HW + 6, HW)
        out.append(F.box((x, Y0 + 0.015, z), (x + 0.4, Y0 + 0.06, z + 0.4), m["lamp"]))
    Gs = np.stack([np.stack([xs, np.full_like(xs, Y0 - 6), back], 1), np.stack([xs, np.full_like(xs, Y0), back], 1)], 1)
    out.append(F.fit_tiles(F.grid(Gs, UV, m["stone"], N=np.broadcast_to([0, 0, -1.0], Gs.shape))))
    out.append(F.box((-BX, Y0 - 6, HW - 0.5), (BX, Y0, HW), m["stone"], tile=4.0, faces="Z"))
    out.append(F.plane((-BX, Y0 - 6, -HW), (2 * BX, 0, 0), (0, 0, 2 * HW), m["stone"], tile=(8, 8)))
    for x in range(-BX + 40, BX, 80):                           # 아치 받침 (아래 도시로)
        for z in (-HW + 4, HW - 4):
            out.append(F.box((x - 3, 0, z - 3), (x + 3, Y0 - 6, z + 3), m["stone"], tile=8.0, faces="xXzZ"))
    return out


def city(m, rng):
    out = []
    for _ in range(220):
        a = rng.uniform(0, 2 * math.pi)
        r = math.sqrt(rng.uniform(40 ** 2, 600 ** 2))
        cx, cz = r * math.cos(a), r * math.sin(a)
        w, l, h = rng.uniform(10, 26), rng.uniform(10, 26), rng.uniform(20, 120)
        out.append(kit.building(cx - w / 2, cz - l / 2, cx + w / 2, cz + l / 2, 0, h, m["city"][int(rng.integers(2))],
                                m["stone"], tile=(8.0, 8.0)))
    out.append(F.plane((-700, 0, 700), (1400, 0, 0), (0, 0, -1400), m["city"][0], tile=(16, 16)).tint((0.5, 0.45, 0.4)))
    for y in (60, 120, 200):                                    # 안개 겹
        out.append(F.plane((-700, y, -700), (1400, 0, 0), (0, 0, 1400), m["fog"], tile=(32, 32)).tint((1, 1, 1), 0.12))
    return out


def build(b):
    from . import fragment as Fr
    from . import philosophy_room
    d = b.dim("philosophy")
    lay = b.form("philosophy")
    rng = np.random.default_rng(2001)
    m = mats()
    near = bridge(m, rng)
    far = city(m, rng)
    lights = [((0, 600, -400), (0.6, 0.45, 0.35), 1200.0)]
    kit.project_add(lay, CAM, m["art"], near=near, far=far, lights=lights, ambient=(0.4, 0.36, 0.4),
                    glow_mats=[m["lamp"], m["fog"], *m["city"]], min_facing=0.1, far_edge=8.0, far_min_facing=0.6,
                    zres=(834, 468))
    lay.add(kit.glass_platform(d, m["glass"], m["stone"], -2.0, 3.0, HW + 7.5, HW + 11.5, PLAT))
    lay.add(kit.glass_stairs(m["glass"], m["stone"], 4, 5, int(HW) + 11, int(HW) + 1, PLAT, Y0))
    # 그린 하늘: 원화 + 둘레로 이어지는 은하수 띠 (고도 25~40°)
    kit.art_sky(lay, "phil", CAM, ART, [(-90, (10, 8, 10)), (-10, (30, 24, 24)), (0, (40, 30, 28)), (12, (24, 18, 22)),
                                        (25, (60, 30, 22)), (32, (110, 60, 40)), (40, (50, 26, 22)), (60, (12, 10, 14)),
                                        (90, (6, 6, 10))],
                cloud_e=(26.0, 38.0), below=(30, 22, 20), zenith=(6, 6, 10))
    lay.emitter(F.Emitter((-80, Y0 + 1, -20, 80, Y0 + 30, 40), rate=6.0, sprites=("ruina:block/form/paper_gold",),
                          wind=(0.2, 0.05, 0.0), size=0.08, life=10.0, spin=0.1, color=(1.0, 0.75, 0.45), glow=True))
    collision(d)
    room = philosophy_room.build(b, d)
    Fr.stage(b, d, "anvil", "철학의 층", ARRIVE, room,
             room_box=f"x={philosophy_room.OX - 200},y=-64,z=-1024,dx=400,dy=1024,dz=2048")
    b.extra_checks += [
        {"what": "비나 방 바이옴", "cmd": f"execute in {d.dim} if biome {philosophy_room.OX} {philosophy_room.Y0} 0 "
                                     f"ruina:philosophy_room", "expect": True},
    ]


def collision(d):
    for x in range(-BX, BX + 1):
        zb = -int(HW - x * x / BX ** 2 * 6)
        d.fill(x, Y0 - 1, zb, x, Y0 - 1, int(HW), "minecraft:barrier")
        d.fill(x, Y0, zb - 1, x, Y0 + 1, zb - 1, "minecraft:barrier")
    d.fill(-BX, Y0, int(HW) + 1, BX, Y0, int(HW) + 1, "minecraft:barrier")
    kit.stair_collision(d, 4, 5, int(HW) + 11, int(HW) + 1, PLAT, Y0)
    d.fill(4, Y0, int(HW) + 1, 5, Y0, int(HW) + 1, "minecraft:air")


PREVIEW_CAMS = [("다리 위", F.Camera((0.5, Y0 + 1.62, 0.0), 90.0, -10.0)),
                ("다리 가장자리에서 아래 도시", F.Camera((0.5, Y0 + 1.62, 19.0), 0.0, 40.0))]


def preview(b):
    build(b)
