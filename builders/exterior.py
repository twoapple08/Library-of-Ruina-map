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
# 비율 근거 (2026-10-11, 위치 전경 원화 측정, 탑 아래 반지름 R 기준): 몸통 높이 ≈ 7.5R, 수관 꼭대기 ≈ 11R,
# 수관 폭(반지름) ≈ 4R, 몸통은 나무 줄기처럼 아래가 굵고 위로 갈수록 좁아짐 (위 ≈ 아래의 0.55배)
PLINTH_H = 30 * K           # 기단 높이
TIERS = 11
TOP = 285 * K               # 몸통 꼭대기 (예전 330 — 탑 혼자 높아 보여서 낮춤)
TIER_H = (TOP - PLINTH_H) / TIERS   # 단 높이 ≈ 23
R_PLINTH = 42 * K
R_BOTTOM = 40 * K
R_TOP = 22 * K
TAPER = 1.35                # >1: 아래쪽에서 빨리 좁아짐 (줄기 모양)
FLARE = 8 * K               # 기단이 땅에서 퍼지는 폭
GATE_W, GATE_H, GATE_FLOOR = 15, 24, 6   # 정문 (K와 무관하게 사람 기준)
PLAZA_R = 110 * K
CITY_R0, CITY_R1 = 300 * K, 750 * K   # 도시 실루엣 반지름 (렌더 거리 문제로 조정 가능)

WOOD = ("minecraft:dark_oak_stairs", "minecraft:dark_oak_slab")
SOUTH = math.pi / 2  # atan2(z, x): +Z 방향


def body_radius(y):
    """기본 반지름(판자 들쑥날쑥 빼고). 기단은 땅에서 나팔처럼 퍼짐."""
    y = np.asarray(y, float)
    t = np.clip((y - PLINTH_H) / (TOP - PLINTH_H), 0, 1)
    r = np.where(y < PLINTH_H, R_PLINTH + FLARE * np.clip(1 - y / (16 * K), 0, 1) ** 2,
                 R_TOP + (R_BOTTOM - R_TOP) * (1 - t) ** TAPER)
    tt = np.clip((y - PLINTH_H) / TIER_H, 0, None)
    bulge = np.where(y >= PLINTH_H, 1.0 * K * np.sin(np.pi * (tt % 1.0)), 0)
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


# 숯색·청회색 나무 (원화). 띠마다 재질이 달라 패치워크처럼 보임
TOWER_STRIPS = (["minecraft:polished_basalt[axis=y]", "minecraft:basalt[axis=y]", "minecraft:deepslate[axis=y]",
                 "minecraft:warped_stem[axis=y]", "minecraft:smooth_basalt", "minecraft:dark_oak_log[axis=y]"],
                [34, 18, 20, 14, 8, 6])
STONE = ("minecraft:polished_deepslate_stairs", "minecraft:polished_deepslate_slab")
WIN_SMALL = "minecraft:ochre_froglight"
WIN_SLIT = "minecraft:shroomlight"


def tower_paint(ctx):
    th, y = ctx.info["theta"], ctx.info["y"]
    tier, idx = _strip(th, y)
    names, w = TOWER_STRIPS
    cw = np.cumsum(w) / np.sum(w)
    h = S.hash01(tier, idx, seed=21)
    states = np.array(names, dtype=object)[np.searchsorted(cw, h, side="right").clip(0, len(names) - 1)]
    # 덧댄 판자 조각 (세로로 9칸마다 띠 재질이 바뀜)
    h2 = S.hash01(tier, idx, np.floor(y / (9 * K)).astype(int), seed=24)
    states = np.where(h2 < 0.12, "minecraft:polished_deepslate", states).astype(object)
    seam = S.hash01(tier, idx, seed=22) < 0.25
    states[seam & (S.hash01(ctx.x, ctx.y, ctx.z, seed=23) < 0.35)] = "minecraft:polished_blackstone"
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
                states[m] = WIN_SMALL if kind == "small" else WIN_SLIT
    return states


def ledge_paint(ctx):
    return np.where(S.hash01(ctx.x, ctx.y, ctx.z, seed=31) < 0.2, "minecraft:polished_basalt[axis=y]",
                    "minecraft:polished_deepslate").astype(object)


