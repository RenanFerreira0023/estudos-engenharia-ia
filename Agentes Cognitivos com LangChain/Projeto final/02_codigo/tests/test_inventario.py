"""Regressões de inventário: dados locais e SDK roteirizado, sem acesso à API."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import httpx
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from auto_super_parts.atendimento_rag import AtendimentoRAG, catalogo_precisa_consulta
from auto_super_parts.catalogo_fase02 import Catalogo
from auto_super_parts.memoria import MemoriaSQLite
from auto_super_parts.planos_consulta import consultar_catalogo_planejado
from auto_super_parts.viacep import criar_cliente_dummy
from test_rag_query import plano
from test_verificacao import RAGFixture

class InventarioTest(unittest.TestCase):
    def setUp(self):
        self.catalogo=Catalogo()
        self.addCleanup(self.catalogo.fechar)

    def test_listar_tudo_nao_exige_categoria_preserva_plano_bruto(self):
        pergunta='Liste todos os produtos cadastrados para o Fusca 1982 1600 a ar.'
        r=consultar_catalogo_planejado(self.catalogo,pergunta,lambda _:plano(
            veiculo_id='V004',consulta_valida=False,pendencias=['Faltando filtros de categoria.']))
        self.assertEqual(r['status'],'ok')
        self.assertEqual([p['id'] for p in r['produtos']],['P019','P020','P021','P022','P023','P024'])
        self.assertFalse(r['plano_gerado']['consulta_valida'])
        self.assertTrue(r['plano']['consulta_valida'])
        self.assertEqual(r['parametros_sql'],['V004',10])

    def test_nao_remove_pendencia_de_motor_nem_pedido_fora_do_escopo(self):
        for pendencias in (['Qual ano e motor?'],['Faltando filtros de categoria.','Operação de exclusão proibida.']):
            r=consultar_catalogo_planejado(self.catalogo,'Liste todos os produtos',lambda _:plano(
                consulta_valida=False,pendencias=pendencias))
            self.assertEqual(r['status'],'consulta_pendente')
            self.assertNotIn('sql_executado',r)

    def test_grupo_correias_nao_inclui_outras_categorias(self):
        r=consultar_catalogo_planejado(self.catalogo,'Quais correias tem do Palio?',lambda _:plano(
            veiculo_id='V002',categoria='correias'))
        self.assertEqual([p['id'] for p in r['produtos']],['P011'])
        self.assertEqual(r['produtos'][0]['preco_centavos'],2990)
        self.assertEqual(r['parametros_sql'],['V002','correia_dentada','correia_acessorios',10])
        self.assertEqual(r['configuracoes_consultadas'][0]['ano_modelo'],2010)

    def test_todos_os_anos_nao_inventa_configuracoes(self):
        r=consultar_catalogo_planejado(self.catalogo,'Quais produtos tem do Gol? Todos os anos.',lambda _:plano(veiculo_id='V001'))
        self.assertEqual(len(r['produtos']),6)
        self.assertEqual([v['ano_modelo'] for v in r['configuracoes_consultadas']],[2010])
        self.assertFalse(r['limite_atingido'])

    def test_historico_nao_substitui_consulta_no_turno(self):
        mensagens=[HumanMessage(content='Quais produtos tem?'),ToolMessage(content='{}',name='consultar_catalogo_estruturado',tool_call_id='a'),
                   AIMessage(content='Velas.'),HumanMessage(content='Quais correias tem do Palio?')]
        self.assertTrue(catalogo_precisa_consulta(mensagens))
        self.assertFalse(catalogo_precisa_consulta(mensagens+[ToolMessage(content='{}',name='consultar_catalogo_estruturado',tool_call_id='b')]))
        self.assertFalse(catalogo_precisa_consulta([HumanMessage(content='Quero 2 velas para meu carro.')]))

    def test_middleware_forca_consulta_uma_vez_no_sdk(self):
        pedidos=[]
        def http(request):
            corpo=json.loads(request.content); pedidos.append(corpo)
            if len(pedidos)==1:
                self.assertEqual(corpo['tool_choice']['function']['name'],'consultar_catalogo_estruturado')
                msg={'role':'assistant','content':None,'tool_calls':[{'id':'inventario','type':'function','function':{
                    'name':'consultar_catalogo_estruturado','arguments':json.dumps({'pergunta':'Quais correias tem do Palio?'})}}]}
                motivo='tool_calls'
            else:
                self.assertNotIsInstance(corpo.get('tool_choice'),dict)
                msg={'role':'assistant','content':'Palio 2010: correia de acessórios, R$ 29,90.'}; motivo='stop'
            return httpx.Response(200,json={'id':'fixture','object':'chat.completion','created':1,'model':'gpt-4o-mini',
                'choices':[{'index':0,'message':msg,'finish_reason':motivo}]})
        with tempfile.TemporaryDirectory() as pasta, httpx.Client(transport=httpx.MockTransport(http)) as cliente:
            modelo=ChatOpenAI(model='gpt-4o-mini',api_key='fixture-local-sem-rede',http_client=cliente,max_retries=0)
            memoria=MemoriaSQLite(Path(pasta)/'mem.sqlite3')
            sistema=AtendimentoRAG(memoria,modelo=modelo,cliente_cep=criar_cliente_dummy(),rag=RAGFixture(),
                planejador=lambda _:plano(veiculo_id='V002',categoria='correias'))
            try:
                sessao=memoria.abrir_sessao('inventario_fixture')
                r=sistema.atender('inventario_fixture',sessao,'Quais correias tem do Palio?',salvar=False)
                self.assertEqual(r['status'],'ok')
                retorno=json.loads(next(t['conteudo'] for t in r['trajetoria'] if t.get('ferramenta')=='consultar_catalogo_estruturado'))
                self.assertEqual(retorno['produtos'][0]['id'],'P011')
                self.assertEqual(len(pedidos),2)
            finally:
                sistema.fechar(); memoria.fechar()

if __name__=='__main__':
    unittest.main()
