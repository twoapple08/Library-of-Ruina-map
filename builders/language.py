"""언어의 층 (게부라) — 자유 형체 판 (2026-10-15).

reference/언어의 층 전경.png: 강철판 발판(판 이음새, 앞 검은 들보와 아래 주황 빛줄, 뒤 녹슨 난간)을 옆 조금 위(유리 전망
발판, 도착)에서 봄 — 뒤 거대한 쇳물 국자(빛나는 쇳물 덩이가 쏟아짐), 붉게 달아오른 판이 군데군데 박힌 검은 기계 구조물 숲,
양옆 리벳 격자 기둥, 발판 아래 쇳물 바다와 잠긴 기계. 쇳물 줄기는 흐르는 무늬(움직임 bob)로.
지정사서 방: builders/language_room.py.
"""
from __future__ import annotations

import math

import numpy as np

from tools import artfit as A
from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 120
BX, HW = 200, 10.5
LAVA = 40
PLAT = Y0 + 4
CAM = F.Camera((0.5, PLAT + 1.62, HW + 10.2), 180.0, 10.0)
ARRIVE = (0.5, PLAT, HW + 10.2, 180.0, 10.0)
ART = "reference/언어의 층 전경.png"
SPACE = "language"
UP = np.array([0, 1.0, 0])


def mats():
    m = {}
    m["art"] = F.mat("lang_art", T.art("art/language", ART), emissive=True, flat=True, ao=False)
    m["plate"] = F.mat("lang_plate", T.steel_plates("lang_plate"), emissive=True, flat=True, ao=False)
    m["black"] = F.mat("lang_black", T.metal("lang_black", (16, 14, 14), (56, 50, 48), seed=171), emissive=True,
                       flat=True, ao=False)
    m["rust"] = F.mat("lang_rust", T.rust("lang_rust", (60, 30, 20), (130, 70, 40), seed=172), emissive=True, flat=True,
                      ao=False)
    m["hot"] = F.mat("lang_hot", T.glow("lang_hot", (255, 100, 40)), emissive=True, flat=True, ao=False, glow=1)
    m["strip"] = F.mat("lang_strip", T.glow("lang_strip", (255, 150, 60)), emissive=True, flat=True, ao=False, glow=1)
    m["molten"] = F.mat("lang_molten", T.molten("lang_molten"), emissive=True, flat=True, ao=False, glow=1)
    m["machine"] = [F.mat(f"lang_machine{i}", T.neon_facade(f"lang_machine{i}", b, ((255, 90, 40), (255, 140, 60),
                                                                                    (200, 60, 30)), seed=173 + i,
                                                            ratio=0.12, edge=(120, 50, 30)),
                          emissive=True, flat=True, ao=False)
                    for i, b in enumerate([(26, 22, 22), (34, 28, 26), (20, 18, 20)])]
    m["glass"] = F.mat("lang_glass", T.glow("lang_glass", (255, 210, 170)), layer="translucent", emissive=True,
                       flat=True, ao=False)
    return m


def platform(m, rng):
    out = [F.plane((-BX, Y0, HW), (2 * BX, 0, 0), (0, 0, -2 * HW), m["plate"], tile=(4, 4))]
    for s in (-1, 1):
        z0, z1 = sorted((s * HW, s * (HW + 1.0)))
        out.append(F.box((-BX, Y0 - 3, z0), (BX, Y0 + 0.2, z1), m["black"], tile=4.0))
        out.append(F.box((-BX, Y0 - 3.6, z0), (BX, Y0 - 3.0, z1), m["strip"], tile=4.0, faces="yzZ"))
    z = -HW + 0.3                                                 # 뒤 녹슨 난간 (군데군데 끊김)
    for x0 in np.arange(-BX, BX, 9.0):
        if rng.random() < 0.12:
            continue
        for x in np.arange(x0, x0 + 9, 1.5):
            out.append(F.box((x - 0.07, Y0, z - 0.07), (x + 0.07, Y0 + 1.6, z + 0.07), m["rust"]))
        for y in (Y0 + 0.8, Y0 + 1.6):
            out.append(F.sweep(np.array([[x0, y, z], [x0 + 9, y, z]]), 0.08, m["rust"], sides=4, step=9.0))
    for x in np.arange(-BX, BX + 1, 40.0):                        # 받침 기둥
        for s in (-1, 1):
            out.append(F.box((x - 1.5, LAVA - 5, s * HW - 1.5), (x + 1.5, Y0 - 3, s * HW + 1.5), m["black"], tile=4.0))
    return out


