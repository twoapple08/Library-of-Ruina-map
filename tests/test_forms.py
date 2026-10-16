"""자유 형체 기반 (tools/forms.py) 시험."""
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import forms as F, region, nbt  # noqa: E402
from tools.world import Dimension, chunk_block  # noqa: E402


class FormsTest(unittest.TestCase):
    def setUp(self):
        F.reset()
        self.m = F.mat("stone", "minecraft:block/stone")

    def test_sweep_faces_outward(self):
        path = np.array([[0, 0, 0], [0, 5, 0], [2, 9, 0]], float)
        q = F.sweep(path, 1.0, self.m, sides=8, step=0.5)
        fn = F.face_normals(q.P)
        self.assertTrue(((fn * q.N.mean(1)).sum(-1) > 0).all())
        # 바깥: 면 중심이 경로에서 멀어지는 쪽
        c = q.P.mean(1)
        self.assertGreater(((c - np.array([c[:, 0] * 0, c[:, 1], c[:, 2] * 0]).T) * fn).sum(-1).mean(), -1)
        lo = np.floor(q.UV.min(1) + 1e-6)
        self.assertTrue((q.UV.max(1) - lo <= 1 + 1e-6).all(), "타일 경계를 넘는 면")

    def test_box_and_plane_orientation(self):
        q = F.box((0, 0, 0), (2, 3, 4), self.m)
        c = q.P.mean(1) - np.array([1, 1.5, 2])
        self.assertTrue(((F.face_normals(q.P) * c).sum(-1) > 0).all())
        self.assertEqual(len(q), 2 * (2 * 3 + 2 * 4 + 3 * 4))

    def test_subdivide_and_tiles(self):
        q = F.plane((0, 0, 0), (10, 0, 0), (0, 0, 3), self.m, tile=(5, 3))
        s = F.subdivide(q, 1.0)
        e = np.linalg.norm(s.P[:, 1] - s.P[:, 0], axis=1)
        self.assertTrue((e <= 1.0 + 1e-9).all())
        self.assertAlmostEqual(np.abs(np.cross(s.P[:, 1] - s.P[:, 0], s.P[:, 3] - s.P[:, 0])).sum(), 30, places=6)

    def test_camera_projection(self):
        cam = F.Camera((0, 0, 0), 0, 0, 70, 16 / 9)       # 남쪽(+z) 봄
        sx, sy, z = cam.project(np.array([[0, 0, 10], [0, 1, 10]]))
        self.assertAlmostEqual(sx[0], 0.5)
        self.assertAlmostEqual(sy[0], 0.5)
        self.assertLess(sy[1], 0.5)                        # 위 → 화면 위쪽
        sx, _, _ = cam.project(np.array([[-1, 0, 10]]))    # 서쪽(-x) = 남쪽을 볼 때 오른쪽
        self.assertGreater(sx[0], 0.5)
        c2 = F.Camera.look_at((0, 0, 0), (-5, 0, 0))
        self.assertAlmostEqual(c2.yaw % 360, 90)

    def test_project_art_occlusion(self):
        art = F.mat("art", "ruina:block/form/art_test", emissive=True, flat=True)
        wall = F.plane((-5, -5, 20), (10, 0, 0), (0, 10, 0), self.m).flipped()   # 카메라 쪽(-z)을 봄
        blocker = F.plane((-1, -1, 10), (2, 0, 0), (0, 2, 0), self.m).flipped()
        cam = F.Camera((0, 0, 0), 0, 0, 70)
        q, sel = F.project_art(F.subdivide(wall, 1.0), cam, art, occluders=[blocker])
        c = q.P.mean(1)
        hidden = (np.abs(c[:, 0]) < 1.5) & (np.abs(c[:, 1]) < 1.5)
        self.assertTrue(sel[~hidden].mean() > 0.9)
        self.assertTrue(sel[(np.abs(c[:, 0]) < 1) & (np.abs(c[:, 1]) < 1)].sum() == 0)

    def test_finalize_write_inject(self):
        d = Dimension("ruina:test", 0, 64, "minecraft:plains")
        d.fill(0, 0, 0, 15, 0, 15, "minecraft:stone")
        d.set(5, 3, 5, "minecraft:barrier")
        d.set(7, 3, 5, "minecraft:light[level=12]")
        lay = F.FormLayer("test", d)
        glow = F.mat("lamp", "minecraft:block/glowstone", emissive=True, glow=3)
        lay.add(F.box((5.1, 3.1, 5.1), (5.9, 3.9, 5.9), self.m))          # barrier 칸
        lay.add(F.box((7.2, 3.2, 5.2), (7.8, 3.8, 5.8), glow))           # light 칸
        lay.add(F.plane((2, 0.0, 2), (0, 0, 1), (1, 0, 0), self.m))      # 바닥(돌) 위 → 위 칸(y=1)으로 옮김
        lay.add(F.box((40.2, 10.2, 40.2), (40.8, 10.8, 40.8), self.m))   # 블록 없는 청크
        lay.mover(F.Mover((9, 4, 9), F.box((-1, -1, -1), (1, 1, 1), self.m), (9.5, 4.5, 9.5)))
        st = lay.finalize()
        self.assertEqual(st["버림"], 0)
        self.assertGreaterEqual(st["옮김"], 1)
        cells = {tuple(int(v) for v in c): s for c, s in zip(lay.cell_pos, lay.anchor_states)}
        self.assertEqual(cells[(5, 3, 5)], "ruina:form[glow=0,half=false,light=0,solid=true]")
        self.assertEqual(cells[(7, 3, 5)], "ruina:form[glow=3,half=false,light=12,solid=false]")
        self.assertIn((2, 1, 2), cells)
        self.assertIn((2, 2), d.extra_chunks)
        with tempfile.TemporaryDirectory() as tmp:
            assets = os.path.join(tmp, "assets", "ruina")
            fs = F.FormSet()
            fs.layers["test"] = lay
            fs.write_assets(assets)
            scale, head, rec = F.read_cells(os.path.join(assets, "forms", "test", "r.0.0.bin"))
            self.assertEqual(scale, F.CELL_SCALE)
            self.assertEqual(head[:, 4].sum(), len(rec))
            i = [tuple(h[:3]) for h in head].index((5, 3, 5))
            r = rec[head[i, 3]:head[i, 3] + head[i, 4]]
            p = r["v"]["p"] / scale
            self.assertTrue((p >= 0.09).all() and (p <= 0.91).all())
            self.assertTrue(os.path.exists(os.path.join(assets, "forms", "test", "mesh_0.bin")))
            # 월드 쓰기 → 주입 → 다시 읽기
            wdir = os.path.join(tmp, "world")
            rdir = os.path.join(wdir, "dimensions", "ruina", "test", "region")
            d.write_regions(rdir, 4000, workers=1)
            # 실제 서버는 블록 엔티티 없는 청크의 리스트를 TAG_END로 저장한다.
            rp = os.path.join(rdir, "r.0.0.mca")
            server_chunks = region.read_region(rp)
            for chunk in server_chunks.values():
                chunk["block_entities"] = nbt.List(elem_tag=nbt.TAG_END)
            region.write_region(rp, server_chunks)
            stats = F.inject(wdir, fs.anchors())
            self.assertEqual(stats["자리 아님"], 0)
            ch = region.read_region(os.path.join(rdir, "r.0.0.mca"))
            self.assertEqual(chunk_block(ch[(0, 0)], 5, 3, 5), "ruina:form[glow=0,half=false,light=0,solid=true]")
            self.assertEqual(chunk_block(ch[(0, 0)], 9, 4, 9), "ruina:mover")
            self.assertEqual(chunk_block(ch[(0, 0)], 3, 0, 3), "minecraft:stone")
            self.assertTrue(any(be["id"] == "ruina:mover" for be in ch[(0, 0)]["block_entities"]))
            self.assertEqual(chunk_block(ch[(2, 2)], 40, 10, 40), "ruina:form[glow=0,half=false,light=0,solid=false]")


if __name__ == "__main__":
    unittest.main()
