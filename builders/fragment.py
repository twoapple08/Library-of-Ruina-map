"""층 등록과 같은 층 안 전환 (모드화 ① 기본 틀, 2026-10-12).

- 층마다 두 장소: 전경(scene, 도착 자리) ↔ 지정사서 방(room). 로비는 전환 전 방 = 전경, 넓은 홀 = 방.
- 아이템은 모드가 가짐 (config.MOD_ITEMS): 방전환 우클릭 → `ruina:mod/room` (차원별로 그 층 `<key>/switch`),
  세피라 우클릭 → 모드가 `ruina:tp/fade/<층>_entrance` 실행. 조각 F·층 사슬·조각 교환·자동 지급은 없앰.
- 티페리트 F(자연과학 돔 색 전환)는 지금 만들지 않음 (사용자 2026-10-12). 나중에 만들 때: 데이터팩 tick 감지는
  CI 게임 테스트에서 손만 돌아오고 전환이 안 됐음 → 모드 Java 에서 왼손을 감지해 전환 함수를 직접 실행할 것.
"""
from __future__ import annotations

from dataclasses import dataclass

NS = "ruina"


def effects(L):
    """번쩍임 (바로 전환). 야간투시 없음 (4차 뒤 결정)."""
    if "fx/switch" in L.functions:
        return
    L.functions["fx/hand_back"] = [
        "item replace entity @s weapon.mainhand from entity @s weapon.offhand",
        "item replace entity @s weapon.offhand with minecraft:air",
    ]
    L.functions["fx/switch"] = [
        "particle minecraft:end_rod ~ ~1 ~ 1.5 1.2 1.5 0.12 160 force @s",
        "particle minecraft:firefly ~ ~1 ~ 4 2 4 0 120 force @s",
        f"playsound {NS}:fragment.switch master @s ~ ~ ~ 1 1",
    ]
    # 플래시 입자는 버전마다 옵션이 달라 따로 (문법 오류면 이 함수만 실패)
    L.functions["fx/flash"] = ["particle minecraft:flash{color:[1.0,0.96,0.85,1.0]} ^ ^1.6 ^1 0 0 0 0 1 force @s"]


def setup(L, key: str, dim: str, b_box: str, to_a: list, to_b: list):
    if f"{NS}.ok" not in L.scores:
        L.scores.append(f"{NS}.ok")
    """같은 층 안 두 장소 전환 함수 `<key>/switch` (A ↔ B, 번쩍임, 바로). b_box: 'B 쪽에 있음' 선택자 범위."""
    effects(L)
    L.functions[f"{key}/switch"] = [
        # 한 번만 판단 (이동 뒤 다시 판단하면 되돌아감). 위치 인자 선택자라 차원을 맞춰서
        f"execute in {dim} if entity @s[{b_box}] run tag @s add {NS}.was_b",
        f"execute if entity @s[tag={NS}.was_b] run function {NS}:{key}/go_a",
        f"execute unless entity @s[tag={NS}.was_b] run function {NS}:{key}/go_b",
        f"tag @s remove {NS}.was_b",
        f"execute at @s run function {NS}:fx/switch",
        f"execute at @s run function {NS}:fx/flash",
    ]
    L.functions[f"{key}/go_a"] = list(to_a)
    L.functions[f"{key}/go_b"] = list(to_b)


def relative(dx: int, fallback: str) -> list:
    """같은 상대 위치(x + dx)로. 머리 칸이 막혔거나 발밑이 비었으면 기본 자리로.
    (발 칸 대신 머리 칸·발밑을 봄: 반블록 위에 서면 발 칸이 반블록이라 늘 '막힘'이 됨 — CI 게임 테스트 티페리트 F)"""
    return [
        f"scoreboard players set @s {NS}.ok 0",
        f"execute positioned ~{dx} ~ ~ if block ~ ~1 ~ minecraft:air unless block ~ ~-0.5 ~ minecraft:air "
        f"run scoreboard players set @s {NS}.ok 1",
        f"execute if score @s {NS}.ok matches 1 positioned ~{dx} ~ ~ run tp @s ~ ~ ~",
        f"execute if score @s {NS}.ok matches 0 run function {NS}:tp/to/{fallback}",
    ]


