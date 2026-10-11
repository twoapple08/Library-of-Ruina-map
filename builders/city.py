"""외부 배경 도시 실루엣 (design/exterior.md 2절 '광장·배경').

- 탑을 둘러싼 고리(반지름 r0~r1)에 고층 빌딩을 겉껍질만 세운다 (속 비움, 지붕 한 겹)
- 창: 빌딩마다 정한 격자(창 폭·간격·층 높이)를 네 면에 똑같이, 불 켜짐은 층 단위로 뭉침.
  꺼진 창은 검은 콘크리트(불투명 → 받침 불필요). 모서리·옥상 난간은 테 재질
- 네온: 일부 빌딩 모서리 세로 띠, 옥상 안테나 (지붕 테두리 발광은 없앰 — Phase 1 테스트 ⑩)
- 바깥으로 갈수록 듬성듬성 + 높게 (원화처럼 뒤쪽이 더 높아 보이게)
블록을 직접 채운다 (도형 엔진보다 훨씬 빠름).
"""
from __future__ import annotations

import math

import numpy as np

WALLS = ["minecraft:gray_concrete", "minecraft:polished_deepslate", "minecraft:cyan_terracotta",
         "minecraft:blue_terracotta", "minecraft:purple_terracotta", "minecraft:polished_blackstone",
         "minecraft:light_blue_terracotta", "minecraft:magenta_terracotta"]
WALL_W = [8, 10, 18, 18, 18, 8, 6, 6]
# 모서리·옥상 난간 (벽과 다른 재질로 테를 둘러 건물 윤곽을 또렷하게)
TRIM = ["minecraft:polished_blackstone_bricks", "minecraft:deepslate_tiles", "minecraft:smooth_stone",
        "minecraft:polished_andesite"]
LIT = ["minecraft:ochre_froglight", "minecraft:sea_lantern", "minecraft:pearlescent_froglight",
       "minecraft:verdant_froglight", "minecraft:glowstone"]
LIT_W = [36, 30, 16, 10, 8]
NEON = ["minecraft:pearlescent_froglight", "minecraft:sea_lantern", "minecraft:verdant_froglight"]
DARK_WINDOW = "minecraft:black_concrete"


def _pick(rng, items, weights):
    w = np.asarray(weights, float)
    return items[rng.choice(len(items), p=w / w.sum())]


class Style:
    """빌딩 하나의 창 규칙 (네 면 모두 같은 격자 → 가지런함)."""

    def __init__(self, rng, d, wall, trim, lit_main, lit_ratio):
        self.wall, self.trim = d.id(wall), d.id(trim)
        self.lit = d.id(lit_main)
        self.dark = d.id(DARK_WINDOW)
        self.win_w = int(rng.choice([1, 2, 2, 3]))
        self.gap = int(rng.choice([1, 1, 2]))
        self.floor_h = int(rng.choice([3, 4, 4]))
        self.win_h = 2 if self.floor_h == 4 else 1 + int(rng.random() < 0.5)
        self.lit_ratio = lit_ratio
        self.seed = int(rng.integers(1 << 30))


