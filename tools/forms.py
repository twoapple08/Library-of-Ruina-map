"""자유 형체 (모드 블록 `ruina:form` 이 그리는 3D 면) — 모든 공간 공용 기반.

흐름
1. 빌더가 형체를 만든다: `q = forms.sweep(...)`, `forms.plane(...)`, ... (사각형 면 묶음 `Quads`)
   - 면 하나 = 꼭짓점 4개 (삼각형은 마지막 점을 겹침). 앞면 = 바깥에서 볼 때 반시계 (뒷면은 안 그림 → `two_sided`)
   - 텍스처 좌표(UV)는 '타일 단위' (0~1 = 텍스처 한 장). 면 하나는 타일 경계를 넘으면 안 됨 → 격자 함수가 맞춰 줌
   - 재질 `mat(...)`: 스프라이트(블록 아틀라스), 그리기 층(solid·cutout·translucent), 스스로 빛남, AO, 평면 음영 끔, BSL 빛 색
2. `b.form(space).add(q)` 로 공간에 넣음. 원화 투영은 `project_art(...)` (도착 시점 카메라에서 원화를 보이는 면에 입힘)
3. `finalize` (build_all 끝): 면을 1칸 이하로 나누고 중심이 든 칸에 배정 (칸이 보이는 블록이면 법선 쪽 빈 칸으로 옮김)
   → 그 칸 = 형체 블록 자리. 블록 자리 표시: 빈 칸은 공기, 충돌 칸은 `minecraft:barrier`, 빛 칸은 `minecraft:light`
   (바닐라 서버가 검증·조명 계산을 그대로 하도록) → 서버 저장 뒤 `inject` 가 리전 파일에서 `ruina:form[...]` 으로 바꿈
4. `write_assets`: 모드 리소스 `assets/ruina/forms/<공간>/r.<rx>.<rz>.bin` (리전 512×512 단위, 클라이언트가 필요할 때 읽음),
   `forms/materials.json`, 움직이는 형체 `movers.json`+`mesh_<n>.bin`, 종이 파티클 `emitters.json`, 텍스처 `textures/block/form/`

파일 형식 (little-endian, Java `FormData` 와 같아야 함)
  "RFM1", f32 scale(블록당 단위), u32 칸 수, 칸마다 (i32 x, i32 y, i32 z, i32 시작 면, i32 면 수) — x,y,z 순 정렬 아님(BlockPos.asLong 정렬)
  면마다 u16 재질, u16 0, 꼭짓점 4개 × (i16 x,y,z (칸 원점 기준 × scale), u16 u,v (스프라이트 안 0~1 × 65535),
  u32 ARGB, i8 nx,ny,nz, u8 0) = 76바이트
"""
from __future__ import annotations

import json
import math
import os
import struct
from dataclasses import dataclass, field

import numpy as np

MAGIC = b"RFM1"
QUAD_BYTES = 76
CELL_SCALE = 1024.0          # 칸 파일: 1/1024 블록 (i16 → ±32블록까지)
MAX_EDGE = 1.0               # 칸 배정 전 면 최대 변 길이 (블록)
FORM_BLOCK = "ruina:form"
MOVER_BLOCK = "ruina:mover"
BARRIER = "minecraft:barrier"
LAYERS = ("solid", "cutout", "translucent")


# ====================================================================== 재질

@dataclass
class Material:
    name: str
    sprite: str                 # 블록 아틀라스 스프라이트 (예: ruina:block/form/book_spine, minecraft:block/stone)
    layer: str = "solid"        # solid | cutout | translucent
    emissive: bool = False      # 월드 빛과 상관없이 밝게 (원화 투영·빛나는 것)
    ao: bool = True             # 블록 그림자(AO)
    flat: bool = False          # 방향별 어둡게 하기 끔 (원화 색 그대로)
    glow: int = 0               # BSL 빛 색 번호 (config.SHADER_GLOW_COLORS, 약한 빛 +25). 0 = 안 빛남

    def json(self):
        return {"name": self.name, "sprite": self.sprite, "layer": self.layer, "emissive": self.emissive,
                "ao": self.ao, "flat": self.flat}


MATERIALS: list[Material] = []
_MAT_INDEX: dict[str, int] = {}
TEXTURES: dict[str, object] = {}   # 이름 → PIL 이미지 (ruina:block/form/<이름>)


def mat(name: str, sprite: str | None = None, **kw) -> int:
    """재질 번호. 처음 부를 때 정의 (같은 이름을 다른 설정으로 다시 정의하면 오류)."""
    if name in _MAT_INDEX:
        i = _MAT_INDEX[name]
        if sprite is not None or kw:
            m = Material(name, sprite or MATERIALS[i].sprite, **kw)
            if m != MATERIALS[i]:
                raise ValueError(f"재질 {name} 을 다르게 다시 정의함")
        return i
    if sprite is None:
        raise KeyError(f"재질 {name} 정의 안 됨")
    m = Material(name, sprite, **kw)
    if m.layer not in LAYERS:
        raise ValueError(m.layer)
    _MAT_INDEX[name] = len(MATERIALS)
    MATERIALS.append(m)
    return _MAT_INDEX[name]


def texture(name: str, img) -> str:
    """모드 텍스처 등록 (PIL 이미지, 한 변은 2의 거듭제곱 권장). 반환: 스프라이트 이름."""
    TEXTURES[name] = img
    return f"ruina:block/form/{name}"


def reset():
    MATERIALS.clear()
    _MAT_INDEX.clear()
    TEXTURES.clear()


# ====================================================================== 면 묶음

