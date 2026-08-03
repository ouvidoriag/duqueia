import sys
import unittest
sys.path.insert(0, ".")

from agent.candidate import Candidate
from agent.context_builder import ContextBuilder

class TestContextBuilder(unittest.TestCase):

    def test_chunk_fusion_same_source(self):
        c1 = Candidate(
            source="carta_servicos_obras.md",
            title="Tapa-Buraco Parte 1",
            category="obras",
            content="Passo 1: Solicitação no aplicativo Colab.",
            retrieval_score=0.90
        )
        c2 = Candidate(
            source="carta_servicos_obras.md",
            title="Tapa-Buraco Parte 2",
            category="obras",
            content="Passo 2: A equipe técnica realiza a vistoria e o reparo em até 30 dias.",
            retrieval_score=0.85
        )

        context_text, sources, final_cands = ContextBuilder.build_context([c1, c2], top_k=5)

        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0], "carta_servicos_obras.md")
        self.assertIn("Passo 1: Solicitação no aplicativo Colab.", context_text)
        self.assertIn("Passo 2: A equipe técnica realiza a vistoria", context_text)

if __name__ == "__main__":
    unittest.main()
