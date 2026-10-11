"""도서관 주변 전경 (reference/도서관 위치 전경.png).

도서관은 거대한 분화구 한가운데 있다:
- 계단식 동심원 단(테라스): 바깥으로 갈수록 높아짐. 안쪽을 향한 옹벽에는 도시 외벽(불 켜진 창),
  단 위에는 빌딩 (builders/city.py)
- 분화구 위를 도는 나선형 구름 팔 (가운데는 뚫려 빛기둥이 보임)
- 거대한 고리 구조물 + 검은 기둥 (원화 오른쪽)
속은 모두 비움 (윗면 한 겹, 옹벽 한 겹).
"""
from __future__ import annotations

import math

import numpy as np

import config
from tools import shapes as S

from .city import build_city

K = config.EXTERIOR_SCALE / 3.0

# 단 경계 반지름과 각 단 윗면 높이 (안 → 밖)
RINGS = [135, 190, 255, 330, 415, 510, 620, 760]
TOPS = [14, 34, 58, 86, 118, 154, 194]
FLOOR_Y = -1  # 광장·분화구 바닥 윗면

PAVE = ["minecraft:gray_concrete", "minecraft:polished_deepslate", "minecraft:deepslate_tiles",
        "minecraft:polished_andesite", "minecraft:gray_concrete"]
STREET = "minecraft:polished_andesite"
# 옹벽: 원화의 밝은 옛 건물 벽 (위에서 보면 동심원 고리가 또렷하게)
WALL = ["minecraft:stone_bricks", "minecraft:polished_andesite", "minecraft:smooth_stone", "minecraft:tuff_bricks",
        "minecraft:polished_tuff", "minecraft:stone_bricks"]
WIN_LIT = ["minecraft:ochre_froglight", "minecraft:sea_lantern", "minecraft:pearlescent_froglight"]
WIN_DARK = "minecraft:black_concrete"


def _ring_cells(r_in, r_out, tile=256):
    """반지름 r_in~r_out 고리의 (x,z) 칸을 타일 단위로 (x0, z0, mask[X,Z], rr, ang)."""
    R = int(math.ceil(r_out))
    for x0 in range(-R, R + 1, tile):
        for z0 in range(-R, R + 1, tile):
            xs = np.arange(x0, min(x0 + tile, R + 1)) + 0.5
            zs = np.arange(z0, min(z0 + tile, R + 1)) + 0.5
            X, Z = np.meshgrid(xs, zs, indexing="ij")
            rr = np.hypot(X, Z)
            m = (rr >= r_in) & (rr < r_out)
            if m.any():
                yield x0, z0, m, rr, np.arctan2(Z, X)


def terraces(d, seed=91):
    rng = np.random.default_rng(seed)
    pave = np.array([d.id(s) for s in PAVE])
    street = d.id(STREET)
    # 분화구 바닥 (광장 바깥 ~ 첫 옹벽)
    for x0, z0, m, rr, ang in _ring_cells(108 * K, RINGS[0] * K):
        ids = np.where(m, pave[1], -1)
        d.place(x0, FLOOR_Y, z0, ids[:, None, :])
    for i, top in enumerate(TOPS):
        a, b = RINGS[i] * K, RINGS[i + 1] * K
        y = int(top * K)
        for x0, z0, m, rr, ang in _ring_cells(a, b):
            h = S.hash01(np.floor(rr / 9).astype(int), np.floor(ang * rr / 9).astype(int), seed=seed + i)
            ids = pave[(h * len(pave)).astype(int).clip(0, len(pave) - 1)]
            # 거리: 원형 길 (단 가운데쯤) + 방사형 길
            ring_road = np.abs(rr - (a + (b - a) * 0.5)) < 2.0
            radial = (np.abs(((ang * rr) % 60) - 30) < 1.6)
            ids = np.where(ring_road | radial, street, ids)
            ids = np.where(m, ids, -1)
            d.place(x0, y, z0, ids[:, None, :])
        retaining_wall(d, a, FLOOR_Y if i == 0 else int(TOPS[i - 1] * K), y, rng)
    # 바깥 테두리 (맨 바깥 단 가장자리 난간)
    for x0, z0, m, rr, ang in _ring_cells(RINGS[-1] * K - 1.5, RINGS[-1] * K):
        ids = np.where(m, d.id("minecraft:polished_blackstone_bricks"), -1)
        d.place(x0, int(TOPS[-1] * K) + 1, z0, np.repeat(ids[:, None, :], 2, axis=1))