class Quads:
    """P (n,4,3) 위치, UV (n,4,2) 타일 단위, C (n,4,4) RGBA 0~1, N (n,4,3) 법선, M (n,) 재질."""

    def __init__(self, P=None, UV=None, C=None, N=None, M=None):
        n = 0 if P is None else len(P)
        self.P = np.zeros((0, 4, 3)) if P is None else np.asarray(P, np.float64).reshape(n, 4, 3)
        self.UV = np.zeros((n, 4, 2)) if UV is None else np.asarray(UV, np.float64).reshape(n, 4, 2)
        if C is None:
            self.C = np.ones((n, 4, 4))
        else:
            C = np.asarray(C, np.float64)
            if C.shape[-1] == 3:
                C = np.concatenate([C, np.ones(C.shape[:-1] + (1,))], -1)
            self.C = np.broadcast_to(C, (n, 4, 4)).copy() if C.ndim < 3 else C.reshape(n, 4, 4).copy()
        self.N = face_normals(self.P)[:, None, :].repeat(4, 1) if N is None else np.asarray(N, np.float64).reshape(n, 4, 3)
        self.M = np.zeros(n, np.int32) if M is None else np.broadcast_to(np.asarray(M, np.int32), (n,)).copy()

    def __len__(self):
        return len(self.P)

    def __add__(self, o: "Quads") -> "Quads":
        return concat([self, o])

    def copy(self) -> "Quads":
        return Quads(self.P.copy(), self.UV.copy(), self.C.copy(), self.N.copy(), self.M.copy())

    def take(self, idx) -> "Quads":
        return Quads(self.P[idx], self.UV[idx], self.C[idx], self.N[idx], self.M[idx])

    # ---------------------------------------------- 변형
    def transform(self, R=np.eye(3), t=(0, 0, 0), origin=(0, 0, 0)) -> "Quads":
        R = np.asarray(R, float)
        o = np.asarray(origin, float)
        q = self.copy()
        q.P = (self.P - o) @ R.T + o + np.asarray(t, float)
        Nn = self.N @ np.linalg.inv(R)          # 법선은 역전치
        q.N = _unit(Nn)
        if np.linalg.det(R) < 0:                 # 거울 변환이면 앞뒤가 바뀜 → 순서 뒤집기
            q = q.flipped()
            q.N = -q.N
        return q

    def translate(self, t) -> "Quads":
        return self.transform(t=t)

    def rotate(self, axis, deg: float, origin=(0, 0, 0)) -> "Quads":
        return self.transform(rot(axis, deg), origin=origin)

    def scale(self, s, origin=(0, 0, 0)) -> "Quads":
        return self.transform(np.diag(np.broadcast_to(np.asarray(s, float), (3,))), origin=origin)

    def flipped(self) -> "Quads":
        """앞뒤 뒤집기 (꼭짓점 순서 0,3,2,1, 법선 반대)."""
        o = [0, 3, 2, 1]
        return Quads(self.P[:, o], self.UV[:, o], self.C[:, o], -self.N[:, o], self.M)

    # ---------------------------------------------- 색
    def tint(self, rgb, a: float | None = None) -> "Quads":
        q = self.copy()
        q.C[..., :3] *= np.asarray(rgb, float)
        if a is not None:
            q.C[..., 3] = a
        return q

    def color_by(self, fn) -> "Quads":
        """fn(P (k,3), N (k,3)) → RGB 배수 (k,3) 또는 RGBA (k,4). 꼭짓점마다."""
        q = self.copy()
        k = q.P.reshape(-1, 3)
        c = np.asarray(fn(k, q.N.reshape(-1, 3)), float)
        c = c.reshape(len(q), 4, -1)
        q.C[..., :c.shape[-1]] *= c
        return q

    def with_mat(self, m: int) -> "Quads":
        q = self.copy()
        q.M[:] = m
        return q

    def bounds(self):
        P = self.P.reshape(-1, 3)
        return P.min(0), P.max(0)


def concat(qs) -> Quads:
    qs = [q for q in qs if q is not None and len(q)]
    if not qs:
        return Quads()
    return Quads(np.concatenate([q.P for q in qs]), np.concatenate([q.UV for q in qs]),
                 np.concatenate([q.C for q in qs]), np.concatenate([q.N for q in qs]),
                 np.concatenate([q.M for q in qs]))


def two_sided(q: Quads) -> Quads:
    return concat([q, q.flipped()])


# ====================================================================== 수학

def _unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.where(n < 1e-12, 1, n)


def rot(axis, deg: float) -> np.ndarray:
    """축 (x,y,z 또는 'x'·'y'·'z') 둘레로 deg 도 (오른손 법칙)."""
    if isinstance(axis, str):
        axis = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis]
    a = _unit(np.asarray(axis, float))
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    x, y, z = a
    return np.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                     [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                     [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])


def face_normals(P) -> np.ndarray:
    """사각형 면 법선 (두 대각선 외적 → 비평면·삼각형도 안정)."""
    P = np.asarray(P, float)
    return _unit(np.cross(P[:, 2] - P[:, 0], P[:, 3] - P[:, 1]))


# ====================================================================== 기본 도형

def grid(G, UV, mat_id: int, N=None, C=None, wrap_v: bool = False) -> Quads:
    """격자 곡면 G (a+1, b+1, 3) → 면 a×b. UV (a+1, b+1, 2) 타일 단위.
    N: 꼭짓점 법선 (없으면 격자에서 계산). 면 방향은 N 쪽이 앞이 되게 자동으로 맞춤.
    한 면의 UV 가 타일 경계를 넘지 않게 격자를 만들 것 (tiles_steps)."""
    G = np.asarray(G, float)
    UV = np.asarray(UV, float)
    a, b = G.shape[0] - 1, G.shape[1] - 1
    if N is None:
        du = np.gradient(G, axis=0)
        dv = np.gradient(G, axis=1)
        N = _unit(np.cross(du, dv))
    N = np.asarray(N, float)
    i, j = np.meshgrid(np.arange(a), np.arange(b), indexing="ij")
    i, j = i.ravel(), j.ravel()
    ci = np.stack([i, i + 1, i + 1, i], 1)
    cj = np.stack([j, j, j + 1, j + 1], 1)
    P = G[ci, cj]
    q = Quads(P, UV[ci, cj], None if C is None else np.asarray(C, float)[ci, cj], N[ci, cj], mat_id)
    fn = face_normals(q.P)
    back = (fn * q.N.mean(1)).sum(-1) < 0
    if back.any():
        f = q.take(back).flipped()
        f.N = -f.N                      # flipped 가 법선을 뒤집으므로 원래 법선으로
        q = concat([q.take(~back), f])
    return q


def tiles_steps(length: float, tile: float, per_tile: int) -> tuple[int, float]:
    """길이를 타일(tile 블록) 단위로 나눈 칸 수와 타일 수: (구간 수, 타일 수). 타일 경계는 항상 구간 경계."""
    tiles = max(1, round(length / tile))
    return tiles * per_tile, float(tiles)


def plane(origin, du, dv, mat_id: int, tile=(1.0, 1.0), per_tile: int = 1) -> Quads:
    """평행사변형 origin + s·du + t·dv (s,t ∈ 0~1). 앞 = du × dv 쪽."""
    o, du, dv = (np.asarray(v, float) for v in (origin, du, dv))
    nu, tu = tiles_steps(np.linalg.norm(du), tile[0], per_tile)
    nv, tv = tiles_steps(np.linalg.norm(dv), tile[1], per_tile)
    s = np.linspace(0, 1, nu + 1)[:, None, None]
    t = np.linspace(0, 1, nv + 1)[None, :, None]
    G = o + s * du + t * dv
    UV = np.concatenate([np.broadcast_to(s * tu, G.shape[:2] + (1,)), np.broadcast_to(t * tv, G.shape[:2] + (1,))], -1)
    n = _unit(np.cross(du, dv))
    return grid(G, UV, mat_id, np.broadcast_to(n, G.shape))


def box(lo, hi, mat_id: int, tile: float = 1.0, faces: str = "xXyYzZ") -> Quads:
    """상자 (바깥 면). faces: x=-x X=+x y=-y Y=+y z=-z Z=+z."""
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
    f = {
        "x": ((x0, y0, z0), (0, 0, sz), (0, sy, 0)),
        "X": ((x1, y0, z1), (0, 0, -sz), (0, sy, 0)),
        "y": ((x0, y0, z0), (sx, 0, 0), (0, 0, sz)),
        "Y": ((x0, y1, z1), (sx, 0, 0), (0, 0, -sz)),
        "z": ((x1, y0, z0), (-sx, 0, 0), (0, sy, 0)),
        "Z": ((x0, y0, z1), (sx, 0, 0), (0, sy, 0)),
    }
    return concat([plane(*f[k], mat_id, (tile, tile)) for k in faces])