def _facade(st: Style, width, height, face: int):
    """한 면의 [가로, 높이] 팔레트 번호 배열. 양 끝 1칸은 모서리 테, 층마다 같은 자리에 창.
    불 켜짐은 층 단위로 뭉쳐서 (층 전체가 켜지거나 그 층의 일부 구간만) — 무작위 점무늬 대신."""
    rng = np.random.default_rng(st.seed + face)
    a = np.full((width, height), st.wall, dtype=np.int32)
    a[0, :] = st.trim
    a[width - 1, :] = st.trim
    period = st.win_w + st.gap
    inner = width - 2
    n = max(1, (inner - st.gap) // period)
    pad = (inner - (n * period - st.gap)) // 2 + 1   # 가운데 맞춤
    for k, y0 in enumerate(range(2, height - 2, st.floor_h)):
        floor_on = rng.random() < st.lit_ratio * 1.6
        run0, run1 = sorted(rng.integers(0, n + 1, 2))
        for i in range(n):
            x0 = pad + i * period
            on = floor_on and (run0 <= i <= run1 or rng.random() < 0.25)
            a[x0:x0 + st.win_w, y0:y0 + st.win_h] = st.lit if on else st.dark
    return a


def _box(d, rng, st: Style, x0, z0, w, l, y0, h):
    """속 빈 직육면체 빌딩 하나: 네 벽(창 격자) + 지붕 + 옥상 난간."""
    x1, z1, y1 = x0 + w - 1, z0 + l - 1, y0 + h - 1
    for k, z in enumerate((z0, z1)):
        d.place(x0, y0, z, _facade(st, w, h, k)[:, :, None])
    for k, x in enumerate((x0, x1)):
        d.place(x, y0, z0, _facade(st, l, h, k + 2)[None, :, :])
    roof = np.full((w, 1, l), st.wall, np.int32)
    d.place(x0, y1, z0, roof)
    rim = np.full((w, 1, l), -1, np.int32)
    rim[[0, -1], 0, :] = st.trim
    rim[:, 0, [0, -1]] = st.trim
    d.place(x0, y1 + 1, z0, rim)
    return x1, y1, z1


def build_city(d, r0: float, r1: float, seed: int = 81, ground_y: int = -40, h_min: int = 60, h_max: int = 120,
               skip=None, spacing0: float = 34, size=(12, 30)) -> dict:
    """skip(x, z) -> True 면 그 자리는 비움 (예: 정면 시야 확보)."""
    rng = np.random.default_rng(seed)
    count, blocks = 0, 0
    r = r0
    while r < r1:
        t = (r - r0) / max(1.0, r1 - r0)
        spacing = spacing0 + 22 * t             # 바깥쪽은 듬성듬성
        n = max(8, int(2 * math.pi * r / spacing))
        off = rng.uniform(0, 2 * math.pi)
        for i in range(n):
            th = off + i * 2 * math.pi / n + rng.uniform(-0.25, 0.25) * (2 * math.pi / n)
            rr = r + rng.uniform(-8, 8)
            cx, cz = rr * math.cos(th), rr * math.sin(th)
            if skip is not None and skip(cx, cz):
                continue
            w = int(rng.integers(size[0], size[1]))
            l = int(rng.integers(size[0], size[1]))
            hmax = h_min + (h_max - h_min) * (0.35 + 0.65 * t)
            h = int(rng.uniform(h_min, hmax) * rng.uniform(0.75, 1.25))
            h = int(np.clip(h, 30, h_max * 1.3))
            wall = _pick(rng, WALLS, WALL_W)
            st = Style(rng, d, wall, _pick(rng, TRIM, [3, 3, 2, 2]), _pick(rng, LIT, LIT_W), rng.uniform(0.12, 0.4))
            x0, z0 = int(cx - w / 2), int(cz - l / 2)
            y0 = ground_y
            height_total = h - ground_y if ground_y < 0 else h
            # 1~3단 계단식 (위로 갈수록 좁아짐)
            tiers = int(rng.choice([1, 1, 2, 2, 3]))
            remaining = height_total
            bx, bz, bw, bl, by = x0, z0, w, l, y0
            for k in range(tiers):
                th_h = remaining if k == tiers - 1 else int(remaining * rng.uniform(0.45, 0.7))
                _, ytop, _ = _box(d, rng, st, bx, bz, bw, bl, by, th_h)
                blocks += 2 * (bw + bl) * th_h + bw * bl
                remaining -= th_h
                if k < tiers - 1:
                    shrink = int(rng.integers(2, max(3, min(bw, bl) // 3)))
                    bx, bz, bw, bl, by = bx + shrink, bz + shrink, bw - 2 * shrink, bl - 2 * shrink, ytop + 1
                    if bw < 6 or bl < 6:
                        break
            # 네온: 모서리 세로 띠만 (지붕 테두리 발광은 '천장이 빛남'으로 보여서 뺌)
            if rng.random() < 0.15:
                neon = _pick(rng, NEON, [5, 4, 2])
                d.fill(x0, y0 + 2, z0, x0, y0 + int(height_total * rng.uniform(0.5, 0.95)), z0, neon)
            # 안테나
            if rng.random() < 0.3:
                ax, az = bx + bw // 2, bz + bl // 2
                ah = int(rng.integers(6, 18))
                d.fill(ax, ytop + 1, az, ax, ytop + ah, az, "minecraft:iron_chain[axis=y]")
                d.set(ax, ytop + ah + 1, az, "minecraft:end_rod[facing=up]")
            count += 1
        r += spacing * 0.85
    return {"buildings": count, "approx_blocks": blocks}
