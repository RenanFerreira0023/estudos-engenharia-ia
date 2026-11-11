"""Pergunta -> plano tipado -> SELECT fixo e parametrizado sobre mensagens autorizadas."""
from datetime import date, datetime, time, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PlanoConsultaMensagens(BaseModel):
    model_config = ConfigDict(extra='forbid')

    tipo: Literal['contagem','lista','nao_suportada']
    autor: str | None = None
    termos: list[str] = Field(default_factory=list, max_length=4)
    data_inicio_local: date | None = None
    data_fim_local_exclusiva: date | None = None
    ordem: Literal['cronologica','recente'] = 'recente'
    limite: int = Field(default=20, ge=1, le=50)
    motivo: str | None = None

    @field_validator('autor')
    @classmethod
    def validar_autor(cls, valor):
        if valor is None:
            return None
        valor = valor.strip()
        if not 1 <= len(valor) <= 80:
            raise ValueError('Autor deve ter de 1 a 80 caracteres.')
        return valor

    @field_validator('termos')
    @classmethod
    def validar_termos(cls, valores):
        termos = [valor.strip() for valor in valores]
        if any(not 1 <= len(valor) <= 80 for valor in termos):
            raise ValueError('Cada termo deve ter de 1 a 80 caracteres.')
        return termos

    @model_validator(mode='after')
    def validar_periodo(self):
        if (self.data_inicio_local and self.data_fim_local_exclusiva and
                self.data_inicio_local >= self.data_fim_local_exclusiva):
            raise ValueError('Fim do período deve ser posterior ao início.')
        return self


INSTRUCOES_PLANO = '''Converta a pergunta em um plano de leitura de mensagens importadas.
Use tipo=contagem para "quantas mensagens" e tipo=lista para "mostre/liste mensagens".
Extraia autor quando mencionado e até quatro palavras/frases que devem aparecer no texto.
Todos os termos serão combinados por E (AND), sem sinônimos automáticos.
Datas são do fuso local do corpus: para um dia, use início nesse dia e fim exclusivo no dia seguinte;
para um mês, use o primeiro dia do mês e o primeiro dia do mês seguinte.
Não invente ano ausente nem transforme "pagamento informado" em pago.
Se o pedido exigir saldo, parcelas, pagamentos confirmados, escrita ou outra tabela,
use tipo=nao_suportada e explique o motivo. Não produza SQL.
Exemplo: "Quantas mensagens de Bruno mencionam orçamento e Alfa?"
-> tipo=contagem, autor=Bruno, termos=["orçamento","Alfa"].'''


def planejar_consulta(pergunta, modelo):
    if not isinstance(pergunta,str) or not pergunta.strip():
        raise ValueError('Informe a pergunta.')
    resposta = modelo.with_structured_output(PlanoConsultaMensagens,method='json_schema').invoke([
        ('system',INSTRUCOES_PLANO),('human',pergunta)])
    return PlanoConsultaMensagens.model_validate(resposta)


def _escapar_like(texto):
    return texto.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')


def executar_plano(banco, ctx, corpus_id, plano):
    """Nunca executa SQL do modelo; compila somente colunas e operadores permitidos."""
    plano = PlanoConsultaMensagens.model_validate(plano)
    corpus = banco._corpus(ctx,corpus_id)
    if plano.tipo == 'nao_suportada':
        return {'status':'nao_suportada','plano':plano.model_dump(mode='json'),
                'motivo':plano.motivo or 'Consulta fora do escopo de mensagens.'}
    filtros = ['empresa_id=?','corpus_id=?']
    parametros = [ctx.empresa_id,corpus_id]
    if plano.autor:
        filtros.append('LOWER(autor)=LOWER(?)')
        parametros.append(plano.autor)
    for termo in plano.termos:
        filtros.append("LOWER(texto) LIKE LOWER(?) ESCAPE '\\'")
        parametros.append('%' + _escapar_like(termo) + '%')
    fuso = ZoneInfo(corpus['fuso'])
    for campo,operador,data in (
        ('inicio','>=',plano.data_inicio_local),
        ('fim','<',plano.data_fim_local_exclusiva),
    ):
        if data:
            instante = datetime.combine(data,time.min,fuso).astimezone(timezone.utc)
            filtros.append(f'instante_utc {operador} ?')
            parametros.append(instante.isoformat())
    onde = ' AND '.join(filtros)
    if plano.tipo == 'contagem':
        sql = f'SELECT COUNT(*) FROM mensagens_importadas WHERE {onde}'
        total = banco.con.execute(sql,parametros).fetchone()[0]
        return {'status':'ok','plano':plano.model_dump(mode='json'),
                'sql_executado':sql,'parametros_sql':parametros,'total':total,
                'limite':'Contagem exaustiva das mensagens que atendem aos filtros; não é saldo financeiro.'}
    ordem = ('instante_utc ASC,id ASC' if plano.ordem == 'cronologica'
             else 'instante_utc DESC,id DESC')
    sql = ('SELECT id,data_original,instante_utc,autor,texto FROM mensagens_importadas '
           f'WHERE {onde} ORDER BY {ordem} LIMIT ?')
    parametros.append(plano.limite)
    linhas = [dict(linha) for linha in banco.con.execute(sql,parametros)]
    return {'status':'ok','plano':plano.model_dump(mode='json'),
            'sql_executado':sql,'parametros_sql':parametros,'mensagens':linhas,
            'limite':'Lista limitada; não use para afirmar total de registros ou somar valores.'}
