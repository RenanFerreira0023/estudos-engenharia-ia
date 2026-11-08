"""Memória explícita de demonstração: SQLite, janela de turnos e resumos vetoriais."""
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sqlite3
from threading import RLock
from uuid import uuid4


def agora():
    return datetime.now(timezone.utc).isoformat()


def identidade(valor):
    if not isinstance(valor, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', valor):
        raise ValueError('Identidade de demonstração deve ter 1 a 64 letras, números, _ ou -.')
    return valor


def vetor_normalizado(valores):
    if not isinstance(valores, (list, tuple)) or not 1 <= len(valores) <= 4096:
        raise ValueError('Dimensão vetorial inválida.')
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in valores):
        raise ValueError('Embedding inválido.')
    norma = math.sqrt(sum(v*v for v in valores))
    if not math.isfinite(norma) or norma == 0:
        raise ValueError('Embedding nulo ou inválido.')
    return [v/norma for v in valores]


class MemoriaSQLite:
    def __init__(self, arquivo, embeddings=None, modelo_embedding=None, janela_turnos=6):
        if not isinstance(janela_turnos, int) or not 1 <= janela_turnos <= 20:
            raise ValueError('Janela deve ter entre 1 e 20 turnos completos.')
        self.janela_turnos = janela_turnos
        self.embeddings = embeddings
        self.modelo_embedding = modelo_embedding or getattr(embeddings, 'model', None)
        if embeddings is not None and not self.modelo_embedding:
            raise ValueError('Identifique o espaço/modelo de embeddings.')
        caminho = Path(arquivo)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self.trava = RLock()
        self.conexao = sqlite3.connect(caminho, check_same_thread=False)
        self.conexao.row_factory = sqlite3.Row
        # STORE persiste dados por cliente e sessão; SQL sempre parametrizado.
        self.conexao.executescript('''
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS sessoes (
                id TEXT PRIMARY KEY, cliente TEXT NOT NULL, criada_em TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS turnos (
                id INTEGER PRIMARY KEY, sessao TEXT NOT NULL REFERENCES sessoes(id),
                pergunta TEXT NOT NULL, resposta TEXT NOT NULL, criado_em TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS perfis (
                cliente TEXT PRIMARY KEY, veiculo TEXT NOT NULL, confirmado_em TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS resumos (
                id TEXT PRIMARY KEY, cliente TEXT NOT NULL, texto TEXT NOT NULL,
                vetor TEXT NOT NULL, modelo TEXT NOT NULL, criado_em TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_turnos_sessao ON turnos(sessao,id);
            CREATE INDEX IF NOT EXISTS idx_resumos_cliente ON resumos(cliente,modelo);
        ''')

    def abrir_sessao(self, cliente, sessao=None):
        cliente = identidade(cliente)
        with self.trava, self.conexao:
            if sessao is not None:
                self._validar_sessao(cliente, sessao)
                return sessao
            sessao = uuid4().hex
            self.conexao.execute('INSERT INTO sessoes VALUES (?,?,?)',(sessao,cliente,agora()))
            return sessao

    def _validar_sessao(self, cliente, sessao):
        identidade(cliente)
        identidade(sessao)
        if not self.conexao.execute('SELECT 1 FROM sessoes WHERE id=? AND cliente=?',(sessao,cliente)).fetchone():
            raise PermissionError('Sessão inexistente ou pertencente a outro cliente de demonstração.')

    def historico(self, cliente, sessao):
        with self.trava:
            self._validar_sessao(cliente,sessao)
            # JANELA mantém pares completos; não corta uma resposta separada da pergunta.
            linhas = self.conexao.execute('SELECT pergunta,resposta FROM turnos WHERE sessao=? ORDER BY id DESC LIMIT ?',
                                          (sessao,self.janela_turnos)).fetchall()
        return [msg for r in reversed(linhas) for msg in ({'role':'user','content':r['pergunta']},{'role':'assistant','content':r['resposta']})]

    def registrar_turno(self, cliente, sessao, pergunta, resposta):
        if not isinstance(pergunta,str) or not pergunta.strip() or not isinstance(resposta,str) or not resposta.strip():
            raise ValueError('Turno completo obrigatório.')
        with self.trava, self.conexao:
            self._validar_sessao(cliente,sessao)
            self.conexao.execute('INSERT INTO turnos(sessao,pergunta,resposta,criado_em) VALUES (?,?,?,?)',
                                 (sessao,pergunta,resposta,agora()))

    def confirmar_veiculo(self, cliente, veiculo):
        identidade(cliente)
        if not isinstance(veiculo, dict) or not veiculo.get('id'):
            raise ValueError('Veículo cadastrado obrigatório.')
        with self.trava, self.conexao:
            # UPSERT substitui o perfil atual, sem acumular veículos antigos como atuais.
            self.conexao.execute('''INSERT INTO perfis VALUES (?,?,?) ON CONFLICT(cliente)
                DO UPDATE SET veiculo=excluded.veiculo,confirmado_em=excluded.confirmado_em''',
                (cliente,json.dumps(veiculo,ensure_ascii=False),agora()))

    def perfil(self, cliente):
        identidade(cliente)
        with self.trava:
            r = self.conexao.execute('SELECT veiculo,confirmado_em FROM perfis WHERE cliente=?',(cliente,)).fetchone()
        return {'veiculo_confirmado':json.loads(r['veiculo']),'confirmado_em':r['confirmado_em']} if r else None

    def guardar_resumo(self, cliente, texto):
        identidade(cliente)
        if not isinstance(texto,str) or not 1 <= len(texto.strip()) <= 1000:
            raise ValueError('Resumo confirmado deve ter de 1 a 1000 caracteres.')
        if self.embeddings is None:
            raise RuntimeError('Recuperação vetorial desativada explicitamente.')
        # EMBEDDINGS transforma o resumo autorizado; não extrai fatos ocultos do histórico.
        try:
            vetor = vetor_normalizado(self.embeddings.embed_documents([texto.strip()])[0])
        except Exception as erro:
            raise RuntimeError(f'Resumo não salvo: falha na vetorização ({type(erro).__name__}).') from None
        chave = uuid4().hex
        with self.trava, self.conexao:
            self.conexao.execute('INSERT INTO resumos VALUES (?,?,?,?,?,?)',
                                (chave,cliente,texto.strip(),json.dumps(vetor),self.modelo_embedding,agora()))
        return chave

    def recuperar(self, cliente, pergunta, limite=3, similaridade_minima=0.2):
        identidade(cliente)
        if self.embeddings is None:
            return {'status':'vetores_desativados','resumos':[]}
        if not 1 <= limite <= 5 or not -1 <= similaridade_minima <= 1:
            raise ValueError('Parâmetros de recuperação inválidos.')
        with self.trava:
            # NAMESPACE/CHAVE: filtra cliente E modelo antes da busca e de enviar a pergunta ao provedor.
            linhas = self.conexao.execute('SELECT id,texto,vetor,criado_em FROM resumos WHERE cliente=? AND modelo=?',
                                          (cliente,self.modelo_embedding)).fetchall()
        if not linhas:
            return {'status':'sem_resumos','resumos':[]}
        consulta = vetor_normalizado(self.embeddings.embed_query(pergunta))
        achados = []
        for r in linhas:
            vetor = vetor_normalizado(json.loads(r['vetor']))
            if len(vetor) != len(consulta):
                raise ValueError('Espaços vetoriais incompatíveis; reindexe os resumos.')
            similaridade = sum(a*b for a,b in zip(vetor,consulta))
            if similaridade >= similaridade_minima:
                achados.append({'id':r['id'],'texto':r['texto'],'criado_em':r['criado_em'],'similaridade':similaridade})
        return {'status':'ok','modelo_embedding':self.modelo_embedding,
                'resumos':sorted(achados,key=lambda x:x['similaridade'],reverse=True)[:limite]}

    def esquecer(self, cliente):
        identidade(cliente)
        with self.trava, self.conexao:
            # EXCLUSÃO também limpa contexto curto para não ressuscitar informação apagada.
            self.conexao.execute('DELETE FROM turnos WHERE sessao IN (SELECT id FROM sessoes WHERE cliente=?)',(cliente,))
            self.conexao.execute('DELETE FROM perfis WHERE cliente=?',(cliente,))
            self.conexao.execute('DELETE FROM resumos WHERE cliente=?',(cliente,))

    def fechar(self):
        self.conexao.close()
