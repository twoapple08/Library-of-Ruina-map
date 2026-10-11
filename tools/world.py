"""공간(차원)별 블록 저장소와 청크 NBT 변환.

- 블록은 차원 전체 팔레트의 번호(uint16)로 16³ 섹션 배열에 저장 (공기 = 0)
- 섹션 배열 순서는 마인크래프트와 같은 [y][z][x] (평탄화하면 index = y*256 + z*16 + x)
- 빌더용 API의 배열은 [x][y][z] 순서
- 블록이 하나라도 있는 청크만 파일로 쓴다. 나머지는 서버가 빈 공간(void)으로 생성
"""
from __future__ import annotations

import json
import math
import os
import re
from collections import defaultdict

import numpy as np

from . import nbt, region
from .nbt import Byte, Int, List, Long

AIR = "minecraft:air"

# 26.3 블록 팔레트 항목 = either(블록 ID 문자열, {Name, Properties}) (2026-10-11 서버 로그로 확인).
# 문자열은 속성 없는 기본 상태만 가능. NBT 리스트는 한 가지 타입이어야 하므로
# "mixed": 섹션 팔레트에 속성 있는 블록이 하나라도 있으면 전부 Compound, 없으면 전부 문자열.
PALETTE_FORMAT = "mixed"
_STATE_RE = re.compile(r"^([a-z0-9_.\-]+:)?([a-z0-9_./\-]+)(?:\[(.*)\])?$")


def parse_state(s: str) -> tuple[str, dict]:
    m = _STATE_RE.match(s.strip())
    if not m:
        raise ValueError(f"블록 상태 형식 오류: {s!r}")
    ns, path, props = m.groups()
    name = (ns or "minecraft:") + path
    d = {}
    if props:
        for kv in props.split(","):
            k, v = kv.split("=")
            d[k.strip()] = v.strip()
    return name, d


def canonical(s: str) -> str:
    name, props = parse_state(s)
    if not props:
        return name
    return name + "[" + ",".join(f"{k}={props[k]}" for k in sorted(props)) + "]"


class BlockRegistry:
    """서버 reports에서 뽑은 블록 목록(ref/blocks.json)으로 블록 이름·속성 검사."""

    def __init__(self, path: str | None):
        self.blocks = None
        if path and os.path.exists(path):
            with open(path) as f:
                self.blocks = json.load(f)

    def check(self, state: str):
        if self.blocks is None:
            return
        name, props = parse_state(state)
        b = self.blocks.get(name)
        if b is None:
            raise ValueError(f"없는 블록: {name}")
        allowed = b.get("p", {})
        for k, v in props.items():
            if k not in allowed:
                raise ValueError(f"{name}에 없는 속성: {k} (가능: {sorted(allowed)})")
            if v not in allowed[k]:
                raise ValueError(f"{name}[{k}]에 없는 값: {v} (가능: {allowed[k]})")


# ------------------------------------------------------------------ 비트 패킹

