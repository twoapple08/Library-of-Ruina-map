"""공간별 빌더 모음. 각 모듈은 build(b: Build) 함수를 가진다."""
from __future__ import annotations

import os
import random

import numpy as np

import config
from tools import datapack
from tools.world import AIR, BlockRegistry, Dimension

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Build:
    """빌드 전체 상태: 차원별 블록, TP 연결, 서버 검증 목록."""

    def __init__(self):
        self.registry = BlockRegistry(os.path.join(ROOT, "ref", "blocks.json"))
        self.dims: dict[str, Dimension] = {}
        self.links = datapack.Links()
        self.extra_checks: list[dict] = []
        self.forceload: list[tuple] = []   # (차원, x, z): 서버가 엔티티를 소환할 수 있게 미리 불러올 칸

    def dim(self, space_id: str) -> Dimension:
        d = self.dims.get(space_id)
        if d is None:
            s = config.SPACE_BY_ID[space_id]
            d = Dimension(s.dim, s.min_y, s.height, s.dim, self.registry)
            self.dims[space_id] = d
        return d

    # ---------------------------------------------- 서버 검증 목록
    def block_checks(self, per_dim_chunks: int = 32, per_chunk: int = 24, seed: int = 1) -> list[dict]:
        """차원마다 몇 개 청크에서 블록을 무작위로 골라 '서버가 같은 블록을 읽는지' 확인할 목록."""
        rng = random.Random(seed)
        out = []
        for sid, d in self.dims.items():
            keys = sorted(d.chunk_keys())
            rng.shuffle(keys)
            for cx, cz in keys[:per_dim_chunks]:
                cells = []
                for (sx, sy, sz), arr in d.sections.items():
                    if (sx, sz) != (cx, cz):
                        continue
                    nz = np.argwhere(arr != 0)
                    for y, z, x in nz[rng.sample(range(len(nz)), min(len(nz), per_chunk))] if len(nz) else []:
                        cells.append((sx * 16 + int(x), sy * 16 + int(y), sz * 16 + int(z)))
                rng.shuffle(cells)
                cells = cells[:per_chunk]
                # 공기도 몇 개
                for _ in range(3):
                    cells.append((cx * 16 + rng.randrange(16), rng.randrange(d.min_y, d.min_y + d.height),
                                  cz * 16 + rng.randrange(16)))
                for x, y, z in cells:
                    out.append({"dim": d.dim, "x": x, "y": y, "z": z, "state": d.get(x, y, z)})
            for (x, y, z), be in d.block_entities.items():
                out.append({"dim": d.dim, "x": x, "y": y, "z": z, "state": d.get(x, y, z), "block_entity": be["id"]})
        return out

    def light_checks(self) -> list[dict]:
        """광원 바로 위/옆 칸은 블록 빛이 0보다 커야 한다 (서버가 조명을 계산했는지 확인)."""
        out = []
        for sid, d in self.dims.items():
            found = 0
            for (sx, sy, sz), arr in sorted(d.sections.items()):
                for state in ("minecraft:glowstone", "minecraft:sea_lantern", "minecraft:lantern[hanging=false]",
                              "minecraft:lantern[hanging=true]", "minecraft:copper_lantern[hanging=false]"):
                    i = d.index.get(state)
                    if i is None:
                        continue
                    for y, z, x in np.argwhere(arr == i)[:2]:
                        wx, wy, wz = sx * 16 + int(x), sy * 16 + int(y), sz * 16 + int(z)
                        for dx, dy, dz in ((0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
                            if d.get(wx + dx, wy + dy, wz + dz) == AIR:
                                out.append({"dim": d.dim, "x": wx + dx, "y": wy + dy, "z": wz + dz, "source": state})
                                found += 1
                                break
                    if found >= 3:
                        break
                if found >= 3:
                    break
        return out


def build_all(only: list[str] | None = None) -> Build:
    """월드에 들어가는 전체. 외부 + 로비 (전환 전 방 ↔ 전환 후 홀) + 역사 ~ 총류의 층 (10개)."""
    from . import (art, exterior, fragment, general, history, language, lighting, literature, lobby, natural_science,
                   philosophy,
                   religion, social_science, technology)
    b = Build()
    exterior.build(b)
    lobby.build(b)
    history.build(b)
    technology.build(b)
    literature.build(b)
    art.build(b)
    natural_science.build(b)
    language.build(b)
    social_science.build(b)
    philosophy.build(b)
    religion.build(b)
    general.build(b)
    fragment.finish(b)      # 층 사슬 (조각 교환·이전/다음 층 F)
    b.light_stats = lighting.light_all(b)   # 걸어 다니는 곳에 보이지 않는 빛 블록 (테스트 3차: 너무 어두움)
    return b