def frames(path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """곡선의 회전 최소 틀 (접선 T, 법선 Nn, 종법선 B) — 이중 반사법."""
    path = np.asarray(path, float)
    T = _unit(np.gradient(path, axis=0))
    Nn = np.zeros_like(path)
    a = np.array([0, 1, 0]) if abs(T[0][1]) < 0.9 else np.array([1, 0, 0])
    Nn[0] = _unit(np.cross(np.cross(T[0], a), T[0]))
    for i in range(len(path) - 1):
        v1 = path[i + 1] - path[i]
        c1 = v1 @ v1
        if c1 < 1e-12:
            Nn[i + 1] = Nn[i]
            continue
        rL = Nn[i] - (2 / c1) * (v1 @ Nn[i]) * v1
        tL = T[i] - (2 / c1) * (v1 @ T[i]) * v1
        v2 = T[i + 1] - tL
        c2 = v2 @ v2
        Nn[i + 1] = rL - (2 / c2) * (v2 @ rL) * v2 if c2 > 1e-12 else rL
    Nn = _unit(Nn)
    return T, Nn, np.cross(T, Nn)


def resample(path, step: float) -> np.ndarray:
    path = np.asarray(path, float)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    n = max(2, int(math.ceil(d[-1] / step)) + 1)
    s = np.linspace(0, d[-1], n)
    return np.stack([np.interp(s, d, path[:, k]) for k in range(3)], 1)


def sweep(path, radius, mat_id: int, sides: int = 8, step: float = 0.5, tile_along: float = 2.0,
          tiles_around: int = 1, twist: float = 0.0, profile=None, squash=1.0) -> Quads:
    """곡선을 따라 단면을 쓸기 (가지·관·뿔). radius: 수 또는 경로 비율 t(0~1) → 반지름 함수.
    profile: 단면 모양 함수 θ → 반지름 배수 (예: 마디·홈). twist: 끝까지 비트는 각도(도). squash: 단면 납작함 (B 방향 배수).
    텍스처: 길이 방향 tile_along 블록마다 한 장, 둘레 tiles_around 장."""
    path = resample(path, step)
    n = len(path)
    t = np.linspace(0, 1, n)
    r = radius(t) if callable(radius) else np.full(n, float(radius))
    per = max(1, int(round(tile_along / step)))
    extra = (-n + 1) % per                       # 길이 방향 구간 수를 타일 배수로 (끝을 살짝 늘려 맞춤)
    if extra:
        path = np.vstack([path, path[-1] + (path[-1] - path[-2]) * np.arange(1, extra + 1)[:, None] * 1e-3])
        r = np.r_[r, np.full(extra, r[-1])]
        n = len(path)
    T, Nn, B = frames(path)
    sides = int(math.ceil(sides / tiles_around) * tiles_around)
    th = np.linspace(0, 2 * math.pi, sides + 1)[None, :] + np.radians(twist) * np.linspace(0, 1, n)[:, None]
    pr = np.asarray(profile(th), float)[..., None] if profile else 1.0
    off = np.cos(th)[..., None] * Nn[:, None] + (np.sin(th)[..., None] * squash) * B[:, None]
    G = path[:, None] + off * r[:, None, None] * pr
    Nv = _unit(np.cos(th)[..., None] * Nn[:, None] * squash + np.sin(th)[..., None] * B[:, None])
    u = (np.arange(n) / per)[:, None].repeat(sides + 1, 1)
    v = (np.arange(sides + 1) / sides * tiles_around)[None, :].repeat(n, 0)
    return grid(G, np.stack([u, v], -1), mat_id, Nv)


def revolve(profile, mat_id: int, segs: int = 32, center=(0, 0, 0), tiles_around: int = 4, tile_up: float = 2.0,
            arc=(0.0, 360.0)) -> Quads:
    """단면 [(r, y), ...] (아래→위) 를 y축 둘레로 돌린 면 (탑·기둥·돔). 바깥이 앞."""
    pr = np.asarray(profile, float)
    seg_len = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pr, axis=0), axis=1))]
    segs = int(math.ceil(segs / tiles_around) * tiles_around)
    a = np.radians(np.linspace(arc[0], arc[1], segs + 1))
    c = np.asarray(center, float)
    G = np.stack([c[0] + pr[:, :1] * np.cos(a)[None], c[1] + pr[:, 1:2] + 0 * a[None], c[2] + pr[:, :1] * np.sin(a)[None]], -1)
    d = np.gradient(pr, axis=0)                     # 단면 접선 (dr, dy) → 바깥 법선 (dy, -dr)
    nr, ny = d[:, 1], -d[:, 0]
    N = _unit(np.stack([nr[:, None] * np.cos(a)[None], ny[:, None] + 0 * a[None], nr[:, None] * np.sin(a)[None]], -1))
    u = (np.arange(segs + 1) / segs * tiles_around * (arc[1] - arc[0]) / 360)[None, :].repeat(len(pr), 0)
    v = (seg_len / tile_up)[:, None].repeat(segs + 1, 1)
    q = grid(G, np.stack([u, v], -1), mat_id, N)
    return fit_tiles(q)


def heightfield(x0: float, z0: float, x1: float, z1: float, fy, mat_id: int, step: float = 1.0, tile: float = 4.0) -> Quads:
    """지면 y = fy(X, Z) (위가 앞)."""
    nx = max(1, int(round((x1 - x0) / step)))
    nz = max(1, int(round((z1 - z0) / step)))
    X, Z = np.meshgrid(np.linspace(x0, x1, nx + 1), np.linspace(z0, z1, nz + 1), indexing="ij")
    Y = fy(X, Z)
    G = np.stack([X, Y, Z], -1)
    dYx = np.gradient(Y, axis=0) / ((x1 - x0) / nx)
    dYz = np.gradient(Y, axis=1) / ((z1 - z0) / nz)
    N = _unit(np.stack([-dYx, np.ones_like(Y), -dYz], -1))
    return fit_tiles(grid(G, np.stack([X / tile, Z / tile], -1), mat_id, N))


def ribbon(path, width, mat_id: int, up=None, step: float = 0.5, tile_along: float = 2.0, twist: float = 0.0) -> Quads:
    """띠 (종이·천·깃발). up: 폭 방향 기준 (없으면 회전 최소 틀). 양면."""
    path = resample(path, step)
    n = len(path)
    t = np.linspace(0, 1, n)
    w = width(t) if callable(width) else np.full(n, float(width))
    T, Nn, B = frames(path)
    side = Nn if up is None else _unit(np.cross(T, np.asarray(up, float)))
    if twist:
        ang = np.radians(twist) * t
        side = _unit(side * np.cos(ang)[:, None] + np.cross(T, side) * np.sin(ang)[:, None])
    G = np.stack([path - side * w[:, None] / 2, path + side * w[:, None] / 2], 1)
    u = (np.arange(n) * step / tile_along)[:, None].repeat(2, 1)
    v = np.array([[0.0, 1.0]]).repeat(n, 0)
    Nv = _unit(np.cross(T, side))[:, None].repeat(2, 1)
    return two_sided(fit_tiles(grid(G, np.stack([u, v], -1), mat_id, Nv)))


