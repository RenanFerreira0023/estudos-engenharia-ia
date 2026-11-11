"""Regras locais de agendamento; o modelo nunca grava diretamente no SQLite."""
from datetime import datetime, timedelta, timezone
import json
import re
from urllib.request import Request, urlopen
from urllib.error import URLError
from zoneinfo import ZoneInfo


FUSO = ZoneInfo('America/Sao_Paulo')


def agora_utc():
    return datetime.now(timezone.utc)


def _instante(valor):
    if isinstance(valor, str):
        valor = datetime.fromisoformat(valor)
    if not isinstance(valor, datetime) or valor.tzinfo is None or valor.utcoffset() is None:
        raise ValueError('Informe data e hora com fuso explícito.')
    return valor.astimezone(timezone.utc)


def consultar_cep(cep, transporte=None):
    """ViaCEP real por padrão; transporte injetável só em testes identificados."""
    digitos = re.sub(r'\D', '', cep or '')
    if len(digitos) != 8:
        raise ValueError('CEP deve ter oito dígitos.')
    url = f'https://viacep.com.br/ws/{digitos}/json/'
    try:
        if transporte is None:
            with urlopen(Request(url, headers={'User-Agent': 'SecretariaIA-Academica/1.0'}), timeout=5) as resposta:
                dados = json.load(resposta)
        else:
            dados = transporte(url)
    except (OSError, URLError, TimeoutError, ValueError) as erro:
        raise ValueError('ViaCEP indisponível; informe o endereço manualmente.') from erro
    if not isinstance(dados, dict) or dados.get('erro'):
        raise ValueError('CEP não localizado pelo ViaCEP.')
    campos = {chave: str(dados.get(chave) or '').strip() for chave in ('cep','logradouro','bairro','localidade','uf')}
    if not campos['localidade'] or not campos['uf']:
        raise ValueError('ViaCEP retornou endereço incompleto; confirme manualmente.')
    return {'origem':'viacep_real' if transporte is None else 'fixture_local', **campos}


def consultar_cnpj(cnpj, transporte=None):
    """Minha Receita: devolve apenas campos necessários à proposta de cadastro."""
    digitos = re.sub(r'\D', '', cnpj or '')
    if len(digitos) != 14:
        raise ValueError('CNPJ deve ter 14 dígitos.')
    url = f'https://minhareceita.org/{digitos}'
    try:
        if transporte is None:
            with urlopen(Request(url, headers={'User-Agent':'SecretariaIA-Academica/1.0'}), timeout=6) as resposta:
                dados = json.load(resposta)
        else:
            dados = transporte(url)
    except (OSError, URLError, TimeoutError, ValueError) as erro:
        raise ValueError('Minha Receita indisponível; confirme os dados manualmente.') from erro
    if not isinstance(dados, dict) or re.sub(r'\D','',str(dados.get('cnpj') or '')) != digitos:
        raise ValueError('Retorno da Minha Receita não corresponde ao CNPJ consultado.')
    razao = str(dados.get('razao_social') or '').strip()
    if not razao:
        raise ValueError('Minha Receita não informou razão social.')
    return {'origem':'minha_receita_real' if transporte is None else 'fixture_local',
            'cnpj':digitos,'razao_social':razao,
            'nome_fantasia':str(dados.get('nome_fantasia') or '').strip(),
            'municipio':str(dados.get('municipio') or '').strip(),
            'uf':str(dados.get('uf') or '').strip(),
            'consultado_em':agora_utc().isoformat()}


