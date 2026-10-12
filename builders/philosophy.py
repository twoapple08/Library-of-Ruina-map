"""철학의 층 (비나). 접대 공간(도시 상공의 돌다리) ↔ 지정사서 방 (모루 F).

참고: reference/철학의 층 전경.png, reference/철학의 층 지정사서 방.png, PLAN.md 8절
("다른 층보다 큰 위압감, 도시 상공의 다리 아래로 도시 야경").

원화(전경): 밤하늘 가로지르는 금빛 은하수 띠, 초승달, 작은 금빛 등이 박힌 넓은 돌 포장 다리(가장자리 살짝 휨),
다리 아래 그늘과 안개 너머 아득한 도시 야경.
원화(방): 동굴 같은 어두운 서고, 뒤틀린 검은 기둥들, 층층이 쌓인 책장이 금빛으로 달아오름, 가운데 뒤 금빛 빛(다음 층 입구),
매달린 팔각 별 등, 빛이 비치는 어두운 반들 바닥, 오른쪽 작은 둥근 탁자(촛불·찻잔)와 의자.

크기 (2048×400): 다리 400×41 (서 있는 Y 300), 도시 바닥 Y 0 (안쪽 400 + 먼 겹), 은하수 띠는 북쪽 하늘 Y 330~460.
"""
from __future__ import annotations

import math

import numpy as np

from tools import shapes as S

from .city import build_city

Y0 = 300
BX, HW = 200, 20
ARRIVE_X = -150
ROOM_X = 4000
RY = 64
PAVE = ["minecraft:stone_bricks", "minecraft:cracked_stone_bricks", "minecraft:polished_andesite", "minecraft:deepslate_bricks",
        "minecraft:stone_bricks", "minecraft:tuff_bricks"]
NIGHT_PAL = {
    "walls": (["minecraft:black_concrete", "minecraft:gray_concrete", "minecraft:polished_blackstone", "minecraft:blue_terracotta",
               "minecraft:purple_terracotta"], [16, 10, 10, 8, 6]),
    "lit": (["minecraft:ochre_froglight", "minecraft:pearlescent_froglight", "minecraft:glowstone"], [50, 30, 20]),
    "neon": (["minecraft:pearlescent_froglight"], [1]),
    "trim": (["minecraft:polished_blackstone_bricks"], [1]),
    "corner_neon": 0.05, "corners": 1, "roof_neon": 0.0, "lit_ratio": (0.2, 0.5),
}


