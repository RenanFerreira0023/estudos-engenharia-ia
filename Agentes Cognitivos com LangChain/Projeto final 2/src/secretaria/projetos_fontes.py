"""Aplica interpretações aceitas a projetos, preservando fontes e confirmação separadas."""
import json
from datetime import datetime, timezone

from .fila_revisao import FilaRevisao


def _agora():
    return datetime.now(timezone.utc).isoformat()


class ProjetosFontes:
    def __init__(self, banco):
        self.banco = banco
        self.fila = FilaRevisao(banco)

    def _preparar(self, ctx, proposta_id, projeto_id, cliente_id):
        proposta = self.fila._registro(ctx, proposta_id)
        if proposta['estado'] != 'aceita':
            raise ValueError('A interpretação precisa estar aceita na opção 6.')
        dados = self.fila._validar(ctx, proposta['corpus_id'], json.loads(proposta['atual_json']))
        titulo = (dados.get('projeto') or '').strip()
        if not titulo:
            raise ValueError('A proposta não identifica um projeto; corrija antes de aceitar.')
        if dados['area'] == 'projeto':
            if projeto_id is not None:
                raise ValueError('Proposta de projeto cria novo projeto; não informe projeto existente.')
            if cliente_id is not None:
                if type(cliente_id) is not int or cliente_id < 1:
                    raise ValueError('ID do cliente inválido.')
                cliente = self.banco.con.execute('SELECT id FROM clientes WHERE empresa_id=? AND id=?',
                                                  (ctx.empresa_id, cliente_id)).fetchone()
                if cliente is None:
                    raise ValueError('Cliente não pertence a esta empresa.')
            destino = None
        else:
            if cliente_id is not None:
                raise ValueError('Cliente só pode ser escolhido ao criar o projeto.')
            if type(projeto_id) is not int or projeto_id < 1:
                raise ValueError('Informe explicitamente o ID do projeto de destino.')
            destino = self.banco.con.execute('SELECT id,titulo FROM projetos WHERE empresa_id=? AND id=?',
                                              (ctx.empresa_id, projeto_id)).fetchone()
            if destino is None:
                raise ValueError('Projeto não pertence a esta empresa.')
            if destino['titulo'].strip().casefold() != titulo.casefold():
                raise ValueError('Nome da proposta diverge do projeto escolhido; revise o vínculo.')
        return proposta, dados, titulo, destino

    def prever(self, ctx, proposta_id, projeto_id=None, cliente_id=None):
        """Mostra a interpretação e suas fontes; não cria registro operacional."""
        proposta, dados, titulo, _ = self._preparar(ctx, proposta_id, projeto_id, cliente_id)
        return {'proposta_id':proposta_id,'versao':proposta['versao'],'acao':
                'criar_projeto' if dados['area']=='projeto' else 'anotar_projeto',
                'projeto':titulo,'projeto_id':projeto_id,'cliente_id':cliente_id,
                'area':dados['area'],'natureza':dados['natureza'],'resumo':dados['resumo'],
                'fontes':dados['fontes'],
                'limite':'Anotação financeira não é pagamento; anotação de agenda não reserva horário.'}

    def confirmar(self, ctx, proposta_id, versao, projeto_id=None, cliente_id=None):
        """Confirma uma proposta aceita sob BEGIN IMMEDIATE, com fonte e destino revalidados."""
        if type(versao) is not int or versao < 1:
            raise ValueError('Informe a versão mostrada na prévia.')
        with self.banco.transacao():
            proposta, dados, titulo, _ = self._preparar(ctx, proposta_id, projeto_id, cliente_id)
            if proposta['versao'] != versao:
                raise ValueError('Versão mudou; confira nova prévia antes de confirmar.')
            anterior = self.banco.con.execute('''SELECT id,projeto_id FROM anotacoes_projeto
                WHERE empresa_id=? AND proposta_id=?''',(ctx.empresa_id,proposta_id)).fetchone()
            if anterior:
                if projeto_id is not None and anterior['projeto_id'] != projeto_id:
                    raise ValueError('Proposta já foi aplicada a outro projeto.')
                if dados['area']=='projeto' and cliente_id is not None:
                    projeto_salvo=self.banco.con.execute('SELECT cliente_id FROM projetos WHERE empresa_id=? AND id=?',
                        (ctx.empresa_id,anterior['projeto_id'])).fetchone()
                    if projeto_salvo['cliente_id']!=cliente_id:
                        raise ValueError('Proposta já foi aplicada com outro vínculo de cliente.')
                return {'estado':'ja_confirmada','projeto_id':anterior['projeto_id'],
                        'anotacao_id':anterior['id']}
            agora = _agora()
            if dados['area'] == 'projeto':
                cur = self.banco.con.execute('''INSERT INTO projetos
                    (empresa_id,cliente_id,titulo,resumo,status,origem_proposta_id,criado_por,criado_em,versao)
                    VALUES (?,?,?,?,'em_levantamento',?,?,?,1)''',
                    (ctx.empresa_id,cliente_id,titulo,dados['resumo'],proposta_id,ctx.usuario_id,agora))
                projeto_id = cur.lastrowid
            cur = self.banco.con.execute('''INSERT INTO anotacoes_projeto
                (empresa_id,projeto_id,proposta_id,corpus_id,area,natureza,resumo,dados_json,criado_por,criado_em)
                VALUES (?,?,?,?,?,?,?,?,?,?)''',
                (ctx.empresa_id,projeto_id,proposta_id,proposta['corpus_id'],dados['area'],
                 dados['natureza'],dados['resumo'],json.dumps(dados,ensure_ascii=False),ctx.usuario_id,agora))
            anotacao_id = cur.lastrowid
            for fonte in dados['fontes']:
                self.banco.con.execute('''INSERT INTO fontes_anotacao
                    (empresa_id,corpus_id,anotacao_id,mensagem_id,trecho_snapshot)
                    VALUES (?,?,?,?,?)''',
                    (ctx.empresa_id,proposta['corpus_id'],anotacao_id,fonte['mensagem_id'],fonte['trecho']))
            return {'estado':'confirmada','projeto_id':projeto_id,'anotacao_id':anotacao_id,
                    'fontes_vinculadas':len(dados['fontes'])}

    def fontes(self, ctx, anotacao_id):
        """Consulta fontes apenas se o usuário tem acesso ao corpus da anotação."""
        self.banco._usuario(ctx)
        anotacao = self.banco.con.execute('''SELECT * FROM anotacoes_projeto
            WHERE empresa_id=? AND id=?''',(ctx.empresa_id,anotacao_id)).fetchone()
        if anotacao is None:
            raise ValueError('Anotação não localizada nesta empresa.')
        self.banco._corpus(ctx,anotacao['corpus_id'])
        self.fila._permitir_area(ctx,anotacao['area'])
        return [dict(r) for r in self.banco.con.execute('''SELECT f.mensagem_id,f.trecho_snapshot,
            m.data_original,m.autor FROM fontes_anotacao f
            JOIN mensagens_importadas m ON m.empresa_id=f.empresa_id AND m.corpus_id=f.corpus_id
            AND m.id=f.mensagem_id WHERE f.empresa_id=? AND f.anotacao_id=? ORDER BY f.mensagem_id''',
            (ctx.empresa_id,anotacao_id))]
