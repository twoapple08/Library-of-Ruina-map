"""로비 (앤젤라). 두 모습: 전환 전 '어두운 나무 방' ↔ 전환 후 '밝은 책장 홀'.

참고: reference/로비.png (전환 전, 계단·기둥·벽등), reference/로비 전경 (전환 후).jpg (가운데 책상),
reference/로비_3D/ (공식 3D 영상 프레임: 01~07 전환 전 방, 08~19 전환 후 홀, story_* 공식 스토리 전환 장면).

크기 (사람 기준, 1블록 ≈ 1m): 3D 영상 19번 프레임에서 사람 키 ≈ 흰 계단 2.4단 → 계단 한 단 ≈ 0.7m → 1블록.
가운데 책상 = 앉은 캐릭터 기준 책상 높이 1블록 (단 위). 원화(전환 후)에서 책상 폭:높이 ≈ 4:1 → 폭 5.
홀 지름 ≈ 책상 폭 × 9 (3D 영상) → 반지름 22, 책장 벽 높이 12 (사다리가 사람 키의 3배쯤).

두 공간은 같은 차원(ruina:lobby)에서 HALL_DX만큼 떨어져 있고, 은조각을 왼손으로 들면(F)
같은 상대 위치로 순간이동한다 (차원 이동이 아니라서 로딩 화면이 없음).
"""
from __future__ import annotations

import math

import numpy as np

from tools import shapes as S

Y0 = 64            # 서 있는 높이 (바닥 블록 Y0-1)
HALL_DX = 512      # 홀 = 방 + (512, 0, 0)

# ---------------------------------------------------------------- 방 (전환 전)
RX, RZ = 10, 16    # 안쪽 반폭 (x -10..10, z -16..16)
RH = 10            # 천장 높이 (안쪽 Y0..Y0+9)
FLOOR = ["minecraft:mangrove_planks", "minecraft:dark_oak_planks", "minecraft:spruce_planks"]
PILLAR = "minecraft:dark_oak_log[axis=y]"          # 껍질 무늬 = 세로 홈 (원화의 홈 파인 기둥)
PLINTH = "minecraft:stripped_dark_oak_wood"
BOARD = "minecraft:dark_oak_planks"


def _floor(d, x0, z0, x1, z1, y, mats, seed):
    """나무 바닥: z 방향으로 긴 판자 줄 (폭 1, 길이 3~6 엇갈림)."""
    xs = np.arange(x0, x1 + 1)
    zs = np.arange(z0, z1 + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    off = (S.hash01(X, seed=seed) * 6).astype(int)
    plank = np.floor((Z + off) / 5).astype(int)
    h = S.hash01(X, plank, seed=seed + 1)
    ids = np.array([d.id(m) for m in mats])[(h * len(mats)).astype(int).clip(0, len(mats) - 1)]
    d.place(x0, y, z0, ids[:, None, :])


def _shelf_wall(d, x0, z0, x1, z1, y0, y1):
    """책장 벽 (한 줄): 아래 걸레받이, 3칸마다 판자 선반, 맨 위 판자."""
    d.fill(x0, y0, z0, x1, y1, z1, "minecraft:bookshelf")
    d.fill(x0, y0, z0, x1, y0, z1, BOARD)
    for y in range(y0 + 4, y1, 4):
        d.fill(x0, y, z0, x1, y, z1, "minecraft:stripped_dark_oak_log[axis=%s]" % ("x" if x1 > x0 else "z"))
    d.fill(x0, y1, z0, x1, y1, z1, BOARD)


def _pillar(d, x, z, y0, top, face, lamp=True):
    """벽에 붙은 홈 기둥: 받침 2 + 기둥 + 주두(뒤집힌 계단), 벽등(울타리 팔 + 매단 랜턴)."""
    d.fill(x, y0, z, x, y0 + 1, z, PLINTH)
    d.fill(x, y0 + 2, z, x, top - 1, z, PILLAR)
    d.set(x, top, z, PLINTH)
    fx, fz = face
    opp = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}[(fx, fz)]
    back = {"east": "west", "west": "east", "south": "north", "north": "south"}[opp]
    d.set(x + fx, top, z + fz, f"minecraft:dark_oak_stairs[facing={back},half=top]")
    if lamp:
        ly = y0 + 6
        d.set(x + fx, ly, z + fz, "minecraft:dark_oak_fence")
        d.set(x + fx, ly - 1, z + fz, "minecraft:lantern[hanging=true]")


