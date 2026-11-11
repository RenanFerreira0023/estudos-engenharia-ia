"""Vínculo explícito entre interpretação aceita, projeto e mensagens importadas."""
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from secretaria.banco import Banco, Contexto
from secretaria.agenda import Agenda
from secretaria.extracao import analisar_snapshot
from secretaria.fixtures_extracao import criar_modelo_fixture
from secretaria.fila_revisao import FilaRevisao
from secretaria.projetos_fontes import ProjetosFontes
from secretaria.agente_agenda import criar_ferramentas_agenda
from secretaria.roteamento import identificar_rota

RAIZ=Path(__file__).resolve().parents[1]


class ProjetosFontesTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.banco=Banco(Path(self.tmp.name)/'teste.sqlite3')
        self.addCleanup(self.banco.fechar)
        self.banco.preparar_demo()
        self.ctx=Contexto('demo','ana')
        self.outro=Contexto('demo','bruno')
        corpus=self.banco.selecionar_corpus(self.ctx,'Demonstração fictícia')
        self.banco.importar(self.ctx,corpus,RAIZ/'dados/ficticios/conversa_empresa.txt')
        resultado=analisar_snapshot(self.banco.snapshot_analise(self.ctx,corpus),
                                   criar_modelo_fixture(),'fixture_manual')
        self.fila=FilaRevisao(self.banco)
        self.ids=self.fila.registrar_resultado(self.ctx,resultado)['ids']
        self.servico=ProjetosFontes(self.banco)

    def aceitar(self,indice):
        id=self.ids[indice]
        self.fila.decidir(self.ctx,id,1,'aceitar','Fonte e interpretação conferidas.')
        return id

    def test_projeto_confirmado_preserva_fontes_e_e_idempotente(self):
        id=self.aceitar(0)
        cliente=Agenda(self.banco).cadastrar_cliente(self.ctx,'Alfa Serviços')
        previa=self.servico.prever(self.ctx,id,cliente_id=cliente)
        self.assertEqual(previa['acao'],'criar_projeto')
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM projetos').fetchone()[0],0)
        primeiro=self.servico.confirmar(self.ctx,id,previa['versao'],cliente_id=cliente)
        segundo=self.servico.confirmar(self.ctx,id,previa['versao'],cliente_id=cliente)
        self.assertEqual(primeiro['estado'],'confirmada')
        self.assertEqual(segundo['estado'],'ja_confirmada')
        self.assertEqual(primeiro['projeto_id'],segundo['projeto_id'])
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM projetos').fetchone()[0],1)
        self.assertEqual(self.banco.con.execute('SELECT cliente_id FROM projetos').fetchone()[0],cliente)
        outro_cliente=Agenda(self.banco).cadastrar_cliente(self.ctx,'Beta Serviços')
        with self.assertRaisesRegex(ValueError,'outro vínculo'):
            self.servico.confirmar(self.ctx,id,previa['versao'],cliente_id=outro_cliente)
        fontes=self.servico.fontes(self.ctx,primeiro['anotacao_id'])
        self.assertEqual(len(fontes),primeiro['fontes_vinculadas'])
        self.assertTrue(all(f['trecho_snapshot'] for f in fontes))

    def test_anotacao_financeira_exige_projeto_e_nao_cria_pagamento(self):
        projeto_id=self.aceitar(0)
        previa=self.servico.prever(self.ctx,projeto_id)
        projeto=self.servico.confirmar(self.ctx,projeto_id,previa['versao'])['projeto_id']
        financeiro_id=self.aceitar(1)
        with self.assertRaisesRegex(ValueError,'ID do projeto'):
            self.servico.prever(self.ctx,financeiro_id)
        previa=self.servico.prever(self.ctx,financeiro_id,projeto_id=projeto)
        resultado=self.servico.confirmar(self.ctx,financeiro_id,previa['versao'],projeto_id=projeto)
        self.assertEqual(resultado['estado'],'confirmada')
        registro=self.banco.con.execute('SELECT area,projeto_id FROM anotacoes_projeto WHERE id=?',
                                        (resultado['anotacao_id'],)).fetchone()
        self.assertEqual(tuple(registro),('financeiro',projeto))
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM pagamentos').fetchone()[0],0)

    def test_agente_consulta_projeto_sem_confundir_cliente_nem_inventar_saldo(self):
        proposta = self.aceitar(0)
        previa = self.servico.prever(self.ctx, proposta)
        projeto = self.servico.confirmar(self.ctx, proposta, previa['versao'])['projeto_id']
        ferramentas = {f.name:f for f in criar_ferramentas_agenda(self.banco.caminho,self.ctx)}
        consulta = ferramentas['consultar_projeto'].invoke({'termo':'Alfa'})
        self.assertEqual(consulta['projetos'][0]['id'], projeto)
        self.assertIn('não comprovam saldo', consulta['limite'])
        self.assertEqual(ferramentas['consultar_projeto'].invoke({'termo':'Beta'})['status'],
                         'projeto_nao_encontrado')
        self.assertEqual(identificar_rota({'pergunta':'Qual é o saldo dele?'})['rota'],'projeto')
        self.assertEqual(identificar_rota({'pergunta':'Agora estou falando do projeto Beta.'})['rota'],'projeto')

    def test_pendente_rejeitada_e_usuario_errado_nao_aplicam(self):
        with self.assertRaisesRegex(ValueError,'aceita'):
            self.servico.prever(self.ctx,self.ids[0])
        self.fila.decidir(self.ctx,self.ids[0],1,'rejeitar','Não usar esta interpretação.')
        with self.assertRaisesRegex(ValueError,'aceita'):
            self.servico.prever(self.ctx,self.ids[0])
        id=self.aceitar(1)
        with self.assertRaises(PermissionError):
            self.servico.prever(self.outro,id,projeto_id=1)
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM projetos').fetchone()[0],0)

    def test_destino_e_versao_sao_revalidados(self):
        id=self.aceitar(0)
        previa=self.servico.prever(self.ctx,id)
        with self.assertRaisesRegex(ValueError,'Versão'):
            self.servico.confirmar(self.ctx,id,previa['versao']-1)
        projeto=self.servico.confirmar(self.ctx,id,previa['versao'])['projeto_id']
        financeiro_id=self.aceitar(6)  # orçamento Beta não pertence ao Alfa
        with self.assertRaisesRegex(ValueError,'diverge'):
            self.servico.prever(self.ctx,financeiro_id,projeto_id=projeto)
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM anotacoes_projeto').fetchone()[0],1)

    def test_terminal_exige_segunda_confirmacao(self):
        from secretaria.cli import aplicar_interpretacao_no_terminal
        id=self.aceitar(0)
        with patch('builtins.input',side_effect=[str(id),'','n']),redirect_stdout(StringIO()):
            aplicar_interpretacao_no_terminal(self.banco,self.ctx)
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM projetos').fetchone()[0],0)
        with patch('builtins.input',side_effect=[str(id),'','s']),redirect_stdout(StringIO()) as saida:
            aplicar_interpretacao_no_terminal(self.banco,self.ctx)
        self.assertIn('fontes_vinculadas',saida.getvalue())
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM projetos').fetchone()[0],1)


if __name__=='__main__':
    unittest.main()
