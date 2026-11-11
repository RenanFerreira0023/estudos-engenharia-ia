import copy
import io
import json
from pathlib import Path
import sys
import unittest
from contextlib import redirect_stdout
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from secretaria.revisao import revisar_cancelamentos,listar_edicoes
from secretaria.apresentacao import exibir_analise

def proposta(texto='Cancelar reunião Beta de 12/11/2026 às 09h; cliente informou indisponibilidade.'):
    return {'area':'agenda','projeto':None,'natureza':'correcao','fontes':[{'mensagem_id':35,'trecho':texto}],
            'pendencias':[]}

def mensagem(id,texto,editada=0,autor='Ana',instante='2026-11-09T11:28:00+00:00'):
    return {'id':id,'texto':texto,'editada':editada,'autor':autor,'instante_utc':instante,'tipo':'mensagem'}

class RevisaoTest(unittest.TestCase):
    def test_cancelamento_nome_e_trilha_de_ajuste(self):
        p=proposta();revisar_cancelamentos([p])
        self.assertEqual((p['projeto'],p['natureza']),('Beta','cancelamento'))
        self.assertIsNone(p['ajustes_revisao'][0]['alteracoes']['projeto']['antes'])
        self.assertEqual(p['fontes'][0]['mensagem_id'],35)
        self.assertTrue(p['pendencias'])
        antes=copy.deepcopy(p);revisar_cancelamentos([p]);self.assertEqual(p,antes)

    def test_nao_converte_pergunta_negacao_ou_mencao(self):
        for t in ['Podemos cancelar reunião Beta de 12/11/2026?',
                  'Não cancelar reunião Beta de 12/11/2026.',
                  'Cliente escreveu: Cancelar reunião Beta de 12/11/2026.',
                  'Cancelar reunião Beta de 12/11/2026?']:
            p=proposta(t)
            antes=copy.deepcopy(p);revisar_cancelamentos([p]);self.assertEqual(p,antes)

    def test_conflito_de_nomes_nao_escolhe(self):
        p=proposta();p['fontes'].append({'mensagem_id':36,'trecho':'Cancelar reunião Alfa de 12/11/2026.'})
        antes=copy.deepcopy(p);revisar_cancelamentos([p]);self.assertEqual(p,antes)

    def test_edicao_preserva_dois_textos_sem_escolher(self):
        a=mensagem(29,'Visita Gama às 15h.')
        b=mensagem(30,'Visita Gama às 16h. <Mensagem editada>',1)
        snapshot={'mensagens':[a,b]};antes=copy.deepcopy(snapshot)
        r=listar_edicoes(snapshot)
        self.assertEqual(r[0]['fonte_editada']['mensagem_id'],30)
        self.assertEqual(r[0]['candidatos_mesmo_autor_instante'][0]['mensagem_id'],29)
        self.assertEqual(snapshot,antes)

    def test_edicao_sem_candidato_e_autor_distinto(self):
        a=mensagem(29,'Visita às 15h.',autor='Bruno')
        b=mensagem(30,'Visita às 16h.',1)
        self.assertEqual(listar_edicoes({'mensagens':[a,b]})[0]['candidatos_mesmo_autor_instante'],[])

    def test_terminal_exibe_edicao_mesmo_sem_proposta_llm(self):
        r={'origem':'fixture_manual','estilo':'lcel','mensagens_em_lotes_concluidos':0,
           'mensagens_no_snapshot':2,'propostas':[],'lotes':[],'status':'parcial',
           'edicoes_para_revisao':listar_edicoes({'mensagens':[
               mensagem(29,'Visita Gama às 15h.'),mensagem(30,'Visita Gama às 16h.',1)]})}
        out=io.StringIO()
        with redirect_stdout(out):exibir_analise(r)
        self.assertIn('15h',out.getvalue());self.assertIn('16h',out.getvalue())
        self.assertIn('nenhum horário foi escolhido',out.getvalue())

    def test_integracao_fixture_preserva_pendencia_de_edicao(self):
        import tempfile
        from secretaria.banco import Banco,Contexto
        from secretaria.extracao import analisar_demonstracao
        from secretaria.fixtures_extracao import criar_modelo_fixture
        with tempfile.TemporaryDirectory() as t:
            b=Banco(Path(t)/'teste.sqlite3');b.preparar_demo()
            r=analisar_demonstracao(b,Contexto('demo','ana'),criar_modelo_fixture(),'fixture_manual')
            b.con.close()
        self.assertEqual(r['gravacoes_operacionais'],0)
        self.assertEqual(r['edicoes_para_revisao'][0]['fonte_editada']['mensagem_id'],30)
        self.assertEqual(r['edicoes_para_revisao'][0]['candidatos_mesmo_autor_instante'][0]['mensagem_id'],29)
