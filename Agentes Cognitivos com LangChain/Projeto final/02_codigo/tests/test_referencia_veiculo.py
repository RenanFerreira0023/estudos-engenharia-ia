"""Regressões de veículo/produto a partir de falhas reais; sem API."""
import json
from pathlib import Path
from contextvars import ContextVar
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from auto_super_parts.agente_fase02 import criar_ferramentas
from auto_super_parts.catalogo_fase02 import Catalogo
from auto_super_parts.contexto_comercial import atualizar_contexto_comercial
from auto_super_parts.planos_consulta import consultar_catalogo_planejado
from auto_super_parts.viacep import criar_cliente_dummy
from auto_super_parts.verificacao import VerificadorResposta
from auto_super_parts.casos_verificacao import montar_casos
from test_verificacao import parecer


class ReferenciaVeiculoTest(unittest.TestCase):
    def setUp(self):
        self.c=Catalogo()
        self.addCleanup(self.c.fechar)
        self.pedido=ContextVar('pedido_referencia',default='')
        self.tools={t.name:t for t in criar_ferramentas(self.c,criar_cliente_dummy(),self.pedido)}

    def test_fusca_nao_consulta_celta_e_oferece_so_recortes_do_modelo_solicitado(self):
        self.pedido.set('me fala o valor da vela do fusca a ar')
        r=self.tools['consultar_catalogo'].invoke({'veiculo_id':'V003','categoria':'vela'})
        self.assertEqual(r['status'],'referencia_veiculo_divergente')
        self.assertEqual(r['produtos'],[])
        self.assertEqual([v['id'] for v in r['veiculos_referenciados']],['V004'])
        self.assertNotIn('sql_executado',r)
        r=self.tools['consultar_catalogo'].invoke({'veiculo_id':'V004','categoria':'vela'})
        self.assertEqual(r['produtos'][0]['id'],'P021')
        self.assertEqual(r['produtos'][0]['preco_centavos'],1490)
        self.assertEqual(r['produtos'][0]['estoque'],0)

    def test_id_de_veiculo_explicito_nao_vira_produto(self):
        self.pedido.set('passa o valor da vela V004')
        r=self.tools['consultar_catalogo'].invoke({'produto_id':'V004','veiculo_id':'V003','categoria':'vela'})
        self.assertEqual(r['status'],'ok')
        self.assertEqual(r['produtos'][0]['id'],'P021')
        self.assertEqual(r['referencia_consulta'],{'produto_id':None,'veiculo_id':'V004'})
        self.assertEqual(r['sql_executado'][0]['parametros'],['V004','vela'])
        self.assertTrue(r['ajustes_identificadores'])

    def test_nao_adivinha_peca_para_id_de_veiculo(self):
        self.pedido.set('Quanto custa V004?')
        r=self.tools['consultar_catalogo'].invoke({'produto_id':'V004','categoria':None})
        self.assertEqual(r['status'],'categoria_pendente')
        self.pedido.set('Quero uma vela')
        r=self.tools['consultar_catalogo'].invoke({'produto_id':'V004','categoria':'vela'})
        self.assertEqual(r['status'],'identificador_de_veiculo_em_produto')

    def test_outros_modelos_cadastrados_tambem_sao_conferidos(self):
        for modelo,vid in [('Palio','V002'),('Gol','V001'),('S10','V005')]:
            self.pedido.set('Quero uma peca para '+modelo)
            r=self.tools['consultar_catalogo'].invoke({'veiculo_id':'V003','categoria':'vela'})
            self.assertEqual(r['status'],'referencia_veiculo_divergente')
            self.assertEqual([v['id'] for v in r['veiculos_referenciados']],[vid])

    def test_produto_adivinhado_de_outro_modelo_nao_vira_orcamento(self):
        self.pedido.set('Tenho um Fusca 1982 1600 a ar gasolina. Quero 2 velas para retirada.')
        r=self.tools['calcular_orcamento'].invoke({'itens':[{'produto_id':'P015','quantidade':2}],'modalidade':'retirada'})
        self.assertEqual(r['status'],'produto_de_outro_veiculo')
        self.assertEqual(r['produtos'],[])

    def test_query_usa_pedido_real_em_vez_de_parafrase_sem_veiculo(self):
        plano={'consulta_valida':True,'veiculo_id':'V003','categoria':'vela','estoque':'qualquer',
               'preco_max_centavos':None,'ordenacao':'id','limite':10,'pendencias':[]}
        r=consultar_catalogo_planejado(self.c,'Quero velas',lambda _:plano,referencia_pedido='Qual o valor da vela do Fusca?')
        self.assertEqual(r['status'],'referencia_veiculo_divergente')
        self.assertNotIn('sql_executado',r)

    def test_estado_aprende_referencia_efetiva_e_nao_argumento_antigo(self):
        self.pedido.set('passa o valor da vela V004')
        r=self.tools['consultar_catalogo'].invoke({'produto_id':'V004','veiculo_id':'V003','categoria':'vela'})
        trajetoria=[{'tipo':'ai','tool_calls':[{'id':'t','name':'consultar_catalogo','args':{'produto_id':'V004','veiculo_id':'V003'}}]},
                    {'tipo':'tool','ferramenta':'consultar_catalogo','tool_call_id':'t','conteudo':json.dumps(r)}]
        self.assertEqual(atualizar_contexto_comercial({},trajetoria)['veiculo_do_pedido'],'V004')
        self.pedido.set('Calcule 7 unidades P009 para retirada.')
        r=self.tools['consultar_catalogo'].invoke({'produto_id':'P009','veiculo_id':'V003'})
        trajetoria[-1]['conteudo']=json.dumps(r)
        self.assertNotIn('veiculo_do_pedido',atualizar_contexto_comercial({'veiculo_do_pedido':'V003'},trajetoria))

    def test_acento_de_citacao_nao_muda_palavras_nem_valores(self):
        r=next(c['resultado'] for c in montar_casos() if c['id']=='orcamento_correto')
        r['resposta']='Não houve reserva. Total: R$ 118,30.'
        def juiz(p):
            d=parecer(p);d['afirmacoes'][0]['trecho']='Nao houve reserva. Total: R$ 118,30.';return d
        v=VerificadorResposta(juiz,lambda p:'')
        self.assertTrue(v.avaliar(r,r['resposta'])['aprovada'])
        for alteracao in ('Não houve reserva. Total: R$ 118,31.','Não houve compra. Total: R$ 118,30.'):
            self.assertFalse(v.avaliar(r,alteracao)['aprovada'])
