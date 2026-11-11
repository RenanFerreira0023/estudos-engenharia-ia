"""Fila de interpretações revisáveis: persistência, autoria e histórico; sem registros operacionais."""
from datetime import datetime,timezone
from hashlib import sha256
import json
from .propostas import Proposta
from .extracao import validar_fontes

# MIGRAÇÃO: acrescenta somente fila/histórico. Não altera mensagens originais nem cria agenda/financeiro.

PERMISSOES={'administrador':{'projeto','financeiro','agenda'},
            'financeiro':{'financeiro'},'atendente':{'projeto','agenda'}}

def _json(dados):
    return json.dumps(dados,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def _agora():
    return datetime.now(timezone.utc).isoformat()

class FilaRevisao:
    def __init__(self,banco):
        self.banco=banco

    def _permitir_area(self,ctx,area):
        perfil=self.banco._usuario(ctx)['perfil']
        if area not in PERMISSOES[perfil]:
            raise PermissionError('Perfil sem permissão para revisar esta área.')

    def _registro(self,ctx,id):
        # IDENTIDADE: vem do contexto do serviço. Nem administrador confirma fila pessoal de outro usuário.
        self.banco._usuario(ctx)
        r=self.banco.con.execute(
            'SELECT * FROM propostas_revisao WHERE id=? AND empresa_id=? AND usuario_id=?',
            (id,ctx.empresa_id,ctx.usuario_id)).fetchone()
        if r is None:
            raise PermissionError('Proposta não acessível neste contexto.')
        self.banco._corpus(ctx,r['corpus_id'])
        self._permitir_area(ctx,r['area'])
        return r

    def _validar(self,ctx,corpus,dados):
        self.banco._corpus(ctx,corpus)
        proposta=Proposta.model_validate(dados)
        self._permitir_area(ctx,proposta.area)
        fontes=[]
        for fonte in proposta.fontes:
            m=self.banco.con.execute(
                'SELECT * FROM mensagens_importadas WHERE id=? AND empresa_id=? AND corpus_id=?',
                (fonte.mensagem_id,ctx.empresa_id,corpus)).fetchone()
            if m is None:
                raise ValueError('Fonte não pertence ao corpus da proposta.')
            fontes.append(dict(m))
        # FONTES: revalida na entrada da fila e na correção, sem aceitar fontes de outro corpus.
        # Foco já foi validado na extração; aqui a fronteira é o corpus autorizado.
        validar_fontes({'propostas':[proposta.model_dump(mode='json')],'observacoes':[]},
                       {'mensagens_foco':fontes,'contexto_vizinho':[]})
        return proposta.model_dump(mode='json')

    def _historico(self,ctx,id,acao,versao,antes,depois,comentario):
        self.banco.con.execute(
            """INSERT INTO historico_revisao(proposta_id,ator_usuario_id,acao,versao_anterior,versao_nova,
               antes_json,depois_json,comentario,instante) VALUES (?,?,?,?,?,?,?,?,?)""",
            (id,ctx.usuario_id,acao,versao,versao+1,
             _json(antes) if antes is not None else None,_json(depois),comentario,_agora()))

    def registrar_resultado(self,ctx,resultado):
        if resultado.get('empresa_id')!=ctx.empresa_id or resultado.get('usuario_id')!=ctx.usuario_id:
            raise PermissionError('Análise não pertence ao contexto atual.')
        if resultado.get('origem') not in ('fixture_manual','api_real'):
            raise ValueError('Origem de análise não suportada.')
        corpus=resultado['corpus_id'];ids=[];novas=0;restritas=0
        # TRANSAÇÃO/IDEMPOTÊNCIA: mesmo conteúdo não reaparece pendente após uma decisão manual.
        with self.banco.transacao():
            self.banco._corpus(ctx,corpus)
            for item in resultado['propostas']:
                if item.get('status')!='aguardando_revisao':
                    raise ValueError('Somente propostas com fontes validadas podem entrar na fila.')
                perfil=self.banco._usuario(ctx)['perfil']
                if item['area'] not in PERMISSOES[perfil]:
                    restritas+=1
                    continue
                dados={k:item[k] for k in Proposta.model_fields}
                dados=self._validar(ctx,corpus,dados)
                chave=sha256(_json(dados).encode()).hexdigest()
                atual=self.banco.con.execute(
                    'SELECT id FROM propostas_revisao WHERE empresa_id=? AND usuario_id=? AND corpus_id=? AND chave=?',
                    (ctx.empresa_id,ctx.usuario_id,corpus,chave)).fetchone()
                if atual:
                    ids.append(atual['id'])
                    continue
                agora=_agora()
                cursor=self.banco.con.execute(
                    """INSERT INTO propostas_revisao(empresa_id,usuario_id,corpus_id,chave,area,estado,versao,
                       original_json,atual_json,origem,criado_em,atualizado_em) VALUES (?,?,?,?,?,'pendente',1,?,?,?,?,?)""",
                    (ctx.empresa_id,ctx.usuario_id,corpus,chave,dados['area'],_json(dados),_json(dados),
                     resultado['origem'],agora,agora))
                id=cursor.lastrowid;ids.append(id);novas+=1
                self._historico(ctx,id,'registrar',0,None,dados,'Interpretação ainda não revisada.')
        return {'ids':ids,'novas':novas,'restritas_por_perfil':restritas}

    def listar(self,ctx):
        perfil=self.banco._usuario(ctx)['perfil']
        areas=PERMISSOES[perfil]
        linhas=self.banco.con.execute(
            'SELECT id,area FROM propostas_revisao WHERE empresa_id=? AND usuario_id=? ORDER BY id',
            (ctx.empresa_id,ctx.usuario_id)).fetchall()
        resultado=[]
        for linha in linhas:
            if linha['area'] not in areas:
                continue
            r=self._registro(ctx,linha['id'])
            if r['area'] in areas:
                resultado.append(self._publico(r))
        return resultado

    def _publico(self,r):
        return {'id':r['id'],'corpus_id':r['corpus_id'],'estado':r['estado'],'versao':r['versao'],
                'origem':r['origem'],'dados':json.loads(r['atual_json'])}

    def obter(self,ctx,id):
        return self._publico(self._registro(ctx,id))

    def historico(self,ctx,id):
        self._registro(ctx,id)
        return [dict(r) for r in self.banco.con.execute(
            'SELECT * FROM historico_revisao WHERE proposta_id=? ORDER BY id',(id,))]

    def corrigir(self,ctx,id,versao,mudancas,comentario):
        if not isinstance(mudancas,dict) or not mudancas or set(mudancas)-{'projeto','natureza','resumo','financeiro','agenda','pendencias'}:
            raise ValueError('Correção só permite campos de interpretação; fontes, área e autoria são imutáveis.')
        comentario=self._comentario(comentario)
        with self.banco.transacao():
            r=self._registro(ctx,id)
            self._pendente(r,versao)
            antes=json.loads(r['atual_json']);novo={**antes,**mudancas}
            novo=self._validar(ctx,r['corpus_id'],novo)
            if novo==antes:
                return self._publico(r)
            self.banco.con.execute(
                'UPDATE propostas_revisao SET atual_json=?,versao=versao+1,atualizado_em=? WHERE id=?',
                (_json(novo),_agora(),id))
            self._historico(ctx,id,'corrigir',versao,antes,novo,comentario)
        return self.obter(ctx,id)

    def decidir(self,ctx,id,versao,decisao,comentario):
        if decisao not in ('aceitar','rejeitar'):
            raise ValueError('Escolha aceitar ou rejeitar.')
        comentario=self._comentario(comentario)
        estado='aceita' if decisao=='aceitar' else 'rejeitada'
        with self.banco.transacao():
            r=self._registro(ctx,id)
            if r['estado']==estado:
                return self._publico(r)
            self._pendente(r,versao)
            dados=json.loads(r['atual_json'])
            self._validar(ctx,r['corpus_id'],dados)
            self.banco.con.execute(
                'UPDATE propostas_revisao SET estado=?,versao=versao+1,atualizado_em=? WHERE id=?',
                (estado,_agora(),id))
            self._historico(ctx,id,decisao,versao,
                            {'estado':r['estado'],'dados':dados},{'estado':estado,'dados':dados},comentario)
        return self.obter(ctx,id)

    @staticmethod
    def _pendente(r,versao):
        if r['estado']!='pendente':
            raise ValueError('Decisão já concluída; este incremento não reabre a proposta.')
        if type(versao) is not int or versao!=r['versao']:
            raise ValueError('Versão mudou. Leia a proposta atual antes de decidir.')

    @staticmethod
    def _comentario(comentario):
        if not isinstance(comentario,str) or not 1<=len(comentario.strip())<=1000:
            raise ValueError('Informe comentário de 1 a 1000 caracteres.')
        return comentario.strip()
