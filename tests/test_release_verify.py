"""배포 성공 판정에 잘못된 커밋/캐시/빈 월드를 허용하지 않는다."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.release_verify import verify


class ReleaseVerifyTest(unittest.TestCase):
    def make_jar(self, root, **overrides):
        meta = dict(source_commit="a" * 40, world_fingerprint="fingerprint", world_id="world-1",
                    mod_version="0.1.0", minecraft="26.3")
        files = {"ruina/build.json": json.dumps(meta), "ruina/source.sha": "fingerprint\n",
                 "ruina/world.id": "world-1\n", "ruina/world.zip": b"world data",
                 "fabric.mod.json": json.dumps({"id": "ruina", "version": "0.1.0",
                                                "depends": {"minecraft": "~26.3"}})}
        files.update(overrides)
        path = Path(root) / "Ruina.jar"
        with zipfile.ZipFile(path, "w") as jar:
            for name, data in files.items():
                jar.writestr(name, data)
        return path

    def test_valid_jar_has_digest(self):
        with tempfile.TemporaryDirectory() as root:
            result = verify(self.make_jar(root), "a" * 40, "fingerprint")
            self.assertEqual(len(result["sha256"]), 64)
            self.assertEqual(result["file"], "Ruina.jar")

    def test_wrong_source_commit_rejected(self):
        with tempfile.TemporaryDirectory() as root, self.assertRaisesRegex(ValueError, "커밋"):
            verify(self.make_jar(root), "b" * 40, "fingerprint")

    def test_stale_cache_rejected(self):
        with tempfile.TemporaryDirectory() as root, self.assertRaisesRegex(ValueError, "지문"):
            verify(self.make_jar(root), "a" * 40, "new fingerprint")

    def test_changed_world_id_rejected(self):
        with tempfile.TemporaryDirectory() as root, self.assertRaisesRegex(ValueError, "건축 버전"):
            verify(self.make_jar(root, **{"ruina/world.id": "other"}))

    def test_empty_world_rejected(self):
        with tempfile.TemporaryDirectory() as root, self.assertRaisesRegex(ValueError, "빈 월드"):
            verify(self.make_jar(root, **{"ruina/world.zip": b""}))


if __name__ == "__main__":
    unittest.main()
