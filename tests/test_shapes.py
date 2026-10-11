import os
import sys
import unittest
from collections import deque

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import shapes as S  # noqa: E402
from tools.world import AIR, Dimension  # noqa: E402


def dense(dim, lo, hi):
    """dim → [x,y,z] 블록 상태 문자열 배열."""
    X, Y, Z = (hi[i] - lo[i] + 1 for i in range(3))
    out = np.full((X, Y, Z), AIR, dtype=object)
    for x in range(X):
        for y in range(Y):
            for z in range(Z):
                out[x, y, z] = dim.get(lo[0] + x, lo[1] + y, lo[2] + z)
    return out


def outside_reachable(solid):
    """격자 바깥에서 6방향으로 닿는 빈칸."""
    X, Y, Z = solid.shape
    seen = np.zeros_like(solid)
    q = deque()
    for idx in np.argwhere(~solid):
        if 0 in idx or idx[0] == X - 1 or idx[1] == Y - 1 or idx[2] == Z - 1:
            seen[tuple(idx)] = True
            q.append(tuple(idx))
    while q:
        x, y, z = q.popleft()
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = (x + dx, y + dy, z + dz)
            if all(0 <= n[i] < solid.shape[i] for i in range(3)) and not seen[n] and not solid[n]:
                seen[n] = True
                q.append(n)
    return seen


class ShapeTest(unittest.TestCase):
    def test_hash_noise(self):
        a = S.hash01(np.arange(1000), np.zeros(1000, int), seed=3)
        self.assertTrue(0 <= a.min() and a.max() < 1)
        self.assertTrue(np.array_equal(a, S.hash01(np.arange(1000), np.zeros(1000, int), seed=3)))
        n = S.fbm(np.random.default_rng(0).uniform(-50, 50, (500, 3)), 8.0)
        self.assertTrue(-1 <= n.min() and n.max() <= 1)

    def test_tube_matches_capsule(self):
        t = S.Tube([[0, 0, 0], [10, 0, 0]], [2, 2])
        P = np.random.default_rng(1).uniform(-5, 15, (300, 3))
        ref = []
        for p in P:
            x = min(max(p[0], 0), 10)
            ref.append(np.linalg.norm(p - [x, 0, 0]) - 2)
        self.assertTrue(np.allclose(t.d(P), ref))

    def test_hollow_sphere_is_closed(self):
        dim = Dimension("t:x", -16, 64, "t:x")
        sph = S.Sphere([0.5, 16.5, 0.5], 9.3).with_(paint="minecraft:stone")
        st = S.carve(dim, sph, shell=1, smooth=False)
        g = dense(dim, (-11, 5, -11), (11, 28, 11))
        solid = g != AIR
        self.assertGreater(solid.sum(), 500)
        # 속이 비어 있어야 하고, 바깥에서 그 속으로 닿을 수 없어야 함
        reach = outside_reachable(solid)
        cavity = ~solid & ~reach
        self.assertGreater(cavity.sum(), 1000, "속이 비지 않음")
        self.assertEqual(st.blocks, int(solid.sum()))

    def test_smoothing_adds_partial_blocks_only_in_air(self):
        dim = Dimension("t:x", -16, 64, "t:x")
        tube = S.Tube(S.resample(S.bezier([0, 10, 0], [10, 20, 0], [20, 20, 5], [30, 12, 10], 40), 1.0), 3.0)
        tube.with_(paint="minecraft:dark_oak_planks", smooth=("minecraft:dark_oak_stairs", "minecraft:dark_oak_slab"))
        st = S.carve(dim, tube, shell=1, smooth=True)
        self.assertGreater(st.smooth, 20)
        states = set(dim.palette)
        self.assertTrue(any("dark_oak_stairs" in s for s in states))
        self.assertTrue(any("dark_oak_slab" in s for s in states))

    def test_subtract_and_owner_paint(self):
        dim = Dimension("t:x", -16, 64, "t:x")
        a = S.Box(0, 0, 0, 9, 9, 9).with_(paint="minecraft:stone")
        b = S.Box(3, 3, -2, 6, 6, 4)
        lamp = S.Box(20, 0, 0, 21, 1, 1).with_(paint="minecraft:glowstone")
        S.carve(dim, (a - b) | lamp, shell=1, smooth=False)
        self.assertEqual(dim.get(4, 4, 0), AIR)       # 파낸 홈
        self.assertEqual(dim.get(4, 4, 5), "minecraft:stone")  # 홈 바닥 벽
        self.assertEqual(dim.get(20, 0, 0), "minecraft:glowstone")
        self.assertEqual(dim.get(5, 5, 9), "minecraft:stone")  # 반대쪽 벽 (속은 비었지만 껍질)
        self.assertEqual(dim.get(5, 5, 7), AIR)  # 속 빔

    def test_curl_spirals_inward(self):
        c = S.curl([0, 0, 0], [1, 0, 0], [0, 1, 0], R0=10, turns=2, shrink=0.5)
        self.assertGreater(len(c), 50)
        center_dist = np.linalg.norm(c - c.mean(0), axis=1)
        self.assertLess(center_dist[-1], center_dist[0])


if __name__ == "__main__":
    unittest.main()
