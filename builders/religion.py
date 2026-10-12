"""종교의 층 (호크마). 접대 공간(거대 시계들 앞 돌기와 무대) ↔ 지정사서 방 (황금사과 F).

참고: reference/종교의 층 전경.png, reference/종교의 층 지정사서 방.png, PLAN.md 8절
("신성·웅장. 접대실은 끝없이 넓은 잿빛 신전 같은 공간, 움직이는 시계 장치, 멀리 거대 시계, 안개 속 겹친 복도,
거대 진자시계, 종소리. 지정사서 방: 회중시계 전등, 위층으로 이어지는 나선계단, 높은 책장").

원화(전경): 흑백. 기와처럼 줄지은 돌판 무대, 아래 기둥 줄(열주), 뒤로 겹쳐 선 거대한 흰 시계 판들(눈금·바늘),
가운데 뾰족 장식 달린 높은 막대(진자), 양옆 난간 달린 발코니 복도, 쇠 틀.
원화(방): 흰빛·잿빛, 양쪽 아주 높은 책장 벽(아래 판넬), 반들 바닥, 가운데 기둥을 감고 오르는 나선계단
(회중시계 전등이 매달림), 계단 아래 책상, 뒤 밝은 안개.

크기 (3072×512, 가장 큼): 무대 440×29 (서 있는 Y 150), 시계 판 7개 (반지름 60~130, 거리 150~420),
진자 막대 높이 330, 발코니 복도 12개, 먼 시계·복도는 600~1100 (Distant Horizons).
"""
from __future__ import annotations

import math

import numpy as np

from tools import shapes as S

from .technology import _chain_line, _line

Y0 = 150
BX, HW = 220, 14
ARRIVE_X = -170
ROOM_X = 4000
RY = 64
SLATE = ["minecraft:deepslate_tiles", "minecraft:polished_deepslate", "minecraft:deepslate_tiles", "minecraft:cobbled_deepslate"]