class Agenda:
    def __init__(self, banco):
        self.banco = banco

    def _usuario(self, ctx, usuario_id):
        self.banco._usuario(ctx)
        row = self.banco.con.execute('SELECT id FROM usuarios WHERE empresa_id=? AND id=?',
                                     (ctx.empresa_id, usuario_id)).fetchone()
        if row is None:
            raise ValueError('Atendente não localizado nesta empresa.')

    def resolver_atendente(self, ctx, identificacao):
        """Aceita ID ou nome completo, sem diferenciar maiúsculas; rejeita ambiguidade."""
        self.banco._usuario(ctx)
        identificacao = (identificacao or '').strip()
        if not identificacao:
            raise ValueError('Informe o atendente.')
        encontrados = self.banco.con.execute('''SELECT id FROM usuarios
            WHERE empresa_id=? AND (id=? COLLATE NOCASE OR nome=? COLLATE NOCASE)''',
            (ctx.empresa_id,identificacao,identificacao)).fetchall()
        if len(encontrados) != 1:
            raise ValueError('Atendente não localizado ou nome ambíguo; informe o ID.')
        return encontrados[0]['id']

    def cadastrar_cliente(self, ctx, nome, tipo='PF', cnpj=None, cadastro_api=None):
        self.banco._usuario(ctx)
        nome = (nome or '').strip()
        if not 2 <= len(nome) <= 120 or tipo not in ('PF','PJ'):
            raise ValueError('Informe nome e tipo PF/PJ válidos.')
        if cnpj is not None:
            cnpj = re.sub(r'\D', '', cnpj)
            if len(cnpj) != 14 or tipo != 'PJ':
                raise ValueError('CNPJ deve ter 14 dígitos e cliente PJ.')
        origem='informado_manualmente'
        nome_fantasia=None
        consultado_em=None
        if cadastro_api is not None:
            if tipo!='PJ' or cadastro_api.get('cnpj')!=cnpj or cadastro_api.get('razao_social')!=nome:
                raise ValueError('Dados da consulta PJ não correspondem ao cadastro.')
            origem=cadastro_api.get('origem') or 'informado_manualmente'
            if origem not in ('minha_receita_real','fixture_local'):
                raise ValueError('Origem da consulta PJ inválida.')
            nome_fantasia=cadastro_api.get('nome_fantasia') or None
            consultado_em=cadastro_api.get('consultado_em')
        with self.banco.transacao():
            if cnpj:
                existente = self.banco.con.execute('SELECT id FROM clientes WHERE empresa_id=? AND cnpj=?',
                                                   (ctx.empresa_id, cnpj)).fetchone()
                if existente:
                    return existente['id']
            cur = self.banco.con.execute('''INSERT INTO clientes
                (empresa_id,nome,tipo_pessoa,cnpj,criado_por,criado_em,nome_fantasia,origem_cadastro,consultado_cnpj_em)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (ctx.empresa_id,nome,tipo,cnpj,ctx.usuario_id,agora_utc().isoformat(),
                 nome_fantasia,origem,consultado_em))
            return cur.lastrowid

    def buscar_cliente(self, ctx, termo):
        self.banco._usuario(ctx)
        termo = (termo or '').strip()
        if not termo or len(termo) > 120:
            raise ValueError('Informe nome ou CNPJ do cliente.')
        cnpj = re.sub(r'\D', '', termo)
        return [dict(r) for r in self.banco.con.execute('SELECT id,nome,tipo_pessoa,cnpj,nome_fantasia,origem_cadastro,consultado_cnpj_em FROM clientes WHERE empresa_id=? AND (nome LIKE ? OR cnpj=?) ORDER BY nome LIMIT 20',
            (ctx.empresa_id, '%' + termo.replace('%','\\%').replace('_','\\_') + '%', cnpj))]

    def _conflita(self, empresa_id, atendente_id, inicio, fim):
        return self.banco.con.execute('''SELECT 1 FROM agendamentos WHERE empresa_id=? AND atendente_id=?
            AND status='confirmado' AND inicio_em<? AND fim_em>? LIMIT 1''',
            (empresa_id,atendente_id,fim.isoformat(),inicio.isoformat())).fetchone() is not None

    def consultar_disponibilidade(self, ctx, atendente_id, inicio, fim):
        atendente_id = self.resolver_atendente(ctx, atendente_id)
        self._usuario(ctx, atendente_id)
        inicio, fim = _instante(inicio), _instante(fim)
        if fim <= inicio:
            raise ValueError('Fim deve ser posterior ao início.')
        return {'sem_conflito_registrado': not self._conflita(ctx.empresa_id,atendente_id,inicio,fim),
                'limite':'Consulta apenas compromissos registrados; não garante disponibilidade fora do sistema.'}

    def propor_visita(self, ctx, cliente_id, inicio, fim, endereco, atendente_id=None, agora=None):
        atendente_id = self.resolver_atendente(ctx,atendente_id or ctx.usuario_id)
        self._usuario(ctx, atendente_id)
        cliente = self.banco.con.execute('SELECT id,nome FROM clientes WHERE empresa_id=? AND id=?',
                                        (ctx.empresa_id,cliente_id)).fetchone()
        if cliente is None:
            raise ValueError('Cliente não localizado nesta empresa.')
        inicio, fim = _instante(inicio), _instante(fim)
        if fim <= inicio or fim - inicio > timedelta(hours=12):
            raise ValueError('Intervalo inválido ou maior que 12 horas.')
        if not isinstance(endereco, dict) or not all(str(endereco.get(k) or '').strip() for k in ('logradouro','numero','cidade','uf')):
            raise ValueError('Confirme logradouro, número, cidade e UF antes da visita.')
        if atendente_id != ctx.usuario_id and self.banco._usuario(ctx)['perfil'] != 'administrador':
            raise PermissionError('Somente administrador pode agendar para outro atendente nesta demonstração.')
        agora = _instante(agora) if agora else agora_utc()
        if inicio <= agora:
            raise ValueError('Agendamento deve ser futuro.')
        with self.banco.transacao():
            if self._conflita(ctx.empresa_id,atendente_id,inicio,fim):
                raise ValueError('Atendente tem compromisso registrado nesse intervalo.')
            cur = self.banco.con.execute('''INSERT INTO propostas_visita
                (empresa_id,solicitante_id,cliente_id,atendente_id,inicio_em,fim_em,endereco_json,estado,criada_em,expira_em)
                VALUES (?,?,?,?,?,?,?,'pendente',?,?)''',
                (ctx.empresa_id,ctx.usuario_id,cliente_id,atendente_id,inicio.isoformat(),fim.isoformat(),
                 json.dumps(endereco,ensure_ascii=False),agora.isoformat(),(agora+timedelta(minutes=30)).isoformat()))
        return {'proposta_id':cur.lastrowid,'cliente':cliente['nome'],'atendente':atendente_id,
                'inicio':inicio.astimezone(FUSO).isoformat(),'fim':fim.astimezone(FUSO).isoformat(),
                'endereco':endereco,'estado':'pendente','aviso':'Ainda não há reserva. Confirme a proposta pelo ID.'}

    def confirmar_visita(self, ctx, proposta_id, agora=None):
        self.banco._usuario(ctx)
        agora = _instante(agora) if agora else agora_utc()
        # TRANSAÇÃO: relê proposta e conflito sob BEGIN IMMEDIATE; confirmação repetida devolve o mesmo registro.
        with self.banco.transacao():
            p = self.banco.con.execute('SELECT * FROM propostas_visita WHERE empresa_id=? AND id=?',
                                       (ctx.empresa_id,proposta_id)).fetchone()
            if p is None or p['solicitante_id'] != ctx.usuario_id:
                raise PermissionError('Proposta não pertence ao usuário atual.')
            anterior = self.banco.con.execute('SELECT id FROM agendamentos WHERE empresa_id=? AND proposta_id=?',
                                               (ctx.empresa_id,proposta_id)).fetchone()
            if anterior:
                return {'agendamento_id':anterior['id'],'estado':'já_confirmada'}
            if p['estado'] != 'pendente' or _instante(p['expira_em']) < agora:
                raise ValueError('Proposta expirada ou não confirmável; crie outra.')
            inicio, fim = _instante(p['inicio_em']), _instante(p['fim_em'])
            if self._conflita(ctx.empresa_id,p['atendente_id'],inicio,fim):
                self.banco.con.execute("UPDATE propostas_visita SET estado='conflito' WHERE id=?",(proposta_id,))
                return {'estado':'conflito','aviso':'Surgiu compromisso no intervalo; crie nova proposta.'}
            cur = self.banco.con.execute('''INSERT INTO agendamentos
                (empresa_id,proposta_id,cliente_id,atendente_id,solicitante_id,inicio_em,fim_em,endereco_snapshot_json,status,versao,criado_em)
                VALUES (?,?,?,?,?,?,?,?,'confirmado',1,?)''',
                (ctx.empresa_id,proposta_id,p['cliente_id'],p['atendente_id'],p['solicitante_id'],
                 p['inicio_em'],p['fim_em'],p['endereco_json'],agora.isoformat()))
            self.banco.con.execute("UPDATE propostas_visita SET estado='confirmada',confirmada_em=? WHERE id=?",
                                   (agora.isoformat(),proposta_id))
            depois = {'id':cur.lastrowid,'proposta_id':proposta_id,'cliente_id':p['cliente_id'],
                      'atendente_id':p['atendente_id'],'inicio_em':p['inicio_em'],'fim_em':p['fim_em']}
            self.banco.con.execute('''INSERT INTO auditoria_agenda
                (empresa_id,ator_id,entidade,entidade_id,operacao,antes_json,depois_json,instante)
                VALUES (?,?, 'agendamento',?,'confirmar',NULL,?,?)''',
                (ctx.empresa_id,ctx.usuario_id,cur.lastrowid,json.dumps(depois),agora.isoformat()))
            return {'agendamento_id':cur.lastrowid,'estado':'confirmada'}

    def listar_agenda(self, ctx):
        self.banco._usuario(ctx)
        return [dict(r) for r in self.banco.con.execute('''SELECT a.id,c.nome AS cliente,a.inicio_em,a.fim_em,a.status
            FROM agendamentos a JOIN clientes c ON c.id=a.cliente_id AND c.empresa_id=a.empresa_id
            WHERE a.empresa_id=? AND a.atendente_id=? ORDER BY a.inicio_em''',(ctx.empresa_id,ctx.usuario_id))]
