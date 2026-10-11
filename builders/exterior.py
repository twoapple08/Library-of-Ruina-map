"""외부 건물 (시제품 v0) — design/exterior.md 수치를 도형 엔진으로.

아직 실제 월드 빌드(build_all)에는 넣지 않고 미리보기로만 확인한다 (Phase 1에서 확정).
좌표: 탑 중심 (0, 0), 광장 윗면 Y=0 (서 있는 높이), 정문은 남쪽(+Z).
"""
from __future__ import annotations

import math

import numpy as np

import config
from tools import shapes as S

K = config.EXTERIOR_SCALE / 3.0  # 설계 수치는 ×3 기준

# ---------------------------------------------------------------- 수치 (design/exterior.md 2절)
PLINTH_H = 30 * K           # 기단 높이
TIER_H = 27.3 * K           # 단 높이 (11단)
TIERS = 11
TOP = PLINTH_H + TIER_H * TIERS   # ≈ 330
R_PLINTH = 38 * K
R_BOTTOM = 36 * K
R_TOP = 27 * K
GATE_W, GATE_H, GATE_FLOOR = 15, 24, 6   # 정문 (K와 무관하게 사람 기준)
PLAZA_R = 110 * K

WOOD = ("minecraft:dark_oak_stairs", "minecraft:dark_oak_slab")
SOUTH = math.pi / 2  # atan2(z, x): +Z 방향


def body_radius(y):
    """기본 반지름(판자 들쑥날쑥 빼고)."""
    y = np.asarray(y, float)
    r = np.where(y < PLINTH_H, R_PLINTH + 3 * K * np.clip(1 - y / (10 * K), 0, 1) ** 2,
                 R_BOTTOM + (R_TOP - R_BOTTOM) * (y - PLINTH_H) / (TOP - PLINTH_H))
    t = np.clip((y - PLINTH_H) / TIER_H, 0, None)
    bulge = np.where(y >= PLINTH_H, 1.0 * K * np.sin(np.pi * (t % 1.0)), 0)
    return r + bulge


def tier_of(y):
    return np.where(y < PLINTH_H, -1, np.floor((y - PLINTH_H) / TIER_H)).astype(int)


def _strip(theta, y):
    """세로 판자 띠 번호 (폭 3칸). 단마다 띠 개수가 달라 어긋나 보임."""
    tier = tier_of(y)
    r = body_radius(y)
    n = np.maximum(12, np.round(2 * np.pi * r / 3)).astype(int)
    idx = np.floor((theta + np.pi) / (2 * np.pi) * n).astype(int)
    return tier, idx


def radius_with_planks(y, theta):
    tier, idx = _strip(theta, y)
    h = S.hash01(tier, idx, seed=11)
    off = np.where(h < 0.18, -0.9, np.where(h > 0.85, 0.6, 0.0)) * K
    # 단마다 세로로 덧댄 판자 조각이 위아래로 어긋나게
    h2 = S.hash01(tier, idx, np.floor(y / (9 * K)).astype(int), seed=12)
    off = off + np.where(h2 > 0.9, 0.5, 0.0)
    return body_radius(y) + off


# ---------------------------------------------------------------- 창문

def _windows(seed=5):
    """단마다 창 목록: (단, 중심각, 중심 y, 호 길이 폭, 높이, 종류)."""
    rng = np.random.default_rng(seed)
    out = []
    for t in range(TIERS):
        y0 = PLINTH_H + t * TIER_H
        n = rng.integers(25, 41)
        for _ in range(n):
            th = rng.uniform(-np.pi, np.pi)
            if abs(((th - SOUTH + np.pi) % (2 * np.pi)) - np.pi) < 0.12 and t == 0:
                continue
            yc = y0 + rng.uniform(5, TIER_H - 6) * 1.0
            group = rng.choice([1, 1, 2, 2, 3])
            for g in range(group):
                out.append((t, th + g * 3.2 / body_radius(yc), yc, 2, 3, "small"))
        for _ in range(rng.integers(1, 3)):
            th = rng.uniform(-np.pi, np.pi)
            yc = y0 + rng.uniform(8, TIER_H - 8)
            for row in range(rng.integers(2, 4)):
                out.append((t, th, yc + row * 2, 12, 1, "slit"))
    # 기단: 정문 양옆 아래 작은 창 2개씩
    for side in (-1, 1):
        for k in range(2):
            x = side * (GATE_W / 2 + 3 + k * 3)
            th = math.atan2(R_PLINTH, x)
            out.append((-1, th, GATE_FLOOR + 3.5, 2, 2, "small"))
    return out


