"""종교의 층 (호크마) — 자유 형체 판 (2026-10-15).

reference/종교의 층 전경.png (흑백): 기와처럼 줄지은 돌판 무대를 옆 조금 위(유리 전망 발판, 도착)에서 봄 — 아래 열주,
뒤로 겹쳐 선 거대한 흰 시계 판들(바늘이 돎 — 시침·분침 움직임), 가운데 뾰족 장식 달린 높은 막대(진자, 흔들림),
양옆 난간 달린 발코니 복도, 쇠 틀, 잿빛 안개. 나무위키: 신성·웅장, 움직이는 시계 장치, 종소리(소리는 나중).
지정사서 방: builders/religion_room.py.
"""
from __future__ import annotations

import math

import numpy as np

from tools import artfit as A
from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 150
BX, HW = 220, 14.5
PLAT = Y0 + 3
CAM = F.Camera((0.5, PLAT + 1.62, HW + 8.6), 180.0, 6.0)
ARRIVE = (0.5, PLAT, HW + 8.6, 180.0, 6.0)
ART = "reference/종교의 층 전경.png"
SPACE = "religion"
UP = np.array([0, 1.0, 0])
CLOCKS = [  # 원화 시계 (가운데 x, y, 반지름 px) → 깊이 z
    (492, 300, 235, -200), (110, 80, 105, -240), (800, 45, 120, -260), (165, 228, 82, -170), (885, 225, 80, -180),
    (40, 250, 45, -150),
]


def clean_art():
    return A.clean_sky(ART, A.circle_mask((1000, 555), [(x, y, r) for x, y, r, _ in CLOCKS], grow=1.04), grow=2)


def mats():
    m = {}
    # 시계 지우기는 하늘 전용. 같은 마스크가 무대 중앙까지 덮으므로
    # 지운 그림을 바닥에 투영하면 거대한 검은 얼룩이 생긴다.
    m["art"] = F.mat("rel_art", T.art("art/religion", ART), emissive=True, flat=True, ao=False)
    m["slate"] = F.mat("rel_slate", T.herringbone("rel_slate", (70, 70, 74), (150, 150, 156), brick=(16, 8), seed=231),
                       emissive=True, flat=True, ao=False)
    m["stone"] = F.mat("rel_stone", T.stone_slab("rel_stone", (110, 110, 114), (190, 190, 194), seed=232), emissive=True,
                       flat=True, ao=False)
    m["iron"] = F.mat("rel_iron", T.metal("rel_iron", (24, 24, 26), (80, 80, 84), seed=233), emissive=True, flat=True,
                      ao=False)
    m["face"] = F.mat("rel_face", T.clock_face("rel_face"), layer="cutout", emissive=True, flat=True, ao=False)
    m["hand"] = F.mat("rel_hand", T.flat("rel_hand", (20, 20, 22)), emissive=True, flat=True, ao=False)
    m["pillar"] = F.mat("rel_pillar", T.stone_slab("rel_pillar", (170, 170, 174), (226, 226, 230), seed=234),
                        emissive=True, flat=True, ao=False)
    m["glass"] = F.mat("rel_glass", T.glow("rel_glass", (230, 230, 235)), layer="translucent", emissive=True,
                       flat=True, ao=False)
    m["fog"] = F.mat("rel_fog", T.glow("rel_fog", (220, 220, 224)), layer="translucent", emissive=True, flat=True,
                     ao=False)
    return m


def stage(m, rng):
    out = [F.plane((-BX, Y0, HW), (2 * BX, 0, 0), (0, 0, -2 * HW), m["slate"], tile=(2, 2))]
    out.append(F.box((-BX, Y0 - 2.6, HW), (BX, Y0 + 0.1, HW + 1.2), m["stone"], tile=2.0))       # 앞 처마
    out.append(F.box((-BX, Y0, -HW - 0.5), (BX, Y0 + 0.5, -HW), m["stone"], tile=2.0))           # 뒤 턱
    out.append(F.plane((-BX, Y0 - 3, -HW), (2 * BX, 0, 0), (0, 0, 2 * HW), m["stone"], tile=(4, 4)))
    for x in range(-BX + 10, BX, 30):                                                          # 열주
        for z in (HW - 2, -HW + 2):
            out.append(F.revolve([(1.3, 0), (1.3, Y0 - 6), (2.2, Y0 - 5), (2.2, Y0 - 3.5)], m["pillar"], segs=16,
                                 center=(x, 0, z), tiles_around=4, tile_up=8.0))
    return out


