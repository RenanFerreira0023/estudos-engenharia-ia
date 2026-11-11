"""Rota leve e auditável para orientar o agente; não autoriza ações nem substitui ferramentas."""
import re
import unicodedata

from langchain_core.runnables import RunnableLambda


def _normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD', texto.lower())
                   if not unicodedata.combining(c))


def identificar_rota(dados):
    """A pergunta atual prevalece; seguimentos curtos herdam a rota recente."""
    pergunta = _normalizar(dados['pergunta'])
    anteriores = dados.get('anteriores', [])
    if re.search(r'\b(quantas?|qtd|numero de)\s+(?:\w+\s+){0,2}(?:mensagens?|msgs?|msngs?)\b|\b(conte|liste|mostre)\s+(?:as\s+)?mensagens\b|\bmensagens de\b', pergunta):
        rota = 'consulta'
    elif re.search(r'\b(onde foi dito|em qual mensagem|qual mensagem|quem falou|onde esta escrito)\b', pergunta):
        rota = 'fonte'
    elif re.search(r'\b(visita|visitar|agendar|agenda|horario|remarcar|disponibilidade)\b', pergunta):
        rota = 'visita'
    elif re.search(r'\b(projeto|projetos|saldo|orcamento|orcamentos)\b', pergunta):
        rota = 'projeto'
    elif re.search(r'\b(cliente|cleinte|cnpj|cadastrar|cadastro|empresa)\b', pergunta):
        rota = 'cliente'
    elif (anteriores and len(pergunta.split()) <= 8 and
          re.search(r'\b(dele|dela|desse|dessa|aquele|aquela|isso|tambem|mesmo)\b'
                    r'|^\s*(as|amanha|hoje|e)\b', pergunta)):
        ultima = _normalizar(anteriores[-1]['pergunta'])
        rota = identificar_rota({'pergunta': ultima})['rota']
    else:
        rota = 'geral'
    return {'rota': rota, 'criterio': 'palavras_da_pergunta_ou_contexto_curto'}


# ROUTER: RunnableLambda expõe uma etapa de roteamento compatível com invoke.
# A decisão é uma dica ao agente; validações e autorização continuam nos serviços.
roteador_pedido = RunnableLambda(identificar_rota)
