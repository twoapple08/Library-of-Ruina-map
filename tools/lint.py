"""블록 품질 검사 (PLAN 1절 '최적화: 낭비 금지').

- 숨은 블록: 6면이 모두 불투명 꽉 찬 블록에 막힌 칸 (안 보이는 속 채움)
- 흐르는 물·용암 (level != 0)
- 떨어지는 블록(모래·자갈·콘크리트 가루 등) 아래가 비었음
- 받침이 필요한 블록: 서 있는 랜턴·초·카펫 아래가 빔, 매달린 랜턴 위가 빔
- 사라지는 잎 (persistent=true 아님)
결과는 경고 목록 + 숫자. 빌드를 막지는 않는다.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .render3d import NOT_FULL
from .world import AIR, Dimension, parse_state

GRAVITY = ("minecraft:sand", "minecraft:red_sand", "minecraft:gravel", "minecraft:anvil", "minecraft:chipped_anvil",
           "minecraft:damaged_anvil", "minecraft:dragon_egg", "minecraft:suspicious_sand",
           "minecraft:suspicious_gravel", "minecraft:scaffolding")
NEEDS_BELOW = ("carpet", "candle", "flower_pot", "rail", "pressure_plate", "_sapling", "torch", "redstone_wire",
               "_button", "lever", "snow[")


@dataclass
class LintResult:
    dim: str
    blocks: int = 0
    hidden: int = 0
    issues: list = field(default_factory=list)   # (종류, 개수, 예시 좌표들)

    def lines(self) -> list[str]:
        pct = 100.0 * self.hidden / max(1, self.blocks)
        out = [f"{self.dim}: 블록 {self.blocks:,}개, 숨은 블록 {self.hidden:,}개 ({pct:.1f}%)"]
        for kind, n, ex in self.issues:
            out.append(f"  - {kind}: {n}곳 (예: {', '.join(str(e) for e in ex[:3])})")
        return out


def _neighbors(dim: Dimension, key):
    """섹션 + 6방향 이웃 섹션으로 [18,18,18] (y,z,x) 패딩 배열."""
    sx, sy, sz = key
    out = np.zeros((18, 18, 18), dtype=np.int32)
    out[1:-1, 1:-1, 1:-1] = dim.sections[key]
    get = dim.sections.get
    n = get((sx, sy - 1, sz))
    if n is not None:
        out[0, 1:-1, 1:-1] = n[15]
    n = get((sx, sy + 1, sz))
    if n is not None:
        out[17, 1:-1, 1:-1] = n[0]
    n = get((sx, sy, sz - 1))
    if n is not None:
        out[1:-1, 0, 1:-1] = n[:, 15]
    n = get((sx, sy, sz + 1))
    if n is not None:
        out[1:-1, 17, 1:-1] = n[:, 0]
    n = get((sx - 1, sy, sz))
    if n is not None:
        out[1:-1, 1:-1, 0] = n[:, :, 15]
    n = get((sx + 1, sy, sz))
    if n is not None:
        out[1:-1, 1:-1, 17] = n[:, :, 0]
    return out


def lint(dim: Dimension, max_examples: int = 5) -> LintResult:
    pal = dim.palette
    full = np.array([s != AIR and not any(k in s for k in NOT_FULL) for s in pal])
    flowing = np.array([(s.startswith("minecraft:water[") or s.startswith("minecraft:lava[")) and "level=0" not in s
                        for s in pal])
    gravity = np.array([parse_state(s)[0] in GRAVITY or parse_state(s)[0].endswith("_concrete_powder") for s in pal])
    def is_lantern(s):
        return s.split("[")[0].endswith("lantern") and "sea_lantern" not in s and "jack_o" not in s
    below = np.array([(any(k in s for k in NEEDS_BELOW) and "wall_" not in s)
                      or (is_lantern(s) and "hanging=true" not in s) for s in pal])
    above = np.array([is_lantern(s) and "hanging=true" in s for s in pal])
    leaves = np.array(["leaves" in s and "persistent=true" not in s for s in pal])
    r = LintResult(dim.dim)
    found: dict[str, list] = {}

    def note(kind, mask, base):
        if mask.any():
            pts = np.argwhere(mask)
            lst = found.setdefault(kind, [0, []])
            lst[0] += len(pts)
            for y, z, x in pts[:max_examples - len(lst[1])] if len(lst[1]) < max_examples else []:
                lst[1].append((base[0] + int(x), base[1] + int(y), base[2] + int(z)))

    for key in sorted(dim.sections):
        arr = dim.sections[key]
        if not arr.any():
            continue
        p = _neighbors(dim, key)
        f = full[p]
        core = arr
        base = (key[0] * 16, key[1] * 16, key[2] * 16)
        r.blocks += int((core != 0).sum())
        hidden = (f[1:-1, 1:-1, 1:-1] & f[:-2, 1:-1, 1:-1] & f[2:, 1:-1, 1:-1] & f[1:-1, :-2, 1:-1]
                  & f[1:-1, 2:, 1:-1] & f[1:-1, 1:-1, :-2] & f[1:-1, 1:-1, 2:])
        r.hidden += int(hidden.sum())
        empty_below = p[:-2, 1:-1, 1:-1] == 0
        empty_above = p[2:, 1:-1, 1:-1] == 0
        note("흐르는 물·용암", flowing[core], base)
        note("떨어지는 블록 아래가 빔", gravity[core] & empty_below, base)
        note("받침 없는 블록(아래가 빔)", below[core] & empty_below, base)
        note("매달린 랜턴 위가 빔", above[core] & empty_above, base)
        note("사라지는 잎(persistent 아님)", leaves[core], base)
    r.issues = [(k, v[0], v[1]) for k, v in found.items()]
    return r


def lint_build(b) -> list[str]:
    lines = []
    for d in b.dims.values():
        lines += lint(d).lines()
    ents = len(b.links.portals)
    bes = sum(len(d.block_entities) for d in b.dims.values())
    lines.append(f"엔티티(TP 상호작용) {ents}개, 블록 엔티티 {bes}개")
    return lines