def build_room(d):
    """전환 전: 어둡고 따뜻한 나무 방. 3D 영상 01~07 + 원화(로비.png)."""
    x0, x1, z0, z1 = -RX - 1, RX + 1, -RZ - 1, RZ + 1
    yt = Y0 + RH
    _floor(d, -RX, -RZ, RX, RZ, Y0 - 1, FLOOR, 301)
    d.fill(x0, Y0 - 2, z0, x1, Y0 - 2, z1, "minecraft:dark_oak_planks")
    # 벽 (책장) + 천장 (판자 + 들보)
    _shelf_wall(d, x0, z0, x1, z0, Y0, yt - 1)
    _shelf_wall(d, x0, z1, x1, z1, Y0, yt - 1)
    _shelf_wall(d, x0, z0, x0, z1, Y0, yt - 1)
    _shelf_wall(d, x1, z0, x1, z1, Y0, yt - 1)
    d.fill(x0, yt, z0, x1, yt, z1, "minecraft:dark_oak_planks")
    for z in range(-RZ, RZ + 1, 5):
        d.fill(-RX, yt - 1, z, RX, yt - 1, z, "minecraft:stripped_dark_oak_log[axis=x]")
    # 북쪽: 넓은 낮은 단 (원화 아래쪽) → 통로 계단 → 어두운 층계참 (막다른 곳)
    d.fill(-RX, Y0, -RZ, RX, Y0, -RZ + 2, "minecraft:dark_oak_planks")
    d.fill(-RX, Y0, -RZ + 3, RX, Y0, -RZ + 3, "minecraft:dark_oak_stairs[facing=north]")
    # 벽 기둥 (5칸마다)
    for z in range(-RZ + 1, RZ, 5):
        _pillar(d, -RX, z, Y0, yt - 2, (1, 0))
        _pillar(d, RX, z, Y0, yt - 2, (-1, 0))
    for x in (-RX + 1, RX - 1):
        _pillar(d, x, -RZ, Y0 + 1, yt - 2, (0, 1), lamp=False)
    for x in (-RX + 1, -5, 5, RX - 1):
        _pillar(d, x, RZ, Y0, yt - 2, (0, -1))
    n = 7
    for k in range(n):
        z = -RZ - 1 - k
        y = Y0 + 1 + k
        d.fill(-3, Y0, z, 3, y + 6, z, "minecraft:bookshelf")                  # 통로 벽·천장 덩어리
        d.fill(-2, Y0, z, 2, y - 1, z, "minecraft:dark_oak_planks")
        d.fill(-2, y, z, 2, y, z, "minecraft:dark_oak_stairs[facing=north]")
        d.fill(-2, y + 1, z, 2, y + 5, z, "minecraft:air")
    zl = -RZ - 1 - n
    d.fill(-3, Y0, zl - 3, 3, Y0 + n + 7, zl, "minecraft:bookshelf")
    d.fill(-2, Y0 + n, zl - 2, 2, Y0 + n, zl, "minecraft:dark_oak_planks")      # 층계참
    d.fill(-2, Y0 + n + 1, zl - 2, 2, Y0 + n + 5, zl, "minecraft:air")
    d.set(0, Y0 + n + 5, zl - 1, "minecraft:lantern[hanging=true]")
    d.set(0, Y0 + n + 6, zl - 1, "minecraft:dark_oak_planks")
    # 기둥 위 종 모양 등 (원화: 계단 입구 양옆 굵은 기둥) — 아치 양옆
    for x in (-4, 4):
        d.fill(x, Y0 + 1, -RZ, x, Y0 + 1, -RZ, PLINTH)
        d.fill(x, Y0 + 2, -RZ, x, yt - 2, -RZ, PILLAR)
        d.set(x, Y0 + 5, -RZ + 1, "minecraft:dark_oak_fence")
        d.set(x, Y0 + 4, -RZ + 1, "minecraft:lantern[hanging=true]")
    # 홀 가운데: 세워진 등 기둥 (받침 + 기둥 + 랜턴) 2줄 (3D 영상 02~05)
    for x in (-5, 5):
        for z in (-7, 3):
            d.set(x, Y0, z, PLINTH)
            d.fill(x, Y0 + 1, z, x, Y0 + 3, z, PILLAR)
            d.set(x, Y0 + 4, z, "minecraft:lantern[hanging=false]")
    # 책상 (3D 영상: 등과 책이 놓인 넓은 책상) + 의자
    d.fill(-2, Y0, -5, 2, Y0, -4, "minecraft:dark_oak_slab[type=top]")
    d.set(-2, Y0 + 1, -5, "minecraft:lantern[hanging=false]")
    d.set(1, Y0 + 1, -5, "minecraft:white_candle[candles=3,lit=true]")
    d.set(2, Y0 + 1, -4, "minecraft:brown_carpet")
    d.set(0, Y0, -6, "minecraft:dark_oak_stairs[facing=north]")
    # 남쪽 출구 (검은 문)
    d.fill(-1, Y0, RZ + 1, 1, Y0 + 3, RZ + 1, "minecraft:air")
    d.fill(-1, Y0 - 1, RZ + 1, 1, Y0 - 1, RZ + 1, "minecraft:dark_oak_planks")   # 문턱 (빠지지 않게)
    d.fill(-1, Y0, RZ + 2, 1, Y0 + 3, RZ + 2, "minecraft:black_concrete")
    d.fill(-2, Y0 + 4, RZ + 1, 2, Y0 + 4, RZ + 1, PLINTH)


