import unittest
import sys
import metrics

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))

class TestMetrics(unittest.TestCase):
    def test_jaro(self):
        self.assertTrue(metrics.jaro('martha', 'marhta') > 0.9)


if __name__ == '__main__':
    unittest.main()