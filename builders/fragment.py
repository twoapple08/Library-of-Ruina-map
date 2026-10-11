"""조각(은조각·금조각): 손에 든 조각을 왼손으로 들면(F) 번쩍이며 두 장소를 오간다.

- 조각은 철/금 조각 + custom_data {ruina:{<key>:1b}} (이름·모양·소리는 나중에 텍스처팩으로)
- 잠깐 왼손에 들렸다가 몇 틱 뒤 오른손으로 돌아옴 (오른손이 비어 있을 때)
- 이동: `relative`(같은 상대 위치, 막혔으면 기본 자리) 또는 고정 자리(anchor)
"""
from __future__ import annotations

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


def setup(L, key: str, dim: str, pred: str, b_box: str, to_a: list, to_b: list, area: str = ""):
    """L: datapack.Links. b_box: 'B 쪽에 있음'을 가리는 선택자 범위 (x=..,dx=..). to_a/to_b: 이동 명령 목록 (@s, at @s).
    area: 이 범위 안에서만 작동 (선택자 인자, 예: 지정사서 방 밖에서만)."""
    up = f"{NS}.{key}_up"
    for sc in (f"{NS}.{key}", f"{NS}.ok"):
        if sc not in L.scores:
            L.scores.append(sc)
    L.tick += [
        f"execute as @a[tag=!{NS}.fading,tag=!{up}{',' + area if area else ''}] at @s if dimension {dim} "
        f"if items entity @s weapon.offhand {pred} run function {NS}:{key}/switch",
        f"execute as @a[tag={up}] run function {NS}:{key}/tick",
    ]
    L.functions[f"{key}/switch"] = [
        f"tag @s add {up}",
        f"scoreboard players set @s {NS}.{key} 0",
        f"execute if entity @s[{b_box}] run tag @s add {NS}.was_b",   # 한 번만 판단 (이동 뒤 다시 판단하면 되돌아감)
        f"execute if entity @s[tag={NS}.was_b] run function {NS}:{key}/go_a",
        f"execute unless entity @s[tag={NS}.was_b] run function {NS}:{key}/go_b",
        f"tag @s remove {NS}.was_b",
        f"execute at @s run function {NS}:fx/switch",
        f"execute at @s run function {NS}:fx/flash",
    ]
    L.functions[f"{key}/go_a"] = list(to_a)
    L.functions[f"{key}/go_b"] = list(to_b)
    L.functions[f"{key}/tick"] = [
        f"scoreboard players add @s {NS}.{key} 1",
        f"execute if score @s {NS}.{key} matches 6.. unless items entity @s weapon.mainhand * "
        f"if items entity @s weapon.offhand {pred} run function {NS}:fx/hand_back",
        f"execute unless items entity @s weapon.offhand {pred} run tag @s remove {up}",
    ]
    L.functions.setdefault("fx/hand_back", [
        "item replace entity @s weapon.mainhand from entity @s weapon.offhand",
        "item replace entity @s weapon.offhand with minecraft:air",
    ])
    L.functions.setdefault("fx/switch", [
        "particle minecraft:end_rod ~ ~1 ~ 1.5 1.2 1.5 0.12 160 force @s",
        "particle minecraft:firefly ~ ~1 ~ 4 2 4 0 120 force @s",
        "effect give @s minecraft:night_vision 1 0 true",
    ])
    # 플래시 입자는 버전마다 옵션이 달라 따로 (문법 오류면 이 함수만 실패)
    L.functions.setdefault("fx/flash", ["particle minecraft:flash{color:[1.0,0.96,0.85,1.0]} ^ ^1.6 ^1 0 0 0 0 1 force @s"])


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


def floor(b, d, key, item_pg, title, entrance, room, ret_zone, ret_dest, room_y=None, extra_keep=()):
    """층 공통 연결: 도착 자리(제목), 지정사서 방 자리, 돌아가는 구역 → 이전 층 문, 조각 F 전환 + 서버 검사.
    entrance/room = (x, y, z, yaw). 반환: 도착 시 명령(arrive)."""
    L = b.links
    name = d.dim.split(":")[1]            # 자리 이름은 층 이름 (예: art_entrance, art_room, art_door)
    arrive = exchange(item_pg, *extra_keep)
    ex, ey, ez, eyaw = entrance
    rx, ry, rz, ryaw = room
    L.anchor(f"{name}_entrance", d.dim, ex, ey, ez, yaw=eyaw, title=title, on_arrive=arrive)
    L.anchor(f"{name}_room", d.dim, rx, ry, rz, yaw=ryaw, on_arrive=arrive)
    L.walk(d.dim, ret_zone, ret_dest, fade=True)
    setup(L, key, d.dim, item_pg[0], ROOM_BOX, to_a=fixed(f"{name}_entrance"), to_b=fixed(f"{name}_room"))
    tag = f"ruina.t{key}"
    b.extra_checks += [
        {"what": f"{title} 조각 전환 접대→방",
         "setup": [f"execute in {d.dim} run summon minecraft:marker {ex} {ey} {ez} {{Tags:[\"{tag}\"]}}",
                   f"execute in {d.dim} as @e[type=minecraft:marker,tag={tag}] at @s run function ruina:{key}/switch"],
         "cmd": f"execute in {d.dim} positioned {rx} {ry} {rz} if entity @e[type=minecraft:marker,tag={tag},distance=..0.5]",
         "expect": True},
        {"what": f"{title} 조각 전환 방→접대",
         "setup": [f"execute in {d.dim} as @e[type=minecraft:marker,tag={tag}] at @s run function ruina:{key}/switch"],
         "cmd": f"execute in {d.dim} positioned {ex} {ey} {ez} if entity @e[type=minecraft:marker,tag={tag},distance=..0.5]",
         "expect": True},
    ]
    return arrive


def door(b, d, key, zone, next_entrance, anchor, title):
    """지정사서 방의 출구(원화 속 빛나는 문) → 다음 층. anchor = 다음 층에서 돌아올 때 설 자리 (x, y, z, yaw)."""
    L = b.links
    name = d.dim.split(":")[1]
    L.walk(d.dim, zone, next_entrance, fade=True)
    x, y, z, yaw = anchor
    arrive = L.anchors[f"{name}_room"].on_arrive
    L.anchor(f"{name}_door", d.dim, x, y, z, yaw=yaw, title=title, on_arrive=arrive)