# ---------------------------------------------------------------- 홀 (전환 후)
HR = 22            # 책장 벽 반지름
HW = 12            # 책장 벽 높이
STAIR_W = 5        # 흰 계단 반폭 (폭 11)
STAIR_Z0 = -15     # 흰 계단 시작 (책상 뒤로 바닥을 두고)
STAIR_N = 30       # 단 수 (한 단 높이 1, 깊이 2)
CAB = "minecraft:mangrove_planks"     # 붉은 아래 장
HFLOOR = ["minecraft:spruce_planks", "minecraft:stripped_spruce_wood", "minecraft:oak_planks",
          "minecraft:spruce_planks", "minecraft:jungle_planks"]
WHITE = "minecraft:smooth_quartz"


def _stair_center(k):
    """k번째 단의 가운데 x (12단 이후 동쪽으로 휨 — 원화·3D 영상의 휘어 오르는 계단)."""
    return 0.0 if k < 12 else 0.045 * (k - 12) ** 2


def _in_stairs(x, z, margin=0):
    k = (STAIR_Z0 - z) / 2
    if k < -margin / 2 or k > STAIR_N + 4:
        return False
    return abs(x - _stair_center(max(k, 0))) <= STAIR_W + margin


def build_hall(d, ox=HALL_DX, seed=401):
    rng = np.random.default_rng(seed)
    # 바닥 (책장 탑 아래까지)
    _floor(d, ox - 64, -64, ox + 64, 64, Y0 - 1, HFLOOR, seed)
    # 둥근 책장 벽 (20각형): 붉은 장 2 + 책장, 4칸마다 세로 기둥, 위 판자. 계단 자리는 뚫음
    sides = 20
    for i in range(sides):
        a0, a1 = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
        n = int(HR * (a1 - a0) * 1.3) + 2
        for t in np.linspace(0, 1, n * 2):
            a = a0 + (a1 - a0) * t
            x, z = int(round(HR * math.cos(a))), int(round(HR * math.sin(a)))
            if z < 0 and _in_stairs(x, z, margin=2):
                continue
            for rr in (HR, HR + 1):   # 두 겹 (대각선 틈 없게)
                xx, zz = int(round(rr * math.cos(a))), int(round(rr * math.sin(a)))
                d.fill(ox + xx, Y0, zz, ox + xx, Y0 + 1, zz, CAB)
                d.fill(ox + xx, Y0 + 2, zz, ox + xx, Y0 + HW - 2, zz, "minecraft:bookshelf")
                d.set(ox + xx, Y0 + HW - 1, zz, "minecraft:spruce_planks")
        # 이음 기둥
        x, z = int(round(HR * math.cos(a0))), int(round(HR * math.sin(a0)))
        if not (z < 0 and _in_stairs(x, z, margin=2)):
            d.fill(ox + x, Y0, z, ox + x, Y0 + HW, z, "minecraft:spruce_log[axis=y]")
    # 사다리 (벽 안쪽에 기대어, 3D 영상 08~10): 안쪽 칸이 비고 벽이 단단한 곳
    for i in range(0, sides, 3):
        a = 2 * math.pi * (i + 0.5) / sides
        x, z = int(round((HR - 1) * math.cos(a))), int(round((HR - 1) * math.sin(a)))
        if z < 0 and _in_stairs(x, z, margin=3):
            continue
        dx, dz = -math.cos(a), -math.sin(a)
        face = ("east" if dx > 0 else "west") if abs(dx) > abs(dz) else ("south" if dz > 0 else "north")
        fx, fz = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}[face]
        if d.get(ox + x - fx, Y0 + 3, z - fz) == "minecraft:bookshelf":
            d.fill(ox + x, Y0, z, ox + x, Y0 + HW - 2, z, f"minecraft:ladder[facing={face}]")
    _towers(d, ox, rng)
    _white_stairs(d, ox)
    _desk(d, ox)
    _clutter(d, ox, rng)
    # 밝기: 보이지 않는 빛 블록 (하늘이 열려 있어 낮처럼 밝지만 벽 아래까지 고르게)
    for x in range(-18, 19, 6):
        for z in range(-18, 19, 6):
            if x * x + z * z < 19 ** 2 and d.get(ox + x, Y0 + 9, z) == "minecraft:air":
                d.set(ox + x, Y0 + 9, z, "minecraft:light[level=15]")
    d.set_biome(ox - 80, -96, ox + 80, 80, "ruina:lobby_hall")


