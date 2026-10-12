"""조각(은조각·금조각): 손에 든 조각을 왼손으로 들면(F) 번쩍이며 두 장소를 오간다.

- 조각은 철/금 조각 + custom_data {ruina:{<key>:1b}} (이름·모양·소리는 나중에 텍스처팩으로)
- 잠깐 왼손에 들렸다가 몇 틱 뒤 오른손으로 돌아옴 (오른손이 비어 있을 때)
- 이동: `relative`(같은 상대 위치, 막혔으면 기본 자리) 또는 고정 자리(anchor)
"""
from __future__ import annotations

from dataclasses import dataclass

NS = "ruina"


def item(key: str, base: str, name: str) -> tuple[str, str]:
    """(검사용 predicate, give 용 아이템)."""
    pred = f"{base}[minecraft:custom_data={{{NS}:{{{key}:1b}}}}]"
    give = (f'{base}[minecraft:custom_data={{{NS}:{{{key}:1b}}}},minecraft:item_name="{name}",'
            "minecraft:enchantment_glint_override=true]")
    return pred, give


def give_if_missing(pred: str, give: str) -> str:
    return (f"execute unless items entity @s container.* {pred} unless items entity @s weapon.offhand {pred} "
            f"run give @s {give}")


def take(pred: str) -> str:
    return f"clear @s {pred}"


UP = f"{NS}.f_up"        # 조각을 왼손으로 든 직후 (다시 발동 막기, 몇 틱 뒤 오른손으로 돌려줌)


def _common(L):
    """모든 조각 공용: 왼손 → 오른손 되돌리기, 효과 함수."""
    for sc in (f"{NS}.f_t", f"{NS}.held", f"{NS}.ok"):
        if sc not in L.scores:
            L.scores.append(sc)
    if "frag/tick" in L.functions:
        return
    L.tick.append(f"execute as @a[tag={UP}] run function {NS}:frag/tick")
    L.functions["frag/up"] = [f"tag @s add {UP}", f"scoreboard players set @s {NS}.f_t 0"]
    L.functions["frag/tick"] = (
        [f"scoreboard players add @s {NS}.f_t 1", f"scoreboard players set @s {NS}.held 0"]
        + [f"execute if items entity @s weapon.offhand {p} run scoreboard players set @s {NS}.held 1" for p, _ in ALL]
        + [f"execute if score @s {NS}.f_t matches 6.. if score @s {NS}.held matches 1 "
           f"unless items entity @s weapon.mainhand * run function {NS}:fx/hand_back",
           f"execute if score @s {NS}.held matches 0 run tag @s remove {UP}"])
    L.functions["fx/hand_back"] = [
        "item replace entity @s weapon.mainhand from entity @s weapon.offhand",
        "item replace entity @s weapon.offhand with minecraft:air",
    ]
    L.functions["fx/switch"] = [
        "particle minecraft:end_rod ~ ~1 ~ 1.5 1.2 1.5 0.12 160 force @s",
        "particle minecraft:firefly ~ ~1 ~ 4 2 4 0 120 force @s",
        "effect give @s minecraft:night_vision 1 0 true",
        f"playsound {NS}:fragment.switch master @s ~ ~ ~ 1 1",
    ]
    # 플래시 입자는 버전마다 옵션이 달라 따로 (문법 오류면 이 함수만 실패)
    L.functions["fx/flash"] = ["particle minecraft:flash{color:[1.0,0.96,0.85,1.0]} ^ ^1.6 ^1 0 0 0 0 1 force @s"]


def trigger(L, dim: str, pred: str, func: str, area: str = ""):
    """dim 차원에서 pred 조각을 왼손으로 들면(F) func 실행. area: 이 범위 안에서만 (선택자 인자).
    위치 인자가 있는 선택자는 실행 차원 안에서만 찾으므로 'execute in dim' 으로 차원을 맞춘다."""
    _common(L)
    L.tick.append(f"execute in {dim} as @a[tag=!{NS}.fading,tag=!{UP}{',' + area if area else ''}] at @s "
                  f"if dimension {dim} if items entity @s weapon.offhand {pred} run function {NS}:{func}")


