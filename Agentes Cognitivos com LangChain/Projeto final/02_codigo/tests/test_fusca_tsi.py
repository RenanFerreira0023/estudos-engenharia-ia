"""Recortes Fusca clássico/TSI, fonte técnica e ausência de aplicações copiadas."""
import json
from pathlib import Path
from contextvars import ContextVar
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from auto_super_parts.catalogo_fase02 import Catalogo
from auto_super_parts.agente_fase02 import criar_ferramentas
from auto_super_parts.viacep import criar_cliente_dummy
from auto_super_parts.consultas_complementares import consultar_tecnica
from auto_super_parts.planos_consulta import consultar_catalogo_planejado


class FuscaTSITest(unittest.TestCase):
    def setUp(self):
        self.c=Catalogo();self.addCleanup(self.c.fechar)
        self.pedido=ContextVar('teste_fusca_tsi',default='')
        self.tools={t.name:t for t in criar_ferramentas(self.c,criar_cliente_dummy(),self.pedido)}

    def test_dois_recortes_separados_sem_transferir_produtos(self):
        fuscas=[v for v in self.c.listar_veiculos()['veiculos'] if v['modelo']=='Fusca']
        self.assertEqual({v['id'] for v in fuscas},{'V004','V006'})
        self.assertEqual(self.c.consultar(veiculo_id='V006')['produtos'],[])
        self.assertEqual(self.c.consultar(produto_id='P021',veiculo_id='V006')['produtos'],[])
        self.assertEqual(self.c.consultar(produto_id='P021',veiculo_id='V004')['produtos'][0]['preco_centavos'],1490)
        self.pedido.set('Posso usar a P021 nele?')
        r=self.tools['consultar_catalogo'].invoke({'produto_id':'P021','veiculo_id':'V006','categoria':'vela'})
        self.assertEqual(r['produtos'],[])
        self.assertEqual(r['referencia_consulta']['veiculo_id'],'V006')
        self.assertIn('JOIN',r['sql_executado'][0]['sql'])
        self.assertEqual(r['status'],'aplicacao_nao_cadastrada')
        self.assertEqual(r['produto_cadastrado']['id'],'P021')
        self.assertEqual({a['veiculo_id'] for a in r['aplicacoes_cadastradas']},{'V004'})
        self.assertNotIn('preco_centavos',r['produto_cadastrado'])

    def test_so_fusca_pergunta_em_vez_de_escolher_classico_ou_tsi(self):
        self.pedido.set('Quanto custa uma vela para meu Fusca?')
        for vid in ('V004','V006'):
            r=self.tools['consultar_catalogo'].invoke({'veiculo_id':vid,'categoria':'vela'})
            self.assertEqual(r['status'],'veiculo_ambiguo')
            self.assertEqual({v['id'] for v in r['veiculos_referenciados']},{'V004','V006'})
            self.assertNotIn('sql_executado',r)

    def test_ano_geracao_e_id_nao_sao_intercambiaveis(self):
        for pedido,errado,correto in [('Fusca TSI 2014','V004','V006'),('Fusca a ar 1982','V006','V004')]:
            self.pedido.set(pedido)
            r=self.tools['consultar_catalogo'].invoke({'veiculo_id':errado,'categoria':'vela'})
            self.assertEqual(r['status'],'referencia_veiculo_divergente')
            r=self.tools['consultar_catalogo'].invoke({'veiculo_id':correto,'categoria':'vela'})
            self.assertEqual(r['referencia_consulta']['veiculo_id'],correto)
        self.pedido.set('Fusca TSI 2015')
        r=self.tools['consultar_catalogo'].invoke({'veiculo_id':'V006','categoria':'vela'})
        self.assertEqual(r['status'],'configuracao_nao_cadastrada')

    def test_nao_usa_peca_do_classico_em_orcamento_tsi(self):
        self.pedido.set('Tenho Fusca TSI 2014 2.0 gasolina. Quero 1 vela para retirada.')
        r=self.tools['calcular_orcamento'].invoke({'itens':[{'produto_id':'P021','quantidade':1}],'modalidade':'retirada'})
        self.assertEqual(r['status'],'produto_de_outro_veiculo')

    def test_fonte_de_arrefecimento_e_lacunas_de_oleo_separadas(self):
        self.pedido.set('Fusca TSI 2014 2.0 gasolina. Como e o arrefecimento?')
        r=self.tools['consultar_informacao_tecnica'].invoke({'veiculo_id':'V006','assunto':'arrefecimento'})
        self.assertEqual(r['status'],'informacao_disponivel')
        self.assertEqual(r['informacoes'][0]['dados']['tipo'],'liquido')
        self.assertEqual(r['fontes'][0]['id'],'SRC08')
        self.assertIsNone(r['informacoes'][0]['dados']['codigo_bomba_agua'])
        r=self.tools['consultar_informacao_tecnica'].invoke({'veiculo_id':'V004','assunto':'arrefecimento'})
        self.assertEqual(r['status'],'referencia_veiculo_divergente')
        self.assertEqual(consultar_tecnica('V006','oleo')['status'],'informacao_pendente')
        self.assertEqual(consultar_tecnica('V004','arrefecimento')['informacoes'][0]['dados']['tipo'],'ar')
        from auto_super_parts.contexto_comercial import atualizar_contexto_comercial
        r=consultar_tecnica('V006','arrefecimento')
        c=atualizar_contexto_comercial({'veiculo_do_pedido':'V004','produtos_consultados':[{'id':'P021'}]},
            [{'tipo':'tool','ferramenta':'consultar_informacao_tecnica','conteudo':json.dumps(r)}])
        self.assertEqual(c['veiculo_do_pedido'],'V006')
        self.assertNotIn('produtos_consultados',c)

    def test_query_reconhece_id_novo_mas_nao_adivinha_recorte_generico(self):
        plano={'consulta_valida':True,'veiculo_id':'V006','categoria':'vela','estoque':'qualquer',
               'preco_max_centavos':None,'ordenacao':'id','limite':10,'pendencias':[]}
        r=consultar_catalogo_planejado(self.c,'vela para Fusca',lambda _:plano)
        self.assertEqual(r['status'],'veiculo_ambiguo')
        r=consultar_catalogo_planejado(self.c,'vela para V006',lambda _:plano)
        self.assertEqual(r['status'],'sem_resultados')
        self.assertIn('V006',r['parametros_sql'])

    def test_comparacao_explicita_permite_consultar_as_duas_geracoes(self):
        self.pedido.set('Qual diferenca entre Fusca a ar e Fusca TSI?')
        for vid in ('V004','V006'):
            r=self.tools['consultar_informacao_tecnica'].invoke({'veiculo_id':vid,'assunto':'arrefecimento'})
            self.assertEqual(r['status'],'informacao_disponivel')

    def test_protecao_de_oleo_nao_apaga_pergunta_de_geracao(self):
        from auto_super_parts.consultas_complementares import conferir_resposta
        r,a=conferir_resposta('Qual oleo devo usar no Fusca?',[],'Use 20W-60.',catalogo=self.c)
        self.assertIn('clássico a ar ou o TSI',r)
        self.assertIn('ano e motor',r)
        self.assertNotIn('20W',r)
        self.assertEqual(a['regra'],'esclarecer_geracao_antes_da_especificacao')

        from langchain_core.messages import ToolMessage
        _,audit=conferir_resposta('Qual oleo devo usar no Fusca?',
            [ToolMessage(content='{}',name='consultar_informacao_tecnica',tool_call_id='teste')],
            'Use 20W-60.',catalogo=self.c)
        self.assertTrue(audit['consulta_tecnica_executada'])

    def test_pergunta_ambigua_e_controlada_sem_chamar_modelo_ou_juiz(self):
        import tempfile
        from langchain_core.messages import AIMessage
        from auto_super_parts.memoria import MemoriaSQLite
        from auto_super_parts.atendimento_verificado import AtendimentoVerificado
        from auto_super_parts.verificacao import VerificadorResposta
        from test_memoria import ModeloObservador
        from test_verificacao import RAGFixture
        with tempfile.TemporaryDirectory() as tmp:
            mem=MemoriaSQLite(Path(tmp)/'m.sqlite3');s=mem.abrir_sessao('a')
            modelo=ModeloObservador(responses=[AIMessage(content='Use a vela do classico.')])
            def nao_chamar(p):
                raise AssertionError('Nao chamar LLM para pergunta controlada')
            sistema=AtendimentoVerificado(mem,modelo=modelo,rag=RAGFixture(),planejador=lambda p:{},
                verificador=VerificadorResposta(nao_chamar,nao_chamar))
            try:
                r=sistema.atender('a',s,'Quanto custa a vela do Fusca?',salvar=False)
                self.assertEqual(r['verificacao_geral']['status'],'identificacao_pendente')
                self.assertFalse(r['geracao_executada'])
                self.assertFalse(modelo.entradas)
                self.assertIn('TSI',r['resposta'])
                self.assertIn('1600 a ar',r['resposta'])
                self.assertEqual(mem.historico('a',s)[-1]['content'],r['resposta'])
            finally:
                sistema.fechar();mem.fechar()

    def test_declaracao_tsi_e_nele_nao_retornam_ao_perfil_classico(self):
        import tempfile
        from langchain_core.messages import AIMessage
        from auto_super_parts.memoria import MemoriaSQLite
        from auto_super_parts.atendimento_memoria import AtendimentoComMemoria
        from test_memoria import ModeloObservador
        with tempfile.TemporaryDirectory() as tmp:
            mem=MemoriaSQLite(Path(tmp)/'m.sqlite3');s=mem.abrir_sessao('a')
            mem.confirmar_veiculo('a',next(v for v in self.c.listar_veiculos()['veiculos'] if v['id']=='V004'))
            modelo=ModeloObservador(responses=[AIMessage(content='Entendi a referencia TSI.'),
                AIMessage(content='',tool_calls=[{'name':'consultar_catalogo','args':{'produto_id':'P021','veiculo_id':'V004','categoria':'vela'},'id':'errado'}]),
                AIMessage(content='',tool_calls=[{'name':'consultar_catalogo','args':{'produto_id':'P021','veiculo_id':None,'categoria':'vela'},'id':'omitido'}]),
                AIMessage(content='Nao tenho aplicacao confirmada para o TSI.')])
            sistema=AtendimentoComMemoria(mem,modelo=modelo)
            try:
                sistema.atender('a',s,'E o Fusca TSI 2014 2.0 gasolina.',salvar=False)
                self.assertEqual(mem.contexto_atendimento('a',s)['veiculo_do_pedido'],'V006')
                r=sistema.atender('a',s,'Posso usar a vela P021 nele?',salvar=False)
                self.assertEqual(r['referencia_relativa_validada'],'V006')
                tools=[json.loads(m['conteudo']) for m in r['trajetoria'] if m.get('tipo')=='tool']
                self.assertEqual(tools[0]['status'],'referencia_veiculo_divergente')
                self.assertEqual(tools[1]['produtos'],[])
                self.assertEqual(tools[1]['referencia_consulta']['veiculo_id'],'V006')
                self.assertEqual(mem.perfil('a')['veiculo_confirmado']['id'],'V004')
            finally:
                sistema.fechar();mem.fechar()

    def test_id_declarado_nao_desaparece_do_plano(self):
        plano={'consulta_valida':True,'veiculo_id':None,'categoria':'vela','estoque':'qualquer',
               'preco_max_centavos':None,'ordenacao':'id','limite':10,'pendencias':[]}
        r=consultar_catalogo_planejado(self.c,'Quero vela para V006',lambda _:plano)
        self.assertEqual(r['status'],'sem_resultados')
        self.assertEqual(r['plano']['veiculo_id'],'V006')
        self.assertIsNone(r['plano_gerado']['veiculo_id'])

    def test_politica_geral_nao_exige_escolher_fusca(self):
        from auto_super_parts.referencia_veiculo import identificacao_pendente
        self.assertIsNone(identificacao_pendente(self.c,'Qual a garantia das pecas do Fusca?'))
        self.assertIsNone(identificacao_pendente(self.c,'Posso pagar as velas do Fusca com Pix?'))
