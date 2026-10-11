"""데이터팩 생성: 차원·차원 타입·바이옴·함수(TP, 초기 설정).

형식 근거: HANDOFF.md 2절 + 서버 jar에서 뽑은 바닐라 파일(ref/vanilla/).
ref/vanilla/ 의 바닐라 overworld 차원 타입·the_void 바이옴을 바탕으로
필요한 값만 덮어쓴다 (필드 이름 추측을 줄이기 위해). ref/ 는 tools.ci refs 로 갱신.
"""
from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field

import config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "ref")
NS = config.NAMESPACE
CLOCK = "minecraft:overworld"   # 모든 공간이 쓰는 시계


@dataclass
class Anchor:
    """TP 도착 지점."""
    name: str
    dim: str
    x: float
    y: float
    z: float
    yaw: float = 0.0
    pitch: float = 0.0
    title: str | None = None       # 암전 TP로 도착하면 화면에 띄울 글자
    on_arrive: list = field(default_factory=list)   # 도착하면 (TP한 플레이어로) 실행할 명령


@dataclass
class Portal:
    """상호작용 엔티티(클릭하면 TP). x,y,z는 엔티티 발밑 중앙."""
    dim: str
    x: float
    y: float
    z: float
    dest: str          # Anchor 이름
    width: float = 1.0
    height: float = 2.0


@dataclass
class Walk:
    """걸어 들어가면 TP되는 구역 (블록 범위, 끝 포함)."""
    dim: str
    box: tuple   # (x0, y0, z0, x1, y1, z1)
    dest: str
    fade: bool = False   # True: 암전 → TP → 도착지 청크 로딩 확인 → 암전 해제 + 제목

    def selector(self, base: str = "@a") -> str:
        x0, y0, z0, x1, y1, z1 = self.box
        inner = f"x={x0},y={y0},z={z0},dx={x1 - x0},dy={y1 - y0},dz={z1 - z0}"
        if base.endswith("]"):
            return base[:-1] + "," + inner + "]"
        return f"{base}[{inner}]"


@dataclass
class Links:
    anchors: dict = field(default_factory=dict)
    portals: list = field(default_factory=list)
    walks: list = field(default_factory=list)
    spawn: str | None = None  # 처음 접속 위치 (Anchor 이름)
    functions: dict = field(default_factory=dict)   # 빌더가 추가하는 함수 {이름: [명령]}
    tick: list = field(default_factory=list)        # 빌더가 추가하는 tick 명령
    scores: list = field(default_factory=list)      # 빌더가 쓰는 점수판 이름
    entity_cmds: list = field(default_factory=list) # 빌드 때 한 번 소환할 엔티티 명령 (build/entities)

    def walk(self, dim, box, dest, fade: bool = False) -> Walk:
        w = Walk(dim, tuple(int(v) for v in box), dest, fade)
        self.walks.append(w)
        return w

    def anchor(self, *a, **k) -> Anchor:
        an = Anchor(*a, **k)
        self.anchors[an.name] = an
        return an

    def portal(self, *a, **k) -> Portal:
        p = Portal(*a, **k)
        self.portals.append(p)
        return p


def _read_json(*parts):
    p = os.path.join(REF, *parts)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


def pack_format():
    v = _read_json("version.json")
    if v and "pack_version" in v:
        pv = v["pack_version"]
        if isinstance(pv, dict):
            return (pv.get("data_major", pv.get("data")), pv.get("data_minor", 0))
        return (pv, 0)
    return config.FALLBACK_PACK_FORMAT


def _fmt(n: float) -> str:
    return f"{n:g}"


# ------------------------------------------------------------------ JSON

def dimension_type(space: config.Space) -> dict:
    """바닐라 overworld 차원 타입을 바탕으로: 자기 시계, 타임라인 제거(하늘은 attributes 고정값), 높이·하늘 덮어쓰기."""
    base = _read_json("vanilla", "dimension_type", "overworld.json")
    if base is None:
        raise FileNotFoundError("ref/vanilla/dimension_type/overworld.json 없음 (python -m tools.ci refs)")
    d = json.loads(json.dumps(base))
    # 기본(오버월드) 시계를 같이 씀: 쉐이더(BSL/Iris)는 기본 시계 시각으로 하늘을 그리는 듯 (Phase 1 테스트 ③ 노을)
    # → 오버월드 시계를 자정에 멈춰 둠 (time_commands). 하늘 색 자체는 attributes 고정값
    d["default_clock"] = CLOCK
    d.pop("timelines", None)
    attrs = dict(d.get("attributes", {}))
    attrs.pop("minecraft:audio/ambient_sounds", None)  # 어두운 곳의 동굴 소리 끔
    attrs.update(space.attributes)
    d.update({
        "min_y": space.min_y,
        "height": space.height,
        "logical_height": space.height,
        "has_skylight": space.has_skylight,
        "has_fixed_time": True,
        "monster_spawn_block_light_limit": 0,
        "monster_spawn_light_level": 0,
        "attributes": dict(sorted(attrs.items())),
    })
    return dict(sorted(d.items()))