def clock_mesh(m, c, R, normal=(0, 0, 1)):
    """시계 판 (원판 + 테 + 뒤 쇠 틀 방사 살)."""
    c = np.asarray(c, float)
    a = np.linspace(0, 2 * math.pi, 49)
    G = np.stack([np.stack([c + [0, 0, 0.1]] * 49), np.stack([c + [R * math.cos(t), R * math.sin(t), 0.1] for t in a])], 1)
    UV = np.stack([np.stack([[0.5, 0.5]] * 49), np.stack([[0.5 + 0.499 * math.cos(t), 0.5 - 0.499 * math.sin(t)] for t in a])],
                  1)
    out = [F.grid(G, UV, m["face"], N=np.broadcast_to([0, 0, 1.0], G.shape))]
    rim = np.stack([c + [R * math.cos(t), R * math.sin(t), 0] for t in a])
    out.append(F.sweep(rim, max(0.6, R * 0.03), m["iron"], sides=6, step=max(1.0, R / 10)))
    for k in range(8):
        t = k * math.pi / 4
        out.append(F.sweep(np.array([c - [0, 0, 1.5], c + [R * math.cos(t), R * math.sin(t), -1.5]]), max(0.5, R * 0.02),
                           m["iron"], sides=4, step=max(2.0, R / 4)))
    return F.concat(out)


def hand_mesh(m, c, R, length, width):
    """바늘 (축 기준 +y 방향으로 뻗은 납작한 마름모 + 짧은 꼬리)."""
    c = np.asarray(c, float)
    p = np.array([[0, -0.12 * R, 0.4], [width / 2, 0.15 * R, 0.4], [0, length * R, 0.4], [-width / 2, 0.15 * R, 0.4]])
    q = F.Quads((p + c)[None], np.array([[[0.5, 0], [1, 0.3], [0.5, 1], [0, 0.3]]]) * 0.99, M=m["hand"])
    hub = F.ellipsoid(c + [0, 0, 0.4], (R * 0.05, R * 0.05, 0.3), m["hand"], 10, 4)
    return F.concat([F.two_sided(q), hub])


def clocks(lay, m, view):
    """시계 판 (정적) + 시침·분침 (움직임: 분침 1분 한 바퀴처럼 빠르게 — 거대 시계가 살아 있게)."""
    out = []
    for i, (px, py, pr, z) in enumerate(CLOCKS):
        c = view.at_z(np.array([float(px)]), np.array([float(py)]), z)[0]
        R = pr * view.px_size(c)
        out.append(clock_mesh(m, c, R))
        for k, (length, width, period) in enumerate(((0.55, R * 0.09, 720.0), (0.85, R * 0.05, 60.0 + 7 * i))):
            mesh = hand_mesh(m, c + [0, 0, 0.3 * (k + 1)], R, length, width).rotate("z", -30 * (i + k * 5), origin=c)
            pos = tuple(int(v) for v in c + [0, 0, 1 + k])
            lay.mover(F.Mover(pos, mesh, tuple(c), "spin", (0, 0, -1), period=period, radius=R * 1.1))
    return out


def pendulum(lay, m, view):
    """가운데 높은 막대 + 위 마름모 장식 (진자: 아래 받침 축에서 천천히 흔들림)."""
    z = -60.0
    base = view.at_z(np.array([485.0]), np.array([250.0]), z)[0]
    top = Y0 + 330
    rod = F.box((base[0] - 0.8, Y0 + 30, z - 0.8), (base[0] + 0.8, top, z + 0.8), m["iron"], tile=4.0)
    dia_c = np.array([base[0], Y0 + 70, z])
    dia = F.concat([F.two_sided(F.Quads(np.array([[dia_c + [0, 10, 0.9], dia_c + [5, 0, 0.9], dia_c + [0, -10, 0.9],
                                                   dia_c + [-5, 0, 0.9]]]), np.array([[[0.5, 0], [1, 0.5], [0.5, 1], [0, 0.5]]]) * 0.99,
                                         M=m["iron"]))])
    lay.mover(F.Mover((int(base[0]), Y0 + 40, int(z)), F.concat([rod, dia]), (base[0], top, z), "swing", (0, 0, 1),
                      period=8.0, amp=1.5))
    frame = F.box((base[0] - 7, Y0, z - 4), (base[0] + 7, Y0 + 30, z + 4), m["iron"], tile=4.0, faces="xXzZY")
    return [frame]


