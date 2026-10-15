"""외부 (도서관 외견·주변 전경) — 자유 형체 판 (2026-10-15).

원화 `reference/도서관 외견.png` 를 도착 자리(초대장 도착, CAM)에서 그대로 보이게 하고, 걸어 다니면 입체:
- 몸통·가지 실루엣은 원화에서 읽은 값(design/fit/exterior.json, tools/art_fit.py)으로 만들고 도착 시점에서 원화를 투영
- 원화에 안 보이는 쪽(뒤·옆·위)은 직접 만든 텍스처(판자·나무껍질)와 미리 구운 밤빛 (원화 색조에 맞춤)
- 하늘·먼 도시는 그린 하늘(모드: 안개 없이 가장 먼 깊이) = 가지를 지운 원화 + 둘레로 이어지는 절차 그림
- 걷는 곳·충돌: 광장·계단은 블록 / 탑·가지·종이 더미는 barrier (보이는 모습은 형체)
좌표: 탑 중심 (0, 0), 광장 윗면 y=0, 정문은 남쪽(+Z). 분화구·도시·고리·구름은 builders/crater.py (블록).
"""
from __future__ import annotations

import math

import numpy as np

import config
from tools import artfit as A
from tools import form_textures as T
from tools import forms as F
from tools import shapes as S

ART = "reference/도서관 외견.png"
CAM = F.Camera((0.1, 1.62, 130.0), 180.0, -32.5)       # 도착 시점 (원화 구도)
SPAWN = (0.1, 0.0, 130.0, 180.0, -32.5)

# ---------------------------------------------------------------- 탑 수치 (원화 실루엣에서, tools/artfit.trunk_profile)
TOP = 362
# 단 경계 (아래 → 위). 앞면 높이는 원화의 턱 줄과 같게
TIERS = [30, 55, 79, 103, 133, 160, 192, 221, 250, 279, 308, 336, TOP]
_PROF_Y = [0, 5, 14, 28, 30, 55, 80, 103, 133, 160, 192, 222, 252, 282, 312, 340, TOP]
_PROF_R = [58.5, 56.5, 55.0, 54.5, 47.0, 48.0, 46.5, 45.0, 45.5, 49.0, 53.0, 53.5, 53.0, 49.5, 44.5, 39.0, 35.0]
PLAZA_R = 134
BAY_C = (0.5, 50.5)          # 정문 앞 반원 돌출부 중심 (x, z)
BAY_R = 9.5                  # → 앞면 z = 60
BAY_H = 16.0
DOOR = (-1.2, 2.2, 2.0, 14.0)   # 문 x0, x1, y0, y1 (빛나는 두 짝, 가운데 어두운 틈)
DOOR_Z = BAY_C[1] + BAY_R - 1.6
GATE_FLOOR = 2               # 문 바닥 높이 (발 높이)
SOUTH = math.pi / 2          # atan2(z, x) 에서 +Z
UP = np.array([0.0, 1.0, 0.0])


def body_radius(y):
    return np.interp(np.asarray(y, float), _PROF_Y, _PROF_R)


# ---------------------------------------------------------------- 재질·빛

def _materials():
    m = {}
    m["art"] = F.mat("ext_art", T.art("art/exterior", ART), emissive=True, flat=True, ao=False)
    boards = [((24, 25, 33), (64, 64, 80)), ((28, 27, 36), (70, 66, 82)), ((22, 26, 34), (58, 66, 80)),
              ((30, 28, 34), (76, 70, 80))]
    m["boards"] = [F.mat(f"ext_board{i}", T.board(f"board{i}", c0, c1, seed=11 + i), emissive=True, flat=True, ao=False)
                   for i, (c0, c1) in enumerate(boards)]
    m["ledge"] = F.mat("ext_ledge", T.board("ledge", (30, 30, 40), (80, 78, 96), w=16, h=16, seed=21, seams=0),
                       emissive=True, flat=True, ao=False)
    m["bark"] = F.mat("ext_bark", T.bark("ext_bark", (30, 28, 40), (78, 70, 94)), emissive=True, flat=True, ao=False)
    m["window"] = F.mat("ext_window", T.window_lit("ext_window"), emissive=True, flat=True, ao=False, glow=3)
    m["slit"] = F.mat("ext_slit", T.window_lit("ext_slit", 32, 8, bars=False), emissive=True, flat=True, ao=False, glow=3)
    m["door"] = F.mat("ext_door", T.glow("ext_door", (255, 226, 160), 16), emissive=True, flat=True, ao=False, glow=3)
    m["dark"] = F.mat("ext_dark", T.flat("ext_dark", (14, 12, 18)), emissive=True, flat=True, ao=False)
    m["paper"] = F.mat("ext_paper", T.paper_pile("ext_paper"), emissive=True, flat=True, ao=False, glow=3)
    m["sheet"] = F.mat("ext_sheet", T.paper("ext_sheet", c=(255, 240, 200), lines=True, seed=31), layer="cutout",
                       emissive=True, flat=True, ao=False)
    m["plaza"] = F.mat("ext_plaza", T.planks("ext_plaza", (26, 22, 24), (70, 60, 58), boards=4, seed=41),
                       emissive=True, flat=True, ao=False)
    m["beam"] = F.mat("ext_beam", T.glow("ext_beam", (255, 236, 190), 16), emissive=True, flat=True, ao=False, glow=3)
    m["beam_halo"] = F.mat("ext_beam_halo", T.glow("ext_beam_halo", (255, 220, 150), 16), layer="translucent",
                           emissive=True, flat=True, ao=False)
    T.paper("paper_0")
    T.paper("paper_1", c=(250, 236, 200), lines=False, seed=9)
    T.paper("paper_gold", c=(255, 214, 120), lines=False, seed=10)
    return m


