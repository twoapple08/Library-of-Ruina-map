"""입체 미리보기: 등각(아이소메트릭) 투영 + Z버퍼, 면 음영, 블록 테두리, 발광 블록 빛 번짐, 원근 안개.

view: 'se','sw','nw','ne' = 그 방향 위에서 내려다봄 (예: 'se' = 남동쪽 하늘에서 북서쪽을 봄)
      'front' = 남쪽 위에서 비스듬히 (정면 입면 + 깊이)
lod:  1 = 블록 하나씩, 2/4/8 = 그만큼 묶어서 (큰 공간 전체 보기용)
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .preview import Palette, _frame
from .world import Dimension

EMISSIVE = ("glowstone", "lantern", "froglight", "sea_lantern", "shroomlight", "torch", "end_rod", "lava",
            "magma_block", "jack_o_lantern", "beacon", "glow_lichen", "redstone_lamp[lit=true", "lit=true",
            "fire", "crying_obsidian", "amethyst_cluster", "respawn_anchor", "light[")
NOT_FULL = ("stairs", "slab", "lantern", "glass", "pane", "fence", "wall", "door", "trapdoor", "carpet", "torch",
            "chain", "rod", "candle", "sign", "button", "pressure_plate", "rail", "ladder", "bars", "lectern",
            "leaves", "flower", "grass[", "short_grass", "fern", "vine", "snow[", "head", "skull", "banner", "pot",
            "_shelf", "lichen", "light[", "scaffolding", "cobweb", "bush", "sapling", "coral", "roots", "kelp",
            "water", "lava", "barrier", "structure_void", "air")


# 발광 블록은 텍스처 평균색(철 테두리 등 섞임) 대신 빛 색으로
GLOW_COLORS = [("soul_lantern", (120, 220, 230)), ("copper_lantern", (170, 230, 140)), ("lantern", (255, 190, 90)),
               ("ochre_froglight", (255, 220, 130)), ("pearlescent_froglight", (250, 215, 225)),
               ("verdant_froglight", (210, 245, 170)), ("glowstone", (255, 215, 120)), ("shroomlight", (255, 160, 80)),
               ("sea_lantern", (200, 235, 230)), ("end_rod", (250, 245, 235)), ("torch", (255, 200, 100))]


def _glow_lut(dim: Dimension, lut: np.ndarray) -> np.ndarray:
    out = lut.copy()
    for i, s in enumerate(dim.palette):
        for k, col in GLOW_COLORS:
            if k in s:
                out[i] = col
                break
    return out


def _flags(dim: Dimension):
    pal = dim.palette
    emis = np.array([any(k in s for k in EMISSIVE) for s in pal])
    full = np.array([s != "minecraft:air" and not any(k in s for k in NOT_FULL) for s in pal])
    return emis, full


# ------------------------------------------------------------------ 복셀 목록

def voxels(dim: Dimension, box=None, lod: int = 1):
    """(N,3) 좌표(lod 단위), 팔레트 번호. lod>1 이면 lod³ 칸마다 대표 블록 하나 (가장 높은 칸 우선)."""
    xs, ids = [], []
    if box is not None:
        bx0, by0, bz0, bx1, by1, bz1 = box
    for (sx, sy, sz), arr in dim.sections.items():
        if box is not None and (sx * 16 > bx1 or sx * 16 + 15 < bx0 or sy * 16 > by1 or sy * 16 + 15 < by0
                                or sz * 16 > bz1 or sz * 16 + 15 < bz0):
            continue
        a = arr  # [y,z,x]
        if lod > 1:
            k = lod
            n = 16 // k
            b = a.reshape(n, k, n, k, n, k).transpose(0, 2, 4, 1, 3, 5).reshape(n, n, n, k ** 3)
            # 대표: 위쪽(큰 y) 우선으로 처음 만나는 블록
            order = np.argsort(-np.repeat(np.arange(k), k * k))  # y가 큰 것부터
            bb = b[..., order]
            nz = bb != 0
            has = nz.any(-1)
            first = nz.argmax(-1)
            rep = np.take_along_axis(bb, first[..., None], -1)[..., 0]
            yzx = np.argwhere(has)
            if not len(yzx):
                continue
            base = np.array([sy * n, sz * n, sx * n])
            g = yzx + base
            xs.append(np.stack([g[:, 2], g[:, 0], g[:, 1]], 1))
            ids.append(rep[has])
        else:
            yzx = np.argwhere(a != 0)
            if not len(yzx):
                continue
            g = yzx + np.array([sy * 16, sz * 16, sx * 16])
            xs.append(np.stack([g[:, 2], g[:, 0], g[:, 1]], 1))
            ids.append(a[a != 0])
    if not xs:
        return np.zeros((0, 3), np.int64), np.zeros(0, np.int64)
    X = np.concatenate(xs).astype(np.int64)
    I = np.concatenate(ids).astype(np.int64)
    if box is not None and lod == 1:
        m = ((X[:, 0] >= bx0) & (X[:, 0] <= bx1) & (X[:, 1] >= by0) & (X[:, 1] <= by1)
             & (X[:, 2] >= bz0) & (X[:, 2] <= bz1))
        X, I = X[m], I[m]
    return X, I


def _key(X):
    return (X[:, 0] + (1 << 20)) * (1 << 42) + (X[:, 1] + (1 << 20)) * (1 << 21) + (X[:, 2] + (1 << 20))


def _present(sorted_keys, q):
    i = np.searchsorted(sorted_keys, q)
    i = np.clip(i, 0, len(sorted_keys) - 1)
    return sorted_keys[i] == q


# ------------------------------------------------------------------ 투영

_ROT = {"se": lambda x, z: (x, z), "sw": lambda x, z: (z, -x), "nw": lambda x, z: (-x, -z), "ne": lambda x, z: (-z, x),
        "front": lambda x, z: (x, z)}


def _sprites(a: int, c: int, front: bool):
    """블록 하나의 화면 픽셀 조각: 면별 (du, dv, 테두리여부). 원점 = 블록 (0,0,0) 꼭짓점의 투영."""
    if front:
        b = a // 2

        def proj(x, y, z):
            return x * a, z * b - y * c
        faces = {0: [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],      # 윗면
                 1: [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]}      # 남쪽 면
    else:
        def proj(x, y, z):
            return (x - z) * a, (x + z) * a // 2 - y * c
        faces = {0: [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],      # 윗면
                 1: [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],      # 남쪽(왼쪽) 면
                 2: [(1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)]}      # 동쪽(오른쪽) 면
    out = {}
    for f, corners in faces.items():
        pts = [proj(*p) for p in corners]
        us, vs = [p[0] for p in pts], [p[1] for p in pts]
        ox, oy = -min(us) + 1, -min(vs) + 1
        W, H = max(us) - min(us) + 3, max(vs) - min(vs) + 3
        im = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(im)
        poly = [(u + ox, v + oy) for u, v in pts]
        d.polygon(poly, fill=1)
        if a >= 6:
            d.line(poly + [poly[0]], fill=2, width=1)
        arr = np.asarray(im)
        vv, uu = np.nonzero(arr)
        out[f] = (uu - ox, vv - oy, arr[vv, uu] == 2)
    return out


def render_iso(dim: Dimension, pal: Palette, box=None, view: str = "se", lod: int = 1, a: int = None,
               target: int = 1400, night: bool = True, fog: float = 0.35, bg=((40, 24, 70), (14, 10, 26)),
               glow: float = 1.0):
    X, I = voxels(dim, box, lod)
    if len(X) == 0:
        return Image.new("RGB", (400, 300), bg[1])
    emis_p, full_p = _flags(dim)
    top_c = _glow_lut(dim, pal.lut(dim, 0))
    side_c = _glow_lut(dim, pal.lut(dim, 1))
    rx, rz = _ROT[view](X[:, 0], X[:, 2])
    R = np.stack([rx, X[:, 1], rz], 1)
    front = view == "front"
    # 가려진 면 빼기 (불투명 꽉 찬 블록만 가림)
    opaque = full_p[I]
    keys = np.sort(_key(R[opaque]))
    faces_dir = {0: (0, 1, 0), 1: (0, 0, 1), 2: (1, 0, 0)}
    if front:
        faces_dir.pop(2)
    # 화면 크기 정하기
    span_u = (R[:, 0] - R[:, 2]) if not front else R[:, 0]
    width_units = span_u.max() - span_u.min() + 2
    if a is None:
        a = int(max(2, min(16, target // max(1, width_units))))
        a -= a % 2
        a = max(a, 2)
    c = int(round(a * 1.15))
    spr = _sprites(a, c, front)
    if front:
        U0 = R[:, 0] * a
        V0 = R[:, 2] * (a // 2) - R[:, 1] * c
        close = R[:, 2] + R[:, 1] * (a / 2) / c
    else:
        U0 = (R[:, 0] - R[:, 2]) * a
        V0 = (R[:, 0] + R[:, 2]) * a // 2 - R[:, 1] * c
        close = R[:, 0] + R[:, 2] + R[:, 1] * a / c
    umin, vmin = U0.min() - 2 * a, V0.min() - 2 * c - a
    umax, vmax = U0.max() + 3 * a, V0.max() + 2 * a + c
    W, H = int(umax - umin), int(vmax - vmin)
    cmin, cmax = close.min(), close.max()
    zbuf = np.full(W * H, -np.inf)
    cbuf = np.zeros((W * H, 3), np.float32)
    ebuf = np.zeros(W * H, np.float32)
    shade = {0: 1.0, 1: 0.80, 2: 0.62} if not front else {0: 1.0, 1: 0.78}
    emis = emis_p[I]
    for f, (dx, dy, dz) in faces_dir.items():
        nb = R + np.array([dx, dy, dz])
        vis = ~_present(keys, _key(nb)) | ~opaque
        idx = np.nonzero(vis)[0]
        if not len(idx):
            continue
        du, dv, edge = spr[f]
        base_col = (top_c if f == 0 else side_c)[I[idx]]
        sh = np.where(emis[idx], 1.0, shade[f])
        if night:
            sh = np.where(emis[idx], 1.15, sh * 0.72)
        depth01 = (close[idx] - cmin) / max(1e-9, cmax - cmin)
        for s in range(0, len(idx), 200_000):
            j = idx[s:s + 200_000]
            col = base_col[s:s + 200_000] * sh[s:s + 200_000, None]
            fogk = (fog * (1 - depth01[s:s + 200_000]))[:, None]
            col = col * (1 - fogk) + np.array(bg[1], np.float32) * fogk
            pu = (U0[j][:, None] + du[None] - umin).astype(np.int64)
            pv = (V0[j][:, None] + dv[None] - vmin).astype(np.int64)
            pix = (pv * W + pu).ravel()
            cl = np.repeat(close[j], len(du))
            cc = np.repeat(col, len(du), axis=0)
            ee = np.repeat(emis[j].astype(np.float32), len(du))
            if edge.any():
                ed = np.tile(edge, len(j))
                cc[ed] *= 0.82
            order = np.argsort(cl, kind="stable")
            pix, cl, cc, ee = pix[order], cl[order], cc[order], ee[order]
            # 픽셀마다 가장 가까운 것 (뒤에서부터 첫 번째)
            rev = pix[::-1]
            _, first = np.unique(rev, return_index=True)
            pick = len(pix) - 1 - first
            p, cpk = pix[pick], cl[pick]
            better = cpk > zbuf[p]
            p = p[better]
            zbuf[p] = cpk[better]
            cbuf[p] = cc[pick][better]
            ebuf[p] = ee[pick][better]
    # 배경 (세로 그라데이션)
    t = np.linspace(0, 1, H)[:, None]
    bgimg = (np.array(bg[0])[None] * (1 - t) + np.array(bg[1])[None] * t)  # (H,3)
    img = np.repeat(bgimg[:, None, :], W, axis=1).reshape(-1, 3).astype(np.float32)
    hit = np.isfinite(zbuf)
    img[hit] = cbuf[hit]
    img = img.reshape(H, W, 3)
    if glow > 0 and ebuf.any():
        e = (ebuf.reshape(H, W, 1) * img).clip(0, 255).astype(np.uint8)
        gl = Image.fromarray(e, "RGB")
        g1 = np.asarray(gl.filter(ImageFilter.GaussianBlur(max(2, a * 1.5))), np.float32)
        g2 = np.asarray(gl.filter(ImageFilter.GaussianBlur(max(4, a * 5))), np.float32)
        img = img + glow * (1.1 * g1 + 0.9 * g2)
    out = Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGB")
    if max(out.size) > target * 1.25:
        k = target / max(out.size)
        out = out.resize((max(1, int(W * k)), max(1, int(H * k))), Image.LANCZOS)
    return out


def iso_panel(dim, pal, title, notes=(), **kw):
    img = render_iso(dim, pal, **kw)
    view = kw.get("view", "se")
    look = {"se": "남동쪽 위에서", "sw": "남서쪽 위에서", "nw": "북서쪽 위에서", "ne": "북동쪽 위에서",
            "front": "남쪽 위에서 비스듬히"}[view]
    lod = kw.get("lod", 1)
    extra = f"{look} 본 입체도" + (f" · {lod}칸 묶음 표시" if lod > 1 else "")
    return _frame(img, title, list(notes) + [extra])
