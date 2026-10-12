"""총류의 층 (롤랑). 접대 공간(책더미 다리) ↔ 지정사서 방 (임시: 마법이 부여된 황금사과 F). 마지막 층.

참고: reference/총류의 층 전경.png, reference/총류의 층 전경 (배경만).png,
reference/총류의 층 지정사서 방.png (사용자 제공, 2026-10-12), PLAN.md 8절
("최상층. 책이 산더미처럼 쌓임, 빌딩만 한 책꽂이, 책더미가 다리처럼 바닥을 이룸, 책탑").

원화(전경): 가장자리가 책 층층이 드러난 다리 (위는 잿빛 돌판), 다리 위 작은 책 더미 피라미드,
뒤로 비틀려 솟은 책탑들, 그 뒤 빌딩만 한 책장 벽(옅은 안개, 빛), 아래 어두운 물과 떨어지는 종이.
원화(방): 빌딩만 한 책장 벽 앞 거대한 촉수처럼 비틀린 책탑, 뒤에서 비치는 빛, 잿빛 안개.

크기 (2048×512): 다리 400×29 (서 있는 Y 120), 책탑 12개 (높이 120~260), 책장 벽 (거리 250~380, 높이 400), 물 Y 40.
"""
from __future__ import annotations

import math

import numpy as np

from tools import shapes as S

Y0 = 120
BX, HW = 200, 14
WATER = 40
ARRIVE_X = -150
ROOM_X = 4000
RY = 64
BOOKS = ["minecraft:gray_terracotta", "minecraft:black_terracotta", "minecraft:light_gray_terracotta", "minecraft:brown_terracotta",
         "minecraft:deepslate_bricks", "minecraft:white_terracotta", "minecraft:dark_oak_planks", "minecraft:gray_terracotta"]   # 잿빛 책 (원화)
PLATE = ["minecraft:polished_deepslate", "minecraft:deepslate_tiles", "minecraft:polished_tuff", "minecraft:polished_deepslate"]


def _books(d, n):
    return np.array([d.id(s) for s in BOOKS])


