"""입체 부품의 닫힘·법선과 실제 계단 충돌 회귀 검사."""
import unittest

import numpy as np

from builders import Build, detail as D, exterior as E, exterior_surroundings as City
from tools import forms as F


def boundary_edges(q):
    """짝이 없는 변. 별도 닫힌 부품끼리 닿아 4회 등장하는 변은 허용한다."""
    points, ids = np.unique(np.round(q.P.reshape(-1, 3), 7), axis=0, return_inverse=True)
    ids = ids.reshape(-1, 4)
    edges = np.stack([ids, np.roll(ids, -1, axis=1)], -1).reshape(-1, 2)
    edges = edges[edges[:, 0] != edges[:, 1]]
    unique, count = np.unique(np.sort(edges, axis=1), axis=0, return_counts=True)
    return points[unique[count % 2 != 0]]


class DetailTest(unittest.TestCase):
    def setUp(self):
        F.reset()
        self.mat = F.mat("detail_test", "minecraft:block/stone")

    def test_chamfer_is_closed_and_outward(self):
        q = D.beveled_box((-1, -2, -3), (1, 2, 3), self.mat, .1)
        self.assertEqual(len(boundary_edges(q)), 0)
        self.assertTrue((np.sum(F.face_normals(q.P)*q.P.mean(1), axis=1) > 0).all())
        self.assertTrue(np.isfinite(q.P).all())
        np.testing.assert_allclose(q.bounds(), [[-1, -2, -3], [1, 2, 3]])

    def test_branch_ends_are_closed(self):
        p = np.array([[0, 0, 0], [0, 3, 0], [2, 5, 1]], float)
        q = E.tube(p, [1, .7, .2], self.mat, rings=False, sides=8)
        self.assertEqual(len(boundary_edges(q)), 0)

    def test_window_and_book_components_are_closed(self):
        for q in (D.casement(1.2, 2.0, self.mat, self.mat, self.mat),
                  D.upright_book(.2, .9, .5, self.mat, self.mat),
                  D.flat_book(1.2, 1.8, .15, self.mat, self.mat)):
            # 서로 닿지 않는 부품의 합집합에도 한쪽만 있는 경계는 없어야 한다.
            self.assertEqual(len(boundary_edges(q)), 0)

    def test_entrance_stairs_match_half_block_collision(self):
        b = Build()
        d = b.dim("exterior")
        E.stairs(d)
        for x0, x1, za, zb, top in E.entrance_steps():
            topcell = int(np.ceil(top))-1
            expected = F.HALF_SOLID if top % 1 else "minecraft:barrier"
            self.assertEqual(d.get(0, topcell, za), expected)
            self.assertEqual(d.get(0, topcell+1, za), "minecraft:air")
        E._bay_collision(d)
        self.assertTrue(E.gate_walkable(d, (-1, 1, int(E.DOOR_Z), 2, 4, 60)))

    def test_city_building_has_finite_geometry_and_roof(self):
        m = City.materials()
        q = City.building(m, 14, 12, 24, 504, near=True)
        self.assertTrue(np.isfinite(q.P).all())
        center = q.P.mean(1)
        roof = (center[:, 1] >= 24) & (F.face_normals(q.P)[:, 1] > .9)
        self.assertTrue(roof.any())
        self.assertLess(q.bounds()[0][1], .01)

    def test_terrace_collision_is_barrier_and_matches_top(self):
        from unittest.mock import patch
        b = Build()
        d = b.dim('exterior')
        with patch.object(City.crater, 'TOPS', [12]), patch.object(City.crater, 'RINGS', [135, 190]):
            City.terrain(b.form('exterior'), d, City.materials())
        self.assertEqual(d.get(160, 12, 0), 'minecraft:barrier')
        self.assertEqual(d.get(160, 13, 0), 'minecraft:air')
        self.assertEqual(d.get(134, -1, 0), 'minecraft:barrier')
        self.assertTrue(b.form('exterior').parts)

    def test_wheel_collision_moves_with_geometry(self):
        from unittest.mock import patch
        from tools import shapes as S
        b = Build()
        with patch.object(S, 'carve') as carve:
            City.wheel(b.form('exterior'), b.dim('exterior'), City.materials())
        field = carve.call_args.args[1]
        old = np.array([360*np.cos(-.45), City.crater.TOPS[3]+78, 360*np.sin(-.45)])
        self.assertLess(field.d(np.array([old+City.WHEEL_SHIFT]))[0], 0)
        self.assertGreater(field.d(np.array([old]))[0], 0)


if __name__ == "__main__":
    unittest.main()
