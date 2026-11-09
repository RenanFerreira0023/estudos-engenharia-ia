"""Contratos/segurança e FAISS local com vetores e respostas roteirizados identificados."""
import json
import os
import re
from pathlib import Path
import shutil
import sys
import subprocess
import tempfile
import unittest
import httpx

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from langchain_core.messages import AIMessage,HumanMessage,ToolMessage
from pydantic import ValidationError
from langchain_openai import ChatOpenAI
from auto_super_parts.atendimento_rag import AtendimentoRAG,politica_precisa_consulta
from auto_super_parts.catalogo_fase02 import Catalogo
from auto_super_parts.configuracao import localizar_projeto
from auto_super_parts.memoria import MemoriaSQLite
from auto_super_parts.planos_consulta import PlanoBusca,PlanoCatalogo,consultar_catalogo_planejado
from auto_super_parts.rag_politicas import ErroIndice,PoliticasRAG,matriz_normalizada,preparar_indice
from auto_super_parts.viacep import criar_cliente_dummy
from test_correcao_fase02 import ModeloRoteirizado


class VetoresFixture:
    model='fixture-rag-quatro-dimensoes'
    def __init__(self):
        self.chamadas_documentos=0
        self.chamadas_consulta=0
    def vetor(self,texto):
        t=texto.lower()
        if t.startswith('pagamento:'): i=0
        elif t.startswith('entrega:'): i=1
        elif t.startswith('troca e garantia:'): i=2
        elif t.startswith('orçamento não confirma'): i=3
        elif re.search(r'\bentrega\b|\bfrete\b',t): i=1
        elif 'troca' in t or 'garantia' in t: i=2
        elif 'reserva' in t: i=3
        else: i=0
        return [float(n==i) for n in range(4)]
    def embed_documents(self,textos):
        self.chamadas_documentos+=1
        return [self.vetor(t) for t in textos]
    def embed_query(self,texto):
        self.chamadas_consulta+=1
        return self.vetor(texto)


def plano(**alteracoes):
    dados={'consulta_valida':True,'veiculo_id':None,'categoria':None,'estoque':'qualquer',
           'preco_max_centavos':None,'ordenacao':'id','limite':10,'pendencias':[]}
    return {**dados,**alteracoes}


class RAGTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pasta=Path(self.tmp.name)/'indice'
        self.fonte=Path(self.tmp.name)/'politicas_loja.txt'
        shutil.copy2(localizar_projeto()/'02_codigo/documentos/politicas_loja.txt',self.fonte)
        self.emb=VetoresFixture()
        self.manifesto=preparar_indice(self.emb,self.pasta,self.fonte,origem_embedding='fixture local, sem API')

    def carregar(self,**kwargs):
        return PoliticasRAG(self.emb,self.pasta,self.fonte,**kwargs)

    def test_indice_existente_carregado_sem_reindexar(self):
        rag=self.carregar()
        for _ in range(2):
            docs=rag.buscar('Posso pagar ao entregador?')
            self.assertEqual(docs[0]['id'],'POL-01')
            self.assertIn('não pagar ao entregador',docs[0]['texto'])
            self.assertEqual(docs[0]['fonte'],'politicas_loja.txt')
        self.assertEqual(self.emb.chamadas_documentos,1)
        self.assertEqual(self.emb.chamadas_consulta,2)

    def test_documento_mudou_indice_nao_e_usado(self):
        self.fonte.write_text(self.fonte.read_text(encoding='utf-8')+'\nAlterado.',encoding='utf-8')
        with self.assertRaises(ErroIndice):
            self.carregar()

    def test_indice_corrompido_nao_e_lista_vazia(self):
        (self.pasta/'politicas.faiss').write_bytes(b'corrompido')
        with self.assertRaises(ErroIndice):
            self.carregar()

    def test_modelo_incompativel_nao_e_usado(self):
        self.emb.model='outro_modelo'
        with self.assertRaises(ErroIndice):
            self.carregar()

    def test_indice_ausente_tem_instrucao_de_preparo(self):
        with self.assertRaisesRegex(ErroIndice,'preparar_politicas.py'):
            PoliticasRAG(self.emb,Path(self.tmp.name)/'ausente',self.fonte)

    def test_reescrita_composta_recupera_ambas_sem_repetir_ids(self):
        reescrever=lambda _:PlanoBusca(consultas=['pagamento cartão','entrega Curitiba'],assuntos_sem_documento=[])
        rag=self.carregar(reescrever=reescrever)
        r=rag.consultar('Cartão e frete de entrega em Curitiba?')
        self.assertEqual({d['id'] for d in r['documentos']},{'POL-01','POL-02'})
        self.assertEqual(len(r['documentos']),2)
        self.assertEqual(len(r['rastro_busca']),3)
        self.assertEqual(r['estrategia'],'decomposicao_multiquery')

    def test_assunto_ausente_nao_fabrica_documento(self):
        rag=self.carregar(reescrever=lambda _:PlanoBusca(consultas=[],assuntos_sem_documento=['horário']))
        r=rag.consultar('Qual o horário?')
        self.assertEqual(r['status'],'sem_evidencia')
        self.assertEqual(r['documentos'],[])
        self.assertEqual(self.emb.chamadas_consulta,0)

    def test_garantia_e_troca_tem_prazos_e_condicoes_distintos(self):
        d=self.carregar().buscar('Troca e garantia')[0]
        self.assertEqual(d['estado'],'documentado')
        self.assertIn('30 dias de garantia',d['texto'])
        self.assertIn('até 7 dias corridos',d['texto'])
        self.assertIn('sem uso e sem instalação',d['texto'])
        self.assertIn('defeito dentro dos 30 dias segue para avaliação',d['texto'])
        regras=json.loads((localizar_projeto()/'02_codigo/dados/loja_regras.json').read_text(encoding='utf-8'))
        self.assertEqual(regras['garantia']['prazo_dias'],30)
        self.assertEqual(regras['troca']['prazo_dias'],7)
        self.assertFalse(regras['garantia']['aprovacao_automatica'])
        self.assertFalse(regras['troca']['aprovacao_automatica'])
        self.assertIn('sem_instalacao',regras['troca']['requisitos'])
        self.assertNotIn('garantia',regras['politicas_pendentes'])
        self.assertNotIn('troca',regras['politicas_pendentes'])
        self.assertIsNone(regras['politicas_pendentes']['frete_devolucao'])

    def test_nao_marca_secao_recuperada_como_documento_ausente(self):
        rag=self.carregar(reescrever=lambda _:PlanoBusca(consultas=['garantia'],assuntos_sem_documento=['Troca e garantia']))
        r=rag.consultar('Qual prazo de garantia?')
        self.assertIn('POL-03',[d['id'] for d in r['documentos']])
        self.assertEqual(r['assuntos_sem_documento'],[])
        self.assertEqual(r['assuntos_sem_documento_sugeridos'],['Troca e garantia'])

    def test_rejeita_vetores_nulos_e_perguntas_invalidas(self):
        for vetores in ([[0.,0.]],[[float('nan'),1]],[]):
            with self.assertRaises(ValueError):
                matriz_normalizada(vetores)
        with self.assertRaises(ValueError):
            self.carregar().consultar('')

    def test_tool_executa_rag_no_mesmo_agente_e_registra_fonte(self):
        modelo=ModeloRoteirizado(responses=[AIMessage(content='',tool_calls=[{'name':'consultar_politicas',
            'args':{'pergunta':'Posso pagar ao entregador?'},'id':'rag'}]),AIMessage(content='Pagamento antecipado. Fonte: Pagamento, politicas_loja.txt.')])
        memoria=MemoriaSQLite(Path(self.tmp.name)/'mem.sqlite3')
        self.addCleanup(memoria.fechar)
        servico=AtendimentoRAG(memoria,modelo=modelo,cliente_cep=criar_cliente_dummy(),rag=self.carregar(),planejador=lambda _:plano())
        self.addCleanup(servico.fechar)
        sessao=memoria.abrir_sessao('cliente_demo')
        r=servico.atender('cliente_demo',sessao,'Posso pagar ao entregador?',salvar=False)
        self.assertEqual(r['status'],'ok')
        self.assertEqual(r['fase'],4)
        retorno=json.loads(next(m['conteudo'] for m in r['trajetoria'] if m.get('ferramenta')=='consultar_politicas'))
        self.assertEqual(retorno['documentos'][0]['id'],'POL-01')
        self.assertEqual(len(servico.atendente.ferramentas),8)
        self.assertIn('Fontes consultadas:',r['resposta'])
        self.assertEqual(memoria.historico('cliente_demo',sessao)[-1]['content'],r['resposta'])

    def test_politica_e_verificada_no_turno_atual(self):
        anterior=[HumanMessage(content='Aceita dinheiro?'),AIMessage(content='Sim, na retirada.')]
        self.assertTrue(politica_precisa_consulta(anterior+[HumanMessage(content='Qual meu carro salvo e posso pagar em dinheiro?')]))
        atual=[HumanMessage(content='Qual prazo de garantia?'),AIMessage(content='',tool_calls=[{'name':'consultar_politicas','args':{'pergunta':'garantia'},'id':'p'}]),
               ToolMessage(content='{}',name='consultar_politicas',tool_call_id='p')]
        self.assertFalse(politica_precisa_consulta(atual))
        self.assertFalse(politica_precisa_consulta([HumanMessage(content='Quero trocar o óleo do meu Celta.')]))

    def test_falha_de_reescrita_nao_e_politica_ausente(self):
        def falhar(_):
            raise TimeoutError('fixture')
        rag=self.carregar(reescrever=falhar)
        with self.assertRaises(TimeoutError):
            rag.consultar('Qual o pagamento?')

    def test_tool_choice_no_campo_do_sdk_sem_duplicacao(self):
        pedidos=[]
        def http(request):
            corpo=json.loads(request.content)
            pedidos.append(corpo)
            if len(pedidos)==1:
                self.assertEqual(corpo['tool_choice']['function']['name'],'consultar_politicas')
                mensagem={'role':'assistant','content':None,'tool_calls':[{'id':'politica','type':'function',
                    'function':{'name':'consultar_politicas','arguments':json.dumps({'pergunta':'Posso pagar ao entregador?'})}}]}
                motivo='tool_calls'
            else:
                self.assertNotIsInstance(corpo.get('tool_choice'),dict)
                mensagem={'role':'assistant','content':'Pagamento antecipado pelo site.'}
                motivo='stop'
            return httpx.Response(200,json={'id':'fixture','object':'chat.completion','created':1,'model':'gpt-4o-mini',
                                           'choices':[{'index':0,'message':mensagem,'finish_reason':motivo}]})
        cliente=httpx.Client(transport=httpx.MockTransport(http))
        self.addCleanup(cliente.close)
        modelo=ChatOpenAI(model='gpt-4o-mini',api_key='fixture-local-sem-rede',http_client=cliente,max_retries=0)
        memoria=MemoriaSQLite(Path(self.tmp.name)/'sdk.sqlite3')
        self.addCleanup(memoria.fechar)
        sistema=AtendimentoRAG(memoria,modelo=modelo,cliente_cep=criar_cliente_dummy(),rag=self.carregar(),planejador=lambda _:plano())
        self.addCleanup(sistema.fechar)
        sessao=memoria.abrir_sessao('cliente_sdk')
        r=sistema.atender('cliente_sdk',sessao,'Posso pagar ao entregador?',salvar=False)
        self.assertEqual(r['status'],'ok')
        self.assertEqual(len(pedidos),2)
        self.assertTrue(r['fontes_documentais'])

    def test_apresentacao_das_respostas_reais_sem_rodape_duplicado(self):
        arquivo=localizar_projeto()/'04_avaliacao_e_evidencias/resultados/fase04_real_20261108T234534311178Z.json'
        reais=json.loads(arquivo.read_text(encoding='utf-8'))
        servico=AtendimentoRAG.__new__(AtendimentoRAG)
        for caso in reais['casos']:
            resultado=servico.finalizar_resposta(caso['resultado'])
            if resultado['fontes_documentais']:
                self.assertEqual(resultado['resposta'].count('Fontes consultadas:'),1)
            self.assertNotIn('Esses produtos são fictícios',resultado['resposta'])
            if caso['caso']=='catalogo_filtrado':
                self.assertIn('especificação a confirmar',resultado['resposta'])

    def test_cli_abre_no_windows_cp1252_sem_chamada_externa(self):
        script=localizar_projeto()/'02_codigo/src/auto_super_parts/atendimento_rag.py'
        ambiente={**os.environ,'OPENAI_API_KEY':'fixture-local-sem-rede','PYTHONIOENCODING':'cp1252'}
        r=subprocess.run([sys.executable,'-B',str(script),'--sem-vetores','--banco',str(Path(self.tmp.name)/'cli.sqlite3')],
                         input='/sair\n',capture_output=True,text=True,encoding='cp1252',env=ambiente,timeout=40)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('SUA MENSAGEM',r.stdout)
        self.assertIn('linguagem natural -> plano tipado',r.stdout)


