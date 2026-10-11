"""Phase 0 스모크 테스트 월드 (임시).

- 외부(ruina:exterior): 보라 밤하늘 아래 작은 받침대 + 임시 정문. 정문을 클릭하면 로비로 TP
- 로비(ruina:lobby): 책장 벽의 작은 방. 남쪽 문을 클릭하면 외부 정문 앞으로 TP
- 확인용: 속성 있는 블록(계단·랜턴), 블록 엔티티(조각된 책장), 여러 광원
나중에 실제 외부·로비 빌더로 교체한다.
"""
from __future__ import annotations

import numpy as np

Y0 = 64  # 바닥 위 첫 칸


def build(b):
    exterior(b)
    engine_sample(b)
    lobby(b)


def engine_sample(b):
    """도형 엔진 견본 (받침대 동쪽): 말린 가지 2개 + 작은 판자 탑. 계단·반블록 곡면 다듬기 화면 확인용."""
    from tools import shapes as S
    d = b.dim("exterior")
    wood = ("minecraft:dark_oak_stairs", "minecraft:dark_oak_slab")
    log = S.log_along("minecraft:dark_oak_log[axis={a}]")
    cx, cz = 30, -6
    d.fill(cx - 8, Y0 - 1, cz - 8, cx + 8, Y0 - 1, cz + 8, "minecraft:polished_deepslate")

    def rad(y, th):
        return 5.5 + 0.8 * np.sin(np.pi * ((y - Y0) % 8) / 8)
    tower = S.Revolve(Y0, Y0 + 24, rad, rmax=7, cx=cx + 0.5, cz=cz + 0.5).with_(
        paint=S.mix(["minecraft:dark_oak_log[axis=y]", "minecraft:stripped_dark_oak_log[axis=y]"], seed=3))
    ledge = S.Revolve(Y0 + 11.5, Y0 + 13, lambda y, th: np.full_like(y, 7.5), rmax=8, cx=cx + 0.5,
                      cz=cz + 0.5).with_(paint="minecraft:dark_oak_planks", smooth=wood)
    parts = [tower, ledge]
    for dirv in (np.array([1.0, 0, 0.25]), np.array([0.2, 0, -1.0])):  # 동쪽, 북쪽 (정문 쪽은 피함)
        dirv = dirv / np.linalg.norm(dirv)
        p0 = np.array([cx + 0.5, Y0 + 16, cz + 0.5]) + dirv * 4
        p3 = p0 + dirv * 26 + np.array([0, 10, 0])
        main = S.resample(S.bezier(p0, p0 + dirv * 8 + [0, 9, 0], p3 - dirv * 9 + [0, 2, 0], p3, 60), 1.0)
        c = S.curl(main[-1], main[-1] - main[-2], [0, 1, 0], 6, turns=1.8, shrink=0.5, step=1.0)
        pts = S.join(main, c)
        radii = np.concatenate([np.linspace(3.2, 1.8, len(main)), np.linspace(1.8, 1.1, len(c) - 1)])
        parts.append(S.Tube(pts, radii).with_(paint=log, smooth=wood))
    S.carve(d, S.Union(*parts), shell=1, smooth=True)
    b.links.anchor("engine_sample", d.dim, cx + 0.5, Y0, cz + 14.5, yaw=180)


