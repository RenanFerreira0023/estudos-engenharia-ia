"""Contratos e fluxo com modelos roteirizados: não substituem teste real de LLM."""
import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from pydantic import ValidationError
from langchain_core.messages import AIMessage
from auto_super_parts.catalogo_fase02 import Catalogo
from auto_super_parts.brasilapi import ClienteBrasilAPI
from auto_super_parts.planos_consulta import PlanoCatalogo,consultar_catalogo_planejado
from auto_super_parts.orcamento_fase02 import calcular_orcamento
from auto_super_parts.atendimento_verificado import AtendimentoVerificado
from auto_super_parts.memoria import MemoriaSQLite
from auto_super_parts.verificacao import VerificadorResposta
from test_rag_query import plano
from test_verificacao import RAGFixture,parecer
from test_correcao_fase02 import ModeloRoteirizado

class MultiplosProdutosTest(unittest.TestCase):
    def setUp(self):
        self.catalogo=Catalogo();self.addCleanup(self.catalogo.fechar)

    def test_correia_e_filtro_retorna_ambos_no_celta(self):
        r=consultar_catalogo_planejado(self.catalogo,'Correia de acessórios e filtro de óleo para Celta 2012 1.0 8V flex',
            lambda _:plano(veiculo_id='V003',categoria=['correia_acessorios','filtro_oleo']))
        self.assertEqual(r['status'],'ok')
        self.assertEqual([p['id'] for p in r['produtos']],['P013','P017'])
        self.assertEqual(r['parametros_sql'],['V003','correia_acessorios','filtro_oleo',10])
        self.assertIn('IN (?,?)',r['sql_executado'])
        orcamento=calcular_orcamento(self.catalogo,[{'produto_id':p['id'],'quantidade':1} for p in r['produtos']],
            'entrega','Curitiba','PR')
        self.assertEqual(orcamento['total_centavos'],5480)
        self.assertEqual(orcamento['frete_centavos'],0)

    def test_lista_nao_duplica_grupo_e_categoria(self):
        r=consultar_catalogo_planejado(self.catalogo,'Quais correias e filtros de óleo tem?',
            lambda _:plano(categoria=['correias','correia_acessorios','filtro_oleo']))
        self.assertEqual(r['parametros_sql'],['correia_dentada','correia_acessorios','filtro_oleo',10])
        self.assertTrue(all(p['categoria'] in ('correia_dentada','correia_acessorios','filtro_oleo') for p in r['produtos']))

    def test_rejeita_categoria_arbitraria_lista_vazia_e_sql(self):
        for categorias in ([],['filtro'],['filtro_oleo',"vela' OR 1=1 --"],['vela']*11):
            with self.assertRaises(ValidationError):
                PlanoCatalogo.model_validate(plano(categoria=categorias))

    def test_ambiguidade_de_filtro_continua_pendente(self):
        r=consultar_catalogo_planejado(self.catalogo,'correia e filtro para o Celta',
            lambda _:plano(consulta_valida=False,veiculo_id='V003',categoria=None,pendencias=['Qual tipo de filtro?']))
        self.assertEqual(r['status'],'consulta_pendente')
        self.assertNotIn('sql_executado',r)

    def test_agente_chama_orcamento_com_os_dois_produtos(self):
        modelo=ModeloRoteirizado(responses=[AIMessage(content='',tool_calls=[{'name':'consultar_cep','args':{'cep':'81910160'},'id':'cep'}]),AIMessage(content='',tool_calls=[{'name':'consultar_catalogo_estruturado',
            'args':{'pergunta':'correia de acessórios e filtro de óleo para Celta 2012 1.0 8V flex'},'id':'multi'}]),
            AIMessage(content='',tool_calls=[{'name':'calcular_orcamento','args':{'itens':[{'produto_id':'P013','quantidade':1},
            {'produto_id':'P017','quantidade':1}],'modalidade':'entrega','municipio':'Curitiba','uf':'PR'},'id':'orcamento'}]),
            AIMessage(content='Filtro: R$ 24,90. Correia: R$ 29,90. Frete: R$ 0,00. Total: R$ 54,80. Prazo pendente.')])
        with tempfile.TemporaryDirectory() as pasta:
            m=MemoriaSQLite(Path(pasta)/'mem.sqlite3')
            s=AtendimentoVerificado(m,modelo=modelo,rag=RAGFixture(),cliente_cep=ClienteBrasilAPI(lambda u,t:(200,json.dumps({'cep':'81910160','city':'Curitiba','state':'PR','location':{'coordinates':{'latitude':-25.4,'longitude':-49.2}}}))),
                planejador=lambda _:plano(veiculo_id='V003',categoria=['correia_acessorios','filtro_oleo']),
                verificador=VerificadorResposta(lambda p:parecer(p),lambda p:''))
            try:
                r=s.atender('multi',m.abrir_sessao('multi'),'Quero 1 correia de acessórios e 1 filtro de óleo para Celta 2012 1.0 8V flex, entrega no CEP 81910-160 Curitiba PR. Calcule o pedido.',salvar=False)
                self.assertEqual(r['verificacao_geral']['status'],'aprovada')
                retorno=json.loads(next(t['conteudo'] for t in r['trajetoria'] if t.get('ferramenta')=='calcular_orcamento'))
                self.assertEqual({i['produto_id'] for i in retorno['itens']},{'P013','P017'})
                self.assertEqual(retorno['total_centavos'],5480)
            finally:
                s.fechar();m.fechar()

if __name__=='__main__':
    unittest.main()
