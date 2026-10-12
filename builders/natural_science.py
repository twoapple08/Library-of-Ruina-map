"""자연과학의 층 (티페리트). 접대 공간(황금 돔 앞 무대) ↔ 지정사서 방 (금발판 F), 돔 색감 전환 (마그마크림 F).

참고: reference/자연과학의 층 전경.png (금빛), reference/자연과학의 층 전경 (색 바뀐 판).jpg (어두운 청록),
reference/자연과학의 층 지정사서 방.png, PLAN.md 8절 ("매우 넓고 화려한 방 하나가 중심").

원화(전경): 갈비뼈 같은 살이 꼭대기 빛 구멍으로 모이는 반원 돔, 벽 가득 촛불 든 아치 감실, 겹겹이 작아지는 아치 끝의
빛나는 뾰족 아치 문, 가운데 받침대 위 금잔·파란 수정, 앞 무대(모자이크 띠 + 붉은 카펫), 무대 앞면 금테 유리판,
아래로 왼쪽 파란 / 오른쪽 주황 휘장.
색 바뀐 판: 같은 구도, 돔이 어두운 청록, 감실 빛이 차가운 흰빛, 받침대 없음.
원화(방): 금빛 나무 책장 벽(사다리), 큰 아치 창(마름모 문양, 청록 보석) — 다음 층 입구, 붉은 카펫이 계단 위
둥근 탁자·안락의자로, 양옆 체크무늬 바닥, 갈비 천장, 왼쪽 어두운 아치 문, A자 사다리.

크기 (1024×400, 사람 기준): 돔 반지름 90·높이 130, 무대 300×15 (서 있는 Y 100), 휘장 Y 30까지.
색감 전환(티페리트 F, 청록 돔)은 지금 만들지 않음 (사용자 2026-10-12). 청록 색표 TEAL·VARIANT_DX 는 나중을 위해 남김.
"""
from __future__ import annotations

import math

import numpy as np

from tools import shapes as S

Y0 = 100
DOME_R, DOME_H = 90, 130
DZ = -6                   # 돔 중심 z (무대 바로 뒤)
STAGE_X, STAGE_Z0, STAGE_Z1 = 150, 2, 16
VARIANT_DX = 1400
ARRIVE = (0.5, Y0, 9.5, 180)
ROOM_X = 4000
RY = 64

GOLD = {
    "wall": ["minecraft:smooth_sandstone", "minecraft:cut_sandstone", "minecraft:sandstone", "minecraft:smooth_sandstone"],
    "rib": "minecraft:gold_block", "rib2": "minecraft:raw_gold_block",
    "niche": "minecraft:ochre_froglight", "frame": "minecraft:gold_block",
    "door": "minecraft:pearlescent_froglight", "oculus": "minecraft:pearlescent_froglight",
    "floor": "minecraft:cut_sandstone", "tile": ["minecraft:chiseled_sandstone", "minecraft:cut_red_sandstone",
                                                 "minecraft:smooth_red_sandstone"],
    "carpet": "minecraft:red_wool", "glass": "minecraft:yellow_stained_glass", "pedestal": True,
}
TEAL = {   # 색 바뀐 판 (reference/자연과학의 층 전경 (색 바뀐 판).jpg)
    "wall": ["minecraft:polished_deepslate", "minecraft:deepslate_tiles", "minecraft:tuff", "minecraft:polished_deepslate"],
    "rib": "minecraft:dark_prismarine", "rib2": "minecraft:prismarine_bricks",
    "niche": "minecraft:sea_lantern", "frame": "minecraft:polished_blackstone",
    "door": "minecraft:sea_lantern", "oculus": "minecraft:sea_lantern",
    "floor": "minecraft:polished_deepslate", "tile": ["minecraft:deepslate_tiles", "minecraft:polished_blackstone_bricks",
                                                       "minecraft:cracked_deepslate_tiles"],
    "carpet": "minecraft:gray_wool", "glass": "minecraft:light_blue_stained_glass", "pedestal": False,
}


