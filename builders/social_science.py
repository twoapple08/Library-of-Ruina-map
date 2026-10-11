"""사회과학의 층 (헤세드). 접대 공간(가라앉은 난파선 갑판) ↔ 지정사서 방 (금블럭 F).

참고: reference/사회과학의 층 전경.png, reference/사회과학의 층 지정사서 방.png, PLAN.md 8절
("바다 깊이 가라앉은 폐허 도시, 해저 난파선이 활동 무대, 물고기와 폐차가 떠다님, 멀리 도시 잔해. 지정사서 방은 커피가 있는 개인실").

원화(전경): 낡은 판자 갑판(구멍), 아래 선체 옆면과 밧줄 감긴 계류 기둥·처진 밧줄, 해초,
뒤로 소용돌이치는 푸른 물결, 빛기둥, 푸른 안개 속 잠긴 도시, 기울어진 채 떠다니는 폐차.
원화(방): 푸른 어둠의 개인실, 격자 큰 창 너머 잠긴 도시, 바닥의 창살 그림자 빛, 소파·쿠션, 낮은 탁자,
커피 드리퍼 놓인 긴 탁자, 뒤 선반(병·상자), 오른쪽 책장, 창틀 옆 푸른 빛줄.

물속 표현: 진짜 물을 채우면 블록 수백만 + 헤엄쳐야 해서, 공기 + 짙은 푸른 안개 + 떠다니는 입자로 (폐차·물고기는 공중에 뜸).
크기 (2048×400): 갑판 300×21 (서 있는 Y 100), 바닥 모래 Y 20, 잠긴 도시 400 안쪽 + 먼 겹.
"""
from __future__ import annotations

import math

import numpy as np

from tools import shapes as S

from .city import build_city

Y0 = 100
BX, HW = 150, 10
FLOOR = 20
ARRIVE_X = -110
ROOM_X = 4000
RY = 64
DECK = ["minecraft:dark_oak_planks", "minecraft:spruce_planks", "minecraft:stripped_dark_oak_wood", "minecraft:dark_oak_planks",
        "minecraft:mangrove_planks"]
SUNK_PAL = {
    "walls": (["minecraft:dark_prismarine", "minecraft:prismarine_bricks", "minecraft:cyan_terracotta",
               "minecraft:blue_terracotta", "minecraft:polished_deepslate", "minecraft:warped_planks"], [16, 10, 14, 14, 10, 4]),
    "lit": (["minecraft:sea_lantern", "minecraft:light_blue_stained_glass"], [30, 70]),
    "neon": (["minecraft:sea_lantern"], [1]),
    "trim": (["minecraft:dark_prismarine", "minecraft:polished_deepslate"], [1, 1]),
    "corner_neon": 0.0, "corners": 1, "roof_neon": 0.0, "lit_ratio": (0.02, 0.12),
}