def branch_paint(ring=7.0):
    bark = S.log_along("minecraft:deepslate[axis={a}]")
    band = S.log_along("minecraft:basalt[axis={a}]")
    pale = S.log_along("minecraft:polished_basalt[axis={a}]")

    def f(ctx):
        s = ctx.info["s"]
        a, b, c = bark(ctx), band(ctx), pale(ctx)
        ph = s % ring
        out = np.where(ph < 1.4, b, a).astype(object)
        out = np.where((ph >= 1.4) & (ph < 2.2), c, out).astype(object)  # 마디 바로 옆 밝은 띠
        return out
    return f


# ---------------------------------------------------------------- 가지·뿌리 곡선

UP = np.array([0.0, 1.0, 0.0])


def _segmented(radii, pts, period):
    """마디: period마다 반지름을 살짝 부풀림 (원화의 고리 띠)."""
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    bump = np.clip(1 - np.abs((s % period) - 0.7) / 0.9, 0, 1)
    return radii * (1 + 0.16 * bump)


def _wiggle(pts, rng, amp, scale):
    """곡선에 부드러운 흔들림 (진행 방향에 수직)."""
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    P = np.stack([s, np.zeros_like(s), np.zeros_like(s)], 1)
    seed = int(rng.integers(1 << 30))
    off = np.stack([S.fbm(P, scale, 2, seed), S.fbm(P, scale, 2, seed + 1), S.fbm(P, scale, 2, seed + 2)], 1)
    w = np.sin(np.pi * np.clip(s / max(s[-1], 1), 0, 1))[:, None]  # 양 끝은 고정
    return pts + off * amp * w


def _limb(rng, p0, direction, reach, rise, r0, r_end, curl_dir, curl_r, turns, ring):
    """한 가지: 베지어 본체 + 흔들림 + 끝 소용돌이. (점, 반지름)"""
    d = direction / np.linalg.norm(direction)
    side = np.cross(UP, d)
    if np.linalg.norm(side) < 1e-6:
        side = np.array([1.0, 0, 0])
    side /= np.linalg.norm(side)
    lateral = side * rng.uniform(-0.35, 0.35) * reach
    p3 = p0 + d * reach + UP * rise + lateral
    p1 = p0 + d * reach * 0.35 + UP * reach * rng.uniform(0.05, 0.35)
    p2 = p3 - d * reach * 0.3 - UP * rise * rng.uniform(-0.2, 0.5) + lateral * 0.3
    main = S.resample(S.bezier(p0, p1, p2, p3, 90), 1.0)
    main = _wiggle(main, rng, amp=reach * 0.06, scale=max(8.0, reach * 0.35))
    tan = main[-1] - main[-2]
    c = S.curl(main[-1], tan, curl_dir, curl_r, turns=turns, shrink=0.5, step=0.8, Rmin=max(1.0, r_end * 0.9))
    pts = S.join(main, c)
    radii = np.concatenate([np.linspace(r0, r_end, len(main)) ** 1.0,
                            np.linspace(r_end, max(1.0, r_end * 0.5), len(c) - 1)])
    return pts, _segmented(radii, pts, ring), main


def _curl_dir(rng, d):
    side = np.cross(UP, d)
    k = rng.random()
    if k < 0.45:
        base = UP
    elif k < 0.8:
        base = -UP
    else:
        base = side * (1 if rng.random() < 0.5 else -1)
    return base + side * rng.uniform(-0.5, 0.5)


