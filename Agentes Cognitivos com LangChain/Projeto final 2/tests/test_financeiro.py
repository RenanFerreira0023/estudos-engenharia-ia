"""Orçamento aceito, parcelas e pagamentos confirmados não se confundem com relatos do chat."""
import tempfile
import unittest
from pathlib import Path

from secretaria.banco import Banco, Contexto
from secretaria.extracao import analisar_snapshot
from secretaria.fixtures_extracao import criar_modelo_fixture
from secretaria.fila_revisao import FilaRevisao
from secretaria.projetos_fontes import ProjetosFontes
from secretaria.financeiro import Financeiro
from secretaria.agente_agenda import criar_ferramentas_agenda
from secretaria.terminal_financeiro import centavos, moeda


class FinanceiroTest(unittest.TestCase):
    def test_moeda_de_console_sem_float(self):
        self.assertEqual(centavos('R$ 10.000,00'),1000000)
        self.assertEqual(moeda(1000000),'R$ 10.000,00')
        self.assertEqual(moeda(None),'não definido')
        with self.assertRaises(ValueError):
            centavos('10,001')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.caminho = Path(self.tmp.name)/'financeiro.sqlite3'
        self.banco = Banco(self.caminho)
        self.addCleanup(self.banco.fechar)
        self.banco.preparar_demo()
        self.ana = Contexto('demo','ana')
        self.bruno = Contexto('demo','bruno')
        self.carla = Contexto('demo','carla')
        corpus = self.banco.selecionar_corpus(self.ana,'Demonstração fictícia')
        self.banco.importar(self.ana,corpus,Path(__file__).resolve().parents[1]/
                           'dados/ficticios/conversa_empresa.txt')
        analise = analisar_snapshot(self.banco.snapshot_analise(self.ana,corpus),
                                   criar_modelo_fixture(),'fixture_manual')
        fila = FilaRevisao(self.banco)
        proposta = fila.registrar_resultado(self.ana,analise)['ids'][0]
        fila.decidir(self.ana,proposta,1,'aceitar','Projeto Alfa conferido.')
        servico = ProjetosFontes(self.banco)
        previa = servico.prever(self.ana,proposta)
        self.projeto = servico.confirmar(self.ana,proposta,previa['versao'])['projeto_id']
        self.financeiro = Financeiro(self.banco)

    def test_relato_nao_vira_recebimento_e_pagamento_parcial(self):
        inicial = self.financeiro.relatorio(self.ana)['projetos'][0]
        self.assertIsNone(inicial['saldo_centavos'])
        orcamento = self.financeiro.criar_orcamento(self.ana,self.projeto,1000000,30)['orcamento_id']
        self.assertIsNone(self.financeiro.relatorio(self.ana)['projetos'][0]['saldo_centavos'])
        self.assertEqual(self.financeiro.aceitar_orcamento(self.ana,orcamento)['status'],'aceito')
        self.assertEqual(self.financeiro.aceitar_orcamento(self.ana,orcamento)['status'],'ja_aceito')
        parcelas = self.financeiro.definir_parcelas(self.ana,orcamento,[
            {'descricao':'Entrada','valor_centavos':300000,'vencimento':'2026-11-20'},
            {'descricao':'Restante','valor_centavos':700000,'vencimento':None}])['parcelas_ids']
        pagamento = self.financeiro.informar_pagamento(self.ana,parcelas[0],100000,
                       '2026-11-11','lancamento-1')['pagamento_id']
        antes = self.financeiro.relatorio(self.ana)['projetos'][0]
        self.assertEqual((antes['recebido_confirmado_centavos'],antes['saldo_centavos']),
                         (0,1000000))
        self.assertEqual(self.financeiro.confirmar_pagamento(self.ana,pagamento)['status'],'confirmado')
        self.assertEqual(self.financeiro.confirmar_pagamento(self.ana,pagamento)['status'],'ja_confirmado')
        depois = self.financeiro.relatorio(self.ana)['projetos'][0]
        self.assertEqual((depois['recebido_confirmado_centavos'],depois['saldo_centavos']),
                         (100000,900000))
        self.assertEqual(depois['percentual_entrada_acordado'],30)
        self.assertEqual(depois['parcelas'][0]['saldo_centavos'],200000)
        with Banco(self.caminho) as reaberto:
            self.assertEqual(Financeiro(reaberto).relatorio(self.bruno)['projetos'][0]
                             ['saldo_centavos'],900000)
        with self.assertRaises(PermissionError):
            self.financeiro.relatorio(self.carla)
        ferramentas_bruno = {f.name:f for f in criar_ferramentas_agenda(self.caminho,self.bruno)}
        resposta = ferramentas_bruno['consultar_financeiro_projeto'].invoke({'termo':'Alfa'})
        self.assertEqual(resposta['projetos'][0]['saldo_centavos'],900000)
        ferramentas_carla = {f.name:f for f in criar_ferramentas_agenda(self.caminho,self.carla)}
        self.assertEqual(ferramentas_carla['consultar_financeiro_projeto'].invoke({'termo':'Alfa'}),
                         {'status':'acesso_negado'})

    def test_regras_de_integridade_e_idempotencia(self):
        with self.assertRaises(ValueError):
            self.financeiro.criar_orcamento(self.ana,self.projeto,100,101)
        primeiro = self.financeiro.criar_orcamento(self.ana,self.projeto,10000)['orcamento_id']
        segundo = self.financeiro.criar_orcamento(self.ana,self.projeto,12000)['orcamento_id']
        self.financeiro.aceitar_orcamento(self.ana,primeiro)
        with self.assertRaisesRegex(ValueError,'Já existe'):
            self.financeiro.aceitar_orcamento(self.ana,segundo)
        with self.assertRaisesRegex(ValueError,'Soma'):
            self.financeiro.definir_parcelas(self.ana,primeiro,[
                {'descricao':'Parcial','valor_centavos':9999}])
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM parcelas').fetchone()[0],0)
        parcela = self.financeiro.definir_parcelas(self.ana,primeiro,[
            {'descricao':'Única','valor_centavos':10000}])['parcelas_ids'][0]
        informado = self.financeiro.informar_pagamento(self.bruno,parcela,9000,
                         '2026-11-11','mesma-chave')
        self.assertTrue(self.financeiro.informar_pagamento(self.bruno,parcela,9000,
                        '2026-11-11','mesma-chave')['reutilizado'])
        with self.assertRaisesRegex(ValueError,'já usada'):
            self.financeiro.informar_pagamento(self.bruno,parcela,8000,'2026-11-11','mesma-chave')
        self.financeiro.confirmar_pagamento(self.bruno,informado['pagamento_id'])
        extra = self.financeiro.informar_pagamento(self.bruno,parcela,2000,
                        '2026-11-11','outra-chave')['pagamento_id']
        with self.assertRaisesRegex(ValueError,'excede'):
            self.financeiro.confirmar_pagamento(self.bruno,extra)
        self.assertEqual(self.financeiro.relatorio(self.bruno)['projetos'][0]['saldo_centavos'],1000)
        with self.assertRaises(PermissionError):
            self.financeiro.criar_orcamento(self.carla,self.projeto,10000)
        self.assertGreaterEqual(self.banco.con.execute('SELECT COUNT(*) FROM auditoria_financeiro').fetchone()[0],5)

    def test_revisao_orcamento_preserva_historico(self):
        anterior = self.financeiro.criar_orcamento(self.ana,self.projeto,10000)['orcamento_id']
        novo = self.financeiro.criar_orcamento(self.ana,self.projeto,12000)['orcamento_id']
        self.financeiro.aceitar_orcamento(self.ana,anterior)
        with self.assertRaises(ValueError):
            self.financeiro.substituir_orcamento(self.ana,novo,'x')
        self.assertEqual(self.financeiro.substituir_orcamento(
            self.ana,novo,'Valor revisado com o cliente.')['status'],'substituido')
        self.assertEqual(self.financeiro.relatorio(self.ana)['projetos'][0]['valor_aceito_centavos'],12000)
        self.assertEqual(self.banco.con.execute(
            'SELECT status FROM orcamentos WHERE id=?',(anterior,)).fetchone()[0],'aceito')
        self.assertEqual(self.banco.con.execute(
            'SELECT COUNT(*) FROM substituicoes_orcamento').fetchone()[0],1)
        with self.assertRaisesRegex(ValueError,'substituído'):
            self.financeiro.definir_parcelas(self.ana,anterior,[
                {'descricao':'Antiga','valor_centavos':10000}])
        self.assertEqual(self.financeiro.substituir_orcamento(
            self.ana,novo,'Valor revisado com o cliente.')['status'],'ja_substituido')

    def test_estorno_remove_do_saldo_sem_apagar_pagamento(self):
        orcamento = self.financeiro.criar_orcamento(self.ana,self.projeto,10000)['orcamento_id']
        self.financeiro.aceitar_orcamento(self.ana,orcamento)
        parcela = self.financeiro.definir_parcelas(self.ana,orcamento,[
            {'descricao':'Única','valor_centavos':10000}])['parcelas_ids'][0]
        pagamento = self.financeiro.informar_pagamento(
            self.ana,parcela,4000,'2026-11-11','primeiro')['pagamento_id']
        self.financeiro.confirmar_pagamento(self.ana,pagamento)
        self.assertEqual(self.financeiro.relatorio(self.ana)['projetos'][0]['saldo_centavos'],6000)
        revisao = self.financeiro.criar_orcamento(self.ana,self.projeto,12000)['orcamento_id']
        with self.assertRaisesRegex(ValueError,'pagamentos vinculados'):
            self.financeiro.substituir_orcamento(self.ana,revisao,'Revisão após pagamento.')
        self.assertEqual(self.financeiro.reverter_pagamento(
            self.ana,pagamento,'Valor registrado incorretamente.')['tipo'],'estorno')
        relatorio = self.financeiro.relatorio(self.ana)['projetos'][0]
        self.assertEqual(relatorio['saldo_centavos'],10000)
        self.assertEqual(relatorio['parcelas'][0]['pagamentos'][0]['status'],'estorno')
        novo = self.financeiro.informar_pagamento(
            self.ana,parcela,3000,'2026-11-11','corrigido')['pagamento_id']
        self.financeiro.confirmar_pagamento(self.ana,novo)
        self.assertEqual(self.financeiro.relatorio(self.ana)['projetos'][0]['saldo_centavos'],7000)
        relato = self.financeiro.informar_pagamento(
            self.ana,parcela,2000,'2026-11-11','relato-a-cancelar')['pagamento_id']
        self.assertEqual(self.financeiro.reverter_pagamento(
            self.ana,relato,'Relato duplicado por engano.')['tipo'],'cancelamento')
        with self.assertRaises(ValueError):
            self.financeiro.confirmar_pagamento(self.ana,relato)
        with self.assertRaises(ValueError):
            self.financeiro.confirmar_pagamento(self.ana,pagamento)


if __name__=='__main__':
    unittest.main()
