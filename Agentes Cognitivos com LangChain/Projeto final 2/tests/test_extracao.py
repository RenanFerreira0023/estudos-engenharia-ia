"""Contratos, fontes e cobertura com respostas roteirizadas; não mede compreensão de LLM."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from pydantic import ValidationError
from secretaria.banco import Banco,Contexto
from secretaria.cli import localizar_projeto
from secretaria.chain_extracao import criar_chain,criar_modelo,esquema_fornecedor
from secretaria.extracao import analisar_demonstracao,analisar_snapshot,preparar_lotes,validar_fontes,FonteInvalida
from secretaria.fixtures_extracao import criar_modelo_fixture
from secretaria.propostas import SaidaExtracao,Financeiro,Agenda

RAIZ=Path(__file__).resolve().parents[1]

def mensagem(id=1,texto='Orçamento X: R$ 10.000,00. Entrada de 30%.'):
    return {'id':id,'autor':'Ana','texto':texto,'tipo':'mensagem','instante_utc':'2026-11-09T11:00:00+00:00',
            'data_original':'09/11/2026, 08:00:00','editada':0,'midia_omitida':0}

def snapshot(mensagens):
    return {'empresa_id':'demo','usuario_id':'ana','corpus_id':1,'fuso':'America/Sao_Paulo','mensagens':mensagens}

def saida(m=None):
    m=m or mensagem()
    return {'propostas':[{'area':'financeiro','projeto':'X','natureza':'previsto','resumo':'Orçamento informado.',
        'financeiro':{'tipo':'orcamento_proposto','valor_centavos':1000000,'percentual':'30','data_referencia':None},
        'agenda':None,'fontes':[{'mensagem_id':m['id'],'trecho':m['texto']}],'pendencias':[]}],'observacoes':[]}

def modelo_json(dados):
    return RunnableLambda(lambda _:AIMessage(content=json.dumps(dados,ensure_ascii=False)))

class ContratosEFontesTest(unittest.TestCase):
    def setUp(self):self.lote=preparar_lotes(snapshot([mensagem()]))[0]

    def test_valor_com_pontuacao_e_percentual_da_fonte(self):
        self.assertEqual(len(validar_fontes(saida(),self.lote).propostas),1)

    def test_rejeita_float_dinheiro_percentual_impossivel_e_campo_extra(self):
        for alteracao in ({'valor_centavos':10.5},{'valor_centavos':-1},{'percentual':'101'}):
            d={'tipo':'condicao_prevista','valor_centavos':None,'percentual':None,'data_referencia':None,**alteracao}
            with self.assertRaises(ValidationError):Financeiro.model_validate(d)
        d=saida();d['propostas'][0]['confirmado']=True
        with self.assertRaises(ValidationError):SaidaExtracao.model_validate(d)

    def test_rejeita_fonte_inexistente_trecho_alterado_e_valor_derivado(self):
        for campo,valor in [('fonte',99),('trecho','Orçamento de R$ 20.000,00.'),('valor',300000),('percentual','25')]:
            d=saida()
            if campo=='fonte':d['propostas'][0]['fontes'][0]['mensagem_id']=valor
            elif campo=='trecho':d['propostas'][0]['fontes'][0]['trecho']=valor
            else:d['propostas'][0]['financeiro']['valor_centavos' if campo=='valor' else 'percentual']=valor
            with self.assertRaises(FonteInvalida):validar_fontes(d,self.lote)

    def test_contexto_sozinho_nao_produz_proposta_e_midia_nao_vira_fato(self):
        lote=preparar_lotes(snapshot([mensagem(),mensagem(2,'Sem informação relevante.')]),tamanho=1)[1]
        with self.assertRaises(FonteInvalida):validar_fontes(saida(),lote)
        lote=self.lote.copy();lote['mensagens_foco']=[{**mensagem(),'tipo':'midia_omitida'}]
        with self.assertRaises(FonteInvalida):validar_fontes(saida(),lote)

    def test_area_nao_pode_esconder_objeto_financeiro(self):
        d=saida();d['propostas'][0]['area']='projeto'
        with self.assertRaises(ValidationError):SaidaExtracao.model_validate(d)

    def test_schema_do_fornecedor_restringe_area_e_contrato(self):
        schema=esquema_fornecedor()
        variantes=schema['properties']['propostas']['items']['anyOf']
        self.assertEqual(len(variantes),3)
        projeto=schema['$defs']['PropostaProjeto']
        self.assertEqual(projeto['properties']['financeiro']['type'],'null')
        self.assertEqual(projeto['properties']['area']['enum'],['projeto'])
        self.assertFalse(projeto['additionalProperties'])

    def test_agenda_sem_fuso_e_intervalo_invalido(self):
        base={'tipo':'visita','inicio_em':'2026-11-10T14:00:00-03:00','fim_em':'2026-11-10T15:00:00-03:00','atendente_nome':None,'local':None}
        Agenda.model_validate(base)
        for altera in ({'inicio_em':'2026-11-10T14:00:00'},{'fim_em':'2026-11-10T13:00:00-03:00'}):
            with self.assertRaises(ValidationError):Agenda.model_validate({**base,**altera})

class FluxoTest(unittest.TestCase):
    def test_lotes_cobrem_tudo_uma_vez_e_incluem_vizinhos(self):
        lotes=preparar_lotes(snapshot([mensagem(i+1,'Texto') for i in range(21)]))
        foco=[m['id'] for l in lotes for m in l['mensagens_foco']]
        self.assertEqual(foco,list(range(1,22)))
        self.assertEqual([m['id'] for m in lotes[1]['contexto_vizinho']],[8,17])

    def test_lcel_e_imperativa_equivalentes_invoke_batch_stream(self):
        entrada={'pacote':json.dumps(self.lote())}
        for estilo in ('lcel','imperativa'):
            c=criar_chain(modelo_json(saida()),estilo)
            self.assertEqual(c.invoke(entrada).model_dump(),saida())
            self.assertEqual(len(c.batch([entrada,entrada])),2)
        c=criar_chain(modelo_json(saida()),'imperativa')
        self.assertEqual([s.model_dump() for s in c.stream(entrada)],[saida()])

    def lote(self):return preparar_lotes(snapshot([mensagem()]))[0]

    def test_json_invalido_nao_vira_analise_completa(self):
        r=analisar_snapshot(snapshot([mensagem()]),RunnableLambda(lambda _:AIMessage(content='não é JSON')),'fixture_manual')
        self.assertEqual(r['status'],'parcial')
        self.assertEqual(r['propostas'],[])
        self.assertEqual(r['mensagens_em_lotes_concluidos'],0)

    def test_erro_de_um_lote_nao_apaga_os_demais(self):
        def responder(prompt):
            lote=json.loads(prompt.to_messages()[-1].content.split('):\n',1)[1])
            if lote['lote_id']==2:raise TimeoutError('fixture')
            return AIMessage(content=json.dumps({'propostas':[],'observacoes':[]}))
        r=analisar_snapshot(snapshot([mensagem(i+1,'Texto') for i in range(10)]),RunnableLambda(responder),'fixture_manual',tamanho=5)
        self.assertEqual(r['status'],'parcial')
        self.assertEqual(r['mensagens_em_lotes_concluidos'],5)
        self.assertEqual([l['status'] for l in r['lotes']],['ok','erro'])

    def test_entrada_grande_nao_trunca_e_vazio_nao_chama_modelo(self):
        modelo=RunnableLambda(lambda _:self.fail('Não deveria chamar modelo.'))
        r=analisar_snapshot(snapshot([mensagem(texto='x'*25000)]),modelo,'fixture_manual')
        self.assertEqual(r['status'],'parcial')
        self.assertEqual(analisar_snapshot(snapshot([]),modelo,'fixture_manual')['status'],'vazia')

    def test_fonte_errada_bloqueia_lote_mesmo_com_json_valido(self):
        d=saida();d['propostas'][0]['fontes'][0]['mensagem_id']=999
        r=analisar_snapshot(snapshot([mensagem()]),modelo_json(d),'fixture_manual')
        self.assertEqual(r['lotes'][0]['tipo_erro'],'FonteInvalida')

    def test_demo_percorre_40_fontes_sem_gravar_registros_operacionais(self):
        with tempfile.TemporaryDirectory() as pasta,Banco(Path(pasta)/'db.sqlite3') as banco:
            banco.preparar_demo();ctx=Contexto('demo','ana')
            corpus=banco.selecionar_corpus(ctx,'Demonstração fictícia')
            banco.importar(ctx,corpus,RAIZ/'dados/ficticios/conversa_empresa.txt')
            antes=banco.con.total_changes
            r=analisar_demonstracao(banco,ctx,criar_modelo_fixture(),'fixture_manual')
            self.assertEqual(r['status'],'completa')
            self.assertEqual(r['mensagens_em_lotes_concluidos'],40)
            self.assertEqual(len(r['propostas']),8)
            self.assertEqual(banco.con.total_changes,antes)
            self.assertTrue(all(p['status']=='aguardando_revisao' for p in r['propostas']))
            self.assertEqual(r['gravacoes_operacionais'],0)

    def test_corpus_contaminado_nao_e_enviado_ao_modelo(self):
        with tempfile.TemporaryDirectory() as pasta,Banco(Path(pasta)/'db.sqlite3') as banco:
            banco.preparar_demo();ctx=Contexto('demo','ana')
            corpus=banco.selecionar_corpus(ctx,'Demonstração fictícia')
            arquivo=Path(pasta)/'outro.txt';arquivo.write_text('[09/11/2026, 08:00:00] Ana: Privado\n',encoding='utf-8')
            banco.importar(ctx,corpus,arquivo)
            with self.assertRaises(ValueError):
                analisar_demonstracao(banco,ctx,RunnableLambda(lambda _:self.fail('Não enviar corpus misturado.')),'api_real')

    def test_erro_de_contrato_e_serializavel_sem_ecoar_a_entrada(self):
        d=saida();d['propostas'][0]['area']='projeto'
        r=analisar_snapshot(snapshot([mensagem()]),modelo_json(d),'fixture_manual')
        self.assertEqual(r['status'],'parcial')
        self.assertTrue(r['lotes'][0]['erros_contrato'])
        json.dumps(r)
        self.assertTrue(all(set(e)=={'campo','tipo','motivo'} for e in r['lotes'][0]['erros_contrato']))

    def test_snapshot_respeita_usuario_do_corpus(self):
        with tempfile.TemporaryDirectory() as pasta,Banco(Path(pasta)/'db.sqlite3') as banco:
            banco.preparar_demo();ctx=Contexto('demo','ana');c=banco.selecionar_corpus(ctx,'Privado')
            with self.assertRaises(PermissionError):banco.snapshot_analise(Contexto('demo','bruno'),c)

    def test_chave_ausente_nao_inventa_fallback(self):
        with tempfile.TemporaryDirectory() as pasta,patch.dict('os.environ',{'OPENAI_API_KEY':''}):
            with self.assertRaises(ValueError):criar_modelo(Path(pasta)/'nao_existe.env')

if __name__=='__main__':unittest.main()