def ellipsoid(center, radii, mat_id: int, segs: int = 16, rings: int = 8) -> Quads:
    rx, ry, rz = radii
    phi = np.linspace(-math.pi / 2, math.pi / 2, rings + 1)
    prof = np.stack([np.cos(phi), np.sin(phi)], 1)
    q = revolve(prof, mat_id, segs, (0, 0, 0), tiles_around=1, tile_up=4.0)
    return q.scale((rx, ry, rz)).translate(center)


def fit_tiles(q: Quads, max_split: int = 6) -> Quads:
    """타일 경계를 넘는 면을 반으로 나눠 경계에 맞춤 (UV 가 직선 비례인 면 기준, 몇 번까지)."""
    for _ in range(max_split):
        lo = np.floor(q.UV.min(1) + 1e-6)
        bad = (q.UV.max(1) - lo > 1 + 1e-6).any(1)
        if not bad.any():
            break
        qb = q.take(bad)
        span = qb.UV.max(1) - qb.UV.min(1)
        ax = (span[:, 1] > span[:, 0]).astype(int)                 # 넘치는 UV 축
        r = np.arange(len(qb))
        d01 = np.abs(qb.UV[r, 1, ax] - qb.UV[r, 0, ax]) + np.abs(qb.UV[r, 2, ax] - qb.UV[r, 3, ax])
        d03 = np.abs(qb.UV[r, 3, ax] - qb.UV[r, 0, ax]) + np.abs(qb.UV[r, 2, ax] - qb.UV[r, 1, ax])
        along01 = d01 >= d03                                        # 그 축이 0-1 변을 따라 변함 → 0-1 변을 반으로
        parts = [q.take(~bad)]
        for which, m in ((0, along01), (1, ~along01)):
            if m.any():
                parts += _split(qb.take(m), which)
        q = concat(parts)
    return q


def _split(q: Quads, which: int):
    """면을 둘로: which=0 → 꼭짓점 0-1·3-2 변 가운데, 1 → 0-3·1-2 변 가운데."""
    def mid(A, i, j):
        return (A[:, i] + A[:, j]) / 2
    out = []
    if which == 0:
        a, b = (0, 1), (3, 2)
        idx1 = lambda A, m1, m2: np.stack([A[:, 0], m1, m2, A[:, 3]], 1)
        idx2 = lambda A, m1, m2: np.stack([m1, A[:, 1], A[:, 2], m2], 1)
    else:
        a, b = (0, 3), (1, 2)
        idx1 = lambda A, m1, m2: np.stack([A[:, 0], A[:, 1], m2, m1], 1)
        idx2 = lambda A, m1, m2: np.stack([m1, m2, A[:, 2], A[:, 3]], 1)
    for f in (idx1, idx2):
        arrs = []
        for A in (q.P, q.UV, q.C, q.N):
            arrs.append(f(A, mid(A, *a), mid(A, *b)))
        out.append(Quads(*arrs, q.M))
    return out


def subdivide(q: Quads, max_edge: float = MAX_EDGE) -> Quads:
    """변이 max_edge 보다 긴 면을 계속 반으로 (칸 배정용)."""
    done = []
    for _ in range(24):
        if not len(q):
            break
        e01 = np.maximum(np.linalg.norm(q.P[:, 1] - q.P[:, 0], axis=1), np.linalg.norm(q.P[:, 2] - q.P[:, 3], axis=1))
        e03 = np.maximum(np.linalg.norm(q.P[:, 3] - q.P[:, 0], axis=1), np.linalg.norm(q.P[:, 2] - q.P[:, 1], axis=1))
        ok = (e01 <= max_edge) & (e03 <= max_edge)
        done.append(q.take(ok))
        rest = ~ok
        su = rest & (e01 >= e03)
        sv = rest & ~su
        parts = []
        if su.any():
            parts += _split(q.take(su), 0)
        if sv.any():
            parts += _split(q.take(sv), 1)
        q = concat(parts)
    done.append(q)
    return concat(done)


# ====================================================================== 음영 굽기 (원화 느낌: 빛을 색에 미리)

def bake_light(q: Quads, sun=(-0.4, 0.8, 0.45), sun_rgb=(1.0, 0.95, 0.85), sky_rgb=(0.45, 0.42, 0.6),
               ground_rgb=(0.18, 0.15, 0.2), strength: float = 1.0) -> Quads:
    """반구 빛 + 해 방향 램버트를 꼭짓점 색에 곱함 (emissive·flat 재질용: 모양이 읽히게)."""
    s = _unit(np.asarray(sun, float))
    def fn(P, N):
        lam = np.clip(N @ s, 0, 1)[:, None]
        hemi = (N[:, 1:2] + 1) / 2
        c = np.asarray(sky_rgb) * hemi + np.asarray(ground_rgb) * (1 - hemi) + np.asarray(sun_rgb) * lam
        return 1 + (c - 1) * strength
    return q.color_by(fn)


def gradient_y(q: Quads, y0: float, y1: float, c0, c1) -> Quads:
    """높이에 따라 색 배수 (아래 c0 → 위 c1)."""
    c0, c1 = np.asarray(c0, float), np.asarray(c1, float)
    return q.color_by(lambda P, N: c0 + (c1 - c0) * np.clip((P[:, 1:2] - y0) / (y1 - y0), 0, 1))


# ====================================================================== 카메라·원화 투영

@dataclass
class Camera:
    """마인크래프트 시점. yaw: 0=남(+z) 90=서(-x) 180=북 270=동, pitch: 아래가 +. fov: 세로 시야각(도, 게임 기본 70).
    pos 는 눈 위치 (발 + 1.62)."""
    pos: tuple
    yaw: float
    pitch: float = 0.0
    fov: float = 70.0
    aspect: float = 16 / 9

    @staticmethod
    def look_at(pos, target, fov=70.0, aspect=16 / 9) -> "Camera":
        d = np.asarray(target, float) - np.asarray(pos, float)
        yaw = math.degrees(math.atan2(-d[0], d[2]))
        pitch = -math.degrees(math.atan2(d[1], math.hypot(d[0], d[2])))
        return Camera(tuple(pos), yaw, pitch, fov, aspect)

    def basis(self):
        y, p = math.radians(self.yaw), math.radians(self.pitch)
        f = np.array([-math.sin(y) * math.cos(p), -math.sin(p), math.cos(y) * math.cos(p)])
        right = _unit(np.cross(f, [0, 1, 0]))
        up = np.cross(right, f)
        return f, right, up

    def project(self, P):
        """P (...,3) → (sx, sy, depth): sx,sy 0~1 (왼쪽 위 0,0), depth = 앞 방향 거리."""
        f, r, u = self.basis()
        V = np.asarray(P, float) - np.asarray(self.pos, float)
        z = V @ f
        th = math.tan(math.radians(self.fov) / 2)
        zz = np.where(z > 1e-6, z, 1e-6)
        sx = 0.5 + (V @ r) / (zz * th * self.aspect) / 2
        sy = 0.5 - (V @ u) / (zz * th) / 2
        return sx, sy, z

    def mc(self) -> str:
        """게임 명령: /tp @s x y z yaw pitch (발 위치)."""
        x, y, z = self.pos
        return f"tp @s {x:.2f} {y - 1.62:.2f} {z:.2f} {self.yaw:.1f} {self.pitch:.1f}"


