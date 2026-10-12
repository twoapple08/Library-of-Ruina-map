"""언어의 층 (게부라). 접대 공간(용광로 위 강철 발판) ↔ 지정사서 방 (철블럭 F).

참고: reference/언어의 층 전경.png, reference/언어의 층 지정사서 방.png, PLAN.md 8절 ("사방이 쇳물 가득한 용광로").

원화(전경): 강철판 이음새가 보이는 발판, 뒤 가장자리 녹슨 난간, 거대한 쇳물 국자(빛나는 쇳물 덩이가 쏟아짐),
붉게 달아오른 창·판이 있는 검은 기계 구조물 숲, 양옆 리벳 격자 기둥, 발판 아래 쇳물 바다와 잠긴 기계.
원화(방): 어두운 서재, 큰 창 너머 용광로 빛과 쇳물 국자, 왼쪽 책장, 오른쪽 큰 검은 소파,
재떨이·컵 놓인 낮은 탁자, 바닥에 흩어진 종이.

크기 (1536×400, 사람 기준): 발판 400×21 (서 있는 Y 120), 쇳물 바다 Y 40, 국자 반지름 32 (발판 뒤 110칸),
기계 구조물 숲 400 안쪽 (+먼 겹). 쇳물 바다는 진짜 용암 (빛 15), 불 번짐은 게임룰로 꺼 둠.
"""
from __future__ import annotations

import math

import numpy as np

from tools import shapes as S

from .city import build_city
from .technology import _line

Y0 = 120
BX, HW = 200, 10
LAVA = 40
ARRIVE_X = -150
ROOM_X = 4000
RY = 64
PLATE = ["minecraft:polished_tuff", "minecraft:tuff_bricks", "minecraft:polished_deepslate", "minecraft:polished_tuff"]
HOT = ["minecraft:shroomlight", "minecraft:magma_block", "minecraft:shroomlight", "minecraft:ochre_froglight"]
FURNACE_PAL = {
    "walls": (["minecraft:polished_blackstone", "minecraft:deepslate_bricks", "minecraft:black_concrete",
               "minecraft:polished_deepslate", "minecraft:gray_concrete", "minecraft:waxed_exposed_copper"],
              [16, 14, 12, 12, 6, 6]),
    "lit": (["minecraft:magma_block", "minecraft:shroomlight", "minecraft:ochre_froglight"], [40, 40, 20]),
    "neon": (["minecraft:magma_block", "minecraft:shroomlight"], [1, 1]),
    "trim": (["minecraft:polished_blackstone_bricks", "minecraft:deepslate_tiles"], [1, 1]),
    "corner_neon": 0.25, "corners": 1, "roof_neon": 0.2,
    "lit_ratio": (0.01, 0.06),   # 기계 구조물: 창은 드물게 (원화는 군데군데 달아오른 판)
}