def retaining_wall(d, r, y0, y1, rng):
    """반지름 r 의 옹벽 (y0 아래 ~ y1). 안쪽 면은 창이 난 도시 외벽."""
    n = int(2 * math.pi * r)
    th = np.arange(n) / n * 2 * math.pi
    xs = np.floor(r * np.cos(th)).astype(int)
    zs = np.floor(r * np.sin(th)).astype(int)
    seen = set()
    H = y1 - y0
    wall_ids = [d.id(s) for s in WALL]
    lit = [d.id(s) for s in WIN_LIT]
    dark = d.id(WIN_DARK)
    seg_len = 18
    for j, (x, z) in enumerate(zip(xs, zs)):
        if (x, z) in seen:
            continue
        seen.add((x, z))
        seg = j // seg_len
        srng = np.random.default_rng(hash((int(r), seg)) & 0xFFFFFFFF)
        wid = wall_ids[int(srng.integers(len(wall_ids)))]
        col = np.full(H + 1, wid, dtype=np.int32)
        ratio = srng.uniform(0.25, 0.6)
        if (j % 3) != 0:  # 창 기둥
            for yy in range(3, H - 1, 4):
                if rng.random() < ratio:
                    col[yy:yy + 2] = lit[int(srng.integers(len(lit)))] if srng.random() < 0.3 else lit[0]
                else:
                    col[yy:yy + 2] = dark
        d.place(x, y0, z, col[None, :, None])


def terrace_city(d, seed=101):
    out = []
    for i, top in enumerate(TOPS):
        a, b = RINGS[i] * K, RINGS[i + 1] * K
        frac = i / (len(TOPS) - 1)
        hmin, hmax = int((12 + 18 * frac) * K), int((26 + 44 * frac) * K)   # 단이 보이게 낮게
        out.append(build_city(d, a + 18, b - 18, seed=seed + i, ground_y=int(top * K) + 1, h_min=hmin, h_max=hmax,
                              spacing0=46, size=(10, 24)))
    return out


# ---------------------------------------------------------------- 구름 소용돌이

CLOUD_IN = (["minecraft:white_wool", "minecraft:snow_block", "minecraft:calcite", "minecraft:white_concrete"],
            [40, 25, 20, 15])
CLOUD_OUT = (["minecraft:light_gray_wool", "minecraft:white_wool", "minecraft:gray_wool", "minecraft:tuff"],
             [40, 30, 18, 12])