def dome(d, ox, pal):
    """북쪽 반원 돔 (타원 껍질), 갈비살 24줄, 감실 격자, 꼭대기 빛 구멍."""
    walls = np.array([d.id(s) for s in pal["wall"]])
    rib, rib2, niche, frame = d.id(pal["rib"]), d.id(pal["rib2"]), d.id(pal["niche"]), d.id(pal["frame"])
    R = DOME_R + 1
    xs, zs = np.arange(-R, R + 1), np.arange(-R, 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    A = np.arctan2(-Z, X)                                   # 0..pi (동 → 북 → 서)
    for y in range(Y0 - 1, Y0 + DOME_H + 1):
        t = (y - (Y0 - 1)) / DOME_H
        r = DOME_R * math.sqrt(max(0.0, 1 - t * t))
        rr = np.hypot(X, Z)
        shell = (rr <= r + 0.5) & (rr > r - 1.0) & (Z <= 0)
        if t > 0.97:
            shell = (rr <= r + 0.5) & (Z <= 0)
        ids = walls[(S.hash01((A * 40).astype(int), np.full_like(X, y // 3), seed=1501) * len(walls)).astype(int)
                    .clip(0, len(walls) - 1)]
        k = A / math.pi * 24
        ids = np.where(np.abs(k - np.round(k)) < 0.06 + 0.5 / max(r, 1), np.where(y % 6 < 3, rib, rib2), ids)
        # 감실: 각도 격자 × 높이 격자 (아래 70%만), 1×2 빛 + 위 아치 테
        kk = A / math.pi * 40
        cell = (np.abs(kk - np.round(kk) - 0.5) < 0.18) & (t < 0.7)
        yy = (y - Y0) % 9
        ids = np.where(cell & (yy in (3, 4)), niche, ids)
        ids = np.where(cell & (yy == 5), frame, ids)
        if t > 0.94:
            ids = np.where(rr < DOME_R * 0.12, d.id(pal["oculus"]), ids)
        d.place(ox - R, y, -R + DZ, np.where(shell, ids, -1)[:, None, :].astype(np.int32))
    # 돔 바닥
    disk = (np.hypot(X, Z) <= DOME_R) & (Z <= 0)
    d.place(ox - R, Y0 - 1, -R + DZ, np.where(disk, d.id(pal["floor"]), -1)[:, None, :].astype(np.int32))


def arches(d, ox, pal):
    """겹겹이 작아지는 아치 (돔 안쪽 → 빛나는 뾰족 아치 문)."""
    for k, z in enumerate(range(DZ - 30, DZ - DOME_R + 4, -10)):
        w = 46 - k * 5
        h = 90 - k * 9
        for x in range(-w, w + 1):
            top = int(h * math.sqrt(max(0.0, 1 - (x / w) ** 2)) ** 0.8)
            for t in (0, 1):
                d.set(ox + x, Y0 + top + t, z, pal["rib"] if t == 0 else pal["rib2"])
        for xx in (-w, w):
            d.fill(ox + xx, Y0, z, ox + xx, Y0 + 10, z, pal["rib"])
    zd = DZ - DOME_R + 2
    for x in range(-7, 8):                                   # 뾰족 아치 문 (빛)
        top = int(26 - 10 * (abs(x) / 7) ** 1.6)
        d.fill(ox + x, Y0, zd, ox + x, Y0 + top, zd, pal["door"])
    d.fill(ox - 9, Y0 - 1, zd + 1, ox + 9, Y0 - 1, zd + 6, pal["frame"])
    d.fill(ox - 8, Y0, zd + 4, ox + 8, Y0, zd + 6, pal["tile"][0])       # 문 앞 단


def pedestal(d, ox):
    """가운데 받침대: 금 기둥, 넓은 그릇, 금잔·파란 수정 상자·작은 불꽃."""
    x, z = ox, DZ - 16
    d.fill(x - 1, Y0, z - 1, x + 1, Y0, z + 1, "minecraft:chiseled_sandstone")
    d.fill(x, Y0 + 1, z, x, Y0 + 3, z, "minecraft:gold_block")
    d.fill(x - 2, Y0 + 4, z - 1, x + 2, Y0 + 4, z + 1, "minecraft:gold_block")
    d.set(x - 1, Y0 + 5, z, "minecraft:light_blue_stained_glass")
    d.set(x, Y0 + 5, z, "minecraft:gold_block")
    d.set(x, Y0 + 6, z, "minecraft:shroomlight")
    d.set(x + 1, Y0 + 5, z, "minecraft:candle[lit=true,candles=1]")


def stage(d, ox, pal):
    """앞 무대: 모자이크 띠 / 붉은 카펫 / 모자이크 띠, 앞 가장자리 금 난간, 앞면 금테 유리판, 아래 휘장 (왼쪽 파랑, 오른쪽 주황)."""
    tile = np.array([d.id(s) for s in pal["tile"]])
    xs, zs = np.arange(-STAGE_X, STAGE_X + 1), np.arange(STAGE_Z0 - 8, STAGE_Z1 + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    ids = tile[(S.hash01(X // 2, Z, seed=1511) * len(tile)).astype(int).clip(0, len(tile) - 1)]
    ids = np.where((Z >= STAGE_Z0 + 4) & (Z <= STAGE_Z1 - 4), d.id(pal["carpet"]), ids)
    ids = np.where(X % 4 == 0, np.where((Z < STAGE_Z0 + 4) | (Z > STAGE_Z1 - 4), d.id(pal["frame"]), ids), ids)
    d.place(ox - STAGE_X, Y0 - 1, STAGE_Z0 - 8, ids[:, None, :])
    zf = STAGE_Z1 + 1
    d.fill(ox - STAGE_X, Y0 - 1, zf, ox + STAGE_X, Y0 - 1, zf, pal["frame"])
    d.fill(ox - STAGE_X, Y0, zf, ox + STAGE_X, Y0, zf, "minecraft:light_weighted_pressure_plate")   # 금 난간 윗줄
    # 앞면: 금테 유리판 (높이 18, 위로 휘는 테)
    for x in range(-STAGE_X, STAGE_X + 1):
        d.fill(ox + x, Y0 - 19, zf, ox + x, Y0 - 2, zf, pal["glass"])
        if x % 40 == 0:
            d.fill(ox + x, Y0 - 19, zf, ox + x, Y0 - 2, zf, pal["frame"])
        bend = int(6 * (1 - (((x % 40) - 20) / 20) ** 2))
        d.set(ox + x, Y0 - 19 + bend, zf, pal["frame"])
        d.set(ox + x, Y0 - 12 + bend, zf, pal["frame"])
    d.fill(ox, Y0 - 19, zf, ox, Y0 - 2, zf, pal["frame"])
    # 휘장: 왼쪽 파랑, 오른쪽 주황 (세로 주름 + 주황엔 빛 줄기)
    blue = ["minecraft:blue_wool", "minecraft:light_blue_wool", "minecraft:cyan_wool", "minecraft:blue_wool"]
    orange = ["minecraft:orange_wool", "minecraft:red_wool", "minecraft:orange_wool", "minecraft:yellow_wool"]
    for x in range(-STAGE_X, STAGE_X + 1):
        cols = blue if x < 0 else orange
        st = cols[(x // 2) % len(cols)]
        bottom = 30 + int(4 * math.sin(x / 6))
        d.fill(ox + x, bottom, zf + 1 + (x // 2) % 2, ox + x, Y0 - 20, zf + 1 + (x // 2) % 2, st)
        if x > 0 and x % 9 == 0:
            d.fill(ox + x, bottom + 5, zf + 2, ox + x, Y0 - 30, zf + 2, "minecraft:ochre_froglight")


def reception(d, ox, pal):
    dome(d, ox, pal)
    arches(d, ox, pal)
    if pal["pedestal"]:
        pedestal(d, ox)
    stage(d, ox, pal)
    for x in range(-60, 61, 12):   # 돔 안 고른 빛 (보이지 않는 빛 블록)
        for z in range(DZ - 70, DZ, 12):
            if x * x + (z - DZ) ** 2 < 80 ** 2 and d.get(ox + x, Y0 + 30, z) == "minecraft:air":
                d.set(ox + x, Y0 + 30, z, "minecraft:light[level=15]")


# ---------------------------------------------------------------- 티페리트 방
RW, RD, RH = 13, 12, 20


def tiphereth_room(d, ox=ROOM_X):
    y0, yt = RY, RY + RH
    xs, zs = np.arange(ox - RW, ox + RW + 1), np.arange(-RD, RD + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    chk = np.where(((X + Z) % 2) == 0, d.id("minecraft:smooth_quartz"), d.id("minecraft:smooth_sandstone"))
    chk = np.where(np.abs(X - ox) <= 2, d.id("minecraft:red_wool"), chk)             # 붉은 카펫 길
    d.place(ox - RW, y0 - 1, -RD, chk[:, None, :])
    x0, x1, z0, z1 = ox - RW - 1, ox + RW + 1, -RD - 1, RD + 1
    for (a0, b0, a1, b1) in ((x0, z0, x1, z0), (x0, z1, x1, z1), (x0, z0, x0, z1), (x1, z0, x1, z1)):
        d.fill(a0, y0, b0, a1, yt, b1, "minecraft:bookshelf")
        for y in range(y0 + 4, yt, 4):
            d.fill(a0, y, b0, a1, y, b1, "minecraft:oak_planks")
        d.fill(a0, y0, b0, a1, y0, b1, "minecraft:stripped_oak_wood")
    for z in range(-RD, RD + 1, 4):                            # 금빛 기둥
        d.fill(x0 + 1, y0, z, x0 + 1, yt - 1, z, "minecraft:stripped_oak_log[axis=y]")
        d.fill(x1 - 1, y0, z, x1 - 1, yt - 1, z, "minecraft:stripped_oak_log[axis=y]")
    # 갈비 천장 (둥근 나무 살)
    for z in range(z0, z1 + 1):
        for x in range(-RW - 1, RW + 2):
            y = yt + int(5 * math.sqrt(max(0.0, 1 - (x / (RW + 1)) ** 2)))
            d.set(ox + x, y, z, "minecraft:oak_planks" if z % 3 else "minecraft:stripped_oak_log[axis=x]")
        for y in range(yt, yt + 6):
            d.set(x0, y, z, "minecraft:oak_planks")
            d.set(x1, y, z, "minecraft:oak_planks")
    # 큰 아치 창 (북쪽 벽) + 마름모 문양·청록 보석 = 다음 층 입구
    for x in range(-5, 6):
        top = int(16 + 3 * math.sqrt(max(0.0, 1 - (x / 5) ** 2)))
        d.fill(ox + x, y0 + 3, z0, ox + x, y0 + top, z0, "minecraft:pearlescent_froglight")
        if x % 3 == 0:   # 창살 (창 면 안에 — 앞을 막지 않게)
            d.fill(ox + x, y0 + 3, z0, ox + x, y0 + top - 4, z0, "minecraft:stripped_oak_log[axis=y]")
    for k in range(-3, 4):                                     # 마름모 테 (창 면 안에)
        d.set(ox + k, y0 + 15 + (3 - abs(k)), z0, "minecraft:gold_block")
        d.set(ox + k, y0 + 15 - (3 - abs(k)), z0, "minecraft:gold_block")
    d.set(ox, y0 + 15, z0, "minecraft:diamond_block")         # 청록 보석
    # 창 앞 단 3칸 + 둥근 탁자 + 안락의자
    for k in range(3):
        d.fill(ox - 6, y0 + k, z0 + 1, ox + 6, y0 + k, z0 + 6 - k * 2, "minecraft:smooth_sandstone")
        d.fill(ox - 2, y0 + k, z0 + 7 - k * 2, ox + 2, y0 + k, z0 + 7 - k * 2, "minecraft:red_wool")
    d.set(ox - 1, y0 + 3, z0 + 3, "minecraft:oak_fence")
    d.set(ox - 1, y0 + 4, z0 + 3, "minecraft:oak_pressure_plate")
    d.set(ox + 2, y0 + 3, z0 + 3, "minecraft:oak_stairs[facing=east]")
    d.set(ox + 3, y0 + 4, z0 + 3, "minecraft:oak_trapdoor[facing=west,open=true]")
    # 사다리 (왼쪽 벽), A자 사다리 (오른쪽), 왼쪽 어두운 아치 문
    d.fill(x0 + 1, y0, -6, x0 + 1, yt - 2, -6, "minecraft:ladder[facing=east]")
    d.fill(ox + 8, y0, 5, ox + 8, y0 + 3, 5, "minecraft:ladder[facing=north]")
    d.fill(ox + 8, y0, 6, ox + 8, y0 + 3, 6, "minecraft:oak_planks")
    d.fill(x0, y0, 2, x0, y0 + 5, 5, "minecraft:black_concrete")
    d.fill(x0 + 1, y0 + 5, 2, x0 + 1, y0 + 5, 5, "minecraft:oak_stairs[facing=west,half=top]")
    # 바닥 책 더미
    rng = np.random.default_rng(1531)
    for _ in range(18):
        x, z = ox + int(rng.integers(-RW + 1, RW)), int(rng.integers(-RD + 7, RD))
        if abs(x - ox) <= 3 or d.get(x, y0, z) != "minecraft:air":
            continue
        for y in range(int(rng.integers(1, 3))):
            d.set(x, y0 + y, z, ["minecraft:brown_terracotta", "minecraft:yellow_terracotta",
                                 "minecraft:terracotta"][int(rng.integers(3))])
    for x in range(-RW + 3, RW, 6):
        for z in range(-RD + 3, RD, 6):
            if d.get(ox + x, yt - 2, z) == "minecraft:air":
                d.set(ox + x, yt - 2, z, "minecraft:light[level=13]")
    d.set_biome(ox - 40, -40, ox + 40, 40, "ruina:natural_science_room")


def build(b):
    from . import fragment as F
    d = b.dim("natural_science")
    reception(d, 0, GOLD)
    tiphereth_room(d)
    F.stage(b, d, "gplate", "자연과학의 층", ARRIVE, (ROOM_X + 0.5, RY, RD - 2.5, 180))
    # 원화 속 출구(빛나는 문·창)는 조형물로만 — 층 사이 이동은 세피라 아이템 (모드)
    b.extra_checks += [
        {"what": "티페리트 방 바이옴", "cmd": f"execute in {d.dim} if biome {ROOM_X} {RY} 0 ruina:natural_science_room",
         "expect": True},
    ]


_GOLDSKY = dict(sky=((90, 70, 30), (160, 120, 50)), fog=(150, 110, 50), stars=0, night=False)
PREVIEW = [
    {"file": "natural_science_compare_stage.png", "ref": "자연과학의 층 전경.png", "cam": (0.5, Y0 + 3, 40),
     "look": (0.5, Y0 + 22, -60), "kw": dict(fov=78, max_dist=400, fog_dist=300, **_GOLDSKY),
     "title": "자연과학의 층 — 원화(위) / 맵(아래): 무대 앞에서 돔 쪽",
     "notes": ["황금 반원 돔(갈비살·촛불 감실·빛 구멍), 겹 아치 끝 빛나는 문, 받침대 금잔", "무대(모자이크·붉은 카펫), 금테 유리판, 파랑/주황 휘장"]},
    {"file": "natural_science_compare_room.png", "ref": "자연과학의 층 지정사서 방.png", "cam": (ROOM_X + 0.5, RY + 2.5, RD - 1),
     "look": (ROOM_X + 0.5, RY + 8, -RD), "kw": dict(fov=80, max_dist=120, sky=((60, 44, 20), (120, 90, 40)),
                                                      fog=(120, 90, 40), fog_dist=70, stars=0),
     "title": "티페리트 방 — 원화(위) / 맵(아래)",
     "notes": ["금빛 책장 벽·사다리, 큰 아치 창(마름모·보석), 붉은 카펫 계단 위 탁자·의자, 체크무늬 바닥"]},
]