def _towers(d, ox, rng):
    """벽 너머로 솟은 책장 덩어리들 (원화 뒤쪽 '책장 도시', 3D 영상 13~16). 겉면만, 바깥으로 갈수록 높게."""
    placed = 0
    for _ in range(400):
        if placed >= 70:
            break
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(HR + 4, 60)
        cx, cz = r * math.cos(a), r * math.sin(a)
        if _in_stairs(cx, cz, margin=4):   # 계단 양옆에 바짝 (원화)
            continue
        tang = abs(math.sin(a)) > abs(math.cos(a))   # 벽과 나란하게
        w, l = int(rng.integers(6, 13)), int(rng.integers(3, 7))
        if not tang:
            w, l = l, w
        x0, z0 = int(cx - w / 2), int(cz - l / 2)
        h = int((14 + (r - HR) * 1.1) * rng.uniform(0.7, 1.4))
        y0 = Y0 + int(rng.integers(-2, 4))
        x1, z1, y1 = x0 + w - 1, z0 + l - 1, y0 + h
        d.fill(ox + x0, y0, z0, ox + x1, y1, z1, "minecraft:bookshelf")
        if w > 2 and l > 2:
            d.fill(ox + x0 + 1, y0, z0 + 1, ox + x1 - 1, y1 - 1, z1 - 1, "minecraft:air")
        for y in range(y0 + 4, y1, 5):   # 선반 판
            d.fill(ox + x0, y, z0, ox + x1, y, z1, "minecraft:spruce_planks")
            if w > 2 and l > 2:
                d.fill(ox + x0 + 1, y, z0 + 1, ox + x1 - 1, y, z1 - 1, "minecraft:air")
        for xx, zz in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
            d.fill(ox + xx, y0, zz, ox + xx, y1, zz, "minecraft:spruce_log[axis=y]")
        d.fill(ox + x0, y1, z0, ox + x1, y1, z1, "minecraft:spruce_slab[type=bottom]")
        placed += 1


