"""검증용 미리보기가 실제 구멍과 검은 면을 구분하는지 검사한다."""
import unittest

import numpy as np

from tools import forms as F
from tools import form_raster as R


class RasterTest(unittest.TestCase):
    def setUp(self):
        F.reset()
        self.mat = F.mat("raster_test", "minecraft:block/stone")
        self.cam = F.Camera((0, 0, 0), 0, 0)

    def test_large_face_has_no_sample_holes(self):
        q = F.plane((-100, -100, 10), (200, 0, 0), (0, 200, 0), self.mat, tile=(200, 200)).flipped()
        ids, depth, weights = R.fragments(q, self.cam, 96, 54)
        self.assertTrue((ids == 0).all())
        np.testing.assert_allclose(depth, 10)
        np.testing.assert_allclose(weights.sum(-1), 1)

    def test_nearest_face_and_backface(self):
        near = F.plane((-1, -1, 3), (2, 0, 0), (0, 2, 0), self.mat, tile=(2, 2)).flipped()
        far = near.translate((0, 0, 2))
        ids, depth, _ = R.fragments(F.concat([far, near]), self.cam, 96, 54)
        self.assertEqual(ids[27, 48], 1)
        self.assertAlmostEqual(depth[27, 48], 3)
        ids, _, _ = R.fragments(near.flipped(), self.cam, 96, 54)
        self.assertTrue((ids < 0).all())

    def test_black_surface_is_covered(self):
        q = F.box((-1, -1, 3), (1, 1, 4), self.mat).tint((0, 0, 0))
        img, depth = R.render([q], self.cam, 96, 54)
        self.assertTrue(np.isfinite(depth[27, 48]))
        np.testing.assert_equal(np.asarray(img)[27, 48], [0, 0, 0])

    def test_cutout_reveals_surface_behind(self):
        from PIL import Image
        texture = np.full((16, 16, 4), 255, dtype=np.uint8)
        texture[:, :8, 3] = 0
        cutout = F.mat('raster_cutout', F.texture('raster_cutout', Image.fromarray(texture)), layer='cutout')
        front = F.plane((-1, -1, 3), (2, 0, 0), (0, 2, 0), cutout, tile=(2, 2)).flipped()
        back = front.translate((0, 0, 2)).scale((2, 2, 1)).with_mat(self.mat)
        ids, _, _ = R.fragments(F.concat([back, front]), self.cam, 96, 54)
        self.assertIn(0, ids[20:35, 40:55])
        self.assertIn(1, ids[20:35, 40:55])

    def test_mover_snapshot_uses_axis_and_phase(self):
        q = F.box((1, 0, 0), (2, 1, 1), self.mat)
        mover = F.Mover((0, 0, 0), q, (0, 0, 0), 'spin', (0, 1, 0), period=4, phase=.25)
        actual = R.mover_mesh(mover, self.cam)
        np.testing.assert_allclose(actual.P, q.rotate('y', 90).P)


if __name__ == '__main__':
    unittest.main()