def stage(d, rng):
    """기와처럼 줄지은 돌판 (줄마다 반 칸 어긋남, 줄 끝 그림자), 앞 처마, 아래 열주."""
    xs, zs = np.arange(-BX, BX + 1), np.arange(-HW, HW + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    off = (Z % 2) * 1
    slate = np.array([d.id(s) for s in SLATE])
    ids = slate[(S.hash01((X + off) // 2, Z, seed=2201) * len(slate)).astype(int).clip(0, len(slate) - 1)]
    ids = np.where((X + off) % 2 == 0, d.id("minecraft:polished_deepslate"), ids)
    d.place(-BX, Y0 - 1, -HW, ids[:, None, :])
    d.fill(-BX, Y0 - 3, -HW, BX, Y0 - 2, HW, "minecraft:polished_deepslate")
    d.fill(-BX, Y0 - 2, HW + 1, BX, Y0 - 1, HW + 1, "minecraft:smooth_stone")                    # 앞 처마
    d.fill(-BX, Y0 - 3, HW + 1, BX, Y0 - 3, HW + 1, "minecraft:smooth_stone_slab[type=top]")
    d.fill(-BX, Y0, -HW, BX, Y0, -HW, "minecraft:smooth_stone_slab[type=bottom]")                # 뒤 턱
    for x in range(-BX + 10, BX, 30):                                                          # 열주
        for z in (HW - 2, -HW + 2):
            d.fill(x - 1, 0, z - 1, x + 1, Y0 - 4, z + 1, "minecraft:quartz_pillar[axis=y]")
            d.fill(x - 2, Y0 - 6, z - 2, x + 2, Y0 - 4, z + 2, "minecraft:smooth_stone")
            d.fill(x - 1, Y0 - 5, z - 1, x + 1, Y0 - 5, z + 1, "minecraft:quartz_pillar[axis=y]")
    d.fill(-BX - 30, -1, -60, BX + 30, -1, 60, "minecraft:polished_deepslate")


def clock(d, cx, cy, cz, R, h1=0.3, h2=2.1, rim="minecraft:polished_deepslate"):
    """거대 시계 판 (남쪽을 봄): 흰 판, 두꺼운 테, 열두 눈금(굵은 막대) + 60 작은 눈금, 시침·분침, 가운데 축.
    판은 한 겹 (뒤는 쇠 틀)."""
    n = int(R + 3)
    g = np.arange(-n, n + 1)
    X, Y = np.meshgrid(g, g, indexing="ij")
    r = np.hypot(X, Y)
    a = np.arctan2(Y, X)
    face = r <= R
    ids = np.where(S.hash01(X // 6, Y // 6, seed=2211) < 0.5, d.id("minecraft:white_concrete"), d.id("minecraft:calcite"))
    ids = np.where((r > R - 3) & face, d.id(rim), ids)
    ids = np.where((np.abs(r - R * 0.86) < 0.8) & face, d.id("minecraft:light_gray_concrete"), ids)       # 눈금 원
    tick = np.abs(((a / (2 * math.pi) * 60) % 1.0) - 0.5) > 0.42
    ids = np.where(tick & (r > R * 0.86) & (r < R - 3), d.id("minecraft:gray_concrete"), ids)
    big = np.abs(((a / (2 * math.pi) * 12) % 1.0) - 0.5) > 0.47
    ids = np.where(big & (r > R * 0.7) & (r < R - 3), d.id("minecraft:black_concrete"), ids)
    for ang, length, w in ((h1, 0.55, 2.2), (h2, 0.85, 1.4)):                                               # 바늘
        dist = np.abs(-np.sin(ang) * X + np.cos(ang) * Y)
        along = np.cos(ang) * X + np.sin(ang) * Y
        ids = np.where((dist < w) & (along > -R * 0.1) & (along < R * length), d.id("minecraft:black_concrete"), ids)
    ids = np.where(r < 3, d.id("minecraft:polished_blackstone"), ids)
    d.place(cx - n, cy - n, cz, np.where(face, ids, -1)[:, :, None].astype(np.int32))
    # 뒤 쇠 틀 (방사 살)
    for k in range(8):
        ang = k * math.pi / 4
        _line(d, (cx, cy, cz - 2), (cx + R * math.cos(ang), cy + R * math.sin(ang), cz - 2), "minecraft:polished_deepslate")


def pendulum(d, x=0, z=-60):
    """가운데 높은 막대 (진자): 위 뾰족 마름모 장식, 아래 무대 뒤 받침 틀."""
    top = Y0 + 330
    d.fill(x - 1, Y0, z - 1, x + 1, top, z + 1, "minecraft:polished_deepslate")
    for k in range(-10, 11):                                    # 마름모 장식
        w = 10 - abs(k)
        d.fill(x - w // 2, Y0 + 70 + k, z, x + w // 2, Y0 + 70 + k, z, "minecraft:polished_blackstone")
    d.fill(x - 1, Y0 + 62, z, x + 1, Y0 + 78, z, "minecraft:white_concrete")
    d.fill(x - 7, Y0, z - 4, x + 7, Y0 + 30, z + 4, "minecraft:polished_deepslate")      # 받침 틀
    d.fill(x - 6, Y0, z - 3, x + 6, Y0 + 29, z + 3, "minecraft:air")
    d.fill(x - 1, Y0, z - 1, x + 1, Y0 + 29, z + 1, "minecraft:polished_deepslate")
    for y in range(Y0 + 2, Y0 + 30, 7):
        d.fill(x - 7, y, z + 4, x + 7, y, z + 4, "minecraft:iron_bars")


def balconies(d, rng, n=12, rmin=60, rmax=300):
    """안개 속 겹친 복도: 난간 달린 발코니 판들 (높이·깊이 제각각)."""
    for _ in range(n):
        x0 = int(rng.uniform(-rmax, rmax))
        z = int(rng.uniform(-rmax, -rmin))
        y = int(rng.uniform(Y0 - 20, Y0 + 160))
        L = int(rng.integers(30, 90))
        d.fill(x0, y, z - 3, x0 + L, y, z + 3, "minecraft:polished_deepslate")
        d.fill(x0, y + 1, z + 3, x0 + L, y + 1, z + 3, "minecraft:iron_bars")
        for x in range(x0, x0 + L + 1, 6):
            d.fill(x, y - 12, z, x, y - 1, z, "minecraft:polished_deepslate")
            _line(d, (x, y - 10, z), (x + 3, y - 1, z), "minecraft:iron_bars")


def framework(d, rng):
    """쇠 틀 (시계들 사이 가로·세로 들보)."""
    for _ in range(40):
        x, y, z = int(rng.uniform(-350, 350)), int(rng.uniform(Y0, Y0 + 300)), int(rng.uniform(-420, -140))
        if rng.random() < 0.5:
            d.fill(x, y, z, x + int(rng.integers(30, 120)), y + 1, z + 1, "minecraft:polished_deepslate")
        else:
            d.fill(x, y, z, x + 1, y + int(rng.integers(30, 160)), z + 1, "minecraft:polished_deepslate")


# ---------------------------------------------------------------- 호크마 방
RW, RD, RH = 12, 18, 32


def hokma_room(d, ox=ROOM_X):
    y0, yt = RY, RY + RH
    xs, zs = np.arange(ox - RW, ox + RW + 1), np.arange(-RD, RD + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    fl = np.where(((X - ox) % 6 == 0) | (Z % 6 == 0), d.id("minecraft:polished_diorite"), d.id("minecraft:smooth_quartz"))
    d.place(ox - RW, y0 - 1, -RD, fl[:, None, :])
    x0, x1, z0, z1 = ox - RW - 1, ox + RW + 1, -RD - 1, RD + 1
    # 양쪽 아주 높은 책장 벽 (아래 판넬, 위 처마 띠), 뒤·앞은 밝은 벽
    for xw in (x0, x1):
        d.fill(xw, y0, z0, xw, yt, z1, "minecraft:bookshelf")
        d.fill(xw, y0, z0, xw, y0 + 4, z1, "minecraft:smooth_quartz")
        for z in range(z0, z1 + 1, 6):
            d.fill(xw, y0, z, xw, yt, z, "minecraft:quartz_pillar[axis=y]")
        for y in (y0 + 5, y0 + 18):
            d.fill(xw, y, z0, xw, y, z1, "minecraft:smooth_quartz")
        inner = xw + (1 if xw < ox else -1)
        d.fill(inner, y0 + 18, z0, inner, y0 + 18, z1, "minecraft:smooth_quartz_slab[type=top]")
    d.fill(x0, y0, z0, x1, yt, z0, "minecraft:white_concrete")
    d.fill(x0, y0, z1, x1, yt, z1, "minecraft:smooth_quartz")
    d.fill(x0, yt, z0, x1, yt, z1, "minecraft:smooth_quartz")
    # 가운데 나선계단: 기둥을 감고 오름 (반지름 5, 한 바퀴 16단), 바깥 난간, 회중시계 전등(랜턴)이 매달림
    cx, cz = ox, -RD + 10
    d.fill(cx, y0, cz, cx, yt - 1, cz, "minecraft:polished_diorite")
    steps = RH - 2
    for k in range(steps):
        a = k * 2 * math.pi / 16
        y = y0 + k
        for rr in range(1, 6):
            for da in (-0.12, 0.0, 0.12):
                x = cx + int(round(rr * math.cos(a + da)))
                z = cz + int(round(rr * math.sin(a + da)))
                if d.get(x, y, z) == "minecraft:air":
                    d.set(x, y, z, "minecraft:smooth_quartz_slab[type=top]")
        ax, az = cx + int(round(6 * math.cos(a))), cz + int(round(6 * math.sin(a)))
        d.set(ax, y + 1, az, "minecraft:iron_bars")
        if k % 3 == 1:
            lx, lz = cx + int(round(3 * math.cos(a + 0.5))), cz + int(round(3 * math.sin(a + 0.5)))
            d.set(lx, y - 3, lz, "minecraft:lantern[hanging=true]")
            d.set(lx, y - 2, lz, "minecraft:iron_chain[axis=y]")
    # 계단 아래 책상
    d.fill(cx - 3, y0, cz + 6, cx + 3, y0, cz + 7, "minecraft:smooth_quartz_slab[type=top]")
    d.set(cx - 1, y0 + 1, cz + 6, "minecraft:white_carpet")
    # 책 더미 (책장 아래)
    rng = np.random.default_rng(2231)
    for _ in range(16):
        x = x0 + 1 if rng.random() < 0.5 else x1 - 1
        z = int(rng.integers(-RD + 2, RD - 1))
        for y in range(int(rng.integers(1, 3))):
            d.set(x, y0 + y, z, ["minecraft:light_gray_terracotta", "minecraft:white_terracotta", "minecraft:gray_terracotta"][int(rng.integers(3))])
    for z in range(-RD + 3, RD, 6):
        for y in (y0 + 10, y0 + 22):
            d.set(ox - 6, y, z, "minecraft:light[level=12]")
            d.set(ox + 6, y, z, "minecraft:light[level=12]")
    d.set_biome(ox - 40, -40, ox + 40, 40, "ruina:religion_room")
    return cx, cz, y0 + steps


def build(b):
    from . import fragment as F
    d = b.dim("religion")
    rng = np.random.default_rng(2301)
    stage(d, rng)
    for (cx, cy, cz, R) in ((-230, Y0 + 120, -190, 110), (60, Y0 + 150, -250, 130), (290, Y0 + 190, -210, 90),
                            (-120, Y0 + 60, -150, 70), (200, Y0 + 50, -160, 60), (-330, Y0 + 230, -300, 100),
                            (330, Y0 + 260, -330, 120)):
        clock(d, cx, cy, cz, R, h1=rng.uniform(0, 6.3), h2=rng.uniform(0, 6.3))
    for i in range(8):                                          # ③ 먼 시계 (DH)
        a = -math.pi / 2 + (i - 3.5) * 0.35
        clock(d, int(800 * math.cos(a)), Y0 + int(rng.uniform(100, 300)), int(800 * math.sin(a)), int(rng.uniform(140, 200)),
              h1=rng.uniform(0, 6.3), h2=rng.uniform(0, 6.3))
    pendulum(d)
    balconies(d, rng)
    balconies(d, rng, n=10, rmin=500, rmax=1000)
    framework(d, rng)
    hokma_room(d)
    F.stage(b, d, "apple", (F.APPLE_P, F.APPLE), "종교의 층", (ARRIVE_X + 0.5, Y0, 0.5, -90), (ROOM_X + 0.5, RY, RD - 2.5, 180))
    # 원화 속 출구(빛나는 문·창)는 조형물로만 — 층 사이 이동은 조각 F (fragment.finish)
    b.extra_checks.append({"what": "호크마 방 바이옴", "cmd": f"execute in {d.dim} if biome {ROOM_X} {RY} 0 ruina:religion_room",
                           "expect": True})


_GREY = dict(sky=((150, 150, 150), (210, 210, 210)), fog=(190, 190, 190), stars=0, night=False)
PREVIEW = [
    {"file": "religion_compare_stage.png", "ref": "종교의 층 전경.png", "cam": (0.5, Y0 + 6, 46), "look": (0.5, Y0 + 50, -150),
     "kw": dict(fov=82, max_dist=900, fog_dist=500, **_GREY),
     "title": "종교의 층 — 원화(위) / 맵(아래): 무대 앞쪽에서 북쪽",
     "notes": ["기와 돌판 무대·열주, 겹쳐 선 거대 시계 판들(눈금·바늘), 가운데 진자 막대, 난간 발코니 복도, 쇠 틀"]},
    {"file": "religion_compare_room.png", "ref": "종교의 층 지정사서 방.png", "cam": (ROOM_X + 0.5, RY + 3, RD - 1),
     "look": (ROOM_X + 0.5, RY + 12, -RD), "kw": dict(fov=78, max_dist=120, sky=((180, 180, 180), (220, 220, 220)),
                                                       fog=(200, 200, 200), fog_dist=80, stars=0, night=False),
     "title": "호크마 방 — 원화(위) / 맵(아래)",
     "notes": ["양쪽 높은 책장 벽, 반들 바닥, 가운데 나선계단(꼭대기 = 총류의 층), 회중시계 전등, 계단 아래 책상"]},
]
