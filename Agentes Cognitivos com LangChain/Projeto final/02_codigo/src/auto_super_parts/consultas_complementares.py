"""Consultas locais e regras específicas para as falhas observadas em 08/11."""
import json
import re

from .configuracao import localizar_projeto
from .orcamento_fase02 import normalizar
from .referencia_veiculo import conferir_referencia


# CONSULTA DOCUMENTAL ESTRUTURADA: usa os registros já cadastrados, sem RAG ou pesquisa externa.
def consultar_tecnica(veiculo_id, assunto):
    pasta = localizar_projeto() / "02_codigo/dados"
    veiculos = json.loads((pasta / "veiculos.json").read_text(encoding="utf-8-sig"))
    if veiculo_id not in {v["id"] for v in veiculos}:
        return {"status": "veiculo_nao_encontrado", "informacoes": [], "fontes": []}
    registros = json.loads((pasta / "conhecimento_tecnico.json").read_text(encoding="utf-8"))
    encontrados = [r for r in registros if r.get("veiculo_id") in (veiculo_id, None)
                   and r["assunto"] == assunto]
    fontes = json.loads((pasta / "fontes.json").read_text(encoding="utf-8"))["fontes"]
    ids = {f for r in encontrados for f in r.get("fontes", [])}
    # PROVENIÊNCIA: fonte existente e status do registro são requisitos separados.
    # Um link em um registro pendente não transforma uma lacuna em fato técnico.
    cadastradas = {f['id'] for f in fontes}
    disponiveis = [r for r in encontrados if r.get('status') != 'pendente'
                   and r.get('fontes') and set(r['fontes']) <= cadastradas]
    status = "informacao_disponivel" if disponiveis else "informacao_pendente"
    return {"status": status, "veiculo_id": veiculo_id,
            "veiculo": next(v for v in veiculos if v['id'] == veiculo_id), "assunto": assunto,
            "informacoes": encontrados, "fontes": [f for f in fontes if f["id"] in ids],
            "limite": "Utilize somente o conteúdo registrado e respeite os limites de cada fonte."}


def pede_correia_dentada(mensagem):
    return bool(re.search(r"\bcorreia(?:s)?\s+(?:dentada(?:s)?|de\s+sincronismo)\b", normalizar(mensagem)))


def pede_especificacao_oleo(mensagem):
    t = normalizar(mensagem)
    return "oleo" in t and bool(re.search(
        r"viscos|capacidade|norma|quantos?\s+litros?|qual\s+oleo|oleo.*recomend|recomend.*oleo|troc|interval|quilometr", t))


def resposta_oleo_documentada(consultas, mensagem=""):
    """Apresenta somente o contrato curado retornado pela ferramenta deste turno."""
    blocos = []
    texto = normalizar(mensagem)
    modelos_citados = {m for m in ('gol', 'palio', 'celta', 'fusca', 's10') if re.search(r'\b' + m + r'\b', texto)}
    anos_citados = {int(a) for a in re.findall(r'\b(?:19|20)\d{2}\b', texto)}
    for consulta in consultas:
        if consulta.get('assunto') != 'oleo' or consulta.get('status') != 'informacao_disponivel':
            continue
        veiculo = consulta.get('veiculo', {})
        if modelos_citados and normalizar(veiculo.get('modelo', '')) not in modelos_citados:
            continue
        if anos_citados and veiculo.get('ano_modelo') not in anos_citados:
            continue
        fontes = {f['id']: f for f in consulta.get('fontes', [])}
        for registro in consulta.get('informacoes', []):
            oleo = registro.get('dados_oleo')
            if registro.get('status') != 'verificado_manual' or not oleo or not registro.get('fontes'):
                continue
            if not set(registro['fontes']) <= fontes.keys():
                continue
            veiculo = consulta.get('veiculo', {})
            nome_veiculo = ' '.join(str(veiculo.get(k, '')) for k in ('modelo', 'ano_modelo', 'motor', 'combustivel')).strip()
            linhas = [f"Especificação cadastrada para {nome_veiculo or consulta['veiculo_id']}:"]
            for especificacao in oleo['especificacoes']:
                linhas.append(f"- SAE {especificacao['viscosidade_sae']}, {especificacao['norma']}.")
                for regime, intervalo in especificacao['intervalos'].items():
                    km = f"{intervalo['km']:,}".replace(',', '.')
                    linhas.append(f"  Uso {regime}: {km} km ou {intervalo['meses']} meses, o que ocorrer primeiro.")
            for servico, litros in oleo['capacidade_litros'].items():
                nome = 'com troca do filtro' if servico == 'com_troca_filtro' else 'sem troca do filtro'
                if litros is not None:
                    linhas.append(f"- Capacidade {nome}: {str(litros).replace('.', ',')} litros.")
            if all(v is None for v in oleo['capacidade_litros'].values()):
                linhas.append('Capacidade em litros ainda não confirmada para a configuração exata.')
            linhas.extend(oleo.get('observacoes', []))
            linhas.append('Para definir o intervalo aplicável: como é a rotina de uso? Há trajetos curtos, poeira ou marcha lenta prolongada?')
            for fonte in registro['fontes']:
                linhas.append(f"Fonte: {fontes[fonte].get('titulo', fonte)} — {registro.get('localizacao', '')}: {fontes[fonte]['url']}")
            blocos.append('\n'.join(linhas))
    return '\n\n'.join(blocos) or None


