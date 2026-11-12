"""Métrica complementar de trajetória e teste do próprio juiz, sem API."""
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / 'src'))

from secretaria.avaliacao import carregar_casos, comparar_ferramentas, testar_juiz


class AvaliacaoJuizTest(unittest.TestCase):
    def test_repeticao_zera_nota_exata_mas_nao_a_complementar(self):
        # Caso observado na execução real de 12/11/2026: listar_corpora_acessiveis chamada duas vezes.
        r = comparar_ferramentas(['listar_corpora_acessiveis', 'consultar_mensagens_estruturado'],
                                 ['listar_corpora_acessiveis', 'listar_corpora_acessiveis',
                                  'consultar_mensagens_estruturado'])
        self.assertEqual((r['nota'], r['nota_sem_repeticao']), (0, 1))
        extra = comparar_ferramentas(['buscar_cliente'], ['buscar_cliente', 'consultar_projeto'])
        self.assertEqual((extra['nota'], extra['nota_sem_repeticao']), (0, 0))

    def test_teste_do_juiz_usa_somente_fixtures_e_marca_origem(self):
        class JuizFalso:
            pass
        casos = carregar_casos(RAIZ)
        from unittest.mock import patch
        with patch('secretaria.avaliacao.julgar_resposta',
                   side_effect=lambda caso, resposta, modelo: {'nota': 0, 'justificativa': 'x'}):
            resultados = testar_juiz(casos, JuizFalso())
        self.assertEqual({r['id'] for r in resultados}, {'proposta_visita', 'oferta_consulta'})
        self.assertTrue(all(r['origem'] == 'teste_do_juiz_fixture' for r in resultados))


if __name__ == '__main__':
    unittest.main()