def bridge(d, rng):
    """넓은 돌 포장 다리: 엇갈린 포석(띠마다 어긋남), 작은 금빛 등이 박힘, 뒤 가장자리 살짝 휜 테, 두꺼운 그늘진 아랫면."""
    xs, zs = np.arange(-BX, BX + 1), np.arange(-HW, HW + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    pave = np.array([d.id(s) for s in PAVE])
    off = (Z // 2) % 2 * 2
    ids = pave[(S.hash01((X + off) // 4, Z // 2, seed=2001) * len(pave)).astype(int).clip(0, len(pave) - 1)]
    lamp = S.hash01(X, Z, seed=2002) < 0.012
    ids = np.where(lamp, d.id("minecraft:ochre_froglight"), ids)
    curve = (HW - np.abs(X) ** 2 / (BX ** 2) * 6).astype(int)        # 뒤(북) 가장자리 살짝 휨
    ids = np.where(Z < -curve, -1, ids)
    d.place(-BX, Y0 - 1, -HW, ids[:, None, :])
    for x in range(-BX, BX + 1):
        zb = -int(HW - x * x / (BX ** 2) * 6)
        d.fill(x, Y0 - 1, zb, x, Y0 - 1, zb, "minecraft:polished_deepslate")
        d.fill(x, Y0 - 6, zb, x, Y0 - 2, zb, "minecraft:deepslate_bricks")
    d.fill(-BX, Y0 - 6, HW, BX, Y0 - 2, HW, "minecraft:deepslate_bricks")
    d.fill(-BX, Y0 - 6, -HW, BX, Y0 - 6, HW, "minecraft:polished_deepslate")       # 아랫면
    for x in (-BX, BX):
        d.fill(x, Y0 - 6, -HW, x, Y0 - 1, HW, "minecraft:deepslate_bricks")
    # 아치 받침 (아래 도시로)
    for x in range(-BX + 40, BX, 80):
        for z in (-HW + 4, HW - 4):
            d.fill(x - 3, 0, z - 3, x + 3, Y0 - 7, z + 3, "minecraft:deepslate_bricks")
            d.fill(x - 2, 0, z - 2, x + 2, Y0 - 8, z + 2, "minecraft:air")


def milky_way(d, rng, n=6000):
    """금빛 은하수 띠 (원화): 북쪽 하늘을 가로지르는 띠 모양으로 작은 빛 블록을 흩뿌림 (가운데 짙게)."""
    glows = ["minecraft:ochre_froglight", "minecraft:shroomlight", "minecraft:glowstone", "minecraft:pearlescent_froglight"]
    dust = ["minecraft:red_terracotta", "minecraft:brown_terracotta", "minecraft:orange_terracotta", "minecraft:red_nether_bricks"]
    for _ in range(n):
        u = rng.uniform(-1, 1)
        x = u * 340
        v = rng.normal(0, 1) * (14 + 10 * (1 - abs(u)))
        y = 430 + 30 * (1 - u * u) + v
        z = -300 - 40 * u * u + rng.normal(0, 14)
        if y > 560 or y < 340:
            continue
        # 붉은 먼지(빛 없음) 70% + 빛나는 점 30% — 원화의 붉은 먼지 띠 속 금빛 점
        pal = glows if rng.random() < 0.3 else dust
        d.set(int(x), int(y), int(z), pal[int(rng.integers(len(pal)))])


# ---------------------------------------------------------------- 비나 방
RW, RD, RH = 18, 16, 22


def _star(d, cx, cy, cz, r):
    """매달린 팔각 별 등: 가로·세로·대각 막대 (빛 블록)."""
    for k in range(-r, r + 1):
        for (dx, dy) in ((k, 0), (0, k), (k, k) if abs(k) <= r * 0.7 else (0, 0), (k, -k) if abs(k) <= r * 0.7 else (0, 0)):
            d.set(cx + dx, cy + dy, cz, "minecraft:ochre_froglight")
    d.set(cx, cy, cz, "minecraft:glowstone")


def binah_room(d, ox=ROOM_X):
    y0, yt = RY, RY + RH
    rng = np.random.default_rng(2011)
    # 반들 어두운 바닥 (돌·흑요석 결), 가운데 빛 비친 길
    xs, zs = np.arange(ox - RW, ox + RW + 1), np.arange(-RD, RD + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    fl = np.where(S.hash01(X // 3, Z // 3, seed=2012) < 0.6, d.id("minecraft:polished_blackstone"), d.id("minecraft:polished_deepslate"))
    fl = np.where((np.abs(X - ox) < 2 + (Z + RD) * 0.1) & (S.hash01(X, Z, seed=2013) < 0.25), d.id("minecraft:ochre_froglight"), fl)
    d.place(ox - RW, y0 - 1, -RD, fl[:, None, :])
    # 동굴 벽: 울퉁불퉁한 검은 바위 (둥근 천장)
    for x in range(-RW - 2, RW + 3):
        for z in range(-RD - 2, RD + 3):
            edge = max(abs(x) / (RW + 1), abs(z) / (RD + 1))
            if edge < 0.94:
                continue
            h = yt + int(4 * S.hash01(np.array(x // 3), np.array(z // 3), seed=2014))
            d.fill(ox + x, y0, z, ox + x, h, z, "minecraft:blackstone" if (x + z) % 3 else "minecraft:basalt[axis=y]")
    for x in range(-RW - 2, RW + 3):
        for z in range(-RD - 2, RD + 3):
            h = yt + int(5 * (1 - (x / (RW + 2)) ** 2) * (1 - (z / (RD + 2)) ** 2))
            d.set(ox + x, h, z, "minecraft:blackstone")
    # 층층이 쌓인 금빛 책장 더미 (양옆, 안쪽으로 갈수록 높게)
    for side in (-1, 1):
        for k in range(10):
            x = ox + side * int(rng.integers(6, RW - 1))
            z = -RD + 1 + int(rng.integers(0, RD))
            w, h = int(rng.integers(2, 5)), int(rng.integers(5, 14))
            d.fill(x, y0, z, x + w, y0 + h, z + 1, "minecraft:bookshelf")
            for y in range(y0 + 3, y0 + h, 3):
                if rng.random() < 0.3:   # 몇 칸만 달아오름
                    d.set(x + int(rng.integers(0, w + 1)), y, z + 2, "minecraft:shroomlight")
    # 뒤틀린 검은 기둥 (바닥 → 천장, 굽어 오름)
    for i in range(8):
        bx, bz = ox + int(rng.uniform(-RW + 3, RW - 3)), int(rng.uniform(-RD + 2, -2))
        if abs(bx - ox) < 4:
            continue
        for y in range(y0, yt + 3):
            t = (y - y0) / (yt - y0)
            x = bx + int(3 * math.sin(t * 3 + i))
            r = 1 + int(1.5 * (1 - t))
            d.fill(x - r, y, bz - r, x + r, y, bz + r, "minecraft:blackstone")
    # 가운데 뒤 금빛 빛 (다음 층 입구)
    d.fill(ox - 4, y0, -RD - 1, ox + 4, y0 + 14, -RD - 1, "minecraft:ochre_froglight")
    d.fill(ox - 2, y0, -RD - 2, ox + 2, y0 + 18, -RD - 2, "minecraft:pearlescent_froglight")
    d.fill(ox - 3, y0, -RD, ox + 3, y0 + 12, -RD, "minecraft:air")
    # 매달린 팔각 별 등
    for i in range(10):
        sx, sy, sz = ox + int(rng.uniform(-6, 6)), yt - int(rng.integers(3, 9)), int(rng.uniform(-RD + 3, -2))
        _star(d, sx, sy, sz, int(rng.integers(1, 3)))
        d.fill(sx, sy + 2, sz, sx, yt, sz, "minecraft:iron_chain[axis=y]")
    # 오른쪽 작은 둥근 탁자 + 촛불·찻잔 + 의자
    tx, tz = ox + 10, 6
    d.set(tx, y0, tz, "minecraft:dark_oak_fence")
    d.fill(tx - 1, y0 + 1, tz - 1, tx + 1, y0 + 1, tz + 1, "minecraft:dark_oak_slab[type=bottom]")
    d.set(tx - 1, y0 + 1, tz, "minecraft:dark_oak_slab[type=bottom]")
    d.set(tx, y0 + 2, tz, "minecraft:candle[lit=true,candles=3]")
    d.set(tx + 1, y0 + 2, tz - 1, "minecraft:flower_pot")
    d.set(tx + 2, y0, tz, "minecraft:dark_oak_stairs[facing=east]")
    d.set(tx + 3, y0 + 1, tz, "minecraft:dark_oak_trapdoor[facing=west,open=true]")
    d.set_biome(ox - 40, -40, ox + 40, 40, "ruina:philosophy_room")


def build(b):
    from . import fragment as F
    d = b.dim("philosophy")
    rng = np.random.default_rng(2101)
    bridge(d, rng)
    skip = lambda x, z: False   # noqa: E731
    build_city(d, 20, 420, seed=2111, ground_y=0, h_min=30, h_max=110, skip=skip, spacing0=26, size=(12, 26),
               palette=NIGHT_PAL)
    build_city(d, 460, 900, seed=2112, ground_y=0, h_min=40, h_max=140, spacing0=70, size=(14, 30), palette=NIGHT_PAL)
    d.fill(-420, -1, -420, 420, -1, 420, "minecraft:black_concrete")
    milky_way(d, rng)
    binah_room(d)
    F.stage(b, d, "anvil", "철학의 층", (ARRIVE_X + 0.5, Y0, 0.5, -90), (ROOM_X + 0.5, RY, RD - 2.5, 180))
    # 원화 속 출구(빛나는 문·창)는 조형물로만 — 층 사이 이동은 세피라 아이템 (모드)
    b.extra_checks.append({"what": "비나 방 바이옴", "cmd": f"execute in {d.dim} if biome {ROOM_X} {RY} 0 ruina:philosophy_room",
                           "expect": True})


_NIGHT = dict(sky=((6, 6, 14), (24, 20, 30)), fog=(40, 30, 30), stars=900)
PREVIEW = [
    {"file": "philosophy_compare_stage.png", "ref": "철학의 층 전경.png", "cam": (0.5, Y0 + 8, 60), "look": (0.5, Y0 + 40, -140),
     "kw": dict(fov=82, max_dist=900, fog_dist=700, **_NIGHT),
     "title": "철학의 층 — 원화(위) / 맵(아래): 다리 앞쪽 위에서 북쪽",
     "notes": ["금빛 등이 박힌 돌 포장 다리, 북쪽 하늘의 금빛 은하수 띠(빛 블록), 초승달(게임 하늘)",
               "다리 아래 아득한 도시 야경 (Y 0)"]},
    {"file": "philosophy_compare_room.png", "ref": "철학의 층 지정사서 방.png", "cam": (ROOM_X + 0.5, RY + 3, RD - 1),
     "look": (ROOM_X + 0.5, RY + 6, -RD), "kw": dict(fov=82, max_dist=150, sky=((10, 6, 2), (30, 18, 6)), fog=(40, 24, 8),
                                                      fog_dist=70, stars=0),
     "title": "비나 방 — 원화(위) / 맵(아래)",
     "notes": ["동굴 같은 서고, 금빛으로 달아오른 책장 더미, 뒤틀린 검은 기둥, 매달린 별 등, 가운데 금빛 빛(다음 층)"]},
]
