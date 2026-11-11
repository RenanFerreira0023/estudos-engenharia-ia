"""Memória conversacional explícita: turnos confirmados e janela curta para o LLM."""
from datetime import datetime, timezone
from difflib import SequenceMatcher
import re
import unicodedata
from uuid import uuid4


_PALAVRAS_VAZIAS = {'a','as','o','os','de','do','da','dos','das','e','em','um','uma','eu','voce',
                   'meu','minha','que','qual','quais','foi','com','para','por','agora','aqui',
                   'mencionei','falei','disse','sobre','tem','estou'}


def pede_contexto_antigo(pergunta):
    """Evita trazer recortes em cumprimentos e pedidos independentes."""
    texto = ''.join(c for c in unicodedata.normalize('NFKD', pergunta.lower())
                    if not unicodedata.combining(c))
    return bool(re.search(
        r'\b(mencionei|falei|disse|lembra|lembrar|antes|anterior|antigo|antiga|'
        r'comeco|inicio|dele|dela|desse|dessa|daquele|daquela)\b', texto))


def _termos(texto):
    simples = ''.join(c for c in unicodedata.normalize('NFKD', texto.lower())
                      if not unicodedata.combining(c))
    return {termo for termo in re.findall(r'[a-z0-9]{3,}', simples)
            if termo not in _PALAVRAS_VAZIAS}


def _pontuar_termos(pergunta, resumo):
    """Exato vale mais; aproximação admite uma pequena troca de letras."""
    termos_resumo = _termos(resumo)
    pontos = 0
    aproximados = False
    for termo in _termos(pergunta):
        if termo in termos_resumo:
            pontos += 2
        elif len(termo) >= 5 and any(
            len(outro) >= 5 and abs(len(termo) - len(outro)) <= 1
            and SequenceMatcher(None, termo, outro, autojunk=False).ratio() >= 0.84
            for outro in termos_resumo
        ):
            pontos += 1
            aproximados = True
    return pontos, aproximados


