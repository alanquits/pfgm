import math
import os
import sys
import unittest

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.join(TEST_DIR, "..")
SRC_DIR = os.path.join(ROOT_DIR, "src")
EXAMPLES_DIR = os.path.join(ROOT_DIR, "examples")
sys.path.append(SRC_DIR)

from tfg import TFG

class TestTfg(unittest.TestCase):
    @staticmethod
    def approxEquals(v1, v2, tolerance=1e-9):
        return abs(v1-v2) < tolerance

    def setUp(self):
        jsonPath = os.path.join(TEST_DIR, "tfg.json")
        self.tfg, self.setupErr = TFG.fromJson(jsonPath)

    def test_sample_pass(self):
        self.assertEqual(1, 1, "pass test")

    def test_read_ok(self):
        if self.setupErr != None:
            self.assertTrue(False)

    def test_read_tfg(self):
        dimOk = self.tfg.nx == 4 and self.tfg.ny == 3
        originOk = self.tfg.x0 == 0.0 and self.tfg.y0 == 1.0
        discOk = self.tfg.dx == 1.0 and self.tfg.dy == 1.0
        self.assertTrue(dimOk and originOk and discOk)

    def test_xrange(self):
        ok = self.tfg.xMin(1) == 1.0 and self.tfg.xMax(1) == 2.0
        self.assertTrue(ok)

    def test_yrange(self):
        ok = self.tfg.yMin(1) == 2.0 and self.tfg.yMax(1) == 3.0
        self.assertTrue(ok)
        
    def test_zrange_1(self):
        ok = self.approxEquals(self.tfg.zMin(0, 0, 0), -2.7) and self.approxEquals(self.tfg.zMin(0, 0, 1), -0.7)
        self.assertTrue(ok)

    def test_zrange_2(self):
        ok = self.approxEquals(self.tfg.zMin(2, 1, 0), -2.5) and self.approxEquals(self.tfg.zMin(2, 1, 1), -0.5)
        self.assertTrue(ok)

if __name__ == "__main__":
    unittest.main()