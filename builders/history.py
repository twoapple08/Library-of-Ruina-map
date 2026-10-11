"""역사의 층 (말쿠트). 접대 공간 ↔ 지정사서 방 (금조각 F).

참고: reference/역사의 층 전경.png (접대 공간을 살짝 위에서 내려다본 구도),
reference/역사의 층 지정사서 방.png, PLAN.md 8절 나무위키 요약
("유리 케이스 속 책 전시, 복도 아래 책장 가득, 멀리 거대 책장, 엘리베이터 양면 거울처럼 바닥이 여러 겹 반복").

크기 (사람 기준 1블록 ≈ 1m, 구역 1536): 3겹
 ① 접대 무대 (중심 0~130): 동서로 긴 길 여러 줄. 난간 간격 8, 진열장 간격 5 (원화 원근에서 진열장 ≈ 사람 키로 환산)
 ② 가까운 배경 (130~370): 아래로 반복되는 바닥 4겹(24칸 간격) + 그 사이 책장 절벽, 거대 책장 기둥, 거대 유물 3개
 ③ 먼 배경 (370~760): 구역 끝을 두르는 더 큰 책장 벽 (Distant Horizons 나 렌더 거리 48청크 이상에서 보임)
보이는 면만 짓는다 (속 빈 상자, 아래 겹은 위 겹에 가려지지 않는 테두리만).
"""
from __future__ import annotations

import math

import numpy as np

from tools import shapes as S

Y0 = 64
# ① 접대 무대
HX = 250                 # 길 길이 반 (x -250..250)
HZ = 124                 # 무대 깊이 반 (z -124..124)
RAIL_DZ = 8              # 난간 간격
CASE_DX = 5              # 진열장 간격
LAYER_DY = 24            # 아래 반복 바닥 간격
LAYERS = 4
LAYER_GROW = 16          # 아래 겹일수록 바깥으로 넓어짐 (위에서 보면 계단처럼 겹겹이)
ARRIVE_Z = 100           # 도착 (남쪽에서 북쪽을 봄 — 원화 구도)
ROOM_X = 4000            # 말쿠트 방 (같은 차원, 멀리)

FLOOR_A = "minecraft:stripped_spruce_log[axis=%s]"
FLOOR_B = "minecraft:stripped_jungle_log[axis=%s]"
RAIL = "minecraft:smooth_basalt"
RAIL_TOP = "minecraft:heavy_weighted_pressure_plate"
RAIL_GLOW = "minecraft:ochre_froglight"
CASE_BASE = "minecraft:polished_blackstone"
CASE_GLASS = "minecraft:glass"


