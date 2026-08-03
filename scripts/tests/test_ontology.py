import sys
import unittest
sys.path.insert(0, ".")

from agent.ontology import MunicipalOntologyEngine

class TestMunicipalOntology(unittest.TestCase):

    def setUp(self):
        self.engine = MunicipalOntologyEngine()

    def test_resolve_isencao_ipi(self):
        ent = self.engine.resolve_entity("to bsucando Isenção de IPI")
        self.assertIsNotNone(ent)
        self.assertEqual(ent["entity_id"], "ISENCAO_TAXISTA")
        self.assertEqual(ent["secretaria"], "Secretaria Municipal de Transportes e Serviços Públicos")

    def test_resolve_matricula(self):
        ent = self.engine.resolve_entity("como faço matrícula escolar para meu filho?")
        self.assertIsNotNone(ent)
        self.assertEqual(ent["entity_id"], "MATRICULA_ESCOLAR")

    def test_resolve_quebra_mola(self):
        ent = self.engine.resolve_entity("quero colocar um quebra mola na minha rua")
        self.assertIsNotNone(ent)
        self.assertEqual(ent["entity_id"], "QUEBRA_MOLAS")

    def test_expand_keywords(self):
        kws = self.engine.expand_query_keywords("isenção ipi taxista")
        self.assertIn("taxista", kws)
        self.assertIn("isencao ipi", kws)

if __name__ == "__main__":
    unittest.main()