def _white_stairs(d, ox):
    """흰 대계단: 책상 뒤에서 북쪽으로 오르며 동쪽으로 휨. 한 단 높이 1·깊이 2, 양옆은 바닥까지 흰 벽 + 난간 턱
    (계단 아래 속은 비움 — 옆벽에 가려 안 보임).
    꼭대기는 빛나는 출구 (원화의 계단 위 빛)."""
    for k in range(STAIR_N):
        y = Y0 + k
        cx = _stair_center(k)
        for zz in (STAIR_Z0 - 2 * k, STAIR_Z0 - 2 * k - 1):
            xa, xb = int(round(cx - STAIR_W)), int(round(cx + STAIR_W))
            st = "minecraft:smooth_quartz_stairs[facing=north]" if zz == STAIR_Z0 - 2 * k else WHITE
            d.fill(ox + xa, y, zz, ox + xb, y, zz, st)
            d.fill(ox + xa - 1, Y0, zz, ox + xa - 1, y + 1, zz, WHITE)       # 난간 턱
            d.fill(ox + xb + 1, Y0, zz, ox + xb + 1, y + 1, zz, WHITE)
            d.fill(ox + xa, y + 1, zz, ox + xb, y + 8, zz, "minecraft:air")   # 머리 위 비움
    # 꼭대기: 빛 (막힌 흰 벽 + 발광)
    k = STAIR_N
    cx = _stair_center(k)
    zt = STAIR_Z0 - 2 * k
    xa, xb = int(round(cx - STAIR_W)), int(round(cx + STAIR_W))
    d.fill(ox + xa, Y0 + k - 1, zt - 6, ox + xb, Y0 + k - 1, zt, WHITE)
    d.fill(ox + xa - 1, Y0, zt - 6, ox + xa - 1, Y0 + k + 1, zt, WHITE)
    d.fill(ox + xb + 1, Y0, zt - 6, ox + xb + 1, Y0 + k + 1, zt, WHITE)
    d.fill(ox + xa, Y0 + k, zt - 6, ox + xb, Y0 + k + 14, zt - 6, "minecraft:pearlescent_froglight")
    d.fill(ox + xa + 2, Y0 + k + 1, zt - 6, ox + xb - 2, Y0 + k + 12, zt - 6, "minecraft:sea_lantern")


def _desk(d, ox):
    """앤젤라의 책상 (원화 가운데, 3D 영상 17~18): 돌 단(높이 1, 앞 계단) 위에 폭 5 책상.
    앞면 = 톱니 장치(구리 격자), 윗면 = 회색 돌판. 뒤에 의자."""
    d.fill(ox - 6, Y0, -9, ox + 6, Y0, -3, "minecraft:polished_tuff")
    d.fill(ox - 6, Y0, -2, ox + 6, Y0, -2, "minecraft:polished_tuff_stairs[facing=north]")
    d.fill(ox - 7, Y0, -9, ox - 7, Y0, -3, "minecraft:polished_tuff_stairs[facing=east]")
    d.fill(ox + 7, Y0, -9, ox + 7, Y0, -3, "minecraft:polished_tuff_stairs[facing=west]")
    d.fill(ox - 2, Y0 + 1, -6, ox + 2, Y0 + 1, -6, "minecraft:waxed_copper_grate")
    d.set(ox - 2, Y0 + 1, -6, "minecraft:waxed_exposed_copper_grate")
    d.set(ox + 2, Y0 + 1, -6, "minecraft:waxed_exposed_copper_grate")
    d.fill(ox - 2, Y0 + 1, -7, ox + 2, Y0 + 1, -7, "minecraft:polished_andesite")
    d.fill(ox - 2, Y0 + 2, -7, ox + 2, Y0 + 2, -6, "minecraft:smooth_stone_slab[type=bottom]")
    d.set(ox - 2, Y0 + 2, -7, "minecraft:lantern[hanging=false]")
    d.set(ox, Y0 + 1, -8, "minecraft:dark_oak_stairs[facing=north]")   # 의자 (남쪽을 봄)


