"""Contratos de interpretação: propostas revisáveis, sem registros operacionais."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

class Contrato(BaseModel):
    model_config=ConfigDict(extra='forbid')

class Fonte(Contrato):
    mensagem_id: Annotated[StrictInt,Field(gt=0)]
    trecho: str=Field(min_length=1,max_length=2500)

class Financeiro(Contrato):
    tipo: Literal['orcamento_proposto','orcamento_aceito','condicao_prevista','pagamento_informado','saldo_indefinido']
    valor_centavos: Annotated[StrictInt,Field(ge=0)] | None
    percentual: str | None
    data_referencia: date | None

    @field_validator('percentual')
    @classmethod
    def percentual_valido(cls,v):
        if v is None:return v
        try:
            n=Decimal(v)
            if not n.is_finite() or not 0<=n<=100:raise ValueError()
        except (InvalidOperation,ValueError):
            raise ValueError('Percentual deve ser decimal entre 0 e 100.') from None
        return v

class Agenda(Contrato):
    tipo: Literal['visita','reuniao','atendimento','indefinido']
    inicio_em: datetime | None
    fim_em: datetime | None
    atendente_nome: str | None
    local: str | None

    @model_validator(mode='after')
    def validar_intervalo(self):
        for instante in (self.inicio_em,self.fim_em):
            if instante is not None and instante.utcoffset() is None:
                raise ValueError('Data/hora precisa indicar fuso.')
        if self.fim_em is not None and self.inicio_em is None:
            raise ValueError('Fim sem início não identifica intervalo.')
        if self.inicio_em is not None and self.fim_em is not None and self.fim_em<=self.inicio_em:
            raise ValueError('Fim precisa ser posterior ao início.')
        return self

class Proposta(Contrato):
    area: Literal['projeto','financeiro','agenda']
    projeto: str | None=Field(max_length=120)
    natureza: Literal['relato','previsto','pergunta','sugestao','confirmacao','correcao','cancelamento','pendencia']
    resumo: str=Field(min_length=1,max_length=1500)
    financeiro: Financeiro | None
    agenda: Agenda | None
    fontes: list[Fonte]=Field(min_length=1,max_length=8)
    pendencias: list[str]=Field(max_length=12)

    @model_validator(mode='after')
    def conferir_area(self):
        if self.area=='financeiro' and (self.financeiro is None or self.agenda is not None):
            raise ValueError('Área financeira precisa de contrato financeiro, sem agenda.')
        if self.area=='agenda' and (self.agenda is None or self.financeiro is not None):
            raise ValueError('Área agenda precisa de contrato de agenda, sem financeiro.')
        if self.area=='projeto' and (self.agenda is not None or self.financeiro is not None):
            raise ValueError('Projeto não pode esconder contrato de outra área.')
        return self

class PropostaProjeto(Proposta):
    area: Literal['projeto']
    financeiro: None
    agenda: None

class PropostaFinanceira(Proposta):
    area: Literal['financeiro']
    financeiro: Financeiro
    agenda: None

class PropostaAgenda(Proposta):
    area: Literal['agenda']
    financeiro: None
    agenda: Agenda

class SaidaExtracao(Contrato):
    propostas: list[PropostaProjeto | PropostaFinanceira | PropostaAgenda]=Field(max_length=30)
    observacoes: list[str]=Field(max_length=12)
