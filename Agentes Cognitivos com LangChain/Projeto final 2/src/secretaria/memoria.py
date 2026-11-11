"""Memória conversacional explícita: turnos confirmados e janela curta para o LLM."""
from datetime import datetime, timezone
from uuid import uuid4


class MemoriaConversas:
    def __init__(self, banco):
        self.banco = banco

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