def night(q: F.Quads, strength: float = 1.0) -> F.Quads:
    """원화의 밤빛을 꼭짓점 색에 구움: 위·왼쪽 앞에서 보랏빛 달빛, 아래에서 황금 종이 반사, 그늘은 남보라."""
    return F.bake_light(q, sun=(-0.45, 0.55, 0.7), sun_rgb=(0.5, 0.42, 0.62), sky_rgb=(0.78, 0.74, 0.98),
                        ground_rgb=(0.72, 0.6, 0.5), strength=strength)


# ---------------------------------------------------------------- 몸통: 세로 판자 패치워크

def board_ring(y0, y1, rfun, mats, seed, board_w=3.6, arc=(0.0, 360.0), center=(0.0, 0.0), bulge=0.9,
               skip=None, row_h=2.0, tile_h=14.0):
    """세로 판자를 둘러 붙인 원통 띠. 판자마다 안팎 들쑥날쑥(0~0.6) + 재질·색조 + 위아래 끝 어긋남.
    rfun(y) = 반지름, bulge = 띠 가운데가 볼록한 정도. skip(x, z, y) → True 면 그 판자 칸을 비움 (문 구멍)."""
    rng = np.random.default_rng(seed)
    cx, cz = center
    r_mid = float(np.mean(rfun(np.array([y0, y1]))))
    a0, a1 = np.radians(arc[0]), np.radians(arc[1])
    n = max(3, int(round((a1 - a0) * r_mid / board_w)))
    edges = np.linspace(a0, a1, n + 1)
    nrow = max(1, int(round((y1 - y0) / row_h)))
    out = []
    offs = rng.choice([0.0, 0.0, 0.18, 0.35, -0.12, 0.55], n)
    tints = rng.uniform(0.82, 1.12, n)
    dy0 = rng.choice([0.0, 0.0, 0.0, 0.6, 1.2], n)
    for k in range(n):
        th = np.linspace(edges[k], edges[k + 1], 3)
        ys = np.linspace(y0 + dy0[k] * 0, y1, nrow + 1)
        Th, Y = np.meshgrid(th, ys, indexing="ij")
        u = (Th - edges[k]) / (edges[k + 1] - edges[k])
        rr = rfun(Y) + offs[k] + bulge * np.sin(np.pi * (Y - y0) / (y1 - y0))
        G = np.stack([cx + rr * np.cos(Th), Y, cz + rr * np.sin(Th)], -1)
        N = np.stack([np.cos(Th), np.zeros_like(Th), np.sin(Th)], -1)
        UV = np.stack([u * 0.999, (Y - y0) / tile_h], -1)
        q = F.fit_tiles(F.grid(G, UV, mats[int(rng.integers(len(mats)))], N=N))
        if skip is not None:
            c = q.P.mean(1)
            q = q.take(~skip(c[:, 0], c[:, 2], c[:, 1]))
        out.append(q.tint((tints[k],) * 3))
        # 옆 판자와의 턱 (세로 띠)
        nk = (k + 1) % n
        if (arc[1] - arc[0]) < 360 and k == n - 1:
            continue
        d = offs[nk] - offs[k]
        if abs(d) > 0.05:
            t = edges[k + 1]
            ys2 = np.linspace(y0, y1, nrow + 1)
            ra = rfun(ys2) + offs[k] + bulge * np.sin(np.pi * (ys2 - y0) / (y1 - y0))
            rb = ra + d
            G = np.stack([np.stack([cx + ra * np.cos(t), ys2, cz + ra * np.sin(t)], -1),
                          np.stack([cx + rb * np.cos(t), ys2, cz + rb * np.sin(t)], -1)], 1)
            side = np.array([-math.sin(t), 0, math.cos(t)]) * (1 if d < 0 else -1)
            UV = np.stack([np.stack([np.zeros(nrow + 1), (ys2 - y0) / tile_h], -1),
                           np.stack([np.full(nrow + 1, 0.12), (ys2 - y0) / tile_h], -1)], 1)
            sq = F.fit_tiles(F.grid(G, UV, mats[0], N=np.broadcast_to(side, G.shape)))
            if skip is not None:
                c = sq.P.mean(1)
                sq = sq.take(~skip(c[:, 0], c[:, 2], c[:, 1]))
            out.append(sq.tint((0.55, 0.55, 0.6)))
    return F.concat(out)