def branch_parts(rng):
    """원화 비율: 가지 굵기 ≈ 몸통 폭의 1/9, 화면 끝까지 길게 뻗고 작은 소용돌이가 많음.
    줄기를 감듯 비스듬히 나오고, 낮은 가지는 아래로 처졌다가 말림. 위로 갈수록 많고 길다."""
    parts = []
    golden = math.pi * (3 - math.sqrt(5))
    n_big = 40
    for i in range(n_big):
        u = rng.random() ** 0.8
        h = 40 * K + (TOP - 45 * K) * u
        th = i * golden + rng.uniform(-0.25, 0.25)
        if abs(((th - SOUTH + np.pi) % (2 * np.pi)) - np.pi) < 0.4 and h < 100 * K:
            th += 0.8  # 정문 위 낮은 곳 비움
        out = np.array([math.cos(th), 0, math.sin(th)])
        tang = np.cross(UP, out) * rng.uniform(-0.7, 0.7)   # 줄기를 감듯이 비스듬히
        d = out + tang
        r_here = float(body_radius(h))
        p0 = out * (r_here - 2.5 * K) + UP * h
        frac = (h - 40 * K) / (TOP - 40 * K)
        reach = (70 + 150 * frac) * K * rng.uniform(0.7, 1.15)
        droop = rng.random() < (0.55 - 0.4 * frac)          # 낮은 가지일수록 아래로 처짐
        rise = reach * math.tan(math.radians(rng.uniform(-30, -8) if droop else rng.uniform(0, 32)))
        r0 = rng.uniform(4.0, 5.6) * K
        r_end = rng.uniform(1.6, 2.1) * K
        pts, rad, main = _limb(rng, p0, d, reach, rise, r0, r_end, _curl_dir(rng, d),
                               r_end * rng.uniform(2.4, 3.4), rng.uniform(1.5, 2.5), ring=rng.uniform(4.5, 6.5) * K)
        parts.append(S.Tube(pts, rad).with_(paint=branch_paint(5.5 * K), smooth=STONE, name=f"branch{i}"))
        # 갈래 1~3개 (본체 30~85% 지점), 각자 끝이 말림
        for j in range(int(rng.integers(1, 4))):
            k = int(len(main) * rng.uniform(0.3, 0.85))
            q0 = main[k]
            tdir = main[min(k + 3, len(main) - 1)] - main[max(k - 3, 0)]
            tdir /= np.linalg.norm(tdir)
            cd = np.cross(tdir, UP)
            if np.linalg.norm(cd) < 1e-6:
                cd = np.array([1.0, 0, 0])
            cd = cd / np.linalg.norm(cd) * (1 if rng.random() < 0.5 else -1)
            cdir = tdir * 0.6 + cd * 0.7 + UP * rng.uniform(-0.5, 0.6)
            rr = float(np.interp(k, [0, len(main) - 1], [r0, r_end])) * 0.62
            rr = max(rr, 1.3)
            cpts, crad, _ = _limb(rng, q0, cdir, reach * rng.uniform(0.25, 0.45), reach * rng.uniform(-0.15, 0.2),
                                  rr, max(1.2, rr * 0.55), _curl_dir(rng, cdir), max(2.6, rr * 2.2),
                                  rng.uniform(1.3, 2.2), ring=4.5 * K)
            parts.append(S.Tube(cpts, crad).with_(paint=branch_paint(4.5 * K), smooth=STONE, name=f"fork{i}_{j}"))
    # 꼭대기 수관 (위치 전경 원화): 몸통 꼭대기에서 꽃병처럼 위·바깥으로 넓게 퍼짐.
    # 수관 반지름 ≈ 4R(160), 꼭대기에서 ≈ 3R(120) 더 솟음. 가운데는 빛기둥 자리로 비움
    n_crown = 13
    for i in range(n_crown):
        th = i * 2 * math.pi / n_crown + rng.uniform(-0.15, 0.15)
        out = np.array([math.cos(th), 0, math.sin(th)])
        y0 = TOP - rng.uniform(4, 22) * K
        p0 = out * (float(body_radius(y0)) - 3 * K) + UP * y0
        reach = rng.uniform(150, 195) * K
        d = out + UP * rng.uniform(0.45, 0.8)
        pts, rad, main = _limb(rng, p0, d, reach, rng.uniform(15, 55) * K, 7.0 * K, 2.2 * K,
                               _curl_dir(rng, out), 2.2 * K * rng.uniform(2.6, 3.6), rng.uniform(1.6, 2.4),
                               ring=6 * K)
        parts.append(S.Tube(pts, rad).with_(paint=branch_paint(6 * K), smooth=STONE, name=f"crown{i}"))
        for j in range(int(rng.integers(2, 5))):  # 갈래: 바깥 절반에서 나와 끝이 말림
            k = int(len(main) * rng.uniform(0.35, 0.9))
            tdir = main[min(k + 3, len(main) - 1)] - main[max(k - 3, 0)]
            tdir /= np.linalg.norm(tdir)
            cdir = tdir + np.cross(tdir, UP) * rng.uniform(-1.1, 1.1) + UP * rng.uniform(-0.6, 0.5)
            rr = float(np.interp(k, [0, len(main) - 1], [7.0 * K, 2.2 * K])) * 0.6
            cpts, crad, _ = _limb(rng, main[k], cdir, reach * rng.uniform(0.18, 0.38), reach * rng.uniform(-0.1, 0.12),
                                  max(rr, 1.3), max(1.2, rr * 0.55), _curl_dir(rng, cdir), max(2.6, rr * 2.2),
                                  rng.uniform(1.4, 2.2), ring=4.5 * K)
            parts.append(S.Tube(cpts, crad).with_(paint=branch_paint(4.5 * K), smooth=STONE, name=f"cfork{i}_{j}"))
    return parts