def _splat_points(qs: list[Quads], cam: Camera, W: int, H: int, max_n: int = 40, density: float = 1.1):
    """면들을 화면 크기에 맞춰 점으로 촘촘히 → (픽셀 번호, 깊이, 면 번호, s, t)."""
    q = concat(qs)
    if not len(q):
        return q, [np.zeros(0, int)] * 5
    sx, sy, z = cam.project(q.P)
    front = (z > 0.05).all(1)
    px = np.stack([sx * W, sy * H], -1)
    edge = np.maximum(np.linalg.norm(px[:, 1] - px[:, 0], axis=1), np.linalg.norm(px[:, 3] - px[:, 0], axis=1))
    edge = np.maximum(edge, np.maximum(np.linalg.norm(px[:, 2] - px[:, 1], axis=1), np.linalg.norm(px[:, 2] - px[:, 3], axis=1)))
    onscreen = front & (px[..., 0].max(1) >= 0) & (px[..., 0].min(1) < W) & (px[..., 1].max(1) >= 0) & (px[..., 1].min(1) < H)
    # 화면 안에 보이는 크기만큼만 (화면 밖으로 크게 걸친 면은 화면 크기로 제한)
    vis = np.minimum(edge, max(W, H))
    n = np.clip(np.ceil(vis * density).astype(int) + 1, 2, max_n)
    outs = [[], [], [], [], []]
    f, r, u = cam.basis()
    th = math.tan(math.radians(cam.fov) / 2)
    for k in np.unique(n[onscreen]):
        idx = np.flatnonzero(onscreen & (n == k))
        s, t = np.meshgrid(np.linspace(0, 1, k), np.linspace(0, 1, k), indexing="ij")
        s, t = s.ravel(), t.ravel()
        Wt = np.stack([(1 - s) * (1 - t), s * (1 - t), s * t, (1 - s) * t], 1)          # (k², 4)
        step = max(1, 1_500_000 // (k * k))
        for c0 in range(0, len(idx), step):
            ii = idx[c0:c0 + step]
            V = q.P[ii] - np.asarray(cam.pos, float)                                     # (m,4,3)
            Vc = np.stack([V @ r, V @ u, V @ f], -1)                                     # 카메라 좌표 (m,4,3)
            Q = np.einsum("sk,mkc->msc", Wt, Vc)                                         # (m,k²,3)
            Z = Q[..., 2]
            zz = np.where(Z > 1e-6, Z, 1e-6)
            xi = np.floor((0.5 + Q[..., 0] / (zz * th * cam.aspect) / 2) * W).astype(np.int64)
            yi = np.floor((0.5 - Q[..., 1] / (zz * th) / 2) * H).astype(np.int64)
            ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H) & (Z > 0.05)
            outs[0].append((yi * W + xi)[ok])
            outs[1].append(Z[ok])
            outs[2].append(np.broadcast_to(ii[:, None], ok.shape)[ok])
            outs[3].append(np.broadcast_to(s[None], ok.shape)[ok])
            outs[4].append(np.broadcast_to(t[None], ok.shape)[ok])
    return q, [np.concatenate(o) if o else np.zeros(0) for o in outs]


def zbuffer(qs: list[Quads], cam: Camera, W: int = 640, H: int = 360) -> np.ndarray:
    _, (pix, z, *_r) = _splat_points(qs, cam, W, H)
    zb = np.full(W * H, np.inf)
    np.minimum.at(zb, pix.astype(int), z)
    return zb.reshape(H, W)


def project_scene(parts: list[Quads], cam: Camera, art_mat: int, occluders: list[Quads] = (), zres=(640, 360),
                  **kw) -> list[Quads]:
    """여러 면 묶음에 한꺼번에 원화 투영 (Z버퍼 한 번). 반환: 투영한 면 묶음들 (같은 순서)."""
    zb = zbuffer([*parts, *occluders], cam, *zres)
    return [project_art(q, cam, art_mat, zres=zres, zb=zb, **kw)[0] for q in parts]


def project_art(target: Quads, cam: Camera, art_mat: int, occluders: list[Quads] = (), zres=(640, 360),
                tol: float = 0.02, min_facing: float = 0.02, margin: float = 0.03, keep_color: bool = False,
                zb: np.ndarray | None = None) -> tuple[Quads, np.ndarray]:
    """원화 투영: 카메라에서 보이는 target 면에 원화(art_mat 의 스프라이트)를 화면 좌표로 입힘.
    occluders: 가리는 면 (target 은 자동 포함). zb: 미리 만든 Z버퍼 (project_scene). 반환: (새 면 묶음, 투영된 면 표시 bool).
    보이지 않거나 화면 밖 면은 원래 재질 그대로 (뒷면·가린 곳은 직접 만든 텍스처)."""
    W, H = zres
    if zb is None:
        zb = zbuffer([target, *occluders], cam, W, H)
    sx, sy, z = cam.project(target.P)
    inside = ((sx >= -margin) & (sx <= 1 + margin) & (sy >= -margin) & (sy <= 1 + margin) & (z > 0.05)).all(1)
    view = _unit(np.asarray(cam.pos, float) - target.P.mean(1))
    cosv = (face_normals(target.P) * view).sum(-1)
    facing = cosv > min_facing
    # 보임: 중심 + 꼭짓점 4개(중심 쪽으로 20%) 중 4개 이상이 Z버퍼와 같은 깊이
    S = np.concatenate([target.P.mean(1, keepdims=True), target.P * 0.8 + target.P.mean(1, keepdims=True) * 0.2], 1)
    X, Y, Z = cam.project(S)
    xi = np.clip((X * W).astype(int), 0, W - 1)
    yi = np.clip((Y * H).astype(int), 0, H - 1)
    # 허용 깊이: 픽셀 하나가 덮는 깊이 차 (비스듬한 면일수록 큼) + 여유
    pix = 2 * math.tan(math.radians(cam.fov) / 2) / H
    slack = (2.0 * Z * pix / np.maximum(cosv, 0.05)[:, None]) + Z * tol + 0.15
    seen = (Z <= zb[yi, xi] + slack).sum(1) >= 4
    sel = inside & facing & seen
    q = target.copy()
    q.M[sel] = art_mat
    q.UV[sel] = np.stack([np.clip(sx[sel], 0, 1), np.clip(sy[sel], 0, 1)], -1)
    if not keep_color:
        q.C[sel] = 1.0
    return q, sel


