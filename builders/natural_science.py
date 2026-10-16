"""자연과학의 층 (티페리트) — 자유 형체 판 (2026-10-15).

reference/자연과학의 층 전경.png: 무대(모자이크 띠 + 붉은 카펫)를 옆 조금 위(유리 전망 발판, 도착)에서 봄 — 뒤로
갈비뼈 같은 살이 꼭대기 빛 구멍으로 모이는 반원 황금 돔, 벽 가득 촛불 든 아치 감실, 겹겹이 작아지는 아치 끝 빛나는
뾰족 아치 문, 가운데 받침대 위 금잔·파란 수정·작은 불꽃, 위에서 쏟아지는 빛줄기, 무대 앞면 금테 유리판, 아래
왼쪽 파란 / 오른쪽 주황 휘장 (살랑 흔들림). 색 바뀐 판(청록 돔)·티페리트 F 전환은 지금 만들지 않음 (사용자 2026-10-12).
지정사서 방: builders/natural_science_room.py.
"""
from __future__ import annotations

import math

import numpy as np

from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 100
DOME_R, DOME_H = 90, 130
DZ = -6
SX, SZ0, SZ1 = 150, 2.0, 16.0
PLAT = Y0 + 2
CAM = F.Camera((0.5, PLAT + 1.62, SZ1 + 7.4), 180.0, 6.0)
ARRIVE = (0.5, PLAT, SZ1 + 7.4, 180.0, 6.0)
ART = "reference/자연과학의 층 전경.png"
SPACE = "natural_science"
UP = np.array([0, 1.0, 0])


def mats():
    m = {}
    m["art"] = F.mat("ns_art", T.art("art/natural_science", ART), emissive=True, flat=True, ao=False)
    m["wall"] = F.mat("ns_wall", T.stone_slab("ns_wall", (150, 106, 40), (230, 180, 90), seed=151), emissive=True,
                      flat=True, ao=False)
    m["gold"] = F.mat("ns_gold", T.metal("ns_gold", (150, 100, 30), (255, 220, 120), seed=152), emissive=True,
                      flat=True, ao=False)
    m["candle"] = F.mat("ns_candle", T.glow("ns_candle", (255, 226, 160)), emissive=True, flat=True, ao=False, glow=3)
    m["mosaic"] = F.mat("ns_mosaic", T.herringbone("ns_mosaic", (120, 90, 50), (230, 196, 130), brick=(8, 8), seed=153),
                        emissive=True, flat=True, ao=False)
    m["carpet"] = F.mat("ns_carpet", T.flat("ns_carpet", (180, 40, 30)), emissive=True, flat=True, ao=False)
    m["glass"] = F.mat("ns_glass", T.glow("ns_glass", (255, 236, 170)), layer="translucent", emissive=True, flat=True,
                       ao=False)
    m["blue"] = F.mat("ns_blue", T.wood("ns_blue", (40, 60, 100), (120, 150, 200), seed=154), emissive=True, flat=True,
                      ao=False)
    m["orange"] = F.mat("ns_orange", T.wood("ns_orange", (160, 50, 20), (250, 150, 60), seed=155), emissive=True,
                        flat=True, ao=False)
    m["ray"] = F.mat("ns_ray", T.glow("ns_ray", (255, 240, 200)), layer="translucent", emissive=True, flat=True,
                     ao=False)
    m["crystal"] = F.mat("ns_crystal", T.glow("ns_crystal", (140, 200, 255)), emissive=True, flat=True, ao=False,
                         glow=4)
    m["door"] = F.mat("ns_door", T.glow("ns_door", (255, 246, 220)), emissive=True, flat=True, ao=False, glow=3)
    return m


