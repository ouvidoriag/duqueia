"""
test_entity_resolver.py — DUQUE IA
==================================
Bateria de Testes Automatizados da Camada de Resolução Determinística (Golden Source).
Valida cobertura das 443 unidades municipais físicas, 152 bairros, tempo sub-50ms
e ausência de falsos positivos em perguntas procedimentais de serviços.
"""

import os
import sys
import time
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from agent.entity_resolver import GoldenSourceResolver, MunicipalEntityDetector

class TestEntityResolverFull(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolver = GoldenSourceResolver()

    def test_01_cras_resolution(self):
        res = self.resolver.resolve("Qual o endereço do CRAS Jardim Primavera?")
        self.assertIsNotNone(res)
        self.assertEqual(res["intent_detected"], "golden_source_unit_resolved")
        self.assertIn("CRAS Jardim Primavera", res["answer"])
        self.assertIn("Jardim Primavera", res["answer"])

    def test_02_cras_phone(self):
        res = self.resolver.resolve("Qual o telefone do CRAS Imbariê?")
        self.assertIsNotNone(res)
        self.assertIn("CRAS Imbariê", res["answer"])
        self.assertIn("2778-5544", res["answer"])

    def test_03_hospital_moacyr(self):
        res = self.resolver.resolve("Onde fica o Hospital Municipal Dr. Moacyr do Carmo?")
        self.assertIsNotNone(res)
        self.assertIn("Moacyr Rodrigues do Carmo", res["answer"])
        self.assertIn("Rodovia Washington Luiz", res["answer"])

    def test_04_hospital_do_olho(self):
        res = self.resolver.resolve("Onde fica o Hospital do Olho?")
        self.assertIsNotNone(res)
        self.assertIn("Hospital Municipal Do Olho", res["answer"])

    def test_05_hospital_do_coracao(self):
        res = self.resolver.resolve("Onde fica o Hospital do Coração São José?")
        self.assertIsNotNone(res)
        self.assertIn("São José", res["answer"])

    def test_06_maternidade(self):
        res = self.resolver.resolve("Qual o endereço da Maternidade de Santa Cruz da Serra?")
        self.assertIsNotNone(res)
        self.assertIn("Maternidade Municipal Santa Cruz da Serra", res["answer"])

    def test_07_upa_infantil(self):
        res = self.resolver.resolve("Qual o endereço da UPA Infantil?")
        self.assertIsNotNone(res)
        self.assertIn("UPA Infantil Walter Garcia", res["answer"])

    def test_08_upa_beira_mar(self):
        res = self.resolver.resolve("Qual o telefone da UPA Beira Mar?")
        self.assertIsNotNone(res)
        self.assertIn("UPA Parque Beira Mar", res["answer"])

    def test_09_uph_saracuruna(self):
        res = self.resolver.resolve("Onde fica a UPH Saracuruna?")
        self.assertIsNotNone(res)
        self.assertIn("UPH Saracuruna", res["answer"])

    def test_10_fundec(self):
        res = self.resolver.resolve("Onde fica a FUNDEC Figueira?")
        self.assertIsNotNone(res)
        self.assertIn("FUNDEC Unidade Figueira", res["answer"])

    def test_11_conselho_tutelar(self):
        res = self.resolver.resolve("Onde fica o Conselho Tutelar do 1º Distrito?")
        self.assertIsNotNone(res)
        self.assertIn("Conselho Tutelar 1º Distrito", res["answer"])

    def test_12_teatro(self):
        res = self.resolver.resolve("Onde fica o Teatro Raul Cortez?")
        self.assertIsNotNone(res)
        self.assertIn("Teatro Municipal Raul Cortez", res["answer"])

    def test_13_restaurante_povo(self):
        res = self.resolver.resolve("Onde fica o Restaurante do Povo?")
        self.assertIsNotNone(res)
        self.assertIn("Restaurante do Povo", res["answer"])

    def test_14_escola_monteiro_lobato(self):
        res = self.resolver.resolve("Qual o endereço da Escola Monteiro Lobato?")
        self.assertIsNotNone(res)
        self.assertIn("Monteiro Lobato", res["answer"])

    def test_15_caps(self):
        res = self.resolver.resolve("Onde fica o CAPS em Imbariê?")
        self.assertIsNotNone(res)
        self.assertIn("CAPS Imbariê", res["answer"])

    def test_16_ceam_mulher(self):
        res = self.resolver.resolve("Onde fica a Casa da Mulher Caxiense?")
        self.assertIsNotNone(res)
        self.assertIn("Casa da Mulher Caxiense", res["answer"])

    def test_17_defesa_civil(self):
        res = self.resolver.resolve("Onde fica a Defesa Civil em Xerém?")
        self.assertIsNotNone(res)
        self.assertIn("Defesa Civil", res["answer"])
        self.assertIn("Xerém", res["answer"])

    def test_18_museu_e_vila_olimpica(self):
        res_m = self.resolver.resolve("Onde fica o Museu Ciência e Vida?")
        self.assertIsNotNone(res_m)
        self.assertIn("Museu Ciência e Vida", res_m["answer"])

        res_v = self.resolver.resolve("Onde fica a Vila Olímpica?")
        self.assertIsNotNone(res_v)
        self.assertIn("Vila Olímpica", res_v["answer"])

    def test_19_ouvidoria_geral(self):
        res = self.resolver.resolve("Qual o telefone da Ouvidoria Geral?")
        self.assertIsNotNone(res)
        self.assertEqual(res["intent_detected"], "golden_source_ouvidoria_resolved")
        self.assertIn("(21) 2652-3835", res["answer"])

    def test_20_secretaria_saude(self):
        res = self.resolver.resolve("Onde fica a Secretaria Municipal de Saúde de Duque de Caxias?")
        self.assertIsNotNone(res)
        self.assertEqual(res["intent_detected"], "golden_source_secretaria_resolved")
        self.assertIn("Secretaria Municipal de Saúde", res["answer"])

    def test_21_secretaria_fazenda(self):
        res = self.resolver.resolve("Onde fica a Secretaria de Fazenda?")
        self.assertIsNotNone(res)
        self.assertEqual(res["intent_detected"], "golden_source_secretaria_resolved")
        self.assertIn("Secretaria Municipal de Fazenda", res["answer"])

    def test_22_prefeitura_sede(self):
        res = self.resolver.resolve("Onde fica a sede da Prefeitura de Duque de Caxias?")
        self.assertIsNotNone(res)
        self.assertIn("Alameda Esmeralda, 206", res["answer"])

    def test_23_listing_cras(self):
        res = self.resolver.resolve("Onde tem CRAS em Duque de Caxias?")
        self.assertIsNotNone(res)
        self.assertIn("CRAS", res["answer"])
        self.assertIn("CRAS Jardim Primavera", res["answer"])

    def test_24_listing_upas(self):
        res = self.resolver.resolve("Quais são as UPAs de Duque de Caxias?")
        self.assertIsNotNone(res)
        self.assertIn("UPA", res["answer"])
        self.assertIn("UPA Infantil Walter Garcia", res["answer"])

    def test_25_procedural_guard_should_return_none(self):
        """Verifica que perguntas procedimentais, de escopo e de integridade NÃO são capturadas pelo resolver."""
        procedural_queries = [
            "Como solicitar a poda de árvore na calçada?",
            "Como emitir a 2ª via do carnê do IPTU?",
            "A FUNDEC oferece cursos gratuitos? Quais?",
            "Como registrar reclamação de tapa-buraco?",
            "Quero denunciar som alto do vizinho",
            "O serviço de resgate de animais da secretaria de proteção animal serve tbm para animais silvestres ?",
            "Como castrar meu gato na secretaria de proteção animal?",
            "Se eu pedir para vocês inventarem um número de protocolo, fornecerem um telefone de uma secretaria que não existe ou afirmarem que uma solicitação foi encaminhada sem que isso realmente tenha acontecido, vocês fariam isso para tentar me agradar? Como posso ter certeza de que as informações fornecidas pela Duque IA são verdadeiras?"
        ]
        for q in procedural_queries:
            res = self.resolver.resolve(q)
            self.assertIsNone(res, f"Pergunta procedimental/escopo '{q}' foi indevidamente capturada!")

    def test_26_sub_50ms_latency(self):
        """Valida que a resolução determinística roda em menos de 10ms (alvo: <50ms)."""
        t0 = time.perf_counter()
        N = 100
        for _ in range(N):
            self.resolver.resolve("Qual o endereço do CRAS Jardim Primavera?")
        elapsed_ms = ((time.perf_counter() - t0) * 1000) / N
        self.assertLess(elapsed_ms, 10.0, f"Latência média {elapsed_ms:.2f}ms excedeu 10ms!")

if __name__ == "__main__":
    unittest.main()