WINDOWS = _windows()
WINDOWS_BY_TIER = {}
for _w in WINDOWS:
    WINDOWS_BY_TIER.setdefault(_w[0], []).append(_w)


def tower_paint(ctx):
    th, y = ctx.info["theta"], ctx.info["y"]
    tier, idx = _strip(th, y)
    h = S.hash01(tier, idx, seed=21)
    states = np.where(h < 0.45, "minecraft:dark_oak_log[axis=y]",
                      np.where(h < 0.8, "minecraft:stripped_dark_oak_log[axis=y]", "minecraft:dark_oak_planks"))
    states = states.astype(object)
    # 판자 띠 경계에 가끔 어두운 틈
    seam = S.hash01(tier, idx, seed=22) < 0.25
    states[seam & (S.hash01(ctx.x, ctx.y, ctx.z, seed=23) < 0.3)] = "minecraft:polished_blackstone"
    # 창문 (바깥 면만)
    outer = ctx.d > -1.0
    if outer.any():
        r = body_radius(y)
        tiers = set(np.unique(tier_of(y[outer])).tolist())
        tiers |= {t + 1 for t in tiers} | {t - 1 for t in tiers}
        cand = [w for t in tiers for w in WINDOWS_BY_TIER.get(t, [])]
        for (t, wth, wy, ww, wh, kind) in cand:
            dth = (th - wth + np.pi) % (2 * np.pi) - np.pi
            m = outer & (np.abs(dth * r) <= ww / 2) & (y >= wy - wh / 2) & (y < wy + wh / 2)
            if m.any():
                states[m] = "minecraft:ochre_froglight" if kind == "small" else "minecraft:shroomlight"
    return states


def ledge_paint(ctx):
    return np.where(S.hash01(ctx.x, ctx.y, ctx.z, seed=31) < 0.15, "minecraft:stripped_dark_oak_log[axis=y]",
                    "minecraft:dark_oak_planks").astype(object)


def branch_paint(ring=7.0):
    log = S.log_along("minecraft:dark_oak_log[axis={a}]")
    ringlog = S.log_along("minecraft:stripped_dark_oak_log[axis={a}]")

    def f(ctx):
        s = ctx.info["s"]
        a, b = log(ctx), ringlog(ctx)
        band = (s % ring) < 1.2
        out = np.where(band, b, a).astype(object)
        return out
    return f


# ---------------------------------------------------------------- 가지·뿌리 곡선

def _branch_curve(rng, h, theta, big: bool, top: bool = False):
    out = np.array([math.cos(theta), 0, math.sin(theta)])
    up = np.array([0.0, 1.0, 0.0])
    r_here = float(body_radius(h))
    p0 = out * (r_here - 3) + up * h
    frac = (h - 60 * K) / (TOP - 60 * K)
    if top:
        reach = rng.uniform(140, 180) * K
        rise = rng.uniform(40, 90) * K
    elif big:
        reach = (60 + 100 * frac) * K * rng.uniform(0.8, 1.15)
        rise = reach * math.tan(math.radians(rng.uniform(5, 30)))
    else:
        reach = rng.uniform(30, 60) * K
        rise = reach * math.tan(math.radians(rng.uniform(0, 35)))
    side = np.cross(up, out)
    wob = side * rng.uniform(-0.25, 0.25) * reach
    p3 = p0 + out * reach + up * rise + wob
    p1 = p0 + out * reach * 0.30 + up * reach * rng.uniform(0.15, 0.4)
    p2 = p3 - out * reach * 0.35 + up * rng.uniform(-0.1, 0.25) * reach
    main = S.resample(S.bezier(p0, p1, p2, p3, 80), 1.0)
    tan = main[-1] - main[-2]
    bend = up if rng.random() < 0.6 else -up
    bend = bend + side * rng.uniform(-0.6, 0.6)
    R0 = rng.uniform(7, 14) * K if big else rng.uniform(4, 7) * K
    c = S.curl(main[-1], tan, bend, R0, turns=rng.uniform(1.4, 2.4), shrink=0.5, step=1.0, Rmin=1.4)
    pts = S.join(main, c)
    if top:
        r0, r1 = 9 * K, 3.0 * K
    elif big:
        r0, r1 = rng.uniform(5, 8) * K, 2.5 * K
    else:
        r0, r1 = rng.uniform(3, 4) * K, 1.6 * K
    nm, nc = len(main), len(c) - 1
    radii = np.concatenate([np.linspace(r0, r1, nm), np.linspace(r1, max(1.1, r1 * 0.45), nc)])
    return pts, radii


