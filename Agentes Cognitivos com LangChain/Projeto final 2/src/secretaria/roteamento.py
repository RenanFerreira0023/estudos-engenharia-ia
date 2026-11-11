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
    if re.search(r'\b(visita|visitar|agendar|agenda|horario|remarcar|disponibilidade)\b', pergunta):
        rota = 'visita'
    elif re.search(r'\b(cliente|cnpj|cadastrar|cadastro|empresa)\b', pergunta):
        rota = 'cliente'
    elif anteriores and len(pergunta.split()) <= 8:
        ultima = _normalizar(anteriores[-1]['pergunta'])
        rota = identificar_rota({'pergunta': ultima})['rota']
    else:
        rota = 'geral'
    return {'rota': rota, 'criterio': 'palavras_da_pergunta_ou_contexto_curto'}


# ROUTER: RunnableLambda expõe uma etapa de roteamento compatível com invoke.
# A decisão é uma dica ao agente; validações e autorização continuam nos serviços.
roteador_pedido = RunnableLambda(identificar_rota)