def balconies(m, rng, n=14):
    out = []
    for _ in range(n):
        x0, z = rng.uniform(-300, 300), rng.uniform(-300, -60)
        y = rng.uniform(Y0 - 20, Y0 + 160)
        L = rng.uniform(30, 90)
        out.append(F.box((x0, y - 0.6, z - 3), (x0 + L, y, z + 3), m["stone"], tile=4.0))
        out.append(F.sweep(np.array([[x0, y + 1.1, z + 3], [x0 + L, y + 1.1, z + 3]]), 0.1, m["iron"], sides=4, step=8.0))
        for x in np.arange(x0, x0 + L + 0.1, 6.0):
            out.append(F.box((x - 0.3, y - 12, z - 0.3), (x + 0.3, y, z + 0.3), m["iron"], tile=4.0))
            out.append(F.box((x - 0.06, y, z + 2.9), (x + 0.06, y + 1.1, z + 3.0), m["iron"]))
    for _ in range(40):                                          # 쇠 틀
        x, y, z = rng.uniform(-350, 350), rng.uniform(Y0, Y0 + 300), rng.uniform(-420, -140)
        if rng.random() < 0.5:
            out.append(F.box((x, y, z), (x + rng.uniform(30, 120), y + 1.2, z + 1.2), m["iron"], tile=4.0))
        else:
            out.append(F.box((x, y, z), (x + 1.2, y + rng.uniform(30, 160), z + 1.2), m["iron"], tile=4.0))
    for y in (Y0 - 40, Y0 - 10):                                 # 안개
        out.append(F.plane((-500, y, -500), (1000, 0, 0), (0, 0, 1000), m["fog"], tile=(32, 32)).tint((1, 1, 1), 0.2))
    return out


def build(b):
    from . import fragment as Fr
    from . import religion_room
    d = b.dim("religion")
    lay = b.form("religion")
    rng = np.random.default_rng(2201)
    m = mats()
    view = A.ArtView(CAM, 1000, 555)
    near = stage(m, rng)
    far = balconies(m, rng) + pendulum(lay, m, view)
    lights = [((0, Y0 + 300, -300), (0.7, 0.7, 0.72), 800.0)]
    kit.project_add(lay, CAM, m["art"], near=near, far=far, lights=lights, ambient=(0.62, 0.62, 0.64),
                    glow_mats=[m["fog"]], min_facing=0.12, far_edge=6.0, far_min_facing=0.5, zres=(1000, 555))
    for q in clocks(lay, m, view):
        lay.add(F.bake_points(q, lights, ambient=(0.85, 0.85, 0.87)), max_edge=6.0)
    lay.add(kit.glass_platform(d, m["glass"], m["iron"], -2.0, 3.0, HW + 6.5, HW + 10.5, PLAT))
    lay.add(kit.glass_stairs(m["glass"], m["iron"], 4, 5, int(HW) + 10, int(HW) + 1, PLAT, Y0))
    kit.art_sky(lay, "rel", CAM, ART, [(-90, (20, 20, 22)), (-10, (120, 120, 124)), (0, (190, 190, 194)),
                                       (30, (210, 210, 214)), (60, (160, 160, 164)), (90, (90, 90, 94))],
                cloud_e=(5.0, 25.0), below=(60, 60, 62), zenith=(90, 90, 94), clean=clean_art())
    lay.emitter(F.Emitter((-60, Y0 + 1, -30, 60, Y0 + 40, 30), rate=3.0, sprites=("ruina:block/form/paper_1",),
                          wind=(0.1, -0.1, 0.0), size=0.1, life=10.0, spin=0.3, color=(0.9, 0.9, 0.92), glow=True))
    collision(d)
    room = religion_room.build(b, d)
    Fr.stage(b, d, "apple", "종교의 층", ARRIVE, room,
             room_box=f"x={religion_room.OX - 200},y=-64,z=-1024,dx=400,dy=1024,dz=2048")
    b.extra_checks += [
        {"what": "호크마 방 바이옴", "cmd": f"execute in {d.dim} if biome {religion_room.OX} {religion_room.Y0} 0 "
                                       f"ruina:religion_room", "expect": True},
    ]


def collision(d):
    d.fill(-BX, Y0 - 1, -int(HW), BX, Y0 - 1, int(HW), "minecraft:barrier")
    d.fill(-BX, Y0, -int(HW) - 1, BX, Y0, -int(HW) - 1, "minecraft:barrier")
    d.fill(-BX, Y0, int(HW) + 1, BX, Y0, int(HW) + 1, "minecraft:barrier")
    kit.stair_collision(d, 4, 5, int(HW) + 10, int(HW) + 1, PLAT, Y0)
    d.fill(4, Y0, int(HW) + 1, 5, Y0, int(HW) + 1, "minecraft:air")


PREVIEW_CAMS = [("무대 위에서 시계", F.Camera((0.5, Y0 + 1.62, 0.0), 180.0, -20.0)),
                ("무대 옆", F.Camera((60.0, Y0 + 1.62, 6.0), 120.0, -5.0))]


def preview(b):
    build(b)