def platform(d, rng):
    """강철판 발판: 판마다 크기 다른 이음새, 앞 가장자리 검은 들보 + 아래 주황 빛줄, 뒤 녹슨 난간."""
    xs, zs = np.arange(-BX, BX + 1), np.arange(-HW, HW + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    plate = np.array([d.id(s) for s in PLATE])
    pw = 6 + (S.hash01(Z // 7, seed=1601) * 6).astype(int)
    ids = plate[(S.hash01(X // pw, Z // 7, seed=1602) * len(plate)).astype(int).clip(0, len(plate) - 1)]
    seam = ((X % pw) == 0) | ((Z % 7) == 0)
    ids = np.where(seam, d.id("minecraft:deepslate_tiles"), ids)
    d.place(-BX, Y0 - 1, -HW, ids[:, None, :])
    d.fill(-BX, Y0 - 3, -HW, BX, Y0 - 2, HW, "minecraft:polished_blackstone")
    for z in (-HW - 1, HW + 1):
        d.fill(-BX, Y0 - 3, z, BX, Y0 - 1, z, "minecraft:polished_blackstone_bricks")
        d.fill(-BX, Y0 - 4, z, BX, Y0 - 4, z, "minecraft:shroomlight")            # 아래 빛줄
    # 뒤 녹슨 난간 (원화): 기둥 + 두 줄, 군데군데 끊김
    z = -HW
    for x in range(-BX, BX + 1):
        if S.hash01(np.array(x // 9), seed=1603) < 0.12:
            continue
        d.set(x, Y0, z, "minecraft:iron_bars")
        d.set(x, Y0 + 1, z, "minecraft:waxed_exposed_cut_copper_slab[type=bottom]" if x % 3 else "minecraft:iron_bars")
        if x % 6 == 0:
            d.fill(x, Y0, z, x, Y0 + 1, z, "minecraft:waxed_exposed_copper")
    # 받침 기둥 (쇳물 속으로)
    for x in range(-BX, BX + 1, 40):
        for zz in (-HW, HW):
            d.fill(x - 1, LAVA - 5, zz, x + 1, Y0 - 4, zz, "minecraft:polished_blackstone")


def lattice_column(d, x, z, y0, y1, w=4):
    """리벳 격자 기둥 (원화 양옆): 네 모서리 기둥 + 사선 띠."""
    for dx in (0, w):
        for dz in (0, w):
            d.fill(x + dx, y0, z + dz, x + dx, y1, z + dz, "minecraft:polished_deepslate")
    for y in range(y0, y1 - w, w):
        for (a, b2) in (((x, z), (x + w, z)), ((x, z + w), (x + w, z + w))):
            _line(d, (a[0], y, a[1]), (b2[0], y + w, b2[1]), "minecraft:iron_bars")
        d.fill(x, y, z, x + w, y, z, "minecraft:waxed_exposed_cut_copper")


def lava_sea(d, R=330):
    d.fill(-R, LAVA - 2, -R, R, LAVA - 1, R, "minecraft:basalt[axis=y]")
    d.fill(-R, LAVA, -R, R, LAVA, R, "minecraft:lava")


def ladle(d, cx=0, cy=Y0 + 70, cz=-110, R=32):
    """거대 쇳물 국자: 빛나는 쇳물 덩이(구) + 오른쪽을 감싼 검은 국자 통 + 쏟아지는 쇳물 줄기."""
    for y in range(-R, R + 1):
        for x in range(-R, R + 1):
            r2 = x * x + y * y
            if r2 > R * R:
                continue
            zz = int(math.sqrt(R * R - r2) * 0.4)
            st = "minecraft:ochre_froglight" if r2 < (R * 0.8) ** 2 else "minecraft:shroomlight"
            d.fill(cx + x, cy + y, cz - zz, cx + x, cy + y, cz + zz, st)
    # 국자 통 (오른쪽 반을 감싼 검은 원통, 기울어짐)
    for a in np.linspace(-math.pi / 2, math.pi / 2, 200):
        for zz in range(-int(R * 0.6), int(R * 0.6) + 1):
            x = cx + int((R + 3) * math.cos(a)) + 6
            y = cy + int((R + 3) * math.sin(a))
            d.fill(x, y, cz + zz, x + 2, y, cz + zz, "minecraft:polished_blackstone")
    d.fill(cx + R + 6, cy - 4, cz - 3, cx + R + 26, cy + 4, cz + 3, "minecraft:polished_deepslate")   # 국자 자루·축
    # 쏟아지는 쇳물 줄기 (국자 아래 가장자리 → 쇳물 바다)
    for y in range(LAVA, cy - R + 4):
        t = (cy - R - y) / (cy - R - LAVA)
        w = 3 + int(2 * t)
        x0 = cx - 6 + int(4 * t)
        d.fill(x0 - w, y, cz - 2, x0 + w, y, cz + 2, "minecraft:ochre_froglight" if (y // 3) % 3 else "minecraft:shroomlight")


def machinery(d, rng):
    """검은 기계 구조물 숲 (붉게 달아오른 창·판) — 발판 앞쪽은 비움."""
    def skip(x, z):   # 발판 앞과 국자 앞은 비움 (원화처럼 국자가 다 보이게)
        return (abs(z) < HW + 24 and abs(x) <= BX + 10) or (abs(x) < 70 and -180 < z < -30)
    near = build_city(d, 40, 380, seed=1611, ground_y=LAVA - 1, h_min=80, h_max=170, skip=skip, spacing0=26,
                      size=(12, 26), palette=FURNACE_PAL)
    far = build_city(d, 420, 760, seed=1612, ground_y=LAVA - 1, h_min=140, h_max=260, spacing0=110, size=(16, 32),
                     palette=FURNACE_PAL)
    # 달아오른 큰 판 (원화의 붉은 사각형들)
    for _ in range(600):
        x, z = int(rng.uniform(-300, 300)), int(rng.uniform(-300, -40))
        y = int(rng.uniform(LAVA + 20, Y0 + 120))
        w, h = int(rng.integers(6, 16)), int(rng.integers(8, 20))
        # 구조물 벽 앞에만 붙임 (허공에 떠 있지 않게): 판 뒤 칸들이 막혀 있어야 함
        if any(d.get(x + dx, y + dy, z - 1) == "minecraft:air" for dx in (0, w) for dy in (0, h)):
            continue
        d.fill(x, y, z, x + w, y + h, z, HOT[int(rng.integers(len(HOT)))])
        d.fill(x - 1, y - 1, z + 1, x + w + 1, y + h + 1, z + 1, "minecraft:polished_blackstone")
        d.fill(x, y, z + 1, x + w, y + h, z + 1, "minecraft:air")
    return {"near": near, "far": far}


# ---------------------------------------------------------------- 게부라 방
RW, RD, RH = 13, 10, 12


def gebura_room(d, ox=ROOM_X):
    y0, yt = RY, RY + RH
    xs, zs = np.arange(ox - RW, ox + RW + 1), np.arange(-RD, RD + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    fl = np.where(S.hash01((X + (Z % 3) * 3) // 6, Z, seed=1621) < 0.5, d.id("minecraft:dark_oak_planks"),
                  d.id("minecraft:spruce_planks"))
    d.place(ox - RW, y0 - 1, -RD, fl[:, None, :])
    x0, x1, z0, z1 = ox - RW - 1, ox + RW + 1, -RD - 1, RD + 1
    for (a0, b0, a1, b1) in ((x0, z1, x1, z1), (x0, z0, x0, z1), (x1, z0, x1, z1)):
        d.fill(a0, y0, b0, a1, yt, b1, "minecraft:dark_oak_planks")
    d.fill(x0, yt, z0, x1, yt, z1, "minecraft:dark_oak_planks")
    # 북쪽 벽 = 큰 창 (검은 창틀) — 너머에 용광로 빛 (쇳물 국자)
    d.fill(x0, y0, z0, x1, yt, z0, "minecraft:polished_blackstone")
    for x in range(ox - RW + 1, ox + RW, 1):
        if (x - ox) % 7 == 0:
            continue
        d.fill(x, y0 + 2, z0, x, yt - 2, z0, "minecraft:orange_stained_glass_pane")
    d.fill(x0, y0 + 6, z0, x1, y0 + 6, z0, "minecraft:polished_blackstone")
    zb = z0 - 6                                                       # 창 너머
    d.fill(x0 - 4, y0 - 2, zb, x1 + 4, yt + 6, zb, "minecraft:magma_block")
    for _ in range(60):
        rng = np.random.default_rng(_)
        x, y = ox + int(rng.integers(-RW - 3, RW + 3)), y0 + int(rng.integers(-1, RH + 5))
        d.fill(x, y, zb, x + 2, y + 1, zb, "minecraft:shroomlight")
    for y in range(-4, 5):                                            # 국자 덩이
        for x in range(-4, 5):
            if x * x + y * y <= 16:
                d.set(ox + 6 + x, yt - 3 + y, zb + 1, "minecraft:ochre_froglight")
    d.fill(ox + 6, y0, zb + 1, ox + 7, yt - 7, zb + 1, "minecraft:shroomlight")
    d.fill(x0 - 4, y0 - 2, zb, x0 - 4, yt + 6, z0, "minecraft:polished_blackstone")
    d.fill(x1 + 4, y0 - 2, zb, x1 + 4, yt + 6, z0, "minecraft:polished_blackstone")
    d.fill(x0 - 4, yt + 6, zb, x1 + 4, yt + 6, z0, "minecraft:polished_blackstone")
    d.fill(x0 - 4, y0 - 2, zb, x1 + 4, y0 - 2, z0, "minecraft:polished_blackstone")
    # 왼쪽 책장
    d.fill(x0 + 1, y0, -RD, x0 + 1, yt - 1, RD, "minecraft:bookshelf")
    for y in range(y0 + 3, yt, 3):
        d.fill(x0 + 1, y, -RD, x0 + 1, y, RD, "minecraft:dark_oak_planks")
    # 큰 검은 소파 (오른쪽, 창 앞)
    sx0, sx1, sz = ox + 2, ox + 11, -RD + 2
    d.fill(sx0, y0, sz, sx1, y0, sz + 1, "minecraft:black_wool")
    d.fill(sx0, y0 + 1, sz, sx1, y0 + 1, sz, "minecraft:black_wool")                    # 등받이
    d.fill(sx0, y0 + 2, sz, sx1, y0 + 2, sz, "minecraft:blackstone_slab[type=bottom]")
    d.fill(sx0, y0, sz + 2, sx1, y0, sz + 2, "minecraft:blackstone_stairs[facing=north]")
    for x in (sx0 - 1, sx1 + 1):                                                         # 팔걸이
        d.fill(x, y0, sz, x, y0 + 1, sz + 2, "minecraft:black_wool")
    # 낮은 탁자 + 재떨이 + 컵, 흩어진 종이
    d.fill(ox - 3, y0, 1, ox + 8, y0, 3, "minecraft:dark_oak_slab[type=bottom]")
    d.set(ox + 1, y0, 2, "minecraft:flower_pot")
    d.set(ox + 4, y0, 2, "minecraft:white_candle[candles=1]")
    rng = np.random.default_rng(1631)
    for _ in range(40):
        x, z = ox + int(rng.integers(-RW + 2, RW)), int(rng.integers(-RD + 4, RD))
        if d.get(x, y0, z) == "minecraft:air":
            d.set(x, y0, z, "minecraft:white_carpet" if rng.random() < 0.7 else "minecraft:light_gray_carpet")
    for x in range(-RW + 4, RW, 7):
        d.set(ox + x, yt - 1, 0, "minecraft:light[level=9]")
    d.set_biome(ox - 40, -40, ox + 40, 40, "ruina:language_room")


def build(b):
    from . import fragment as F
    d = b.dim("language")
    rng = np.random.default_rng(1701)
    lava_sea(d)
    platform(d, rng)
    for x in (-170, 170):
        lattice_column(d, x, -20, LAVA - 2, Y0 + 220)
        lattice_column(d, x, 20, LAVA - 2, Y0 + 220)
    machinery(d, rng)
    ladle(d)
    gebura_room(d)
    F.stage(b, d, "iblock", "언어의 층", (ARRIVE_X + 0.5, Y0, 0.5, -90), (ROOM_X + 0.5, RY, RD - 2.5, 180))
    # 원화 속 출구(빛나는 문·창)는 조형물로만 — 층 사이 이동은 세피라 아이템 (모드)
    b.extra_checks.append({"what": "게부라 방 바이옴", "cmd": f"execute in {d.dim} if biome {ROOM_X} {RY} 0 ruina:language_room",
                           "expect": True})


_FIRE = dict(sky=((40, 12, 6), (90, 26, 10)), fog=(90, 26, 10), stars=0, night=False)
PREVIEW = [
    {"file": "language_compare_stage.png", "ref": "언어의 층 전경.png", "cam": (0.5, Y0 + 4, 34), "look": (0.5, Y0 + 30, -120),
     "kw": dict(fov=80, max_dist=800, fog_dist=300, **_FIRE),
     "title": "언어의 층 — 원화(위) / 맵(아래): 발판 옆에서 북쪽",
     "notes": ["강철판 발판·뒤 녹슨 난간, 거대 쇳물 국자와 쏟아지는 쇳물, 붉게 달아오른 기계 구조물 숲",
               "양옆 격자 기둥, 발판 아래 쇳물 바다(진짜 용암)"]},
    {"file": "language_compare_room.png", "ref": "언어의 층 지정사서 방.png", "cam": (ROOM_X - 6.5, RY + 2.2, RD - 1),
     "look": (ROOM_X + 4, RY + 3, -RD), "kw": dict(fov=80, max_dist=120, sky=((30, 10, 4), (70, 20, 8)), fog=(70, 20, 8),
                                                    fog_dist=60, stars=0),
     "title": "게부라 방 — 원화(위) / 맵(아래)",
     "notes": ["큰 창 너머 용광로 빛·국자, 왼쪽 책장, 검은 소파, 재떨이·컵 탁자, 흩어진 종이"]},
]
