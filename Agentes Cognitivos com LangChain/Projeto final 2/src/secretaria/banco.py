"""SQLite local: migração inicial, identidade de demonstração e fontes de importação."""
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime,timezone
import json
from pathlib import Path
import sqlite3
from .importador import ler_arquivo,interpretar


@dataclass(frozen=True)
class Contexto:
    empresa_id: str
    usuario_id: str


# MIGRAÇÃO 1: fontes ficam separadas da mensagem deduplicada. Não há tabelas financeiras ficticiamente prontas.
ESQUEMA='''
BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS empresas(id TEXT PRIMARY KEY,nome TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS usuarios(
 id TEXT PRIMARY KEY,empresa_id TEXT NOT NULL,nome TEXT NOT NULL,perfil TEXT NOT NULL
 CHECK(perfil IN ('administrador','financeiro','atendente')),
 UNIQUE(empresa_id,id),FOREIGN KEY(empresa_id) REFERENCES empresas(id));
CREATE TABLE IF NOT EXISTS corpora(
 id INTEGER PRIMARY KEY,empresa_id TEXT NOT NULL,nome TEXT NOT NULL,fuso TEXT NOT NULL,
 criado_por TEXT NOT NULL,UNIQUE(empresa_id,nome),UNIQUE(empresa_id,id),
 FOREIGN KEY(empresa_id,criado_por) REFERENCES usuarios(empresa_id,id));
CREATE TABLE IF NOT EXISTS importacoes(
 id INTEGER PRIMARY KEY,empresa_id TEXT NOT NULL,corpus_id INTEGER NOT NULL,usuario_id TEXT NOT NULL,
 nome_arquivo TEXT NOT NULL,membro_zip TEXT,hash_arquivo TEXT NOT NULL,hash_texto TEXT NOT NULL,
 texto_original TEXT NOT NULL,criado_em TEXT NOT NULL,fuso TEXT NOT NULL,
 resumo_json TEXT NOT NULL,UNIQUE(corpus_id,hash_texto),UNIQUE(empresa_id,corpus_id,id),
 FOREIGN KEY(empresa_id,corpus_id) REFERENCES corpora(empresa_id,id),
 FOREIGN KEY(empresa_id,usuario_id) REFERENCES usuarios(empresa_id,id));
CREATE TABLE IF NOT EXISTS mensagens_importadas(
 id INTEGER PRIMARY KEY,empresa_id TEXT NOT NULL,corpus_id INTEGER NOT NULL,chave TEXT NOT NULL,
 ocorrencia INTEGER NOT NULL CHECK(ocorrencia>0),data_original TEXT NOT NULL,instante_utc TEXT NOT NULL,
 autor TEXT,texto TEXT NOT NULL,tipo TEXT NOT NULL,editada INTEGER NOT NULL CHECK(editada IN (0,1)),midia_omitida INTEGER NOT NULL CHECK(midia_omitida IN (0,1)),
 UNIQUE(corpus_id,chave,ocorrencia),UNIQUE(empresa_id,corpus_id,id),
 FOREIGN KEY(empresa_id,corpus_id) REFERENCES corpora(empresa_id,id));
CREATE INDEX IF NOT EXISTS mensagens_por_data ON mensagens_importadas(corpus_id,instante_utc,id);
CREATE TABLE IF NOT EXISTS fontes_importacao(
 empresa_id TEXT NOT NULL,corpus_id INTEGER NOT NULL,importacao_id INTEGER NOT NULL,mensagem_id INTEGER NOT NULL,
 ordem INTEGER NOT NULL,linha_inicio INTEGER NOT NULL,linha_fim INTEGER NOT NULL,original TEXT NOT NULL,
 PRIMARY KEY(importacao_id,ordem),
 FOREIGN KEY(empresa_id,corpus_id,importacao_id) REFERENCES importacoes(empresa_id,corpus_id,id),
 FOREIGN KEY(empresa_id,corpus_id,mensagem_id) REFERENCES mensagens_importadas(empresa_id,corpus_id,id));
CREATE TABLE IF NOT EXISTS avisos_importacao(
 id INTEGER PRIMARY KEY,empresa_id TEXT NOT NULL,corpus_id INTEGER NOT NULL,importacao_id INTEGER NOT NULL,
 tipo TEXT NOT NULL,detalhes_json TEXT NOT NULL,
 FOREIGN KEY(empresa_id,corpus_id,importacao_id) REFERENCES importacoes(empresa_id,corpus_id,id));
PRAGMA user_version=1;
COMMIT;
'''


