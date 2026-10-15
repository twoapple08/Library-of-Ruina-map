"""원화에 맞춘 형체 (빌드 때, numpy 만): tools/art_fit.py 가 미리 뽑아 둔 design/fit/<공간>.json·마스크를 읽어
도착 시점 카메라(forms.Camera)에서 원화와 같은 실루엣이 되는 3D 모양을 만든다.

- ArtView: 원화 픽셀 ↔ 카메라 광선 (픽셀 → 월드 점)
- trunk_profile: 원화의 몸통 폭(줄마다) → 회전체 단면 [(반지름, 높이)]
- branch_paths: 원화 가지 중심선 → 3D 곡선 + 굵기 (화면에서는 원화 가지와 겹치고, 깊이는 매끈한 장으로 퍼뜨림)
- clean_sky: 마스크 부분(형체가 덮는 곳)을 주변 색으로 메운 원화 → 하늘 그림용 (걸어 다녀도 하늘에 가지가 안 남게)
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
from PIL import Image

from . import forms as F

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_fit(space: str) -> dict:
    with open(os.path.join(ROOT, "design", "fit", space + ".json"), encoding="utf-8") as f:
        return json.load(f)


def load_mask(space: str, name: str = "mask") -> np.ndarray:
    return np.asarray(Image.open(os.path.join(ROOT, "design", "fit", f"{space}_{name}.png")).convert("L")) > 127


class ArtView:
    """원화(W×H 픽셀)를 도착 카메라에 맞춘 것. 원화는 16:9 로 보고 화면 전체에 대응."""

    def __init__(self, cam: F.Camera, W: int, H: int):
        self.cam, self.W, self.H = cam, W, H
        self.f, self.r, self.u = cam.basis()
        self.C = np.asarray(cam.pos, float)
        self.th = math.tan(math.radians(cam.fov) / 2)

    def ray(self, px, py) -> np.ndarray:
        """픽셀 (배열 가능) → 단위 광선 (...,3)."""
        px, py = np.asarray(px, float), np.asarray(py, float)
        sx, sy = (px + 0.5) / self.W, (py + 0.5) / self.H
        v = (self.f + self.r * ((sx - 0.5) * 2 * self.th * self.cam.aspect)[..., None]
             + self.u * ((0.5 - sy) * 2 * self.th)[..., None])
        return v / np.linalg.norm(v, axis=-1, keepdims=True)

    def on_plane_z(self, px, py, z: float) -> np.ndarray:
        v = self.ray(px, py)
        t = (z - self.C[2]) / v[..., 2]
        return self.C + t[..., None] * v

    def at_z(self, px, py, z) -> np.ndarray:
        """광선 위에서 월드 z 가 z 인 점 (z 배열 가능)."""
        v = self.ray(px, py)
        t = (np.asarray(z, float) - self.C[2]) / v[..., 2]
        return self.C + t[..., None] * v

    def px_size(self, P) -> np.ndarray:
        """월드 점 P 에서 원화 1픽셀의 월드 크기."""
        z = (np.asarray(P, float) - self.C) @ self.f
        return z * 2 * self.th / self.H


def trunk_profile(view: ArtView, rows, axis=(0.0, 0.0), smooth: int = 15) -> np.ndarray:
    """원화 줄마다 몸통 왼쪽·오른쪽 x → (높이, 반지름) 배열 (높이 오름차순, 튀는 값은 이웃 중간값으로)."""
    out = []
    ax, az = axis
    for y, xl, xr in rows:
        pc = view.on_plane_z((xl + xr) / 2, y, az)
        pl = view.on_plane_z(xl, y, az)
        prr = view.on_plane_z(xr, y, az)
        half = abs(prr[0] - pl[0]) / 2
        dist = math.hypot(pc[0] - view.C[0], pc[2] - view.C[2])
        out.append((pc[1], dist * math.sin(math.atan(half / dist))))
    a = np.array(sorted(out))
    r = a[:, 1].copy()
    k = smooth
    med = np.array([np.median(r[max(0, i - k):i + k + 1]) for i in range(len(r))])
    return np.stack([a[:, 0], med], 1)


def _smooth_noise(x, y, scale, seed):
    """픽셀 평면의 매끈한 잡음 -1~1 (사인 몇 개 합, 결정적)."""
    rng = np.random.default_rng(seed)
    v = np.zeros_like(np.asarray(x, float))
    tot = 0.0
    for k in range(5):
        a = rng.uniform(0, 2 * math.pi)
        fr = (1.0 + k * 0.7) / scale
        ph = rng.uniform(0, 2 * math.pi)
        w = 1.0 / (1 + k)
        v = v + w * np.sin((np.cos(a) * x + np.sin(a) * y) * fr * 2 * math.pi + ph)
        tot += w
    return v / tot


def branch_paths(view: ArtView, lines, radius_at, depth_amp=0.55, seed=3, ymax_px=None, min_len=10,
                 attach_px=8.0, trunk_edge=None):
    """원화 가지 중심선 → [(점 (n,3), 반지름 (n,))].
    깊이: 축(0,0)에서의 가로 거리 × depth_amp × 매끈한 잡음 (가지마다 앞뒤로 퍼짐, 갈림길에서 이어짐).
    radius_at(y) = 그 높이 몸통 반지름. trunk_edge(y_px) = (왼, 오른) 몸통 가장자리 픽셀 → 가까운 끝은 몸통 속까지 늘림."""
    out = []
    for line in lines:
        L = np.asarray(line, float)
        if ymax_px is not None:
            L = L[L[:, 1] <= ymax_px]
        if len(L) < min_len // 2:
            continue
        px, py, w = L[:, 0], L[:, 1], L[:, 2]
        # 1) 축 평면(z=0)에서의 위치로 가로 거리
        P0 = view.on_plane_z(px, py, 0.0)
        lat = np.abs(P0[:, 0])
        n = _smooth_noise(px, py, 260.0, seed)
        z = lat * depth_amp * n
        # 몸통 반지름 안으로 들어가지 않게: 가로 거리가 반지름보다 작으면 앞쪽(카메라 쪽)으로 밀어냄
        rr = np.array([radius_at(yy) for yy in P0[:, 1]]) + 2.0
        inside = lat < rr
        z = np.where(inside, np.maximum(z, np.sqrt(np.maximum(rr ** 2 - lat ** 2, 0)) + 1.0), z)
        P = view.at_z(px, py, z)
        rad = np.maximum(w * view.px_size(P) * 0.92, 0.6)
        # 몸통 쪽 끝은 몸통 표면 안까지 이어 붙임
        if trunk_edge is not None:
            for end in (0, -1):
                yp = py[end]
                e = trunk_edge(yp)
                if e is None:
                    continue
                if min(abs(px[end] - e[0]), abs(px[end] - e[1])) <= attach_px:
                    q = P[end].copy()
                    rq = radius_at(q[1])
                    d = math.hypot(q[0], q[2])
                    inner = q * np.array([1, 1, 1.0])
                    inner[[0, 2]] = q[[0, 2]] / max(d, 1e-6) * (rq - 3.0)
                    if end == 0:
                        P = np.vstack([inner, P])
                        rad = np.r_[rad[0] * 1.15, rad]
                    else:
                        P = np.vstack([P, inner])
                        rad = np.r_[rad, rad[-1] * 1.15]
        if len(P) >= 2:
            out.append((P, rad))
    return out


def clean_sky(art_path: str, mask: np.ndarray, size=(1024, 576), grow: int = 3) -> Image.Image:
    """마스크(True = 형체가 덮는 곳)를 주변 색으로 메운 원화 (밀어 올리기·내리기 피라미드, 부드럽게)."""
    im = Image.open(os.path.join(ROOT, art_path)).convert("RGB")
    m = Image.fromarray((mask * 255).astype(np.uint8)).resize(im.size)
    m = np.asarray(m) > 127
    if grow:
        from PIL import ImageFilter
        m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(grow * 2 + 1))) > 127
    img = np.asarray(im, float)
    wgt = (~m).astype(float)
    levels = []
    c, w = img * wgt[..., None], wgt
    while min(c.shape[:2]) > 4:
        levels.append((c, w))
        h2, w2 = c.shape[0] // 2, c.shape[1] // 2
        c = c[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2, 3).sum((1, 3))
        w = w[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2).sum((1, 3))
    fill = c / np.maximum(w, 1e-6)[..., None]
    for c, w in reversed(levels):
        up = np.asarray(Image.fromarray(np.clip(fill, 0, 255).astype(np.uint8)).resize((c.shape[1], c.shape[0]),
                                                                                         Image.BILINEAR), float)
        own = c / np.maximum(w, 1e-6)[..., None]
        a = np.clip(w, 0, 1)[..., None]
        fill = own * a + up * (1 - a)
    out = np.where(m[..., None], fill, img)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def sky_panorama(cam: F.Camera, clean: Image.Image, W: int = 4096, H: int = 1536, e_lo: float = -30.0,
                 e_hi: float = 90.0, gradient=None, zenith=(46, 22, 86), below=(22, 14, 34), city=None,
                 cloud_e=(54.0, 62.0), feather: float = 0.08, seed: int = 5) -> Image.Image:
    """하늘 전체 그림 (방위 0~360 × 고도 e_lo~e_hi, 방위 0 = 카메라 정면).
    정면 시야 안 = 메운 원화 (가장자리 feather 비율로 섞음), 밖 = 절차 그림: 고도별 색(gradient [(고도, (r,g,b))]),
    구름 고리(cloud_e), 별, 도시 실루엣(city = dict(최대 고도, 색...) 또는 None)."""
    rng = np.random.default_rng(seed)
    az = (np.arange(W) + 0.5) / W * 2 * math.pi
    eld = e_hi - (np.arange(H) + 0.5) / H * (e_hi - e_lo)
    # ---------------------------------------------- 하늘 색 (고도별)
    g = sorted(gradient or [(-5, below), (0, (60, 40, 80)), (67.5, (58, 32, 85)), (90, zenith)])
    ge = np.array([a for a, _ in g])
    gc = np.array([c for _, c in g], float)
    sky = np.stack([np.interp(eld, ge, gc[:, k]) for k in range(3)], 1)[:, None, :].repeat(W, 1)
    A, Ed = np.meshgrid(az, eld)
    # 구름 고리: 고도 cloud_e 근처 밝은 띠 + 잡음
    from PIL import ImageFilter
    nz = rng.random((H // 8 + 1, W // 8 + 1))
    nz = np.asarray(Image.fromarray((nz * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
                    .filter(ImageFilter.GaussianBlur(6)), float) / 255
    c0, c1 = cloud_e
    band = np.clip(1 - np.abs(Ed - (c0 + c1) / 2) / ((c1 - c0) / 2 + 1e-6), 0, 1) ** 1.5
    cl = band * np.clip(nz * 1.6 - 0.25, 0, 1)
    sky = sky * (1 - cl[..., None] * 0.6) + np.array([150, 130, 190.0]) * cl[..., None] * 0.6
    # 별
    n = W * H // 2500
    sx, sy = rng.integers(0, W, n), rng.integers(0, H, n)
    up = eld[sy] > 45
    sky[sy[up], sx[up]] = np.minimum(255, sky[sy[up], sx[up]] + rng.uniform(70, 170, (up.sum(), 1)))
    out = sky
    # ---------------------------------------------- 도시 실루엣 (두 겹: 먼 겹은 흐리게)
    if city:
        px_deg = W / 360.0
        py_deg = H / (e_hi - e_lo)
        ey = lambda e: int((e_hi - e) * py_deg)
        for layer, (hmin, hmax, haze) in enumerate(((6, city.get("far", 24), 0.55), (3, city.get("near", 34), 0.0))):
            x = 0
            while x < W:
                w = int(rng.uniform(1.2, 3.6) * px_deg)
                h = rng.uniform(hmin, hmax) * (0.55 + 0.45 * rng.random())
                top = ey(h)
                bot = ey(-1)
                if rng.random() < 0.85:
                    tone = rng.uniform(0.7, 1.15)
                    body = np.linspace(0, 1, max(bot - top, 1))[:, None]
                    base = (np.asarray(city.get("dark", (34, 24, 58)), float) * (1 - body)
                            + np.asarray(city.get("glow", (150, 70, 150)), float) * body ** 3) * tone
                    rim = np.asarray(city.get("rim", (90, 150, 190)), float)
                    blk = base[:, None, :].repeat(w, 1).copy()
                    blk[:, :2] = blk[:, :2] * 0.5 + rim * 0.5
                    # 창: 격자, 일부만 켜짐
                    wy, wx = max(2, int(0.55 * py_deg)), max(2, int(0.45 * px_deg))
                    lit = np.asarray(rng.choice([(255, 220, 160), (255, 160, 220), (170, 230, 255)]), float)
                    ratio = rng.uniform(0.15, 0.55)
                    for yy in range(3, blk.shape[0] - 3, wy * 2):
                        for xx in range(3, w - 2, wx * 2):
                            if rng.random() < ratio:
                                blk[yy:yy + wy, xx:xx + wx] = lit * rng.uniform(0.7, 1.0)
                    xe = min(W, x + w)
                    blk = blk[:bot - top, :xe - x]
                    if haze:
                        blk = blk * (1 - haze) + out[top:bot, x:xe] * haze
                    out[top:bot, x:xe] = blk
                x += w + int(rng.uniform(0, 0.6) * px_deg)
        # 지평선 아래: 황금 종이 빛 띠 → 어둠
        gl = np.clip(1 - np.abs(Ed - 0.5) / 2.0, 0, 1)[..., None]
        out = out * (1 - gl) + np.array([250, 225, 150.0]) * gl
    dark = np.clip((-Ed - 1.5) / 6, 0, 1)[..., None]
    out = out * (1 - dark) + np.asarray(below, float) * dark
    # ---------------------------------------------- 정면: 원화
    art = np.asarray(clean.convert("RGB"), float)
    ah, aw = art.shape[:2]
    f0, r0, _ = cam.basis()
    fwd = np.array([f0[0], 0, f0[2]]) / np.hypot(f0[0], f0[2])
    right = np.array([r0[0], 0, r0[2]]) / np.hypot(r0[0], r0[2])
    E = np.radians(Ed)
    D = (np.cos(E)[..., None] * (np.cos(A)[..., None] * fwd + np.sin(A)[..., None] * right)
         + np.sin(E)[..., None] * np.array([0, 1.0, 0]))
    sxa, sya, z = cam.project(np.asarray(cam.pos) + D * 100)
    ok = (z > 0) & (sxa >= 0) & (sxa < 1) & (sya >= 0) & (sya < 1)
    xi = np.clip((sxa * aw).astype(int), 0, aw - 1)
    yi = np.clip((sya * ah).astype(int), 0, ah - 1)
    edge = np.minimum(np.minimum(sxa, 1 - sxa), np.minimum(sya, 1 - sya) * 1.6)
    wgt = np.where(ok, np.clip(edge / feather, 0, 1), 0)[..., None]
    wgt = np.where((sya > 0.85)[..., None], np.minimum(wgt, 1.0), wgt)
    out = out * (1 - wgt) + art[yi, xi] * wgt
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def sky_dome(tiles: list[list[int]], radius: float = 100.0, e_lo: float = -30.0, e_hi: float = 90.0, yaw: float = 180.0,
             per_tile: int = 8, below_mat: int | None = None) -> F.Quads:
    """sky_panorama 타일 재질들 [[행][열]] → 카메라 중심 구 (안쪽이 앞). yaw = 파노라마 방위 0 의 마인크래프트 yaw."""
    rows, cols = len(tiles), len(tiles[0])
    na, ne = cols * per_tile, rows * per_tile
    parts = []
    y0 = math.radians(yaw)
    fwd = np.array([-math.sin(y0), 0, math.cos(y0)])
    right = np.cross(fwd, [0, 1, 0])
    right /= np.linalg.norm(right)
    for r in range(rows):
        for c in range(cols):
            a = np.linspace(c, c + 1, per_tile + 1) / cols * 2 * math.pi
            e = np.radians(e_hi - np.linspace(r, r + 1, per_tile + 1) / rows * (e_hi - e_lo))
            Ag, Eg = np.meshgrid(a, e, indexing="ij")
            D = (np.cos(Eg)[..., None] * (np.cos(Ag)[..., None] * fwd + np.sin(Ag)[..., None] * right)
                 + np.sin(Eg)[..., None] * np.array([0, 1.0, 0]))
            u = (Ag / (2 * math.pi) * cols - c)
            v = (e_hi - np.degrees(Eg)) / (e_hi - e_lo) * rows - r
            UV = np.stack([np.clip(u, 0, 1) * 0.999 + 0.0005, np.clip(v, 0, 1) * 0.999 + 0.0005], -1)
            parts.append(F.grid(D * radius, UV, tiles[r][c], N=-D))
    if below_mat is not None:
        a = np.linspace(0, 2 * math.pi, na + 1)
        e = np.radians(np.linspace(e_lo, -90, 7))
        Ag, Eg = np.meshgrid(a, e, indexing="ij")
        D = (np.cos(Eg)[..., None] * (np.cos(Ag)[..., None] * fwd + np.sin(Ag)[..., None] * right)
             + np.sin(Eg)[..., None] * np.array([0, 1.0, 0]))
        parts.append(F.grid(D * radius, np.full(D.shape[:2] + (2,), 0.5), below_mat, N=-D))
    return F.concat(parts)


def circle_mask(size, circles, grow=1.15):
    """원화 크기 (W, H) 에 원들 [(x, y, r)] 을 칠한 마스크 (움직이는 형체가 대신할 부분 지우기용)."""
    W, H = size
    y, x = np.mgrid[0:H, 0:W]
    m = np.zeros((H, W), bool)
    for cx, cy, r in circles:
        m |= (x - cx) ** 2 + (y - cy) ** 2 <= (r * grow) ** 2
    return m


def box_mask(size, boxes):
    W, H = size
    m = np.zeros((H, W), bool)
    for x0, y0, x1, y1 in boxes:
        m[max(0, y0):y1, max(0, x0):x1] = True
    return m