class QueryTest(unittest.TestCase):
    def setUp(self):
        self.catalogo=Catalogo()
        self.addCleanup(self.catalogo.fechar)

    def executar(self,**filtros):
        return consultar_catalogo_planejado(self.catalogo,'Pedido fixture local',lambda _:plano(**filtros))

    def test_combina_categoria_estoque_preco_e_ordem(self):
        r=self.executar(categoria='vela',estoque='disponivel',preco_max_centavos=2000,ordenacao='preco_crescente')
        self.assertTrue(r['produtos'])
        self.assertIn('P003',{p['id'] for p in r['produtos']})
        self.assertTrue(all(p['categoria']=='vela' and p['estoque']>0 and p['preco_centavos']<=2000 for p in r['produtos']))
        precos=[p['preco_centavos'] for p in r['produtos']]
        self.assertEqual(precos,sorted(precos))
        self.assertEqual(r['parametros_sql'],['vela',2000,10])
        self.assertIn('LIMIT ?',r['sql_executado'])

    def test_estoque_zerado_retorna_produto_existente(self):
        r=self.executar(estoque='zerado')
        self.assertIn('P023',{p['id'] for p in r['produtos']})
        self.assertTrue(all(p['estoque']==0 for p in r['produtos']))

    def test_veiculo_com_aplicacao_local_e_sem_produtos(self):
        r=self.executar(veiculo_id='V001',categoria='vela')
        self.assertEqual([p['id'] for p in r['produtos']],['P003'])
        self.assertEqual(self.executar(veiculo_id='V005')['status'],'sem_resultados')

    def test_sql_livre_campos_extras_e_identificadores_nao_passam(self):
        for alteracao in ({'sql':'DELETE FROM produtos'}, {'ordenacao':'preco; DROP TABLE produtos'},
                          {'categoria':"vela' OR 1=1 --"},{'veiculo_id':'V999'},{'limite':10000},
                          {'preco_max_centavos':-1},{'preco_max_centavos':True}):
            with self.assertRaises(ValidationError):
                self.executar(**alteracao)
        self.assertEqual(len(self.catalogo.ler('SELECT id FROM produtos')),24)

    def test_ambiguidade_nao_executa_consulta_global(self):
        r=self.executar(consulta_valida=False,pendencias=['Qual motor e ano do Gol?'])
        self.assertEqual(r['status'],'consulta_pendente')
        self.assertNotIn('sql_executado',r)
        self.assertEqual(r['produtos'],[])

    def test_preco_zero_nao_e_ignorado(self):
        r=self.executar(preco_max_centavos=0)
        self.assertEqual(r['status'],'sem_resultados')
        self.assertIn(0,r['parametros_sql'])

    def test_contrato_nao_aceita_consultas_demais(self):
        with self.assertRaises(ValidationError):
            PlanoBusca(consultas=['a','b','c','d'],assuntos_sem_documento=[])


if __name__=='__main__':
    unittest.main()
