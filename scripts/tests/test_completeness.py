import sys
import unittest
sys.path.insert(0, ".")

from agent.completeness import calculate_completeness_score

class TestCompletenessScore(unittest.TestCase):

    def test_markdown_rich_completeness(self):
        candidate = {
            "source": "lacunas_dados_resolvidas.md",
            "category": "faq_chunks",
            "content": "A" * 350
        }
        score = calculate_completeness_score(candidate)
        self.assertEqual(score, 1.00)

    def test_incomplete_sql_completeness(self):
        candidate = {
            "source": "vw_ia_servicos (ID: 1208)",
            "category": "carta_servicos",
            "content": "[FONTE OFICIAL ESTRUTURADA]\nServiço Oficial: Matrícula\nEndereço: Não cadastrado\nDescrição: Não cadastrado"
        }
        score = calculate_completeness_score(candidate)
        self.assertLessEqual(score, 0.60)

    def test_multiplicative_scoring_ranking(self):
        # SQL candidato com alta similaridade de busca (0.95), mas incompleto (0.30) -> final_score = 0.285
        sql_candidate = {
            "source": "vw_ia_servicos (ID: 1208)",
            "category": "carta_servicos",
            "content": "[FONTE OFICIAL ESTRUTURADA]\nServiço Oficial: Matrícula\nEndereço: Não cadastrado",
            "similarity": 0.95
        }
        
        # Markdown candidato com similaridade (0.85), e completo (1.00) -> final_score = 0.85
        md_candidate = {
            "source": "lacunas_dados_resolvidas.md",
            "category": "faq_chunks",
            "content": "Documentação necessária para Matrícula em Creche..." + "A" * 300,
            "similarity": 0.85
        }
        
        score_sql = sql_candidate["similarity"] * calculate_completeness_score(sql_candidate)
        score_md = md_candidate["similarity"] * calculate_completeness_score(md_candidate)

        # O documento rico DEVE vencer o SQL incompleto por matemática pura
        self.assertGreater(score_md, score_sql)

if __name__ == "__main__":
    unittest.main()
