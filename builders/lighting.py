"""보이지 않는 빛 블록(minecraft:light)으로 걸어 다니는 곳을 밝힘 (테스트 3차: "광원 빼고 안 보임").

도착 자리마다 둘레(반지름 R)를 격자(간격 STEP)로 훑어, 자리 높이 근처의 바닥(밟을 수 있는 블록 위 빈칸 3칸)을 찾고
바닥 + 3 칸(머리 위)에 빛 블록을 둔다. 발·머리 칸은 비워 둠 (조각 전환의 '빈칸 확인'·도착 자리 검사와 안 겹치게).
빛 블록은 보이지 않고 부딪히지도 않음. 쉐이더(BSL)는 블록 빛으로 그림.
"""
from __future__ import annotations

import numpy as np

AIR = "minecraft:air"
LEVEL = 14
STEP = 7            # 빛 14 → 격자 칸 사이 가장 어두운 곳도 약 8
R_SCENE = 160       # 전경 도착 자리 둘레
R_ROOM = 40         # 방 (방 크기보다 넉넉히)
DY_UP, DY_DOWN = 6, 12

# 바닥으로 치지 않을 블록 (빛 블록·물·용암·잎 따위)
NOT_FLOOR = ("minecraft:light", "minecraft:water", "minecraft:lava", "leaves", "glass_pane", "minecraft:barrier",
             "_carpet", "minecraft:chain", "lantern", "minecraft:end_rod", "_bars", "fence", "wall")


def _floor_y(d, x, z, y_hi, y_lo):
    """y_hi 부터 내려가며 첫 바닥(위로 빈칸 3칸) 높이. 없으면 None."""
    air_run = 0
    for y in range(y_hi, y_lo - 1, -1):
        st = d.get(x, y, z)
        if st == AIR:
            air_run += 1
            continue
        if air_run >= 3 and not any(k in st for k in NOT_FLOOR):
            return y
        air_run = 0
    return None


def light_area(d, cx, cy, cz, r, step=STEP, level=LEVEL):
    n = 0
    state = f"minecraft:light[level={level}]"
    for x in range(int(cx) - r, int(cx) + r + 1, step):
        for z in range(int(cz) - r, int(cz) + r + 1, step):
            if (x - cx) ** 2 + (z - cz) ** 2 > r * r:
                continue
            fy = _floor_y(d, x, z, int(cy) + DY_UP, int(cy) - DY_DOWN)
            if fy is None:
                continue
            if d.get(x, fy + 3, z) == AIR:
                d.set(x, fy + 3, z, state)
                n += 1
    return n


def light_all(b) -> dict:
    """모든 도착 자리 둘레. 방 자리(이름 *_room, lobby_hall)는 좁게."""
    dims = {d.dim: d for d in b.dims.values()}
    stats = {}
    for name, a in b.links.anchors.items():
        d = dims[a.dim]
        r = R_ROOM if name.endswith("_room") else R_SCENE
        stats[name] = light_area(d, a.x, a.y, a.z, r)
    return stats
