"""기술과학의 층 (예소드). 접대 공간(고가도로) ↔ 지정사서 방 (철괴 F).

참고: reference/기술과학의 층 전경.png, reference/기술과학의 층 지정사서 방.png, PLAN.md 8절 나무위키 요약
("밤의 대규모 현대 도시, 가장 높은 건물과 거대 톱니가 연결, 톱니가 돌면 층 전체 건물이 움직임" — 톱니는 이번엔 고정).

원화(전경): 높은 고가도로(아스팔트 4차선, 점선, 철 난간), 녹슨 리벳 철 주탑 + 늘어진 쇠사슬,
다리 아래 철 트러스 받침과 네온 도시·무지개빛 길, 배경 네온 빌딩 숲 속 녹슨 거대 톱니들,
가운데 가장 높은 건물 꼭대기(꼬인 조형물)에서 톱니로 뻗은 케이블, 보라 구름 하늘·초승달.

크기 (처음 정한 2048×512, 사람 기준 1블록 ≈ 1m): 3겹
 ① 고가도로 (x -340..340, 폭 21, 서 있는 높이 Y 250), 주탑 160칸마다 높이 120
 ② 300 안쪽 네온 도시(바닥 Y 40, 높이 40~200), 톱니 6개, 가장 높은 건물(꼭대기 Y 400)
 ③ 420~900 성긴 먼 도시 (Distant Horizons/높은 렌더 거리)
"""
from __future__ import annotations

import math

import numpy as np

from tools import shapes as S

from .city import build_city

Y0 = 250                 # 다리 위 서 있는 높이
GROUND = 40              # 도시 바닥 (윗면)
BX = 340                 # 다리 반길이
HW = 10                  # 다리 반폭 (z -10..10, 4차선 + 갓길)
PYLONS = (-240, -80, 80, 240)
PYLON_H = 120
ARRIVE_X = -250
ROOM_X = 4000            # 예소드 방 (같은 차원, 멀리)
RY = 64                  # 방 바닥 높이

RUST = ["minecraft:waxed_exposed_copper", "minecraft:terracotta", "minecraft:waxed_exposed_cut_copper",
        "minecraft:brown_terracotta", "minecraft:waxed_exposed_copper"]   # 녹슨 철 (초록 녹은 안 씀)
STEEL = "minecraft:polished_deepslate"
NEONS = ["minecraft:pearlescent_froglight", "minecraft:sea_lantern", "minecraft:crying_obsidian",
         "minecraft:verdant_froglight", "minecraft:ochre_froglight"]
NEON_PAL = {
    "walls": (["minecraft:black_concrete", "minecraft:gray_concrete", "minecraft:blue_terracotta",
               "minecraft:purple_terracotta", "minecraft:cyan_terracotta", "minecraft:polished_blackstone",
               "minecraft:magenta_terracotta"], [12, 8, 16, 18, 10, 8, 8]),
    "lit": (["minecraft:pearlescent_froglight", "minecraft:sea_lantern", "minecraft:ochre_froglight",
             "minecraft:verdant_froglight"], [40, 30, 20, 10]),
    "neon": (["minecraft:pearlescent_froglight", "minecraft:sea_lantern", "minecraft:crying_obsidian"], [5, 4, 3]),
    "trim": (["minecraft:polished_blackstone_bricks", "minecraft:deepslate_tiles"], [1, 1]),
    "corner_neon": 0.6, "corners": 2, "roof_neon": 0.55,
}


def _line(d, p0, p1, state, step=0.5):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    n = max(2, int(np.linalg.norm(p1 - p0) / step))
    for t in np.linspace(0, 1, n):
        p = p0 + (p1 - p0) * t
        d.set(int(round(p[0])), int(round(p[1])), int(round(p[2])), state)


def _chain_line(d, p0, p1):
    """쇠사슬 (블록 방향은 가장 긴 축)."""
    v = np.asarray(p1, float) - np.asarray(p0, float)
    axis = "xyz"[int(np.argmax(np.abs(v)))]
    _line(d, p0, p1, f"minecraft:iron_chain[axis={axis}]")


# ---------------------------------------------------------------- ① 고가도로