def root_parts(rng):
    parts = []
    # 뿌리는 종이 물결 사이사이에 두 개씩 (물결 7줄기 → 사이 6곳, 정문 앞은 비움)
    angs = sorted([math.radians(72), math.radians(108)] + [a % (2 * math.pi) for a in STREAM_ANGLES])
    mids = []
    for a, b in zip(angs, angs[1:] + [angs[0] + 2 * math.pi]):
        if abs(a - math.radians(72)) < 1e-6:
            continue  # 정문 두 줄기 사이
        m = (a + b) / 2
        mids += [m - 0.17 + rng.uniform(-0.05, 0.05), m + 0.17 + rng.uniform(-0.05, 0.05)]
    for i, th in enumerate(mids):
        out = np.array([math.cos(th), 0, math.sin(th)])
        side = np.cross(UP, out)
        p0 = out * (R_PLINTH - 5 * K) + UP * 10 * K
        reach = rng.uniform(40, 70) * K
        pts, rad, _ = _limb(rng, p0, out + side * rng.uniform(-0.15, 0.15), reach, -9 * K, rng.uniform(5, 7) * K,
                            2.2 * K, UP + side * rng.uniform(-1, 1), 2.2 * K * 3, 1.6, ring=5.5 * K)
        parts.append(S.Tube(pts, rad).with_(paint=branch_paint(7 * K), smooth=STONE, name=f"root{i}"))
    return parts


# ---------------------------------------------------------------- 조립

