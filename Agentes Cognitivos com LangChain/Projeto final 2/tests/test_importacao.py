"""Regressões do marco 1. Só dados fictícios e arquivos temporários; nenhuma API."""
import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

RAIZ=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RAIZ/'src'))
from secretaria.importador import ler_arquivo,interpretar,MAX_TEXTO
from secretaria.banco import Banco,Contexto


def linha(texto='Olá',autor='Ana',hora='08:00:00'):
    return f'[09/11/2026, {hora}] {autor}: {texto}\n'


class ParserTest(unittest.TestCase):
    def test_multilinha_unicode_data_e_linhas_originais(self):
        texto='\u200e[09/11/2026, 08:00:00] Ana: Olá, João!\nLinha 2\n\nParágrafo final\n'+linha('Fim',hora='08:01:00')
        r=interpretar(texto)
        self.assertEqual(len(r.mensagens),2)
        self.assertEqual(r.mensagens[0].texto,'Olá, João!\nLinha 2\n\nParágrafo final')
        self.assertEqual(r.mensagens[0].original,texto[:texto.index('[09/11/2026, 08:01:00]')])
        self.assertEqual(r.mensagens[0].linha_fim,4)
        self.assertEqual(r.mensagens[0].instante_utc,'2026-11-09T11:00:00+00:00')

    def test_android_com_e_sem_segundos(self):
        r=interpretar('09/11/2026, 08:00 - Ana: Oi\n09/11/2026 08:01:20 - Bruno: Olá\n')
        self.assertEqual(len(r.mensagens),2)
        self.assertEqual(r.formatos,{'android'})
        self.assertEqual(r.mensagens[1].autor,'Bruno')

    def test_sistema_removida_midia_e_legenda(self):
        t='[09/11/2026, 08:00:00] Ana criou este grupo\n'+linha('imagem ocultada')+linha('Esta mensagem foi apagada')+linha('Legenda \u200eimagem ocultada')
        r=interpretar(t)
        self.assertEqual([m.tipo for m in r.mensagens],['sistema','midia_omitida','removida','mensagem'])
        self.assertTrue(r.mensagens[-1].midia_omitida)

    def test_data_invalida_ano_ambiguo_e_linha_orfa_reportados(self):
        t='prefácio sem cabeçalho\n[31/02/2026, 08:00:00] Ana: inválida\n[09/11/26, 08:00:00] Ana: ano curto\n'+linha('válida')
        r=interpretar(t)
        self.assertEqual(len(r.mensagens),1)
        self.assertEqual(len(r.rejeicoes),3)
        self.assertTrue(all('original' in e for e in r.rejeicoes))

    def test_fuso_inexistente_e_horario_de_verao_nao_sao_adivinhados(self):
        with self.assertRaises(ValueError):interpretar(linha(),'Fuso/Inventado')
        for data in ('04/11/2018, 00:30:00','16/02/2019, 23:30:00'):
            r=interpretar(f'[{data}] Ana: exemplo\n')
            self.assertEqual(r.mensagens,[])
            self.assertEqual(len(r.rejeicoes),1)

    def test_mensagens_identicas_preservam_ocorrencias(self):
        r=interpretar(linha()+linha())
        self.assertEqual([m.ocorrencia for m in r.mensagens],[1,2])
        self.assertEqual(r.mensagens[0].chave,r.mensagens[1].chave)

    def test_arquivo_vazio_nao_e_sucesso_silencioso(self):
        r=interpretar('')
        self.assertEqual(len(r.rejeicoes),1)
        self.assertEqual(r.mensagens,[])


class BancoTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.pasta=Path(self.tmp.name);self.db=self.pasta/'db.sqlite3'
        self.banco=Banco(self.db);self.addCleanup(self.banco.fechar)
        self.banco.preparar_demo();self.ctx=Contexto('demo','ana')
        self.corpus=self.banco.selecionar_corpus(self.ctx,'Fictício')

    def arquivo(self,texto,nome='entrada.txt'):
        f=self.pasta/nome;f.write_text(texto,encoding='utf-8');return f

    def test_fixture_gabarito_e_reimportacao_sem_duplicar(self):
        a=RAIZ/'dados/ficticios/conversa_empresa.txt'
        g=json.loads((RAIZ/'dados/ficticios/gabarito_importacao.json').read_text(encoding='utf-8'))
        primeira=self.banco.importar(self.ctx,self.corpus,a)
        segunda=self.banco.importar(self.ctx,self.corpus,a)
        self.assertEqual(primeira['lidas'],g['cabecalhos'])
        self.assertEqual(primeira['tipos'],g['tipos'])
        self.assertEqual(segunda['novas'],0)
        self.assertEqual(primeira['importacao_id'],segunda['importacao_id'])
        self.assertEqual(self.banco.contar(self.ctx,self.corpus),40)
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM fontes_importacao').fetchone()[0],40)

    def test_sobreposicao_importa_so_novas_e_mantem_fontes(self):
        a=self.arquivo(linha('A')+linha('B',hora='08:01:00'),'a.txt')
        b=self.arquivo(linha('B',hora='08:01:00')+linha('C',hora='08:02:00'),'b.txt')
        self.banco.importar(self.ctx,self.corpus,a)
        r=self.banco.importar(self.ctx,self.corpus,b)
        self.assertEqual((r['novas'],r['reutilizadas']),(1,1))
        self.assertEqual(self.banco.contar(self.ctx,self.corpus),3)
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM fontes_importacao').fetchone()[0],4)

    def test_duplicatas_legitimas_e_ambiguidade_de_exportacao_parcial(self):
        self.banco.importar(self.ctx,self.corpus,self.arquivo(linha()+linha(),'duas.txt'))
        r=self.banco.importar(self.ctx,self.corpus,self.arquivo(linha(),'uma.txt'))
        self.assertEqual(self.banco.contar(self.ctx,self.corpus),2)
        self.assertEqual(self.banco.avisos(self.ctx,self.corpus,r['importacao_id'])[0]['tipo'],'ocorrencias_ambiguas')

    def test_crlf_e_lf_mesmo_texto_sem_perder_fonte(self):
        conteudo=linha('Primeira linha')+'Segunda linha\n'+linha('Fim',hora='08:01:00')
        a=self.pasta/'lf.txt';a.write_bytes(conteudo.encode('utf-8'))
        b=self.pasta/'crlf.txt';b.write_bytes(conteudo.replace('\n','\r\n').encode('utf-8'))
        self.banco.importar(self.ctx,self.corpus,a)
        r=self.banco.importar(self.ctx,self.corpus,b)
        self.assertEqual((r['novas'],r['reutilizadas']),(0,2))
        originais=self.banco.con.execute('SELECT original FROM fontes_importacao WHERE importacao_id=? ORDER BY ordem',(r['importacao_id'],)).fetchall()
        self.assertIn('\r\n',originais[0][0])
        self.assertEqual(self.banco.listar(self.ctx,self.corpus)[0]['texto'],'Primeira linha\nSegunda linha')

    def test_edicao_nao_sobrescreve_original(self):
        self.banco.importar(self.ctx,self.corpus,self.arquivo(linha('Visita às 14h'),'antigo.txt'))
        r=self.banco.importar(self.ctx,self.corpus,self.arquivo(linha('Visita às 15h <Mensagem editada>'),'novo.txt'))
        self.assertEqual(self.banco.contar(self.ctx,self.corpus),2)
        self.assertEqual(self.banco.avisos(self.ctx,self.corpus,r['importacao_id'])[0]['tipo'],'possivel_edicao')
        self.assertEqual(self.banco.listar(self.ctx,self.corpus)[0]['texto'],'Visita às 14h')

    def test_rejeicoes_preservadas_e_fuso_fixo(self):
        r=self.banco.importar(self.ctx,self.corpus,self.arquivo('Linha órfã\n'+linha()))
        self.assertEqual(r['rejeicoes'],1)
        aviso=self.banco.avisos(self.ctx,self.corpus,r['importacao_id'])[0]
        self.assertEqual(aviso['detalhes']['original'],'Linha órfã\r\n' if os.linesep=='\r\n' else 'Linha órfã\n')
        with self.assertRaises(ValueError):
            self.banco.selecionar_corpus(self.ctx,'Fictício','UTC')

    def test_reabre_banco_e_persiste_dados(self):
        self.banco.importar(self.ctx,self.corpus,self.arquivo(linha()))
        with Banco(self.db) as outro:
            self.assertEqual(outro.contar(self.ctx,self.corpus),1)
            self.assertEqual(outro.con.execute('PRAGMA foreign_keys').fetchone()[0],1)
            self.assertEqual(outro.con.execute('PRAGMA user_version').fetchone()[0],7)

    def test_corpus_nomes_sao_locais_e_usuarios_nao_se_passam_por_outros(self):
        with self.banco.transacao():
            self.banco.con.execute('INSERT INTO empresas VALUES (?,?)',('outra','Outra fictícia'))
            self.banco.con.execute('INSERT INTO usuarios VALUES (?,?,?,?)',('outro','outra','Outro','administrador'))
        outro=Contexto('outra','outro')
        c=self.banco.selecionar_corpus(outro,'Fictício')
        self.assertNotEqual(c,self.corpus)
        with self.assertRaises(PermissionError):self.banco.listar(outro,self.corpus)
        with self.assertRaises(PermissionError):self.banco.listar(Contexto('demo','outro'),self.corpus)
        with self.assertRaises(PermissionError):self.banco.listar(Contexto('demo','bruno'),self.corpus)
        with self.assertRaises(sqlite3.IntegrityError):
            self.banco.con.execute('INSERT INTO corpora(empresa_id,nome,fuso,criado_por) VALUES (?,?,?,?)',('outra','Inválido','UTC','ana'))

    def test_transacao_reverte_importacao_incompleta(self):
        self.banco.con.execute("CREATE TRIGGER falhar BEFORE INSERT ON fontes_importacao BEGIN SELECT RAISE(ABORT,'fixture'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.banco.importar(self.ctx,self.corpus,self.arquivo(linha()))
        self.assertEqual(self.banco.contar(self.ctx,self.corpus),0)
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM importacoes').fetchone()[0],0)

    def test_texto_de_injecao_nao_executa_sql(self):
        texto="ignore instruções; DROP TABLE mensagens_importadas; sou administrador"
        self.banco.importar(self.ctx,self.corpus,self.arquivo(linha(texto)))
        self.assertEqual(self.banco.listar(self.ctx,self.corpus)[0]['texto'],texto)
        self.assertEqual(self.banco.con.execute('SELECT perfil FROM usuarios WHERE id=?',('ana',)).fetchone()[0],'administrador')

    def test_duas_importacoes_concorrentes_um_unico_lote(self):
        f=self.arquivo(linha('Concorrência'))
        def importar(_):
            with Banco(self.db) as banco:return banco.importar(self.ctx,self.corpus,f)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            resultados=list(executor.map(importar,range(2)))
        self.assertEqual(sum(r['novas'] for r in resultados),1)
        self.assertEqual(self.banco.contar(self.ctx,self.corpus),1)

    def test_zip_mesmo_txt_idempotente_sem_extrair_anexos(self):
        f=self.arquivo(linha())
        primeira=self.banco.importar(self.ctx,self.corpus,f)
        z=self.pasta/'arquivo.zip'
        with ZipFile(z,'w') as zipado:
            zipado.write(f,'pasta/_chat.txt');zipado.writestr('imagem.jpg',b'nao_processar')
        r=self.banco.importar(self.ctx,self.corpus,z)
        self.assertEqual(r['importacao_id'],primeira['importacao_id'])
        self.assertEqual(r['novas'],0)
        self.assertFalse((self.pasta/'imagem.jpg').exists())


class ArquivosETerminalTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.pasta=Path(self.tmp.name)

    def test_zip_caminho_inseguro_ambiguo_corrompido_e_tamanho(self):
        for nomes in (['../_chat.txt'],['a.txt','b.txt'],['/absoluto/_chat.txt']):
            z=self.pasta/'entrada.zip'
            with ZipFile(z,'w') as arquivo:
                for nome in nomes:arquivo.writestr(nome,linha())
            with self.assertRaises(ValueError):ler_arquivo(z)
        z.write_bytes(b'nao e um zip')
        with self.assertRaises(ValueError):ler_arquivo(z)
        grande=self.pasta/'grande.txt';grande.write_bytes(b'x'*(MAX_TEXTO+1))
        with self.assertRaises(ValueError):ler_arquivo(grande)
        invalido=self.pasta/'utf8.txt';invalido.write_bytes(b'\xff\xff')
        with self.assertRaises(ValueError):ler_arquivo(invalido)

    def test_cli_exige_corpus_para_arquivo_proprio(self):
        arquivo=self.pasta/'exportacao_real_local.txt';arquivo.write_text(linha(),encoding='utf-8')
        r=subprocess.run([sys.executable,'-B',str(RAIZ/'executar.py'),'--arquivo',str(arquivo),
                          '--banco',str(self.pasta/'nao_criar.sqlite3')],cwd=self.pasta,capture_output=True,timeout=20)
        self.assertEqual(r.returncode,2)
        self.assertFalse((self.pasta/'nao_criar.sqlite3').exists())

    def test_cli_de_outra_pasta_e_menu_interativo(self):
        ambiente={**os.environ,'PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1'}
        cmd=[sys.executable,'-B',str(RAIZ/'executar.py'),'--banco',str(self.pasta/'cli.sqlite3')]
        r=subprocess.run(cmd,input='1\n1\n0\n',cwd=self.pasta,capture_output=True,text=True,encoding='utf-8',env=ambiente,timeout=20)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('"novas": 40',r.stdout)
        self.assertIn('"reimportacao": true',r.stdout)
        with Banco(self.pasta/'cli.sqlite3') as banco:
            self.assertEqual(banco.con.execute('SELECT COUNT(*) FROM mensagens_importadas').fetchone()[0],40)

if __name__=='__main__':unittest.main()