def ledge(y, r, mat, depth=2.4, th=1.6, arc=(0.0, 360.0), center=(0.0, 0.0), segs=None):
    """단 경계 턱 (둥근 테). 위는 밝게, 아래는 어둡게."""
    prof = [(r - 0.3, y - th * 0.7), (r + depth * 0.8, y - th * 0.55), (r + depth, y - th * 0.1),
            (r + depth * 0.95, y + th * 0.3), (r + depth * 0.4, y + th * 0.5), (r - 0.3, y + th * 0.45)]
    segs = segs or max(24, int(2 * math.pi * r / 2.2))
    q = F.revolve(prof, mat, segs=segs, center=(center[0], 0, center[1]), tiles_around=max(1, segs // 2),
                  tile_up=1.0, arc=arc)
    return q


def tower(m):
    """몸통·기단·턱·정문 돌출부·문 (형체). 반환: (면 묶음 목록, 창 목록)."""
    parts = []

    def door_hole(x, z, y):
        return (x > DOOR[0] - 0.3) & (x < DOOR[1] + 0.3) & (y < DOOR[3] + 0.2) & (z > BAY_C[1])

    # 기단 (0~30): 판자 + 나팔처럼 퍼진 아래
    parts.append(board_ring(0, TIERS[0], body_radius, m["boards"], seed=1, bulge=0.6, row_h=2.5))
    # 단 (11개 + 꼭대기)
    for i, (ya, yb) in enumerate(zip(TIERS[:-1], TIERS[1:])):
        parts.append(board_ring(ya, yb, body_radius, m["boards"], seed=10 + i, bulge=1.1, row_h=2.5,
                                board_w=3.4 + 0.4 * (i % 3)))
    for y in TIERS[:-1]:
        parts.append(ledge(y, float(body_radius(y + 0.5)), m["ledge"]))
    # 꼭대기 덮개 (평평하지 않게 살짝 오목) — 빛기둥 받침이 올라섬
    rt = float(body_radius(TOP))
    parts.append(F.revolve([(0.0, TOP - 3), (rt * 0.6, TOP - 1.5), (rt + 0.5, TOP + 0.4)][::-1], m["ledge"], segs=96,
                           tiles_around=48, tile_up=2.0).flipped())
    # 정문 돌출부 (반원 판자 벽 + 위 테 + 문 홈)
    bc = BAY_C
    rb = lambda y: np.full_like(np.asarray(y, float), BAY_R)
    parts.append(board_ring(0, BAY_H, rb, m["boards"], seed=5, arc=(-10, 190), center=bc, bulge=0.4,
                            board_w=2.6, skip=door_hole, row_h=2.0, tile_h=10.0))
    parts.append(ledge(BAY_H, BAY_R, m["ledge"], depth=2.0, th=2.4, arc=(-15, 195), center=bc))
    parts.append(F.revolve([(BAY_R + 1.5, BAY_H + 1.2), (0.0, BAY_H + 1.6)], m["ledge"], segs=40,
                           center=(bc[0], 0, bc[1]), tiles_around=10, tile_up=4.0, arc=(-15, 195)))
    # 문 홈: 양옆·위 벽(어둡게) + 빛나는 두 짝 (가운데 0.3 어두운 틈)
    x0, x1, y0, y1 = DOOR
    zf = bc[1] + BAY_R + 0.6
    zd = DOOR_Z
    parts.append(F.plane((x0 - 0.3, y0, zd), (0, 0, zf - zd), (0, y1 - y0 + 0.2, 0), m["dark"]))
    parts.append(F.plane((x1 + 0.3, y0, zf), (0, 0, zd - zf), (0, y1 - y0 + 0.2, 0), m["dark"]))
    parts.append(F.plane((x0 - 0.3, y1 + 0.2, zf), (x1 - x0 + 0.6, 0, 0), (0, 0, zd - zf), m["dark"]))
    xm = (x0 + x1) / 2
    for a, b in ((x0, xm - 0.15), (xm + 0.15, x1)):
        parts.append(F.plane((a, y0, zd), (b - a, 0, 0), (0, y1 - y0, 0), m["door"], tile=(4, 4)))
    parts.append(F.plane((xm - 0.15, y0, zd - 0.05), (0.3, 0, 0), (0, y1 - y0, 0), m["dark"]))
    return parts


def windows(m, view: A.ArtView, fit, seed=5):
    """창: 원화에 보이는 창은 원화 자리 그대로(몸통 앞면에 되비춤), 나머지 둘레는 절차 배치. 작은 창 2×3, 긴 창 12×1."""
    out = []
    rng = np.random.default_rng(seed)

    def place(th, yc, w, h, mat, rad=None):
        r = (float(body_radius(yc)) + 1.2) if rad is None else rad
        n = np.array([math.cos(th), 0, math.sin(th)])
        t = np.array([-math.sin(th), 0, math.cos(th)])
        c = n * r + UP * yc
        return F.plane(c - t * w / 2 - UP * h / 2, t * w, UP * h, mat, tile=(max(w, 0.5), max(h, 0.5)))

    front = []
    for x0, y0, x1, y1 in fit["windows"]:
        # 원화 창 상자 가운데 광선이 몸통(반지름+1.2)에 닿는 점
        v = view.ray((x0 + x1) / 2, (y0 + y1) / 2)
        C = view.C
        lo, hi = 0.0, 400.0
        for _ in range(40):
            mid = (lo + hi) / 2
            P = C + v * mid
            if math.hypot(P[0], P[2]) > float(body_radius(P[1])) + 1.2:
                lo = mid
            else:
                hi = mid
        P = C + v * hi
        size = view.px_size(P)
        w, h = max(1.0, (x1 - x0) * size), max(0.8, (y1 - y0) * size)
        th = math.atan2(P[2], P[0])
        kind = m["slit"] if w > 4 * h else m["window"]
        out.append(place(th, P[1], w, h, kind))
        front.append((th, P[1]))
    # 절차 창: 정면(원화에 보이는 쪽 ±70°)은 빼고
    for t in range(len(TIERS) - 1):
        ya, yb = TIERS[t], TIERS[t + 1]
        for _ in range(int(rng.integers(18, 30))):
            th = rng.uniform(-math.pi, math.pi)
            if abs((th - SOUTH + math.pi) % (2 * math.pi) - math.pi) < math.radians(70):
                continue
            yc = rng.uniform(ya + 4, yb - 4)
            g = int(rng.choice([1, 1, 2, 2, 3]))
            for k in range(g):
                out.append(place(th + k * 2.4 / float(body_radius(yc)), yc, 1.4, 2.0, m["window"]))
        for _ in range(int(rng.integers(0, 3))):
            th = rng.uniform(-math.pi, math.pi)
            if abs((th - SOUTH + math.pi) % (2 * math.pi) - math.pi) < math.radians(70):
                continue
            yc = rng.uniform(ya + 6, yb - 6)
            for row in range(int(rng.integers(2, 4))):
                out.append(place(th, yc + row * 1.6, 9.0, 0.7, m["slit"]))
    # 기단 문 옆 작은 창 (원화: 문 양옆 아래 2개씩)
    for side in (-1, 1):
        for k in range(2):
            x = BAY_C[0] + side * (3.6 + k * 2.0)
            z = BAY_C[1] + math.sqrt(max(BAY_R ** 2 - (x - BAY_C[0]) ** 2, 0)) + 0.45
            out.append(F.plane((x - 0.6, 3.0, z), (1.2, 0, 0), (0, 1.8, 0), m["window"]))
    return out


# ---------------------------------------------------------------- 가지·뿌리 (뒤쪽·수관은 절차, 앞쪽은 원화)

def _wiggle(pts, rng, amp, scale):
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    P = np.stack([s, np.zeros_like(s), np.zeros_like(s)], 1)
    seed = int(rng.integers(1 << 30))
    off = np.stack([S.fbm(P, scale, 2, seed), S.fbm(P, scale, 2, seed + 1), S.fbm(P, scale, 2, seed + 2)], 1)
    w = np.sin(np.pi * np.clip(s / max(s[-1], 1), 0, 1))[:, None]
    return pts + off * amp * w


def _limb(rng, p0, direction, reach, rise, r0, r_end, curl_dir, curl_r, turns):
    """한 가지: 베지어 본체 + 흔들림 + 끝 소용돌이 → (점, 반지름, 본체 점)."""
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
    radii = np.concatenate([np.linspace(r0, r_end, len(main)), np.linspace(r_end, max(0.8, r_end * 0.5), len(c) - 1)])
    return pts, radii, main


def _curl_dir(rng, d):
    side = np.cross(UP, d)
    k = rng.random()
    base = UP if k < 0.45 else (-UP if k < 0.8 else side * (1 if rng.random() < 0.5 else -1))
    return base + side * rng.uniform(-0.5, 0.5)


def _front(th, deg=62):
    return abs((th - SOUTH + math.pi) % (2 * math.pi) - math.pi) < math.radians(deg)


def procedural_branches(rng):
    """뒤·옆 가지 (원화가 덮는 정면 ±62° 는 빼고), 수관(꼭대기 둘레 전부), 갈래. [(점, 반지름)]"""
    out = []
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(46):
        u = rng.random() ** 0.8
        h = 45 + (TOP - 50) * u
        th = i * golden + rng.uniform(-0.25, 0.25)
        if _front(th):
            continue
        o = np.array([math.cos(th), 0, math.sin(th)])
        d = o + np.cross(UP, o) * rng.uniform(-0.7, 0.7)
        p0 = o * (float(body_radius(h)) - 3) + UP * h
        frac = (h - 45) / (TOP - 45)
        reach = (80 + 150 * frac) * rng.uniform(0.7, 1.15)
        droop = rng.random() < (0.55 - 0.4 * frac)
        rise = reach * math.tan(math.radians(rng.uniform(-30, -8) if droop else rng.uniform(0, 32)))
        r0, r_end = rng.uniform(4.5, 6.2), rng.uniform(1.7, 2.3)
        pts, rad, main = _limb(rng, p0, d, reach, rise, r0, r_end, _curl_dir(rng, d), r_end * rng.uniform(2.4, 3.4),
                               rng.uniform(1.5, 2.5))
        out.append((pts, rad))
        for _ in range(int(rng.integers(1, 4))):
            k = int(len(main) * rng.uniform(0.3, 0.85))
            tdir = main[min(k + 3, len(main) - 1)] - main[max(k - 3, 0)]
            tdir /= np.linalg.norm(tdir)
            cd = np.cross(tdir, UP)
            cd = cd / max(np.linalg.norm(cd), 1e-6) * (1 if rng.random() < 0.5 else -1)
            cdir = tdir * 0.6 + cd * 0.7 + UP * rng.uniform(-0.5, 0.6)
            rr = max(float(np.interp(k, [0, len(main) - 1], [r0, r_end])) * 0.62, 1.3)
            cp, cr, _ = _limb(rng, main[k], cdir, reach * rng.uniform(0.25, 0.45), reach * rng.uniform(-0.15, 0.2),
                              rr, max(1.1, rr * 0.55), _curl_dir(rng, cdir), max(2.6, rr * 2.2), rng.uniform(1.3, 2.2))
            out.append((cp, cr))
    # 수관: 꼭대기에서 꽃병처럼 위·바깥으로 (위치 전경 원화)
    for i in range(14):
        th = i * 2 * math.pi / 14 + rng.uniform(-0.15, 0.15)
        o = np.array([math.cos(th), 0, math.sin(th)])
        y0 = TOP - rng.uniform(6, 26)
        p0 = o * (float(body_radius(y0)) - 3) + UP * y0
        reach = rng.uniform(160, 210)
        d = o + UP * rng.uniform(0.45, 0.8)
        pts, rad, main = _limb(rng, p0, d, reach, rng.uniform(15, 55), 8.0, 2.4, _curl_dir(rng, o),
                               2.4 * rng.uniform(2.6, 3.6), rng.uniform(1.6, 2.4))
        out.append((pts, rad))
        for _ in range(int(rng.integers(2, 5))):
            k = int(len(main) * rng.uniform(0.35, 0.9))
            tdir = main[min(k + 3, len(main) - 1)] - main[max(k - 3, 0)]
            tdir /= np.linalg.norm(tdir)
            cdir = tdir + np.cross(tdir, UP) * rng.uniform(-1.1, 1.1) + UP * rng.uniform(-0.6, 0.5)
            rr = max(float(np.interp(k, [0, len(main) - 1], [8.0, 2.4])) * 0.6, 1.3)
            cp, cr, _ = _limb(rng, main[k], cdir, reach * rng.uniform(0.18, 0.38), reach * rng.uniform(-0.1, 0.12),
                              rr, max(1.1, rr * 0.55), _curl_dir(rng, cdir), max(2.6, rr * 2.2), rng.uniform(1.4, 2.2))
            out.append((cp, cr))
    return out


def roots(rng):
    """기단에서 땅을 따라 뻗는 굵은 뿌리 (종이 물결 사이, 정문 앞은 비움)."""
    out = []
    angs = [a for a in np.linspace(0, 2 * math.pi, 14, endpoint=False) + 0.12
            if abs((a - SOUTH + math.pi) % (2 * math.pi) - math.pi) > 0.32]
    for th in angs:
        th += rng.uniform(-0.08, 0.08)
        o = np.array([math.cos(th), 0, math.sin(th)])
        side = np.cross(UP, o)
        p0 = o * (float(body_radius(8)) - 4) + UP * 12
        near = _front(th, 60)        # 정면 쪽은 짧게, 옆으로 (도착 시점 앞을 막지 않게)
        reach = rng.uniform(22, 32) if near else rng.uniform(40, 75)
        dirn = o * 0.5 + side * (1 if (th - SOUTH) % (2 * math.pi) < math.pi else -1) if near else \
            o + side * rng.uniform(-0.2, 0.2)
        pts, rad, _ = _limb(rng, p0, dirn, reach, -12.5, rng.uniform(5.0, 7.0) if not near else rng.uniform(3.5, 4.5),
                            2.0, UP + side * rng.uniform(-1, 1), 5.5, 1.6)
        out.append((pts, rad))
    return out


def art_branches(view, fit):
    edge = {y: (a, b) for y, a, b in fit["trunk"]}
    return A.branch_paths(view, fit["branches"], lambda y: float(body_radius(y)), ymax_px=440,
                          trunk_edge=lambda yp: edge.get(int(round(yp))))


def tube(P, R, mat, rings=True, sides=None):
    """가지 관 (마디 고리: 6칸마다 살짝 부풂, 둘레 면 수는 굵기에 따라)."""
    P = np.asarray(P, float)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    L = max(s[-1], 1e-3)
    R = np.asarray(R, float)
    if rings:
        bump = np.clip(1 - np.abs((s % 6.0) - 0.7) / 0.9, 0, 1)
        R = R * (1 + 0.14 * bump)
    rmax = float(R.max())
    sides = sides or int(np.clip(round(rmax * 2.2), 6, 14))
    return F.sweep(P, lambda t: np.interp(t * L, s, R), mat, sides=sides, step=min(1.6, max(0.6, rmax * 0.35)),
                   tile_along=3.0, profile=lambda th: 1 + 0.06 * np.cos(th * 5))


# ---------------------------------------------------------------- 황금 종이 물결

STREAM_ANGLES = [math.radians(a) for a in (162, 216, 270, 324, 18)]


def _gate_stream_path(side):
    """정문 돌출부 옆에서 쏟아져 계단 옆을 지나 앞·바깥으로 휘며 퍼짐 (원화)."""
    pts = np.array([[11, 52], [14, 59], [19, 66], [28, 74], [42, 84], [60, 92], [80, 98], [100, 102]], float)
    pts[:, 0] = pts[:, 0] * side + BAY_C[0]
    return S.resample(np.c_[pts[:, 0], np.zeros(len(pts)), pts[:, 1]], 2.0)[:, [0, 2]]


def _radial_stream_path(ang):
    r0, r1 = float(body_radius(2)) - 4, 132.0
    u = np.linspace(0, 1, 24)
    r = r0 + (r1 - r0) * u
    a = ang + 0.3 * u ** 1.5
    return S.resample(np.c_[r * np.cos(a), np.zeros_like(r), r * np.sin(a)], 2.0)[:, [0, 2]]


def stream_paths():
    out = [(_gate_stream_path(-1), 61), (_gate_stream_path(1), 62)]
    out += [(_radial_stream_path(a), 63 + i) for i, a in enumerate(STREAM_ANGLES)]
    return out


def _stream_height(path, seed):
    def h(X, Z):
        dist, s, L = S.polyline_2d(path, X, Z)
        u = s / L
        half = 5 + 15 * u ** 0.8
        top = 4.0 - 2.2 * u
        P = np.stack([X, np.zeros_like(X), Z], 1)
        edge = half * (1 + 0.35 * S.fbm(P, 9.0, 3, seed))
        v = np.clip(dist / np.maximum(edge, 1e-6), 0, None)
        prof = np.where(v < 1, np.clip(1 - v ** 2, 0, None) ** 0.6, 0.0)
        bumps = 0.7 * S.fbm(P, 4.0, 2, seed + 7)
        hh = -0.3 + (top + 0.3) * prof + bumps * prof
        fall = np.clip(1 - s / 14, 0, 1) ** 1.5 * 7 * np.clip(1 - dist / 9, 0, 1) ** 0.7   # 기단 벽을 따라 흘러내림
        return np.where(prof > 0, hh + fall, -9.0)
    return h


def paper_streams(m, rng):
    """종이 물결: 높이장 형체(빛나는 종이 더미) + 위에 흩어진 종이 장. 반환 (물결 면들, 종이 장, 충돌용 높이장 Part 들)."""
    faces, sheets, parts = [], [], []
    for path, seed in stream_paths():
        x0, z0 = path.min(0) - 30
        x1, z1 = path.max(0) + 30
        fy = _stream_height(path, seed)
        q = F.heightfield(x0, z0, x1, z1, lambda X, Z: fy(X.ravel(), Z.ravel()).reshape(X.shape), m["paper"],
                          step=1.0, tile=4.0)
        c = q.P.mean(1)
        q = q.take(q.P[:, :, 1].max(1) > -0.2)          # 물결 바깥(바닥 아래) 버림
        q = q.color_by(lambda P, N: np.clip(0.75 + 0.1 * P[:, 1:2], 0.7, 1.15) * np.ones((1, 3)))
        faces.append(q)
        parts.append(S.HeightField(fy, x0, z0, x1, z1, y0=-0.5, ymax=22).with_(paint="minecraft:barrier"))
        # 흩어진 종이 장 (물결 위·가장자리)
        n = int(len(q) * 0.05)
        idx = rng.integers(0, len(q), n)
        for i in idx:
            p = q.P[i].mean(0) + np.array([rng.uniform(-0.5, 0.5), 0.05, rng.uniform(-0.5, 0.5)])
            a = rng.uniform(0, 2 * math.pi)
            du = np.array([math.cos(a), rng.uniform(-0.15, 0.15), math.sin(a)]) * 0.7
            dv = np.array([-math.sin(a), rng.uniform(-0.1, 0.25), math.cos(a)]) * 0.5
            sheets.append(F.two_sided(F.plane(p - du / 2 - dv / 2, du, dv, m["sheet"])))
    return faces, F.concat(sheets), parts


# ---------------------------------------------------------------- 광장 (형체 겉면, 걷는 건 barrier)

def plaza_faces(m):
    """방사형 나무 판자 바닥 (y=0 윗면). 판자 띠 = 각도 96칸 × 반지름 9칸마다 색조."""
    rr = np.arange(0, PLAZA_R + 1, 4.0)
    rr[0] = 0.5
    out = []
    n = 96
    rng = np.random.default_rng(51)
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        A_, R_ = np.meshgrid(np.linspace(a0, a1, 3), rr, indexing="ij")
        G = np.stack([R_ * np.cos(A_), np.zeros_like(R_), R_ * np.sin(A_)], -1)
        UV = np.stack([(A_ - a0) / (a1 - a0) * 0.999, R_ / 8.0], -1)
        q = F.fit_tiles(F.grid(G, UV, m["plaza"], N=np.broadcast_to(UP, G.shape)))
        c = q.P.mean(1)
        ring = np.floor(np.hypot(c[:, 0], c[:, 2]) / 9).astype(int)
        tone = 0.8 + 0.35 * S.hash01(np.full(len(q), k), ring, seed=52)
        q.C[..., :3] *= tone[:, None, None]
        out.append(q)
    return F.concat(out)


# ---------------------------------------------------------------- 빛기둥 (위치 전경 원화: 꼭대기에서 하늘 끝까지)

def light_spire(m, y_end):
    y0 = TOP - 2
    core = F.revolve([(14.0, y0), (9.0, y0 + 200), (6.0, y_end)], m["beam"], segs=48, tiles_around=12, tile_up=16)
    halo = F.revolve([(20.0, y0), (14.0, y0 + 200), (10.0, y_end)], m["beam_halo"], segs=48, tiles_around=12,
                     tile_up=16)
    halo = F.gradient_y(halo, y0, y_end, (1, 1, 1), (1, 1, 1)).tint((1, 1, 1), 0.35)
    # 받침: 꼭대기 테두리에서 기둥으로 모이는 검은 갈비살 8개
    ribs = []
    rim = float(body_radius(TOP)) - 1.5
    for k in range(8):
        a = k * math.pi / 4 + 0.2
        o = np.array([math.cos(a), 0, math.sin(a)])
        pts = S.resample(S.bezier(o * rim + UP * (TOP - 6), o * (rim + 4) + UP * (TOP + 14), o * 19 + UP * (y0 + 26),
                                  o * 16 + UP * (y0 + 42), 60), 1.0)
        ribs.append(F.sweep(pts, lambda t: 2.4 - 1.2 * t, m["bark"], sides=8, step=1.0))
    return [core, halo, *ribs]


# ---------------------------------------------------------------- 하늘

SKY_GRADIENT = [(-5, (22, 14, 34)), (2.7, (250, 230, 175)), (6, (155, 124, 96)), (13, (146, 83, 122)),
                (21, (130, 95, 146)), (30, (106, 116, 160)), (38, (84, 139, 160)), (46, (61, 126, 151)),
                (50.5, (54, 104, 133)), (54, (69, 73, 111)), (58, (101, 80, 141)), (64.5, (74, 44, 103)),
                (67.5, (58, 32, 85)), (90, (40, 20, 76))]


def sky(lay):
    from PIL import Image
    hsv = np.asarray(Image.open(A.ROOT + "/" + ART).convert("HSV"), float)
    s, v = hsv[..., 1], hsv[..., 2]
    yy = np.arange(hsv.shape[0])[:, None]
    mask = A.load_mask("exterior") | ((v < 100) & (s < 120) & (yy < 200)) | ((v < 95) & (s < 75) & (yy >= 200) & (yy < 440))
    clean = A.clean_sky(ART, mask, grow=4)
    pano = A.sky_panorama(CAM, clean, 4096, 1536, gradient=SKY_GRADIENT, city=dict(near=30, far=22), feather=0.15)
    names = T.panorama("sky_ext", pano, 512)
    mats = [[F.mat(f"sky_ext_{r}_{c}", nm, emissive=True, flat=True, ao=False) for c, nm in enumerate(row)]
            for r, row in enumerate(names)]
    below = F.mat("sky_ext_below", T.flat("sky_ext_below", (22, 14, 34)), emissive=True, flat=True, ao=False)
    lay.sky(A.sky_dome(mats, radius=100.0, yaw=CAM.yaw, below_mat=below))


# ---------------------------------------------------------------- 조립

def tree_collision(branches, roots_):
    """보이는 모습은 형체 → 충돌만 barrier (몸통·기단·돌출부 껍질, 가지·뿌리 관)."""
    def body_r(y, th):
        return body_radius(y) + 0.8
    parts = [S.Revolve(0, TOP, body_r, rmax=62)]
    tubes = [S.Tube(P, np.maximum(np.asarray(R) * 0.9, 0.8)) for P, R in branches + roots_]
    return parts, tubes


def build(b, city: bool = True, clouds: bool = True):
    from builders import crater
    d = b.dim("exterior")
    lay = b.form("exterior")
    rng = np.random.default_rng(7)
    m = _materials()
    fit = A.load_fit("exterior")
    view = A.ArtView(CAM, *fit["size"])
    mask = A.load_mask("exterior")
    paper_mask = A.load_mask("exterior", "paper")

    # ---------------------------------------------- 걷는 곳 (블록·barrier)
    plaza_blocks(d)
    stair_end = stairs(d)

    # ---------------------------------------------- 형체
    body = tower(m)
    wins = windows(m, view, fit)
    ab = art_branches(view, fit)
    pb = procedural_branches(rng)
    rt = roots(rng)
    br = [tube(P, R, m["bark"]) for P, R in ab + pb + rt]
    paper_faces, sheets, paper_parts = paper_streams(m, rng)
    plaza = plaza_faces(m)

    body = [night(q) for q in body]
    br = [night(q) for q in br]
    # 원화 투영 (도착 시점에서 보이는 면, 마스크 안만). 창·문·종이 장은 제 색 그대로 (가리개로만)
    tree_parts = [F.subdivide(q, 2.0) for q in body + br]
    plaza_s = F.subdivide(plaza, 2.0)
    paper_s = [F.subdivide(q, 2.0) for q in paper_faces]
    grow = _dilate(mask, 3)
    projected = F.project_scene(tree_parts + [plaza_s] + paper_s, CAM, m["art"], occluders=wins,
                                masks=[grow] * len(tree_parts) + [None] + [_dilate(paper_mask, 4)] * len(paper_s),
                                min_facing=0.18, zres=(1000, 562))
    for q in projected[:len(tree_parts)]:
        lay.add(q, max_edge=2.0)
    lay.add(projected[len(tree_parts)], max_edge=4.0)
    for q in projected[len(tree_parts) + 1:]:
        lay.add(q, max_edge=2.0)
    lay.add(sheets)
    for q in wins:
        lay.add(q)
    y_end = d.min_y + d.height - 8
    for q in light_spire(m, y_end):
        lay.add(q, max_edge=4.0)
    sky(lay)

    # ---------------------------------------------- 충돌 (barrier)
    body_parts, tubes = tree_collision(ab + pb, rt)
    S.carve(d, S.Union(*[p.with_(paint="minecraft:barrier") for p in body_parts + tubes + paper_parts]),
            shell=1, smooth=False, only_air=True)
    _bay_collision(d)

    # ---------------------------------------------- 날리는 종이 (정문 앞·물결 위)
    for path, _ in stream_paths()[:2]:
        (x0, z0), (x1, z1) = path.min(0) - 6, path.max(0) + 6
        lay.emitter(F.Emitter((x0, 0.5, z0, x1, 10, z1), rate=5.0,
                              sprites=("ruina:block/form/paper_0", "ruina:block/form/paper_1",
                                       "ruina:block/form/paper_gold"), wind=(0.0, -0.5, 0.35), size=0.3, glow=True))
    lay.emitter(F.Emitter((-60, 20, -60, 60, 120, 75), rate=6.0, sprites=("ruina:block/form/paper_1",
                                                                          "ruina:block/form/paper_gold"),
                          wind=(0.3, -0.7, 0.2), size=0.35, glow=True))

    stats = {"faces_tree": sum(len(q) for q in tree_parts), "branches": len(ab) + len(pb) + len(rt)}
    if city:
        crater.terraces(d)
        stats["city"] = crater.terrace_city(d)
        stats["ring"] = S.carve(d, S.Union(*crater.ring_landmark()), shell=1, smooth=True)
    if clouds:
        stats["clouds"] = crater.clouds(d)

    L = b.links
    L.anchor("exterior_spawn", d.dim, *SPAWN[:3], yaw=SPAWN[3], pitch=SPAWN[4], title="도서관")
    L.anchor("exterior_gate", d.dim, BAY_C[0], 0, stair_end + 2.5, yaw=0)
    L.spawn = "exterior_spawn"
    zf = BAY_C[1] + BAY_R
    w = L.walk(d.dim, (-1, GATE_FLOOR - 1, int(DOOR_Z), 2, GATE_FLOOR + 2, int(zf)), "lobby_entrance", fade=True)
    stats["gate_walkable"] = gate_walkable(d, w.box)
    L.portal(d.dim, BAY_C[0], GATE_FLOOR, DOOR_Z + 0.6, "lobby_entrance", width=4, height=12)
    return stats


def _dilate(mask, n):
    from PIL import Image, ImageFilter
    return np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * n + 1))) > 127