def pack_indices(idx: np.ndarray, bits: int) -> np.ndarray:
    """팔레트 인덱스 → LongArray (long 경계를 넘지 않음, 남는 비트 버림)."""
    per = 64 // bits
    n = -(-idx.size // per)
    pad = np.zeros(n * per, dtype=np.uint64)
    pad[:idx.size] = idx
    shifts = np.arange(per, dtype=np.uint64) * np.uint64(bits)
    longs = (pad.reshape(n, per) << shifts).sum(axis=1, dtype=np.uint64)
    return longs.view(np.int64)


def unpack_indices(longs: np.ndarray, bits: int, count: int) -> np.ndarray:
    per = 64 // bits
    u = np.asarray(longs, dtype=np.int64).view(np.uint64)
    shifts = np.arange(per, dtype=np.uint64) * np.uint64(bits)
    mask = np.uint64((1 << bits) - 1)
    vals = (u[:, None] >> shifts[None, :]) & mask
    return vals.reshape(-1)[:count].astype(np.int64)


def block_bits(n: int) -> int:
    return max(4, math.ceil(math.log2(n)))


def biome_bits(n: int) -> int:
    return max(1, math.ceil(math.log2(n)))


# ------------------------------------------------------------------ 차원

class Dimension:
    def __init__(self, dim: str, min_y: int, height: int, biome: str, registry: BlockRegistry | None = None):
        self.dim = dim
        self.min_y = min_y
        self.height = height
        self.biome = biome
        self.registry = registry or BlockRegistry(None)
        self.palette: list[str] = [AIR]
        self.index: dict[str, int] = {AIR: 0}
        self.sections: dict[tuple, np.ndarray] = {}
        self.block_entities: dict[tuple, dict] = {}

    # ---------------------------------------------- 팔레트
    def id(self, state: str) -> int:
        i = self.index.get(state)
        if i is not None:
            return i
        c = canonical(state)
        i = self.index.get(c)
        if i is None:
            self.registry.check(c)
            i = len(self.palette)
            if i >= 65535:
                raise OverflowError("블록 상태 종류가 너무 많음")
            self.palette.append(c)
            self.index[c] = i
        self.index[state] = i
        return i

    def _check_y(self, y0, y1):
        if y0 < self.min_y or y1 >= self.min_y + self.height:
            raise ValueError(f"{self.dim}: Y {y0}~{y1} 가 높이 범위 {self.min_y}~{self.min_y + self.height - 1} 밖")

    def _sec(self, key, create=True):
        s = self.sections.get(key)
        if s is None and create:
            s = np.zeros((16, 16, 16), dtype=np.uint16)
            self.sections[key] = s
        return s

    # ---------------------------------------------- 쓰기
    def set(self, x: int, y: int, z: int, state: str):
        self._check_y(y, y)
        i = self.id(state)
        s = self._sec((x >> 4, y >> 4, z >> 4), create=i != 0)
        if s is not None:
            s[y & 15, z & 15, x & 15] = i

    def get(self, x: int, y: int, z: int) -> str:
        s = self.sections.get((x >> 4, y >> 4, z >> 4))
        return AIR if s is None else self.palette[s[y & 15, z & 15, x & 15]]

    def _boxes(self, x0, y0, z0, x1, y1, z1):
        """(x0..x1, y0..y1, z0..z1 포함) 상자가 걸치는 섹션별 조각."""
        for sx in range(x0 >> 4, (x1 >> 4) + 1):
            ax0, ax1 = max(x0, sx * 16), min(x1, sx * 16 + 15)
            for sy in range(y0 >> 4, (y1 >> 4) + 1):
                ay0, ay1 = max(y0, sy * 16), min(y1, sy * 16 + 15)
                for sz in range(z0 >> 4, (z1 >> 4) + 1):
                    az0, az1 = max(z0, sz * 16), min(z1, sz * 16 + 15)
                    yield (sx, sy, sz), (ax0, ay0, az0, ax1, ay1, az1)

    def fill(self, x0, y0, z0, x1, y1, z1, state: str):
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))
        z0, z1 = sorted((z0, z1))
        self._check_y(y0, y1)
        i = self.id(state)
        for key, (ax0, ay0, az0, ax1, ay1, az1) in self._boxes(x0, y0, z0, x1, y1, z1):
            s = self._sec(key, create=i != 0)
            if s is not None:
                s[ay0 & 15:(ay1 & 15) + 1, az0 & 15:(az1 & 15) + 1, ax0 & 15:(ax1 & 15) + 1] = i

    def place(self, x0: int, y0: int, z0: int, ids: np.ndarray):
        """ids: [X,Y,Z] 정수 배열 (팔레트 번호, -1 = 건드리지 않음)."""
        ids = np.asarray(ids)
        X, Y, Z = ids.shape
        self._check_y(y0, y0 + Y - 1)
        for key, (ax0, ay0, az0, ax1, ay1, az1) in self._boxes(x0, y0, z0, x0 + X - 1, y0 + Y - 1, z0 + Z - 1):
            sub = ids[ax0 - x0:ax1 - x0 + 1, ay0 - y0:ay1 - y0 + 1, az0 - z0:az1 - z0 + 1]
            sub = sub.transpose(1, 2, 0)  # → [y,z,x]
            m = sub >= 0
            if not m.any():
                continue
            s = self.sections.get(key)
            if s is None:
                if not (sub[m] != 0).any():
                    continue
                s = self._sec(key)
            view = s[ay0 & 15:(ay1 & 15) + 1, az0 & 15:(az1 & 15) + 1, ax0 & 15:(ax1 & 15) + 1]
            view[m] = sub[m]

    def place_mask(self, x0: int, y0: int, z0: int, mask: np.ndarray, state: str):
        """mask: [X,Y,Z] bool. True인 칸에 state."""
        ids = np.where(np.asarray(mask, dtype=bool), self.id(state), -1).astype(np.int32)
        self.place(x0, y0, z0, ids)

    def block_entity(self, x: int, y: int, z: int, data: dict):
        self.block_entities[(x, y, z)] = data

    # ---------------------------------------------- 조회
    def chunk_keys(self) -> set:
        keys = {(cx, cz) for (cx, _, cz), s in self.sections.items() if s.any()}
        keys |= {(x >> 4, z >> 4) for (x, _, z) in self.block_entities}
        return keys

    def bounds(self):
        """내용이 있는 범위 (x0, y0, z0, x1, y1, z1) — 섹션 단위로 대략."""
        ks = [k for k, s in self.sections.items() if s.any()]
        if not ks:
            return None
        a = np.array(ks)
        lo, hi = a.min(0) * 16, a.max(0) * 16 + 15
        return int(lo[0]), int(lo[1]), int(lo[2]), int(hi[0]), int(hi[1]), int(hi[2])

    # ---------------------------------------------- 청크 NBT
    def chunk_nbt(self, cx: int, cz: int, data_version: int) -> dict:
        sy0 = self.min_y >> 4
        sy1 = (self.min_y + self.height - 1) >> 4
        biomes = {"palette": List([self.biome])}
        sections = List(elem_tag=nbt.TAG_COMPOUND)
        for sy in range(sy0, sy1 + 1):
            sec = {"Y": Byte(sy)}
            s = self.sections.get((cx, sy, cz))
            if s is None or not s.any():
                sec["block_states"] = {"palette": List([AIR if PALETTE_FORMAT == "mixed" else {"Name": AIR}])}
            else:
                uniq, inv = np.unique(s.ravel(), return_inverse=True)
                pal = List()
                as_str = PALETTE_FORMAT == "mixed" and not any("[" in self.palette[u] for u in uniq)
                for u in uniq:
                    if as_str:
                        pal.append(self.palette[u])
                    else:
                        name, props = parse_state(self.palette[u])
                        e = {"Name": name}
                        if props:
                            e["Properties"] = props
                        pal.append(e)
                bs = {"palette": pal}
                if len(uniq) > 1:
                    bs["data"] = pack_indices(inv.astype(np.uint64), block_bits(len(uniq)))
                sec["block_states"] = bs
            sec["biomes"] = biomes
            sections.append(sec)
        bes = List(elem_tag=nbt.TAG_COMPOUND)
        for (x, y, z), data in self.block_entities.items():
            if (x >> 4, z >> 4) == (cx, cz):
                e = {"id": data["id"], "x": Int(x), "y": Int(y), "z": Int(z), "keepPacked": Byte(0)}
                e.update({k: v for k, v in data.items() if k != "id"})
                bes.append(e)
        return {
            "DataVersion": Int(data_version),
            "xPos": Int(cx),
            "zPos": Int(cz),
            "yPos": Int(sy0),
            "Status": "minecraft:full",
            "LastUpdate": Long(0),
            "InhabitedTime": Long(0),
            "isLightOn": Byte(0),
            "sections": sections,
            "block_entities": bes,
            "Heightmaps": {},
            "fluid_ticks": List(elem_tag=nbt.TAG_COMPOUND),
            "block_ticks": List(elem_tag=nbt.TAG_COMPOUND),
            "PostProcessing": List([List(elem_tag=nbt.TAG_END) for _ in range(sy0, sy1 + 1)], elem_tag=nbt.TAG_LIST),
            "structures": {"References": {}, "starts": {}},
        }

    def write_regions(self, region_dir: str, data_version: int) -> int:
        """청크를 리전 파일로 쓴다. 반환: 쓴 청크 수."""
        os.makedirs(region_dir, exist_ok=True)
        by_region = defaultdict(list)
        for cx, cz in self.chunk_keys():
            by_region[(cx >> 5, cz >> 5)].append((cx, cz))
        n = 0
        for (rx, rz), keys in sorted(by_region.items()):
            chunks = {k: nbt.dumps(self.chunk_nbt(k[0], k[1], data_version)) for k in keys}
            region.write_region(os.path.join(region_dir, region.region_name(rx, rz)), chunks)
            n += len(chunks)
        return n


# ------------------------------------------------------------------ 읽기 (검증용)

def decode_section_blocks(sec: dict) -> np.ndarray | None:
    """섹션 NBT → [y,z,x] 블록 상태 문자열 배열."""
    bs = sec.get("block_states")
    if bs is None:
        return None
    pal = []
    for e in bs["palette"]:
        if isinstance(e, str):
            pal.append(canonical(e))
            continue
        props = e.get("Properties", {})
        pal.append(e["Name"] + ("[" + ",".join(f"{k}={props[k]}" for k in sorted(props)) + "]" if props else ""))
    if "data" not in bs:
        return np.full((16, 16, 16), pal[0], dtype=object)
    idx = unpack_indices(bs["data"], block_bits(len(pal)), 4096)
    return np.array(pal, dtype=object)[idx].reshape(16, 16, 16)


def chunk_block(chunk: dict, x: int, y: int, z: int) -> str:
    for sec in chunk["sections"]:
        if sec["Y"] == y >> 4:
            arr = decode_section_blocks(sec)
            return AIR if arr is None else arr[y & 15, z & 15, x & 15]
    return AIR