def biome(space: config.Space, attributes: dict | None = None, particles: list | None = None) -> dict:
    """공간 기본 바이옴 (attributes/particles 를 주면 추가 바이옴)."""
    particles = space.particles if particles is None else particles
    base = _read_json("vanilla", "worldgen", "biome", "the_void.json")
    if base is None:
        raise FileNotFoundError("ref/vanilla/worldgen/biome/the_void.json 없음")
    b = json.loads(json.dumps(base))
    b["has_precipitation"] = False
    b["features"] = []
    if "carvers" in b:
        b["carvers"] = []
    # 바이옴 시각 속성이 차원 값을 덮어쓰므로 지운다 (HANDOFF 2절)
    if isinstance(b.get("attributes"), dict):
        b["attributes"] = {k: v for k, v in b["attributes"].items() if not k.startswith("minecraft:visual/")}
    if attributes:
        b.setdefault("attributes", {}).update(attributes)
    if particles:  # 바닐라 basalt_deltas.json 과 같은 형식
        b.setdefault("attributes", {})["minecraft:visual/ambient_particles"] = {
            "argument": [{"particle": {"type": t}, "probability": p} for t, p in particles],
            "modifier": "append"}
    return b


def dimension(space: config.Space) -> dict:
    return {
        "type": space.dim,
        "generator": {
            "type": "minecraft:flat",
            "settings": {
                "biome": space.dim,
                "layers": [],
                "features": False,
                "lakes": False,
                "structure_overrides": [],
            },
        },
    }


# ------------------------------------------------------------------ 함수

FADE_IN = 10      # 암전 시작 후 TP까지 (틱)
FADE_MIN = 20     # 최소 암전 시간 (틱)
FADE_MAX = 200    # 청크가 안 불러와져도 이 시간이 지나면 해제
LOAD_R = 48       # 도착지 둘레 이만큼(블록)의 청크가 서버에 불러와졌으면 '로딩 끝'


