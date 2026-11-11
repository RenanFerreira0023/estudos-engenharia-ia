"""Plano tipado e SELECT restrito; nenhuma chamada de LLM neste teste."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from secretaria.banco import Banco, Contexto
from secretaria.consulta_estruturada import (PlanoConsultaMensagens,
                                            executar_plano, planejar_consulta)
from secretaria.agente_agenda import criar_ferramentas_agenda


class ModeloFixture:
    def with_structured_output(self, esquema, method):
        assert esquema is PlanoConsultaMensagens and method == 'json_schema'
        return self

    def invoke(self, mensagens):
        assert 'SQL' in mensagens[0][1]
        return {'tipo':'contagem','autor':'Bruno','termos':['orçamento','Alfa']}


class ConsultaEstruturadaTest(unittest.TestCase):
    def test_pergunta_plano_sql_parametrizado_e_resultado(self):
        with tempfile.TemporaryDirectory() as pasta:
            with Banco(Path(pasta)/'demo.sqlite3') as banco:
                banco.preparar_demo()
                ana, bruno = Contexto('demo','ana'), Contexto('demo','bruno')
                corpus = banco.selecionar_corpus(ana,'Demonstração fictícia')
                banco.importar(ana,corpus,Path(__file__).resolve().parents[1] /
                              'dados/ficticios/conversa_empresa.txt')
                plano = planejar_consulta(
                    'Quantas mensagens de Bruno mencionam orçamento e Alfa?',ModeloFixture())
                resultado = executar_plano(banco,ana,corpus,plano)
                self.assertEqual(resultado['total'],1)
                self.assertIn('COUNT(*)',resultado['sql_executado'])
                self.assertNotIn('Alfa',resultado['sql_executado'])
                self.assertIn('%Alfa%',resultado['parametros_sql'])
                self.assertEqual(executar_plano(banco,ana,corpus,{
                    'tipo':'lista','autor':'Bruno','termos':['orçamento','Alfa'],
                    'limite':1})['mensagens'][0]['id'],4)
                with self.assertRaises(PermissionError):
                    executar_plano(banco,bruno,corpus,plano)

    def test_periodo_local_e_termo_nao_viram_sql_livre(self):
        with tempfile.TemporaryDirectory() as pasta:
            with Banco(Path(pasta)/'demo.sqlite3') as banco:
                banco.preparar_demo()
                ana = Contexto('demo','ana')
                corpus = banco.selecionar_corpus(ana,'Demonstração fictícia')
                banco.importar(ana,corpus,Path(__file__).resolve().parents[1] /
                              'dados/ficticios/conversa_empresa.txt')
                periodo = executar_plano(banco,ana,corpus,{
                    'tipo':'contagem','data_inicio_local':'2026-11-09',
                    'data_fim_local_exclusiva':'2026-11-10'})
                self.assertEqual(periodo['total'],40)
                self.assertIn('2026-11-09T03:00:00+00:00',periodo['parametros_sql'])
                injetado = executar_plano(banco,ana,corpus,{
                    'tipo':'contagem','termos':["Alfa%' OR 1=1 --"]})
                self.assertEqual(injetado['total'],0)
                self.assertNotIn('OR 1=1',injetado['sql_executado'])
                with self.assertRaises(ValueError):
                    PlanoConsultaMensagens(tipo='lista',limite=1000)
                with self.assertRaises(ValueError):
                    PlanoConsultaMensagens(tipo='contagem',data_inicio_local='2026-11-10',
                                          data_fim_local_exclusiva='2026-11-09')

    def test_ferramenta_do_agente_respeita_autorizacao(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta)/'demo.sqlite3'
            with Banco(caminho) as banco:
                banco.preparar_demo()
                ana = Contexto('demo','ana')
                corpus = banco.selecionar_corpus(ana,'Demonstração fictícia')
                banco.importar(ana,corpus,Path(__file__).resolve().parents[1] /
                              'dados/ficticios/conversa_empresa.txt')
            with patch('secretaria.agente_agenda.obter_chave_api',return_value='chave-fixture'), \
                 patch('langchain_openai.ChatOpenAI',return_value=ModeloFixture()):
                ferramentas = criar_ferramentas_agenda(caminho,ana)
                consulta = next(f for f in ferramentas if f.name=='consultar_mensagens_estruturado')
                resposta = consulta.invoke({'corpus_id':corpus,'pergunta':'Quantas mensagens de Bruno mencionam orçamento e Alfa?'})
                self.assertEqual(resposta['total'],1)
                bruno = Contexto('demo','bruno')
                outra = next(f for f in criar_ferramentas_agenda(caminho,bruno)
                             if f.name=='consultar_mensagens_estruturado')
                self.assertEqual(outra.invoke({'corpus_id':corpus,'pergunta':'Quantas mensagens?'}),
                                 {'status':'acesso_negado'})


if __name__ == '__main__':
    unittest.main()