class Banco:
    def __init__(self,caminho):
        self.caminho=Path(caminho)
        self.caminho.parent.mkdir(parents=True,exist_ok=True)
        self.con=sqlite3.connect(self.caminho,isolation_level=None,timeout=10)
        self.con.row_factory=sqlite3.Row
        self.con.execute('PRAGMA foreign_keys=ON')
        versao=self.con.execute('PRAGMA user_version').fetchone()[0]
        if versao==0:
            self.con.executescript(ESQUEMA)
        elif versao not in (1,2,3,4,5,6,7):
            self.con.close()
            raise ValueError('Versão de banco não suportada por este incremento.')
        if self.con.execute('PRAGMA user_version').fetchone()[0]==1:
            from .migracao_revisao import ESQUEMA_REVISAO
            try:
                self.con.executescript(ESQUEMA_REVISAO)
            except BaseException:
                if self.con.in_transaction:
                    self.con.execute('ROLLBACK')
                self.con.close()
                raise
        if self.con.execute('PRAGMA user_version').fetchone()[0]==2:
            from .migracao_agenda import ESQUEMA_AGENDA
            try:
                self.con.executescript(ESQUEMA_AGENDA)
            except BaseException:
                if self.con.in_transaction:
                    self.con.execute('ROLLBACK')
                self.con.close()
                raise
        if self.con.execute('PRAGMA user_version').fetchone()[0]==3:
            from .migracao_cliente_api import ESQUEMA_CLIENTE_API
            try:
                self.con.executescript(ESQUEMA_CLIENTE_API)
            except BaseException:
                if self.con.in_transaction:
                    self.con.execute('ROLLBACK')
                self.con.close()
                raise
        if self.con.execute('PRAGMA user_version').fetchone()[0]==4:
            from .migracao_cadastro_cliente import ESQUEMA_CADASTRO_CLIENTE
            try:
                self.con.executescript(ESQUEMA_CADASTRO_CLIENTE)
            except BaseException:
                if self.con.in_transaction:
                    self.con.execute('ROLLBACK')
                self.con.close()
                raise
        if self.con.execute('PRAGMA user_version').fetchone()[0]==5:
            from .migracao_projetos_fontes import ESQUEMA_PROJETOS_FONTES
            try:
                self.con.executescript(ESQUEMA_PROJETOS_FONTES)
            except BaseException:
                if self.con.in_transaction:
                    self.con.execute('ROLLBACK')
                self.con.close()
                raise
        if self.con.execute('PRAGMA user_version').fetchone()[0]==6:
            from .migracao_memoria import ESQUEMA_MEMORIA
            try:
                self.con.executescript(ESQUEMA_MEMORIA)
            except BaseException:
                if self.con.in_transaction:
                    self.con.execute('ROLLBACK')
                self.con.close()
                raise

    def fechar(self):
        self.con.close()

    def __enter__(self):return self
    def __exit__(self,*_):self.fechar()

    @contextmanager
    def transacao(self):
        # TRANSAÇÃO: confirmação da importação e vínculos são atômicos, inclusive sob concorrência.
        self.con.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.con.execute('COMMIT')
        except BaseException:
            self.con.execute('ROLLBACK')
            raise

    def preparar_demo(self):
        with self.transacao():
            self.con.execute('INSERT OR IGNORE INTO empresas VALUES (?,?)',('demo','Prestadora Acadêmica — fictícia'))
            self.con.executemany('INSERT OR IGNORE INTO usuarios VALUES (?,?,?,?)',[
                ('ana','demo','Ana','administrador'),('bruno','demo','Bruno','financeiro'),('carla','demo','Carla','atendente')])

    def _usuario(self,ctx):
        if not isinstance(ctx,Contexto):
            raise ValueError('Contexto de execução obrigatório.')
        usuario=self.con.execute('SELECT * FROM usuarios WHERE id=? AND empresa_id=?',(ctx.usuario_id,ctx.empresa_id)).fetchone()
        if usuario is None:
            raise PermissionError('Usuário não pertence à empresa selecionada.')
        return usuario

    def _corpus(self,ctx,corpus_id):
        usuario=self._usuario(ctx)
        corpus=self.con.execute('SELECT * FROM corpora WHERE id=? AND empresa_id=?',(corpus_id,ctx.empresa_id)).fetchone()
        if corpus is None:
            raise PermissionError('Corpus não pertence ao contexto selecionado.')
        if corpus['criado_por']!=ctx.usuario_id and usuario['perfil']!='administrador':
            raise PermissionError('Corpus bruto privado do importador; compartilhamento ainda não foi configurado.')
        return corpus

    def selecionar_corpus(self,ctx,nome,fuso='America/Sao_Paulo'):
        self._usuario(ctx)
        if not isinstance(nome,str) or not 1<=len(nome.strip())<=120:
            raise ValueError('Informe nome de corpus com 1 a 120 caracteres.')
        # VALIDAÇÃO DO FUSO ocorre mesmo para corpus vazio, antes de criar metadados inválidos.
        interpretar('',fuso)
        with self.transacao():
            self.con.execute('INSERT OR IGNORE INTO corpora(empresa_id,nome,fuso,criado_por) VALUES (?,?,?,?)',
                             (ctx.empresa_id,nome,fuso,ctx.usuario_id))
            corpus=self.con.execute('SELECT * FROM corpora WHERE empresa_id=? AND nome=?',(ctx.empresa_id,nome)).fetchone()
            if corpus['fuso']!=fuso:
                raise ValueError('Corpus já existe com outro fuso; selecione outro corpus ou mantenha o fuso original.')
        self._corpus(ctx,corpus['id'])
        return corpus['id']

    def importar(self,ctx,corpus_id,caminho):
        corpus=self._corpus(ctx,corpus_id)
        arquivo=ler_arquivo(caminho)
        leitura=interpretar(arquivo.texto,corpus['fuso'])
        with self.transacao():
            # IDEMPOTÊNCIA por conteúdo do TXT + corpus. Mesmo TXT num ZIP não cria nova cópia.
            anterior=self.con.execute('SELECT id,resumo_json FROM importacoes WHERE corpus_id=? AND hash_texto=?',
                                      (corpus_id,arquivo.sha256_texto)).fetchone()
            if anterior:
                return {**json.loads(anterior['resumo_json']),'importacao_id':anterior['id'],'reimportacao':True,
                        'novas':0,'reutilizadas':len(leitura.mensagens)}
            cursor=self.con.execute('''INSERT INTO importacoes(empresa_id,corpus_id,usuario_id,nome_arquivo,membro_zip,
                hash_arquivo,hash_texto,texto_original,criado_em,fuso,resumo_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                (ctx.empresa_id,corpus_id,ctx.usuario_id,arquivo.nome,arquivo.membro_zip,arquivo.sha256_arquivo,
                 arquivo.sha256_texto,arquivo.texto,datetime.now(timezone.utc).isoformat(),corpus['fuso'],'{}'))
            importacao_id=cursor.lastrowid
            novas=0;reutilizadas=0;avisos=[]
            totais=Counter(m.chave for m in leitura.mensagens)
            for chave,total in totais.items():
                existentes=self.con.execute('SELECT COUNT(*) FROM mensagens_importadas WHERE corpus_id=? AND chave=?',
                                           (corpus_id,chave)).fetchone()[0]
                if existentes and (total>1 or existentes>1) and total!=existentes:
                    avisos.append(('ocorrencias_ambiguas',{'chave':chave,'ocorrencias_no_banco':existentes,
                        'ocorrencias_no_arquivo':total,'motivo':'Sem ID nativo, não é possível distinguir qual repetição corresponde a cada exportação parcial.'}))
            for mensagem in leitura.mensagens:
                existente=self.con.execute('SELECT id FROM mensagens_importadas WHERE corpus_id=? AND chave=? AND ocorrencia=?',
                                          (corpus_id,mensagem.chave,mensagem.ocorrencia)).fetchone()
                if existente:
                    mensagem_id=existente['id'];reutilizadas+=1
                else:
                    candidatas=[]
                    if mensagem.editada:
                        candidatas=[r['id'] for r in self.con.execute('''SELECT id FROM mensagens_importadas
                            WHERE corpus_id=? AND instante_utc=? AND autor IS ? AND chave<>?''',
                            (corpus_id,mensagem.instante_utc,mensagem.autor,mensagem.chave))]
                    cursor=self.con.execute('''INSERT INTO mensagens_importadas(empresa_id,corpus_id,chave,ocorrencia,
                        data_original,instante_utc,autor,texto,tipo,editada,midia_omitida) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                        (ctx.empresa_id,corpus_id,mensagem.chave,mensagem.ocorrencia,mensagem.data_original,
                         mensagem.instante_utc,mensagem.autor,mensagem.texto,mensagem.tipo,int(mensagem.editada),int(mensagem.midia_omitida)))
                    mensagem_id=cursor.lastrowid;novas+=1
                    if candidatas:
                        avisos.append(('possivel_edicao',{'mensagem_nova':mensagem_id,'candidatas_anteriores':candidatas,
                            'motivo':'Edição sinalizada; original preservado e resolução manual pendente.'}))
                self.con.execute('INSERT INTO fontes_importacao VALUES (?,?,?,?,?,?,?,?)',
                                 (ctx.empresa_id,corpus_id,importacao_id,mensagem_id,mensagem.ordem,
                                  mensagem.linha_inicio,mensagem.linha_fim,mensagem.original))
            for rejeicao in leitura.rejeicoes:
                avisos.append(('rejeicao',rejeicao))
            for tipo,detalhes in avisos:
                self.con.execute('INSERT INTO avisos_importacao(empresa_id,corpus_id,importacao_id,tipo,detalhes_json) VALUES (?,?,?,?,?)',
                                 (ctx.empresa_id,corpus_id,importacao_id,tipo,json.dumps(detalhes,ensure_ascii=False)))
            tipos=dict(Counter(m.tipo for m in leitura.mensagens))
            resumo={'importacao_id':importacao_id,'corpus_id':corpus_id,'reimportacao':False,'lidas':len(leitura.mensagens),
                    'novas':novas,'reutilizadas':reutilizadas,'rejeicoes':len(leitura.rejeicoes),'avisos':len(avisos),
                    'tipos':tipos,'formatos':sorted(leitura.formatos),'fuso':corpus['fuso'],
                    'origem_fuso':'premissa configurada; não informada no arquivo',
                    'primeiro_instante_utc':min((m.instante_utc for m in leitura.mensagens),default=None),
                    'ultimo_instante_utc':max((m.instante_utc for m in leitura.mensagens),default=None)}
            self.con.execute('UPDATE importacoes SET resumo_json=? WHERE id=?',(json.dumps(resumo,ensure_ascii=False),importacao_id))
            return resumo

    def listar(self,ctx,corpus_id,limite=50):
        self._corpus(ctx,corpus_id)
        if type(limite) is not int or not 1<=limite<=500:
            raise ValueError('Limite deve estar entre 1 e 500.')
        # CONSULTA SQL: parâmetros e empresa/corpus são obrigatórios; ainda não é text-to-query por LLM.
        return [dict(r) for r in self.con.execute('''SELECT id,data_original,instante_utc,autor,texto,tipo,editada,midia_omitida
            FROM mensagens_importadas WHERE empresa_id=? AND corpus_id=? ORDER BY instante_utc,id LIMIT ?''',
            (ctx.empresa_id,corpus_id,limite))]

    def contar(self,ctx,corpus_id):
        self._corpus(ctx,corpus_id)
        return self.con.execute('SELECT COUNT(*) FROM mensagens_importadas WHERE empresa_id=? AND corpus_id=?',
                                (ctx.empresa_id,corpus_id)).fetchone()[0]

    def avisos(self,ctx,corpus_id,importacao_id):
        self._corpus(ctx,corpus_id)
        return [{'tipo':r['tipo'],'detalhes':json.loads(r['detalhes_json'])} for r in self.con.execute(
            'SELECT tipo,detalhes_json FROM avisos_importacao WHERE empresa_id=? AND corpus_id=? AND importacao_id=? ORDER BY id',
            (ctx.empresa_id,corpus_id,importacao_id))]

    def snapshot_analise(self,ctx,corpus_id):
        # SNAPSHOT DE LEITURA: todos os registros autorizados; não usar LIMIT/top-k como análise completa.
        self.con.execute('BEGIN')
        try:
            corpus=self._corpus(ctx,corpus_id)
            quantidade=self.con.execute('SELECT COUNT(*) FROM mensagens_importadas WHERE corpus_id=?',(corpus_id,)).fetchone()[0]
            if quantidade>5000:
                raise ValueError('Este incremento analisa até 5000 mensagens; não houve truncamento silencioso.')
            mensagens=[dict(r) for r in self.con.execute(
                'SELECT id,data_original,instante_utc,autor,texto,tipo,editada,midia_omitida FROM mensagens_importadas WHERE empresa_id=? AND corpus_id=? ORDER BY instante_utc,id',
                (ctx.empresa_id,corpus_id))]
            hashes=[r[0] for r in self.con.execute('SELECT DISTINCT hash_texto FROM importacoes WHERE empresa_id=? AND corpus_id=?',
                                                  (ctx.empresa_id,corpus_id))]
            return {'empresa_id':ctx.empresa_id,'usuario_id':ctx.usuario_id,'corpus_id':corpus_id,
                    'fuso':corpus['fuso'],'mensagens':mensagens,'hashes_importados':hashes}
        finally:
            self.con.execute('ROLLBACK')
