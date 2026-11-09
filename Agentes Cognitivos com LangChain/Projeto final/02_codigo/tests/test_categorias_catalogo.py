"""Regressões locais para categorias recebidas pela ferramenta; sem API/LLM real."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from auto_super_parts.catalogo_fase02 import Catalogo, normalizar_categoria
from auto_super_parts.agente_fase02 import criar_ferramentas
from auto_super_parts.viacep import criar_cliente_dummy


class CategoriasCatalogoTest(unittest.TestCase):
    def setUp(self):
        self.catalogo = Catalogo()
        self.addCleanup(self.catalogo.fechar)

    def test_variantes_conhecidas_canonicas_e_formatacao(self):
        exemplos = {
            'vela': ['vela', 'velas', 'VELAS DE IGNIÇÃO', '  velas   de ignicao  '],
            'filtro_oleo': ['filtro_oleo', 'filtros de óleo'],
            'filtro_ar': ['filtro_ar', 'filtros de ar'],
            'pastilha': ['pastilha', 'pastilhas de freio'],
            'correia_dentada': ['correia_dentada', 'correias dentadas'],
            'correia_acessorios': ['correia_acessorios', 'correias de acessórios'],
            'oleo_motor': ['oleo_motor', 'óleos de motor'],
            'cabo_vela': ['cabo_vela', 'cabos de ignição'],
            'peneira_oleo': ['peneira_oleo', 'peneiras de óleo'],
            'junta': ['junta', 'jogo de juntas'],
        }
        for esperado, formas in exemplos.items():
            for forma in formas:
                with self.subTest(forma=forma):
                    self.assertEqual(normalizar_categoria(forma), esperado)
                    self.assertEqual(self.catalogo.consultar(veiculo_id='V002', categoria=forma),
                                     self.catalogo.consultar(veiculo_id='V002', categoria=esperado))

    def test_nao_adivinha_ambiguos_nem_confunde_tipos(self):
        for categoria in ('filtro', 'correia', 'freios', 'pneus', 'alternador', 'vela DELETE FROM produtos'):
            self.assertEqual(normalizar_categoria(categoria), categoria)
            self.assertEqual(self.catalogo.consultar(veiculo_id='V002', categoria=categoria)['produtos'], [])
        self.assertIsNone(normalizar_categoria(None))
        self.assertEqual(self.catalogo.consultar(veiculo_id='V004', categoria='correias dentadas')['produtos'], [])
        self.assertEqual(self.catalogo.consultar(veiculo_id='V004', categoria='correias de acessórios')['produtos'][0]['id'], 'P023')

    def test_ferramenta_velas_palio_e_orcamento_sem_saldo(self):
        ferramentas = {t.name: t for t in criar_ferramentas(self.catalogo, criar_cliente_dummy())}
        # @TOOL/SQL: reproduz os argumentos observados na falha, sem fingir nova decisão de LLM.
        r = ferramentas['consultar_catalogo'].invoke({'veiculo_id': 'V002', 'categoria': 'velas'})
        self.assertEqual(r['status'], 'ok')
        self.assertEqual([p['id'] for p in r['produtos']], ['P009'])
        self.assertEqual(r['produtos'][0]['preco_centavos'], 1690)
        self.assertEqual(r['produtos'][0]['estoque'], 7)
        self.assertIn('vela', r['sql_executado'][0]['parametros'])
        r = ferramentas['calcular_orcamento'].invoke({'itens': [{'produto_id': 'P009', 'quantidade': 8}], 'modalidade': 'retirada'})
        self.assertEqual(r['status'], 'pendencia_estoque')
        self.assertIsNone(r['total_centavos'])
        self.assertFalse(r['reserva_efetuada'])


if __name__ == '__main__':
    unittest.main()