def dome(m, rng):
    """북쪽 반원 돔 (안쪽이 앞), 갈비살 24줄, 아치 감실(촛불) 격자, 꼭대기 빛 구멍."""
    out = []
    ys = np.linspace(0, DOME_H, 30)
    prof = [(DOME_R * math.sqrt(max(0.0, 1 - (y / DOME_H) ** 2)) + 0.01, Y0 + y) for y in ys if y < DOME_H * 0.97]
    q = F.revolve(prof, m["wall"], segs=64, center=(0, 0, DZ), tiles_around=48, tile_up=6.0, arc=(180, 360)).flipped()
    out.append(q)
    for k in range(25):                                         # 갈비살
        a = math.pi + k * math.pi / 24
        pts = np.array([[math.cos(a) * r, y, DZ + math.sin(a) * r] for r, y in prof])
        out.append(F.sweep(pts * [0.985, 1, 1] + [0, 0, DZ * 0.015], 0.9, m["gold"], sides=6, step=3.0, tile_along=4))
    for k in range(40):                                         # 감실: 각도 40칸 × 높이 7줄 (아래 70%)
        a = math.pi + (k + 0.5) * math.pi / 40
        for j in range(7):
            y = 8 + j * 12
            if y > DOME_H * 0.7:
                continue
            r = DOME_R * math.sqrt(max(0.0, 1 - (y / DOME_H) ** 2)) - 0.3
            n = np.array([-math.cos(a), 0, -math.sin(a)])
            t = np.array([-math.sin(a), 0, math.cos(a)])
            c = np.array([math.cos(a) * r, Y0 + y, DZ + math.sin(a) * r])
            out.append(F.plane(c - t * 1.1 - UP * 1.6 + n * 0.05, t * 2.2, UP * 3.2, m["gold"]).flipped())
            out.append(F.plane(c - t * 0.7 - UP * 1.2 + n * 0.1, t * 1.4, UP * 2.4, m["candle"]).flipped())
    out.append(F.revolve([(DOME_R * 0.22, Y0 + DOME_H * 0.97), (DOME_R * 0.12, Y0 + DOME_H + 2)], m["door"], segs=24,
                         center=(0, 0, DZ), tiles_around=6, tile_up=4.0, arc=(180, 360)).flipped())
    out.append(F.plane((-DOME_R, Y0, DZ), (2 * DOME_R, 0, 0), (0, 0, -DOME_R), m["mosaic"], tile=(4, 4)).flipped())
    return out


def arches(m):
    """겹겹이 작아지는 아치 → 빛나는 뾰족 아치 문."""
    out = []
    for k, z in enumerate(range(DZ - 30, DZ - DOME_R + 4, -10)):
        w, h = 46 - k * 5, 90 - k * 9
        t = np.linspace(-1, 1, 30)
        pts = np.stack([w * t, Y0 + h * np.sqrt(np.maximum(0, 1 - t ** 2)) ** 0.8, np.full_like(t, z)], 1)
        out.append(F.sweep(pts, 1.4, m["gold"], sides=6, step=3.0))
    zd = DZ - DOME_R + 2
    xs = np.linspace(-7, 7, 15)
    G = np.stack([np.stack([xs, np.full_like(xs, Y0), np.full_like(xs, zd)], 1),
                  np.stack([xs, Y0 + 26 - 10 * (np.abs(xs) / 7) ** 1.6, np.full_like(xs, zd)], 1)], 1)
    UV = np.stack([np.stack([(xs + 7) / 14 * 0.99, np.zeros(15)], 1), np.stack([(xs + 7) / 14 * 0.99, np.full(15, 0.99)], 1)], 1)
    out.append(F.grid(G, UV, m["door"], N=np.broadcast_to([0, 0, 1.0], G.shape)))
    return out


def pedestal(m):
    x, z = 0.5, DZ - 16
    out = [F.revolve([(1.6, Y0), (1.4, Y0 + 0.6), (0.5, Y0 + 1.0), (0.45, Y0 + 3.4), (1.2, Y0 + 3.8), (2.4, Y0 + 4.4),
                      (2.5, Y0 + 4.7), (0.01, Y0 + 4.7)], m["gold"], segs=24, center=(x, 0, z), tiles_around=6,
                     tile_up=2.0)]
    out.append(F.revolve([(0.3, Y0 + 4.7), (0.12, Y0 + 5.2), (0.5, Y0 + 5.9), (0.55, Y0 + 6.2)], m["gold"], segs=16,
                         center=(x - 1.2, 0, z), tiles_around=4, tile_up=1.0))
    out.append(F.box((x - 0.2, Y0 + 4.7, z - 0.35), (x + 0.6, Y0 + 5.6, z + 0.35), m["crystal"]))
    out.append(F.ellipsoid((x + 1.2, Y0 + 5.2, z), (0.2, 0.45, 0.2), m["candle"], 8, 4))
    return out


