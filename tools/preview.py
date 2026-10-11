"""폰으로 확인할 미리보기 PNG: 위에서 본 모습(높이 음영), 정면 입면도, 단면.

블록 색은 ref/block_colors.json (CI가 클라이언트 텍스처 평균색으로 계산). 없으면 이름으로 대충 추정.
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .world import Dimension

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATHS = ["/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
              "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"]

_FALLBACK = [  # (이름 조각, 색)
    ("glowstone", "#f5d27a"), ("sea_lantern", "#cfe8e0"), ("lantern", "#f2b54a"), ("shroomlight", "#f19a4a"),
    ("gold", "#f3cf45"), ("deepslate", "#4a4a50"), ("blackstone", "#2c2830"), ("black", "#1a1a1e"),
    ("dark_oak", "#4b3220"), ("spruce", "#6b4f30"), ("bookshelf", "#7a5a3a"), ("carpet", "#9a2a2a"),
    ("glass", "#b8d8e0"), ("water", "#3f76e4"), ("stone", "#808080"), ("planks", "#a07a4a"), ("log", "#5a4630"),
    ("concrete", "#909090"), ("copper", "#c06a4a"), ("amethyst", "#8a5ac0"),
]


def _font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size=size)


def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in range(0, len(c), 2))


class Palette:
    def __init__(self):
        p = os.path.join(ROOT, "ref", "block_colors.json")
        self.table = {}
        if os.path.exists(p):
            with open(p) as f:
                self.table = json.load(f)

    def color(self, state: str, face: int) -> tuple:
        """face 0 = 윗면, 1 = 옆면. (r, g, b)"""
        name = state.split("[")[0]
        t = self.table.get(name)
        if t:
            return _hex(t[face])[:3]
        short = name.split(":")[-1]
        for key, c in _FALLBACK:
            if key in short:
                return _hex(c)
        h = hashlib.md5(name.encode()).digest()
        return (80 + h[0] % 120, 80 + h[1] % 120, 80 + h[2] % 120)

    def lut(self, dim: Dimension, face: int) -> np.ndarray:
        return np.array([self.color(s, face) for s in dim.palette], dtype=np.float32)


# ------------------------------------------------------------------ 계산

def heightmap(dim: Dimension, x0, z0, x1, z1, y_max=None):
    """(x0..x1, z0..z1) 각 칸에서 가장 높은 블록의 높이와 팔레트 번호. 없으면 높이 = min_y-1."""
    W, H = x1 - x0 + 1, z1 - z0 + 1
    hy = np.full((W, H), dim.min_y - 1, dtype=np.int32)
    hid = np.zeros((W, H), dtype=np.int32)
    y_max = dim.min_y + dim.height - 1 if y_max is None else y_max
    keys = [k for k in dim.sections if x0 >> 4 <= k[0] <= x1 >> 4 and z0 >> 4 <= k[2] <= z1 >> 4
            and k[1] * 16 <= y_max]
    for sx, sy, sz in sorted(keys, key=lambda k: -k[1]):
        arr = dim.sections[(sx, sy, sz)]
        top = min(15, y_max - sy * 16)
        a = arr[:top + 1]
        nz = a != 0
        if not nz.any():
            continue
        # 위에서부터 첫 블록: y 축을 뒤집어 argmax
        rev = nz[::-1]
        has = rev.any(axis=0)                     # [z,x]
        ly = top - rev.argmax(axis=0)            # [z,x]
        ids = np.take_along_axis(a, ly[None], axis=0)[0]
        gx0, gz0 = sx * 16, sz * 16
        lx0, lx1 = max(x0, gx0), min(x1, gx0 + 15)
        lz0, lz1 = max(z0, gz0), min(z1, gz0 + 15)
        sub_has = has[lz0 - gz0:lz1 - gz0 + 1, lx0 - gx0:lx1 - gx0 + 1].T
        sub_y = (ly + sy * 16)[lz0 - gz0:lz1 - gz0 + 1, lx0 - gx0:lx1 - gx0 + 1].T
        sub_id = ids[lz0 - gz0:lz1 - gz0 + 1, lx0 - gx0:lx1 - gx0 + 1].T
        view_y = hy[lx0 - x0:lx1 - x0 + 1, lz0 - z0:lz1 - z0 + 1]
        view_id = hid[lx0 - x0:lx1 - x0 + 1, lz0 - z0:lz1 - z0 + 1]
        upd = sub_has & (view_y < sub_y)
        view_y[upd] = sub_y[upd]
        view_id[upd] = sub_id[upd]
    return hy, hid


def elevation(dim: Dimension, x0, x1, y0, y1, z_near, z_far, axis="z"):
    """옆에서 본 모습. axis='z': 남쪽(+Z)에서 북쪽을 봄 (z_near > z_far). 반환: 깊이[x,y], 번호[x,y]."""
    W, H = x1 - x0 + 1, y1 - y0 + 1
    depth = np.full((W, H), -1, dtype=np.int32)
    hid = np.zeros((W, H), dtype=np.int32)
    zlo, zhi = min(z_near, z_far), max(z_near, z_far)
    for (sx, sy, sz), arr in dim.sections.items():
        if axis == "z":
            if not (x0 >> 4 <= sx <= x1 >> 4 and y0 >> 4 <= sy <= y1 >> 4 and zlo >> 4 <= sz <= zhi >> 4):
                continue
            a = arr.transpose(2, 0, 1)  # [x,y,z]
            g0, g1, g2 = sx * 16, sy * 16, sz * 16
        else:  # axis='x': 동쪽(+X)에서 서쪽을 봄, 가로축은 z (남→북 순서로 그리기 위해 뒤집음)
            if not (x0 >> 4 <= sz <= x1 >> 4 and y0 >> 4 <= sy <= y1 >> 4 and zlo >> 4 <= sx <= zhi >> 4):
                continue
            a = arr.transpose(1, 0, 2)  # [z,y,x]
            g0, g1, g2 = sz * 16, sy * 16, sx * 16
        c0, c1 = max(zlo, g2), min(zhi, g2 + 15)
        a = a[:, :, c0 - g2:c1 - g2 + 1]
        nz = a != 0
        if not nz.any():
            continue
        # 가까운 쪽(큰 z)부터 첫 블록
        rev = nz[:, :, ::-1]
        has = rev.any(axis=2)
        k = rev.argmax(axis=2)
        dz = (c1 - k) - z_far if z_near > z_far else (c0 + k) - z_far
        ids = np.take_along_axis(a[:, :, ::-1], k[:, :, None], axis=2)[:, :, 0]
        lx0, lx1 = max(x0, g0), min(x1, g0 + 15)
        ly0, ly1 = max(y0, g1), min(y1, g1 + 15)
        sl = (slice(lx0 - g0, lx1 - g0 + 1), slice(ly0 - g1, ly1 - g1 + 1))
        dv = depth[lx0 - x0:lx1 - x0 + 1, ly0 - y0:ly1 - y0 + 1]
        iv = hid[lx0 - x0:lx1 - x0 + 1, ly0 - y0:ly1 - y0 + 1]
        upd = has[sl] & (dz[sl] > dv)
        dv[upd] = dz[sl][upd]
        iv[upd] = ids[sl][upd]
    return depth, hid


# ------------------------------------------------------------------ 그리기

BG = (24, 20, 34)


def _scale(img: Image.Image, target=1200) -> Image.Image:
    w, h = img.size
    k = max(1, min(16, target // max(w, h)))
    return img.resize((w * k, h * k), Image.NEAREST), k


def _frame(img: Image.Image, title: str, notes: list[str]) -> Image.Image:
    f1, f2 = _font(28), _font(20)
    pad = 16
    head = 50 + 28 * len(notes)
    W = max(img.width + pad * 2, 700)
    out = Image.new("RGB", (W, img.height + head + pad), BG)
    d = ImageDraw.Draw(out)
    d.text((pad, 10), title, font=f1, fill=(240, 230, 255))
    for i, n in enumerate(notes):
        d.text((pad, 48 + 28 * i), n, font=f2, fill=(190, 180, 210))
    out.paste(img, (pad, head))
    return out


def render_top(dim: Dimension, pal: Palette, box, title, notes=(), y_max=None, marks=(), target=1200):
    x0, z0, x1, z1 = box
    hy, hid = heightmap(dim, x0, z0, x1, z1, y_max)
    lut = pal.lut(dim, 0)
    rgb = lut[hid]
    empty = hy < dim.min_y
    filled = hy[~empty]
    lo, hi = (filled.min(), filled.max()) if filled.size else (0, 1)
    shade = 0.55 + 0.45 * (hy - lo) / max(1, hi - lo)
    # 북서쪽 빛: 북서 이웃보다 높으면 밝게
    nw = np.pad(hy, ((1, 0), (1, 0)), mode="edge")[:-1, :-1]
    shade = shade * np.clip(1 + 0.08 * (hy - nw), 0.75, 1.25)
    rgb = rgb * shade[..., None]
    rgb[empty] = BG
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8).transpose(1, 0, 2), "RGB")  # [z,x] → 가로 x, 세로 z
    img, k = _scale(img, target)
    d = ImageDraw.Draw(img)
    _grid(d, img, k, x0, z0, x1, z1)
    for (mx, mz, label, color) in marks:
        px, pz = (mx - x0) * k, (mz - z0) * k
        r = max(4, k)
        d.ellipse((px - r, pz - r, px + r, pz + r), outline=color, width=3)
        d.text((px + r + 3, pz - r - 2), label, font=_font(18), fill=color)
    return _frame(img, title, list(notes) + [f"X {x0}~{x1}, Z {z0}~{z1} · 위쪽 = 북(-Z) · 격자 16칸(청크)"])


def render_side(dim: Dimension, pal: Palette, box, title, notes=(), axis="z", cut=None, target=1200):
    """box = (가로0, y0, 가로1, y1, 앞, 뒤). axis='z'면 가로=x, 앞/뒤=z."""
    h0, y0, h1, y1, near, far = box
    depth, hid = elevation(dim, h0, h1, y0, y1, near, far, axis)
    lut = pal.lut(dim, 1)
    rgb = lut[hid]
    span = max(1, abs(near - far))
    shade = 0.45 + 0.55 * np.clip(depth / span, 0, 1)
    rgb = rgb * shade[..., None]
    rgb[depth < 0] = BG
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8).transpose(1, 0, 2)[::-1], "RGB")
    if axis == "x":  # 서쪽을 보면 왼쪽이 남(+Z)
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    img, k = _scale(img, target)
    d = ImageDraw.Draw(img)
    for y in range((y0 // 16 + 1) * 16, y1 + 1, 16):
        py = (y1 - y + 1) * k
        d.line((0, py, img.width, py), fill=(70, 60, 90), width=1)
    look = "남쪽에서 북쪽을 봄" if axis == "z" else "동쪽에서 서쪽을 봄"
    return _frame(img, title, list(notes) + [f"{look} · 가로 {h0}~{h1}, Y {y0}~{y1} · 가로줄 16칸"])


def _grid(d, img, k, x0, z0, x1, z1):
    if k < 2:
        return
    for x in range((x0 // 16 + 1) * 16, x1 + 1, 16):
        d.line(((x - x0) * k, 0, (x - x0) * k, img.height), fill=(60, 52, 80), width=1)
    for z in range((z0 // 16 + 1) * 16, z1 + 1, 16):
        d.line((0, (z - z0) * k, img.width, (z - z0) * k), fill=(60, 52, 80), width=1)