def lattice(m, x, z, y0, y1, w=4.0):
    out = []
    for dx in (0, w):
        for dz in (0, w):
            out.append(F.box((x + dx - 0.3, y0, z + dz - 0.3), (x + dx + 0.3, y1, z + dz + 0.3), m["black"], tile=4.0))
    for y in np.arange(y0, y1 - w, w):
        for zz in (z, z + w):
            out.append(F.sweep(np.array([[x, y, zz], [x + w, y + w, zz]]), 0.15, m["rust"], sides=4, step=4.0))
            out.append(F.sweep(np.array([[x + w, y, zz], [x, y + w, zz]]), 0.15, m["rust"], sides=4, step=4.0))
    return F.concat(out)


def ladle(lay, m, view):
    """거대 쇳물 국자: 원화 자리 (픽셀 가운데 467,140 반지름 72 → 깊이 -110)."""
    z = -110.0
    c = view.at_z(np.array([467.0]), np.array([140.0]), z)[0]
    R = 72 * view.px_size(c)
    out = [F.ellipsoid(c, (R, R, R * 0.45), m["molten"], 24, 12)]
    t = np.linspace(-math.pi / 2, math.pi / 2, 20)
    for zz in np.linspace(-R * 0.55, R * 0.55, 2):
        arc = np.stack([c[0] + 6 + (R + 3) * np.cos(t), c[1] + (R + 3) * np.sin(t), np.full_like(t, c[2] + zz)], 1)
        out.append(F.sweep(arc, 2.0, m["black"], sides=6, step=3.0))
    G = np.stack([np.stack([c[0] + 6 + (R + 3) * np.cos(t), c[1] + (R + 3) * np.sin(t), np.full_like(t, c[2] + zz)], 1)
                  for zz in (-R * 0.55, R * 0.55)], 1)
    UV = np.stack(np.meshgrid(np.linspace(0, 4, 20), np.array([0, 1.0]), indexing="ij"), -1)
    out.append(F.fit_tiles(F.grid(G, UV, m["black"])))
    out.append(F.box((c[0] + R + 6, c[1] - 4, c[2] - 3), (c[0] + R + 26, c[1] + 4, c[2] + 3), m["black"], tile=4.0))
    # 쏟아지는 쇳물 줄기 (움직임: 흐르는 무늬처럼 위아래로 살짝)
    top = c[1] - R + 4
    path = np.array([[c[0] - 6, top, c[2]], [c[0] - 4, (top + LAVA) / 2, c[2]], [c[0] - 2, LAVA, c[2]]])
    stream = F.sweep(path, lambda s: 3.0 + 2.0 * s, m["molten"], sides=10, step=4.0, tile_along=6.0)
    lay.mover(F.Mover((int(c[0] - 4), int((top + LAVA) / 2), int(c[2])), stream, (c[0] - 4, (top + LAVA) / 2, c[2]), "bob",
                      (0, 1, 0), period=1.2, amp=0.4))
    return F.concat(out)


def machinery(m, rng):
    """검은 기계 구조물 숲 (붉게 달아오른 판) — 발판 앞쪽·국자 앞은 비움."""
    out = []
    placed = []
    for r0, r1, n, hmin, hmax in ((40, 380, 160, 80, 170), (420, 760, 70, 140, 260)):
        cnt = 0
        for _ in range(n * 5):
            if cnt >= n:
                break
            a = rng.uniform(0, 2 * math.pi)
            r = math.sqrt(rng.uniform(r0 ** 2, r1 ** 2))
            cx, cz = r * math.cos(a), r * math.sin(a)
            if (abs(cz) < HW + 24 and abs(cx) <= BX + 10) or (abs(cx) < 70 and -180 < cz < -30):
                continue
            w, l = rng.uniform(12, 26), rng.uniform(12, 26)
            if any(abs(cx - px) < (w + pw) / 2 + 3 and abs(cz - pz) < (l + pl) / 2 + 3 for px, pz, pw, pl in placed):
                continue
            placed.append((cx, cz, w, l))
            h = rng.uniform(hmin, hmax)
            q = kit.building(cx - w / 2, cz - l / 2, cx + w / 2, cz + l / 2, LAVA - 1, LAVA + h,
                             m["machine"][int(rng.integers(3))], m["black"], tile=(8.0, 8.0))
            out.append(q)
            if r < 300 and cz < 0:
                for _k in range(int(rng.integers(0, 3))):            # 달아오른 큰 판 (남쪽 면)
                    pw, ph = rng.uniform(6, min(14, w - 3)), rng.uniform(8, min(18, h - 25))
                    px = cx + rng.uniform(-w / 2 + 1, max(-w / 2 + 1.01, w / 2 - pw - 1))
                    py = LAVA + rng.uniform(20, max(20.01, h - ph - 2))
                    out.append(F.plane((px, py, cz + l / 2 + 0.2), (pw, 0, 0), (0, ph, 0), m["hot"], tile=(4, 4)))
            cnt += 1
    return out