# ====================================================================== 움직임·파티클

@dataclass
class Mover:
    """움직이는 형체 (블록 엔티티 렌더러가 매 프레임 그림). pos = 블록 칸 (빈 칸이어야 함).
    mesh 는 pivot(월드 좌표) 기준으로 옮겨 저장. motion: spin(축 회전) | swing(진자, amp 도) | bob(위아래, amp 블록) |
    follow(카메라를 따라오는 먼 배경: 하늘 그림·먼 산 등, mesh 는 카메라 기준 좌표) | still"""
    pos: tuple
    mesh: Quads
    pivot: tuple
    motion: str = "spin"
    axis: tuple = (0, 1, 0)
    period: float = 20.0        # 초 (spin: 한 바퀴, swing/bob: 왕복)
    amp: float = 15.0
    phase: float = 0.0          # 0~1
    radius: float = 0.0         # 그리기 범위 반지름 (0 = 메시에서 계산)


@dataclass
class Emitter:
    """종이 등 날리는 파티클. box = (x0,y0,z0,x1,y1,z1) 안에서 생겨 떨어짐/날림.
    rate: 초당 개수 (플레이어 64블록 안일 때만), wind: 바람 (블록/초), sprites: 스프라이트 이름들."""
    box: tuple
    rate: float = 4.0
    sprites: tuple = ("ruina:block/form/paper_0",)
    wind: tuple = (0.0, -0.6, 0.0)
    size: float = 0.35
    life: float = 12.0          # 초
    spin: float = 1.0           # 팔랑거림 세기
    color: tuple = (1.0, 1.0, 1.0)
    glow: bool = False


# ====================================================================== 공간별 묶음

class FormLayer:
    def __init__(self, space_id: str, dim):
        self.space = space_id
        self.dim = dim
        self.parts: list[Quads] = []
        self.movers: list[Mover] = []
        self.emitters: list[Emitter] = []
        self.cells = None        # finalize 결과
        self.stats = {}

    def add(self, q: Quads):
        if len(q):
            self.parts.append(q)

    def mover(self, m: Mover):
        self.movers.append(m)

    def emitter(self, e: Emitter):
        self.emitters.append(e)

    def solid(self, x0, y0, z0, mask):
        """충돌 칸 (보이는 모습은 형체): barrier. mask [X,Y,Z] bool."""
        self.dim.place_mask(x0, y0, z0, mask, BARRIER)

    def solid_box(self, x0, y0, z0, x1, y1, z1):
        self.dim.fill(x0, y0, z0, x1, y1, z1, BARRIER)

    # ---------------------------------------------- 칸 배정
    def finalize(self):
        q = subdivide(concat(self.parts))
        d = self.dim
        n0 = len(q)
        cell = np.floor(q.P.mean(1) + 1e-7).astype(np.int64)
        ok_state = _placeholder_ids(d)
        dropped = 0
        moved = 0
        if n0:
            ids = _get_ids(d, cell)
            bad = ~ok_state[ids]
            if bad.any():
                fn = face_normals(q.P[bad])
                cand = _neighbor_order(fn)                      # (k, 26, 3)
                c0 = cell[bad]
                best = np.full(len(c0), -1)
                for j in range(cand.shape[1]):
                    need = best < 0
                    if not need.any():
                        break
                    c = c0[need] + cand[need, j]
                    good = ok_state[_get_ids(d, c)]
                    best[np.flatnonzero(need)[good]] = j
                fixed = best >= 0
                bi = np.flatnonzero(bad)
                cell[bi[fixed]] = c0[fixed] + cand[np.flatnonzero(fixed), best[fixed]]
                moved = int(fixed.sum())
                keep = np.ones(n0, bool)
                keep[bi[~fixed]] = False
                dropped = int((~fixed).sum())
                q, cell = q.take(keep), cell[keep]
        key = _pos_key(cell)
        order = np.argsort(key, kind="stable")
        q, cell, key = q.take(order), cell[order], key[order]
        uk, start, count = np.unique(key, return_index=True, return_counts=True)
        ucell = cell[start]
        # 움직이는 형체 자리: 빈 칸이고 형체 칸이 아니어야 함 → 아니면 가까운 빈 칸으로 (모양·중심은 그대로)
        taken = {tuple(int(v) for v in c) for c in ucell}
        for m in self.movers:
            p0 = tuple(int(v) for v in m.pos)
            for dp in sorted(((x, y, z) for x in range(-3, 4) for y in range(-3, 4) for z in range(-3, 4)),
                             key=lambda v: abs(v[0]) + abs(v[1]) + abs(v[2])):
                p = (p0[0] + dp[0], p0[1] + dp[1], p0[2] + dp[2])
                if p not in taken and d.get(*p) == "minecraft:air":
                    break
            else:
                raise ValueError(f"{self.space}: 움직이는 형체 {p0} 근처에 빈 칸 없음")
            m.pos = p
            taken.add(p)
        mcells = {tuple(m.pos) for m in self.movers}
        glow = np.zeros(len(uk), np.int32)
        gm = np.array([m.glow for m in MATERIALS] or [0], np.int32)
        if len(q):
            np.maximum.at(glow, np.repeat(np.arange(len(uk)), count), gm[q.M])
        self.q, self.cell_keys, self.cell_pos, self.cell_start, self.cell_count, self.cell_glow = q, uk, ucell, start, count, glow
        d.extra_chunks |= {(int(c[0]) >> 4, int(c[2]) >> 4) for c in ucell}
        d.extra_chunks |= {(int(p[0]) >> 4, int(p[2]) >> 4) for p in mcells}
        states = [d.get(*map(int, c)) for c in ucell]
        self.anchor_states = [_anchor_state(s, int(g)) for s, g in zip(states, glow)]
        self.stats = {"면": len(q), "칸": len(uk), "옮김": moved, "버림": dropped, "움직임": len(self.movers),
                      "파티클": len(self.emitters)}
        return self.stats

    # ---------------------------------------------- 모드 리소스
    def write_assets(self, assets: str):
        out = os.path.join(assets, "forms", self.space)
        os.makedirs(out, exist_ok=True)
        if self.cells is None and not hasattr(self, "q"):
            self.finalize()
        if len(self.cell_keys):
            reg = (self.cell_pos[:, 0] >> 9) * 100000 + (self.cell_pos[:, 2] >> 9)
            for r in np.unique(reg):
                ci = np.flatnonzero(reg == r)
                rx, rz = int(self.cell_pos[ci[0], 0] >> 9), int(self.cell_pos[ci[0], 2] >> 9)
                _write_cells(os.path.join(out, f"r.{rx}.{rz}.bin"), self.q, self.cell_pos[ci], self.cell_start[ci],
                             self.cell_count[ci])
        movers = []
        for i, m in enumerate(self.movers):
            mesh = m.mesh.translate(-np.asarray(m.pivot, float))
            lo, hi = mesh.bounds() if len(mesh) else (np.zeros(3), np.zeros(3))
            ext = float(max(np.abs(lo).max(), np.abs(hi).max(), 0.01))
            name = f"mesh_{i}"
            _write_cells(os.path.join(out, name + ".bin"), mesh, np.zeros((1, 3), np.int64), np.array([0]),
                         np.array([len(mesh)]), scale=32000.0 / ext)
            piv = np.asarray(m.pivot, float) - np.asarray(m.pos, float)
            movers.append({"pos": [int(v) for v in m.pos], "mesh": name, "pivot": [round(float(v), 4) for v in piv],
                           "motion": m.motion, "axis": [float(v) for v in _unit(np.asarray(m.axis, float))],
                           "period": m.period, "amp": m.amp, "phase": m.phase,
                           "radius": float(m.radius or ext * math.sqrt(3))})
        with open(os.path.join(out, "movers.json"), "w") as f:
            json.dump(movers, f)
        with open(os.path.join(out, "emitters.json"), "w") as f:
            json.dump([{"box": list(map(float, e.box)), "rate": e.rate, "sprites": list(e.sprites), "wind": list(e.wind),
                        "size": e.size, "life": e.life, "spin": e.spin, "color": list(e.color), "glow": e.glow}
                       for e in self.emitters], f)


