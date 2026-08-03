import sys
import unittest
sys.path.insert(0, ".")

from agent.retrieval import compute_rrf_fusion

class TestRRFFusion(unittest.TestCase):

    def test_rrf_combination(self):
        list1 = [
            {"source": "docA", "score": 0.90},
            {"source": "docB", "score": 0.80}
        ]
        list2 = [
            {"source": "docB", "score": 0.95},
            {"source": "docC", "score": 0.70}
        ]

        fused = compute_rrf_fusion([list1, list2], k=60)
        
        self.assertIn("docA", fused)
        self.assertIn("docB", fused)
        self.assertIn("docC", fused)

        # docB aparece em rank 2 (list1) e rank 1 (list2)
        score_docB = (1.0 / 62) + (1.0 / 61)
        score_docA = (1.0 / 61)

        self.assertAlmostEqual(fused["docB"]["score"], score_docB, places=5)
        self.assertGreater(fused["docB"]["score"], fused["docA"]["score"])

if __name__ == "__main__":
    unittest.main()
