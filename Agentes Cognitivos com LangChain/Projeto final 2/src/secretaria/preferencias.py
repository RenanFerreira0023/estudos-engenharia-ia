"""Memória pessoal validada por comando explícito; não deriva fatos da resposta do LLM."""
from datetime import datetime, timezone


VALORES_PERMITIDOS = {
    'estilo': {'curto', 'detalhado'},
    'idioma': {'portugues', 'ingles'},
}


class PreferenciasUsuario:
    def __init__(self, banco):
        self.banco = banco

    def _validar_chave(self, chave):
        if chave not in VALORES_PERMITIDOS:
            raise ValueError('Use estilo=curto/detalhado ou idioma=portugues/ingles.')

    def listar(self, ctx):
        self.banco._usuario(ctx)
        return [dict(linha) for linha in self.banco.con.execute(
            '''SELECT chave,valor,versao FROM preferencias_usuario
               WHERE empresa_id=? AND usuario_id=? ORDER BY chave''',
            (ctx.empresa_id, ctx.usuario_id),
        )]

    def salvar(self, ctx, chave, valor):
        self.banco._usuario(ctx)
        self._validar_chave(chave)
        if valor not in VALORES_PERMITIDOS[chave]:
            raise ValueError('Valor inválido. Use estilo=curto/detalhado ou idioma=portugues/ingles.')
        agora = datetime.now(timezone.utc).isoformat()
        # UPSERT: a nova preferência substitui a anterior somente após comando do usuário.
        # Histórico guarda versões; o agente recebe apenas o valor corrente.
        with self.banco.transacao():
            anterior = self.banco.con.execute(
                '''SELECT valor,versao FROM preferencias_usuario
                   WHERE empresa_id=? AND usuario_id=? AND chave=?''',
                (ctx.empresa_id, ctx.usuario_id, chave),
            ).fetchone()
            if anterior and anterior['valor'] == valor:
                return {'chave': chave, 'valor': valor, 'versao': anterior['versao'],
                        'estado': 'sem_alteracao'}
            versao = (anterior['versao'] + 1) if anterior else 1
            self.banco.con.execute(
                '''INSERT INTO preferencias_usuario(empresa_id,usuario_id,chave,valor,versao,atualizado_em)
                   VALUES (?,?,?,?,?,?) ON CONFLICT(empresa_id,usuario_id,chave)
                   DO UPDATE SET valor=excluded.valor,versao=excluded.versao,
                                 atualizado_em=excluded.atualizado_em''',
                (ctx.empresa_id, ctx.usuario_id, chave, valor, versao, agora),
            )
            self.banco.con.execute(
                '''INSERT INTO historico_preferencias
                   (empresa_id,usuario_id,chave,valor,versao,alterado_em,origem)
                   VALUES (?,?,?,?,?,?,?)''',
                (ctx.empresa_id, ctx.usuario_id, chave, valor, versao, agora,
                 'comando_explicito'),
            )
        return {'chave': chave, 'valor': valor, 'versao': versao, 'estado': 'salva'}

    def apagar(self, ctx, chave):
        self.banco._usuario(ctx)
        self._validar_chave(chave)
        # EXCLUSÃO: apaga também versões antigas para não conservar o valor removido.
        with self.banco.transacao():
            cursor = self.banco.con.execute(
                '''DELETE FROM preferencias_usuario WHERE empresa_id=? AND usuario_id=? AND chave=?''',
                (ctx.empresa_id, ctx.usuario_id, chave),
            )
            self.banco.con.execute(
                '''DELETE FROM historico_preferencias WHERE empresa_id=? AND usuario_id=? AND chave=?''',
                (ctx.empresa_id, ctx.usuario_id, chave),
            )
        return {'chave': chave, 'estado': 'apagada' if cursor.rowcount else 'nao_encontrada'}