def _pos_key(c) -> np.ndarray:
    """BlockPos.asLong 과 같은 값 (x 26비트, z 26비트, y 12비트)."""
    c = np.asarray(c, np.int64)
    return ((c[:, 0] & 0x3FFFFFF) << 38) | ((c[:, 2] & 0x3FFFFFF) << 12) | (c[:, 1] & 0xFFF)


def _get_ids(d, cells) -> np.ndarray:
    """칸들의 팔레트 번호 (벡터)."""
    cells = np.asarray(cells, np.int64)
    out = np.zeros(len(cells), np.int64)
    sk = cells >> 4
    keys = sk[:, 0] * 1_000_003 * 4099 + sk[:, 1] * 1_000_003 + sk[:, 2]
    uk, inv = np.unique(keys, return_inverse=True)
    for i in range(len(uk)):
        sel = np.flatnonzero(inv == i)
        s = d.sections.get(tuple(int(v) for v in sk[sel[0]]))
        if s is None:
            continue
        c = cells[sel] & 15
        out[sel] = s[c[:, 1], c[:, 2], c[:, 0]]
    return out


def _placeholder_ids(d) -> np.ndarray:
    """팔레트 번호 → 형체 블록 자리로 쓸 수 있나 (공기·barrier·light)."""
    ok = np.zeros(len(d.palette) + 1, bool)
    for i, s in enumerate(d.palette):
        ok[i] = s == "minecraft:air" or s == BARRIER or s.startswith("minecraft:light[") or s == "minecraft:light"
    return ok


_NB = np.array([(x, y, z) for x in (-1, 0, 1) for y in (-1, 0, 1) for z in (-1, 0, 1) if (x, y, z) != (0, 0, 0)])


def _neighbor_order(fn) -> np.ndarray:
    """면 법선 쪽 이웃 칸부터 (k, 26, 3)."""
    nb = _NB / np.linalg.norm(_NB, axis=1, keepdims=True)
    score = fn @ nb.T - 0.01 * np.abs(_NB).sum(1)[None]
    return _NB[np.argsort(-score, axis=1)]


def _anchor_state(placeholder: str, glow: int) -> str:
    solid = placeholder == BARRIER
    light = 0
    if placeholder.startswith("minecraft:light"):
        light = 15
        if "level=" in placeholder:
            light = int(placeholder.split("level=")[1].split(",")[0].rstrip("]"))
    return f"{FORM_BLOCK}[glow={glow},light={light},solid={'true' if solid else 'false'}]"


def _write_cells(path, q: Quads, cell_pos, start, count, scale: float = CELL_SCALE):
    """칸 파일 쓰기 (형식은 모듈 설명)."""
    parts = [MAGIC, struct.pack("<fI", scale, len(cell_pos))]
    sel = np.concatenate([np.arange(s, s + c) for s, c in zip(start, count)]) if len(count) else np.zeros(0, int)
    new_start = np.r_[0, np.cumsum(count)[:-1]] if len(count) else np.zeros(0, int)
    head = np.zeros((len(cell_pos), 5), np.int32)
    head[:, :3] = cell_pos
    head[:, 3] = new_start
    head[:, 4] = count
    parts.append(head.astype("<i4").tobytes())
    sub = q.take(sel)
    origin = np.repeat(np.asarray(cell_pos, float), count, axis=0)[:, None, :]
    rel = np.round((sub.P - origin) * scale)
    if len(rel) and (np.abs(rel) > 32767).any():
        raise ValueError(f"{path}: 칸 밖으로 너무 멀리 뻗은 면 (최대 {np.abs(sub.P - origin).max():.1f}블록)")
    uv = sub.UV - np.floor(sub.UV.min(1, keepdims=True) + 1e-6)        # 타일 안 좌표
    uv = np.round(np.clip(uv, 0, 1) * 65535)
    c = np.clip(np.round(sub.C * 255), 0, 255).astype(np.uint32)
    argb = (c[..., 3] << 24) | (c[..., 0] << 16) | (c[..., 1] << 8) | c[..., 2]
    nrm = np.clip(np.round(_unit(sub.N) * 127), -127, 127)
    rec = np.zeros(len(sub), dtype=np.dtype([("m", "<u2"), ("pad", "<u2"),
                                              ("v", [("p", "<i2", 3), ("uv", "<u2", 2), ("c", "<u4"), ("n", "i1", 3),
                                                     ("pad", "u1")], 4)]))
    rec["m"] = sub.M
    rec["v"]["p"] = rel
    rec["v"]["uv"] = uv
    rec["v"]["c"] = argb
    rec["v"]["n"] = nrm
    assert rec.dtype.itemsize == QUAD_BYTES
    parts.append(rec.tobytes())
    with open(path, "wb") as f:
        for p in parts:
            f.write(p)


def read_cells(path):
    """시험·미리보기용: 칸 파일 → (scale, 칸 머리 (n,5), 면 레코드)."""
    with open(path, "rb") as f:
        raw = f.read()
    assert raw[:4] == MAGIC
    scale, n = struct.unpack_from("<fI", raw, 4)
    head = np.frombuffer(raw, "<i4", n * 5, 12).reshape(n, 5)
    rec = np.frombuffer(raw[12 + n * 20:], np.dtype([("m", "<u2"), ("pad", "<u2"),
                                                    ("v", [("p", "<i2", 3), ("uv", "<u2", 2), ("c", "<u4"), ("n", "i1", 3),
                                                           ("pad", "u1")], 4)]))
    return scale, head, rec


