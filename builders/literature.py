"""문학의 층 (호드). 접대 공간(나무 보도) ↔ 지정사서 방 (금괴 F).

참고: reference/문학의 층 전경.png, reference/문학의 층 지정사서 방.png, PLAN.md 8절 나무위키 요약
("광원은 모두 주홍빛 전구, 천장이 크기 제각각인 전구로 도배, 에스컬레이터형 책장으로 책 이동, 접대실 기둥 안에 특히 큰 전구").

원화(전경): 나무 판자 보도, 아래 검은 들보 + 팔각 아치가 이어진 고가 구조(아치 안에 줄 전구),
뒤로 사선으로 엇갈린 책장 계단(에스컬레이터형 책장) 여러 줄, 공중에 줄에 매달린 물방울 전구,
판자를 덧댄 나무 탑(불 켜진 창, 안에 큰 전구), 상자형 등불, 푸른 회색 안개.

크기 (처음 정한 1536×400, 사람 기준 1블록 ≈ 1m): 3겹
 ① 나무 보도 (x -200..200, 폭 17, 서 있는 높이 Y 150) + 아래 팔각 아치 고가
 ② 400 안쪽: 책장 계단 ~70줄, 나무 탑 8개, 매달린 전구 ~600개(작은 것 = 쇠사슬 랜턴, 큰 것 = 유리 + 발광 덩어리), 상자 등불
 ③ 400~700: 더 큰 책장 계단·탑 (Distant Horizons/높은 렌더 거리)
에스컬레이터형 책장은 이번엔 고정 (사용자 결정).
"""
from __future__ import annotations

import math

import numpy as np

from tools import shapes as S

Y0 = 150
BX, HW = 200, 8          # 보도 반길이, 반폭
ARRIVE_X = -150
ROOM_X = 4000
RY = 64
BULB_CORE = "minecraft:shroomlight"      # 주홍빛
BULB_GLASS = "minecraft:white_stained_glass"
WOODS = ["minecraft:spruce_planks", "minecraft:dark_oak_planks", "minecraft:stripped_spruce_wood",
         "minecraft:spruce_planks", "minecraft:stripped_dark_oak_wood"]


