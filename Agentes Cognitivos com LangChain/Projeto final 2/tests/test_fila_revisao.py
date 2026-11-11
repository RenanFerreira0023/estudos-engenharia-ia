"""Integração da revisão com SQLite real e dados fictícios; não usa API."""
import copy
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from secretaria.banco import Banco,Contexto,ESQUEMA
from secretaria.fila_revisao import FilaRevisao
from secretaria.extracao import analisar_snapshot
from secretaria.fixtures_extracao import criar_modelo_fixture
from secretaria.terminal_revisao import revisar_no_terminal

RAIZ=Path(__file__).resolve().parents[1]

class FilaRevisaoTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/'teste.sqlite3'
        self.b=Banco(self.db);self.addCleanup(self.b.fechar)
        self.b.preparar_demo();self.ctx=Contexto('demo','ana')
        self.r=self.gerar(self.ctx,'Fontes Ana');self.f=FilaRevisao(self.b)
        self.cadastro=self.f.registrar_resultado(self.ctx,self.r)
        self.id=self.cadastro['ids'][0]

    def gerar(self,ctx,nome):
        c=self.b.selecionar_corpus(ctx,nome)
        self.b.importar(ctx,c,RAIZ/'dados/ficticios/conversa_empresa.txt')
        return analisar_snapshot(self.b.snapshot_analise(ctx,c),criar_modelo_fixture(),'fixture_manual')

    def test_registro_nao_muda_resultado_e_reimportacao_nao_duplica(self):
        antes=copy.deepcopy(self.r);n=self.b.con.total_changes
        out=self.f.registrar_resultado(self.ctx,self.r)
        self.assertEqual(out['novas'],0);self.assertEqual(self.b.con.total_changes,n)
        self.assertEqual(self.r,antes);self.assertEqual(len(self.f.listar(self.ctx)),8)
        self.assertEqual(len(self.f.historico(self.ctx,self.id)),1)

    def test_aceitar_persiste_e_repeticao_nao_muda_auditoria(self):
        r=self.f.decidir(self.ctx,self.id,1,'aceitar','Conferi a fonte.')
        self.assertEqual((r['estado'],r['versao']),('aceita',2))
        n=self.b.con.total_changes
        repetida=self.f.decidir(self.ctx,self.id,1,'aceitar','Mesmo pedido.')
        self.assertEqual(repetida,r);self.assertEqual(self.b.con.total_changes,n)
        with Banco(self.db) as outro:
            self.assertEqual(FilaRevisao(outro).obter(self.ctx,self.id)['estado'],'aceita')
        self.f.registrar_resultado(self.ctx,self.r)
        self.assertEqual(self.f.obter(self.ctx,self.id)['estado'],'aceita')

    def test_rejeitar_e_nao_reabrir_silenciosamente(self):
        self.f.decidir(self.ctx,self.id,1,'rejeitar','Interpretação inadequada.')
        with self.assertRaises(ValueError):self.f.decidir(self.ctx,self.id,2,'aceitar','Mudei de ideia.')
        with self.assertRaises(ValueError):self.f.corrigir(self.ctx,self.id,2,{'resumo':'Novo'},'Motivo')
        self.assertEqual(self.f.obter(self.ctx,self.id)['estado'],'rejeitada')

    def test_correcao_preserva_original_fontes_antes_depois(self):
        antes=self.f.obter(self.ctx,self.id)
        novo=self.f.corrigir(self.ctx,self.id,1,{'resumo':'Portal de atendimento da Alfa.'},'Clareza do resumo.')
        self.assertEqual((novo['estado'],novo['versao']),('pendente',2))
        self.assertEqual(novo['dados']['fontes'],antes['dados']['fontes'])
        h=self.f.historico(self.ctx,self.id)[1]
        self.assertEqual(json.loads(h['antes_json']),antes['dados'])
        self.assertEqual(json.loads(h['depois_json']),novo['dados'])
        original=self.b.con.execute('SELECT original_json FROM propostas_revisao WHERE id=?',(self.id,)).fetchone()[0]
        self.assertEqual(json.loads(original),antes['dados'])

    def test_versao_antiga_bloqueada_inclusive_outra_conexao(self):
        with Banco(self.db) as outro:
            fila2=FilaRevisao(outro);tela=fila2.obter(self.ctx,self.id)
            self.f.corrigir(self.ctx,self.id,1,{'resumo':'Resumo revisado.'},'Correção.')
            with self.assertRaisesRegex(ValueError,'Versão mudou'):
                fila2.decidir(self.ctx,self.id,tela['versao'],'aceitar','Tela antiga')
        self.assertEqual(self.f.obter(self.ctx,self.id)['estado'],'pendente')

    def test_fontes_area_e_autoria_nao_sao_editaveis(self):
        for campo,valor in [('fontes',[]),('area','financeiro'),('usuario_id','bruno'),('estado','aceita')]:
            with self.assertRaises(ValueError):
                self.f.corrigir(self.ctx,self.id,1,{campo:valor},'Tentativa inválida.')
        self.assertEqual(self.f.obter(self.ctx,self.id)['versao'],1)

    def test_dinheiro_fora_da_fonte_e_contrato_invalido_nao_gravam(self):
        item=next(p for p in self.f.listar(self.ctx) if p['dados']['area']=='financeiro')
        f=copy.deepcopy(item['dados']['financeiro']);f['valor_centavos']=123456
        n=self.b.con.total_changes
        with self.assertRaises(ValueError):
            self.f.corrigir(self.ctx,item['id'],1,{'financeiro':f},'Valor que não está na fonte.')
        self.assertEqual(self.b.con.total_changes,n)
        self.assertEqual(self.f.obter(self.ctx,item['id'])['versao'],1)

    def test_outro_usuario_nao_le_nem_decide_fila_alheia(self):
        ctx=Contexto('demo','bruno')
        self.assertEqual(self.f.listar(ctx),[])
        for operacao in (lambda:self.f.obter(ctx,self.id),
                         lambda:self.f.historico(ctx,self.id),
                         lambda:self.f.decidir(ctx,self.id,1,'aceitar','Tentativa')):
            with self.assertRaises(PermissionError):operacao()

    def test_administrador_nao_confirma_fila_pessoal_de_colega(self):
        bruno=Contexto('demo','bruno');r=self.gerar(bruno,'Fontes Bruno')
        id=self.f.registrar_resultado(bruno,r)['ids'][0]
        with self.assertRaises(PermissionError):self.f.decidir(self.ctx,id,1,'aceitar','Admin não é proprietário.')

    def test_perfis_restringem_areas_antes_de_cadastrar(self):
        for usuario,esperadas in [('bruno',{'financeiro'}),('carla',{'agenda','projeto'})]:
            ctx=Contexto('demo',usuario);r=self.gerar(ctx,'Fontes '+usuario)
            out=self.f.registrar_resultado(ctx,r)
            self.assertGreater(out['restritas_por_perfil'],0)
            self.assertEqual({p['dados']['area'] for p in self.f.listar(ctx)},esperadas)

    def test_usuario_ou_empresa_falsos_sao_negados(self):
        for ctx in [Contexto('demo','naoexiste'),Contexto('outra','ana')]:
            with self.assertRaises(PermissionError):self.f.obter(ctx,self.id)
        r=copy.deepcopy(self.r);r['usuario_id']='bruno'
        with self.assertRaises(PermissionError):self.f.registrar_resultado(self.ctx,r)

    def test_fonte_de_outro_corpus_e_rejeitada_e_transacao_reverte(self):
        r=copy.deepcopy(self.r)
        outro=self.gerar(self.ctx,'Outras fontes')
        r['propostas']=[copy.deepcopy(r['propostas'][0]),copy.deepcopy(outro['propostas'][0])]
        r['propostas'][0]['resumo']='Novo resumo, antes da fonte inválida.'
        n=len(self.f.listar(self.ctx))
        with self.assertRaises(ValueError):self.f.registrar_resultado(self.ctx,r)
        self.assertEqual(len(self.f.listar(self.ctx)),n)

    def test_rejeitada_por_fonte_nao_entra_na_fila(self):
        r=copy.deepcopy(self.r);r['propostas'][0]['status']='rejeitada_por_fonte'
        with self.assertRaises(ValueError):self.f.registrar_resultado(self.ctx,r)

    def test_comentario_e_decisao_validos_sao_obrigatorios(self):
        for comentario in ['',None,' '*10,'x'*1001]:
            with self.assertRaises(ValueError):self.f.decidir(self.ctx,self.id,1,'aceitar',comentario)
        with self.assertRaises(ValueError):self.f.decidir(self.ctx,self.id,1,'apagar','Teste')

    def test_aceite_com_pendencia_nao_cria_registros_operacionais(self):
        agenda=next(p for p in self.f.listar(self.ctx) if p['dados']['area']=='agenda')
        self.assertTrue(agenda['dados']['pendencias'])
        self.f.decidir(self.ctx,agenda['id'],1,'aceitar','Interpretação correta; local ainda pendente.')
        self.assertEqual(self.b.con.execute('SELECT COUNT(*) FROM agendamentos').fetchone()[0],0)
        self.assertEqual(self.b.con.execute('SELECT COUNT(*) FROM projetos').fetchone()[0],0)
        self.assertEqual(self.b.con.execute('SELECT COUNT(*) FROM anotacoes_projeto').fetchone()[0],0)

    def test_terminal_aceita_somente_apos_acao_e_comentario(self):
        out=io.StringIO()
        with patch('builtins.input',side_effect=[str(self.id),'a','Conferido no teste.','']),redirect_stdout(out):
            revisar_no_terminal(self.b,self.ctx)
        self.assertEqual(self.f.obter(self.ctx,self.id)['estado'],'aceita')
        self.assertIn('Nenhum registro operacional',out.getvalue())

    def test_terminal_correcao_invalida_continua_sem_alterar(self):
        with patch('builtins.input',side_effect=[str(self.id),'c','{invalido','']),redirect_stdout(io.StringIO()):
            revisar_no_terminal(self.b,self.ctx)
        self.assertEqual(self.f.obter(self.ctx,self.id)['versao'],1)

    def test_migracao_de_v1_preserva_fontes_e_idempotencia(self):
        caminho=Path(self.tmp.name)/'legado.sqlite3'
        # Simula banco v1 populado: os dados-base foram criados pelo mesmo esquema original.
        with Banco(caminho) as antigo:
            antigo.preparar_demo();c=antigo.selecionar_corpus(self.ctx,'Legado')
            antigo.importar(self.ctx,c,RAIZ/'dados/ficticios/conversa_empresa.txt')
            fontes_antes=antigo.listar(self.ctx,c)
        con=sqlite3.connect(caminho)
        con.execute('DROP TABLE fontes_anotacao')
        con.execute('DROP TABLE anotacoes_projeto')
        con.execute('DROP TABLE projetos')
        con.execute('DROP TABLE auditoria_clientes')
        con.execute('DROP TABLE propostas_cliente')
        con.execute('DROP TABLE consultas_cnpj')
        con.execute('DROP TABLE auditoria_agenda')
        con.execute('DROP TABLE agendamentos')
        con.execute('DROP TABLE propostas_visita')
        con.execute('DROP TABLE clientes')
        con.execute('DROP TABLE historico_revisao')
        con.execute('DROP TABLE propostas_revisao')
        con.execute('PRAGMA user_version=1');con.commit();con.close()
        with Banco(caminho) as novo:
            self.assertEqual(novo.con.execute('PRAGMA user_version').fetchone()[0],7)
            self.assertEqual(novo.listar(self.ctx,c),fontes_antes)
            self.assertEqual(novo.contar(self.ctx,c),40)
            self.assertEqual(novo.importar(self.ctx,c,RAIZ/'dados/ficticios/conversa_empresa.txt')['novas'],0)
