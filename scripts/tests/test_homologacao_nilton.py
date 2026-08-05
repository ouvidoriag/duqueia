"""
Suíte de Teste de Homologação — 10 Diálogos do Relatório de Nilton (05/08/2026)
DUQUE IA — Validação de Regras de Negócio, Intent Routing, Guardrails e Anti-Redundância
"""
import sys
import os
import unittest

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from agent.agent import DuqueIAAgent
from agent.triage import perform_triage

class TestHomologacaoNilton(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = DuqueIAAgent()

    def test_dialogo_01_matricula_creche_formatacao(self):
        query = "Queria saber como faço para matricular meu filho na creche."
        res = self.agent.process_query(query)
        ans = res.get("answer", "")
        
        self.assertIn("creche", ans.lower())
        # Deve ter destaques em negrito estruturados
        self.assertTrue("**" in ans)
        print("\n[OK] Diálogo 01 - Matrícula na Creche (Formatação Limpa)")

    def test_dialogo_02_creche_mais_proxima_ambiguidade_e_anti_redundancia(self):
        # Turno 1
        q1 = "Queria saber como faço para matricular meu filho na creche."
        r1 = self.agent.process_query(q1, conversation_id="test_nilton_02")
        
        # Turno 2 - sem localização (bairro/rua)
        q2 = "E qual a creche mais próxima da minha casa?"
        history = [q1, r1["answer"]]
        r2 = self.agent.process_query(q2, conversation_id="test_nilton_02", history=history)
        ans2 = r2.get("answer", "")
        
        # Deve solicitar o bairro/rua (Agente Coletor)
        self.assertTrue("bairro" in ans2.lower() or "rua" in ans2.lower() or "localização" in ans2.lower())
        print("\n[OK] Diálogo 02 - Creche mais próxima (Solicita Bairro/Rua)")

    def test_dialogo_03_barulho_e_trafico_de_drogas(self):
        query = "Tem um bar na minha rua que faz muito barulho todos os dias de madrugada. Preciso que me ajudem! O bar tem tráfico de drogas também as vezes."
        res = self.agent.process_query(query)
        ans = res.get("answer", "")
        
        # Deve orientar ligar para 190 (PM) e Colab/SMSP
        self.assertTrue("190" in ans or "polícia" in ans.lower() or "policia" in ans.lower())
        self.assertTrue("colab" in ans.lower() or "segurança pública" in ans.lower() or "smsp" in ans.lower())
        print("\n[OK] Diálogo 03 - Barulho + Tráfico de Drogas (Roteado para 190 e SMSP)")

    def test_dialogo_04_oportunidade_emprego(self):
        query = "Queria uma oportunidade de emprego. O município consegue me contratar?"
        res = self.agent.process_query(query)
        ans = res.get("answer", "")
        
        # Não deve inventar datas futuras alucinadas de 2026/2027 inexistentes
        self.assertNotIn("28 de abril e 6 de maio de 2026", ans)
        self.assertTrue("concurso" in ans.lower() or "sine" in ans.lower() or "portal" in ans.lower() or "fundec" in ans.lower())
        print("\n[OK] Diálogo 04 - Oportunidade de Emprego (Sem alucinação de datas)")

    def test_dialogo_05_casa_desabando_defesa_civil(self):
        query = "Preciso de orientação. Minha casa está desabando, como o município pode me ajudar?"
        res = self.agent.process_query(query)
        ans = res.get("answer", "")
        
        # NÃO pode responder sobre parte elétrica! Deve ser Defesa Civil (199)
        self.assertNotIn("elétrica", ans.lower())
        self.assertTrue("defesa civil" in ans.lower())
        self.assertTrue("199" in ans or "2676-8000" in ans)
        print("\n[OK] Diálogo 05 - Casa Desabando (Roteamento Rápido Defesa Civil 199)")

    def test_dialogo_06_assistencia_social_passando_fome(self):
        query = "estou passando necessidades. sem dinheiro. Com fome. Preciso de ajuda"
        res = self.agent.process_query(query)
        ans = res.get("answer", "")
        
        self.assertTrue("cras" in ans.lower() or "assistência social" in ans.lower() or "assistencia social" in ans.lower())
        print("\n[OK] Diálogo 06 - Assistência Social (Informativo e Direcionamento CRAS)")

    def test_dialogo_06b_menor_agressao(self):
        query = "Vizinho menor de idade está sofrendo agressão dos pais."
        res = self.agent.process_query(query)
        ans = res.get("answer", "")
        
        # Deve orientar Polícia Militar (190), Disque 100 ou Conselho Tutelar
        self.assertTrue("190" in ans or "100" in ans or "conselho tutelar" in ans.lower() or "ouvidoria" in ans.lower())
        print("\n[OK] Diálogo 06b - Agressão a Menor (Proteção ao Menor / Escalona Humanamente)")

    def test_dialogo_07_belford_roxo_fora_competencia(self):
        query = "Sou de Belford Roxo e queria reparo de uma rua minha."
        res = self.agent.process_query(query)
        ans = res.get("answer", "")
        
        self.assertIn("fora", ans.lower())
        self.assertTrue("belford roxo" in ans.lower() or "outros municípios" in ans.lower() or "atribuições" in ans.lower())
        print("\n[OK] Diálogo 07 - Belford Roxo (Bloqueado Fora de Competência)")

    def test_dialogo_08_arvore_caiu_no_carro_trava_juridica(self):
        query = "Caiu uma árvore no meu carro. Com quem eu falo na prefeitura para resolver?"
        res = self.agent.process_query(query)
        ans = res.get("answer", "")
        
        # Não deve assumir culpa/dizer que a prefeitura paga diretamente
        self.assertTrue("procuradoria" in ans.lower() or "ouvidoria" in ans.lower() or "processo administrativo" in ans.lower() or "danos" in ans.lower())
        print("\n[OK] Diálogo 08 - Árvore Caiu no Carro (Trava Jurídica Patrimonial)")

    def test_dialogo_09_arvore_fio_alta_tensao(self):
        query = "Tem uma árvore encostada no fio de alta tensão. Como posso solicitar ajuda?"
        res = self.agent.process_query(query)
        ans = res.get("answer", "")
        
        self.assertTrue("light" in ans.lower() or "energia" in ans.lower() or "meio ambiente" in ans.lower() or "colab" in ans.lower())
        print("\n[OK] Diálogo 09 - Árvore em Alta Tensão (Orientação da concessionária Light + Meio Ambiente)")

if __name__ == "__main__":
    unittest.main()