class FormSet:
    """빌드 전체의 형체 (공간별 FormLayer)."""

    def __init__(self):
        self.layers: dict[str, FormLayer] = {}

    def layer(self, space_id: str, dim) -> FormLayer:
        if space_id not in self.layers:
            self.layers[space_id] = FormLayer(space_id, dim)
        return self.layers[space_id]

    def finalize(self) -> dict:
        return {k: l.finalize() for k, l in self.layers.items()}

    def write_assets(self, assets: str):
        """assets = .../assets/ruina"""
        base = os.path.join(assets, "forms")
        os.makedirs(base, exist_ok=True)
        with open(os.path.join(base, "materials.json"), "w") as f:
            json.dump([m.json() for m in MATERIALS], f, indent=1)
        with open(os.path.join(base, "spaces.json"), "w") as f:
            json.dump(sorted(self.layers), f)
        for l in self.layers.values():
            l.write_assets(assets)
        tdir = os.path.join(assets, "textures", "block", "form")
        for name, img in TEXTURES.items():
            p = os.path.join(tdir, name + ".png")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            img.save(p)

    def anchors(self) -> dict[str, dict]:
        """{차원 id: {(x,y,z): 블록 상태}} — 서버 저장 뒤 inject 로 넣을 것 (움직이는 형체 포함)."""
        out = {}
        for l in self.layers.values():
            a = {tuple(int(v) for v in c): s for c, s in zip(l.cell_pos, l.anchor_states)}
            for m in l.movers:
                a[tuple(int(v) for v in m.pos)] = MOVER_BLOCK
            if a:
                out[l.dim.dim] = a
        return out


# ====================================================================== 서버 저장 뒤 리전에 넣기

def inject(world_dir: str, anchors: dict[str, dict]) -> dict:
    """서버가 저장한 리전 파일의 자리 표시(공기·barrier·light)를 형체 블록으로 바꾸고 움직이는 형체 블록 엔티티를 넣음.
    조명 값은 그대로 (형체 블록은 빛을 막지 않고, light 자리는 같은 밝기로 빛남)."""
    from . import nbt, region
    from .world import AIR, block_bits, decode_section_blocks, pack_indices, parse_state
    stats = {"칸": 0, "청크": 0, "자리 아님": 0}
    for dim, cells in anchors.items():
        rdir = os.path.join(world_dir, "dimensions", *dim.split(":"), "region")
        by_region: dict[tuple, dict] = {}
        for (x, y, z), st in cells.items():
            by_region.setdefault((x >> 9, z >> 9), {}).setdefault((x >> 4, z >> 4), []).append((x, y, z, st))
        for (rx, rz), chunks in by_region.items():
            path = os.path.join(rdir, region.region_name(rx, rz))
            raw = region.read_region_raw(path) if os.path.exists(path) else {}
            out = dict(raw)
            for (cx, cz), items in chunks.items():
                if (cx, cz) not in raw:
                    raise ValueError(f"{dim} 청크 {cx},{cz} 가 저장된 월드에 없음 (형체만 있는 청크는 빌더가 공기 아닌 블록을 하나 둬야 함)")
                ch = nbt.loads(raw[(cx, cz)])
                secs = {int(s["Y"]): s for s in ch["sections"]}
                by_sec: dict[int, list] = {}
                for it in items:
                    by_sec.setdefault(it[1] >> 4, []).append(it)
                for sy, its in by_sec.items():
                    sec = secs[sy]
                    arr = decode_section_blocks(sec)
                    if arr is None:
                        arr = np.full((16, 16, 16), AIR, dtype=object)
                    for x, y, z, st in its:
                        cur = arr[y & 15, z & 15, x & 15]
                        if not (cur == AIR or cur == BARRIER or cur.startswith("minecraft:light")):
                            stats["자리 아님"] += 1
                            continue
                        arr[y & 15, z & 15, x & 15] = st
                        stats["칸"] += 1
                        if st == MOVER_BLOCK:
                            ch.setdefault("block_entities", nbt.List(elem_tag=nbt.TAG_COMPOUND)).append(
                                {"id": "ruina:mover", "x": nbt.Int(x), "y": nbt.Int(y), "z": nbt.Int(z),
                                 "keepPacked": nbt.Byte(0)})
                    uniq, inv = np.unique(arr.ravel(), return_inverse=True)
                    mixed = any("[" in u for u in uniq)
                    pal = nbt.List()
                    for u in uniq:
                        name, props = parse_state(u)
                        pal.append({"id": name, "properties": props} if props else ({"": name} if mixed else name))
                    bs = {"palette": pal}
                    if len(uniq) > 1:
                        bs["data"] = pack_indices(inv.astype(np.uint64), block_bits(len(uniq)))
                    sec["block_states"] = bs
                out[(cx, cz)] = ch
                stats["청크"] += 1
            region.write_region(path, out)
    return stats


# ====================================================================== 미리보기 (게임 없이 형체만 원근으로)

def render_preview(qs: list[Quads], cam: Camera, W: int = 960, H: int = 540, bg=(30, 20, 50), light=(-0.4, 0.8, 0.45)):
    """형체 원근 미리보기 (PIL 이미지). 텍스처는 등록된 forms 텍스처 (바닐라 스프라이트는 회색).
    emissive·flat 재질은 색 그대로, 나머지는 간단한 램버트."""
    from PIL import Image
    q, (pix, z, qi, s, t) = _splat_points(qs, cam, W, H)
    img = np.empty((H * W, 3))
    img[:] = bg
    if len(pix):
        pix = pix.astype(int)
        o = np.lexsort((z, pix))
        first = np.r_[True, pix[o][1:] != pix[o][:-1]]
        sel = o[first]
        pix, qi, s, t = pix[sel], qi[sel].astype(int), s[sel], t[sel]
        w = np.stack([(1 - s) * (1 - t), s * (1 - t), s * t, (1 - s) * t], 1)[..., None]
        uv = ((q.UV[qi] - np.floor(q.UV[qi].min(1, keepdims=True) + 1e-6)) * w).sum(1)
        col = (q.C[qi] * w).sum(1)
        nrm = _unit((q.N[qi] * w).sum(1))
        out = np.zeros((len(pix), 3))
        texs = {}
        for m in np.unique(q.M[qi]):
            mm = MATERIALS[m] if m < len(MATERIALS) else Material("?", "?")
            k = q.M[qi] == m
            name = mm.sprite.split("ruina:block/form/")[-1]
            if mm.sprite.startswith("ruina:block/form/") and name in TEXTURES:
                if name not in texs:
                    texs[name] = np.asarray(TEXTURES[name].convert("RGB"), float)
                tx = texs[name]
                th, tw = tx.shape[:2]
                c = tx[np.clip((uv[k, 1] * th).astype(int), 0, th - 1), np.clip((uv[k, 0] * tw).astype(int), 0, tw - 1)]
            else:
                c = np.full((k.sum(), 3), 128.0)
            c = c * col[k, :3]
            if not (mm.emissive or mm.flat):
                c = c * (0.45 + 0.55 * np.clip(nrm[k] @ _unit(np.asarray(light, float)), 0, 1))[:, None]
            out[k] = c
        img[pix] = out
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8).reshape(H, W, 3))