def bridge(d, rng):
    xs, zs = np.arange(-BX, BX + 1), np.arange(-HW, HW + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    asphalt = np.array([d.id(s) for s in ("minecraft:gray_concrete", "minecraft:black_concrete",
                                           "minecraft:smooth_basalt", "minecraft:gray_concrete")])
    ids = asphalt[(S.hash01(X, Z, seed=801) * 4).astype(int).clip(0, 3)]
    white = d.id("minecraft:white_concrete")
    for zl in (-4, 0, 4):                                  # 차선 점선 (3칸 칠, 3칸 빔)
        ids = np.where((Z == zl) & ((X % 6) < 3), white, ids)
    ids = np.where(np.abs(Z) == HW - 2, d.id("minecraft:light_gray_concrete"), ids)   # 가장자리 실선
    d.place(-BX, Y0 - 1, -HW, ids[:, None, :])
    # 바닥판 두께·옆 거더 (녹슨 철, 리벳 줄)
    rust = np.array([d.id(s) for s in RUST])
    for z in (-HW - 1, HW + 1):
        g = rust[(S.hash01(xs // 4, np.full_like(xs, z), seed=802) * len(RUST)).astype(int).clip(0, len(RUST) - 1)]
        for y in range(Y0 - 4, Y0):
            d.place(-BX, y, z, g[:, None, None].astype(np.int32))
        d.fill(-BX, Y0 - 2, z, BX, Y0 - 2, z, "minecraft:waxed_cut_copper")       # 리벳 띠
    d.fill(-BX, Y0 - 4, -HW, BX, Y0 - 4, HW, STEEL)                              # 바닥판 아래
    # 난간: 철 기둥 4칸마다 + 두 줄 가로대 (원화의 굵은 철 난간)
    for z in (-HW, HW):
        d.fill(-BX, Y0, z, BX, Y0, z, "minecraft:iron_bars")
        d.fill(-BX, Y0 + 1, z, BX, Y0 + 1, z, "minecraft:waxed_exposed_cut_copper_slab[type=bottom]")
        for x in range(-BX, BX + 1, 4):
            d.set(x, Y0, z, "minecraft:waxed_exposed_copper")
    # 다리 아래 트러스 (주탑 아래 교각 + 사이 대각 버팀, 원화 아래 모서리)
    for px in PYLONS:
        for z in (-HW, HW):
            for dx in (-3, 3):
                d.fill(px + dx, GROUND, z, px + dx, Y0 - 5, z, "minecraft:waxed_exposed_copper")
            for y in range(GROUND + 6, Y0 - 5, 12):
                _line(d, (px - 3, y, z), (px + 3, y + 12, z), STEEL)
                _line(d, (px + 3, y, z), (px - 3, y + 12, z), STEEL)
        for side in (-1, 1):   # 바닥판으로 퍼지는 큰 대각 받침
            for z in (-HW, HW):
                _line(d, (px + 3 * side, Y0 - 50, z), (px + 30 * side, Y0 - 5, z), "minecraft:waxed_exposed_copper")
                _line(d, (px + 3 * side, Y0 - 30, z), (px + 18 * side, Y0 - 5, z), STEEL)
        d.fill(px - 30, Y0 - 5, -HW, px + 30, Y0 - 5, -HW, STEEL)
        d.fill(px - 30, Y0 - 5, HW, px + 30, Y0 - 5, HW, STEEL)


def pylons_and_chains(d, rng):
    """주탑 (녹슨 리벳 철, 다리 양옆 두 다리 + 위 가로보) + 쇠사슬: 주탑 꼭대기 사이 처진 주케이블, 다리로 내려오는 사선."""
    rust = [d.id(s) for s in RUST]
    tops = []
    for px in PYLONS:
        for z in (-HW - 3, HW + 3):
            for x in range(px - 2, px + 3):
                for zz in range(z - 2, z + 3):
                    if abs(x - px) == 2 or abs(zz - z) == 2:
                        col = np.array([rust[int(S.hash01(np.array(x), np.array(y // 6), np.array(zz), seed=811) * len(rust)) % len(rust)]
                                        for y in range(Y0 - 4, Y0 + PYLON_H)], np.int32)
                        d.place(x, Y0 - 4, zz, col[None, :, None])
            for y in range(Y0 + 4, Y0 + PYLON_H, 8):    # 리벳 띠
                d.fill(px - 2, y, z - 2, px + 2, y, z + 2, "minecraft:waxed_cut_copper")
                d.fill(px - 1, y, z - 1, px + 1, y, z + 1, "minecraft:air")
            # 아래 교각으로 이어짐
            d.fill(px - 2, GROUND, z, px + 2, Y0 - 5, z, "minecraft:waxed_exposed_copper")
            tops.append((px, Y0 + PYLON_H, z))
        d.fill(px - 2, Y0 + PYLON_H - 6, -HW - 3, px + 2, Y0 + PYLON_H - 2, HW + 3, "minecraft:waxed_exposed_copper")
        d.fill(px - 2, Y0 + 40, -HW - 3, px + 2, Y0 + 42, HW + 3, "minecraft:waxed_exposed_copper")
    for z in (-HW - 3, HW + 3):
        # 처진 주케이블 (주탑 사이 + 양 끝)
        xs = [-BX] + list(PYLONS) + [BX]
        for a, b in zip(xs, xs[1:]):
            ya = Y0 + (PYLON_H if a in PYLONS else 8)
            yb = Y0 + (PYLON_H if b in PYLONS else 8)
            pts = []
            for t in np.linspace(0, 1, 120):
                x = a + (b - a) * t
                y = ya + (yb - ya) * t - 70 * 4 * t * (1 - t) * (1 if (a in PYLONS and b in PYLONS) else 0.4)
                pts.append((x, max(y, Y0 + 4), z))
            for p, q in zip(pts, pts[1:]):
                _chain_line(d, p, q)
        # 원화의 늘어진 사선 쇠사슬 (주탑 꼭대기 → 다리 반대편 가장자리)
        for px in PYLONS:
            for dx in (-36, 36):
                _chain_line(d, (px, Y0 + PYLON_H - 8, z), (px + dx, Y0 + 2, -z))


# ---------------------------------------------------------------- ② 도시·톱니·탑

def city(d, rng):
    d.fill(-420, GROUND - 1, -420, 420, GROUND - 1, 420, "minecraft:black_concrete")
    # 다리 바로 아래는 비움 (교각 자리) — 원화처럼 다리 아래로 도시가 보이되 다리와 겹치지 않게
    skip = lambda x, z: abs(z) < HW + 16 and abs(x) <= BX + 10   # noqa: E731
    # 원화: 다리 위에서 봐도 뒤 빌딩 숲이 다리(Y 250)보다 높이 솟음 → 꼭대기 Y 190~370
    near = build_city(d, 40, 360, seed=821, ground_y=GROUND, h_min=150, h_max=290, skip=skip, spacing0=24,
                      size=(12, 26), palette=NEON_PAL)
    far = build_city(d, 430, 900, seed=822, ground_y=GROUND, h_min=130, h_max=290, spacing0=120, size=(16, 34),
                     palette=dict(NEON_PAL, corner_neon=0.4, roof_neon=0.3))
    # 무지개빛 길 (원화 다리 아래): 휘어 가는 빛 띠, 색이 바뀜
    cols = ["minecraft:ochre_froglight", "minecraft:pearlescent_froglight", "minecraft:crying_obsidian",
            "minecraft:sea_lantern", "minecraft:verdant_froglight"]
    for k in range(2):
        pts = [(-360 + 720 * t, GROUND - 1, 60 * math.sin(t * 5 + k * 2) + (-40 if k else 50)) for t in np.linspace(0, 1, 400)]
        for i, (x, y, z) in enumerate(pts):
            c = cols[(i // 40) % len(cols)]
            d.fill(int(x), y, int(z) - 1, int(x), y, int(z) + 1, c)
    return {"near": near, "far": far}


def gear(d, cx, cy, cz, R, teeth=None, thick=4, holes=6, seed=0, mats=None):
    """세로로 선 녹슨 톱니 (남쪽을 봄): 테 + 이 + 바퀴살 구멍. 앞·뒷면과 테두리만."""
    teeth = teeth or max(10, int(R / 3))
    rng = np.random.default_rng(seed)
    n = int(R + 6)
    xs, ys = np.arange(-n, n + 1), np.arange(-n, n + 1)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    r = np.hypot(X, Y)
    a = np.arctan2(Y, X)
    tooth = ((a / (2 * np.pi) * teeth) % 1.0) < 0.45
    outer = np.where(tooth, R + 4, R)
    body = r <= outer
    hub = r <= R * 0.22
    ring = (r >= R * 0.72) | hub
    spoke = np.zeros_like(body)
    for k in range(holes):
        ang = 2 * np.pi * k / holes
        dist = np.abs(-np.sin(ang) * X + np.cos(ang) * Y)
        spoke |= (dist < R * 0.09) & (np.cos(ang) * X + np.sin(ang) * Y > 0)
    solid = body & (ring | spoke)
    rust = np.array([d.id(s) for s in (mats or RUST)])
    ids = rust[(S.hash01(X // 3, Y // 3, seed=830 + seed) * len(rust)).astype(int).clip(0, len(rust) - 1)]
    ids = np.where(solid, ids, -1).astype(np.int32)
    edge = solid & ~(np.roll(solid, 1, 0) & np.roll(solid, -1, 0) & np.roll(solid, 1, 1) & np.roll(solid, -1, 1))
    for dz in range(thick):
        layer = ids if dz in (0, thick - 1) else np.where(edge, ids, -1)
        d.place(cx - n, cy - n, cz + dz, layer[:, :, None])


def gears_and_tower(d, rng):
    """가장 높은 건물 (꼭대기 꼬인 조형물) + 톱니 6개 + 꼭대기에서 톱니 가운데로 뻗은 케이블."""
    tx, tz = 20, -330
    top = 460
    d.fill(tx - 14, GROUND, tz - 14, tx + 14, top - 40, tz + 14, "minecraft:black_concrete")
    d.fill(tx - 13, GROUND, tz - 13, tx + 13, top - 41, tz + 13, "minecraft:air")
    for y in range(GROUND + 4, top - 40, 4):     # 층마다 네온 띠
        d.fill(tx - 14, y, tz + 14, tx + 14, y, tz + 14, "minecraft:pearlescent_froglight" if y % 8 else "minecraft:sea_lantern")
    for y in range(top - 40, top + 30):           # 꼬인 조형물 (원화 꼭대기)
        t = (y - (top - 40)) / 70
        r = 10 * (1 - t) + 2
        a = t * 5.0
        for k in range(3):
            ang = a + k * 2 * math.pi / 3
            x, z = tx + r * math.cos(ang), tz + r * math.sin(ang)
            d.fill(int(x) - 1, y, int(z) - 1, int(x) + 1, y, int(z) + 1, "minecraft:waxed_exposed_copper")
    apex = (tx, top + 28, tz)
    specs = [(-230, 310, -300, 70), (230, 330, -320, 60), (-120, 250, -260, 45), (150, 260, -230, 50),
             (-330, 240, -120, 40), (320, 260, -60, 38)]   # 원화: 톱니가 빌딩 숲 위로 솟음
    for i, (gx, gy, gz, R) in enumerate(specs):
        gear(d, gx, gy, gz, R, seed=i)
        _chain_line(d, apex, (gx, gy, gz))       # 케이블
        d.fill(gx - 3, GROUND, gz + 1, gx + 3, gy - R + 2, gz + 3, STEEL)   # 받침 기둥


# ---------------------------------------------------------------- 예소드 방
RW, RD, RH = 12, 10, 14


def yesod_room(d, ox=ROOM_X):
    """원화: 어두운 사무실, 빛줄 있는 서랍장, 천장에 매달린 톱니 샹들리에(보라 발광 테두리),
    가운데 콘솔 책상(화면), 뒤 빛나는 유리문(초승달), 파일 상자, 어두운 타일 바닥."""
    y0, yt = RY, RY + RH
    xs, zs = np.arange(ox - RW, ox + RW + 1), np.arange(-RD, RD + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    tile = np.where(((X // 3) + (Z // 3)) % 2 == 0, d.id("minecraft:polished_deepslate"),
                    d.id("minecraft:deepslate_tiles"))
    tile = np.where((X % 3 == 0) | (Z % 3 == 0), d.id("minecraft:polished_blackstone"), tile)
    d.place(ox - RW, y0 - 1, -RD, tile[:, None, :])
    x0, x1, z0, z1 = ox - RW - 1, ox + RW + 1, -RD - 1, RD + 1
    for (a0, b0, a1, b1) in ((x0, z0, x1, z0), (x0, z1, x1, z1), (x0, z0, x0, z1), (x1, z0, x1, z1)):
        d.fill(a0, y0, b0, a1, yt, b1, "minecraft:black_concrete")
    for x in range(x0, x1 + 1, 4):                              # 벽 패널 이음
        d.fill(x, y0, z0, x, yt, z0, "minecraft:polished_blackstone")
    d.fill(x0, yt, z0, x1, yt, z1, "minecraft:black_concrete")
    d.fill(x0, yt - 3, z0 + 1, x1, yt - 3, z0 + 1, "minecraft:polished_blackstone")   # 위 가로 들보

    def cabinet(xa, xb, za, face):
        """서랍장: 서랍(검은 블록) 칸 + 칸마다 아래 빛줄(가로 끝막대)."""
        for y in range(y0, y0 + 10):
            d.fill(xa, y, za, xb, y, za, "minecraft:polished_blackstone_bricks" if (y - y0) % 2 else "minecraft:bookshelf")
        for y in range(y0 + 1, y0 + 10, 2):
            for x in range(xa, xb + 1):
                d.set(x, y, za + face, "minecraft:end_rod[facing=east]")
    cabinet(ox + 4, ox + 10, z0 + 1, 1)          # 오른쪽 큰 서랍장 (원화)
    cabinet(ox - 10, ox - 6, z0 + 1, 1)          # 왼쪽
    for z in range(-RD + 2, RD - 1, 3):          # 양옆 벽 서랍
        for y in range(y0, y0 + 12, 2):
            d.set(x0 + 1, y, z, "minecraft:polished_blackstone_bricks")
            d.set(x1 - 1, y, z, "minecraft:polished_blackstone_bricks")
            d.set(x0 + 2, y + 1, z, "minecraft:end_rod[facing=east]")
            d.set(x1 - 2, y + 1, z, "minecraft:end_rod[facing=west]")
    # 뒤 유리문 (빛나는 보라 유리 + 초승달)
    d.fill(ox + 1, y0, z0 + 1, ox + 4, y0 + 7, z0 + 1, "minecraft:pearlescent_froglight")
    d.fill(ox + 1, y0, z0 + 2, ox + 4, y0 + 7, z0 + 2, "minecraft:purple_stained_glass")
    d.fill(ox, y0, z0 + 2, ox, y0 + 8, z0 + 2, "minecraft:polished_blackstone")
    d.fill(ox + 5, y0, z0 + 2, ox + 5, y0 + 8, z0 + 2, "minecraft:polished_blackstone")
    for x, y in ((ox + 3, y0 + 5), (ox + 3, y0 + 6), (ox + 2, y0 + 6)):
        d.set(x, y, z0 + 1, "minecraft:sea_lantern")
    # 콘솔 책상 (두 칸) + 화면
    d.fill(ox - 4, y0, -RD + 6, ox + 3, y0, -RD + 7, "minecraft:polished_blackstone")
    d.fill(ox - 4, y0 + 1, -RD + 6, ox + 3, y0 + 1, -RD + 7, "minecraft:polished_blackstone_slab[type=bottom]")
    d.fill(ox - 4, y0, -RD + 8, ox + 3, y0, -RD + 8, "minecraft:crying_obsidian")       # 앞 빛 테두리
    d.set(ox - 2, y0 + 1, -RD + 6, "minecraft:light_blue_stained_glass")             # 화면
    d.set(ox - 3, y0 + 1, -RD + 6, "minecraft:light_blue_stained_glass")
    # 파일 상자 (왼쪽 아래, 오른쪽 아래)
    for x, z, h in ((ox - 10, -2, 2), (ox - 9, -2, 1), (ox - 10, -1, 1), (ox + 9, 2, 2), (ox + 10, 2, 1)):
        d.fill(x, y0, z, x, y0 + h - 1, z, "minecraft:light_gray_concrete")
    # 톱니 샹들리에: 세로 톱니 + 기울어진 고리 + 작은 톱니, 천장에서 줄로 매달림, 보라 발광 테두리
    cx, cy, cz = ox - 2, yt - 6, -2
    dark = ["minecraft:polished_blackstone", "minecraft:blackstone"]
    gear(d, cx, cy, cz, 5, teeth=10, thick=1, holes=4, seed=9, mats=dark)
    for a in np.linspace(0, 2 * math.pi, 120):              # 기울어진 고리
        for rr in (6.5, 7.0):
            x, z = cx + rr * math.cos(a), cz + rr * math.sin(a)
            y = cy - 3 + 2.5 * math.sin(a)
            d.set(int(round(x)), int(round(y)), int(round(z)), "minecraft:crying_obsidian")
    gear(d, cx + 3, cy - 7, cz, 3, teeth=8, thick=1, holes=3, seed=10, mats=dark)
    for dx in (-3, 0, 3):
        _chain_line(d, (cx + dx, yt - 1, cz), (cx + dx, cy + 4, cz))
    for a in np.linspace(0, 2 * math.pi, 80):               # 발광 테두리
        d.set(int(round(cx + 6 * math.cos(a))), int(round(cy + 6 * math.sin(a))), cz - 1, "minecraft:crying_obsidian")
    d.set_biome(ox - 40, -40, ox + 40, 40, "ruina:technology_room")


# ---------------------------------------------------------------- 조립

def build(b):
    from . import fragment as F
    d = b.dim("technology")
    rng = np.random.default_rng(901)
    bridge(d, rng)
    pylons_and_chains(d, rng)
    stats = city(d, rng)
    gears_and_tower(d, rng)
    yesod_room(d)

    L = b.links
    arrive = F.exchange(F.IRON_P, F.IRON)
    L.anchor("technology_entrance", d.dim, ARRIVE_X + 0.5, Y0, 0.5, yaw=-90, title="기술과학의 층", on_arrive=arrive)
    L.anchor("technology_room", d.dim, ROOM_X + 0.5, RY, RD - 2.5, yaw=180, on_arrive=arrive)
    # 돌아가는 길: 다리 서쪽 끝 (안개 속) → 역사의 층 말쿠트 방 금빛 틈 앞
    L.walk(d.dim, (-BX + 6, Y0, -HW + 1, -BX + 9, Y0 + 3, HW - 1), "history_gap", fade=True)
    # 예소드 방 빛나는 유리문에 다가가면 → 문학의 층. 돌아오면 유리문 앞에서 방 쪽(남쪽)을 봄
    z0 = -RD - 1
    L.walk(d.dim, (ROOM_X + 1, RY, z0 + 3, ROOM_X + 4, RY + 2, z0 + 3), "literature_entrance", fade=True)
    L.anchor("technology_door", d.dim, ROOM_X + 2.5, RY, z0 + 6.5, yaw=0, title="기술과학의 층", on_arrive=arrive)
    F.setup(L, "iron", d.dim, F.IRON_P, f"x={ROOM_X - 200},y=-64,z=-1024,dx=400,dy=1024,dz=2048",
            to_a=F.fixed("technology_entrance"), to_b=F.fixed("technology_room"))
    b.extra_checks += [
        {"what": "예소드 방 바이옴", "cmd": f"execute in {d.dim} if biome {ROOM_X} {RY} 0 ruina:technology_room",
         "expect": True},
        {"what": "철괴 전환 다리→방",
         "setup": [f"execute in {d.dim} run summon minecraft:marker {ARRIVE_X + 0.5} {Y0} 0.5 {{Tags:[\"ruina.isw\"]}}",
                   f"execute in {d.dim} as @e[type=minecraft:marker,tag=ruina.isw] at @s run function ruina:iron/switch"],
         "cmd": f"execute in {d.dim} positioned {ROOM_X + 0.5} {RY} {RD - 2.5} if entity @e[type=minecraft:marker,tag=ruina.isw,distance=..0.5]",
         "expect": True},
        {"what": "철괴 전환 방→다리",
         "setup": [f"execute in {d.dim} as @e[type=minecraft:marker,tag=ruina.isw] at @s run function ruina:iron/switch"],
         "cmd": f"execute in {d.dim} positioned {ARRIVE_X + 0.5} {Y0} 0.5 if entity @e[type=minecraft:marker,tag=ruina.isw,distance=..0.5]",
         "expect": True},
    ]
    return stats