def _planks_along_x(d, x0, z0, x1, z1, y, mats, seed):
    """길이 방향(x)으로 긴 판자 (판자마다 길이·색 다르게)."""
    xs, zs = np.arange(x0, x1 + 1), np.arange(z0, z1 + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    off = (S.hash01(Z, seed=seed) * 7).astype(int)
    board = (X + off) // 7
    ids = np.array([d.id(m) for m in mats])[(S.hash01(board, Z, seed=seed + 1) * len(mats)).astype(int).clip(0, len(mats) - 1)]
    d.place(x0, y, z0, ids[:, None, :])


# ---------------------------------------------------------------- ① 보도 + 팔각 아치 고가

def walkway(d, rng):
    _planks_along_x(d, -BX, -HW, BX, HW, Y0 - 1, ["minecraft:spruce_planks", "minecraft:dark_oak_planks",
                                                    "minecraft:spruce_planks", "minecraft:jungle_planks"], 1001)
    for z in (-HW, HW):                                      # 보도 가장자리 테 (원화의 밝은 선)
        d.fill(-BX, Y0 - 1, z, BX, Y0 - 1, z, "minecraft:stripped_birch_log[axis=x]")
    d.fill(-BX, Y0 - 3, -HW, BX, Y0 - 2, HW, "minecraft:dark_oak_planks")   # 두께
    # 고가 구조: 양쪽 면에 팔각 아치가 이어진 검은 벽 (높이 22), 아치 테는 밝은 돌
    period, ow, oh = 24, 18, 14
    for z in (-HW, HW):
        d.fill(-BX, Y0 - 26, z, BX, Y0 - 4, z, "minecraft:polished_blackstone")
        d.fill(-BX, Y0 - 4, z, BX, Y0 - 4, z, "minecraft:smooth_stone")
        for xc in range(-BX + period // 2, BX, period):
            ya, yb = Y0 - 22, Y0 - 22 + oh
            for x in range(xc - ow // 2, xc + ow // 2 + 1):
                dxe = ow // 2 - abs(x - xc)
                cut = max(0, 4 - dxe)                       # 모서리를 깎아 팔각형
                for y in range(ya + cut, yb - cut + 1):
                    d.set(x, y, z, "minecraft:air")
                d.set(x, ya + cut - 1, z, "minecraft:smooth_stone")
                d.set(x, yb - cut + 1, z, "minecraft:smooth_stone")
            # 아치 안 줄 전구 (원화 아래쪽): 아치 위쪽에서 처진 줄 + 랜턴
            for t in np.linspace(0.1, 0.9, 6):
                x = int(xc - ow // 2 + ow * t)
                y = int(yb - 3 - 4 * math.sin(math.pi * t))
                d.set(x, y, z, "minecraft:lantern[hanging=true]")
                d.set(x, y + 1, z, "minecraft:iron_chain[axis=y]")
    # 교각: 아치 사이 기둥이 안개 속으로 (Y 0까지)
    for x in range(-BX, BX + 1, period):
        for z in (-HW, HW):
            d.fill(x - 1, 0, z, x + 1, Y0 - 26, z, "minecraft:polished_blackstone")
    # 보도 아래 가로 들보 (두 벽을 잇는)
    for x in range(-BX, BX + 1, 12):
        d.fill(x, Y0 - 5, -HW, x, Y0 - 4, HW, "minecraft:dark_oak_log[axis=z]")


# ---------------------------------------------------------------- ② 배경

def escalator(d, x0, y0, z0, n, sx, width=5, thick=4):
    """에스컬레이터형 책장: 1칸 오르고 1칸 나아가는 띠 (위·아래 톱니 모양 단), 옆 테는 짙은 나무, 6단마다 작은 빛."""
    for k in range(n):
        x, y = x0 + sx * k, y0 + k
        d.fill(x, y - thick, z0, x, y, z0 + width - 1, "minecraft:bookshelf")
        if thick > 2 and width > 2:   # 속은 비움 (위아래 단과 옆 테에 가려 안 보임)
            d.fill(x, y - thick + 1, z0 + 1, x, y - 1, z0 + width - 2, "minecraft:air")
        face = "east" if sx > 0 else "west"
        back = "west" if sx > 0 else "east"
        d.fill(x, y + 1, z0, x, y + 1, z0 + width - 1, f"minecraft:spruce_stairs[facing={face}]")
        d.fill(x, y - thick - 1, z0, x, y - thick - 1, z0 + width - 1, f"minecraft:spruce_stairs[facing={back},half=top]")
        d.fill(x, y - thick, z0, x, y + 1, z0, "minecraft:dark_oak_planks")
        d.fill(x, y - thick, z0 + width - 1, x, y + 1, z0 + width - 1, "minecraft:dark_oak_planks")
        if k % 6 == 3:
            d.set(x, y - 1, z0, BULB_CORE)
            d.set(x, y - 1, z0 + width - 1, BULB_CORE)


def escalators(d, rng, r_in=40, r_out=400, count=90, far=False):
    for _ in range(count):
        for _try in range(20):
            x = int(rng.uniform(-r_out, r_out))
            z = int(rng.uniform(-r_out, r_out))
            if abs(z) > r_in or abs(x) > BX + 40:
                break
        n = int(rng.integers(60, 170 if not far else 240))
        sx = 1 if rng.random() < 0.5 else -1
        y0 = int(rng.uniform(20, 300))
        if y0 + n > 520:
            n = 520 - y0
        escalator(d, x - sx * n // 2, y0, z, n, sx, width=7 if not far else 9, thick=5 if not far else 7)


def wood_tower(d, rng, cx, cz, w, h, y0=0, window=True, seed=0, window_y=None):
    """판자를 덧댄 나무 탑 (속 빔). 남쪽 면에 커튼 친 불 켜진 창 + 안에 큰 전구 (접대실 기둥 안 큰 전구)."""
    x0, x1, z0, z1 = cx - w // 2, cx + w // 2, cz - w // 2, cz + w // 2
    pid = np.array([d.id(p) for p in WOODS])
    for (a0, a1, fixed, along_x) in ((x0, x1, z0, True), (x0, x1, z1, True), (z0, z1, x0, False), (z0, z1, x1, False)):
        A, Y = np.meshgrid(np.arange(a0, a1 + 1), np.arange(y0, y0 + h + 1), indexing="ij")
        patch = S.hash01(A // 5, Y // 9, seed=1011 + seed)
        ids = pid[(patch * len(pid)).astype(int).clip(0, len(pid) - 1)]
        ids = np.where((A % 5 == 0) & (S.hash01(A, Y // 9, seed=1012 + seed) < 0.5),
                       d.id("minecraft:dark_oak_log[axis=y]"), ids)
        if along_x:
            d.place(a0, y0, fixed, ids[:, :, None])
        else:
            d.place(fixed, y0, a0, ids.T[None, :, :])
    d.fill(x0, y0 + h, z0, x1, y0 + h, z1, "minecraft:dark_oak_planks")
    # 위로 덧붙은 작은 상자 (원화의 울퉁불퉁한 탑 꼭대기)
    for k in range(int(rng.integers(1, 4))):
        bw = int(rng.integers(4, max(5, w // 2)))
        bx, bz = cx + int(rng.integers(-w // 3, w // 3)), cz + int(rng.integers(-w // 3, w // 3))
        bh = int(rng.integers(5, 16))
        d.fill(bx - bw // 2, y0 + h, bz - bw // 2, bx + bw // 2, y0 + h + bh, bz + bw // 2,
               WOODS[int(rng.integers(len(WOODS)))])
    if window:
        wy = window_y if window_y is not None else y0 + int(h * rng.uniform(0.45, 0.7))
        ww, wh = max(5, w // 3), max(8, w // 2)
        d.fill(cx - ww // 2 - 1, wy - 1, z1, cx + ww // 2 + 1, wy + wh + 1, z1, "minecraft:stripped_dark_oak_wood")
        d.fill(cx - ww // 2, wy, z1, cx + ww // 2, wy + wh, z1, "minecraft:white_stained_glass")   # 커튼 친 창
        big_bulb(d, cx, wy + wh // 2, z1 - 3, size=max(2, ww // 3))
        for x in range(cx - ww // 2, cx + ww // 2 + 1, 2):
            d.set(x, wy - 2, z1 + 1, "minecraft:dark_oak_trapdoor[facing=south,half=top]")


def big_bulb(d, cx, cy, cz, size=2):
    """큰 물방울 전구: 유리 껍질 + 주홍빛 속 (위로 갈수록 가늘어짐) + 위 꼭지."""
    for y in range(-size - 1, size * 2 + 1):
        r = size * (1.0 if y < 0 else max(0.25, 1 - y / (size * 2.2)))
        ri = int(math.ceil(r))
        for x in range(-ri, ri + 1):
            for z in range(-ri, ri + 1):
                dd = math.hypot(x, z)
                if dd <= r:
                    st = BULB_CORE if dd <= r - 1 and y < size else BULB_GLASS
                    d.set(cx + x, cy + y, cz + z, st)
    d.fill(cx, cy + size * 2 + 1, cz, cx, cy + size * 2 + 2, cz, "minecraft:copper_block")


def hanging_bulbs(d, rng, n=600, r=380):
    """줄에 매달린 전구 (위는 안개 속으로): 대부분 쇠사슬 + 랜턴, 일부는 큰 물방울 전구, 일부 상자 등불."""
    placed = 0
    while placed < n:
        x, z = int(rng.uniform(-r, r)), int(rng.uniform(-r, r))
        if abs(z) <= HW + 3 and abs(x) <= BX + 3:
            continue
        y = int(rng.uniform(Y0 - 40, Y0 + 180))
        L = int(rng.integers(6, 40))
        if d.get(x, y, z) != "minecraft:air":
            continue
        kind = rng.random()
        d.fill(x, y + 1, z, x, y + L, z, "minecraft:iron_chain[axis=y]")
        if kind < 0.78:
            d.set(x, y, z, "minecraft:lantern[hanging=true]")
        elif kind < 0.93:
            big_bulb(d, x, y - 4, z, size=int(rng.integers(1, 3)))
        else:                                            # 상자 등불
            d.fill(x - 1, y - 3, z - 1, x + 1, y, z + 1, "minecraft:ochre_froglight")
            d.fill(x - 1, y - 3, z - 1, x - 1, y, z - 1, "minecraft:dark_oak_log[axis=y]")
            d.fill(x + 1, y - 3, z + 1, x + 1, y, z + 1, "minecraft:dark_oak_log[axis=y]")
            d.fill(x - 1, y + 1, z - 1, x + 1, y + 1, z + 1, "minecraft:dark_oak_slab[type=bottom]")
        placed += 1


# ---------------------------------------------------------------- 호드 방
RW, RD, RH = 13, 11, 16


def hod_room(d, ox=ROOM_X):
    """원화: 천장까지 닿는 나무 책장 기둥들(앞으로 튀어나온 칸), 높이 제각각 매달린 전구 다발, 나무 바닥,
    책상 + 의자 넷, 오른쪽 안개 속으로 겹겹이 멀어지는 팔각 문틀 복도 (다음 층 예술 입구 예정)."""
    y0, yt = RY, RY + RH
    _planks_along_x(d, ox - RW, -RD, ox + RW, RD, y0 - 1, ["minecraft:spruce_planks", "minecraft:dark_oak_planks",
                                                          "minecraft:jungle_planks"], 1041)
    x0, x1, z0, z1 = ox - RW - 1, ox + RW + 1, -RD - 1, RD + 1
    for (a0, b0, a1, b1) in ((x0, z0, x1, z0), (x0, z1, x1, z1), (x0, z0, x0, z1), (x1, z0, x1, z1)):
        d.fill(a0, y0, b0, a1, yt, b1, "minecraft:bookshelf")
        for y in range(y0 + 4, yt, 4):
            d.fill(a0, y, b0, a1, y, b1, "minecraft:spruce_planks")
    d.fill(x0, yt, z0, x1, yt, z1, "minecraft:dark_oak_planks")
    # 책장 기둥 (원화 왼쪽: 바닥~천장, 칸마다 판, 앞면 테)
    for x in range(ox - RW + 2, ox + 2, 5):
        for z in (-RD + 1, -2):
            d.fill(x, y0, z, x + 2, yt - 1, z + 1, "minecraft:bookshelf")
            for y in range(y0 + 3, yt - 1, 3):
                d.fill(x, y, z, x + 2, y, z + 1, "minecraft:spruce_planks")
            d.fill(x, y0, z, x, yt - 1, z, "minecraft:dark_oak_log[axis=y]")
            d.fill(x + 2, y0, z, x + 2, yt - 1, z, "minecraft:dark_oak_log[axis=y]")
    # 책상 + 의자 넷
    d.fill(ox + 1, y0, 3, ox + 7, y0, 4, "minecraft:dark_oak_slab[type=top]")
    for x in (ox + 2, ox + 6):
        d.set(x, y0, 5, "minecraft:spruce_stairs[facing=south]")
        d.set(x, y0, 2, "minecraft:spruce_stairs[facing=north]")
    d.fill(ox + 3, y0 + 1, 3, ox + 4, y0 + 1, 3, "minecraft:brown_terracotta")   # 책
    # 오른쪽 팔각 문틀 복도: 벽에 구멍 → 4칸마다 밝은 팔각 테, 안쪽으로 갈수록 밝게(안개)
    zc, oh, ow = -2, 10, 8
    d.fill(x1, y0, zc - ow // 2, x1, y0 + oh, zc + ow // 2, "minecraft:air")
    for k in range(12):
        x = x1 + 1 + k * 4
        d.fill(x, y0 - 1, zc - ow // 2 - 1, x + 3, y0 - 1, zc + ow // 2 + 1, "minecraft:spruce_planks")
        d.fill(x, y0, zc - ow // 2 - 1, x + 3, y0 + oh + 1, zc - ow // 2 - 1, "minecraft:dark_oak_planks")
        d.fill(x, y0, zc + ow // 2 + 1, x + 3, y0 + oh + 1, zc + ow // 2 + 1, "minecraft:dark_oak_planks")
        d.fill(x, y0 + oh + 1, zc - ow // 2 - 1, x + 3, y0 + oh + 1, zc + ow // 2 + 1, "minecraft:dark_oak_planks")
        for z in range(zc - ow // 2, zc + ow // 2 + 1):          # 팔각 테 (모서리 깎음)
            dz = ow // 2 - abs(z - zc)
            cut = max(0, 2 - dz)
            d.set(x, y0 + oh - cut, z, "minecraft:calcite")
        for y in range(y0, y0 + oh):
            d.set(x, y, zc - ow // 2, "minecraft:calcite")
            d.set(x, y, zc + ow // 2, "minecraft:calcite")
        if k % 3 == 1:
            d.set(x + 2, y0 + oh, zc, "minecraft:lantern[hanging=true]")
    d.fill(x1 + 49, y0, zc - ow // 2, x1 + 49, y0 + oh, zc + ow // 2, "minecraft:pearlescent_froglight")  # 끝의 빛
    # 매달린 전구 다발 (높이 제각각)
    rng = np.random.default_rng(1051)
    for _ in range(40):
        x, z = ox + int(rng.integers(-RW + 1, RW)), int(rng.integers(-RD + 1, RD))
        L = int(rng.integers(1, 7))
        if d.get(x, yt - 1, z) != "minecraft:air":
            continue
        d.fill(x, yt - L, z, x, yt - 1, z, "minecraft:iron_chain[axis=y]")
        if rng.random() < 0.7:
            d.set(x, yt - L - 1, z, "minecraft:lantern[hanging=true]")
        else:
            d.set(x, yt - L - 1, z, BULB_CORE)
            d.set(x, yt - L - 2, z, BULB_GLASS)
    d.set_biome(ox - 40, -40, ox + 80, 40, "ruina:literature_room")


# ---------------------------------------------------------------- 조립

def build(b):
    from . import fragment as F
    d = b.dim("literature")
    rng = np.random.default_rng(1101)
    walkway(d, rng)
    escalators(d, rng)
    escalators(d, rng, r_in=400, r_out=700, count=40, far=True)
    towers = [(0, -60, 26, 230), (-170, -120, 22, 180), (160, -90, 20, 200), (-90, 110, 18, 160), (120, 140, 24, 220),
              (-300, -40, 30, 260), (300, 60, 28, 240), (40, -240, 34, 290)]
    for i, (cx, cz, w, h) in enumerate(towers):
        # 가운데 탑: 원화처럼 보도 눈높이에 불 켜진 창 (안에 큰 전구)
        wood_tower(d, rng, cx, cz, w, h, seed=i, window_y=Y0 - 4 if i == 0 else None)
    for i in range(10):     # ③ 먼 탑
        a = 2 * math.pi * i / 10 + 0.3
        wood_tower(d, rng, int(560 * math.cos(a)), int(560 * math.sin(a)), int(rng.integers(30, 44)),
                   int(rng.integers(260, 380)), window=False, seed=20 + i)
    hanging_bulbs(d, rng)
    hod_room(d)

    F.stage(b, d, "goldbar", "문학의 층", (ARRIVE_X + 0.5, Y0, 0.5, -90), (ROOM_X + 0.5, RY, RD - 2.5, 180))
    # 원화 속 출구(빛나는 문·창)는 조형물로만 — 층 사이 이동은 세피라 아이템 (모드)
    b.extra_checks.append({"what": "호드 방 바이옴", "cmd": f"execute in {d.dim} if biome {ROOM_X} {RY} 0 ruina:literature_room",
                           "expect": True})