def build(b):
    from . import fragment as Fr
    from . import language_room
    d = b.dim("language")
    lay = b.form("language")
    rng = np.random.default_rng(1601)
    m = mats()
    view = A.ArtView(CAM, 1000, 575)
    near = platform(m, rng)
    for x in (-21.0, 25.0, -150.0, 150.0):
        near.append(lattice(m, x, -HW - 6, LAVA, Y0 + 80))
    far = machinery(m, rng) + [ladle(lay, m, view)]
    lava = F.plane((-120, LAVA, 40), (240, 0, 0), (0, 0, -200), m["molten"], tile=(8, 8))
    lights = [((0, Y0 + 70, -110), (1.4, 0.7, 0.3), 260.0), ((0, LAVA, 0), (1.0, 0.45, 0.2), 120.0)]
    kit.project_add(lay, CAM, m["art"], near=near + [lava], far=far, lights=lights, ambient=(0.42, 0.3, 0.26),
                    glow_mats=[m["hot"], m["strip"], m["molten"]], min_facing=0.12, far_edge=6.0, far_min_facing=0.5,
                    zres=(1000, 575))
    for x0, z0, x1, z1 in ((-600, -600, 600, -160), (-600, 40, 600, 600), (-600, -160, -120, 40), (120, -160, 600, 40)):
        lay.add(F.plane((x0, LAVA, z1), (x1 - x0, 0, 0), (0, 0, z0 - z1), m["molten"], tile=(16, 16)), max_edge=8.0)
    lay.add(kit.glass_platform(d, m["glass"], m["black"], -2.0, 3.0, HW + 8.0, HW + 12.0, PLAT))
    lay.add(kit.glass_stairs(m["glass"], m["black"], 4, 5, int(HW) + 11, int(HW) + 1, PLAT, Y0))
    kit.art_sky(lay, "lang", CAM, ART, [(-90, (60, 20, 8)), (-10, (140, 50, 20)), (0, (120, 40, 20)), (20, (60, 24, 16)),
                                        (60, (30, 14, 10)), (90, (16, 8, 6))],
                city=dict(near=30, far=22, dark=(26, 20, 20), glow=(180, 60, 30), rim=(255, 120, 60)),
                cloud_e=(30.0, 40.0), below=(120, 40, 10), zenith=(16, 8, 6))
    lay.emitter(F.Emitter((-60, LAVA + 2, -80, 60, Y0 + 40, 30), rate=10.0, sprites=("ruina:block/form/paper_gold",),
                          wind=(0.0, 0.6, 0.0), size=0.1, life=6.0, spin=0.1, color=(1.0, 0.5, 0.2), glow=True))
    collision(d)
    room = language_room.build(b, d)
    Fr.stage(b, d, "iblock", "언어의 층", ARRIVE, room,
             room_box=f"x={language_room.OX - 200},y=-64,z=-1024,dx=400,dy=1024,dz=2048")
    b.extra_checks += [
        {"what": "게부라 방 바이옴", "cmd": f"execute in {d.dim} if biome {language_room.OX} {language_room.Y0} 0 "
                                       f"ruina:language_room", "expect": True},
    ]


def collision(d):
    d.fill(-BX, Y0 - 1, -int(HW), BX, Y0 - 1, int(HW), "minecraft:barrier")
    d.fill(-BX, Y0, -int(HW) - 1, BX, Y0 + 1, -int(HW) - 1, "minecraft:barrier")
    d.fill(-BX, Y0, int(HW) + 1, BX, Y0, int(HW) + 1, "minecraft:barrier")
    kit.stair_collision(d, 4, 5, int(HW) + 11, int(HW) + 1, PLAT, Y0)
    d.fill(4, Y0, int(HW) + 1, 5, Y0, int(HW) + 1, "minecraft:air")


PREVIEW_CAMS = [("발판 위", F.Camera((0.5, Y0 + 1.62, 0.0), 90.0, 0.0)),
                ("발판에서 국자", F.Camera((0.5, Y0 + 1.62, -4.0), 180.0, -10.0))]


def preview(b):
    build(b)
