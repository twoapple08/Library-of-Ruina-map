"""전 지정사서 방의 실제 생성과 도착 공간 검사 (게임 실행 아님)."""
import importlib
import math
import unittest

import numpy as np

from builders import Build


class RoomBuildTest(unittest.TestCase):
    def test_all_rooms_generate_with_safe_arrivals(self):
        b = Build()  # 실제 전체 빌드처럼 재질/텍스처 레지스트리를 공유한다.
        importlib.import_module("builders.general").mats()
        for room in ("history", "technology", "literature", "art", "natural_science",
                     "language", "social_science", "philosophy", "religion", "general"):
            with self.subTest(room=room):
                module = importlib.import_module(f"builders.{room}_room")
                d = b.dim(room)
                x, y, z, yaw, pitch = module.build(b, d)
                cell = (math.floor(x), math.floor(y), math.floor(z))
                self.assertEqual(d.get(*cell), "minecraft:air", "도착점 발이 충돌 블록에 끼임")
                self.assertEqual(d.get(cell[0], cell[1] + 1, cell[2]), "minecraft:air", "도착점 머리가 끼임")
                self.assertNotEqual(d.get(cell[0], cell[1] - 1, cell[2]), "minecraft:air", "도착점 바닥 없음")
                parts = b.form(room).parts
                self.assertTrue(parts, "방 형체 없음")
                for mesh, _ in parts:
                    self.assertTrue(np.isfinite(mesh.P).all(), "유효하지 않은 좌표")


if __name__ == "__main__":
    unittest.main()
