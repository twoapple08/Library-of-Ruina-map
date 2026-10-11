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


def setup(L, key: str, dim: str, pred: str, b_box: str, to_a: list, to_b: list):
    """L: datapack.Links. b_box: 'B 쪽에 있음'을 가리는 선택자 범위 (x=..,dx=..). to_a/to_b: 이동 명령 목록 (@s, at @s)."""
    up = f"{NS}.{key}_up"
    for sc in (f"{NS}.{key}", f"{NS}.ok"):
        if sc not in L.scores:
            L.scores.append(sc)
    L.tick += [
        f"execute as @a[tag=!{NS}.fading,tag=!{up}] at @s if dimension {dim} "
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


SILVER_P, SILVER = item("silver", "minecraft:iron_nugget", "은조각")
GOLD_P, GOLD = item("gold", "minecraft:gold_nugget", "금조각")
