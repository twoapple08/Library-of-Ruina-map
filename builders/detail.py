"""가까이서도 닫힌 입체로 보이는 공용 건축 부품. 로컬 +Z가 앞면이다.

원화 투영 전의 원본 기하: 옆/뒤 재질과 실제 두께를 항상 유지한다.
"""
from __future__ import annotations

import itertools
import math

import numpy as np

from tools import forms as F


def beveled_box(lo, hi, mat, bevel=0.04):
    """6개 면·12개 깎인 모서리·8개 꼭짓점으로 닫힌 육면체 (26면).

    면마다 0..1 UV를 사용한다. 칸별 분할은 FormLayer가 맡는다.
    """
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    if np.any(hi <= lo):
        raise ValueError("부품의 세 변 길이는 양수여야 함")
    b = min(float(bevel), float((hi - lo).min()) * 0.45)
    if b <= 0:
        corners = lo + (hi-lo)*np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],
                                        [0,0,1],[1,0,1],[1,1,1],[0,1,1]])
        indices = np.array([[0,4,7,3],[5,1,2,6],[0,1,5,4],[7,6,2,3],[1,0,3,2],[4,5,6,7]])
        return F.Quads(corners[indices], np.tile([[0,0],[1,0],[1,1],[0,1]],(6,1,1)), M=mat)
    mid = (lo + hi) / 2
    half = (hi - lo) / 2
    faces = []

    def face(points):
        faces.append(points)

    for axis in range(3):
        u, v = [i for i in range(3) if i != axis]
        for sign in (-1, 1):
            pts = []
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                p = np.zeros(3)
                p[axis] = sign * half[axis]
                p[u], p[v] = su * (half[u] - b), sv * (half[v] - b)
                pts.append(p)
            face(pts)
    for run in range(3):
        u, v = [i for i in range(3) if i != run]
        for su, sv in itertools.product((-1, 1), repeat=2):
            pts = []
            for sr, lip in ((-1, 0), (1, 0), (1, 1), (-1, 1)):
                p = np.zeros(3)
                p[run] = sr * (half[run] - b)
                p[u] = su * (half[u] - (b if lip else 0))
                p[v] = sv * (half[v] - (0 if lip else b))
                pts.append(p)
            face(pts)
    for signs in itertools.product((-1, 1), repeat=3):
        corner = np.asarray(signs) * (half - b)
        pts = [corner + np.eye(3)[i] * signs[i] * b for i in range(3)]
        face([*pts, pts[-1]])
    uv = np.tile([[0, 0], [1, 0], [1, 1], [0, 1]], (26, 1, 1))
    points = np.asarray(faces, float)
    back = np.sum(F.face_normals(points)*points.mean(1), axis=1) < 0
    points[back] = points[back][:, [0,3,2,1]]
    return F.Quads(points+mid, uv, M=mat)


def casement(width, height, frame, glass, dark, depth=0.75, bar=None):
    """돌출창: 닫힌 뒷판·안으로 들어간 유리·사방 틀·깎인 창턱·독립된 창살.

    원점 = 창 중심, 앞틀 z=0, 뒷면 z=-depth. 창빛을 그림으로만 그리지 않는다.
    """
    w, h = width / 2, height / 2
    rim = min(0.20, width * 0.10, height * 0.10)
    bar = max(0.035, rim * 0.45) if bar is None else bar
    out = [beveled_box((-w-rim, -h-rim, -depth), (w+rim, h+rim, -depth+0.08), dark),
           # 유리도 두께가 있는 닫힌 부품. 네 둘레의 깊은 턱은 아래 틀로 막힌다.
           beveled_box((-w, -h, -depth+0.08), (w, h, -depth+0.13), glass, 0.012)]
    for x in (-w-rim, w):
        out.append(beveled_box((x, -h-rim, -depth), (x+rim, h+rim, 0), frame))
    for y in (-h-rim, h):
        out.append(beveled_box((-w, y, -depth), (w, y+rim, 0), frame))
    out.append(beveled_box((-w-2*rim, -h-2*rim, -depth-0.04),
                           (w+2*rim, -h-rim, rim*1.8), frame))
    count = max(1, int(width / max(height * 0.9, 1.0)))
    for x in np.linspace(-w, w, count+2)[1:-1]:
        out.append(beveled_box((x-bar/2, -h, -depth+0.1), (x+bar/2, h, -0.06), frame, 0.015))
    return F.concat(out)


def upright_book(width, height, depth, cover, pages, bevel=0.015):
    """밑면 y=0, 책등 +Z. 표지 두 장·책등·안쪽 종이 묶음을 따로 만든다."""
    w, d = width/2, depth/2
    c = min(width * 0.14, height * 0.035, depth * 0.2, 0.06)
    out = [beveled_box((-w+c, c, -d+c), (w-c, height-c, d-c), pages, bevel)]
    for x in (-w, w-c):
        out.append(beveled_box((x, 0, -d), (x+c, height, d), cover, bevel))
    out.append(beveled_box((-w, 0, d-c), (w, height, d+c*0.2), cover, bevel))
    return F.concat(out)


def flat_book(width, length, thickness, cover, pages, bevel=0.015):
    """바닥 y=0인 눕힌 책. 수평 표지 두 장·앞 책등·안쪽 종이 묶음."""
    w, l, h = width/2, length/2, thickness
    c = min(h*.14, width*.04, length*.04, .04)
    out = [beveled_box((-w+c, c, -l+c), (w-c, h-c, l-c), pages, bevel)]
    for y in (0, h-c):
        out.append(beveled_box((-w, y, -l), (w, y+c, l), cover, bevel))
    out.append(beveled_box((-w, 0, l-c), (w, h, l+c*.2), cover, bevel))
    return F.concat(out)


def column(radius, height, mat, segs=16):
    """발판·두 겹 받침·엔타시스 몸통·칼라·주두를 가진 원형 기둥."""
    r, h = radius, height
    profile = [(0, 0), (1.35*r, 0), (1.35*r, .035*h), (1.15*r, .05*h),
               (1.15*r, .09*h), (.84*r, .12*h), (.92*r, .38*h), (.76*r, .84*h),
               (.95*r, .86*h), (.95*r, .90*h), (1.25*r, .94*h), (1.3*r, h), (0, h)]
    return F.revolve(profile, mat, segs=segs, tiles_around=4, tile_up=max(h, 1))


def radial(q, theta, radius, y, center=(0, 0)):
    """로컬 +Z 앞면을 원통의 바깥쪽으로 향하게 배치 (폭 = 접선 방향)."""
    return q.rotate("y", 90 - math.degrees(theta)).translate(
        (center[0] + math.cos(theta)*radius, y, center[1] + math.sin(theta)*radius))