def functions(links: Links) -> dict:
    f = {}
    f["load"] = [
        f"# {NS} 데이터팩 로드",
        "scoreboard objectives add ruina.state dummy",
        f"scoreboard objectives add {NS}.fade dummy",
    ] + [f"scoreboard objectives add {sc} dummy" for sc in links.scores]
    f["tick"] = [
        f"execute as @e[type=minecraft:interaction,tag={NS}.tp] if data entity @s interaction run function {NS}:tp/clicked",
        f"execute as @e[type=minecraft:interaction,tag={NS}.tp] if data entity @s attack run function {NS}:tp/clicked",
        f"execute as @a[tag=!{NS}.joined] at @s run function {NS}:first_join",
        f"execute as @a[tag={NS}.fading] at @s run function {NS}:tp/fade_tick",
    ]
    for w in links.walks:
        if w.dest not in links.anchors:
            raise KeyError(f"걷기 TP 목적지 {w.dest} 없음")
        kind = "fade" if w.fade else "to"
        f["tick"].append(f"execute in {w.dim} as {w.selector(f'@a[tag=!{NS}.fading]')} run function {NS}:tp/{kind}/{w.dest}")
    f["tick"] += links.tick
    f["first_join"] = [f"tag @s add {NS}.joined"]
    if links.spawn:
        f["first_join"].append(f"execute if dimension minecraft:overworld run function {NS}:tp/to/{links.spawn}")

    clicked = []
    for name in links.anchors:
        sel = f"@s[tag={NS}.to.{name}]"
        clicked.append(f"execute if entity {sel} if data entity @s interaction on target run function {NS}:tp/to/{name}")
        clicked.append(f"execute if entity {sel} if data entity @s attack on attacker run function {NS}:tp/to/{name}")
    clicked += ["data remove entity @s interaction", "data remove entity @s attack"]
    f["tp/clicked"] = clicked

    # 암전 TP: 시작 → (FADE_IN틱) TP → 도착지 둘레 청크가 서버에 불러와지면(최소 FADE_MIN틱) 암전 해제 + 제목
    tick = [f"scoreboard players add @s {NS}.fade 1"]
    done = ["effect clear @s minecraft:blindness", f"tag @s remove {NS}.fading", f"scoreboard players reset @s {NS}.fade"]
    c = LOAD_R
    loaded = " ".join(f"if loaded ~{dx} ~ ~{dz}" for dx in (-c, c) for dz in (-c, c))
    for name, a in links.anchors.items():
        f[f"tp/to/{name}"] = [
            f"execute in {a.dim} run tp @s {_fmt(a.x)} {_fmt(a.y)} {_fmt(a.z)} {_fmt(a.yaw)} {_fmt(a.pitch)}",
            f"execute at @s run playsound minecraft:item.book.page_turn master @s ~ ~ ~ 1 0.8",
        ] + list(a.on_arrive)
        f[f"tp/fade/{name}"] = [
            f"tag @s add {NS}.fading",
            f"tag @s add {NS}.fade.{name}",
            f"scoreboard players set @s {NS}.fade 0",
            "effect give @s minecraft:blindness infinite 0 true",
        ]
        tick.append(f"execute if score @s {NS}.fade matches {FADE_IN} if entity @s[tag={NS}.fade.{name}] "
                    f"run function {NS}:tp/to/{name}")
        if a.title:
            done.insert(0, f"execute if entity @s[tag={NS}.fade.{name}] run title @s title "
                           f'{{"text":"{a.title}","color":"#ecd6a6"}}')
        done.append(f"tag @s remove {NS}.fade.{name}")
    tick += [f"execute if score @s {NS}.fade matches {FADE_MIN}.. at @s {loaded} run function {NS}:tp/fade_done",
             f"execute if score @s {NS}.fade matches {FADE_MAX}.. run function {NS}:tp/fade_done"]
    f["tp/fade_tick"] = tick
    f["tp/fade_done"] = done

    setup = [f"gamerule {k} {v}" for k, v in config.GAMERULES.items()]
    setup += time_commands()
    if links.spawn:
        a = links.anchors[links.spawn]
        setup.append(f"execute in {a.dim} run setworldspawn {int(a.x)} {int(a.y)} {int(a.z)}")
    f["setup"] = setup

    ents = []
    for p in links.portals:
        if p.dest not in links.anchors:
            raise KeyError(f"포털 목적지 {p.dest} 없음")
        nbt = (f"{{width:{_fmt(p.width)}f,height:{_fmt(p.height)}f,response:1b,"
               f"Tags:[\"{NS}.tp\",\"{NS}.to.{p.dest}\"]}}")
        ents.append(f"execute in {p.dim} run summon minecraft:interaction {_fmt(p.x)} {_fmt(p.y)} {_fmt(p.z)} {nbt}")
    f["build/entities"] = ents + list(links.entity_cmds)
    for k, v in links.functions.items():
        if k in f:
            raise KeyError(f"함수 이름 겹침: {k}")
        f[k] = v
    return f


def time_commands() -> list[str]:
    """기본(오버월드) 시계를 자정에 멈춤 (모든 공간 공통)."""
    return [f"time of {CLOCK} set {config.CLOCK_TIME}", f"time of {CLOCK} pause"]


# ------------------------------------------------------------------ 출력

def write(out_dir: str, links: Links):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    data = os.path.join(out_dir, "data")

    def put(rel, obj):
        p = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            if isinstance(obj, str):
                fh.write(obj)
            else:
                json.dump(obj, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

    fmt = list(pack_format())
    put("pack.mcmeta", {"pack": {
        "description": "Library of Ruina - 도서관",
        "min_format": fmt,
        "max_format": fmt,
    }})
    for s in config.SPACES:
        put(f"data/{NS}/dimension_type/{s.id}.json", dimension_type(s))
        put(f"data/{NS}/dimension/{s.id}.json", dimension(s))
        put(f"data/{NS}/worldgen/biome/{s.id}.json", biome(s))
        for bid, extra in s.biomes.items():
            put(f"data/{NS}/worldgen/biome/{bid}.json", biome(s, extra.get("attributes"), extra.get("particles", [])))
    put("data/minecraft/tags/function/load.json", {"values": [f"{NS}:load"]})
    put("data/minecraft/tags/function/tick.json", {"values": [f"{NS}:tick"]})
    for name, lines in functions(links).items():
        put(f"data/{NS}/function/{name}.mcfunction", "\n".join(lines) + "\n")
    return data