def fixed(anchor: str) -> list:
    return [f"function {NS}:tp/to/{anchor}"]


ROOM_BOX = "x=3800,y=-64,z=-1024,dx=400,dy=1024,dz=2048"   # 지정사서 방은 x 4000 둘레


@dataclass
class Stage:
    key: str            # 전환 함수 이름 <key>/switch
    dim: str
    title: str
    scene: str          # 전경 도착 자리 이름
    room: str           # 지정사서 방 자리 이름
    room_box: str       # 방 쪽 범위 (선택자 인자)


CHAIN: list = []


def stage(b, d, key, title, scene, room, room_box=ROOM_BOX, to_a=None, to_b=None, scene_name=None, room_name=None):
    """층 등록: 전경·방 자리 + 방전환. scene/room = (x, y, z, yaw[, pitch]).
    to_a/to_b 를 주면 그 이동(예: 같은 상대 위치)을 쓰고, 없으면 고정 자리로."""
    L = b.links
    name = d.dim.split(":")[1]
    sn, rn = scene_name or f"{name}_entrance", room_name or f"{name}_room"
    ex, ey, ez, eyaw, *ep = scene
    rx, ry, rz, ryaw, *rp = room
    L.anchor(sn, d.dim, ex, ey, ez, yaw=eyaw, pitch=(ep or [0.0])[0], title=title)   # 제목은 암전으로 올 때만
    L.anchor(rn, d.dim, rx, ry, rz, yaw=ryaw, pitch=(rp or [0.0])[0], title=title)
    st = Stage(key, d.dim, title, sn, rn, room_box)
    CHAIN.append(st)
    setup(L, key, d.dim, room_box, to_a=list(to_a or fixed(sn)), to_b=list(to_b or fixed(rn)))
    tag = f"ruina.t{key}"
    b.extra_checks += [
        {"what": f"{title} 방전환 전경→방",
         "setup": [f"execute in {d.dim} run summon minecraft:marker {ex} {ey} {ez} {{Tags:[\"{tag}\"]}}",
                   f"execute in {d.dim} as @e[type=minecraft:marker,tag={tag}] at @s run function ruina:{key}/switch"],
         "cmd": f"execute in {d.dim} positioned {rx} {ry} {rz} if entity @e[type=minecraft:marker,tag={tag},distance=..0.5]",
         "expect": True},
        {"what": f"{title} 방전환 방→전경",
         "setup": [f"execute in {d.dim} as @e[type=minecraft:marker,tag={tag}] at @s run function ruina:{key}/switch"],
         "cmd": f"execute in {d.dim} positioned {ex} {ey} {ez} if entity @e[type=minecraft:marker,tag={tag},distance=..0.5]",
         "expect": True},
    ]
    return st


def finish(b):
    """방전환 디스패처(`mod/room`, 모드 전용)와 세피라 층 이동 검사 목록. build_all 끝에서 한 번."""
    L = b.links
    room = [f"execute if dimension {s.dim} run function {NS}:{s.key}/switch" for s in CHAIN]
    room.append(f"execute if dimension {NS}:exterior run title @s actionbar "
                '{"text":"여기에는 지정사서 방이 없어요","color":"#ecd6a6"}')
    L.mod_functions["mod/room"] = room
    # 세피라는 어디서든 그 층 전경으로 (CI: 로비 홀에서 출발하는 암전 TP 검사)
    hall = next((s for s in CHAIN if s.room == "lobby_hall"), None)
    for s in CHAIN:
        if hall and s is not hall:
            L.jumps.append((hall.dim, L.anchors[hall.room], s.scene))
    CHAIN.clear()