def herringbone(d, x0, z0, x1, z1, y, seed=501):
    """헤링본 나무 바닥 (원화): 2칸짜리 판자가 대각선 띠마다 방향을 바꿈, 판자마다 색 조금씩."""
    xs, zs = np.arange(x0, x1 + 1), np.arange(z0, z1 + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    ax_x = ((X - Z) % 4) < 2
    brick = np.where(ax_x, (X + Z) // 2, (X - Z) // 2)
    tone = S.hash01(brick, np.where(ax_x, Z, X) // 2, seed=seed) < 0.38
    ids = {}
    for t, base in ((False, FLOOR_A), (True, FLOOR_B)):
        for a in (True, False):
            ids[(t, a)] = d.id(base % ("x" if a else "z"))
    out = np.empty(X.shape, np.int32)
    for (t, a), i in ids.items():
        out[(tone == t) & (ax_x == a)] = i
    d.place(x0, y, z0, out[:, None, :])


def rails_and_cases(d, x0, x1, z0, z1, y, rng, entities=None, near=None):
    """난간 줄 (z 방향 RAIL_DZ 간격): 검은 몸통 + 금속 윗면 + 앞(남쪽) 바닥 빛줄, 진열장은 앞뒤로 엇갈려 5칸마다.
    entities: 진열장 안 책(item_display) 소환 명령을 모을 목록 (near(x,z)가 참인 곳만 — 엔티티 수 최소화)."""
    for zr in range(z0 + RAIL_DZ // 2, z1, RAIL_DZ):
        d.fill(x0, y, zr, x1, y, zr, RAIL)
        d.fill(x0, y + 1, zr, x1, y + 1, zr, RAIL_TOP)
        d.fill(x0, y - 1, zr + 1, x1, y - 1, zr + 1, RAIL_GLOW)
        off = int(rng.integers(0, CASE_DX))
        for i, x in enumerate(range(x0 + off, x1 + 1, CASE_DX)):
            z = zr + (1 if i % 2 == 0 else -1)
            d.set(x, y, z, CASE_BASE)
            d.set(x, y + 1, z, CASE_GLASS)
            if entities is not None and near(x, z):
                entities.append((x + 0.5, y + 1.5, z + 0.5))


def stage(d, rng, entities):
    """① 접대 무대 + ② 아래로 반복되는 바닥(겹마다 바깥 테두리만) + 그 사이 책장 절벽."""
    herringbone(d, -HX, -HZ, HX, HZ, Y0 - 1)
    rails_and_cases(d, -HX, HX, -HZ, HZ, Y0, rng, entities, near=lambda x, z: abs(x) <= 40 and abs(z - 40) <= 70)
    # 아래 겹: 위 겹 가장자리보다 LAYER_GROW 넓음 → 보이는 테두리(+4)만 짓기
    for k in range(1, LAYERS + 1):
        y = Y0 - 1 - LAYER_DY * k
        hx, hz = HX + LAYER_GROW * k, HZ + LAYER_GROW * k
        ix, iz = HX + LAYER_GROW * (k - 1) - 4, HZ + LAYER_GROW * (k - 1) - 4
        for (a0, b0, a1, b1) in ((-hx, -hz, hx, -iz), (-hx, iz, hx, hz), (-hx, -iz, -ix, iz), (ix, -iz, hx, iz)):
            herringbone(d, a0, b0, a1, b1, y, seed=501 + k)
        # 난간·진열장: 테두리 띠 안에만 (북·남 띠는 동서로 길게, 동·서 띠는 짧은 조각)
        rails_and_cases(d, -hx, hx, -hz, -iz, y + 1, rng)
        rails_and_cases(d, -hx, hx, iz, hz, y + 1, rng)
        for xa, xb in ((-hx, -ix), (ix, hx)):
            rails_and_cases(d, xa, xb, -iz, iz, y + 1, rng)
        # 위 겹 가장자리 아래 = 책장 절벽 (복도 아래 책장 가득): 위 겹 바닥 아래 ~ 이 겹 바닥 위
        yt = Y0 - 2 - LAYER_DY * (k - 1)
        px, pz = HX + LAYER_GROW * (k - 1), HZ + LAYER_GROW * (k - 1)
        for (a0, b0, a1, b1) in ((-px, -pz, px, -pz), (-px, pz, px, pz), (-px, -pz, -px, pz), (px, -pz, px, pz)):
            d.fill(a0, y + 1, b0, a1, yt, b1, "minecraft:bookshelf")
            for yy in range(y + 4, yt, 4):
                d.fill(a0, yy, b0, a1, yy, b1, "minecraft:spruce_planks")
            d.fill(a0, yt, b0, a1, yt, b1, "minecraft:dark_oak_planks")
    # 맨 아래 겹 가장자리 아래도 책장 절벽 (안개 속으로 사라짐)
    k = LAYERS
    px, pz = HX + LAYER_GROW * k, HZ + LAYER_GROW * k
    yb = Y0 - 1 - LAYER_DY * k
    for (a0, b0, a1, b1) in ((-px, -pz, px, -pz), (-px, pz, px, pz), (-px, -pz, -px, pz), (px, -pz, px, pz)):
        d.fill(a0, d.min_y + 2, b0, a1, yb - 1, b1, "minecraft:bookshelf")


def exit_stairs(d):
    """도착 자리 뒤(남쪽) 내려가는 계단 → 빛 (로비로 돌아가는 길). 원화 밖이라 장식 없이 최소한."""
    z0 = ARRIVE_Z + 6
    for k in range(6):
        z = z0 + k
        d.fill(-3, Y0 - 1 - k, z, 3, Y0 - 1 - k, z, "minecraft:spruce_stairs[facing=south]")
        d.fill(-3, Y0 - k, z, 3, Y0 + 3, z, "minecraft:air")
        d.fill(-4, Y0 - 1 - k, z, -4, Y0 + 1, z, RAIL)
        d.fill(4, Y0 - 1 - k, z, 4, Y0 + 1, z, RAIL)
    zl = z0 + 6
    d.fill(-3, Y0 - 7, zl, 3, Y0 - 7, zl + 3, "minecraft:stripped_spruce_wood")
    d.fill(-3, Y0 - 6, zl + 3, 3, Y0 - 1, zl + 3, "minecraft:pearlescent_froglight")   # 빛
    d.fill(-4, Y0 - 7, zl, -4, Y0 - 1, zl + 3, RAIL)
    d.fill(4, Y0 - 7, zl, 4, Y0 - 1, zl + 3, RAIL)
    return (-3, Y0 - 6, zl, 3, Y0 - 3, zl + 2)


# ---------------------------------------------------------------- ② 배경

def _hollow_box(d, x0, y0, z0, x1, y1, z1, face, frame="minecraft:spruce_log[axis=y]", board="minecraft:spruce_planks",
                top="minecraft:spruce_slab[type=bottom]", board_dy=6):
    """겉면만 있는 책장 덩어리: 네 면 face, 모서리 기둥 frame, board_dy 마다 선반 판, 윗면."""
    for (a0, b0, a1, b1) in ((x0, z0, x1, z0), (x0, z1, x1, z1), (x0, z0, x0, z1), (x1, z0, x1, z1)):
        d.fill(a0, y0, b0, a1, y1, b1, face)
        for yy in range(y0 + board_dy, y1, board_dy):
            d.fill(a0, yy, b0, a1, yy, b1, board)
    for xx, zz in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        d.fill(xx, y0, zz, xx, y1, zz, frame)
    d.fill(x0, y1, z0, x1, y1, z1, top)


def towers(d, rng):
    """원화 뒤쪽: 하늘을 덮는 거대 책장 기둥 줄 (사이로 빛), 밑동은 안개 속 빛."""
    x = -460
    while x < 460:
        w = int(rng.integers(26, 46))
        dz = int(rng.integers(18, 30))
        z1 = int(rng.integers(-370, -330))
        h = int(rng.integers(150, 250))
        _hollow_box(d, x, Y0 - 110, z1 - dz, x + w, Y0 + h, z1, "minecraft:bookshelf")   # 밑동은 안개 속
        d.fill(x, Y0 - 30, z1, x + w, Y0 - 26, z1, "minecraft:shroomlight")   # 밑동 빛 (안개 속)
        x += w + int(rng.integers(8, 20))
    # 양옆에도 몇 개 (무대 끝이 안개 속 책장으로)
    for side in (-1, 1):
        for z in range(-280, 200, 90):
            w, dz, h = int(rng.integers(20, 34)), int(rng.integers(20, 34)), int(rng.integers(120, 220))
            x0 = side * int(rng.integers(330, 370))
            _hollow_box(d, min(x0, x0 + side * w), Y0 - 110, z, max(x0, x0 + side * w), Y0 + h, z + dz,
                        "minecraft:bookshelf")


def cabinet(d, rng, cx=-235, cz=-270):
    """왼쪽 유물: 판자를 덧댄 거대한 나무 장, 남쪽 면에 불 켜진 창 + 작은 불꽃 셋."""
    w, dz, y0, y1 = 70, 44, d.min_y + 4, Y0 + 175
    x0, x1, z0, z1 = cx - w // 2, cx + w // 2, cz - dz // 2, cz + dz // 2
    planks = ["minecraft:spruce_planks", "minecraft:dark_oak_planks", "minecraft:stripped_spruce_wood",
              "minecraft:spruce_planks", "minecraft:oak_planks", "minecraft:stripped_dark_oak_wood"]
    pid = np.array([d.id(p) for p in planks])

    def face(a0, a1, along_x, fixed):
        A, Y = np.meshgrid(np.arange(a0, a1 + 1), np.arange(y0, y1 + 1), indexing="ij")
        patch = S.hash01(A // 7, Y // 11, seed=611 + fixed)        # 덧댄 판자 조각
        ids = pid[(patch * len(pid)).astype(int).clip(0, len(pid) - 1)]
        seam = (A % 7 == 0) | (Y % 11 == 0)
        ids = np.where(seam, d.id("minecraft:dark_oak_log[axis=y]"), ids)
        if along_x:
            d.place(a0, y0, fixed, ids[:, :, None])
        else:
            d.place(fixed, y0, a0, ids.T[None, :, :])   # ids [Z, Y] → [1, Y, Z]
    face(x0, x1, True, z1)
    face(x0, x1, True, z0)
    face(z0, z1, False, x0)
    face(z0, z1, False, x1)
    d.fill(x0, y1, z0, x1, y1, z1, "minecraft:dark_oak_planks")
    # 불 켜진 창 (남쪽 면): 테두리 + 불빛
    wx0, wx1, wy0, wy1 = cx - 4, cx + 26, Y0 + 70, Y0 + 125
    d.fill(wx0 - 2, wy0 - 2, z1, wx1 + 2, wy1 + 2, z1, "minecraft:stripped_dark_oak_wood")
    d.fill(wx0, wy0, z1, wx1, wy1, z1, "minecraft:ochre_froglight")
    for i in range(40):  # 불꽃 무늬 (가운데 밝게)
        x = int(rng.integers(wx0 + 4, wx1 - 4))
        y = int(rng.integers(wy0 + 4, wy1 - 8))
        d.set(x, y, z1, "minecraft:pearlescent_froglight")
    d.fill(cx + 8, wy0 + 6, z1, cx + 14, wy1 - 10, z1, "minecraft:pearlescent_froglight")
    for i, x in enumerate((cx - 22, cx - 16, cx - 10)):  # 작은 불꽃 셋
        d.fill(x, wy1 - 6 - i, z1, x + 1, wy1 - 2 - i, z1, "minecraft:shroomlight")


def stone_pillar(d, rng, cx=25, cz=-300):
    """가운데 유물: 기울어진 꼭대기의 돌기둥, 옆에 거대 톱니, 비스듬히 감긴 쇠사슬."""
    r, y0, y1 = 24, d.min_y + 4, Y0 + 205
    stones = ["minecraft:smooth_sandstone", "minecraft:cut_sandstone", "minecraft:sandstone", "minecraft:terracotta",
              "minecraft:smooth_sandstone"]
    sid = np.array([d.id(s) for s in stones])
    seam = d.id("minecraft:brown_terracotta")
    for y in range(y0, y1 + 1):
        top_cut = y1 - 0.45 * np.arange(-r, r + 1)            # 꼭대기는 동쪽으로 기울어짐
        xs = np.arange(cx - r, cx + r + 1)
        for zz in (cz - r, cz + r):
            ids = sid[(S.hash01(xs // 4, np.full_like(xs, y // 3), np.full_like(xs, zz), seed=621) * len(sid)).astype(int)]
            ids = np.where(((xs + (y // 3) * 2) % 4 == 0) | (y % 3 == 0), seam, ids)
            ids = np.where(y <= top_cut, ids, -1)
            d.place(cx - r, y, zz, ids[:, None, None].astype(np.int32))
        zs = np.arange(cz - r, cz + r + 1)
        for xx in (cx - r, cx + r):
            ids = sid[(S.hash01(np.full_like(zs, xx), np.full_like(zs, y // 3), zs // 4, seed=622) * len(sid)).astype(int)]
            ids = np.where(((zs + (y // 3) * 2) % 4 == 0) | (y % 3 == 0), seam, ids)
            ids = np.where(y <= y1 - 0.45 * (xx - cx), ids, -1)
            d.place(xx, y, cz - r, ids[None, None, :].astype(np.int32))
    for x in range(cx - r, cx + r + 1):   # 기울어진 뚜껑
        yt = int(y1 - 0.45 * (x - cx))
        d.fill(x, yt, cz - r, x, yt, cz + r, "minecraft:smooth_sandstone")
    # 톱니 (남쪽을 보는 면, 서쪽 위)
    gx, gy, gz, R = cx - r + 4, Y0 + 160, cz + r + 2, 20
    for a in np.linspace(0, 2 * math.pi, 400):
        for rr in np.arange(R - 4, R + 0.5, 0.7):
            d.set(int(round(gx + rr * math.cos(a))), int(round(gy + rr * math.sin(a))), gz, "minecraft:cut_copper")
    for t in range(14):
        a = t * 2 * math.pi / 14
        for rr in range(R, R + 5):
            for w in (-1, 0, 1):
                x = int(round(gx + rr * math.cos(a) - w * math.sin(a)))
                y = int(round(gy + rr * math.sin(a) + w * math.cos(a)))
                d.set(x, y, gz, "minecraft:cut_copper")
    d.fill(gx - 3, gy - 3, gz, gx + 3, gy + 3, gz, "minecraft:exposed_cut_copper")
    # 쇠사슬 두 줄: 기둥을 비스듬히 감는 고리들 (고리 = 납작한 테, 번갈아 방향)
    for c, (ystart, turn) in enumerate(((Y0 + 175, -1), (Y0 + 120, 1))):
        n = 70
        for i in range(n):
            t = i / n
            a = turn * (0.4 + 2.2 * t * math.pi)
            px = cx + (r + 3) * math.cos(a)
            pz = cz + (r + 3) * math.sin(a)
            py = ystart - 80 * t
            for b in np.linspace(0, 2 * math.pi, 18):
                ox, oy = 3.2 * math.cos(b), 2.0 * math.sin(b)
                if i % 2 == 0:
                    pos = (px + ox * -math.sin(a), py + oy, pz + ox * math.cos(a))
                else:
                    pos = (px + oy * math.cos(a), py + ox, pz + oy * math.sin(a))
                d.set(int(round(pos[0])), int(round(pos[1])), int(round(pos[2])), "minecraft:polished_deepslate")


def moss_monolith(d, rng, cx=265, cz=-255):
    """오른쪽 유물: 이끼 덮인 둥근 초록 돌덩이, 표면에 작은 불빛(창 같은 점)."""
    rx, rz, y0, y1 = 46, 30, d.min_y + 4, Y0 + 195
    mats = ["minecraft:moss_block", "minecraft:green_terracotta", "minecraft:mossy_cobblestone",
            "minecraft:moss_block", "minecraft:mossy_stone_bricks", "minecraft:lime_terracotta"]
    mid = np.array([d.id(m) for m in mats])
    R = rx + 4
    xs, zs = np.arange(cx - R, cx + R + 1), np.arange(cz - R, cz + R + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    ang = np.arctan2((Z - cz) / rz, (X - cx) / rx)
    for y in range(y0, y1 + 1):
        t = (y - y0) / (y1 - y0)
        s = 1.0 - 0.25 * max(0.0, t - 0.75) / 0.25 * 1.0 + 0.06 * math.sin(y / 17)
        n = 0.08 * S.hash01((ang * 6).astype(int), np.full_like(X, y // 9), seed=631)
        e = np.hypot((X - cx) / (rx * s), (Z - cz) / (rz * s)) - n
        shell = (e <= 1.0) & (e > 1.0 - 1.6 / min(rx, rz))
        if y == y1:
            shell = e <= 1.0
        h = S.hash01(X // 3, np.full_like(X, y // 3), Z // 3, seed=632)
        ids = mid[(h * len(mid)).astype(int).clip(0, len(mid) - 1)]
        ids = np.where(S.hash01(X, np.full_like(X, y), Z, seed=633) < 0.006, d.id("minecraft:verdant_froglight"), ids)
        d.place(cx - R, y, cz - R, np.where(shell, ids, -1)[:, None, :].astype(np.int32))


def far_ring(d, rng):
    """③ 먼 배경: 구역 끝(반지름 600~740)을 두르는 더 큰 책장 벽."""
    n = 26
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.05, 0.05)
        r = rng.uniform(600, 720)
        cx, cz = r * math.cos(a), r * math.sin(a)
        w, dz = int(rng.integers(50, 90)), int(rng.integers(20, 34))
        if abs(math.cos(a)) < abs(math.sin(a)):
            x0, z0, x1, z1 = int(cx - w / 2), int(cz - dz / 2), int(cx + w / 2), int(cz + dz / 2)
        else:
            x0, z0, x1, z1 = int(cx - dz / 2), int(cz - w / 2), int(cx + dz / 2), int(cz + w / 2)
        _hollow_box(d, x0, Y0 - 120, z0, x1, Y0 + int(rng.integers(250, 350)), z1, "minecraft:bookshelf",
                    board_dy=8)


# ---------------------------------------------------------------- 지정사서 방 (말쿠트)
RW, RD, RH = 14, 11, 15   # 반폭, 반깊이, 천장


def malkuth_room(d, ox=ROOM_X):
    """원화: 천장까지 닿는 책장 칸(사이 기둥에 가는 금빛 빛줄), 아래 칸엔 책 더미, 큰 책상 + 높은 등받이 의자 둘,
    펼친 책·책 더미, 오른쪽 책장 틈으로 쏟아지는 금빛 (그 안 헤링본 바닥과 책장), 오른쪽 앞 짙은 기둥."""
    herringbone(d, ox - RW, -RD, ox + RW, RD, Y0 - 1, seed=541)
    x0, x1, z0, z1, yt = ox - RW - 1, ox + RW + 1, -RD - 1, RD + 1, Y0 + RH
    d.fill(x0, yt, z0, x1, yt, z1, "minecraft:dark_oak_planks")
    for z in range(-RD, RD + 1, 4):
        d.fill(x0, yt - 1, z, x1, yt - 1, z, "minecraft:dark_oak_log[axis=x]")

    def bay_wall(a0, a1, fixed, along_x, opening=None):
        for a in range(a0, a1 + 1):
            pos = (a, fixed) if along_x else (fixed, a)
            k = (a - a0) % 6
            if opening and opening[0] <= a <= opening[1]:
                continue
            if k == 0:   # 기둥 + 빛줄
                d.fill(pos[0], Y0, pos[1], pos[0], yt - 1, pos[1], "minecraft:dark_oak_log[axis=y]")
            else:
                d.fill(pos[0], Y0, pos[1], pos[0], yt - 1, pos[1], "minecraft:bookshelf")
                for yy in range(Y0 + 3, yt - 1, 3):
                    d.set(pos[0], yy, pos[1], "minecraft:dark_oak_planks")
                d.set(pos[0], Y0, pos[1], "minecraft:dark_oak_planks")
        # 기둥 앞 가는 금빛 줄 (원화의 칸 사이 빛)
        for a in range(a0, a1 + 1, 6):
            if opening and opening[0] - 1 <= a <= opening[1] + 1:
                continue
            p = (a, fixed + (1 if fixed < 0 else -1)) if along_x else (fixed + (1 if fixed < ox else -1), a)
            d.fill(p[0], Y0 + 1, p[1], p[0], yt - 3, p[1], "minecraft:end_rod[facing=up]")

    bay_wall(x0, x1, z0, True)                                   # 북쪽 (원화 정면)
    bay_wall(z0, z1, x0, False)                                  # 서쪽
    bay_wall(z0, z1, x1, False, opening=(-6, 0))                 # 동쪽: 금빛 틈
    bay_wall(x0, x1, z1, True)                                   # 남쪽
    # 금빛 틈 너머: 헤링본 바닥 + 양옆 책장 + 빛나는 안쪽 벽 (원화 오른쪽)
    herringbone(d, x1, -6, x1 + 8, 0, Y0 - 1, seed=542)
    d.fill(x1, Y0, -7, x1 + 9, yt - 1, -7, "minecraft:bookshelf")
    d.fill(x1, Y0, 1, x1 + 9, yt - 1, 1, "minecraft:bookshelf")
    d.fill(x1 + 9, Y0, -6, x1 + 9, yt - 1, 0, "minecraft:ochre_froglight")
    d.fill(x1, yt, -7, x1 + 9, yt, 1, "minecraft:dark_oak_planks")
    for z in (-5, -1):
        d.fill(x1 + 1, Y0, z, x1 + 2, Y0 + int(2 + abs(z) % 3), z, "minecraft:brown_terracotta")  # 빛 속 책 더미
    # 오른쪽 앞 짙은 기둥
    d.fill(ox + 11, Y0, 6, ox + 12, yt - 1, 7, "minecraft:dark_oak_log[axis=y]")
    # 책상 (가운데 남쪽, 북쪽 책장을 향함) + 높은 등받이 의자 둘 (책상 너머에서 이쪽을 봄)
    d.fill(ox - 6, Y0, 2, ox + 5, Y0, 4, "minecraft:dark_oak_slab[type=top]")
    d.set(ox - 3, Y0 + 1, 3, "minecraft:white_carpet")       # 펼친 책
    d.set(ox - 2, Y0 + 1, 3, "minecraft:white_carpet")
    for x, h in ((ox + 1, 2), (ox + 2, 1), (ox + 4, 1), (ox - 5, 1)):   # 책 더미
        d.fill(x, Y0 + 1, 3, x, Y0 + h, 3, "minecraft:brown_terracotta" if h > 1 else "minecraft:red_terracotta")
    d.set(ox + 3, Y0 + 1, 2, "minecraft:black_candle[candles=1,lit=false]")   # 잉크병 대신
    for x in (ox - 3, ox + 2):
        d.set(x, Y0, 0, "minecraft:dark_oak_stairs[facing=north]")
        d.set(x, Y0 + 1, -1, "minecraft:dark_oak_trapdoor[facing=south,half=bottom,open=true]")
        d.set(x, Y0 + 2, -1, "minecraft:dark_oak_trapdoor[facing=south,half=bottom,open=true]")
    # 바닥 책 더미 (원화 오른쪽·책장 아래)
    rng = np.random.default_rng(551)
    for _ in range(26):
        x, z = ox + int(rng.integers(-RW + 1, RW)), int(rng.integers(-RD + 1, RD))
        if -1 <= z <= 5 and -7 <= x - ox <= 6:
            continue
        if d.get(x, Y0, z) != "minecraft:air":
            continue
        for y in range(int(rng.integers(1, 4))):
            d.set(x, Y0 + y, z, ["minecraft:brown_terracotta", "minecraft:red_terracotta",
                                 "minecraft:terracotta"][int(rng.integers(3))])
    # 은은한 빛 (보이지 않는 빛 블록)
    for x in range(-RW + 3, RW, 6):
        for z in range(-RD + 3, RD, 6):
            if d.get(ox + x, yt - 2, z) == "minecraft:air":
                d.set(ox + x, yt - 2, z, "minecraft:light[level=11]")
    d.set_biome(ox - 40, -40, ox + 40, 40, "ruina:history_room")


# ---------------------------------------------------------------- 조립

def build(b):
    from . import fragment as F
    d = b.dim("history")
    rng = np.random.default_rng(701)
    books = []
    stage(d, rng, books)
    zone = exit_stairs(d)
    towers(d, rng)
    cabinet(d, rng)
    stone_pillar(d, rng)
    moss_monolith(d, rng)
    far_ring(d, rng)
    malkuth_room(d)

    L = b.links
    arrive = F.exchange(F.GOLD_P, F.GOLD)
    L.anchor("history_entrance", d.dim, 0.5, Y0, ARRIVE_Z + 0.5, yaw=180, title="역사의 층", on_arrive=arrive)
    L.anchor("history_room", d.dim, ROOM_X + 0.5, Y0, RD - 2.5, yaw=180, on_arrive=arrive)
    L.walk(d.dim, zone, "lobby_stairs", fade=True)
    # 말쿠트 방 오른쪽 금빛 틈 안쪽으로 걸어 들어가면 → 기술과학의 층. 돌아오면 틈 앞(방 안)에서 서쪽을 봄
    gx = ROOM_X + RW + 1
    L.walk(d.dim, (gx + 5, Y0, -6, gx + 8, Y0 + 3, 0), "technology_entrance", fade=True)
    L.anchor("history_gap", d.dim, gx - 3 + 0.5, Y0, -2.5, yaw=90, title="역사의 층", on_arrive=arrive)
    # 금조각 F: 접대 공간 ↔ 말쿠트 방 (고정 자리)
    F.setup(L, "gold", d.dim, F.GOLD_P, f"x={ROOM_X - 200},y=-64,z=-1024,dx=400,dy=1024,dz=2048",
            to_a=F.fixed("history_entrance"), to_b=F.fixed("history_room"))
    # 진열장 속 책 (도착 자리 둘레만 — 엔티티 최소화)
    for x, y, z in books:
        b.forceload.append((d.dim, x, z))
        L.entity_cmds.append(
            f"execute in {d.dim} run summon minecraft:item_display {x} {y} {z} "
            '{item:{id:"minecraft:book",count:1},item_display:"fixed",Tags:["ruina.case"],'
            "brightness:{sky:15,block:12},transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],"
            "translation:[0f,0f,0f],scale:[0.6f,0.6f,0.6f]}}")
    b.extra_checks += [
        {"what": "말쿠트 방 바이옴", "cmd": f"execute in {d.dim} if biome {ROOM_X} {Y0} 0 ruina:history_room",
         "expect": True},
        {"what": "진열장 책 (item_display)", "cmd": f"execute in {d.dim} if entity @e[type=minecraft:item_display,tag=ruina.case]",
         "expect": True, "after_entities": True},
        {"what": "금조각 전환 접대→방",
         "setup": [f"execute in {d.dim} run summon minecraft:marker 0.5 {Y0} {ARRIVE_Z + 0.5} {{Tags:[\"ruina.gsw\"]}}",
                   f"execute in {d.dim} as @e[type=minecraft:marker,tag=ruina.gsw] at @s run function ruina:gold/switch"],
         "cmd": f"execute in {d.dim} positioned {ROOM_X + 0.5} {Y0} {RD - 2.5} if entity @e[type=minecraft:marker,tag=ruina.gsw,distance=..0.5]",
         "expect": True},
        {"what": "금조각 전환 방→접대",
         "setup": [f"execute in {d.dim} as @e[type=minecraft:marker,tag=ruina.gsw] at @s run function ruina:gold/switch"],
         "cmd": f"execute in {d.dim} positioned 0.5 {Y0} {ARRIVE_Z + 0.5} if entity @e[type=minecraft:marker,tag=ruina.gsw,distance=..0.5]",
         "expect": True},
    ]