def _root_curve(rng, theta):
    out = np.array([math.cos(theta), 0, math.sin(theta)])
    up = np.array([0.0, 1.0, 0.0])
    side = np.cross(up, out)
    p0 = out * (R_PLINTH - 6) + up * 6 * K
    reach = rng.uniform(40, 90) * K
    p3 = p0 + out * reach + up * (-4 * K) + side * rng.uniform(-0.3, 0.3) * reach
    p1 = p0 + out * reach * 0.3 + up * rng.uniform(6, 14) * K
    p2 = p3 - out * reach * 0.3 + up * rng.uniform(2, 8) * K
    main = S.resample(S.bezier(p0, p1, p2, p3, 80), 1.0)
    tan = main[-1] - main[-2]
    c = S.curl(main[-1], tan, up + side * rng.uniform(-1, 1), rng.uniform(5, 9) * K, turns=1.6, shrink=0.5,
               step=1.0, Rmin=1.4)
    pts = S.join(main, c)
    r0 = rng.uniform(6, 9) * K
    radii = np.concatenate([np.linspace(r0, 2.6 * K, len(main)), np.linspace(2.6 * K, 1.2, len(c) - 1)])
    return pts, radii


# ---------------------------------------------------------------- 조립

def tower_parts(seed=7):
    parts = []
    body = S.Revolve(0, TOP, radius_with_planks, rmax=R_PLINTH + 4 * K).with_(paint=tower_paint, name="body")
    gate_cut = S.Box(-GATE_W // 2, GATE_FLOOR, int(R_PLINTH - 4), GATE_W // 2, GATE_FLOOR + GATE_H - 1,
                     int(R_PLINTH + 12))
    parts.append(S.Subtract(body, gate_cut))
    # 단 경계 턱
    for t in range(TIERS + 1):
        yb = PLINTH_H + t * TIER_H

        def rad(y, th, yb=yb):
            return body_radius(np.full_like(y, yb)) + 2.2 * K
        ledge = S.Revolve(yb - 1.0, yb + 1.2, rad, rmax=R_PLINTH + 4 * K).with_(paint=ledge_paint, smooth=WOOD)
        parts.append(S.Subtract(ledge, gate_cut) if t == 0 else ledge)
    # 정문 위 차양 (남쪽 ±25°)

    def awning(y, th):
        dth = np.abs((th - SOUTH + np.pi) % (2 * np.pi) - np.pi)
        return np.where(dth < 0.42, body_radius(np.full_like(y, PLINTH_H)) + 5 * K, 0.0)
    parts.append(S.Revolve(GATE_FLOOR + GATE_H, GATE_FLOOR + GATE_H + 3.5, awning,
                           rmax=R_PLINTH + 7 * K).with_(paint=ledge_paint, smooth=WOOD))
    # 빛나는 문 두 짝 (홈 안쪽 벽 앞)
    zb = int(R_PLINTH - 4)
    for x0, x1 in ((-GATE_W // 2, -1), (1, GATE_W // 2)):
        parts.append(S.Box(x0, GATE_FLOOR, zb, x1, GATE_FLOOR + GATE_H - 1, zb).with_(
            paint=S.mix(["minecraft:ochre_froglight", "minecraft:pearlescent_froglight"], [3, 1], seed=41)))
    rng = np.random.default_rng(seed)
    # 가지
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(24):
        h = 60 * K + (TOP - 70 * K) * (rng.random() ** 0.6)
        th = i * golden + rng.uniform(-0.2, 0.2)
        if abs(((th - SOUTH + np.pi) % (2 * np.pi)) - np.pi) < 0.35 and h < 120 * K:
            th += 0.7  # 정문 바로 위 낮은 곳은 피함
        pts, rad = _branch_curve(rng, h, th, big=True)
        parts.append(S.Tube(pts, rad).with_(paint=branch_paint(), smooth=WOOD, name=f"branch{i}"))
    for i in range(10):
        h = 80 * K + (TOP - 90 * K) * rng.random()
        th = rng.uniform(-np.pi, np.pi)
        pts, rad = _branch_curve(rng, h, th, big=False)
        parts.append(S.Tube(pts, rad).with_(paint=branch_paint(5.0), smooth=WOOD, name=f"twig{i}"))
    for i in range(7):  # 꼭대기 수관
        th = i * 2 * math.pi / 7 + rng.uniform(-0.2, 0.2)
        pts, rad = _branch_curve(rng, TOP - 8 * K, th, big=True, top=True)
        parts.append(S.Tube(pts, rad).with_(paint=branch_paint(), smooth=WOOD, name=f"crown{i}"))
    # 뿌리 (정문 앞은 비움)
    for i in range(8):
        th = SOUTH + math.pi / 8 + i * 2 * math.pi / 8 + rng.uniform(-0.15, 0.15)
        if abs(((th - SOUTH + np.pi) % (2 * np.pi)) - np.pi) < 0.45:
            continue
        pts, rad = _root_curve(rng, th)
        parts.append(S.Tube(pts, rad).with_(paint=branch_paint(), smooth=WOOD, name=f"root{i}"))
    return parts


def plaza(d):
    """원형 나무 광장 (윗면 Y=-1 한 겹, 가장자리 두께 3 테두리)."""
    R = int(PLAZA_R)
    xs, zs = np.meshgrid(np.arange(-R, R + 1), np.arange(-R, R + 1), indexing="ij")
    rr = np.hypot(xs, zs)
    disk = rr <= R
    ang = np.arctan2(zs, xs)
    sector = np.floor((ang + np.pi) / (2 * np.pi) * 96).astype(int)
    ring = np.floor(rr / 9).astype(int)
    h = S.hash01(sector, ring, seed=51)
    top = np.where(h < 0.5, d.id("minecraft:dark_oak_planks"),
                   np.where(h < 0.85, d.id("minecraft:spruce_planks"), d.id("minecraft:stripped_dark_oak_wood")))
    top = np.where(disk, top, -1)
    d.place(-R, -1, -R, top[:, None, :])
    rim = disk & (rr > R - 2)
    d.place_mask(-R, -3, -R, np.repeat(rim[:, None, :], 2, axis=1), "minecraft:polished_deepslate")


def stairs(d):
    """정문 앞 사다리꼴 계단 6단 (Y 5 → 0), 앞줄은 계단 블록."""
    z0 = int(R_PLINTH - 4)
    d.fill(-GATE_W // 2 - 2, 0, z0 - 2, GATE_W // 2 + 2, GATE_FLOOR - 1, z0 + 3, "minecraft:dark_oak_planks")
    zc = z0 + 4
    for k in range(6):
        top = GATE_FLOOR - 1 - k
        hw = 10 + 3 * k
        za, zb = zc + 3 * k, zc + 3 * k + 2
        if top >= 0:
            d.fill(-hw, 0, za, hw, top - 1, zb, "minecraft:dark_oak_planks") if top > 0 else None
            d.fill(-hw, top, za, hw, top, zb - 1, "minecraft:dark_oak_planks")
            d.fill(-hw, top, zb, hw, top, zb, "minecraft:dark_oak_stairs[facing=north,half=bottom]")


# ---------------------------------------------------------------- 황금 종이 물결

PAPER = ("minecraft:smooth_sandstone_stairs", "minecraft:smooth_sandstone_slab")
PAPER_MIX = (["minecraft:smooth_sandstone", "minecraft:birch_planks", "minecraft:sandstone",
              "minecraft:honeycomb_block", "minecraft:ochre_froglight", "minecraft:glowstone",
              "minecraft:gold_block", "minecraft:end_stone_bricks"],
             [30, 14, 8, 8, 14, 6, 4, 6])


def _stream_path(side: int):
    """종이 물결 중심선 (xz). 정문 옆 기단에서 출발해 계단 옆을 지나 앞·바깥으로 휘며 퍼짐."""
    pts = np.array([[13, 37], [19, 47], [27, 60], [36, 72], [50, 84], [66, 92], [80, 96]], float) * K
    pts[:, 0] *= side
    return S.resample(np.c_[pts[:, 0], np.zeros(len(pts)), pts[:, 1]], 2.0)[:, [0, 2]]


def _stream_height(side: int, seed: int):
    path = _stream_path(side)

    def h(X, Z):
        dist, s, L = S.polyline_2d(path, X, Z)
        u = s / L
        half = (6 + 14 * u ** 0.8) * K                  # 반폭 6 → 20
        top = (4.2 - 2.4 * u) * K                         # 높이 4.2 → 1.8
        P = np.stack([X, np.zeros_like(X), Z], 1)
        edge = half * (1 + 0.35 * S.fbm(P, 9.0 * K, 3, seed))   # 들쭉날쭉한 가장자리
        v = np.clip(dist / np.maximum(edge, 1e-6), 0, None)
        prof = np.where(v < 1, np.clip(1 - v ** 2, 0, None) ** 0.6, 0.0)
        bumps = 0.7 * S.fbm(P, 4.0, 2, seed + 7)         # 종이 더미 울퉁불퉁
        hh = -0.5 + (top + 0.5) * prof + bumps * prof
        # 출발점: 기단 벽을 따라 흘러내림 (처음 10칸은 높게)
        fall = np.clip(1 - s / (10 * K), 0, 1) * 14 * K * np.clip(1 - dist / (6 * K), 0, 1)
        return np.where(prof > 0, hh + fall, -9.0)
    return h


def paper_parts():
    parts = []
    for side, seed in ((-1, 61), (1, 62)):
        fn = _stream_height(side, seed)
        xs = [p * side for p in (8 * K, 110 * K)]
        parts.append(S.HeightField(fn, min(xs), 26 * K, max(xs), 125 * K, y0=-0.5, ymax=22 * K).with_(
            paint=S.mix(*PAPER_MIX, seed=seed), smooth=PAPER, name=f"paper{side}"))
    return parts


def scatter_pages(d, seed=71):
    """물결 위·주변에 흩어진 종이 (카펫). 물결에서 멀수록 드물게."""
    rng = np.random.default_rng(seed)
    pages = ["minecraft:white_carpet", "minecraft:white_carpet", "minecraft:yellow_carpet"]
    R = int(PLAZA_R) - 2
    for side in (-1, 1):
        path = _stream_path(side)
        xs = np.arange(-R, R + 1)
        X, Z = np.meshgrid(xs, np.arange(20, R + 1), indexing="ij")
        X, Z = X.ravel(), Z.ravel()
        inside = np.hypot(X, Z) < R
        dist, s, L = S.polyline_2d(path, X + 0.5, Z + 0.5)
        half = (6 + 14 * (s / L) ** 0.8) * K
        p = np.clip(1.2 - dist / (half * 1.6), 0, 1) ** 2 * 0.12
        pick = inside & (rng.random(len(X)) < p)
        for x, z in zip(X[pick], Z[pick]):
            # 가장 높은 블록 위가 비었으면 종이 한 장
            for y in range(int(22 * K), -2, -1):
                st = d.get(int(x), y, int(z))
                if st != "minecraft:air":
                    if "carpet" not in st and "slab" not in st and "stairs" not in st and d.get(int(x), y + 1, int(z)) == "minecraft:air":
                        d.set(int(x), y + 1, int(z), pages[rng.integers(len(pages))])
                    break


def build(b):
    d = b.dim("exterior")
    plaza(d)
    stairs(d)
    st = S.carve(d, S.Union(*tower_parts(), *paper_parts()), shell=1, smooth=True)
    scatter_pages(d)
    return st
