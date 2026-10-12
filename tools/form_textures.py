"""자유 형체용 텍스처 (절차 생성 + 원화). 모두 forms.texture 로 등록 → assets/ruina/textures/block/form/.

크기는 16의 배수 (블록 아틀라스 밉맵 단계를 낮추지 않게). 원화는 1024×576 (16:9) 기본.
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageFilter

from . import forms

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _noise(h, w, scale, seed, octaves=4):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(1, int(scale / 2 ** o))
        g = rng.random((h // s + 2, w // s + 2))
        img = Image.fromarray((g * 255).astype(np.uint8)).resize(((w // s + 2) * s, (h // s + 2) * s), Image.BICUBIC)
        out += amp * np.asarray(img, float)[:h, :w] / 255
        tot += amp
        amp *= 0.5
    return out / tot


def _img(rgb: np.ndarray, a: np.ndarray | None = None) -> Image.Image:
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    if a is None:
        return Image.fromarray(rgb, "RGB").convert("RGBA")
    return Image.fromarray(np.dstack([rgb, np.clip(a, 0, 255).astype(np.uint8)]), "RGBA")


def _mix(c0, c1, t):
    return np.asarray(c0, float) * (1 - t[..., None]) + np.asarray(c1, float) * t[..., None]


def bark(name="bark", c0=(38, 36, 44), c1=(78, 74, 90), size=64, seed=1) -> str:
    """세로 결 나무껍질 (탑 판자·가지)."""
    h = w = size
    streak = _noise(h * 4, w, 8, seed, 3)[::4]
    streak = np.asarray(Image.fromarray((streak * 255).astype(np.uint8)).resize((w, h)), float) / 255
    fine = _noise(h, w, 4, seed + 1, 2)
    t = np.clip(streak * 0.7 + fine * 0.5 - 0.1, 0, 1)
    return forms.texture(name, _img(_mix(c0, c1, t)))


def planks(name="planks", c0=(40, 40, 50), c1=(84, 82, 98), boards=4, size=64, seed=2) -> str:
    """세로 판자 (경계 홈 + 결)."""
    h = w = size
    rng = np.random.default_rng(seed)
    base = _noise(h, w, 6, seed, 3)
    x = np.arange(w)[None, :].repeat(h, 0)
    bw = w // boards
    tone = rng.uniform(-0.15, 0.15, boards)[np.minimum(x // bw, boards - 1)]
    groove = ((x % bw) == 0) | ((x % bw) == bw - 1)
    t = np.clip(base * 0.6 + 0.25 + tone, 0, 1)
    t[groove] *= 0.35
    return forms.texture(name, _img(_mix(c0, c1, t)))


def paper(name="paper", c=(236, 226, 196), lines=True, size=32, seed=3, alpha=True) -> str:
    """종이 한 장 (가장자리 약간 투명·누런 얼룩, 글줄)."""
    h = w = size
    n = _noise(h, w, 4, seed, 2)
    rgb = np.asarray(c, float)[None, None] * (0.88 + 0.12 * n[..., None])
    if lines:
        for y in range(h // 6, h - h // 8, max(2, h // 8)):
            rgb[y, w // 8: w - w // 8] *= 0.72
    a = np.full((h, w), 255.0)
    if alpha:
        a[[0, -1], :] = 0
        a[:, [0, -1]] = 0
    return forms.texture(name, _img(rgb, a))


def book_spines(name="book_spines", palette=None, size=64, seed=4) -> str:
    """책등 줄 (책장 벽·책 더미). 한 장 = 책 여러 권."""
    palette = palette or [(92, 46, 38), (58, 66, 92), (110, 92, 54), (60, 82, 62), (130, 112, 86), (72, 52, 76)]
    h = w = size
    rng = np.random.default_rng(seed)
    rgb = np.zeros((h, w, 3))
    x = 0
    while x < w:
        bw = int(rng.integers(3, 8))
        c = np.asarray(palette[int(rng.integers(len(palette)))], float) * rng.uniform(0.75, 1.15)
        top = int(rng.integers(0, h // 6))
        rgb[top:, x:x + bw] = c
        rgb[:top, x:x + bw] = (20, 16, 18)
        band = int(rng.integers(h // 5, h // 2))
        rgb[band:band + 2, x:x + bw] *= 1.5                  # 금박 띠
        rgb[top:, x:x + 1] *= 0.6
        x += bw
    rgb *= (0.85 + 0.15 * _noise(h, w, 4, seed, 2))[..., None]
    return forms.texture(name, _img(rgb))


def stone_slab(name="stone_slab", c0=(96, 94, 100), c1=(150, 146, 150), size=64, seed=5) -> str:
    """잿빛 돌판 (줄눈 + 얼룩)."""
    h = w = size
    n = _noise(h, w, 16, seed, 4)
    rgb = _mix(c0, c1, n)
    rgb[[0, h // 2], :] *= 0.6
    rgb[:h // 2, [0]] *= 0.6
    rgb[h // 2:, [w // 2]] *= 0.6
    return forms.texture(name, _img(rgb))


def metal(name="metal", c0=(70, 58, 40), c1=(176, 148, 96), size=32, seed=6) -> str:
    """닳은 금속 (톱니·시계 바늘)."""
    h = w = size
    n = _noise(h, w, 4, seed, 3)
    return forms.texture(name, _img(_mix(c0, c1, n)))


def glow(name="glow", c=(255, 214, 140), size=16) -> str:
    """빛나는 면 (가운데가 밝은 단색)."""
    y, x = np.mgrid[0:size, 0:size] / (size - 1) - 0.5
    t = 1 - np.clip(np.hypot(x, y) * 0.9, 0, 1) * 0.35
    return forms.texture(name, _img(np.asarray(c, float)[None, None] * t[..., None]))


def flat(name, c, size=16) -> str:
    return forms.texture(name, _img(np.broadcast_to(np.asarray(c, float), (size, size, 3)).copy()))


def art(name: str, path: str, size=(1024, 576), crop=None) -> str:
    """원화 → 텍스처 (16:9 로 맞춰 자름). crop = (왼, 위, 오른, 아래) 비율 0~1."""
    im = Image.open(os.path.join(ROOT, path)).convert("RGB")
    W, H = im.size
    if crop:
        im = im.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
        W, H = im.size
    want = size[0] / size[1]
    if W / H > want:
        nw = int(H * want)
        im = im.crop(((W - nw) // 2, 0, (W - nw) // 2 + nw, H))
    else:
        nh = int(W / want)
        im = im.crop((0, (H - nh) // 2, W, (H - nh) // 2 + nh))
    im = im.resize(size, Image.LANCZOS).filter(ImageFilter.UnsharpMask(1, 40, 2))
    return forms.texture(name, im.convert("RGBA"))