def exterior(b):
    d = b.dim("exterior")
    # 원형 받침대 (반지름 7, 두께 3)
    r = 7
    xs, zs = np.meshgrid(np.arange(-r, r + 1), np.arange(-r, r + 1), indexing="ij")
    disk = xs ** 2 + zs ** 2 <= r * r + r
    rim = disk & (xs ** 2 + zs ** 2 >= (r - 1) ** 2)
    for dy, state in ((-3, "minecraft:deepslate_tiles"), (-2, "minecraft:deepslate_tiles"),
                      (-1, "minecraft:polished_deepslate")):
        d.place_mask(-r, Y0 + dy, -r, disk[:, None, :], state)
    d.place_mask(-r, Y0 - 1, -r, rim[:, None, :], "minecraft:polished_blackstone_bricks")
    d.set(0, Y0 - 1, 0, "minecraft:glowstone")

    # 정문까지 길 (z = -8 .. -18)
    d.fill(-2, Y0 - 2, -18, 2, Y0 - 1, -8, "minecraft:polished_deepslate")
    for z in range(-18, -7, 4):
        d.set(-3, Y0, z, "minecraft:lantern[hanging=false]")
        d.set(3, Y0, z, "minecraft:copper_lantern[hanging=false]")
        d.set(-3, Y0 - 1, z, "minecraft:polished_deepslate")
        d.set(3, Y0 - 1, z, "minecraft:polished_deepslate")

    # 임시 정문: 기둥 2개 + 상인방, 안쪽은 비워 둠 (클릭 영역)
    gz = -20
    d.fill(-6, Y0 - 2, gz - 2, 6, Y0 - 1, gz + 1, "minecraft:polished_deepslate")
    d.fill(-6, Y0, gz - 1, -4, Y0 + 12, gz, "minecraft:dark_oak_log[axis=y]")
    d.fill(4, Y0, gz - 1, 6, Y0 + 12, gz, "minecraft:dark_oak_log[axis=y]")
    d.fill(-7, Y0 + 13, gz - 1, 7, Y0 + 14, gz, "minecraft:stripped_dark_oak_log[axis=x]")
    for x in range(-3, 4):
        d.set(x, Y0 - 1, gz + 1, "minecraft:polished_deepslate_stairs[facing=north,half=bottom]")
    d.fill(-3, Y0, gz - 1, 3, Y0 + 12, gz - 1, "minecraft:black_concrete")  # 문 안쪽 어둠
    d.set(-5, Y0 + 12, gz + 1, "minecraft:lantern[hanging=true]")
    d.set(5, Y0 + 12, gz + 1, "minecraft:lantern[hanging=true]")

    # 조각된 책장 (블록 엔티티 확인용)
    shelf = ("minecraft:chiseled_bookshelf[facing=south,slot_0_occupied=true,slot_1_occupied=true,"
             "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=false]")
    d.set(-6, Y0, 4, shelf)
    d.block_entity(-6, Y0, 4, {
        "id": "minecraft:chiseled_bookshelf",
        "Items": [{"Slot": _b(0), "id": "minecraft:book", "count": 1},
                  {"Slot": _b(1), "id": "minecraft:enchanted_book", "count": 1},
                  {"Slot": _b(3), "id": "minecraft:written_book", "count": 1}],
        "last_interacted_slot": -1,
    })
    b.extra_checks.append({"cmd": "execute in ruina:exterior if data block -6 64 4 Items[2]", "expect": True,
                           "what": "조각된 책장 블록 엔티티의 책 3권"})

    L = b.links
    L.anchor("exterior_spawn", d.dim, 0.5, Y0, 0.5, yaw=180)
    L.anchor("exterior_gate", d.dim, 0.5, Y0, gz + 6.5, yaw=0)
    L.spawn = "exterior_spawn"
    L.portal(d.dim, 0.5, Y0, gz + 0.5, "lobby_entrance", width=7, height=12)
    L.walk(d.dim, (-3, Y0, gz, 3, Y0 + 3, gz), "lobby_entrance")  # 문 안쪽 한 칸에 걸어 들어가면 TP


def lobby(b):
    d = b.dim("lobby")
    h = 10  # 방 높이
    n = 11  # 반폭
    d.fill(-n, Y0 - 1, -n, n, Y0 - 1, n, "minecraft:dark_oak_planks")
    d.fill(-n + 2, Y0 - 1, -n + 2, n - 2, Y0 - 1, n - 2, "minecraft:spruce_planks")
    d.fill(-3, Y0, -3, 3, Y0, 3, "minecraft:red_carpet")
    # 벽: 책장, 모서리 기둥
    for x0, z0, x1, z1 in ((-n, -n, n, -n), (-n, n, n, n), (-n, -n, -n, n), (n, -n, n, n)):
        d.fill(x0, Y0, z0, x1, Y0 + h - 1, z1, "minecraft:bookshelf")
    for x in (-n, n):
        for z in (-n, n):
            d.fill(x, Y0, z, x, Y0 + h - 1, z, "minecraft:stripped_dark_oak_log[axis=y]")
    d.fill(-n, Y0 + h, -n, n, Y0 + h, n, "minecraft:dark_oak_planks")
    # 천장 조명
    for x in (-6, 0, 6):
        for z in (-6, 0, 6):
            d.set(x, Y0 + h - 1, z, "minecraft:lantern[hanging=true]")
    d.set(0, Y0 - 1, 0, "minecraft:sea_lantern")
    # 남쪽 문 (클릭하면 밖으로)
    d.fill(-1, Y0, n, 1, Y0 + 3, n, "minecraft:air")
    d.fill(-1, Y0, n + 1, 1, Y0 + 3, n + 1, "minecraft:black_concrete")
    # 책상
    d.set(0, Y0, -6, "minecraft:lectern[facing=south]")

    L = b.links
    L.anchor("lobby_entrance", d.dim, 0.5, Y0, n - 2.5, yaw=180)
    L.portal(d.dim, 0.5, Y0, n + 0.5, "exterior_gate", width=3, height=4)
    L.walk(d.dim, (-1, Y0, n, 1, Y0 + 2, n), "exterior_gate")


def _b(v):
    from tools.nbt import Byte
    return Byte(v)
