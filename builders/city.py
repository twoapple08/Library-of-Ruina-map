"""외부 배경 도시 실루엣 (design/exterior.md 2절 '광장·배경').

- 탑을 둘러싼 고리(반지름 r0~r1)에 고층 빌딩을 겉껍질만 세운다 (속 비움, 지붕 한 겹)
- 창: 층마다(4칸) 창 줄, 일부만 불 켜짐(발광 블록), 꺼진 창은 검은 콘크리트(불투명 → 받침 불필요)
- 네온: 일부 빌딩 지붕 테두리·모서리에 분홍/청록 발광 띠, 옥상 안테나
- 바깥으로 갈수록 듬성듬성 + 높게 (원화처럼 뒤쪽이 더 높아 보이게)
블록을 직접 채운다 (도형 엔진보다 훨씬 빠름).
"""
from __future__ import annotations

import math

import numpy as np

WALLS = ["minecraft:black_concrete", "minecraft:gray_concrete", "minecraft:polished_deepslate",
         "minecraft:cyan_terracotta", "minecraft:blue_terracotta", "minecraft:purple_terracotta",
         "minecraft:polished_blackstone"]
WALL_W = [14, 6, 8, 20, 16, 18, 6]
LIT = ["minecraft:ochre_froglight", "minecraft:sea_lantern", "minecraft:pearlescent_froglight",
       "minecraft:verdant_froglight", "minecraft:glowstone"]
LIT_W = [36, 30, 16, 10, 8]
NEON = ["minecraft:pearlescent_froglight", "minecraft:sea_lantern", "minecraft:verdant_froglight"]
DARK_WINDOW = "minecraft:black_concrete"


def _pick(rng, items, weights):
    w = np.asarray(weights, float)
    return items[rng.choice(len(items), p=w / w.sum())]


def _facade(rng, width, height, wall_id, lit_ids, dark_id, lit_ratio, floor_h=4):
    """한 면의 [가로, 높이] 팔레트 번호 배열."""
    a = np.full((width, height), wall_id, dtype=np.int32)
    win_w = int(rng.integers(1, 3))
    gap = int(rng.integers(1, 3))
    period = win_w + gap
    for y0 in range(2, height - 2, floor_h):
        rows = slice(y0, min(height - 1, y0 + 2))
        for x0 in range(1, width - 1, period):
            cols = slice(x0, min(width - 1, x0 + win_w))
            if rng.random() < lit_ratio:
                a[cols, rows] = lit_ids[int(rng.integers(len(lit_ids)))] if rng.random() < 0.15 else lit_ids[0]
            else:
                a[cols, rows] = dark_id
    return a


def _box(d, rng, x0, z0, w, l, y0, h, wall, lit_ratio, lit_main):
    """속 빈 직육면체 빌딩 하나: 네 벽(창 무늬) + 지붕."""
    x1, z1, y1 = x0 + w - 1, z0 + l - 1, y0 + h - 1
    wid = d.id(wall)
    lit_ids = [d.id(lit_main)] + [d.id(s) for s in LIT]
    dark = d.id(DARK_WINDOW)
    # 남·북 벽 (x 방향 가로)
    for z in (z0, z1):
        f = _facade(rng, w, h, wid, lit_ids, dark, lit_ratio)
        d.place(x0, y0, z, f[:, :, None])
    # 동·서 벽 (z 방향 가로)
    for x in (x0, x1):
        f = _facade(rng, l, h, wid, lit_ids, dark, lit_ratio)
        d.place(x, y0, z0, f[None, :, :])
    d.fill(x0, y1, z0, x1, y1, z1, wall)  # 지붕
    return x1, y1, z1


def build_city(d, r0: float, r1: float, seed: int = 81, ground_y: int = -40, h_min: int = 60, h_max: int = 120,
               skip=None) -> dict:
    """skip(x, z) -> True 면 그 자리는 비움 (예: 정면 시야 확보)."""
    rng = np.random.default_rng(seed)
    count, blocks = 0, 0
    r = r0
    while r < r1:
        t = (r - r0) / max(1.0, r1 - r0)
        spacing = 34 + 22 * t                   # 바깥쪽은 듬성듬성
        n = max(8, int(2 * math.pi * r / spacing))
        off = rng.uniform(0, 2 * math.pi)
        for i in range(n):
            th = off + i * 2 * math.pi / n + rng.uniform(-0.25, 0.25) * (2 * math.pi / n)
            rr = r + rng.uniform(-8, 8)
            cx, cz = rr * math.cos(th), rr * math.sin(th)
            if skip is not None and skip(cx, cz):
                continue
            w = int(rng.integers(12, 30))
            l = int(rng.integers(12, 30))
            hmax = h_min + (h_max - h_min) * (0.35 + 0.65 * t)
            h = int(rng.uniform(h_min, hmax) * rng.uniform(0.75, 1.25))
            h = int(np.clip(h, 30, h_max * 1.3))
            wall = _pick(rng, WALLS, WALL_W)
            lit_main = _pick(rng, LIT, LIT_W)
            lit_ratio = rng.uniform(0.05, 0.28)
            x0, z0 = int(cx - w / 2), int(cz - l / 2)
            y0 = ground_y
            height_total = h - ground_y if ground_y < 0 else h
            # 1~3단 계단식 (위로 갈수록 좁아짐)
            tiers = int(rng.choice([1, 1, 2, 2, 3]))
            remaining = height_total
            bx, bz, bw, bl, by = x0, z0, w, l, y0
            for k in range(tiers):
                th_h = remaining if k == tiers - 1 else int(remaining * rng.uniform(0.45, 0.7))
                _, ytop, _ = _box(d, rng, bx, bz, bw, bl, by, th_h, wall, lit_ratio, lit_main)
                blocks += 2 * (bw + bl) * th_h + bw * bl
                remaining -= th_h
                if k < tiers - 1:
                    shrink = int(rng.integers(2, max(3, min(bw, bl) // 3)))
                    bx, bz, bw, bl, by = bx + shrink, bz + shrink, bw - 2 * shrink, bl - 2 * shrink, ytop + 1
                    if bw < 6 or bl < 6:
                        break
            # 네온: 지붕 테두리 / 모서리 세로 띠
            if rng.random() < 0.3:
                neon = _pick(rng, NEON, [5, 4, 2])
                yt = ytop + 1
                d.fill(bx, yt, bz, bx + bw - 1, yt, bz, neon)
                d.fill(bx, yt, bz + bl - 1, bx + bw - 1, yt, bz + bl - 1, neon)
                d.fill(bx, yt, bz, bx, yt, bz + bl - 1, neon)
                d.fill(bx + bw - 1, yt, bz, bx + bw - 1, yt, bz + bl - 1, neon)
            if rng.random() < 0.25:
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
