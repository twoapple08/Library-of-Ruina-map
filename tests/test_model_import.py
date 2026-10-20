"""External asset import must fail visibly on unsupported authoring features."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from tools import forms as F
from tools.model_import import load_bbmodel

ASSET = Path(__file__).resolve().parents[1] / "design/models/tiphereth_table.bbmodel"


class ModelImportTest(unittest.TestCase):
    def setUp(self):
        F.reset()
        self.mat = F.mat("import_test", "minecraft:block/stone")
        self.data = json.loads(ASSET.read_text())

    def load_modified(self, edit):
        data = copy.deepcopy(self.data)
        edit(data)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "asset.bbmodel"
            p.write_text(json.dumps(data))
            return load_bbmodel(p, {0: self.mat})

    def test_table_scale_normals_and_closed_components(self):
        q = load_bbmodel(ASSET, {0: self.mat})
        np.testing.assert_allclose(q.bounds(), [[-1.3, 0, -.54], [1.3, 1, .54]], atol=1e-6)
        np.testing.assert_allclose(np.linalg.norm(q.N, axis=-1), 1)
        self.assertEqual(len(q), 234)
        for e in self.data["elements"]:
            vertices = np.array(list(e["vertices"].values())) / 16
            center = (vertices.min(0) + vertices.max(0)) / 2
            keys = e["vertices"]
            edges = []
            for face in e["faces"].values():
                names = face["vertices"]
                p = np.array([keys[k] for k in names])/16
                normal = np.cross(p[1]-p[0], p[2]-p[0])
                self.assertGreater(float(normal @ (p.mean(0)-center)), 0)
                edges.extend(tuple(sorted((a, b))) for a, b in zip(names, names[1:]+names[:1]))
            from collections import Counter
            self.assertTrue(all(n == 2 for n in Counter(edges).values()))

    def test_unsupported_features_are_not_silently_dropped(self):
        edits = [lambda d: d.update(animations=[{"name": "spin"}]),
                 lambda d: d["elements"][0].update(rotation=[0, 30, 0]),
                 lambda d: d["elements"][0].update(type="cube"),
                 lambda d: d["outliner"].append(d["outliner"][0]),
                 lambda d: d.update(outliner=[{"rotation": [0, 15, 0], "children": d["outliner"]}]),
                 lambda d: d["resolution"].update(width=0)]
        for edit in edits:
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                self.load_modified(edit)

    def test_bad_uv_missing_binding_and_nonfinite_vertex(self):
        face = next(iter(self.data["elements"][0]["faces"].values()))
        face_key = next(iter(self.data["elements"][0]["faces"]))
        vertex_key = face["vertices"][0]
        edits = [lambda d: d["elements"][0]["faces"][face_key]["uv"].update({vertex_key: [65, 0]}),
                 lambda d: d["elements"][0]["faces"][face_key].update(texture=1),
                 lambda d: d["elements"][0]["vertices"].update({vertex_key: [float("nan"), 0, 0]})]
        for edit in edits:
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                self.load_modified(edit)

    def test_model_change_invalidates_world_cache(self):
        from tools.world_cache import INCLUDE_DIRS
        self.assertIn("design/models", INCLUDE_DIRS)


if __name__ == "__main__":
    unittest.main()
