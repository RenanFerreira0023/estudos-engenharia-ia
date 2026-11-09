"""Contratos e ciclo de reparo com juiz/modelo roteirizados, sem API ou métricas semânticas reais."""
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from langchain_core.messages import AIMessage
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from auto_super_parts.verificacao import VerificadorResposta, coletar_evidencias, checar_valores, LIMITACAO_SEGURA
from auto_super_parts.casos_verificacao import montar_casos, resultado_fixture
from auto_super_parts.atendimento_verificado import AtendimentoVerificado
from auto_super_parts.memoria import MemoriaSQLite
from auto_super_parts.viacep import criar_cliente_dummy
from test_correcao_fase02 import ModeloRoteirizado


def parecer(pacote, classe='sustentada', **alteracoes):
    return {'afirmacoes': [{'trecho': pacote['resposta'], 'classe': classe, 'evidencias': ['E001'], 'motivo': 'Parecer roteirizado de teste.'}],
            'cobertura_completa': True, 'responde_pedido': True, 'coerencia_logica': True, 'comentario': 'Fixture', **alteracoes}


class RAGFixture:
    manifesto={'modelo_embedding':'fixture', 'sha256_fonte':'fixture'}
    def consultar(self, pergunta):
        return {'status':'sem_evidencia', 'documentos':[]}