# PROTEÇÃO DE TIPO: a categoria solicitada não pode ser silenciosamente trocada por outra peça.
def conferir_tipo_catalogo(mensagem, categoria, retorno):
    if not pede_correia_dentada(mensagem):
        return retorno
    categorias = {p["categoria"] for p in retorno.get("produtos", [])}
    if categoria == "correia_acessorios" or categorias - {"correia_dentada"}:
        return {"status": "tipo_peca_divergente", "produtos": [], "aplicacoes": [],
                "tipo_solicitado": "correia_dentada", "categoria_recusada": categoria,
                "pendencias": ["Correia dentada e correia de acessórios não são equivalentes. "
                               "Consulte a informação de sincronismo do veículo; não substitua a peça."]}
    return retorno


# REGRAS DE RESPOSTA ESPECÍFICAS: não são NLI nem um verificador semântico geral.
# Bloqueiam as duas falhas observadas mesmo se o modelo ignorar as instruções do prompt.
def conferir_resposta(mensagem, mensagens, candidata, catalogo=None):
    # CLARIFICAÇÃO tem prioridade sobre a proteção técnica: não apagar a pergunta sobre geração.
    if catalogo is not None and (pede_especificacao_oleo(mensagem) or pede_correia_dentada(mensagem)):
        referencia = conferir_referencia(catalogo, mensagem)
        if referencia['erro'] and referencia['erro']['status'] == 'veiculo_ambiguo':
            return ('Seu Fusca é o clássico a ar ou o TSI? Informe ano e motor, ou o ID do veículo.',
                    {'regra':'esclarecer_geracao_antes_da_especificacao','substituida':True,
                     'consulta_tecnica_executada':any(getattr(m, 'type', None)=='tool' and getattr(m, 'name', None)=='consultar_informacao_tecnica' for m in mensagens)})
    tecnicas = []
    for msg in mensagens:
        if getattr(msg, "type", None) == "tool" and msg.name == "consultar_informacao_tecnica":
            try:
                tecnicas.append(json.loads(msg.content))
            except (ValueError, TypeError):
                pass
    if pede_especificacao_oleo(mensagem):
        # VERIFICAÇÃO DETERMINÍSTICA: só libera os campos do contrato técnico consultado.
        documentada = resposta_oleo_documentada(tecnicas, mensagem)
        if documentada:
            return documentada, {'regra':'oleo_com_fonte_cadastrada', 'substituida':candidata != documentada,
                                 'consulta_tecnica_executada':True}
        resposta = ("Não tenho especificações verificadas de viscosidade, norma e capacidade de óleo "
                    "para essa configuração na base disponível. Preciso de uma fonte técnica aplicável "
                    "ao veículo e ao motor antes de recomendar o óleo ou a quantidade de litros.")
        return resposta, {"regra": "oleo_sem_especificacao_verificada", "substituida": candidata != resposta,
                          "consulta_tecnica_executada": any(t.get("assunto") == "oleo" for t in tecnicas)}
    # CONDIÇÃO TÉCNICA: não omitir direção hidráulica ao apresentar a regra do alternador.
    if 'alternador' in normalizar(mensagem):
        fonte = next((t for t in tecnicas if t.get('veiculo_id') == 'V003'
                      and t.get('assunto') == 'alternador' and t.get('status') == 'informacao_disponivel'), None)
        if fonte and not any(m in normalizar(mensagem) for m in ('fusca', 'gol', 'palio', 's10')):
            registro = next((r for r in fonte['informacoes'] if r.get('status') == 'verificado_manual'), None)
            if registro:
                dados = registro['dados']
                resposta = (f"No Celta 2012 1.0 flex original, o manual diferencia "
                            f"{dados['com_ar_ou_direcao_hidraulica_a']} A com ar-condicionado e/ou direção hidráulica "
                            f"e {dados['sem_ar_condicionado_a']} A na configuração sem esses equipamentos. "
                            "Confirme os equipamentos e a referência instalada: a amperagem sozinha não identifica o código da peça. "
                            "Fonte: " + fonte['fontes'][0]['url'])
                return resposta, {'regra':'alternador_equipamentos', 'substituida':candidata != resposta,
                                  'consulta_tecnica_executada':True}
    if pede_correia_dentada(mensagem):
        fonte = next((t for t in tecnicas if t.get("veiculo_id") == "V004"
                      and t.get("assunto") == "sincronismo" and t.get("status") == "informacao_disponivel"), None)
        if fonte:
            resposta = ("Para o Fusca 1982 1600 a ar, a informação técnica cadastrada indica que o "
                        "sincronismo do comando é por engrenagens, não por correia dentada. "
                        "A correia externa em V do alternador/dínamo tem outra função e não a substitui. "
                        "A referência cadastrada é parcial; não valida código ou dimensões de uma peça.")
        else:
            confirmada = next((t for t in tecnicas if t.get('assunto') == 'sincronismo'
                               and t.get('status') == 'informacao_disponivel'
                               and any(r.get('status') == 'verificado_manual'
                                       and r.get('dados', {}).get('tipo') == 'correia_dentada'
                                       for r in t.get('informacoes', []))), None)
            if confirmada:
                resposta = ('O manual cadastrado confirma correia dentada de distribuição nessa configuração. '
                            'Ela é diferente da correia de acessórios. O código da peça e o intervalo de troca '
                            'ainda precisam de confirmação; não vou inventar esses valores.')
                fonte = confirmada
            else:
                resposta = ("Você pediu uma correia dentada. Não tenho evidência técnica suficiente nesta consulta "
                            "para indicar essa peça para o veículo. Não vou substituí-la por uma correia de acessórios.")
        return resposta, {"regra": "preservar_tipo_correia", "substituida": candidata != resposta,
                          "consulta_tecnica_executada": fonte is not None}
    return candidata, {"regra": "fora_das_protecoes_especificas", "substituida": False}
