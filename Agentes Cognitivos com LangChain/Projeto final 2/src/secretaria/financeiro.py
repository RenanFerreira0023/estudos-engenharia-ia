"""Financeiro operacional local: dinheiro em centavos e confirmação humana explícita."""
from datetime import date, datetime, timezone
import json


def _agora():
    return datetime.now(timezone.utc).isoformat()


def _inteiro_positivo(valor, nome):
    if type(valor) is not int or valor <= 0:
        raise ValueError(f'{nome} deve ser inteiro positivo em centavos.')


def _data(valor, nome):
    if valor is None or valor == '':
        return None
    if type(valor) is not str:
        raise ValueError(f'{nome} deve usar AAAA-MM-DD.')
    try:
        return date.fromisoformat(valor).isoformat()
    except ValueError as erro:
        raise ValueError(f'{nome} deve usar AAAA-MM-DD.') from erro


class Financeiro:
    """Controle de orçamento, parcelas e pagamentos com histórico auditável."""
    def __init__(self, banco):
        self.banco = banco

    def _permitir(self, ctx):
        perfil = self.banco._usuario(ctx)['perfil']
        if perfil not in ('administrador', 'financeiro'):
            raise PermissionError('Perfil sem acesso ao financeiro.')

    def _auditar(self, ctx, entidade, entidade_id, acao, detalhes):
        self.banco.con.execute(
            '''INSERT INTO auditoria_financeiro
               (empresa_id,usuario_id,entidade,entidade_id,acao,detalhes_json,instante)
               VALUES (?,?,?,?,?,?,?)''',
            (ctx.empresa_id,ctx.usuario_id,entidade,entidade_id,acao,
             json.dumps(detalhes,ensure_ascii=False,sort_keys=True),_agora()))

    def _orcamento(self, ctx, orcamento_id):
        self._permitir(ctx)
        if type(orcamento_id) is not int or orcamento_id < 1:
            raise ValueError('ID do orçamento inválido.')
        linha = self.banco.con.execute(
            'SELECT * FROM orcamentos WHERE empresa_id=? AND id=?',
            (ctx.empresa_id,orcamento_id)).fetchone()
        if linha is None:
            raise ValueError('Orçamento não encontrado nesta empresa.')
        return linha

    def criar_orcamento(self, ctx, projeto_id, valor_centavos, percentual_entrada=None):
        self._permitir(ctx)
        _inteiro_positivo(valor_centavos,'Valor do orçamento')
        if percentual_entrada is not None and (
                type(percentual_entrada) is not int or not 0 <= percentual_entrada <= 100):
            raise ValueError('Percentual de entrada deve estar entre 0 e 100.')
        if type(projeto_id) is not int or projeto_id < 1:
            raise ValueError('ID do projeto inválido.')
        with self.banco.transacao():
            projeto = self.banco.con.execute(
                'SELECT id FROM projetos WHERE empresa_id=? AND id=?',
                (ctx.empresa_id,projeto_id)).fetchone()
            if projeto is None:
                raise ValueError('Projeto não encontrado nesta empresa.')
            revisao = self.banco.con.execute(
                'SELECT COALESCE(MAX(revisao),0)+1 FROM orcamentos WHERE empresa_id=? AND projeto_id=?',
                (ctx.empresa_id,projeto_id)).fetchone()[0]
            cur = self.banco.con.execute(
                '''INSERT INTO orcamentos
                   (empresa_id,projeto_id,revisao,valor_centavos,percentual_entrada_acordado,
                    status,criado_por,criado_em)
                   VALUES (?,?,?,?,?,'proposto',?,?)''',
                (ctx.empresa_id,projeto_id,revisao,valor_centavos,
                 percentual_entrada,ctx.usuario_id,_agora()))
            self._auditar(ctx,'orcamento',cur.lastrowid,'propor',
                          {'projeto_id':projeto_id,'valor_centavos':valor_centavos,
                           'revisao':revisao,'percentual_entrada_acordado':percentual_entrada})
        return {'orcamento_id':cur.lastrowid,'projeto_id':projeto_id,
                'revisao':revisao,'status':'proposto'}

    def aceitar_orcamento(self, ctx, orcamento_id):
        with self.banco.transacao():
            atual = self._orcamento(ctx,orcamento_id)
            if atual['status']=='aceito':
                return {'orcamento_id':orcamento_id,'status':'ja_aceito'}
            outro = self.banco.con.execute(
                """SELECT o.id FROM orcamentos o WHERE o.empresa_id=? AND o.projeto_id=?
                   AND o.status='aceito' AND NOT EXISTS
                   (SELECT 1 FROM substituicoes_orcamento s
                    WHERE s.empresa_id=o.empresa_id AND s.anterior_id=o.id)""",
                (ctx.empresa_id,atual['projeto_id'])).fetchone()
            if outro:
                raise ValueError('Já existe orçamento ativo; use a substituição com motivo.')
            agora = _agora()
            self.banco.con.execute(
                "UPDATE orcamentos SET status='aceito',aceito_por=?,aceito_em=? WHERE id=?",
                (ctx.usuario_id,agora,orcamento_id))
            self._auditar(ctx,'orcamento',orcamento_id,'aceitar',
                          {'projeto_id':atual['projeto_id'],'valor_centavos':atual['valor_centavos']})
        return {'orcamento_id':orcamento_id,'status':'aceito'}

    def substituir_orcamento(self, ctx, novo_id, motivo):
        """Aceita nova revisão e conserva o orçamento anterior no histórico."""
        if not isinstance(motivo,str) or not 5 <= len(motivo.strip()) <= 500:
            raise ValueError('Informe o motivo da substituição (5 a 500 caracteres).')
        with self.banco.transacao():
            novo = self._orcamento(ctx,novo_id)
            existente = self.banco.con.execute(
                'SELECT anterior_id FROM substituicoes_orcamento WHERE empresa_id=? AND novo_id=?',
                (ctx.empresa_id,novo_id)).fetchone()
            if existente:
                return {'orcamento_id':novo_id,'anterior_id':existente['anterior_id'],'status':'ja_substituido'}
            if novo['status']!='proposto':
                raise ValueError('A nova revisão precisa estar proposta.')
            anterior = self.banco.con.execute(
                """SELECT o.id FROM orcamentos o WHERE o.empresa_id=? AND o.projeto_id=?
                   AND o.status='aceito' AND NOT EXISTS
                   (SELECT 1 FROM substituicoes_orcamento s
                    WHERE s.empresa_id=o.empresa_id AND s.anterior_id=o.id)""",
                (ctx.empresa_id,novo['projeto_id'])).fetchone()
            if anterior is None:
                raise ValueError('Não há orçamento ativo para substituir.')
            pagamentos = self.banco.con.execute(
                '''SELECT 1 FROM pagamentos pg JOIN parcelas pa
                   ON pa.empresa_id=pg.empresa_id AND pa.id=pg.parcela_id
                   WHERE pa.empresa_id=? AND pa.orcamento_id=? LIMIT 1''',
                (ctx.empresa_id,anterior['id'])).fetchone()
            if pagamentos:
                raise ValueError('Há pagamentos vinculados ao orçamento anterior; revise manualmente antes de substituir.')
            agora = _agora()
            self.banco.con.execute(
                '''INSERT INTO substituicoes_orcamento
                   (empresa_id,anterior_id,novo_id,motivo,usuario_id,instante)
                   VALUES (?,?,?,?,?,?)''',
                (ctx.empresa_id,anterior['id'],novo_id,motivo.strip(),ctx.usuario_id,agora))
            self.banco.con.execute(
                "UPDATE orcamentos SET status='aceito',aceito_por=?,aceito_em=? WHERE empresa_id=? AND id=?",
                (ctx.usuario_id,agora,ctx.empresa_id,novo_id))
            self._auditar(ctx,'orcamento',novo_id,'substituir',
                          {'anterior_id':anterior['id'],'motivo':motivo.strip()})
        return {'orcamento_id':novo_id,'anterior_id':anterior['id'],'status':'substituido'}

    def definir_parcelas(self, ctx, orcamento_id, parcelas):
        if not isinstance(parcelas,list) or not parcelas:
            raise ValueError('Informe uma lista de parcelas.')
        if any(not isinstance(item,dict) for item in parcelas):
            raise ValueError('Cada parcela deve ser um objeto.')
        with self.banco.transacao():
            orcamento = self._orcamento(ctx,orcamento_id)
            if orcamento['status']!='aceito':
                raise ValueError('Aceite o orçamento antes de definir parcelas.')
            substituido = self.banco.con.execute(
                'SELECT 1 FROM substituicoes_orcamento WHERE empresa_id=? AND anterior_id=?',
                (ctx.empresa_id,orcamento_id)).fetchone()
            if substituido:
                raise ValueError('Orçamento substituído; defina parcelas na revisão ativa.')
            existente = self.banco.con.execute(
                'SELECT 1 FROM parcelas WHERE empresa_id=? AND orcamento_id=? LIMIT 1',
                (ctx.empresa_id,orcamento_id)).fetchone()
            if existente:
                raise ValueError('Parcelas já definidas; alteração requer fluxo de revisão.')
            valores = []
            for item in parcelas:
                valor = item.get('valor_centavos')
                _inteiro_positivo(valor,'Valor da parcela')
                descricao = str(item.get('descricao') or '').strip()
                if not 1 <= len(descricao) <= 120:
                    raise ValueError('Descrição da parcela deve ter de 1 a 120 caracteres.')
                vencimento = _data(item.get('vencimento'),'Vencimento')
                lembrar = _data(item.get('lembrar_cobranca'),'Data de cobrança')
                valores.append((valor,descricao,vencimento,lembrar))
            if sum(item[0] for item in valores)!=orcamento['valor_centavos']:
                raise ValueError('Soma das parcelas deve ser igual ao orçamento aceito.')
            ids = []
            for sequencia,(valor,descricao,vencimento,lembrar) in enumerate(valores,1):
                cur = self.banco.con.execute(
                    '''INSERT INTO parcelas
                       (empresa_id,orcamento_id,sequencia,valor_previsto_centavos,
                        vencimento,lembrar_cobranca,descricao) VALUES (?,?,?,?,?,?,?)''',
                    (ctx.empresa_id,orcamento_id,sequencia,valor,vencimento,lembrar,descricao))
                ids.append(cur.lastrowid)
            self._auditar(ctx,'orcamento',orcamento_id,'definir_parcelas',
                          {'parcelas_ids':ids,'total_centavos':sum(item[0] for item in valores)})
        return {'orcamento_id':orcamento_id,'parcelas_ids':ids,'total_centavos':orcamento['valor_centavos']}

    def informar_pagamento(self, ctx, parcela_id, valor_centavos, data_pagamento,
                           chave_idempotencia, observacao=''):
        self._permitir(ctx)
        _inteiro_positivo(valor_centavos,'Valor do pagamento')
        data_pagamento = _data(data_pagamento,'Data do pagamento')
        if not data_pagamento:
            raise ValueError('Informe a data do pagamento.')
        if not isinstance(chave_idempotencia,str) or not 1 <= len(chave_idempotencia.strip()) <= 120:
            raise ValueError('Informe chave de idempotência de 1 a 120 caracteres.')
        chave_idempotencia = chave_idempotencia.strip()
        if not isinstance(observacao,str) or len(observacao)>500:
            raise ValueError('Observação deve ter até 500 caracteres.')
        if type(parcela_id) is not int or parcela_id<1:
            raise ValueError('ID da parcela inválido.')
        with self.banco.transacao():
            parcela = self.banco.con.execute(
                'SELECT id,orcamento_id FROM parcelas WHERE empresa_id=? AND id=?',
                (ctx.empresa_id,parcela_id)).fetchone()
            if parcela is None:
                raise ValueError('Parcela não encontrada nesta empresa.')
            substituido = self.banco.con.execute(
                'SELECT 1 FROM substituicoes_orcamento WHERE empresa_id=? AND anterior_id=?',
                (ctx.empresa_id,parcela['orcamento_id'])).fetchone()
            if substituido:
                raise ValueError('Parcela pertence a orçamento substituído.')
            anterior = self.banco.con.execute(
                'SELECT * FROM pagamentos WHERE empresa_id=? AND chave_idempotencia=?',
                (ctx.empresa_id,chave_idempotencia)).fetchone()
            if anterior:
                if (anterior['parcela_id'],anterior['valor_centavos'],anterior['data_pagamento']) != (
                        parcela_id,valor_centavos,data_pagamento):
                    raise ValueError('Chave de idempotência já usada com outros dados.')
                reversao = self.banco.con.execute(
                    'SELECT tipo FROM reversoes_pagamento WHERE empresa_id=? AND pagamento_id=?',
                    (ctx.empresa_id,anterior['id'])).fetchone()
                return {'pagamento_id':anterior['id'],
                        'status':reversao['tipo'] if reversao else anterior['status'],
                        'reutilizado':True}
            cur = self.banco.con.execute(
                '''INSERT INTO pagamentos
                   (empresa_id,parcela_id,valor_centavos,data_pagamento,status,
                    chave_idempotencia,observacao,criado_por,criado_em)
                   VALUES (?,?,?,?,'informado',?,?,?,?)''',
                (ctx.empresa_id,parcela_id,valor_centavos,data_pagamento,
                 chave_idempotencia,observacao,ctx.usuario_id,_agora()))
            self._auditar(ctx,'pagamento',cur.lastrowid,'informar',
                          {'parcela_id':parcela_id,'valor_centavos':valor_centavos})
        return {'pagamento_id':cur.lastrowid,'status':'informado','reutilizado':False}

    def confirmar_pagamento(self, ctx, pagamento_id):
        self._permitir(ctx)
        if type(pagamento_id) is not int or pagamento_id<1:
            raise ValueError('ID do pagamento inválido.')
        with self.banco.transacao():
            pagamento = self.banco.con.execute(
                '''SELECT pg.*,pa.valor_previsto_centavos FROM pagamentos pg
                   JOIN parcelas pa ON pa.empresa_id=pg.empresa_id AND pa.id=pg.parcela_id
                   WHERE pg.empresa_id=? AND pg.id=?''',
                (ctx.empresa_id,pagamento_id)).fetchone()
            if pagamento is None:
                raise ValueError('Pagamento não encontrado nesta empresa.')
            reversao = self.banco.con.execute(
                'SELECT tipo FROM reversoes_pagamento WHERE empresa_id=? AND pagamento_id=?',
                (ctx.empresa_id,pagamento_id)).fetchone()
            if reversao:
                raise ValueError('Pagamento já revertido; informe um novo lançamento com outra chave.')
            if pagamento['status']=='confirmado':
                return {'pagamento_id':pagamento_id,'status':'ja_confirmado'}
            confirmado = self.banco.con.execute(
                """SELECT COALESCE(SUM(pg.valor_centavos),0) FROM pagamentos pg
                   WHERE pg.empresa_id=? AND pg.parcela_id=? AND pg.status='confirmado'
                   AND NOT EXISTS (SELECT 1 FROM reversoes_pagamento r
                   WHERE r.empresa_id=pg.empresa_id AND r.pagamento_id=pg.id)""",
                (ctx.empresa_id,pagamento['parcela_id'])).fetchone()[0]
            if confirmado+pagamento['valor_centavos']>pagamento['valor_previsto_centavos']:
                raise ValueError('Pagamento excede o saldo da parcela.')
            agora = _agora()
            self.banco.con.execute(
                "UPDATE pagamentos SET status='confirmado',confirmado_por=?,confirmado_em=? WHERE id=?",
                (ctx.usuario_id,agora,pagamento_id))
            self._auditar(ctx,'pagamento',pagamento_id,'confirmar',
                          {'parcela_id':pagamento['parcela_id'],
                           'valor_centavos':pagamento['valor_centavos']})
        return {'pagamento_id':pagamento_id,'status':'confirmado'}

    def reverter_pagamento(self, ctx, pagamento_id, motivo):
        """Cancela um relato ou estorna um recebimento confirmado sem apagar o registro."""
        self._permitir(ctx)
        if type(pagamento_id) is not int or pagamento_id < 1:
            raise ValueError('ID do pagamento inválido.')
        if not isinstance(motivo,str) or not 5 <= len(motivo.strip()) <= 500:
            raise ValueError('Informe o motivo da reversão (5 a 500 caracteres).')
        with self.banco.transacao():
            pagamento = self.banco.con.execute(
                'SELECT status FROM pagamentos WHERE empresa_id=? AND id=?',
                (ctx.empresa_id,pagamento_id)).fetchone()
            if pagamento is None:
                raise ValueError('Pagamento não encontrado nesta empresa.')
            anterior = self.banco.con.execute(
                'SELECT tipo FROM reversoes_pagamento WHERE empresa_id=? AND pagamento_id=?',
                (ctx.empresa_id,pagamento_id)).fetchone()
            if anterior:
                return {'pagamento_id':pagamento_id,'status':'ja_revertido','tipo':anterior['tipo']}
            tipo = 'estorno' if pagamento['status']=='confirmado' else 'cancelamento'
            self.banco.con.execute(
                '''INSERT INTO reversoes_pagamento
                   (empresa_id,pagamento_id,tipo,motivo,usuario_id,instante)
                   VALUES (?,?,?,?,?,?)''',
                (ctx.empresa_id,pagamento_id,tipo,motivo.strip(),ctx.usuario_id,_agora()))
            self._auditar(ctx,'pagamento',pagamento_id,tipo,{'motivo':motivo.strip()})
        return {'pagamento_id':pagamento_id,'status':'revertido','tipo':tipo}

    def relatorio(self, ctx, projeto_id=None):
        """Leitura consistente e autorizada; ausência de contrato produz saldo None."""
        self._permitir(ctx)
        if projeto_id is not None and (type(projeto_id) is not int or projeto_id<1):
            raise ValueError('ID do projeto inválido.')
        if self.banco.con.in_transaction:
            raise ValueError('Relatório exige leitura fora de outra transação.')
        self.banco.con.execute('BEGIN')
        try:
            return self._relatorio_snapshot(ctx,projeto_id)
        finally:
            self.banco.con.execute('ROLLBACK')

    def _relatorio_snapshot(self, ctx, projeto_id):
        projetos = self.banco.con.execute(
            '''SELECT p.id,p.titulo,p.resumo,p.status,c.nome AS cliente,c.cnpj
               FROM projetos p LEFT JOIN clientes c ON c.empresa_id=p.empresa_id AND c.id=p.cliente_id
               WHERE p.empresa_id=? AND (? IS NULL OR p.id=?) ORDER BY p.id''',
            (ctx.empresa_id,projeto_id,projeto_id)).fetchall()
        saida = []
        for projeto in projetos:
            orcamento = self.banco.con.execute(
                """SELECT o.* FROM orcamentos o WHERE o.empresa_id=? AND o.projeto_id=?
                   AND o.status='aceito' AND NOT EXISTS
                   (SELECT 1 FROM substituicoes_orcamento s
                    WHERE s.empresa_id=o.empresa_id AND s.anterior_id=o.id)""",
                (ctx.empresa_id,projeto['id'])).fetchone()
            parcelas = []
            total_recebido = 0
            if orcamento:
                for parcela in self.banco.con.execute(
                        'SELECT * FROM parcelas WHERE empresa_id=? AND orcamento_id=? ORDER BY sequencia',
                        (ctx.empresa_id,orcamento['id'])):
                    pagamentos = [dict(linha) for linha in self.banco.con.execute(
                        '''SELECT pg.id,pg.valor_centavos,pg.data_pagamento,
                           COALESCE(r.tipo,pg.status) AS status FROM pagamentos pg
                           LEFT JOIN reversoes_pagamento r ON r.empresa_id=pg.empresa_id
                           AND r.pagamento_id=pg.id
                           WHERE pg.empresa_id=? AND pg.parcela_id=? ORDER BY pg.id''',
                        (ctx.empresa_id,parcela['id']))]
                    recebido = sum(p['valor_centavos'] for p in pagamentos if p['status']=='confirmado')
                    total_recebido += recebido
                    parcelas.append({'id':parcela['id'],'sequencia':parcela['sequencia'],
                                     'descricao':parcela['descricao'],
                                     'valor_previsto_centavos':parcela['valor_previsto_centavos'],
                                     'vencimento':parcela['vencimento'],
                                     'lembrar_cobranca':parcela['lembrar_cobranca'],
                                     'recebido_confirmado_centavos':recebido,
                                     'saldo_centavos':parcela['valor_previsto_centavos']-recebido,
                                     'pagamentos':pagamentos})
            saida.append({'projeto_id':projeto['id'],'projeto':projeto['titulo'],
                          'cliente':projeto['cliente'],'cnpj':projeto['cnpj'],
                          'orcamento_aceito_id':orcamento['id'] if orcamento else None,
                          'valor_aceito_centavos':orcamento['valor_centavos'] if orcamento else None,
                          'percentual_entrada_acordado':orcamento['percentual_entrada_acordado'] if orcamento else None,
                          'recebido_confirmado_centavos':total_recebido if orcamento else None,
                          'saldo_centavos':orcamento['valor_centavos']-total_recebido if orcamento else None,
                          'parcelas':parcelas})
        return {'data_base_utc':_agora(),'projetos':saida,
                'limite':'Somente orçamento aceito e pagamentos confirmados entram no saldo; anotações do chat não entram.'}