def clouds(d, y0=250.0, r_hole=400.0, r_out=760.0, arms=3, twist=1.9, thick=12.0, seed=111, tile=192):
    """나선 소용돌이 구름층 (열 단위로 직접 채움 — 빠름).

    - 가운데(반지름 r_hole 안)는 맑게: 땅에서 보면 머리 위는 맑고 지평선 쪽에 구름 고리 (외견 원화)
    - 위에서 보면 바깥 도시 위를 도는 나선 팔 (위치 전경 원화)
    - 겉면만 블록: 각 열의 윗면·아랫면 + 이웃 열보다 튀어나온 옆면
    """
    y0, r_hole, r_out, thick = y0 * K, r_hole * K, r_out * K, thick * K
    rng_ids_in = [d.id(x) for x in CLOUD_IN[0]]
    rng_ids_out = [d.id(x) for x in CLOUD_OUT[0]]
    w_in = np.cumsum(CLOUD_IN[1]) / np.sum(CLOUD_IN[1])
    w_out = np.cumsum(CLOUD_OUT[1]) / np.sum(CLOUD_OUT[1])
    R = int(r_out)
    total = 0
    for x0 in range(-R, R + 1, tile):
        for z0 in range(-R, R + 1, tile):
            xs = np.arange(x0 - 1, min(x0 + tile, R + 1) + 1) + 0.5
            zs = np.arange(z0 - 1, min(z0 + tile, R + 1) + 1) + 0.5
            X, Z = np.meshgrid(xs, zs, indexing="ij")
            r = np.hypot(X, Z) + 1e-6
            if r.min() > r_out or r.max() < r_hole:
                continue
            th = np.arctan2(Z, X)
            phase = th - twist * np.log(r / r_hole)
            band = (0.5 + 0.5 * np.cos(arms * phase)) ** 2.2
            P = np.stack([X.ravel(), np.zeros(X.size), Z.ravel()], 1)
            n = S.fbm(P, 30.0 * K, 3, seed).reshape(X.shape)
            n2 = S.fbm(P, 9.0 * K, 2, seed + 3).reshape(X.shape)
            ramp = np.clip((r - r_hole) / (70 * K), 0, 1) * np.clip((r_out - r) / (40 * K), 0, 1)
            dens = (band * 1.1 + 0.45 * n - 0.22) * ramp
            half = thick * np.clip(dens, 0, None) * (1 + 0.5 * n2)
            center = y0 + 14 * K * S.fbm(P, 110.0 * K, 2, seed + 5).reshape(X.shape) + 25 * K * (r - r_hole) / r_out
            top = np.floor(center + half + 2.0 * n2 * (half > 0)).astype(int)
            bot = np.ceil(center - half * 0.55).astype(int)
            has = (half > 0.6) & (top >= bot)
            top = np.where(has, top, -10 ** 6)
            bot = np.where(has, bot, 10 ** 6)
            ylo, yhi = int(bot[has].min()) if has.any() else 0, int(top[has].max()) if has.any() else -1
            if yhi < ylo:
                continue
            ys = np.arange(ylo, yhi + 1)
            inside = (ys[None, None, :] >= bot[..., None]) & (ys[None, None, :] <= top[..., None])
            core = inside[1:-1, 1:-1]
            exposed = core & ~(inside[:-2, 1:-1] & inside[2:, 1:-1] & inside[1:-1, :-2] & inside[1:-1, 2:])
            exposed |= core & ((ys[None, None, :] == bot[1:-1, 1:-1, None]) | (ys[None, None, :] == top[1:-1, 1:-1, None]))
            if not exposed.any():
                continue
            Xc, Zc = X[1:-1, 1:-1], Z[1:-1, 1:-1]
            h = S.hash01(np.floor(Xc / 3).astype(int)[..., None], np.floor(ys / 3).astype(int)[None, None, :],
                         np.floor(Zc / 3).astype(int)[..., None], seed=seed + 7)
            t = np.clip((r[1:-1, 1:-1] - 520 * K) / (220 * K), 0, 1)[..., None]
            outer = S.hash01(np.floor(Xc / 4).astype(int)[..., None], np.floor(ys / 4).astype(int)[None, None, :],
                             np.floor(Zc / 4).astype(int)[..., None], seed=seed + 8) < t
            ids_in = np.array(rng_ids_in)[np.searchsorted(w_in, h).clip(0, len(rng_ids_in) - 1)]
            ids_out = np.array(rng_ids_out)[np.searchsorted(w_out, h).clip(0, len(rng_ids_out) - 1)]
            ids = np.where(outer, ids_out, ids_in)
            ids = np.where(exposed, ids, -1).astype(np.int32)
            d.place(x0, ylo, z0, ids.transpose(0, 2, 1), only_air=True)  # [x,z,y] → [x,y,z]
            total += int(exposed.sum())
    return total


# ---------------------------------------------------------------- 고리 구조물