def _clutter(d, ox, rng):
    """바닥: 책 더미 탑, 흩어진 책·종이, 작은 탁자 (3D 영상 08~12)."""
    books = ["minecraft:red_terracotta", "minecraft:brown_terracotta", "minecraft:white_terracotta",
             "minecraft:terracotta", "minecraft:light_gray_terracotta"]
    loose = ["minecraft:red_carpet", "minecraft:brown_carpet", "minecraft:white_carpet", "minecraft:white_carpet"]
    for _ in range(60):
        x, z = int(rng.integers(-19, 20)), int(rng.integers(-19, 20))
        if x * x + z * z > 19 ** 2 or _in_stairs(x, z, margin=2) or (-8 <= x <= 8 and -10 <= z <= -1):
            continue
        if abs(x) <= 2 and z > 0:   # 도착 자리 앞 통로
            continue
        if d.get(ox + x, Y0, z) != "minecraft:air":
            continue
        if rng.random() < 0.35:     # 책 탑
            for y in range(int(rng.integers(1, 5))):
                d.set(ox + x, Y0 + y, z, books[int(rng.integers(len(books)))])
        else:                       # 흩어진 책·종이
            for _ in range(int(rng.integers(3, 8))):
                xx, zz = x + int(rng.integers(-2, 3)), z + int(rng.integers(-2, 3))
                if d.get(ox + xx, Y0, zz) == "minecraft:air" and d.get(ox + xx, Y0 - 1, zz) != "minecraft:air":
                    d.set(ox + xx, Y0, zz, loose[int(rng.integers(len(loose)))])
    for x, z in ((-12, 4), (11, -2), (-13, -8), (13, 9)):   # 작은 탁자
        if d.get(ox + x, Y0, z) == "minecraft:air":
            d.set(ox + x, Y0, z, "minecraft:spruce_fence")
            d.set(ox + x, Y0 + 1, z, "minecraft:spruce_slab[type=bottom]")
            d.set(ox + x + 1, Y0, z, "minecraft:spruce_fence")
            d.set(ox + x + 1, Y0 + 1, z, "minecraft:spruce_slab[type=bottom]")


# ---------------------------------------------------------------- 조립 + TP·전환

def stair_top():
    """흰 대계단 꼭대기 (빛 앞 층계참): (가운데 x, 서 있는 y, 층계참 z 범위)."""
    k = STAIR_N
    zt = STAIR_Z0 - 2 * k
    return HALL_DX + _stair_center(k), Y0 + k, (zt - 5, zt)


def build(b):
    from . import fragment as F
    d = b.dim("lobby")
    build_room(d)
    build_hall(d)
    L = b.links
    # 방전환 우클릭: 번쩍 → 방 ↔ 홀 (같은 상대 위치, 막혀 있으면 기본 자리). 홀 = 지정사서 방 자리.
    # 흰 대계단 꼭대기 빛은 조형물로만 남김
    F.stage(b, d, "silver", "로비", (0.5, Y0, RZ - 2.5, 180), (HALL_DX + 0.5, Y0, RZ - 2.5, 180),
            room_box=f"x={HALL_DX // 2},y=-64,z=-1024,dx=4096,dy=1024,dz=2048",
            to_a=F.relative(-HALL_DX, "lobby_entrance"), to_b=F.relative(HALL_DX, "lobby_hall"),
            scene_name="lobby_entrance", room_name="lobby_hall")
    L.portal(d.dim, 0.5, Y0, RZ + 1.5, "exterior_gate", width=3, height=4)
    L.walk(d.dim, (-1, Y0, RZ + 1, 1, Y0 + 2, RZ + 1), "exterior_gate", fade=True)
    # 서버 검증: 홀 바이옴, 방 → 홀 → 방 전환 (마커로)
    ax, az = 0.5, RZ - 2.5
    b.extra_checks += [
        {"what": "홀 바이옴 ruina:lobby_hall", "cmd": f"execute in {d.dim} if biome {HALL_DX} {Y0} 0 ruina:lobby_hall",
         "expect": True},
        {"what": "방 바이옴 ruina:lobby", "cmd": f"execute in {d.dim} if biome 0 {Y0} 0 ruina:lobby", "expect": True},
    ]