def tower_parts(seed=7):
    parts = []
    body = S.Revolve(0, TOP, radius_with_planks, rmax=R_PLINTH + FLARE + 3 * K).with_(paint=tower_paint, name="body")
    gate_cut = S.Box(-GATE_W // 2, GATE_FLOOR, int(R_PLINTH - 4), GATE_W // 2, GATE_FLOOR + GATE_H - 1,
                     int(R_PLINTH + 14))
    # 정문 아래 계단 자리 (기단 나팔 부분을 계단 폭만큼 파냄 → 양옆은 기단 벽)
    stair_cut = S.Box(-GATE_W // 2 - 2, 0, int(R_PLINTH - 6), GATE_W // 2 + 2, GATE_FLOOR - 1, STAIR_Z + 2)
    parts.append(S.Subtract(S.Subtract(body, gate_cut), stair_cut))
    # 단 경계 턱
    for t in range(TIERS + 1):
        yb = PLINTH_H + t * TIER_H

        def rad(y, th, yb=yb):
            return body_radius(np.full_like(y, yb)) + 2.2 * K
        ledge = S.Revolve(yb - 1.0, yb + 1.2, rad, rmax=R_PLINTH + 4 * K).with_(paint=ledge_paint, smooth=STONE)
        parts.append(S.Subtract(ledge, gate_cut) if t == 0 else ledge)

    def awning(y, th):  # 정문 위 차양 (남쪽 ±25°)
        dth = np.abs((th - SOUTH + np.pi) % (2 * np.pi) - np.pi)
        return np.where(dth < 0.42, body_radius(np.full_like(y, PLINTH_H)) + 5 * K, 0.0)
    parts.append(S.Revolve(GATE_FLOOR + GATE_H, GATE_FLOOR + GATE_H + 3.5, awning,
                           rmax=R_PLINTH + 9 * K).with_(paint=ledge_paint, smooth=STONE))
    # 빛나는 문 두 짝 (홈 안쪽 벽 앞): 원화처럼 좁고 긴 빛줄기 (폭 3+3, 가운데 1칸 어두운 틈)
    zb = int(R_PLINTH - 4)
    for x0, x1 in ((-3, -1), (1, 3)):
        parts.append(S.Box(x0, GATE_FLOOR, zb, x1, GATE_FLOOR + GATE_H - 1, zb).with_(
            paint=S.mix(["minecraft:ochre_froglight", "minecraft:pearlescent_froglight"], [3, 1], seed=41)))
    rng = np.random.default_rng(seed)
    parts += branch_parts(rng)
    parts += root_parts(rng)
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


STAIR_Z = int(math.ceil(R_PLINTH + FLARE)) + 1   # 기단 나팔 바깥 = 계단 시작


def stairs(d):
    """정문 홈 → 기단을 판 통로(Y 5) → 앞 사다리꼴 계단 6단 (Y 5 → 0), 앞줄은 계단 블록."""
    z0 = int(R_PLINTH - 4)
    d.fill(-GATE_W // 2 - 2, 0, z0 - 2, GATE_W // 2 + 2, GATE_FLOOR - 1, STAIR_Z, "minecraft:dark_oak_planks")
    zc = STAIR_Z + 1
    for k in range(6):
        top = GATE_FLOOR - 1 - k
        hw = 10 + 3 * k
        za, zb = zc + 3 * k, zc + 3 * k + 2
        if top >= 0:
            d.fill(-hw, 0, za, hw, top - 1, zb, "minecraft:dark_oak_planks") if top > 0 else None
            d.fill(-hw, top, za, hw, top, zb - 1, "minecraft:dark_oak_planks")
            d.fill(-hw, top, zb, hw, top, zb, "minecraft:dark_oak_stairs[facing=north,half=bottom]")
    return zc + 18   # 계단 끝 z


# ---------------------------------------------------------------- 황금 종이 물결

PAPER = ("minecraft:smooth_sandstone_stairs", "minecraft:smooth_sandstone_slab")
PAPER_MIX = (["minecraft:smooth_sandstone", "minecraft:birch_planks", "minecraft:sandstone",
              "minecraft:honeycomb_block", "minecraft:ochre_froglight", "minecraft:glowstone",
              "minecraft:gold_block", "minecraft:end_stone_bricks"],
             [30, 14, 8, 8, 14, 6, 4, 6])


# 원화(위치 전경)의 종이 물결은 탑 둘레 7줄기: 정문 양옆 2줄기 + 나머지 5줄기는 고르게 (54°마다)
STREAM_ANGLES = [math.radians(a) for a in (162, 216, 270, 324, 18)]


def _gate_stream_path(side: int):
    """정문 옆 줄기 중심선 (xz). 기단에서 출발해 계단 옆을 지나 앞·바깥으로 휘며 퍼짐."""
    pts = np.array([[13, 41], [19, 51], [27, 64], [36, 76], [50, 88], [66, 96], [80, 100]], float) * K
    pts[:, 0] *= side
    return S.resample(np.c_[pts[:, 0], np.zeros(len(pts)), pts[:, 1]], 2.0)[:, [0, 2]]


def _radial_stream_path(ang: float):
    """방사형 줄기: 기단 벽에서 출발해 바깥(분화구 첫 옹벽 앞)까지, 살짝 소용돌이 방향으로 휨."""
    r0, r1 = R_PLINTH + FLARE - 6 * K, 132 * K
    u = np.linspace(0, 1, 24)
    r = r0 + (r1 - r0) * u
    a = ang + 0.3 * u ** 1.5
    return S.resample(np.c_[r * np.cos(a), np.zeros_like(r), r * np.sin(a)], 2.0)[:, [0, 2]]


def stream_paths():
    """[(중심선, seed)] 7줄기."""
    out = [(_gate_stream_path(-1), 61), (_gate_stream_path(1), 62)]
    out += [(_radial_stream_path(a), 63 + i) for i, a in enumerate(STREAM_ANGLES)]
    return out


def _stream_height(path, seed: int):
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
    for i, (path, seed) in enumerate(stream_paths()):
        x0, z0 = path.min(0) - 32 * K
        x1, z1 = path.max(0) + 32 * K
        parts.append(S.HeightField(_stream_height(path, seed), x0, z0, x1, z1, y0=-0.5, ymax=22 * K).with_(
            paint=S.mix(*PAPER_MIX, seed=seed), smooth=PAPER, name=f"paper{i}"))
    return parts


def scatter_pages(d, seed=71):
    """물결 위·주변에 흩어진 종이 (카펫). 물결에서 멀수록 드물게."""
    rng = np.random.default_rng(seed)
    pages = ["minecraft:white_carpet", "minecraft:white_carpet", "minecraft:yellow_carpet"]
    R = int(PLAZA_R) - 2
    for path, _ in stream_paths():
        (bx0, bz0), (bx1, bz1) = path.min(0) - 40 * K, path.max(0) + 40 * K
        X, Z = np.meshgrid(np.arange(int(bx0), int(bx1) + 1), np.arange(int(bz0), int(bz1) + 1), indexing="ij")
        X, Z = X.ravel(), Z.ravel()
        inside = (np.hypot(X, Z) < R) & (np.hypot(X, Z) > R_PLINTH)
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


def gate_walkable(d, box):
    """걷기 구역 가운데 줄: 발밑(Y 5)은 단단하고, 서 있을 두 칸(Y 6, 7)은 비어야 함. 막힌 칸 목록."""
    x0, y0, z0, x1, y1, z1 = box
    bad = []
    for x in range(-2, 3):
        for z in range(z0, z1 + 1):
            feet = d.get(x, GATE_FLOOR - 1, z)
            if feet == "minecraft:air" or any(d.get(x, y, z) not in ("minecraft:air",) and "carpet" not in d.get(x, y, z)
                                              for y in (GATE_FLOOR, GATE_FLOOR + 1)):
                bad.append((x, z))
    if bad:
        raise AssertionError(f"정문 걷기 구역이 막힘/구멍: {bad}")
    return True


def build(b, city: bool = True, clouds: bool = True):
    """외부 전체: 광장·계단 → 탑·종이 물결 → 분화구(단·도시) → 고리 구조물 → 구름 → 빛기둥 건축물 → TP."""
    from builders import crater
    d = b.dim("exterior")
    plaza(d)
    stair_end = stairs(d)
    stats = {"tower": S.carve(d, S.Union(*tower_parts(), *paper_parts()), shell=1, smooth=True)}
    scatter_pages(d)
    if city:
        crater.terraces(d)
        stats["city"] = crater.terrace_city(d)
        stats["ring"] = S.carve(d, S.Union(*crater.ring_landmark()), shell=1, smooth=True)
    if clouds:
        stats["clouds"] = crater.clouds(d)
    stats["spire_top"] = crater.light_spire(d, int(TOP))

    L = b.links
    zb = int(R_PLINTH - 4)
    L.anchor("exterior_spawn", d.dim, 0.5, 0, 100.5, yaw=180)   # 광장 남쪽, 탑을 바라봄
    L.anchor("exterior_gate", d.dim, 0.5, 0, stair_end + 2.5, yaw=0)       # 로비에서 나오면 계단 앞
    L.spawn = "exterior_spawn"
    # 정문: 빛나는 문 앞 홈에 걸어 들어가면 로비로 (클릭도 됨). 홈 바닥 전체(문 앞 4칸)를 구역으로
    # (Phase 1 테스트 ④: 문 앞 2칸만이라 TP 안 됨 → 넓힘, 바닥이 막혀 있지 않은지 gate_walkable 로 확인)
    # 암전 → 로비 청크 로딩 확인 → 암전 해제 + '로비' 글자 (datapack 암전 TP)
    w = L.walk(d.dim, (-6, GATE_FLOOR - 1, zb + 1, 6, GATE_FLOOR + 3, zb + 4), "lobby_entrance", fade=True)
    stats["gate_walkable"] = gate_walkable(d, w.box)
    L.portal(d.dim, 0.5, GATE_FLOOR, zb + 1.5, "lobby_entrance", width=7, height=12)
    return stats