def ring_landmark(seed=121):
    """원화 오른쪽의 거대한 고리(바퀴) + 검은 기둥. 북동쪽 단 위에 세움."""
    ang = -0.45
    cx, cz = 360 * K * math.cos(ang), 360 * K * math.sin(ang)
    base_y = TOPS[3] * K
    R = 72 * K
    center = np.array([cx, base_y + R + 6 * K, cz])
    radial = np.array([math.cos(ang), 0, math.sin(ang)])
    tang = np.array([-math.sin(ang), 0, math.cos(ang)])   # 고리 면 = (접선, 위)
    up = np.array([0.0, 1.0, 0.0])
    t = np.linspace(0, 2 * math.pi, 240)
    circle = center + R * (np.cos(t)[:, None] * tang + np.sin(t)[:, None] * up)
    mat = S.mix(["minecraft:polished_deepslate", "minecraft:deepslate_tiles", "minecraft:polished_basalt[axis=y]"],
                [5, 3, 2], seed=seed)
    stone = ("minecraft:polished_deepslate_stairs", "minecraft:polished_deepslate_slab")
    parts = [S.Tube(circle, 6.5 * K).with_(paint=mat, smooth=stone, name="ring")]
    inner = center + (R - 14 * K) * (np.cos(t)[:, None] * tang + np.sin(t)[:, None] * up)
    parts.append(S.Tube(inner, 2.5 * K).with_(paint=mat, smooth=stone, name="ring_in"))
    for k in range(10):  # 바퀴살 (비스듬히)
        a0 = k * 2 * math.pi / 10
        p_out = center + R * (math.cos(a0) * tang + math.sin(a0) * up)
        p_in = center + 10 * K * (math.cos(a0 + 0.6) * tang + math.sin(a0 + 0.6) * up)
        parts.append(S.Tube(np.array([p_in, p_out]), [2.2 * K, 1.6 * K]).with_(paint=mat, smooth=stone))
    parts.append(S.Sphere(center, 11 * K).with_(paint=mat, smooth=stone, name="hub"))
    # 받침 (아래 단에 박힘) + 옆의 검은 기둥
    parts.append(S.Box(int(cx - 10 * K), int(base_y), int(cz - 6 * K), int(cx + 10 * K), int(base_y + 10 * K),
                       int(cz + 6 * K)).with_(paint="minecraft:polished_blackstone_bricks"))
    px, pz = cx - 70 * K * math.sin(ang) + 20 * K * math.cos(ang), cz + 70 * K * math.cos(ang) + 20 * K * math.sin(ang)
    parts.append(S.Box(int(px - 9 * K), int(base_y), int(pz - 9 * K), int(px + 9 * K), int(base_y + 230 * K),
                       int(pz + 9 * K)).with_(paint=S.mix(["minecraft:blackstone", "minecraft:polished_blackstone",
                                                           "minecraft:basalt[axis=y]"], seed=seed + 1)))
    return parts


# ---------------------------------------------------------------- 빛기둥

def light_beam(d, top_y_guess: int):
    """탑 꼭대기 가운데: 금 블록 3×3 + 신호기 + 노란 유리 → 하늘로 솟는 금빛 빛기둥."""
    y = top_y_guess + 12
    while y > top_y_guess - 30 and d.get(0, y, 0) == "minecraft:air":
        y -= 1
    d.fill(-1, y, -1, 1, y, 1, "minecraft:gold_block")
    d.set(0, y + 1, 0, "minecraft:beacon")
    d.block_entity(0, y + 1, 0, {"id": "minecraft:beacon"})
    d.set(0, y + 2, 0, "minecraft:yellow_stained_glass")
    # 위로 막힌 블록 제거 (빛이 통과해야 함)
    for yy in range(y + 3, d.min_y + d.height):
        if d.get(0, yy, 0) != "minecraft:air":
            d.set(0, yy, 0, "minecraft:air")
    return y + 1