def _bay_collision(d):
    """정문 돌출부: 반원 벽 barrier (문 홈은 비움) + 홈 바닥 블록."""
    cx, cz = BAY_C
    for x in range(int(cx - BAY_R) - 1, int(cx + BAY_R) + 2):
        for z in range(int(cz), int(cz + BAY_R) + 2):
            r = math.hypot(x + 0.5 - cx, z + 0.5 - cz)
            if r > BAY_R + 0.4:
                continue
            door = DOOR[0] - 0.5 <= x + 0.5 <= DOOR[1] + 0.5 and z + 0.5 > DOOR_Z - 0.6
            for y in range(0, int(BAY_H) + 2):
                if door and y >= GATE_FLOOR and y < DOOR[3]:
                    continue
                if d.get(x, y, z) == "minecraft:air":
                    d.set(x, y, z, "minecraft:barrier")


def plaza_blocks(d):
    """광장: 걷는 바닥 = barrier 한 겹 (보이는 모습은 형체 판자), 가장자리 아래 돌 테두리."""
    R = PLAZA_R
    xs, zs = np.meshgrid(np.arange(-R, R + 1), np.arange(-R, R + 1), indexing="ij")
    rr = np.hypot(xs + 0.5, zs + 0.5)
    disk = rr <= R
    d.place_mask(-R, -1, -R, disk[:, None, :], "minecraft:barrier")
    rim = disk & (rr > R - 2)
    d.place_mask(-R, -3, -R, np.repeat(rim[:, None, :], 2, axis=1), "minecraft:polished_deepslate")


