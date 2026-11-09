"""BrasilAPI, geodesia e isolamento com HTTP/modelos injetados; sem chamadas reais."""
import json,math,sys,unittest
from pathlib import Path
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from langchain_core.messages import AIMessage
from auto_super_parts.brasilapi import ClienteBrasilAPI,coordenadas_validas
from auto_super_parts.distancia_entrega import distancia_linha_reta,consultar_entrega_geografica
from auto_super_parts.agente_fase02 import criar_ferramentas,AtendimentoFase02
from auto_super_parts.catalogo_fase02 import Catalogo
from test_correcao_fase02 import ModeloRoteirizado


def dados(cep='01002020',city='São Paulo',state='SP',coords=None):
    return {'cep':cep,'city':city,'state':state,'street':'Rua de teste','neighborhood':'Centro',
            'service':'fixture','location':{'type':'Point','coordinates':coords or {'latitude':'-23.5475','longitude':'-46.63611'}}}


def cliente(d=None):
    return ClienteBrasilAPI(transporte=lambda u,t:(200,json.dumps(d or dados())))


class BrasilAPIEntregaTest(unittest.TestCase):
    def test_endereco_coordenadas_zero_inicial_e_url_fixa(self):
        chamadas=[]
        c=ClienteBrasilAPI(lambda u,t:(chamadas.append(u) or 200,json.dumps(dados())))
        r=c.consultar('01002-020')
        self.assertEqual(r['status'],'ok')
        self.assertEqual(r['endereco']['localidade'],'São Paulo')
        self.assertEqual(r['coordenadas'],{'latitude':-23.5475,'longitude':-46.63611})
        self.assertEqual(chamadas,['https://brasilapi.com.br/api/cep/v2/01002020'])
        self.assertFalse(r['tentativa_http_real'])
        c.consultar('01002020')
        self.assertEqual(len(chamadas),1)

    def test_entrada_invalida_nao_chama_http(self):
        c=ClienteBrasilAPI(lambda u,t:self.fail('HTTP não deveria executar'))
        for cep in ('../../etc','1002020',1002020,'01002020?host=x'):
            self.assertEqual(c.consultar(cep)['status'],'cep_invalido')

    def test_endereco_sem_coordenadas_nao_vira_erro_de_endereco(self):
        d=dados();d['location']={'coordinates':{}}
        r=cliente(d).consultar('01002020')
        self.assertEqual(r['status'],'ok')
        self.assertIsNone(r['coordenadas'])
        entrega=consultar_entrega_geografica(r,'São Paulo','SP')
        self.assertEqual(entrega['status'],'coordenadas_pendentes')
        self.assertIsNone(entrega['frete_centavos'])

    def test_coordenadas_invalidas_e_nan(self):
        for coords in ({'latitude':True,'longitude':0},{'latitude':91,'longitude':0},
                       {'latitude':0,'longitude':181},{'latitude':'NaN','longitude':0},
                       {'latitude':float('inf'),'longitude':0}):
            self.assertIsNone(coordenadas_validas(coords))
        with self.assertRaises(ValueError):
            distancia_linha_reta({}, {})

    def test_falhas_http_timeout_e_json_sem_fallback(self):
        for transporte,status in ((lambda u,t:(404,'{}'),'cep_nao_encontrado'),
                                  (lambda u,t:(429,'{}'),'erro_http'),
                                  (lambda u,t:(200,'x'),'resposta_invalida'),
                                  (lambda u,t:(200,json.dumps(dados(cep='99999999'))),'resposta_invalida')):
            self.assertEqual(ClienteBrasilAPI(transporte).consultar('01002020')['status'],status)
        def falhar(u,t):raise TimeoutError()
        self.assertEqual(ClienteBrasilAPI(falhar).consultar('01002020')['status'],'timeout')

    def test_haversine_identidade_simetria_e_um_grau(self):
        a={'latitude':0,'longitude':0};b={'latitude':0,'longitude':1}
        self.assertEqual(distancia_linha_reta(a,a),0)
        self.assertAlmostEqual(distancia_linha_reta(a,b),111.195,places=3)
        self.assertEqual(distancia_linha_reta(a,b),distancia_linha_reta(b,a))

    def test_sao_paulo_sem_tabela_tem_distancia_e_frete(self):
        r=consultar_entrega_geografica(cliente().consultar('01002020'),'São Paulo','SP')
        self.assertEqual(r['status'],'parcial')
        self.assertTrue(300<r['distancia_km']<400)
        self.assertGreater(r['frete_centavos'],0)
        self.assertEqual(r['metodo_distancia'],'haversine_linha_reta')
        self.assertNotIn('distancia_km_simulada',r)

    def test_curitiba_gratis_mesmo_sem_coordenadas(self):
        d=dados(cep='81910160',city='Curitiba',state='PR');d['location']={}
        r=consultar_entrega_geografica(cliente(d).consultar('81910160'),'Curitiba','PR')
        self.assertEqual(r['frete_centavos'],0)
        self.assertIsNone(r['prazo_dias_uteis'])

    def test_destino_divergente_e_falta_cep_nao_cotam(self):
        r=cliente().consultar('01002020')
        self.assertEqual(consultar_entrega_geografica(r,'Salvador','BA')['status'],'destino_divergente')
        self.assertEqual(consultar_entrega_geografica(None,'São Paulo','SP')['status'],'destino_pendente')

    def test_tools_orcamento_usa_destino_http_sem_permitir_coordenadas_llm(self):
        catalogo=Catalogo();self.addCleanup(catalogo.fechar)
        fs={f.name:f for f in criar_ferramentas(catalogo,cliente())}
        self.assertEqual(fs['consultar_entrega'].invoke({'municipio':'São Paulo','uf':'SP'})['status'],'destino_pendente')
        fs['consultar_cep'].invoke({'cep':'01002020'})
        r=fs['calcular_orcamento'].invoke({'itens':[{'produto_id':'P013','quantidade':1},{'produto_id':'P017','quantidade':1}],
                                        'modalidade':'entrega','municipio':'São Paulo','uf':'SP'})
        self.assertEqual(r['subtotal_centavos'],5480)
        self.assertEqual(r['total_centavos'],5480+r['frete_centavos'])
        self.assertGreater(r['frete_centavos'],0)

    def test_calculo_antes_da_tool_cep_resolve_cep_declarado_e_registra_origem(self):
        from contextvars import ContextVar
        catalogo=Catalogo();self.addCleanup(catalogo.fechar)
        fs={f.name:f for f in criar_ferramentas(catalogo,cliente(),ContextVar('pedido_teste',default='Entrega no CEP 01002-020'))}
        r=fs['calcular_orcamento'].invoke({'itens':[{'produto_id':'P013','quantidade':1},{'produto_id':'P017','quantidade':1}],
                                        'modalidade':'entrega','municipio':'São Paulo','uf':'SP'})
        self.assertEqual(r['subtotal_centavos'],5480)
        self.assertGreater(r['frete_centavos'],0)
        self.assertEqual(r['total_centavos'],5480+r['frete_centavos'])
        self.assertEqual(r['consulta_cep']['cep'],'01002020')
        self.assertEqual(r['consulta_cep']['origem'],'brasilapi_transporte_injetado_teste')

    def test_destino_nao_vaza_entre_turnos_e_cep_inventado_nao_consulta(self):
        respostas=[AIMessage(content='',tool_calls=[{'name':'consultar_cep','args':{'cep':'01002020'},'id':'a'}]),AIMessage(content='Localizado.'),
                   AIMessage(content='',tool_calls=[{'name':'consultar_entrega','args':{'municipio':'São Paulo','uf':'SP'},'id':'b'}]),AIMessage(content='Informe o CEP.'),
                   AIMessage(content='',tool_calls=[{'name':'consultar_cep','args':{'cep':'40000000'},'id':'c'}]),AIMessage(content='Informe o CEP.')]
        s=AtendimentoFase02(modelo=ModeloRoteirizado(responses=respostas),cliente_cep=cliente())
        self.addCleanup(s.fechar)
        primeiro=s.atender('Meu CEP é 01002-020',salvar=False)
        segundo=s.atender('Qual o frete para São Paulo?',salvar=False)
        terceiro=s.atender('Quanto para centro da Bahia?',salvar=False)
        def retorno(r):return json.loads(next(t['conteudo'] for t in r['trajetoria'] if t.get('tipo')=='tool'))
        self.assertEqual(retorno(primeiro)['status'],'ok')
        self.assertEqual(retorno(segundo)['status'],'destino_pendente')
        self.assertEqual(retorno(terceiro)['status'],'cep_nao_informado')

if __name__=='__main__':unittest.main()
