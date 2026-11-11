"""Fixtures manuais para falhas de fonte; não são resultados de compreensão do LLM."""
import copy
import io
import unittest
from contextlib import redirect_stdout
from test_extracao import mensagem,snapshot,saida,modelo_json
from secretaria.extracao import analisar_snapshot,preparar_lotes,validar_fontes,FonteInvalida
from secretaria.apresentacao import exibir_analise

class FontesPorPropostaTest(unittest.TestCase):
    def test_preserva_valida_e_registra_invalida_sem_aprovar_lote(self):
        dados=saida();ruim=copy.deepcopy(dados['propostas'][0])
        ruim['fontes'][0]['trecho']='Texto inexistente na fonte.'
        dados['propostas'].append(ruim)
        r=analisar_snapshot(snapshot([mensagem()]),modelo_json(dados),'fixture_manual')
        self.assertEqual(len(r['propostas']),1)
        self.assertEqual(r['status'],'parcial')
        self.assertEqual(r['lotes'][0]['status'],'parcial')
        self.assertEqual(r['mensagens_em_lotes_concluidos'],0)
        self.assertEqual(r['propostas_rejeitadas_por_fonte'],1)
        rejeitada=r['lotes'][0]['propostas_rejeitadas'][0]
        self.assertEqual(rejeitada['numero_proposta'],2)
        self.assertEqual(rejeitada['status'],'rejeitada_por_fonte')
        self.assertEqual(rejeitada['proposta'],ruim)
        self.assertEqual(r['gravacoes_operacionais'],0)

    def test_distingue_ids_repetidos_de_ausencia_de_foco(self):
        d=saida();d['propostas'][0]['fontes']*=2
        with self.assertRaisesRegex(FonteInvalida,'repetidos'):
            validar_fontes(d,preparar_lotes(snapshot([mensagem()]))[0])
        lote=preparar_lotes(snapshot([mensagem(),mensagem(2)]),tamanho=1)[1]
        with self.assertRaisesRegex(FonteInvalida,'Nenhuma fonte'):
            validar_fontes(saida(),lote)

    def test_proposta_de_vizinho_e_rejeitada_sem_perder_foco(self):
        dados=saida();vizinha=copy.deepcopy(dados['propostas'][0])
        vizinha['fontes'][0]['mensagem_id']=2
        dados['propostas'].append(vizinha)
        r=analisar_snapshot(snapshot([mensagem(),mensagem(2)]),modelo_json(dados),'fixture_manual',tamanho=1)
        self.assertEqual(r['propostas_rejeitadas_por_fonte'],2)
        self.assertEqual(len(r['propostas']),2)
        self.assertEqual([p['fontes'][0]['mensagem_id'] for p in r['propostas']],[1,2])
        self.assertEqual(r['status'],'parcial')

    def test_valor_inventado_nao_entra_nas_propostas_aceitas(self):
        dados=saida();ruim=copy.deepcopy(dados['propostas'][0])
        ruim['financeiro']['valor_centavos']=12345;dados['propostas'].insert(0,ruim)
        r=analisar_snapshot(snapshot([mensagem()]),modelo_json(dados),'fixture_manual')
        self.assertEqual(len(r['propostas']),1)
        self.assertEqual(r['propostas'][0]['financeiro']['valor_centavos'],1000000)
        self.assertIn('Valor monetário',r['lotes'][0]['propostas_rejeitadas'][0]['motivo'])

    def test_todas_invalidas_nao_inventam_resultado(self):
        dados=saida();dados['propostas'][0]['fontes'][0]['mensagem_id']=999
        r=analisar_snapshot(snapshot([mensagem()]),modelo_json(dados),'fixture_manual')
        self.assertEqual(r['propostas'],[])
        self.assertEqual(r['propostas_rejeitadas_por_fonte'],1)
        self.assertEqual(r['status'],'parcial')

    def test_saida_sem_propostas_pode_concluir_lote(self):
        r=analisar_snapshot(snapshot([mensagem()]),modelo_json({'propostas':[],'observacoes':[]}), 'fixture_manual')
        self.assertEqual(r['status'],'completa')
        self.assertEqual(r['propostas_rejeitadas_por_fonte'],0)

    def test_terminal_indica_numero_e_causa_da_rejeicao(self):
        dados=saida();dados['propostas'][0]['fontes']*=2
        r=analisar_snapshot(snapshot([mensagem()]),modelo_json(dados),'fixture_manual')
        out=io.StringIO()
        with redirect_stdout(out):exibir_analise(r)
        self.assertIn('Lote 1 | Proposta 1 rejeitada',out.getvalue())
        self.assertIn('IDs de fontes repetidos',out.getvalue())
        self.assertIn('parcial',out.getvalue())