def stairs(d):
    """문 홈 바닥(블록) + 앞 계단 2단 (y 1 → 0). 반환: 계단 끝 z."""
    cx = BAY_C[0]
    zf = int(BAY_C[1] + BAY_R)
    d.fill(int(DOOR[0]) - 1, 0, int(DOOR_Z) - 1, int(DOOR[1]) + 1, GATE_FLOOR - 1, zf, "minecraft:dark_oak_planks")
    d.fill(int(cx) - 6, 0, zf + 1, int(cx) + 6, 0, zf + 2, "minecraft:dark_oak_planks")
    d.fill(int(cx) - 6, 1, zf + 1, int(cx) + 6, 1, zf + 1, "minecraft:dark_oak_stairs[facing=north,half=bottom]")
    d.fill(int(cx) - 8, 0, zf + 3, int(cx) + 8, 0, zf + 3, "minecraft:dark_oak_stairs[facing=north,half=bottom]")
    return zf + 4


def gate_walkable(d, box):
    x0, y0, z0, x1, y1, z1 = box
    bad = []
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if d.get(x, GATE_FLOOR - 1, z) == "minecraft:air" or any(
                    d.get(x, y, z) not in ("minecraft:air",) for y in (GATE_FLOOR, GATE_FLOOR + 1)):
                bad.append((x, z))
    if bad:
        raise AssertionError(f"정문 걷기 구역이 막힘/구멍: {bad}")
    return True


PREVIEW_CAMS = [
    ("정문 앞 (계단에서 올려다봄)", F.Camera.look_at((14, 1.62, 82), (0, 60, 0))),
    ("옆 (동쪽 광장)", F.Camera.look_at((120, 6, 30), (0, 110, 0))),
    ("뒤 (북서쪽 멀리)", F.Camera.look_at((-200, 60, -230), (0, 180, 0))),
]