def book_layer(d, x0, y, z0, x1, z1, seed, along_x=True):
    """책 한 층: 책등이 보이게 짧은 칸마다 색이 바뀜 (가장자리만 블록, 속은 비움)."""
    books = _books(d, 0)
    xs, zs = np.arange(x0, x1 + 1), np.arange(z0, z1 + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    key = (X // 2) if not along_x else (Z // 2)
    ids = books[(S.hash01(key, np.full_like(X, y), (Z if not along_x else X) // 5, seed=seed) * len(books)).astype(int)
                .clip(0, len(books) - 1)]
    edge = (X == x0) | (X == x1) | (Z == z0) | (Z == z1)
    return ids, edge


def bridge(d, rng):
    """책더미 다리: 위 잿빛 돌판, 가장자리는 책 층층이 (아래로 들쭉날쭉 15칸)."""
    xs, zs = np.arange(-BX, BX + 1), np.arange(-HW, HW + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    plate = np.array([d.id(s) for s in PLATE])
    ids = plate[(S.hash01(X // 5, Z // 4, seed=2401) * len(plate)).astype(int).clip(0, len(plate) - 1)]
    ids = np.where((X % 5 == 0) | (Z % 4 == 0), d.id("minecraft:deepslate_tiles"), ids)
    d.place(-BX, Y0 - 1, -HW, ids[:, None, :])
    books = _books(d, 0)
    for x in range(-BX, BX + 1):
        depth = 8 + int(10 * S.hash01(np.array(x // 6), seed=2402))
        for z in (-HW, HW, -HW - 1, HW + 1):
            col = books[(S.hash01(np.full(depth, x // 2), np.arange(depth), np.full(depth, z), seed=2403) * len(books))
                        .astype(int).clip(0, len(books) - 1)]
            dz = 0 if abs(z) == HW else (1 if S.hash01(np.array(x // 3), np.array(z), seed=2404) < 0.5 else 0)
            if abs(z) == HW + 1 and not dz:
                continue
            d.place(x, Y0 - 1 - depth, z, col[None, :, None].astype(np.int32))
    for x in (-BX, BX):
        d.fill(x, Y0 - 16, -HW, x, Y0 - 2, HW, "minecraft:brown_terracotta")
    d.fill(-BX, Y0 - 16, -HW, BX, Y0 - 16, HW, "minecraft:black_terracotta")
    # 다리 위 작은 책 더미 피라미드, 흩어진 책
    for _ in range(14):
        x, z = int(rng.uniform(-BX + 10, BX - 10)), int(rng.uniform(-HW + 2, HW - 2))
        if abs(z) < 4 and abs(x - ARRIVE_X) < 10:
            continue
        h = int(rng.integers(2, 5))
        for k in range(h):
            d.fill(x - (h - k), Y0 + k, z - (h - k) // 2, x + (h - k), Y0 + k, z + (h - k) // 2,
                   BOOKS[int(rng.integers(len(BOOKS)))])
    for _ in range(80):
        x, z = int(rng.uniform(-BX, BX)), int(rng.uniform(-HW, HW))
        if d.get(x, Y0, z) == "minecraft:air":
            d.set(x, Y0, z, ["minecraft:white_carpet", "minecraft:brown_carpet", "minecraft:black_carpet"][int(rng.integers(3))])


def book_tower(d, rng, cx, cz, h, w0=12, y0=WATER - 5, seed=0):
    """비틀려 솟은 책탑: 층마다 책 한 겹 (방향 번갈아), 중심이 사인 곡선으로 흔들리며 위로 가늘어짐. 속은 비움."""
    books = _books(d, 0)
    ph = rng.uniform(0, 6.3)
    for k, y in enumerate(range(y0, y0 + h)):
        t = (y - y0) / h
        w = max(4, int(w0 * 1.8 * (1 - 0.6 * t) * (1 + 0.15 * math.sin(k / 3))))   # 원화의 굵은 책더미
        dd = max(3, int(w * 0.7))
        ox = cx + int(14 * t * math.sin(t * 5 + ph) + 3 * math.sin(k / 2.3))
        oz = cz + int(10 * t * math.cos(t * 4 + ph))
        along = (k // 2) % 2 == 0
        x0, x1 = (ox - w // 2, ox + w // 2) if along else (ox - dd // 2, ox + dd // 2)
        z0, z1 = (oz - dd // 2, oz + dd // 2) if along else (oz - w // 2, oz + w // 2)
        ids, edge = book_layer(d, x0, y, z0, x1, z1, 2410 + seed, along)
        top = (y == y0 + h - 1)
        d.place(x0, y, z0, np.where(edge | top, ids, -1)[:, None, :].astype(np.int32))


def shelf_wall(d, x0, x1, z, y0, y1):
    """빌딩만 한 책장 벽 (남쪽 면): 책장 + 세로 칸막이 + 가로 판."""
    d.fill(x0, y0, z, x1, y1, z, "minecraft:bookshelf")
    for x in range(x0, x1 + 1, 12):
        d.fill(x, y0, z + 1, x + 1, y1, z + 1, "minecraft:dark_oak_log[axis=y]")
    for y in range(y0 + 6, y1, 6):
        d.fill(x0, y, z, x1, y, z, "minecraft:dark_oak_planks")


def backdrop(d, rng):
    """뒤 책장 빌딩들 (사이로 빛) — 원화 배경."""
    x = -420
    while x < 420:
        w = int(rng.integers(50, 90))
        z = -int(rng.integers(250, 330))
        shelf_wall(d, x, x + w, z, WATER - 10, Y0 + int(rng.integers(260, 400)))
        for zz in range(z - 20, z):
            d.fill(x, WATER - 10, zz, x, WATER - 10 + 1, zz, "minecraft:bookshelf")
        x += w + int(rng.integers(6, 16))
    for i in range(10):     # ③ 먼 책장 빌딩 (DH)
        a = 2 * math.pi * i / 10
        cx, cz = int(700 * math.cos(a)), int(700 * math.sin(a))
        shelf_wall(d, cx - 60, cx + 60, cz, WATER - 10, Y0 + 400)
    d.fill(-420, WATER - 1, -420, 420, WATER - 1, 420, "minecraft:black_concrete")
    d.fill(-420, WATER, -420, 420, WATER, 420, "minecraft:water")


# ---------------------------------------------------------------- 롤랑 방 (사용자 제공 원화)
RW, RD, RH = 30, 30, 90


def roland_room(d, rng, ox=ROOM_X):
    y0, yt = RY, RY + RH
    xs, zs = np.arange(ox - RW, ox + RW + 1), np.arange(-RD, RD + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    fl = np.where(S.hash01(X // 4, Z // 4, seed=2421) < 0.5, d.id("minecraft:polished_deepslate"), d.id("minecraft:deepslate_tiles"))
    d.place(ox - RW, y0 - 1, -RD, fl[:, None, :])
    x0, x1, z0, z1 = ox - RW - 1, ox + RW + 1, -RD - 1, RD + 1
    for (a0, a1, z) in ((x0, x1, z1),):
        shelf_wall(d, a0, a1, z, y0, yt)
    for xw in (x0, x1):
        d.fill(xw, y0, z0, xw, yt, z1, "minecraft:bookshelf")
        for y in range(y0 + 6, yt, 6):
            d.fill(xw, y, z0, xw, y, z1, "minecraft:dark_oak_planks")
    # 북쪽: 빌딩만 한 책장 두 채 사이 빛 (원화 가운데 밝은 틈)
    shelf_wall(d, x0, ox - 6, z0, y0, yt)
    shelf_wall(d, ox + 6, x1, z0, y0, yt)
    d.fill(ox - 5, y0, z0 - 4, ox + 5, yt, z0 - 4, "minecraft:pearlescent_froglight")
    d.fill(ox - 5, y0, z0, ox + 5, yt, z0, "minecraft:air")
    for x in (ox - 6, ox + 6):
        d.fill(x, y0, z0 - 4, x, yt, z0, "minecraft:bookshelf")
    d.fill(x0, yt, z0 - 4, x1, yt, z1, "minecraft:dark_oak_planks")
    # 촉수처럼 비틀린 거대 책탑 (원화 가운데) + 작은 것 둘
    book_tower(d, rng, ox - 4, z0 + 12, RH - 6, w0=16, y0=y0, seed=40)
    book_tower(d, rng, ox + 12, z0 + 14, RH // 2, w0=7, y0=y0, seed=41)
    book_tower(d, rng, ox + 18, z0 + 8, RH // 3, w0=6, y0=y0, seed=42)
    for _ in range(30):   # 바닥 책 더미
        x, z = ox + int(rng.integers(-RW + 2, RW - 1)), int(rng.integers(-RD + 2, RD - 1))
        if d.get(x, y0, z) != "minecraft:air":
            continue
        for y in range(int(rng.integers(1, 4))):
            d.set(x, y0 + y, z, BOOKS[int(rng.integers(len(BOOKS)))])
    for x in range(-RW + 5, RW, 10):
        for z in range(-RD + 5, RD, 10):
            d.set(ox + x, y0 + 30, z, "minecraft:light[level=10]")
    d.set_biome(ox - 60, -60, ox + 60, 60, "ruina:general_room")


def build(b):
    from . import fragment as F
    d = b.dim("general")
    rng = np.random.default_rng(2501)
    backdrop(d, rng)
    bridge(d, rng)
    for i, (cx, cz, h, w) in enumerate(((-220, -90, 230, 18), (-90, -120, 170, 13), (40, -100, 200, 12), (150, -130, 190, 11),
                                        (280, -110, 250, 16), (-300, 80, 210, 14), (-60, 110, 160, 12), (110, 120, 220, 14),
                                        (300, 90, 180, 12), (-160, -220, 260, 16), (200, -230, 240, 15), (0, -260, 280, 18))):
        book_tower(d, rng, cx, cz, h, w0=w, seed=i)
    roland_room(d, rng)
    F.stage(b, d, "eapple", "총류의 층", (ARRIVE_X + 0.5, Y0, 0.5, -90), (ROOM_X + 0.5, RY, RD - 2.5, 180))
    b.extra_checks.append({"what": "롤랑 방 바이옴", "cmd": f"execute in {d.dim} if biome {ROOM_X} {RY} 0 ruina:general_room",
                           "expect": True})


_HAZE = dict(sky=((120, 116, 108), (176, 170, 158)), fog=(150, 146, 136), stars=0, night=False)
PREVIEW = [
    {"file": "general_compare_stage.png", "ref": "총류의 층 전경.png", "cam": (0.5, Y0 + 4, 40), "look": (0.5, Y0 + 40, -150),
     "kw": dict(fov=80, max_dist=800, fog_dist=400, **_HAZE),
     "title": "총류의 층 — 원화(위) / 맵(아래): 다리 앞쪽에서 북쪽",
     "notes": ["책 층층이 드러난 다리(위 잿빛 돌판)·책 더미, 비틀려 솟은 책탑들, 빌딩만 한 책장 벽, 아래 어두운 물"]},
    {"file": "general_compare_room.png", "ref": "총류의 층 지정사서 방.png", "cam": (ROOM_X + 0.5, RY + 6, RD - 1),
     "look": (ROOM_X + 0.5, RY + 40, -RD), "kw": dict(fov=80, max_dist=160, sky=((90, 88, 84), (140, 136, 128)),
                                                       fog=(120, 116, 108), fog_dist=120, stars=0, night=False),
     "title": "롤랑 방 — 원화(위) / 맵(아래)",
     "notes": ["빌딩만 한 책장 벽 사이 빛, 촉수처럼 비틀린 거대 책탑 (지정사서 방 원화: 사용자 제공)"]},
]