class MemoriaConversas:
    def __init__(self, banco):
        self.banco = banco
        # Cache apenas em RAM durante o processo; os recortes originais persistem no SQLite.
        self._vetores = {}

    def _sessao(self, ctx, sessao_id):
        self.banco._usuario(ctx)
        linha = self.banco.con.execute(
            'SELECT * FROM sessoes_agente WHERE id=? AND empresa_id=? AND usuario_id=?',
            (sessao_id, ctx.empresa_id, ctx.usuario_id),
        ).fetchone()
        if linha is None:
            raise PermissionError('Conversa não pertence ao usuário atual.')
        return linha

    def iniciar(self, ctx):
        self.banco._usuario(ctx)
        sessao_id = uuid4().hex
        with self.banco.transacao():
            self.banco.con.execute(
                'INSERT INTO sessoes_agente(id,empresa_id,usuario_id,criada_em) VALUES (?,?,?,?)',
                (sessao_id, ctx.empresa_id, ctx.usuario_id, datetime.now(timezone.utc).isoformat()),
            )
        return sessao_id

    def ultima_ativa(self, ctx):
        self.banco._usuario(ctx)
        linha = self.banco.con.execute(
            '''SELECT id FROM sessoes_agente WHERE empresa_id=? AND usuario_id=?
               AND encerrada_em IS NULL ORDER BY criada_em DESC, rowid DESC LIMIT 1''',
            (ctx.empresa_id, ctx.usuario_id),
        ).fetchone()
        return linha['id'] if linha else None

    def encerrar(self, ctx, sessao_id):
        self._sessao(ctx, sessao_id)
        with self.banco.transacao():
            self.banco.con.execute(
                'UPDATE sessoes_agente SET encerrada_em=? WHERE id=? AND encerrada_em IS NULL',
                (datetime.now(timezone.utc).isoformat(), sessao_id),
            )

    def registrar(self, ctx, sessao_id, pergunta, resposta):
        sessao = self._sessao(ctx, sessao_id)
        if sessao['encerrada_em']:
            raise ValueError('Conversa encerrada; inicie outra.')
        if not isinstance(pergunta, str) or not pergunta.strip():
            raise ValueError('Pergunta vazia.')
        if not isinstance(resposta, str) or not resposta.strip():
            raise ValueError('Resposta vazia.')
        with self.banco.transacao():
            self.banco.con.execute(
                '''INSERT INTO turnos_agente(sessao_id,empresa_id,usuario_id,pergunta,resposta,criado_em)
                   VALUES (?,?,?,?,?,?)''',
                (sessao_id, ctx.empresa_id, ctx.usuario_id, pergunta.strip(), resposta.strip(),
                 datetime.now(timezone.utc).isoformat()),
            )
            # RESUMO EXTRATIVO: ao sair da janela, guardamos só a fala do usuário
            # com ID de origem. Não inferimos fatos nem copiamos respostas do modelo.
            corte = self.banco.con.execute(
                '''SELECT id FROM turnos_agente WHERE sessao_id=? AND empresa_id=? AND usuario_id=?
                   ORDER BY id DESC LIMIT 1 OFFSET 5''',
                (sessao_id, ctx.empresa_id, ctx.usuario_id),
            ).fetchone()
            if corte:
                antigos = self.banco.con.execute(
                    '''SELECT id,pergunta FROM turnos_agente WHERE sessao_id=? AND empresa_id=?
                       AND usuario_id=? AND id<? AND id NOT IN
                       (SELECT turno_id FROM resumos_turnos_agente WHERE sessao_id=? AND empresa_id=? AND usuario_id=?)
                       ORDER BY id''',
                    (sessao_id, ctx.empresa_id, ctx.usuario_id, corte['id'],
                     sessao_id, ctx.empresa_id, ctx.usuario_id),
                ).fetchall()
                for turno in antigos:
                    resumo = ' '.join(turno['pergunta'].split())[:500]
                    self.banco.con.execute(
                        '''INSERT INTO resumos_turnos_agente
                           (sessao_id,empresa_id,usuario_id,turno_id,resumo,criado_em)
                           VALUES (?,?,?,?,?,?)''',
                        (sessao_id, ctx.empresa_id, ctx.usuario_id, turno['id'], resumo,
                         datetime.now(timezone.utc).isoformat()),
                    )

    def buscar_resumos(self, ctx, sessao_id, pergunta, limite=2):
        """Busca lexical nos recortes antigos da mesma conversa, sem busca vetorial."""
        self._sessao(ctx, sessao_id)
        if type(limite) is not int or not 1 <= limite <= 5:
            raise ValueError('Limite de resumos deve ser de 1 a 5.')
        termos = _termos(pergunta)
        if not termos:
            return []
        # CONSULTA: escopo por empresa, usuário e sessão antes da pontuação.
        # Os 500 recortes mais recentes limitam custo; FAISS entra na fase 4.
        linhas = self.banco.con.execute(
            '''SELECT turno_id,resumo FROM resumos_turnos_agente
               WHERE sessao_id=? AND empresa_id=? AND usuario_id=? ORDER BY turno_id DESC LIMIT 500''',
            (sessao_id, ctx.empresa_id, ctx.usuario_id),
        ).fetchall()
        pontuados = [(*_pontuar_termos(pergunta, linha['resumo']),
                      linha['turno_id'], linha['resumo']) for linha in linhas]
        pontuados = [item for item in pontuados if item[0] > 0]
        pontuados.sort(key=lambda item: (item[0], item[2]), reverse=True)
        return [{'turno_id': turno_id, 'resumo_extrativo': resumo,
                 'pontuacao_lexical': pontos,
                 'tipo_correspondencia': 'aproximada' if aproximados else 'exata'}
                for pontos, aproximados, turno_id, resumo in pontuados[:limite]]

    def buscar_resumos_vetoriais(self, ctx, sessao_id, pergunta, embeddings, limite=2,
                                 similaridade_minima=0.35):
        """FAISS sobre recortes da sessão autorizada; embeddings são injetados para teste offline."""
        import faiss
        import numpy as np

        self._sessao(ctx, sessao_id)
        if type(limite) is not int or not 1 <= limite <= 5:
            raise ValueError('Limite de resumos deve ser de 1 a 5.')
        if not isinstance(pergunta, str) or not pergunta.strip():
            return []
        # ESCOPO: filtrar no SQLite antes de construir o índice evita resultados de outro usuário.
        linhas = self.banco.con.execute(
            '''SELECT turno_id,resumo FROM resumos_turnos_agente
               WHERE sessao_id=? AND empresa_id=? AND usuario_id=? ORDER BY turno_id DESC LIMIT 500''',
            (sessao_id, ctx.empresa_id, ctx.usuario_id),
        ).fetchall()
        if not linhas:
            return []
        faltantes = [linha for linha in linhas if (ctx.empresa_id,ctx.usuario_id,sessao_id,
                                                    linha['turno_id'],linha['resumo']) not in self._vetores]
        if faltantes:
            novos = embeddings.embed_documents([linha['resumo'] for linha in faltantes])
            if len(novos) != len(faltantes):
                raise ValueError('Embedding retornou quantidade inesperada de vetores.')
            for linha, vetor in zip(faltantes, novos):
                chave = (ctx.empresa_id,ctx.usuario_id,sessao_id,linha['turno_id'],linha['resumo'])
                self._vetores[chave] = vetor
        matriz = np.asarray([self._vetores[(ctx.empresa_id,ctx.usuario_id,sessao_id,
                                           linha['turno_id'],linha['resumo'])] for linha in linhas],
                            dtype='float32')
        consulta = np.asarray([embeddings.embed_query(pergunta)],dtype='float32')
        if matriz.ndim != 2 or consulta.ndim != 2 or matriz.shape[1] != consulta.shape[1]:
            raise ValueError('Dimensões dos embeddings incompatíveis.')
        faiss.normalize_L2(matriz)
        faiss.normalize_L2(consulta)
        indice = faiss.IndexFlatIP(matriz.shape[1])
        indice.add(matriz)
        escores, posicoes = indice.search(consulta,min(limite,len(linhas)))
        return [{'turno_id':linhas[int(posicao)]['turno_id'],
                 'resumo_extrativo':linhas[int(posicao)]['resumo'],
                 'similaridade':round(float(escore),4),
                 'estrategia':'faiss_embeddings'}
                for escore,posicao in zip(escores[0],posicoes[0])
                if posicao >= 0 and escore >= similaridade_minima]

    def ultimos(self, ctx, sessao_id, limite=6):
        self._sessao(ctx, sessao_id)
        if type(limite) is not int or not 1 <= limite <= 20:
            raise ValueError('Janela deve conter de 1 a 20 turnos.')
        linhas = self.banco.con.execute(
            '''SELECT pergunta,resposta FROM turnos_agente WHERE sessao_id=? AND empresa_id=?
               AND usuario_id=? ORDER BY id DESC LIMIT ?''',
            (sessao_id, ctx.empresa_id, ctx.usuario_id, limite),
        ).fetchall()
        return [dict(linha) for linha in reversed(linhas)]

    def mensagens(self, ctx, sessao_id, limite=6):
        mensagens = []
        for turno in self.ultimos(ctx, sessao_id, limite):
            mensagens.extend(({'role': 'user', 'content': turno['pergunta']},
                              {'role': 'assistant', 'content': turno['resposta']}))
        return mensagens