def stage(m):
    """무대: 모자이크 띠 / 붉은 카펫 / 모자이크 띠, 앞 금 난간, 앞면 금테 유리판."""
    out = [F.plane((-SX, Y0, SZ1), (2 * SX, 0, 0), (0, 0, SZ0 - 8 - SZ1), m["mosaic"], tile=(2, 2))]
    out.append(F.plane((-SX, Y0 + 0.02, SZ1 - 4), (2 * SX, 0, 0), (0, 0, -(SZ1 - SZ0 - 8)), m["carpet"], tile=(4, 4)))
    zf = SZ1
    out.append(F.sweep(np.array([[-SX, Y0 + 0.3, zf], [SX, Y0 + 0.3, zf]]), 0.3, m["gold"], sides=6, step=8.0, tile_along=8))
    out.append(F.two_sided(F.box((-SX, Y0 - 19, zf + 0.18), (SX, Y0 - 0.5, zf + 0.24), m["glass"])).tint((1, 1, 1), 0.45))
    for x0 in np.arange(-SX, SX, 20.0):                        # 금테: 세로 + 위로 휘는 테 두 줄
        out.append(F.box((x0 - 0.3, Y0 - 19, zf), (x0 + 0.3, Y0, zf + 0.5), m["gold"]))
        for base in (Y0 - 19, Y0 - 12):
            t = np.linspace(0, 1, 12)
            arc = np.stack([x0 + 20 * t, base + 6 * (1 - (2 * t - 1) ** 2), np.full_like(t, zf + 0.4)], 1)
            out.append(F.sweep(arc, 0.25, m["gold"], sides=4, step=2.0))
    return out


def curtains(lay, m, rng):
    """무대 아래 휘장 (왼쪽 파랑, 오른쪽 주황): 세로 주름 띠, 가까운 쪽은 살랑 흔들림."""
    out = []
    zf = SZ1 + 1.2
    for x0 in np.arange(-SX, SX, 4.0):
        mat = m["blue"] if x0 < 0 else m["orange"]
        bottom = 30 + 4 * math.sin(x0 / 6)
        t = np.linspace(0, 1, 9)
        path = np.stack([np.full_like(t, x0 + 2), Y0 - 20 - (Y0 - 20 - bottom) * t, np.full_like(t, zf)], 1)
        rib = F.ribbon(path, 4.2, mat, up=[0, 0, 1], step=4.0, tile_along=8.0)
        rib = rib.color_by(lambda P, N: 0.75 + 0.25 * np.cos((P[:, 0:1] - x0) * 1.6))
        if abs(x0) < 40:
            piv = (x0 + 2, Y0 - 20, zf)
            lay.mover(F.Mover((int(x0 + 2), int(Y0 - 25), int(zf)), rib, piv, "swing", (1, 0, 0), period=7.0 + rng.random(),
                              amp=1.2, phase=rng.random()))
        else:
            out.append(rib)
    return out


def rays(m):
    """빛 구멍에서 쏟아지는 빛줄기 (반투명 판)."""
    out = []
    rng = np.random.default_rng(5)
    for k in range(9):
        a = rng.uniform(-0.9, 0.9)
        top = np.array([0.5 + 8 * a, Y0 + DOME_H - 4, DZ - 25])
        bot = np.array([0.5 + 55 * a, Y0, DZ - 10 + rng.uniform(-10, 10)])
        w = rng.uniform(5, 10)
        side = np.array([1.0, 0, 0]) * w
        out.append(F.two_sided(F.Quads(np.array([[top - side * 0.3, top + side * 0.3, bot + side, bot - side]]),
                                       np.array([[[0, 0], [0.99, 0], [0.99, 0.99], [0, 0.99]]]), M=m["ray"]))
                   .tint((1, 1, 1), 0.12))
    return out