class VerificacaoTest(unittest.TestCase):
    def setUp(self):
        self.casos={c['id']:c['resultado'] for c in montar_casos()}

    def test_valores_atuais_aprovam_e_total_errado_reprova(self):
        r=self.casos['orcamento_correto']
        self.assertEqual(checar_valores(r['resposta'],coletar_evidencias(r)),[])
        erros=checar_valores('Total: R$ 16,90.',coletar_evidencias(r))
        self.assertTrue(any(e['regra']=='valor_diverge_do_orcamento' for e in erros))
        erros=checar_valores('Total: R$ 100,00.',coletar_evidencias(r))
        self.assertTrue(any(e['regra']=='valor_sem_evidencia' for e in erros))

    def test_total_nulo_nao_pode_ser_aprovado_e_reserva_nao_existe(self):
        e=coletar_evidencias(self.casos['saldo_insuficiente'])
        self.assertTrue(checar_valores('Total: R$ 16,90.',e))
        self.assertTrue(checar_valores('Reservei as unidades.',e))
        self.assertFalse(checar_valores('Não reservei as unidades.',e))

    def test_nao_usa_preco_do_perfil_como_evidencia(self):
        r=resultado_fixture('Quanto custa?', 'R$ 16,90',[])
        r['memoria_utilizada']={'perfil':{'preco_centavos':1690}}
        self.assertTrue(checar_valores(r['resposta'],coletar_evidencias(r)))

    def test_regra_numerica_nao_detecta_troca_de_precos_juiz_e_necessario(self):
        r=self.casos['precos_trocados']
        self.assertFalse(checar_valores(r['resposta'],coletar_evidencias(r)))
        v=VerificadorResposta(lambda p:parecer(p,'contradita'),lambda p:LIMITACAO_SEGURA)
        self.assertFalse(v.avaliar(r,r['resposta'])['aprovada'])

    def test_tres_classes_e_cobertura_resposta_coerencia(self):
        r=self.casos['orcamento_correto']
        for classe in ('contradita','sem_suporte'):
            v=VerificadorResposta(lambda p:parecer(p,classe),lambda p:'')
            self.assertFalse(v.avaliar(r,r['resposta'])['aprovada'])
        for chave in ('cobertura_completa','responde_pedido','coerencia_logica'):
            v=VerificadorResposta(lambda p:parecer(p,**{chave:False}),lambda p:'')
            self.assertFalse(v.avaliar(r,r['resposta'])['aprovada'])

    def test_parecer_nao_pode_inventar_citacao_ou_trecho(self):
        r=self.casos['orcamento_correto']
        for alteracao in ({'evidencias':['E999']},{'evidencias':[]},{'trecho':'frase inexistente'}):
            def juiz(p):
                valor=parecer(p);valor['afirmacoes'][0].update(alteracao);return valor
            self.assertFalse(VerificadorResposta(juiz,lambda p:'').avaliar(r,r['resposta'])['aprovada'])

    def test_juiz_incompleto_ou_indisponivel_fecha_com_limitacao_sem_reparo(self):
        for juiz in (lambda p:{},lambda p:(_ for _ in ()).throw(TimeoutError())):
            reparos=[]
            resposta,a=VerificadorResposta(juiz,lambda p:reparos.append(p)).processar(self.casos['orcamento_correto'])
            self.assertEqual(resposta,LIMITACAO_SEGURA)
            self.assertEqual(a['status'],'limitacao')
            self.assertFalse(reparos)

    def test_um_reparo_reavaliado_sem_loop(self):
        r=self.casos['total_incorreto'];chamadas=[]
        def juiz(p):
            chamadas.append('juiz');return parecer(p,'contradita')
        def reparar(p):
            chamadas.append('reparo');return 'Total: R$ 100,00.'
        resposta,a=VerificadorResposta(juiz,reparar).processar(r)
        self.assertEqual(chamadas,['juiz','reparo','juiz'])
        self.assertEqual(resposta,LIMITACAO_SEGURA)
        self.assertEqual(a['reparos_executados'],1)

    def test_reparo_corrigido_erro_e_resposta_vazia(self):
        r=self.casos['total_incorreto']
        v=VerificadorResposta(lambda p:parecer(p),lambda p:'Total: R$ 118,30.')
        resposta,a=v.processar(r)
        self.assertEqual(a['status'],'corrigida')
        self.assertEqual(resposta,'Total: R$ 118,30.')
        for reparar in (lambda p:'',lambda p:(_ for _ in ()).throw(ValueError())):
            resposta,a=VerificadorResposta(lambda p:parecer(p),reparar).processar(r)
            self.assertEqual(resposta,LIMITACAO_SEGURA)
            self.assertEqual(a['status'],'limitacao')

    def test_hook_persiste_apenas_resposta_liberada_e_preserva_candidata(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem=MemoriaSQLite(Path(tmp)/'m.sqlite3')
            sessao=mem.abrir_sessao('teste')
            modelo=ModeloRoteirizado(responses=[
                AIMessage(content='',tool_calls=[{'name':'calcular_orcamento','args':{'itens':[{'produto_id':'P009','quantidade':7}],'modalidade':'retirada'},'id':'t'}]),
                AIMessage(content='Total: R$ 100,00.')])
            sistema=AtendimentoVerificado(mem,modelo=modelo,cliente_cep=criar_cliente_dummy(),rag=RAGFixture(),planejador=lambda p:{},
                verificador=VerificadorResposta(lambda p:parecer(p),lambda p:'Total: R$ 118,30.'))
            try:
                r=sistema.atender('teste',sessao,'Calcule 7 P009 para retirada.',salvar=False)
                self.assertEqual(r['fase'],5)
                self.assertEqual(r['verificacao_geral']['status'],'corrigida')
                self.assertEqual(r['resposta_antes_da_verificacao'],'Total: R$ 100,00.')
                self.assertEqual(mem.historico('teste',sessao)[-1]['content'],'Total: R$ 118,30.')
            finally:
                sistema.fechar();mem.fechar()

    def test_sem_ferramenta_nao_herda_retorno_de_outro_teste(self):
        e=coletar_evidencias(self.casos['saudacao'])
        self.assertEqual([v['id'] for v in e],['M001'])
        self.assertFalse(checar_valores('Olá!',e))

    def test_cli_inicia_em_cp1252_sem_rede(self):
        with tempfile.TemporaryDirectory() as tmp:
            script=Path(__file__).resolve().parents[1]/'src/auto_super_parts/atendimento_verificado.py'
            r=subprocess.run([sys.executable,'-B',str(script),'--sem-vetores','--banco',str(Path(tmp)/'cli.sqlite3')],
                input='/sair\n',capture_output=True,text=True,encoding='cp1252',timeout=40,
                env={**os.environ,'OPENAI_API_KEY':'fixture-sem-rede','PYTHONIOENCODING':'cp1252'})
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn('No maximo um reparo',r.stdout)

    def test_citacao_aceita_apenas_diferenca_de_espacos_e_markdown(self):
        r=self.casos['orcamento_correto'].copy()
        r['resposta']='**Total:** R$ 118,30.\n\nNao houve reserva.'
        def juiz(p):
            a=parecer(p);a['afirmacoes'][0]['trecho']='Total: R$ 118,30. Nao houve reserva.';return a
        v=VerificadorResposta(juiz,lambda p:'')
        self.assertTrue(v.avaliar(r,r['resposta'])['aprovada'])
        r['resposta']='**Total:** R$ 118,31. Nao houve reserva.'
        self.assertFalse(v.avaliar(r,r['resposta'])['aprovada'])

    def test_falha_do_juiz_nao_grava_candidata_sem_suporte(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem=MemoriaSQLite(Path(tmp)/'m.sqlite3')
            sessao=mem.abrir_sessao('teste')
            modelo=ModeloRoteirizado(responses=[AIMessage(content='Reservei 8 unidades. Total: R$ 100,00.')])
            verificador=VerificadorResposta(lambda p:(_ for _ in ()).throw(TimeoutError()),lambda p:'Nao executar')
            sistema=AtendimentoVerificado(mem,modelo=modelo,rag=RAGFixture(),planejador=lambda p:{},verificador=verificador)
            try:
                r=sistema.atender('teste',sessao,'Quero 8 velas.',salvar=False)
                self.assertEqual(r['resposta'],LIMITACAO_SEGURA)
                self.assertEqual(mem.historico('teste',sessao)[-1]['content'],LIMITACAO_SEGURA)
                self.assertIn('Reservei',r['resposta_antes_da_verificacao'])
            finally:
                sistema.fechar();mem.fechar()

    def test_replay_listagem_real_teto_nao_e_preco_de_peca(self):
        from auto_super_parts.configuracao import localizar_projeto
        f=localizar_projeto()/'04_avaliacao_e_evidencias/resultados/fase05_20261109T011010952628Z.json'
        r=json.loads(f.read_text(encoding='utf-8'))
        resposta=r['resposta_antes_da_verificacao']
        self.assertFalse(checar_valores(resposta,coletar_evidencias(r)))
        # REPLAY: reutiliza parecer real gravado; não é uma nova chamada de API.
        anterior=r['verificacao_geral']['avaliacoes'][0]['parecer']
        v=VerificadorResposta(lambda p:anterior,lambda p:'Nao executar',origem='replay de parecer real gravado')
        self.assertTrue(v.avaliar(r,resposta)['aprovada'])

    def test_teto_nao_autoriza_preco_total_ou_teto_inventados(self):
        from auto_super_parts.configuracao import localizar_projeto
        f=localizar_projeto()/'04_avaliacao_e_evidencias/resultados/fase05_20261109T011010952628Z.json'
        r=json.loads(f.read_text(encoding='utf-8'));e=coletar_evidencias(r)
        for resposta in ('Preco: R$ 20,00.', 'Total: R$ 20,00.', 'Velas até R$ 21,00.'):
            self.assertTrue(checar_valores(resposta,e),resposta)
        self.assertFalse(checar_valores('Teto: R$ 20,00. Palio: R$ 16,90.',e))
        e=[item for item in e if item.get('ferramenta')!='consultar_catalogo_estruturado']
        self.assertTrue(checar_valores('Velas até R$ 20,00.',e))
