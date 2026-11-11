"""Ferramentas do agente usam conexão SQLite da thread em que são executadas."""
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from secretaria.banco import Banco, Contexto
from secretaria.agenda import Agenda
from secretaria.agente_agenda import criar_ferramentas_agenda


class FerramentasThreadTest(unittest.TestCase):
    def test_busca_sem_termo_devolve_pedido_de_identificacao(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho=Path(pasta)/'agenda.sqlite3'
            with Banco(caminho) as banco:
                banco.preparar_demo()
            ferramentas={f.name:f for f in criar_ferramentas_agenda(caminho,Contexto('demo','ana'))}
            resposta=ferramentas['buscar_cliente'].invoke({'termo':''})
            self.assertEqual(resposta['status'],'termo_necessario')

    def test_busca_e_disponibilidade_em_thread(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho=Path(pasta)/'agenda.sqlite3'
            ctx=Contexto('demo','bruno')
            with Banco(caminho) as banco:
                banco.preparar_demo()
                Agenda(banco).cadastrar_cliente(ctx,'Alfa Serviços')
                ferramentas={f.name:f for f in criar_ferramentas_agenda(caminho,ctx)}
                with ThreadPoolExecutor(max_workers=2) as executor:
                    busca=executor.submit(ferramentas['buscar_cliente'].invoke,{'termo':'Alfa'})
                    livre=executor.submit(ferramentas['consultar_disponibilidade'].invoke,
                        {'inicio_iso':'2026-11-11T14:00:00-03:00',
                         'fim_iso':'2026-11-11T15:00:00-03:00'})
                    self.assertEqual(busca.result()[0]['nome'],'Alfa Serviços')
                    self.assertTrue(livre.result()['sem_conflito_registrado'])

    def test_cnpj_existente_nao_chama_api_externa(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho=Path(pasta)/'agenda.sqlite3'
            ctx=Contexto('demo','ana')
            with Banco(caminho) as banco:
                banco.preparar_demo()
                Agenda(banco).cadastrar_cliente(ctx,'Empresa Exemplo','PJ','33683111000280')
            with patch('secretaria.agenda.consultar_cnpj',side_effect=AssertionError('API não deve ser chamada')):
                ferramentas={f.name:f for f in criar_ferramentas_agenda(caminho,ctx)}
                with ThreadPoolExecutor(max_workers=1) as executor:
                    futuro=executor.submit(ferramentas['consultar_cnpj_minha_receita'].invoke,
                                          {'cnpj':'33683111000280'})
                    resposta=futuro.result()
            self.assertEqual(resposta['status'],'ja_cadastrado')
            self.assertFalse(resposta['api_externa_chamada'])
            self.assertEqual(resposta['cliente']['nome'],'Empresa Exemplo')

    def test_cnpj_ausente_consulta_mas_nao_cadastra(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho=Path(pasta)/'agenda.sqlite3'
            ctx=Contexto('demo','ana')
            with Banco(caminho) as banco:
                banco.preparar_demo()
            consulta={'origem':'fixture_local','cnpj':'33683111000280','razao_social':'Empresa Exemplo'}
            with patch('secretaria.agenda.consultar_cnpj',return_value=consulta) as api:
                ferramentas={f.name:f for f in criar_ferramentas_agenda(caminho,ctx)}
                resposta=ferramentas['consultar_cnpj_minha_receita'].invoke({'cnpj':'33683111000280'})
            api.assert_called_once_with('33683111000280')
            self.assertEqual(resposta['status'],'nao_cadastrado')
            with Banco(caminho) as banco:
                self.assertEqual(banco.con.execute('SELECT COUNT(*) FROM clientes').fetchone()[0],0)


if __name__=='__main__':
    unittest.main()