def build(b):
    from . import fragment as Fr
    from . import natural_science_room
    d = b.dim("natural_science")
    lay = b.form("natural_science")
    rng = np.random.default_rng(1501)
    m = mats()
    near = stage(m) + pedestal(m)
    near.extend(F.box((x-.22, Y0-.65, SZ1-.9), (x+.22, Y0+.32, SZ1-.55), m['gold']) for x in np.arange(-SX+12, SX, 24))
    near.append(F.box((-SX, Y0-.6, SZ1-.6), (SX, Y0+.25, SZ1), m['gold']))
    far = dome(m, rng) + arches(m) + curtains(lay, m, rng)
    lights = [((0.5, Y0 + DOME_H, DZ - 20), (1.0, 0.85, 0.5), 260.0)]
    kit.project_add(lay, CAM, m["art"], near=near, far=far, lights=lights, ambient=(0.7, 0.58, 0.4),
                    glow_mats=[m["candle"], m["door"], m["crystal"], m["glass"]], min_facing=0.12, far_edge=4.0,
                    far_min_facing=0.35)
    for q in rays(m):
        lay.add(q, max_edge=6.0)
    lay.add(kit.glass_platform(d, m["glass"], m["gold"], -2.0, 3.0, SZ1 + 5.0, SZ1 + 9.0, PLAT))
    lay.add(kit.glass_stairs(m["glass"], m["gold"], 4, 5, int(SZ1) + 8, int(SZ1) + 1, PLAT, Y0))
    kit.art_sky(lay, "ns", CAM, ART, [(-90, (90, 50, 20)), (0, (240, 200, 120)), (40, (250, 220, 150)),
                                      (90, (255, 240, 200))], cloud_e=(70.0, 80.0), below=(90, 60, 30),
                zenith=(255, 240, 200))
    lay.emitter(F.Emitter((-40, Y0 + 2, DZ - 60, 40, Y0 + 60, SZ1), rate=4.0, sprites=("ruina:block/form/paper_gold",),
                          wind=(0.0, -0.1, 0.0), size=0.1, life=10.0, spin=0.1, color=(1.0, 0.9, 0.6), glow=True))
    collision(d)
    room = natural_science_room.build(b, d)
    Fr.stage(b, d, "gplate", "자연과학의 층", ARRIVE, room,
             room_box=f"x={natural_science_room.OX - 200},y=-64,z=-1024,dx=400,dy=1024,dz=2048")
    b.extra_checks += [
        {"what": "티페리트 방 바이옴", "cmd": f"execute in {d.dim} if biome {natural_science_room.OX} "
                                       f"{natural_science_room.Y0} 0 ruina:natural_science_room", "expect": True},
    ]


def collision(d):
    d.fill(-SX, Y0 - 1, int(SZ0) - 8, SX, Y0 - 1, int(SZ1) - 1, "minecraft:barrier")
    d.fill(-SX, Y0, int(SZ1), SX, Y0, int(SZ1), "minecraft:barrier")                   # 앞 난간
    # 반원형 돔 바닥: 방사형 점 수만 개 대신 X별 연속 구간 fill.
    # 원형 외곽벽도 같은 X 단면의 경계에 맞춰 배치해 시각/충돌 정합 유지.
    radius = int(math.ceil(DOME_R))
    for x in range(-radius, radius + 1):
        dx = min(abs(x), DOME_R)
        depth = math.sqrt(max(0.0, DOME_R * DOME_R - dx * dx))
        z_edge = int(math.floor(DZ - depth))
        z_back = int(math.floor(DZ))
        d.fill(x, Y0 - 1, z_edge, x, Y0 - 1, z_back, "minecraft:barrier")
        d.fill(x, Y0, z_edge, x, Y0 + 20, z_edge, "minecraft:barrier")
    kit.stair_collision(d, 4, 5, int(SZ1) + 8, int(SZ1) + 1, PLAT, Y0)
    d.fill(4, Y0, int(SZ1), 5, Y0, int(SZ1), "minecraft:air")


PREVIEW_CAMS = [("무대 위에서 돔", F.Camera((0.5, Y0 + 1.62, 6.0), 180.0, -20.0)),
                ("돔 안에서 무대", F.Camera((20.0, Y0 + 1.62, -50.0), 20.0, -5.0))]


def preview(b):
    build(b)