def setup(L, key: str, dim: str, pred: str, b_box: str, to_a: list, to_b: list, area: str = ""):
    """같은 층 안 두 장소 전환 (A ↔ B). b_box: 'B 쪽에 있음'을 가리는 선택자 범위 (x=..,dx=..).
    to_a/to_b: 이동 명령 목록 (@s, at @s). area: 이 범위 안에서만 작동."""
    trigger(L, dim, pred, f"{key}/switch", area)
    L.functions[f"{key}/switch"] = [
        f"function {NS}:frag/up",
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
    """같은 상대 위치(x + dx)로, 발밑·머리 칸이 막혔으면 기본 자리로."""
    return [
        f"scoreboard players set @s {NS}.ok 0",
        f"execute positioned ~{dx} ~ ~ if block ~ ~ ~ minecraft:air if block ~ ~1 ~ minecraft:air "
        f"run scoreboard players set @s {NS}.ok 1",
        f"execute if score @s {NS}.ok matches 1 positioned ~{dx} ~ ~ run tp @s ~ ~ ~",
        f"execute if score @s {NS}.ok matches 0 run function {NS}:tp/to/{fallback}",
    ]


def fixed(anchor: str) -> list:
    return [f"function {NS}:tp/to/{anchor}"]


# 층 순서대로 (사용자 지정, 2026-10-12): 철조각, 금조각, 철괴, 금괴, 철발판, 금발판, 철블럭, 금블럭, 모루, 황금사과.
# 로비부터 하나씩, 총류는 마법이 부여된 황금사과 (사용자 확정)
SILVER_P, SILVER = item("silver", "minecraft:iron_nugget", "철조각")                 # 로비 (예전 이름 '은조각')
GOLD_P, GOLD = item("gold", "minecraft:gold_nugget", "금조각")                       # 역사
IRON_P, IRON = item("iron", "minecraft:iron_ingot", "철괴")                          # 기술과학
GOLDBAR_P, GOLDBAR = item("goldbar", "minecraft:gold_ingot", "금괴")                 # 문학
IPLATE_P, IPLATE = item("iplate", "minecraft:heavy_weighted_pressure_plate", "철발판")  # 예술
GPLATE_P, GPLATE = item("gplate", "minecraft:light_weighted_pressure_plate", "금발판")  # 자연과학
IBLOCK_P, IBLOCK = item("iblock", "minecraft:iron_block", "철블럭")                  # 언어
GBLOCK_P, GBLOCK = item("gblock", "minecraft:gold_block", "금블럭")                  # 사회과학
ANVIL_P, ANVIL = item("anvil", "minecraft:anvil", "모루")                            # 철학
APPLE_P, APPLE = item("apple", "minecraft:golden_apple", "황금사과")                  # 종교
EAPPLE_P, EAPPLE = item("eapple", "minecraft:enchanted_golden_apple", "마법이 부여된 황금사과")  # 총류
MAGMA_P, MAGMA = item("magma", "minecraft:magma_cream", "마그마크림")                 # 자연과학 색감 전환
ALL = [(SILVER_P, SILVER), (GOLD_P, GOLD), (IRON_P, IRON), (GOLDBAR_P, GOLDBAR), (IPLATE_P, IPLATE),
       (GPLATE_P, GPLATE), (IBLOCK_P, IBLOCK), (GBLOCK_P, GBLOCK), (ANVIL_P, ANVIL), (APPLE_P, APPLE),
       (EAPPLE_P, EAPPLE), (MAGMA_P, MAGMA)]


def exchange(*keeps) -> list:
    """그 층에 도착하면: 다른 조각은 회수, 그 층 조각(들)은 없으면 1개. keeps = (pred, give), ..."""
    if len(keeps) == 2 and isinstance(keeps[0], str):
        keeps = (keeps,)
    keep_p = {p for p, _ in keeps}
    return [take(p) for p, _ in ALL if p not in keep_p] + [give_if_missing(p, g) for p, g in keeps]


ROOM_BOX = "x=3800,y=-64,z=-1024,dx=400,dy=1024,dz=2048"   # 지정사서 방은 x 4000 둘레


# ---------------------------------------------------------------- 층 사슬 (사용자 결정 2026-10-12)
# 층 N 의 두 장소: 전경(scene, 도착 자리) ↔ 지정사서 방(room). 로비는 전환 전 방 = 전경, 넓은 홀 = 지정사서 방.
# 가진 조각: 전경 = 이전 층 조각 + N 조각 (+ 그 층 전용, 예: 마그마크림) / 방 = 거기에 다음 층 조각.
# F (조각을 왼손으로): N 조각 → 전경 ↔ 방, 다음 층 조각(방에서만) → 다음 층 전경, 이전 층 조각 → 이전 층 지정사서 방.
# 걸어 들어가는 층 사이 이동은 없음 (원화 속 빛나는 문·창 같은 조형물은 그대로 둠).

@dataclass
class Stage:
    key: str            # 조각 키 (함수 이름 <key>/switch)
    dim: str
    item: tuple         # (pred, give)
    title: str
    scene: str          # 전경 도착 자리 이름
    room: str           # 지정사서 방 자리 이름
    room_box: str       # 방 쪽 범위 (선택자 인자)
    extra: tuple = ()   # 그 층에서만 쓰는 조각 (pred, give)


CHAIN: list = []


def stage(b, d, key, item_pg, title, scene, room, room_box=ROOM_BOX, to_a=None, to_b=None, extra_keep=(),
          scene_name=None, room_name=None):
    """층 등록: 전경·방 자리 + 조각 F 전환. scene/room = (x, y, z, yaw). 다른 층과의 연결은 finish() 에서.
    to_a/to_b 를 주면 그 이동(예: 같은 상대 위치)을 쓰고, 없으면 고정 자리로."""
    L = b.links
    name = d.dim.split(":")[1]
    sn, rn = scene_name or f"{name}_entrance", room_name or f"{name}_room"
    ex, ey, ez, eyaw = scene
    rx, ry, rz, ryaw = room
    L.anchor(sn, d.dim, ex, ey, ez, yaw=eyaw, title=title)
    L.anchor(rn, d.dim, rx, ry, rz, yaw=ryaw, title=title)   # 제목은 암전으로 올 때만 (다른 층에서 돌아올 때)
    st = Stage(key, d.dim, item_pg, title, sn, rn, room_box, tuple(extra_keep))
    CHAIN.append(st)
    setup(L, key, d.dim, item_pg[0], room_box, to_a=list(to_a or fixed(sn)), to_b=list(to_b or fixed(rn)))
    tag = f"ruina.t{key}"
    b.extra_checks += [
        {"what": f"{title} 조각 전환 전경→방",
         "setup": [f"execute in {d.dim} run summon minecraft:marker {ex} {ey} {ez} {{Tags:[\"{tag}\"]}}",
                   f"execute in {d.dim} as @e[type=minecraft:marker,tag={tag}] at @s run function ruina:{key}/switch"],
         "cmd": f"execute in {d.dim} positioned {rx} {ry} {rz} if entity @e[type=minecraft:marker,tag={tag},distance=..0.5]",
         "expect": True},
        {"what": f"{title} 조각 전환 방→전경",
         "setup": [f"execute in {d.dim} as @e[type=minecraft:marker,tag={tag}] at @s run function ruina:{key}/switch"],
         "cmd": f"execute in {d.dim} positioned {ex} {ey} {ez} if entity @e[type=minecraft:marker,tag={tag},distance=..0.5]",
         "expect": True},
    ]
    return st


def finish(b):
    """층 사슬 연결: 도착할 때 조각 교환, 이전/다음 층 조각 F. build_all 끝에서 한 번."""
    L = b.links
    for i, s in enumerate(CHAIN):
        prev = CHAIN[i - 1] if i > 0 else None
        nxt = CHAIN[i + 1] if i + 1 < len(CHAIN) else None
        keep_scene = ([prev.item] if prev else []) + [s.item] + list(s.extra)
        keep_room = keep_scene + ([nxt.item] if nxt else [])
        scene_cmds, room_cmds = exchange(*keep_scene), exchange(*keep_room)
        L.anchors[s.scene].on_arrive = scene_cmds + L.anchors[s.scene].on_arrive
        L.anchors[s.room].on_arrive = room_cmds + L.anchors[s.room].on_arrive
        # 같은 층 전환 뒤에도 교환 (같은 상대 위치 이동은 도착 자리 함수를 안 거치므로)
        L.functions[f"{s.key}/go_a"] += scene_cmds
        L.functions[f"{s.key}/go_b"] += room_cmds
        if prev:
            trigger(L, s.dim, prev.item[0], f"frag/{s.key}/back")
            L.functions[f"frag/{s.key}/back"] = [f"function {NS}:frag/up", f"function {NS}:tp/fade/{prev.room}",
                                                 f"execute at @s run function {NS}:fx/switch"]
            L.jumps.append((s.dim, L.anchors[s.scene], prev.room))
        if nxt:
            trigger(L, s.dim, nxt.item[0], f"frag/{s.key}/next", area=s.room_box)
            L.functions[f"frag/{s.key}/next"] = [f"function {NS}:frag/up", f"function {NS}:tp/fade/{nxt.scene}",
                                                 f"execute at @s run function {NS}:fx/switch"]
            L.jumps.append((s.dim, L.anchors[s.room], nxt.scene))
    CHAIN.clear()
