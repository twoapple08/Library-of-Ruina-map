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


def art(name: str, path: str, size=(1024, 576), crop=None, img=None) -> str:
    """원화 → 텍스처 (16:9 로 맞춰 자름). crop = (왼, 위, 오른, 아래) 비율 0~1. img: 미리 손본 원화 (PIL)."""
    im = (img if img is not None else Image.open(os.path.join(ROOT, path))).convert("RGB")
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


def board(name="board", c0=(30, 31, 40), c1=(72, 72, 88), w=16, h=64, seed=7, seams=2) -> str:
    """세로 판자 한 장 (결 + 어두운 가장자리 + 가로 이음매·못). 탑 몸통 패치워크."""
    rng = np.random.default_rng(seed)
    grain = _noise(h * 4, w, 3, seed, 3)[::4]
    grain = np.asarray(Image.fromarray((grain * 255).astype(np.uint8)).resize((w, h)), float) / 255
    fine = _noise(h, w, 2, seed + 1, 2)
    t = np.clip(grain * 0.65 + fine * 0.45 - 0.05, 0, 1)
    rgb = _mix(c0, c1, t)
    rgb[:, 0] *= 0.45
    rgb[:, -1] *= 0.6
    rgb[:, 1] *= 0.85
    for _ in range(seams):
        y = int(rng.integers(4, h - 4))
        rgb[y] *= 0.5
        rgb[y + 1] *= 1.12
        rgb[y - 2:y, w // 2] = np.asarray(c1, float) * 1.25          # 못
    return forms.texture(name, _img(rgb))


def paper_pile(name="paper_pile", size=64, seed=8) -> str:
    """빛나는 황금 종이 더미 (겹친 종이 장, 밝은 가장자리)."""
    rng = np.random.default_rng(seed)
    h = w = size
    rgb = np.zeros((h, w, 3)) + np.asarray((200, 150, 60), float)
    for _ in range(70):
        cx, cy = rng.integers(0, w), rng.integers(0, h)
        pw, ph = rng.integers(6, 14), rng.integers(4, 10)
        c = np.asarray(rng.choice([(255, 236, 170), (255, 222, 130), (250, 245, 215), (240, 196, 96)]), float)
        c = c * rng.uniform(0.85, 1.05)
        ys = (np.arange(cy, cy + ph) % h)[:, None]
        xs = (np.arange(cx, cx + pw) % w)[None, :]
        rgb[ys, xs] = c
        rgb[ys[-1], xs] = c * 0.62                                   # 아래 그림자 한 줄
    rgb *= (0.9 + 0.1 * _noise(h, w, 4, seed, 2))[..., None]
    return forms.texture(name, _img(rgb))


def window_lit(name="window_lit", w=16, h=16, c=(255, 214, 140), frame=(60, 44, 30), bars=True) -> str:
    """불 켜진 창 (가는 창살)."""
    y, x = np.mgrid[0:h, 0:w] / max(h - 1, 1)
    t = 1 - 0.28 * np.hypot(x - 0.5, (y - 0.5) * w / h)
    rgb = np.asarray(c, float)[None, None] * t[..., None]
    rgb[[0, -1], :] = frame
    rgb[:, [0, -1]] = frame
    if bars:
        rgb[:, w // 2] = np.asarray(frame) * 1.5
    return forms.texture(name, _img(rgb))


def panorama(name, img, size) -> list[list[str]]:
    """큰 그림을 타일(스프라이트)로 잘라 등록 → [[이름 (행, 열)]] (위 행부터). size = 타일 한 변."""
    W, H = img.size
    out = []
    for r in range(H // size):
        row = []
        for c in range(W // size):
            row.append(forms.texture(f"{name}_{r}_{c}", img.crop((c * size, r * size, (c + 1) * size, (r + 1) * size))
                                     .convert("RGBA")))
        out.append(row)
    return out


def shelf(name="shelf", palette=None, wood=(58, 34, 22), size=64, seed=12, dark_back=(18, 10, 8)) -> str:
    """책장 한 칸 (위 판자 + 책 줄, 책 사이 빈 곳은 어두운 뒤판). 1장 = 폭 1 × 높이 1 블록 기준."""
    palette = palette or [(110, 52, 34), (86, 40, 28), (132, 84, 50), (70, 46, 34), (150, 110, 70), (96, 66, 40),
                          (60, 36, 30)]
    h = w = size
    rng = np.random.default_rng(seed)
    rgb = np.zeros((h, w, 3)) + np.asarray(dark_back, float)
    board = h // 8
    x = 0
    while x < w:
        bw = int(rng.integers(3, 7))
        if rng.random() < 0.08:
            x += bw
            continue
        c = np.asarray(palette[int(rng.integers(len(palette)))], float) * rng.uniform(0.75, 1.15)
        top = board + int(rng.integers(2, h // 4))
        lean = rng.random() < 0.1
        rgb[top:, x:x + bw] = c
        rgb[top:, x:x + 1] *= 0.55
        band = int(rng.integers(top + 3, h - 6))
        rgb[band:band + 2, x:x + bw] = np.minimum(255, c * 1.7)       # 금박 띠
        if lean:
            rgb[top:top + 4, x:x + bw] *= 0.7
        x += bw
    rgb *= (0.85 + 0.15 * _noise(h, w, 4, seed, 2))[..., None]
    rgb[:board] = np.asarray(wood, float) * (0.9 + 0.2 * _noise(board, w, 4, seed + 1, 2))[..., None]
    rgb[board - 1] = np.asarray(wood, float) * 0.5
    rgb[-1] = np.asarray(wood, float) * 0.6
    return forms.texture(name, _img(rgb))


def wood(name="wood", c0=(40, 22, 14), c1=(96, 56, 34), size=64, seed=13, grain=True) -> str:
    """결 있는 나무 (기둥·들보·책상). 세로 결."""
    h = w = size
    g = _noise(h * 4, w, 3, seed, 3)[::4]
    g = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h)), float) / 255
    t = np.clip(g * 0.7 + _noise(h, w, 2, seed + 1, 2) * 0.4 - 0.05, 0, 1) if grain else _noise(h, w, 8, seed, 3)
    return forms.texture(name, _img(_mix(c0, c1, t)))


def herringbone(name="herringbone", c0=(70, 44, 26), c1=(150, 100, 60), size=64, brick=(16, 4), seed=14) -> str:
    """헤링본 나무 바닥 (한 장 = 2×2 블록 권장). 판자 = brick (길이, 폭) 픽셀, 대각선 띠마다 방향이 바뀜."""
    h = w = size
    L, W = brick
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w]
    u = (x + y) // W                     # 대각선 띠
    horiz = (u % 2) == 0
    k = np.where(horiz, (x - y // W * W) // L, (y - x // W * W) // L)
    tone = rng.uniform(0.75, 1.15, 4096)[(k * 31 + u * 7) % 4096]
    t = np.clip(_noise(h, w, 4, seed, 2) * 0.5 + 0.35, 0, 1) * tone
    rgb = _mix(c0, c1, np.clip(t, 0, 1))
    edge = (((x + y) % W) == 0) | np.where(horiz, ((x - y // W * W) % L) == 0, ((y - x // W * W) % L) == 0)
    rgb[edge] *= 0.45
    return forms.texture(name, _img(rgb))


def asphalt(name="asphalt", size=64, seed=15, lines=True) -> str:
    """아스팔트 (한 장 = 4×4 블록): 거친 회색 + 얼룩."""
    h = w = size
    n = _noise(h, w, 3, seed, 4)
    rgb = _mix((38, 38, 44), (84, 82, 90), n)
    rng = np.random.default_rng(seed)
    for _ in range(40):
        y, x = rng.integers(0, h), rng.integers(0, w)
        rgb[y, x] = rgb[y, x] * 1.4
    return forms.texture(name, _img(rgb))


def neon_facade(name, base=(30, 24, 48), lit=((255, 120, 220), (120, 220, 255), (255, 200, 120)), size=64,
                seed=16, ratio=0.4, edge=(200, 90, 255)) -> str:
    """네온 빌딩 벽 (한 장 = 8×8 블록): 어두운 벽 + 창 격자 (일부 불 켜짐) + 위 가장자리 네온 줄."""
    h = w = size
    rng = np.random.default_rng(seed)
    rgb = np.zeros((h, w, 3)) + np.asarray(base, float)
    rgb *= (0.85 + 0.25 * _noise(h, w, 8, seed, 2))[..., None]
    for y in range(3, h - 2, 8):
        for x in range(2, w - 2, 6):
            c = np.asarray(lit[int(rng.integers(len(lit)))], float)
            if rng.random() < ratio:
                rgb[y:y + 4, x:x + 4] = c * rng.uniform(0.7, 1.0)
            else:
                rgb[y:y + 4, x:x + 4] = np.asarray(base, float) * 0.5
    rgb[0:2] = edge
    return forms.texture(name, _img(rgb))


def rust(name="rust", c0=(70, 40, 26), c1=(150, 92, 56), size=64, seed=17, rivets=True) -> str:
    """녹슨 리벳 철판."""
    h = w = size
    n = _noise(h, w, 6, seed, 4)
    rgb = _mix(c0, c1, n)
    rgb *= (0.8 + 0.3 * _noise(h, w, 2, seed + 1, 2))[..., None]
    if rivets:
        for y in range(4, h, 16):
            rgb[y:y + 1] *= 0.6
            for x in range(4, w, 8):
                rgb[y + 2:y + 4, x:x + 2] = np.asarray(c1, float) * 1.3
    return forms.texture(name, _img(rgb))


def steel_plates(name="steel_plates", size=64, seed=18) -> str:
    """강철판 바닥 (한 장 = 4×4 블록): 크기 다른 판 + 이음새 홈 + 긁힘."""
    h = w = size
    rng = np.random.default_rng(seed)
    rgb = _mix((70, 64, 66), (120, 112, 112), _noise(h, w, 6, seed, 3))
    for _ in range(9):
        x0, y0 = rng.integers(0, w), rng.integers(0, h)
        x1, y1 = min(w, x0 + rng.integers(12, 40)), min(h, y0 + rng.integers(8, 30))
        rgb[y0:y1, x0:x1] *= rng.uniform(0.85, 1.12)
        rgb[y0, x0:x1] *= 0.5
        rgb[y0:y1, x0] *= 0.5
    rgb[0] *= 0.45
    rgb[:, 0] *= 0.45
    return forms.texture(name, _img(rgb))


def molten(name="molten", size=64, seed=19) -> str:
    """쇳물 (밝은 노랑~주황 흐름 무늬)."""
    h = w = size
    n = _noise(h, w, 8, seed, 4)
    t = np.clip(n * 1.4 - 0.2, 0, 1)
    rgb = _mix((255, 120, 20), (255, 240, 150), t)
    return forms.texture(name, _img(rgb))


def clock_face(name="clock_face", size=256, seed=20, c0=(196, 196, 196), c1=(240, 240, 240), ink=(40, 40, 44)) -> str:
    """시계 판 (흑백 스케치 느낌): 밝은 판 + 테 + 60 눈금 + 12 굵은 눈금 + 안쪽 동심원·방사 선. 바늘은 따로 (움직임)."""
    h = w = size
    y, x = (np.mgrid[0:h, 0:w] - (size - 1) / 2) / (size / 2)
    r = np.hypot(x, y)
    a = np.arctan2(y, x)
    t = np.clip(_noise(h, w, 12, seed, 3), 0, 1)
    rgb = _mix(c0, c1, t)
    inkc = np.asarray(ink, float)
    rim = (r > 0.93) & (r <= 1.0)
    rgb[rim] = inkc * 1.6
    for rr in (0.86, 0.55, 0.3):
        rgb[np.abs(r - rr) < 0.008] = inkc * 2.5
    tick = (np.abs(((a / (2 * np.pi) * 60) % 1.0) - 0.5) > 0.46) & (r > 0.86) & (r < 0.93)
    rgb[tick] = inkc
    big = (np.abs(((a / (2 * np.pi) * 12) % 1.0) - 0.5) > 0.475) & (r > 0.68) & (r < 0.93)
    rgb[big] = inkc * 0.8
    spoke = (np.abs(((a / (2 * np.pi) * 24) % 1.0) - 0.5) > 0.49) & (r > 0.3) & (r < 0.55)
    rgb[spoke] = inkc * 3.0
    alpha = np.where(r <= 1.0, 255, 0)
    return forms.texture(name, _img(rgb, alpha))


def book_stack(name="book_stack", palette=None, size=64, seed=21, page=(206, 198, 180)) -> str:
    """눕혀 쌓은 책 더미 옆면 (층층이 두께가 다른 책, 책등·책배(종이 결) 번갈아, 어긋난 끝). 1장 = 1 × 1 블록."""
    palette = palette or [(70, 66, 64), (96, 90, 84), (54, 50, 50), (120, 112, 100), (84, 70, 58), (40, 38, 40)]
    h = w = size
    rng = np.random.default_rng(seed)
    rgb = np.zeros((h, w, 3)) + 24.0
    y = 0
    while y < h:
        bh = min(int(rng.integers(3, 7)), h - y)
        x = int(rng.integers(-8, 0))
        while x < w:
            bw = int(rng.integers(10, 26))
            x0, x1 = max(0, x), min(w, x + bw - 1)
            if rng.random() < 0.4:                                   # 책배: 종이 결
                c = np.asarray(page, float) * rng.uniform(0.7, 1.05)
                rgb[y:y + bh, x0:x1] = c
                rgb[y + 1:y + bh - 1:2, x0:x1] *= 0.86
            else:
                c = np.asarray(palette[int(rng.integers(len(palette)))], float) * rng.uniform(0.8, 1.2)
                rgb[y:y + bh, x0:x1] = c
                if rng.random() < 0.5:
                    rgb[y + bh // 2, x0:x1] = np.minimum(255, c * 1.5)    # 금박 줄
            rgb[y + bh - 1, x0:x1] *= 0.55
            x += bw
        y += bh
    rgb *= (0.88 + 0.12 * _noise(h, w, 4, seed, 2))[..., None]
    return forms.texture(name, _img(rgb))
