"""Demonstração reprodutível do contrato: fixtures não são execuções reais do atendente."""
from .casos_verificacao import montar_casos
from .verificacao import VerificadorResposta, checar_valores, coletar_evidencias, criar_juiz, criar_reparador


def demonstrar(modelo=None):
    verificador = None if modelo is None else VerificadorResposta(criar_juiz(modelo), criar_reparador(modelo),
        origem=type(modelo).__name__ + ':' + str(getattr(modelo, 'model_name', 'modelo injetado')))
    resultados = []
    for caso in montar_casos():
        r = caso['resultado']
        avaliacao = verificador.avaliar(r, r['resposta']) if verificador else None
        conferiu = None
        if avaliacao:
            parecer = avaliacao.get('parecer', {})
            conferiu = (avaliacao['aprovada'] == caso['esperado_aprovada']
                and (caso['classe_esperada'] is None or any(a['classe'] == caso['classe_esperada'] for a in parecer.get('afirmacoes', [])))
                and (caso['responde_esperado'] is None or parecer.get('responde_pedido') == caso['responde_esperado']))
        resultados.append({**caso, 'regras_locais': checar_valores(r['resposta'], coletar_evidencias(r)),
                           'avaliacao_juiz': avaliacao, 'conferiu_gabarito': conferiu})
    return {'origem': 'fixtures manuais; juiz ' + ('com modelo configurado' if modelo else 'NAO executado'),
            'casos': resultados, 'limite': 'Gabarito manual e comparação binária não comprovam acurácia geral nem equivalência a classificador NLI.'}
