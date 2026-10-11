"""SDF(부호 거리장) 도형 엔진.

유기적인 형태(탑·가지·소용돌이·뿌리·물결)를 거리 함수로 정의하고
  1) 겉껍질만 블록으로 만든다 (속 채움 금지: 바깥 공기와 닿는 칸 + 두께 shell)
  2) 곡면 바깥 가장자리에 계단·반블록을 덧붙여 매끄럽게 한다 (덧붙이기만 하므로 껍질에 구멍이 안 생김)
  3) 부품(part)마다 칠하기 함수로 재질을 정한다 (판자 무늬, 고리 띠, 창문 등)

좌표: 블록 (x, y, z)는 연속 공간의 [x, x+1) 칸이고 중심은 (x+0.5, y+0.5, z+0.5).
거리 d < 0 이면 안, > 0 이면 밖. 거리는 대략값이어도 되지만(립시츠 lip ≤ 약 1.5) 부호는 정확해야 한다.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

FAR = 1e3      # 가지치기로 계산 안 한 곳의 거리 (충분히 멀다)
PRUNE = 3.0    # 상자에서 이보다 먼 부품은 계산 생략 (껍질·다듬기에 필요한 범위보다 큼)


# =================================================================== 난수·노이즈

_M1, _M2, _M3 = np.uint64(0x9E3779B97F4A7C15), np.uint64(0xBF58476D1CE4E5B9), np.uint64(0x94D049BB133111EB)


def _mix(h):
    h = (h ^ (h >> np.uint64(30))) * _M2
    h = (h ^ (h >> np.uint64(27))) * _M3
    return h ^ (h >> np.uint64(31))


def hash01(*ints, seed: int = 0) -> np.ndarray:
    """정수 배열들 → [0,1) 결정적 난수 (같은 입력이면 항상 같은 값)."""
    with np.errstate(over="ignore"):
        shape = np.broadcast_shapes(*[np.shape(a) for a in ints])
        h = np.full(shape, np.uint64(seed & 0xFFFFFFFF) * _M1 + np.uint64(0x632BE59BD9B4E019), dtype=np.uint64)
        for a in ints:
            h = _mix(h ^ (np.asarray(a).astype(np.int64).astype(np.uint64) + _M1))
    return (h >> np.uint64(11)).astype(np.float64) / float(1 << 53)


def value_noise(P: np.ndarray, scale: float, seed: int = 0) -> np.ndarray:
    """3D 값 노이즈, 결과 [-1, 1]. P (N,3)."""
    q = np.asarray(P, dtype=np.float64) / scale
    i = np.floor(q).astype(np.int64)
    f = q - i
    u = f * f * (3 - 2 * f)
    out = 0.0
    for dx in (0, 1):
        wx = u[:, 0] if dx else 1 - u[:, 0]
        for dy in (0, 1):
            wy = u[:, 1] if dy else 1 - u[:, 1]
            for dz in (0, 1):
                wz = u[:, 2] if dz else 1 - u[:, 2]
                out = out + wx * wy * wz * hash01(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, seed=seed)
    return out * 2 - 1


def fbm(P, scale: float, octaves: int = 3, seed: int = 0, gain: float = 0.5) -> np.ndarray:
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total = total + amp * value_noise(P, scale / (2 ** o), seed + o * 101)
        norm += amp
        amp *= gain
    return total / norm


# =================================================================== 필드 기본

def _gap(alo, ahi, blo, bhi) -> float:
    """두 상자 사이 거리 (겹치면 0)."""
    g = np.maximum(0, np.maximum(alo - bhi, blo - ahi))
    return float(np.sqrt((g * g).sum()))


class Field:
    lo: np.ndarray
    hi: np.ndarray
    lip: float = 1.0

    def d(self, P: np.ndarray, lo=None, hi=None) -> np.ndarray:
        raise NotImplementedError

    def near(self, lo, hi, margin=PRUNE) -> bool:
        return _gap(self.lo, self.hi, lo, hi) <= margin

    def sections(self, margin: float = 2.0) -> set:
        a = np.floor((self.lo - margin) / 16).astype(int)
        b = np.floor((self.hi + margin) / 16).astype(int)
        return {(x, y, z) for x in range(a[0], b[0] + 1) for y in range(a[1], b[1] + 1) for z in range(a[2], b[2] + 1)}

    # 편의: 집합 연산
    def __or__(self, other):
        return Union(self, other)

    def __sub__(self, other):
        return Subtract(self, other)


class Part(Field):
    """칠할 수 있는 도형 (Union의 직접 자식)."""
    paint = None       # callable(ctx) -> 블록 상태 문자열 배열
    smooth = None      # (계단, 반블록) 이름. None이면 다듬기 안 함
    name = ""

    def info(self, P) -> dict:
        return {}

    def with_(self, paint=None, smooth=None, name=None):
        if paint is not None:
            self.paint = paint if callable(paint) else solid(paint)
        if smooth is not None:
            self.smooth = smooth
        if name is not None:
            self.name = name
        return self


class Union(Field):
    def __init__(self, *children):
        kids = []
        for c in children:
            kids.extend(c.children if isinstance(c, Union) else [c])
        self.children = kids
        self.lo = np.min([c.lo for c in kids], axis=0)
        self.hi = np.max([c.hi for c in kids], axis=0)
        self.lip = max(c.lip for c in kids)

    def d(self, P, lo=None, hi=None):
        return self.d_owner(P, lo, hi)[0]

    def d_owner(self, P, lo=None, hi=None):
        best = np.full(len(P), FAR)
        owner = np.full(len(P), -1, dtype=np.int32)
        for i, c in enumerate(self.children):
            if lo is not None and not c.near(lo, hi):
                continue
            dc = c.d(P, lo, hi)
            m = dc < best
            best[m] = dc[m]
            owner[m] = i
        return best, owner

    def near(self, lo, hi, margin=PRUNE):
        return any(c.near(lo, hi, margin) for c in self.children)

    def sections(self, margin=2.0):
        s = set()
        for c in self.children:
            s |= c.sections(margin)
        return s


class Subtract(Part):
    """base 에서 cut 을 파낸다. 칠하기·다듬기는 base 를 따름."""

    def __init__(self, base: Part, cut: Field):
        self.base, self.cut = base, cut
        self.lo, self.hi, self.lip = base.lo, base.hi, max(base.lip, cut.lip)
        self.paint, self.smooth, self.name = base.paint, base.smooth, base.name

    def d(self, P, lo=None, hi=None):
        db = self.base.d(P, lo, hi)
        if lo is not None and not self.cut.near(lo, hi):
            return db
        return np.maximum(db, -self.cut.d(P, lo, hi))

    def info(self, P):
        return self.base.info(P)

    def sections(self, margin=2.0):
        return self.base.sections(margin)


class Displace(Part):
    """표면을 노이즈 등으로 울퉁불퉁하게: d - fn(P). fn 크기 amp 이하."""

    def __init__(self, base: Part, fn, amp: float, lip_add: float = 0.5):
        self.base, self.fn, self.amp = base, fn, amp
        self.lo, self.hi = base.lo - amp, base.hi + amp
        self.lip = base.lip + lip_add
        self.paint, self.smooth, self.name = base.paint, base.smooth, base.name

    def d(self, P, lo=None, hi=None):
        return self.base.d(P, lo, hi) - self.fn(P)

    def info(self, P):
        return self.base.info(P)

    def sections(self, margin=2.0):
        return self.base.sections(margin + self.amp)


# =================================================================== 기본 도형

class Box(Part):
    """블록 범위 x0..x1, y0..y1, z0..z1 (끝 포함)을 채우는 상자. round > 0이면 모서리 둥글게."""

    def __init__(self, x0, y0, z0, x1, y1, z1, round_: float = 0.0):
        lo = np.array([min(x0, x1), min(y0, y1), min(z0, z1)], float)
        hi = np.array([max(x0, x1), max(y0, y1), max(z0, z1)], float) + 1
        self.lo, self.hi, self.r = lo, hi, round_
        self.c, self.h = (lo + hi) / 2, (hi - lo) / 2 - round_

    def d(self, P, lo=None, hi=None):
        q = np.abs(P - self.c) - self.h
        out = np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0)
        return out - self.r


class Sphere(Part):
    def __init__(self, c, r):
        self.c, self.r = np.asarray(c, float), float(r)
        self.lo, self.hi = self.c - r, self.c + r

    def d(self, P, lo=None, hi=None):
        return np.linalg.norm(P - self.c, axis=1) - self.r


class Revolve(Part):
    """세로축(x=cx, z=cz) 회전체. 반지름 r(y, θ)는 radius(y, theta) 함수 (배열 → 배열).

    탑 몸통처럼 높이·각도에 따라 반지름이 변하는 원통. rmax는 r의 최댓값(경계 상자용).
    """

    def __init__(self, y0, y1, radius, rmax, cx=0.0, cz=0.0, lip=1.2):
        self.y0, self.y1, self.radius = float(y0), float(y1), radius
        self.cx, self.cz = float(cx), float(cz)
        self.lo = np.array([cx - rmax, y0, cz - rmax])
        self.hi = np.array([cx + rmax, y1, cz + rmax])
        self.lip = lip

    def polar(self, P):
        dx, dz = P[:, 0] - self.cx, P[:, 2] - self.cz
        return np.hypot(dx, dz), np.arctan2(dz, dx)

    def d(self, P, lo=None, hi=None):
        rho, th = self.polar(P)
        y = P[:, 1]
        dr = rho - self.radius(np.clip(y, self.y0, self.y1), th)
        dy = np.maximum(self.y0 - y, y - self.y1)
        out = np.maximum(dr, dy)
        both = (dr > 0) & (dy > 0)
        out[both] = np.hypot(dr[both], dy[both])
        return out

    def info(self, P):
        rho, th = self.polar(P)
        return {"rho": rho, "theta": th, "y": P[:, 1]}

    def sections(self, margin=2.0):
        # 회전체는 경계 상자보다 원 모양 둘레만: 반지름 rmax 원과 겹치는 섹션
        s = super().sections(margin)
        rmax = float(self.hi[0] - self.cx) + margin
        out = set()
        for (x, y, z) in s:
            # 섹션 사각형과 원 중심 사이 최소 거리
            gx = max(x * 16 - self.cx, 0, self.cx - (x * 16 + 16))
            gz = max(z * 16 - self.cz, 0, self.cz - (z * 16 + 16))
            if math.hypot(gx, gz) <= rmax:
                out.add((x, y, z))
        return out


class Tube(Part):
    """곡선을 따라가는 관 (가지·뿌리·덩굴). points (M,3), radii (M,) — 굵기가 변하는 캡슐들의 합.

    info: s(곡선 길이 위치), tangent(진행 방향), r(그 위치 굵기), off(중심선에서의 벡터)
    """

    def __init__(self, points, radii, lip=1.15, simplify: float = 0.12):
        P = np.asarray(points, float)
        R = np.broadcast_to(np.asarray(radii, float), (len(P),)).copy()
        if len(P) < 2:
            raise ValueError("Tube에는 점이 2개 이상 필요")
        if simplify > 0 and len(P) > 2:  # 곧은 부분의 점을 줄여 계산량 감소 (오차 simplify 칸 이하)
            keep = _simplify(np.concatenate([P, R[:, None]], 1), simplify)
            P, R = P[keep], R[keep]
        self.a, self.b = P[:-1], P[1:]
        self.ra, self.rb = R[:-1], R[1:]
        seg = self.b - self.a
        self.len2 = np.maximum((seg * seg).sum(1), 1e-12)
        self.seglen = np.sqrt(self.len2)
        self.s0 = np.concatenate([[0], np.cumsum(self.seglen)[:-1]])
        self.length = float(self.seglen.sum())
        rmax = np.maximum(self.ra, self.rb)[:, None]
        self.slo = np.minimum(self.a, self.b) - rmax
        self.shi = np.maximum(self.a, self.b) + rmax
        self.lo, self.hi = self.slo.min(0), self.shi.max(0)
        self.lip = lip

    def _segs(self, lo, hi, margin=PRUNE):
        if lo is None:
            return np.arange(len(self.a))
        g = np.maximum(0, np.maximum(self.slo - hi, lo - self.shi))
        return np.nonzero((g * g).sum(1) <= margin * margin)[0]

    def _closest(self, P, idx):
        a, ab = self.a[idx], (self.b - self.a)[idx]
        ap = P[:, None, :] - a[None]
        t = np.clip(np.einsum("nsk,sk->ns", ap, ab) / self.len2[idx][None], 0, 1)
        diff = ap - t[..., None] * ab[None]
        r = self.ra[idx][None] + t * (self.rb - self.ra)[idx][None]
        dist = np.sqrt(np.einsum("nsk,nsk->ns", diff, diff)) - r
        k = dist.argmin(1)
        rows = np.arange(len(P))
        tk = t[rows, k]
        q = a[k] + tk[:, None] * ab[k]
        return dist[rows, k], idx[k], tk, q, r[rows, k]

    def d(self, P, lo=None, hi=None):
        idx = self._segs(lo, hi)
        if len(idx) == 0:
            return np.full(len(P), FAR)
        out = np.empty(len(P))
        for i in range(0, len(P), 4096):  # 메모리 제한
            out[i:i + 4096] = self._closest(P[i:i + 4096], idx)[0]
        return out

    def info(self, P):
        dist, seg, t, q, r = self._closest(P, np.arange(len(self.a)))
        tan = (self.b - self.a)[seg] / self.seglen[seg][:, None]
        return {"s": self.s0[seg] + t * self.seglen[seg], "tangent": tan, "r": r, "off": P - q, "seg": seg}

    def sections(self, margin=2.0):
        out = set()
        for lo, hi in zip(self.slo - margin, self.shi + margin):
            a = np.floor(lo / 16).astype(int)
            b = np.floor(hi / 16).astype(int)
            for x in range(a[0], b[0] + 1):
                for y in range(a[1], b[1] + 1):
                    for z in range(a[2], b[2] + 1):
                        out.add((x, y, z))
        return out


# =================================================================== 곡선 도구

def _simplify(Q: np.ndarray, tol: float) -> np.ndarray:
    """더글러스-포이커: 남길 점 번호 (양 끝 포함). Q (M,k) — 위치+반지름을 같이 봄."""
    keep = np.zeros(len(Q), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(Q) - 1)]
    while stack:
        i, j = stack.pop()
        if j - i < 2:
            continue
        a, b = Q[i], Q[j]
        ab = b - a
        L2 = float(ab @ ab)
        mid = Q[i + 1:j]
        t = np.clip(((mid - a) @ ab) / L2, 0, 1) if L2 > 0 else np.zeros(len(mid))
        dev = np.linalg.norm(mid - (a + t[:, None] * ab), axis=1)
        k = int(dev.argmax())
        if dev[k] > tol:
            m = i + 1 + k
            keep[m] = True
            stack += [(i, m), (m, j)]
    return np.nonzero(keep)[0]


def bezier(p0, p1, p2, p3, n: int = 64) -> np.ndarray:
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = (np.asarray(p, float) for p in (p0, p1, p2, p3))
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


def resample(points, step: float = 1.0) -> np.ndarray:
    """곡선 길이 기준 같은 간격으로 다시 찍기."""
    P = np.asarray(points, float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(2, int(math.ceil(s[-1] / step)) + 1)
    ts = np.linspace(0, s[-1], n)
    return np.stack([np.interp(ts, s, P[:, k]) for k in range(3)], axis=1)


def _unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def curl(start, tangent, bend, R0: float, turns: float = 2.0, shrink: float = 0.55, step: float = 0.5,
         Rmin: float = 1.2) -> np.ndarray:
    """소용돌이(고사리순) 곡선. start에서 tangent 방향으로 출발해 bend 쪽으로 감긴다.

    한 바퀴 돌 때마다 곡률 반지름이 shrink 배로 줄어든다 (로그 나선). 평면 곡선.
    """
    t = _unit(tangent)
    n = _unit(np.asarray(bend, float) - np.dot(bend, t) * t)  # tangent에 수직인 감김 방향
    pts = [np.asarray(start, float)]
    phi, R = 0.0, R0
    total = turns * 2 * math.pi
    k = math.log(shrink) / (2 * math.pi)  # dR/dphi = k R
    while phi < total and R > Rmin:
        dphi = step / R
        phi += dphi
        R = R0 * math.exp(k * phi)
        heading = math.cos(phi) * t + math.sin(phi) * n
        pts.append(pts[-1] + heading * step)
    return np.array(pts)


def join(*curves) -> np.ndarray:
    out = [np.asarray(curves[0], float)]
    for c in curves[1:]:
        c = np.asarray(c, float)
        out.append(c[1:] if np.allclose(c[0], out[-1][-1]) else c)
    return np.concatenate(out)


def taper(points, r0: float, r1: float, power: float = 1.0) -> np.ndarray:
    """곡선 길이에 따라 r0 → r1로 가늘어지는 반지름 배열."""
    P = np.asarray(points, float)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    u = s / max(s[-1], 1e-9)
    return r0 + (r1 - r0) * u ** power


# =================================================================== 칠하기

@dataclass
class Ctx:
    """칠하기 함수에 넘기는 값들 (모두 같은 길이의 배열)."""
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    P: np.ndarray          # 칸 중심 (N,3)
    d: np.ndarray          # 거리 (껍질 깊이: 0에 가까울수록 바깥 면)
    info: dict = field(default_factory=dict)

    def __len__(self):
        return len(self.x)


def solid(state: str):
    return lambda ctx: np.full(len(ctx), state, dtype=object)


def mix(states, weights=None, seed: int = 0, cell: int = 1):
    """칸마다 무작위로 섞기. cell > 1 이면 그 크기 덩어리로."""
    states = list(states)
    w = np.cumsum(weights if weights is not None else [1] * len(states)).astype(float)
    w /= w[-1]
    arr = np.array(states, dtype=object)

    def f(ctx):
        r = hash01(ctx.x // cell, ctx.y // cell, ctx.z // cell, seed=seed)
        return arr[np.searchsorted(w, r, side="right").clip(0, len(arr) - 1)]
    return f


def log_along(state_fmt: str):
    """관 진행 방향으로 원목 축 맞추기. state_fmt 예: 'minecraft:dark_oak_log[axis={a}]'."""
    axes = np.array(["x", "y", "z"], dtype=object)
    names = {a: state_fmt.format(a=a) for a in "xyz"}

    def f(ctx):
        tan = ctx.info.get("tangent")
        if tan is None:
            return np.full(len(ctx), names["y"], dtype=object)
        a = axes[np.abs(tan).argmax(1)]
        return np.vectorize(names.get, otypes=[object])(a)
    return f


# =================================================================== 계단·반블록 판정표

# 8분할(옥탄트) 번호 = ox + 2*oz + 4*oy  (ox: 0=서 1=동, oz: 0=북 1=남, oy: 0=아래 1=위)
# 마인크래프트 StairBlock: 모서리 비트 1=북서 2=북동 4=남서 8=남동, SHAPE_BY_STATE[shape*4 + facing2d]
_FACING2D = ["south", "west", "north", "east"]
_SHAPES = ["straight", "inner_left", "inner_right", "outer_left", "outer_right"]
_SHAPE_BY_STATE = [12, 5, 3, 10, 14, 13, 7, 11, 13, 7, 11, 14, 8, 4, 1, 2, 4, 1, 2, 8]
_QUAD_OCT = {1: (0, 0), 2: (1, 0), 4: (0, 1), 8: (1, 1)}  # 비트 → (ox, oz)


def _oct(ox, oy, oz):
    return 1 << (ox + 2 * oz + 4 * oy)


def _stair_candidates():
    cands = [("air", 0, {}, 0), ("full", 0xFF, {}, 5)]
    cands.append(("slab", sum(_oct(x, 0, z) for x in (0, 1) for z in (0, 1)), {"type": "bottom"}, 1))
    cands.append(("slab", sum(_oct(x, 1, z) for x in (0, 1) for z in (0, 1)), {"type": "top"}, 1))
    for half in ("bottom", "top"):
        base_y, corner_y = (0, 1) if half == "bottom" else (1, 0)
        base = sum(_oct(x, base_y, z) for x in (0, 1) for z in (0, 1))
        for si, shape in enumerate(_SHAPES):
            for fi, facing in enumerate(_FACING2D):
                bits = _SHAPE_BY_STATE[si * 4 + fi]
                m = base
                for b, (ox, oz) in _QUAD_OCT.items():
                    if bits & b:
                        m |= _oct(ox, corner_y, oz)
                pri = 2 if shape == "straight" else 3
                cands.append(("stairs", m, {"facing": facing, "half": half, "shape": shape}, pri))
    return cands


def _build_table():
    cands = _stair_candidates()
    table = []
    for pat in range(256):
        best = min(cands, key=lambda c: (bin(pat ^ c[1]).count("1"), c[3]))
        table.append(best)
    return table


STAIR_TABLE = _build_table()
_KIND = np.array([{"air": 0, "full": 2}.get(c[0], 1) for c in STAIR_TABLE])  # 0 공기, 1 계단·반블록, 2 꽉 찬 블록


def _family_lut(family, dim, cache) -> np.ndarray:
    """패턴(0~255) → 팔레트 번호 (-1 = 안 놓음). 꽉 찬 블록(2)은 따로 칠함."""
    out = np.full(256, -1, dtype=np.int32)
    for pat, (kind, _, props, _) in enumerate(STAIR_TABLE):
        s = stair_state(kind, props, family)
        if s is not None:
            out[pat] = cache.setdefault(s, dim.id(s))
    return out


def stair_state(kind: str, props: dict, family) -> str | None:
    stairs, slab = family
    if kind == "slab":
        return f"{slab}[type={props['type']}]"
    if kind == "stairs":
        return f"{stairs}[facing={props['facing']},half={props['half']},shape={props['shape']}]"
    return None


# =================================================================== 블록으로 만들기

@dataclass
class CarveStats:
    sections: int = 0
    blocks: int = 0
    smooth: int = 0
    skipped: int = 0


def carve(dim, shape: Field, shell: float = 1.0, smooth: bool = True, only_air: bool = False,
          default_paint: str = "minecraft:stone") -> CarveStats:
    """도형을 dim에 블록으로 쓴다.

    shell: 껍질 두께(칸). 바깥 공기와 맞닿은 칸은 항상 포함 (구멍 방지).
    smooth: 부품에 smooth=(계단, 반블록)이 있으면 바깥 가장자리에 계단·반블록을 덧붙임 (공기 칸에만).
    only_air: True면 이미 블록이 있는 칸은 건드리지 않음.
    """
    root = shape if isinstance(shape, Union) else Union(shape)
    parts = root.children
    st = CarveStats()
    ymin, ymax = dim.min_y, dim.min_y + dim.height - 1
    g = np.arange(-1, 17) + 0.5
    GX, GY, GZ = np.meshgrid(g, g, g, indexing="ij")
    base_grid = np.stack([GX.ravel(), GY.ravel(), GZ.ravel()], axis=1)
    sub = (np.arange(4) + 0.5) / 4
    SX, SY, SZ = np.meshgrid(sub, sub, sub, indexing="ij")
    sub_off = np.stack([SX.ravel(), SY.ravel(), SZ.ravel()], axis=1) - 0.5  # (64,3)
    oct_of_sub = ((SX.ravel() > 0.5).astype(int) + 2 * (SZ.ravel() > 0.5) + 4 * (SY.ravel() > 0.5))
    cg = np.arange(6) * 3 - 1 + 1.5  # 묶음 중심 (섹션 원점 기준)
    CX, CY, CZ = np.meshgrid(cg, cg, cg, indexing="ij")
    coarse_grid = np.stack([CX.ravel(), CY.ravel(), CZ.ravel()], axis=1)
    band = root.lip * 2.6 + shell + 2.0  # 묶음 반대각선(1.5√3) × 립시츠 + 껍질 + 여유
    cache: dict[str, int] = {}

    def ids_of(states):
        u, inv = np.unique(states.astype(str), return_inverse=True)
        lut = np.array([cache.setdefault(s, dim.id(s)) for s in u], dtype=np.int32)
        return lut[inv]

    for key in sorted(root.sections(2.0)):
        sx, sy, sz = key
        if sy * 16 + 15 < ymin or sy * 16 > ymax:
            continue
        o = np.array([sx * 16, sy * 16, sz * 16], float)
        lo, hi = o - 1, o + 17
        if not root.near(lo, hi):
            st.skipped += 1
            continue
        P = base_grid + o
        # 1단계: 3칸 묶음(6³) 중심에서 거리 → 표면에서 먼 묶음은 그 값으로 채우고 건너뜀
        dco, oco = root.d_owner(coarse_grid + o, lo, hi)
        need = np.abs(dco) <= band
        if not need.any():
            st.skipped += 1
            continue
        rep = np.repeat(np.repeat(np.repeat(np.arange(216).reshape(6, 6, 6), 3, 0), 3, 1), 3, 2).ravel()
        dd = dco[rep].copy()
        own = oco[rep].copy()
        fine = need[rep]
        dd[fine], own[fine] = root.d_owner(P[fine], lo, hi)
        dd = dd.reshape(18, 18, 18)
        own = own.reshape(18, 18, 18)
        inside = dd <= 0
        core = inside[1:-1, 1:-1, 1:-1]
        if not core.any() and not (smooth and (dd[1:-1, 1:-1, 1:-1] < 1).any()):
            st.skipped += 1
            continue
        enclosed = (inside[:-2, 1:-1, 1:-1] & inside[2:, 1:-1, 1:-1] & inside[1:-1, :-2, 1:-1] &
                    inside[1:-1, 2:, 1:-1] & inside[1:-1, 1:-1, :-2] & inside[1:-1, 1:-1, 2:])
        dc = dd[1:-1, 1:-1, 1:-1]
        oc = own[1:-1, 1:-1, 1:-1]
        mask = core & (~enclosed | (dc > -shell))
        ids = np.full((16, 16, 16), -1, dtype=np.int32)
        Pc = P.reshape(18, 18, 18, 3)[1:-1, 1:-1, 1:-1]
        if mask.any():
            for pi in np.unique(oc[mask]):
                sel = mask & (oc == pi)
                part = parts[pi]
                pts = Pc[sel]
                xi, yi, zi = (np.floor(pts[:, k]).astype(np.int64) for k in range(3))
                ctx = Ctx(xi, yi, zi, pts, dc[sel], part.info(pts) if part.paint is not None else {})
                states = part.paint(ctx) if part.paint is not None else np.full(len(pts), default_paint, object)
                ids[sel] = ids_of(np.asarray(states, dtype=object))
            st.blocks += int(mask.sum())
        if smooth:
            near_in = np.zeros_like(core)
            near_in |= inside[:-2, 1:-1, 1:-1] | inside[2:, 1:-1, 1:-1] | inside[1:-1, :-2, 1:-1]
            near_in |= inside[1:-1, 2:, 1:-1] | inside[1:-1, 1:-1, :-2] | inside[1:-1, 1:-1, 2:]
            cand = ~core & near_in & (dc < 0.9)
            fam_ok = np.array([p.smooth is not None for p in parts] + [False])
            nb_owner = _neighbor_owner(own, inside)
            cand &= fam_ok[np.where(nb_owner >= 0, nb_owner, len(parts))]
            if cand.any():
                cpts = Pc[cand]
                cown = nb_owner[cand]
                S = (cpts[:, None, :] + sub_off[None]).reshape(-1, 3)
                ds = root.d(S, lo, hi).reshape(len(cpts), 64) <= 0
                occ = np.zeros((len(cpts), 8))
                for k in range(8):
                    occ[:, k] = ds[:, oct_of_sub == k].mean(1)
                pat = ((occ >= 0.5) * (1 << np.arange(8))).sum(1).astype(int)
                out = np.full(len(cpts), -1, dtype=np.int32)
                for pi in np.unique(cown):
                    part = parts[pi]
                    lut = _family_lut(part.smooth, dim, cache)
                    sel = cown == pi
                    out[sel] = lut[pat[sel]]
                    full = sel & (_KIND[pat] == 2)
                    if full.any():
                        pt = cpts[full]
                        xi, yi, zi = (np.floor(pt[:, k]).astype(np.int64) for k in range(3))
                        states = part.paint(Ctx(xi, yi, zi, pt, np.zeros(len(pt)), part.info(pt))) \
                            if part.paint else np.full(len(pt), default_paint, object)
                        out[full] = ids_of(np.asarray(states, dtype=object))
                ids[cand] = out
                st.smooth += int((out >= 0).sum())
        if (ids >= 0).any():
            dim.place(sx * 16, sy * 16, sz * 16, ids, only_air=only_air)
            st.sections += 1
    return st


def _neighbor_owner(own, inside):
    """각 칸의 6이웃 중 안쪽 칸의 주인 부품 (없으면 -1)."""
    res = np.full((16, 16, 16), -1, dtype=np.int32)
    for sl in ((slice(0, -2), slice(1, -1), slice(1, -1)), (slice(2, None), slice(1, -1), slice(1, -1)),
               (slice(1, -1), slice(0, -2), slice(1, -1)), (slice(1, -1), slice(2, None), slice(1, -1)),
               (slice(1, -1), slice(1, -1), slice(0, -2)), (slice(1, -1), slice(1, -1), slice(2, None))):
        m = inside[sl] & (res < 0)
        res[m] = own[sl][m]
    return res
