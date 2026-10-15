"""원화 분석 (오프라인, 한 번만): 원화에서 형체 모양을 읽어 design/fit/ 에 저장 → 빌더가 읽음.

빌드(CI)에는 numpy·pillow 만 있으므로 무거운 분석(scipy·scikit-image)은 여기서 미리 해 두고 결과만 커밋한다.
    pip install scipy scikit-image
    python -m tools.art_fit exterior

결과 (공간마다):
- design/fit/<공간>_mask.png : 형체가 덮을 원화 영역 (흰색 = 탑·가지 등 앞 형체, 나머지 = 하늘/먼 배경)
- design/fit/<공간>.json     : trunk (줄마다 몸통 왼쪽·오른쪽 x), branches (가지 중심선: [[x, y, 반폭], ...] 픽셀)
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "design", "fit")


def _dark_mask(path, v_max=115, s_max=120, seed_xy=(500, 300), min_hole=250):
    from scipy import ndimage as ndi
    hsv = np.asarray(Image.open(path).convert("HSV"), float)
    s, v = hsv[..., 1], hsv[..., 2]
    dark = (v < v_max) & (s < s_max)
    dark = ndi.binary_closing(dark, iterations=1)
    holes = ndi.binary_fill_holes(dark) & ~dark
    hl, hn = ndi.label(holes)
    sz = ndi.sum(holes, hl, range(1, hn + 1))
    dark |= np.isin(hl, 1 + np.flatnonzero(sz < min_hole))     # 창문 같은 작은 구멍만 메움
    dark = ndi.binary_opening(dark, iterations=1)
    lab, _ = ndi.label(dark)
    return lab == lab[seed_xy[1], seed_xy[0]]


def _trace(skel):
    """뼈대 픽셀 → 갈림길에서 끊은 선들 [(y,x) 목록]."""
    H, W = skel.shape
    pts = set(zip(*np.nonzero(skel)))
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    def neigh(p):
        return [(p[0] + a, p[1] + b) for a, b in nb if (p[0] + a, p[1] + b) in pts]
    deg = {p: len(neigh(p)) for p in pts}
    nodes = {p for p in pts if deg[p] != 2}
    used = set()
    lines = []
    for n in nodes:
        for q in neigh(n):
            if (n, q) in used:
                continue
            line = [n, q]
            used.add((n, q))
            prev, cur = n, q
            while cur not in nodes:
                nx = [r for r in neigh(cur) if r != prev and r not in line[-3:]]
                if not nx:
                    break
                prev, cur = cur, nx[0]
                line.append(cur)
            used.add((cur, prev))
            lines.append(line)
    # 고리(갈림길 없는 닫힌 선)
    rest = pts - {p for l in lines for p in l}
    while rest:
        p = rest.pop()
        line = [p]
        cur = p
        while True:
            nx = [r for r in neigh(cur) if r in rest]
            if not nx:
                break
            cur = nx[0]
            rest.discard(cur)
            line.append(cur)
        lines.append(line)
    return lines


def fit_exterior():
    from scipy import ndimage as ndi
    from skimage.morphology import disk, opening, skeletonize
    path = os.path.join(ROOT, "reference", "도서관 외견.png")
    m = _dark_mask(path)
    H, W = m.shape
    # 몸통: 굵은 원판으로 열기 → 가지(폭 40px 이하)는 사라지고 몸통만
    trunk = opening(m, disk(30))
    from scipy.ndimage import label
    lab, _ = label(trunk)
    trunk = lab == lab[300, 500]
    rows = []
    for y in range(H):
        xs = np.flatnonzero(trunk[y])
        if len(xs):
            # 가운데(500) 를 포함하는 연속 구간
            seg = np.split(xs, np.flatnonzero(np.diff(xs) > 1) + 1)
            best = min(seg, key=lambda s: 0 if s[0] <= 500 <= s[-1] else min(abs(s[0] - 500), abs(s[-1] - 500)))
            rows.append([y, int(best[0]), int(best[-1])])
    br = m & ~ndi.binary_dilation(trunk, iterations=4)
    br = ndi.binary_opening(br, iterations=1)
    dist = ndi.distance_transform_edt(m)
    sk = skeletonize(br)
    lines = []
    for l in _trace(sk):
        if len(l) < 12:
            continue
        arr = np.array(l)
        w = dist[arr[:, 0], arr[:, 1]]
        sel = np.arange(0, len(arr), 2)
        if sel[-1] != len(arr) - 1:
            sel = np.r_[sel, len(arr) - 1]
        lines.append([[int(arr[i, 1]), int(arr[i, 0]), round(float(w[i]), 1)] for i in sel])
    # 창문: 몸통 안의 밝은 노란 점 덩어리 → 상자 [x0, y0, x1, y1]
    rgb = np.asarray(Image.open(path).convert("RGB"), float)
    yel = (rgb[..., 0] > 200) & (rgb[..., 1] > 150) & (rgb[..., 2] < 228) & (rgb[..., 0] - rgb[..., 2] > 30)
    near = ndi.binary_dilation(trunk, iterations=6)
    wl, wn = ndi.label(yel & near)
    windows = []
    for sl in ndi.find_objects(wl):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        if (y1 - y0) * (x1 - x0) >= 4 and y1 < 445:
            windows.append([x0, y0, x1, y1])
    # 황금 종이: 아래쪽의 밝은 노랑~흰 (원화 아래 1/4)
    paper = (rgb.sum(-1) > 480) & (rgb[..., 0] > 200) & (rgb[..., 2] < 235)
    paper[:380] = False
    paper = ndi.binary_closing(paper, iterations=3)
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray((paper * 255).astype(np.uint8)).save(os.path.join(OUT, "exterior_paper.png"))
    Image.fromarray((m * 255).astype(np.uint8)).save(os.path.join(OUT, "exterior_mask.png"))
    Image.fromarray((trunk * 255).astype(np.uint8)).save(os.path.join(OUT, "exterior_trunk.png"))
    with open(os.path.join(OUT, "exterior.json"), "w") as f:
        json.dump({"art": "reference/도서관 외견.png", "size": [W, H], "trunk": rows, "branches": lines,
                   "windows": windows}, f)
    print(f"몸통 줄 {len(rows)}, 가지 선 {len(lines)}, 창 {len(windows)}")


if __name__ == "__main__":
    {"exterior": fit_exterior}[sys.argv[1]]()
