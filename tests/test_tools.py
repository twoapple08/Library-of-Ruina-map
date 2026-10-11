"""python -m unittest discover -s tests"""
import os
import random
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import nbt, region, world  # noqa: E402


def ref_pack(values, bits):
    """느리지만 명확한 참고 구현."""
    per = 64 // bits
    out = []
    for i in range(0, len(values), per):
        v = 0
        for j, x in enumerate(values[i:i + per]):
            v |= int(x) << (j * bits)
        out.append(v - (1 << 64) if v >= 1 << 63 else v)
    return out


class NbtTest(unittest.TestCase):
    def test_roundtrip(self):
        root = {
            "b": nbt.Byte(-1), "s": nbt.Short(300), "i": nbt.Int(-5), "l": nbt.Long(-(1 << 62)),
            "f": nbt.Float(0.5), "d": nbt.Double(-1.25), "str": "도서관 \x00 \U0001F4D6",
            "empty": nbt.List(elem_tag=nbt.TAG_COMPOUND), "ints": nbt.List([nbt.Int(1), nbt.Int(2)]),
            "ba": np.array([1, -2], np.int8), "ia": np.array([7, -8], np.int32),
            "la": np.array([-1, 2 ** 63 - 1], np.int64), "c": {"nested": [{"a": "b"}, {"a": "c"}]},
        }
        raw = nbt.dumps(root)
        back = nbt.loads(raw)
        self.assertEqual(nbt.dumps(back), raw)
        self.assertEqual(back["str"], root["str"])
        self.assertIsInstance(back["l"], nbt.Long)
        self.assertEqual(back["empty"].elem_tag, nbt.TAG_COMPOUND)

    def test_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.dat")
            nbt.write_file(p, {"a": nbt.Int(1)})
            self.assertEqual(nbt.read_file(p), {"a": 1})


class RegionTest(unittest.TestCase):
    def test_roundtrip_and_external(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.-1.0.mca")
            big = np.random.default_rng(1).integers(-2 ** 62, 2 ** 62, 300000, dtype=np.int64)
            chunks = {(-32, 0): {"a": nbt.Int(1)}, (-1, 31): {"big": big}}
            region.write_region(p, chunks)
            self.assertTrue(os.path.exists(os.path.join(d, "c.-1.31.mcc")))
            back = region.read_region(p)
            self.assertEqual(set(back), set(chunks))
            self.assertTrue(np.array_equal(back[(-1, 31)]["big"], big))
            self.assertEqual(os.path.getsize(p) % 4096, 0)


class PackTest(unittest.TestCase):
    def test_pack_matches_reference(self):
        rng = random.Random(3)
        for bits in [1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 15, 16]:
            for count in (64, 4096):
                vals = [rng.randrange(1 << bits) for _ in range(count)]
                got = world.pack_indices(np.array(vals, np.uint64), bits).tolist()
                self.assertEqual(got, ref_pack(vals, bits), f"bits={bits}")
                back = world.unpack_indices(np.array(got, np.int64), bits, count).tolist()
                self.assertEqual(back, vals)

    def test_bits(self):
        self.assertEqual(world.block_bits(2), 4)
        self.assertEqual(world.block_bits(16), 4)
        self.assertEqual(world.block_bits(17), 5)
        self.assertEqual(world.block_bits(257), 9)
        self.assertEqual(world.biome_bits(2), 1)
        self.assertEqual(world.biome_bits(5), 3)


class WorldTest(unittest.TestCase):
    def test_state_parse(self):
        self.assertEqual(world.canonical("oak_stairs[half=top,facing=north]"),
                         "minecraft:oak_stairs[facing=north,half=top]")
        self.assertEqual(world.canonical("ruina:x"), "ruina:x")

    def test_build_write_read(self):
        dim = world.Dimension("ruina:test", -64, 640, "ruina:test")
        dim.fill(-20, -64, -20, 20, -60, 20, "stone")
        dim.fill(-5, -63, -5, 5, -61, 5, "air")
        dim.set(100, 575, -100, "glowstone")
        dim.set(3, 10, 3, "oak_stairs[facing=east,half=bottom]")
        rng = np.random.default_rng(0)
        # 300종 블록이 섞인 섹션 (팔레트 > 256 → 9비트)
        many = [f"minecraft:block_{i}" for i in range(300)]
        ids = np.array([dim.id(s) for s in many])
        arr = ids[rng.integers(0, 300, (16, 16, 16))]
        dim.place(32, 64, 32, arr)
        mask = np.zeros((10, 10, 10), bool)
        mask[::2] = True
        dim.place_mask(200, 0, 200, mask, "glass")
        with tempfile.TemporaryDirectory() as d:
            n = dim.write_regions(d, 5023)
            self.assertEqual(n, len(dim.chunk_keys()))
            chunks = {}
            for f in os.listdir(d):
                chunks.update(region.read_region(os.path.join(d, f)))
        for (cx, cz), c in chunks.items():
            self.assertEqual(len(c["sections"]), 40)
            self.assertEqual(c["yPos"], -4)
        probes = [(0, -64, 0), (-5, -62, -5), (6, -62, 0), (100, 575, -100), (3, 10, 3), (35, 70, 40),
                  (200, 0, 200), (201, 0, 200), (209, 9, 209)]
        probes += [(int(x), int(y), int(z)) for x, y, z in zip(rng.integers(32, 48, 50), rng.integers(64, 80, 50),
                                                            rng.integers(32, 48, 50))]
        for x, y, z in probes:
            c = chunks.get((x >> 4, z >> 4))
            got = world.chunk_block(c, x, y, z) if c else world.AIR
            self.assertEqual(got, dim.get(x, y, z), (x, y, z))

    def test_cached_empty_sections_same_bytes(self):
        """빈 섹션을 미리 직렬화해 재사용해도 결과 바이트가 일반 경로와 같아야 함."""
        dim = world.Dimension("ruina:test", -64, 640, "ruina:test")
        dim.fill(0, 0, 0, 20, 3, 20, "minecraft:oak_stairs[facing=east]")
        dim.set(5, 100, 5, "minecraft:glowstone")
        for cx, cz in dim.chunk_keys():
            raw = nbt.dumps(dim.chunk_nbt(cx, cz, 5023))
            again = nbt.dumps(nbt.loads(raw))
            self.assertEqual(raw, again)

    def test_parallel_write_matches_serial(self):
        dim = world.Dimension("ruina:test", -64, 640, "ruina:test")
        dim.fill(-600, 0, -600, 600, 0, 600, "minecraft:stone")
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            n1 = dim.write_regions(a, 5023, workers=1)
            n2 = dim.write_regions(b, 5023, workers=3)
            self.assertEqual(n1, n2)
            for f in os.listdir(a):
                with open(os.path.join(a, f), "rb") as fa, open(os.path.join(b, f), "rb") as fb:
                    self.assertEqual(fa.read(), fb.read(), f)

    def test_registry_check(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "b.json")
            with open(p, "w") as f:
                f.write('{"minecraft:stone":{},"minecraft:oak_stairs":{"p":{"facing":["north","east"]},"d":{}}}')
            dim = world.Dimension("x", 0, 16, "b", world.BlockRegistry(p))
            dim.set(0, 0, 0, "stone")
            dim.set(0, 1, 0, "oak_stairs[facing=east]")
            with self.assertRaises(ValueError):
                dim.set(0, 2, 0, "stonee")
            with self.assertRaises(ValueError):
                dim.set(0, 2, 0, "oak_stairs[facing=up]")


if __name__ == "__main__":
    unittest.main()