def deck(d, rng):
    """난파선 갑판: 길이 방향 판자 (색·결 제각각, 금·구멍), 뒤 가장자리 부서진 뱃전, 앞 선체 옆면 + 계류 기둥·밧줄."""
    xs, zs = np.arange(-BX, BX + 1), np.arange(-HW, HW + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    off = (S.hash01(Z, seed=1801) * 9).astype(int)
    ids = np.array([d.id(s) for s in DECK])[(S.hash01((X + off) // 9, Z, seed=1802) * len(DECK)).astype(int).clip(0, len(DECK) - 1)]
    hole = (np.hypot((X + 60) / 4.0, (Z - 2) / 2.0) < 1) | (np.hypot((X - 70) / 3.0, (Z + 3) / 2.0) < 1)
    ids = np.where(hole, -1, ids)
    d.place(-BX, Y0 - 1, -HW, ids[:, None, :])
    d.fill(-BX, Y0 - 3, -HW, BX, Y0 - 2, HW, "minecraft:dark_oak_planks")
    for hx in (-60, 70):                                         # 구멍 아래 어두운 속
        d.fill(hx - 4, Y0 - 3, -2, hx + 4, Y0 - 2, 4, "minecraft:air")
    # 뒤 뱃전 (군데군데 부서짐)
    for x in range(-BX, BX + 1):
        h = 2 if S.hash01(np.array(x // 11), seed=1803) > 0.25 else 0
        if h:
            d.fill(x, Y0, -HW - 1, x, Y0 + h - 1, -HW - 1, "minecraft:dark_oak_planks")
            d.set(x, Y0 + h, -HW - 1, "minecraft:dark_oak_slab[type=bottom]")
    # 앞 선체 옆면 (아래로 기울며 모래까지), 가로 판자
    for y in range(FLOOR, Y0 - 1):
        t = (Y0 - 1 - y) / (Y0 - 1 - FLOOR)
        z = HW + 1 - int(8 * t * t)
        st = DECK[(y // 2 + 1) % len(DECK)]
        d.fill(-BX, y, z, BX, y, z, st)
        if y % 6 == 0:
            d.fill(-BX, y, z + 1, BX, y, z + 1, "minecraft:stripped_dark_oak_log[axis=x]")
    # 계류 기둥 + 감긴 밧줄 + 기둥 사이 처진 밧줄 (원화 앞쪽)
    posts = list(range(-BX + 10, BX, 50))
    for x in posts:
        d.fill(x, Y0 - 14, HW + 2, x, Y0, HW + 2, "minecraft:dark_oak_log[axis=y]")
        d.set(x, Y0 + 1, HW + 2, "minecraft:dark_oak_slab[type=bottom]")
        d.fill(x, Y0 - 4, HW + 3, x, Y0 - 1, HW + 3, "minecraft:mangrove_roots")
    for a, b2 in zip(posts, posts[1:]):
        for t in np.linspace(0, 1, 120):
            x = a + (b2 - a) * t
            y = Y0 - 3 - 18 * 4 * t * (1 - t)
            d.set(int(x), int(y), HW + 3, "minecraft:mangrove_roots")
    # 해초 (선체 아래·모래 위)
    for _ in range(300):
        x, z = int(rng.uniform(-BX - 40, BX + 40)), int(rng.uniform(HW, HW + 40))
        h = int(rng.integers(4, 18))
        d.fill(x, FLOOR, z, x, FLOOR + h - 2, z, "minecraft:twisting_vines_plant")
        d.set(x, FLOOR + h - 1, z, "minecraft:twisting_vines")


def seafloor(d, R=420):
    xs = np.arange(-R, R + 1)
    for x0 in range(-R, R + 1, 120):
        for z0 in range(-R, R + 1, 120):
            X, Z = np.meshgrid(np.arange(x0, min(x0 + 120, R + 1)), np.arange(z0, min(z0 + 120, R + 1)), indexing="ij")
            h = S.hash01(X // 7, Z // 7, seed=1811)
            ids = np.where(h < 0.6, d.id("minecraft:sand"), np.where(h < 0.85, d.id("minecraft:gravel"),
                                                                       d.id("minecraft:prismarine")))
            d.place(x0, FLOOR - 1, z0, ids[:, None, :])
            d.place(x0, FLOOR - 2, z0, np.full_like(ids, d.id("minecraft:sandstone"))[:, None, :])


def currents(d, rng, n=10):
    """소용돌이치는 물결 (원화 배경): 세로 판에 나선 띠 (푸른 유리), 가운데에 빛기둥."""
    for _ in range(n):
        cx, cz = int(rng.uniform(-300, 300)), int(rng.uniform(-260, -90))
        cy = int(rng.uniform(Y0 + 10, Y0 + 120))
        R = rng.uniform(25, 55)
        for t in np.linspace(0, 1, 1400):
            a = t * 3.2 * 2 * math.pi
            r = R * t
            x, y = cx + r * math.cos(a), cy + r * math.sin(a) * 0.8
            w = 1 + int(4 * t)                                  # 바깥으로 갈수록 굵은 띠
            st = "minecraft:light_blue_stained_glass" if t > 0.3 else "minecraft:cyan_stained_glass"
            d.fill(int(x) - w // 2, int(y) - w // 2, cz, int(x) + w // 2, int(y) + w // 2, cz + 1, st)
            if int(t * 1400) % 37 == 0:
                d.set(int(x), int(y), cz, "minecraft:sea_lantern")
        # 빛기둥 (아래 모래에서 위로)
        d.fill(cx - 1, FLOOR, cz - 1, cx + 1, cy + int(R), cz + 1, "minecraft:light_blue_stained_glass")
        d.fill(cx, FLOOR, cz, cx, cy + int(R), cz, "minecraft:sea_lantern")


def floating(b, d, rng, cars=12, fish=40):
    """떠다니는 폐차 (블록 디스플레이 3개: 차체·지붕·바퀴줄, 기울어짐) + 물고기 (아이템 디스플레이)."""
    cmds = []
    for i in range(cars):
        x, y, z = rng.uniform(-200, 200), rng.uniform(Y0 + 10, Y0 + 90), rng.uniform(-160, -40)
        ax = rng.uniform(-0.6, 0.6)
        q = [round(math.sin(ax / 2), 3), 0.0, round(math.sin(ax / 3), 3), 0.0]
        q[3] = round(math.sqrt(max(0.0, 1 - q[0] ** 2 - q[2] ** 2)), 3)
        body = ["minecraft:blue_concrete", "minecraft:black_concrete", "minecraft:green_concrete", "minecraft:gray_concrete"][i % 4]
        for state, tr, sc in ((body, (-2.5, 0, -1), (5, 1.2, 2)), ("minecraft:tinted_glass", (-1.5, 1.2, -0.9), (3, 0.9, 1.8)),
                              ("minecraft:black_concrete", (-2.2, -0.4, -1.05), (4.4, 0.5, 2.1))):
            cmds.append(f"execute in {d.dim} run summon minecraft:block_display {x:.1f} {y:.1f} {z:.1f} "
                        f'{{block_state:"{state}",Tags:["ruina.car"],transformation:{{left_rotation:[{q[0]}f,{q[1]}f,{q[2]}f,{q[3]}f],'
                        f"right_rotation:[0f,0f,0f,1f],translation:[{tr[0]}f,{tr[1]}f,{tr[2]}f],scale:[{sc[0]}f,{sc[1]}f,{sc[2]}f]}}}}")
        b.forceload.append((d.dim, x, z))
    kinds = ["minecraft:tropical_fish", "minecraft:cod", "minecraft:salmon", "minecraft:pufferfish"]
    for i in range(fish):
        x, y, z = rng.uniform(-140, 140), rng.uniform(Y0 + 2, Y0 + 40), rng.uniform(-60, 30)
        if abs(z) < HW + 2:
            z -= 20
        cmds.append(f"execute in {d.dim} run summon minecraft:item_display {x:.1f} {y:.1f} {z:.1f} "
                    f'{{item:{{id:"{kinds[i % 4]}",count:1}},Tags:["ruina.fish"],item_display:"fixed",billboard:"vertical",'
                    "transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],"
                    "scale:[1.5f,1.5f,1.5f]}}")
        b.forceload.append((d.dim, x, z))
    b.links.entity_cmds += cmds


# ---------------------------------------------------------------- 헤세드 방
RW, RD, RH = 12, 10, 12


def chesed_room(d, ox=ROOM_X):
    y0, yt = RY, RY + RH
    xs, zs = np.arange(ox - RW, ox + RW + 1), np.arange(-RD, RD + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    fl = np.where(S.hash01((X + (Z % 4) * 2) // 6, Z, seed=1821) < 0.5, d.id("minecraft:dark_oak_planks"),
                  d.id("minecraft:spruce_planks"))
    # 바닥의 창살 그림자 빛 (원화): 창 쪽에서 비스듬히 들어온 푸른 빛 → 밝은 판자
    lit = ((X - ox - (Z + RD) * 0.6) % 6 > 1) & (np.abs(X - ox - 2 - (Z + RD) * 0.6) < 7) & (Z > -RD + 3) & (Z < 4)
    fl = np.where(lit, d.id("minecraft:warped_planks"), fl)
    d.place(ox - RW, y0 - 1, -RD, fl[:, None, :])
    x0, x1, z0, z1 = ox - RW - 1, ox + RW + 1, -RD - 1, RD + 1
    for (a0, b0, a1, b1) in ((x0, z1, x1, z1), (x0, z0, x0, z1), (x1, z0, x1, z1), (x0, z0, x1, z0)):
        d.fill(a0, y0, b0, a1, yt, b1, "minecraft:polished_deepslate")
    d.fill(x0, yt, z0, x1, yt, z1, "minecraft:polished_deepslate")
    # 격자 큰 창 (북쪽 왼쪽) + 너머 잠긴 도시·푸른 빛
    wx0, wx1 = ox - 10, ox + 1
    for x in range(wx0, wx1 + 1):
        for y in range(y0 + 3, yt - 1):
            frame = (x - wx0) % 4 == 0 or (y - y0 - 3) % 4 == 0
            d.set(x, y, z0, "minecraft:polished_blackstone" if frame else "minecraft:light_blue_stained_glass")
    zb = z0 - 8
    d.fill(wx0 - 3, y0 - 2, zb, wx1 + 3, yt + 4, zb, "minecraft:light_blue_stained_glass")
    d.fill(wx0 - 3, y0 - 2, zb - 1, wx1 + 3, yt + 4, zb - 1, "minecraft:sea_lantern")
    for k, (bx, bh) in enumerate(((wx0, 9), (wx0 + 4, 6), (wx0 + 7, 11), (wx1 - 1, 7))):
        d.fill(bx, y0 - 2, zb + 1 + k % 2, bx + 2, y0 + bh, zb + 1 + k % 2, "minecraft:dark_prismarine")
    for x in (wx0 - 3, wx1 + 3):
        d.fill(x, y0 - 2, zb, x, yt + 4, z0 - 1, "minecraft:polished_deepslate")
    d.fill(wx0 - 3, yt + 4, zb, wx1 + 3, yt + 4, z0 - 1, "minecraft:polished_deepslate")
    d.fill(wx0 - 3, y0 - 2, zb, wx1 + 3, y0 - 2, z0 - 1, "minecraft:polished_deepslate")
    d.fill(wx0 - 2, y0, z0 + 1, wx0 - 2, yt - 1, z0 + 1, "minecraft:sea_lantern")          # 창틀 옆 푸른 빛줄
    d.fill(wx0 - 1, y0 + 2, z0 + 1, wx1, y0 + 2, z0 + 1, "minecraft:polished_deepslate_slab[type=top]")   # 창턱
    # 뒤 선반 (병·상자) + 커피 드리퍼 긴 탁자
    for y in range(y0 + 3, yt - 1, 3):
        d.fill(ox + 3, y, z0 + 1, ox + RW, y, z0 + 1, "minecraft:dark_oak_slab[type=top]")
        for x in range(ox + 3, ox + RW + 1, 2):
            d.set(x, y + 1, z0 + 1, ["minecraft:flower_pot", "minecraft:decorated_pot", "minecraft:brown_candle[candles=2]"][x % 3])
    d.fill(ox + 2, y0, z0 + 4, ox + 9, y0, z0 + 5, "minecraft:dark_oak_slab[type=top]")
    d.set(ox + 5, y0 + 1, z0 + 4, "minecraft:brewing_stand")                               # 커피 드리퍼
    # 소파 + 쿠션 (왼쪽 앞), 낮은 탁자
    d.fill(x0 + 1, y0, 0, x0 + 2, y0, 8, "minecraft:gray_wool")
    d.fill(x0 + 1, y0 + 1, 0, x0 + 1, y0 + 1, 8, "minecraft:gray_wool")
    d.set(x0 + 2, y0 + 1, 2, "minecraft:purple_carpet")
    d.set(x0 + 2, y0 + 1, 5, "minecraft:purple_carpet")
    d.fill(ox - 7, y0, 3, ox - 4, y0, 6, "minecraft:dark_oak_slab[type=bottom]")
    # 오른쪽 책장
    d.fill(x1 - 1, y0, -RD + 4, x1 - 1, yt - 1, RD, "minecraft:bookshelf")
    for y in range(y0 + 3, yt, 3):
        d.fill(x1 - 1, y, -RD + 4, x1 - 1, y, RD, "minecraft:dark_oak_planks")
    for x in range(-RW + 3, RW, 7):
        d.set(ox + x, yt - 1, 2, "minecraft:light[level=8]")
    d.set_biome(ox - 40, -40, ox + 40, 40, "ruina:social_science_room")


def build(b):
    from . import fragment as F
    d = b.dim("social_science")
    rng = np.random.default_rng(1901)
    seafloor(d)
    deck(d, rng)
    skip = lambda x, z: abs(z) < HW + 40 and abs(x) <= BX + 30   # noqa: E731
    build_city(d, 60, 400, seed=1911, ground_y=FLOOR, h_min=60, h_max=170, skip=skip, spacing0=40, size=(14, 30),
               palette=SUNK_PAL)
    build_city(d, 440, 820, seed=1912, ground_y=FLOOR, h_min=90, h_max=220, spacing0=120, size=(18, 34), palette=SUNK_PAL)
    currents(d, rng)
    floating(b, d, rng)
    chesed_room(d)
    F.floor(b, d, "gblock", (F.GBLOCK_P, F.GBLOCK), "사회과학의 층", (ARRIVE_X + 0.5, Y0, 0.5, -90),
            (ROOM_X + 0.5, RY, RD - 2.5, 180), (-BX + 4, Y0, -HW + 1, -BX + 7, Y0 + 3, HW - 1), "language_door")
    # 헤세드 방 격자 큰 창 → 철학의 층. 돌아오면 창 앞에서 방 쪽(남쪽)을 봄
    F.door(b, d, "gblock", (ROOM_X - 9, RY, -RD, ROOM_X, RY + 3, -RD + 1), "philosophy_entrance",
           (ROOM_X - 4.5, RY, -RD + 6.5, 0), "사회과학의 층")
    b.extra_checks += [
        {"what": "헤세드 방 바이옴", "cmd": f"execute in {d.dim} if biome {ROOM_X} {RY} 0 ruina:social_science_room", "expect": True},
        {"what": "떠다니는 폐차·물고기 (디스플레이)", "cmd": f"execute in {d.dim} if entity @e[type=minecraft:item_display,tag=ruina.fish]",
         "expect": True, "after_entities": True},
    ]


_SEA = dict(sky=((10, 30, 70), (20, 70, 140)), fog=(18, 60, 120), stars=0, night=False)
PREVIEW = [
    {"file": "social_science_compare_stage.png", "ref": "사회과학의 층 전경.png", "cam": (0.5, Y0 + 3, 34),
     "look": (0.5, Y0 + 30, -120), "kw": dict(fov=80, max_dist=700, fog_dist=200, **_SEA),
     "title": "사회과학의 층 — 원화(위) / 맵(아래): 갑판 옆에서 북쪽",
     "notes": ["난파선 갑판(구멍)·선체·계류 기둥과 밧줄, 소용돌이 물결과 빛기둥, 푸른 안개 속 잠긴 도시",
               "떠다니는 폐차·물고기는 디스플레이 엔티티라 미리보기에 안 나옴"]},
    {"file": "social_science_compare_room.png", "ref": "사회과학의 층 지정사서 방.png", "cam": (ROOM_X + 4.5, RY + 2.2, RD - 1),
     "look": (ROOM_X - 4, RY + 4, -RD), "kw": dict(fov=80, max_dist=120, sky=((6, 16, 30), (12, 30, 50)), fog=(12, 30, 50),
                                                    fog_dist=60, stars=0),
     "title": "헤세드 방 — 원화(위) / 맵(아래)",
     "notes": ["격자 큰 창 너머 잠긴 도시, 바닥 창살 빛, 소파·탁자, 커피 드리퍼 탁자, 선반, 책장"]},
]
