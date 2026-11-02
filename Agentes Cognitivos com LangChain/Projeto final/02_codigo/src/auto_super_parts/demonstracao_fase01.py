import json
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from .chain_inicial import criar_chains, processar_mensagem


PROJETO = Path(__file__).resolve().parents[3]


class ObservarSaidas(BaseCallbackHandler):
    # CALLBACK guarda o conteúdo bruto para distinguir erro de estrutura de erro de extração.
    # Não registra headers, chave, ambiente ou configuração do cliente HTTP.
    def __init__(self):
        self.saidas = []

    def on_llm_end(self, response, **kwargs):
        self.saidas.append(response.generations[0][0].message.content)

    def on_llm_error(self, error, **kwargs):
        self.saidas.append(None)


def carregar_casos():
    caminho = PROJETO / "04_avaliacao_e_evidencias/casos/casos_fase_01.json"
    return json.loads(caminho.read_text(encoding="utf-8"))


def criar_modelo_simulado(saidas):
    # DUMMY reproduz respostas roteirizadas para testar o encadeamento/parser offline.
    # Ele não interpreta a mensagem e não é evidência de acerto da LLM real.
    return FakeListChatModel(responses=[s if isinstance(s, str) else json.dumps(s, ensure_ascii=False) for s in saidas])


def comparar_esperado(esperado, observado, caminho=""):
    # GABARITO verifica apenas os campos especificados e permanece fora do prompt real.
    if isinstance(esperado, dict):
        if not isinstance(observado, dict):
            return [f"{caminho}: esperado objeto, observado {observado!r}"]
        return [erro for chave, valor in esperado.items() for erro in comparar_esperado(valor, observado.get(chave), f"{caminho}.{chave}")]
    return [] if esperado == observado else [f"{caminho}: esperado {esperado!r}; observado {observado!r}"]


def avaliar_casos(modo="simulado"):
    if modo not in ("real", "simulado"):
        raise ValueError("Modo deve ser real ou simulado; não há fallback automático.")
    casos = carregar_casos()
    modelo = criar_modelo_simulado([c["saida_simulada"] for c in casos]) if modo == "simulado" else None
    composicoes = criar_chains(modelo=modelo)
    # BATCH executa casos independentes. Concorrência 1 preserva a ordem do dummy e facilita auditoria.
    # RETURN_EXCEPTIONS mantém uma falha visível sem perder os demais casos do lote.
    entradas = [{"mensagem": c["mensagem"]} for c in casos]
    observador = ObservarSaidas()
    saidas = composicoes.lcel.batch(entradas, config={"max_concurrency": 1, "callbacks": [observador]}, return_exceptions=True)
    registros = []
    for indice, (caso, saida) in enumerate(zip(casos, saidas, strict=True)):
        # O tratamento de erro usa a mesma função da CLI sem fazer nova chamada à LLM.
        def devolver_resultado(entrada, valor=saida):
            if isinstance(valor, Exception):
                raise valor
            return valor
        observado = processar_mensagem(RunnableLambda(devolver_resultado), caso["mensagem"]).model_dump(mode="json")
        divergencias = comparar_esperado(caso["esperado"], observado)
        registros.append({"id": caso["id"], "mensagem": caso["mensagem"], "modo": modo,
                          "saida_modelo_nao_validada": observador.saidas[indice] if indice < len(observador.saidas) else None,
                          "esperado": caso["esperado"], "observado": observado, "passou": not divergencias,
                          "divergencias": divergencias})
    return registros


def registrar_evidencia(registros, modo, pasta=None):
    # EVIDÊNCIA guarda cada execução em arquivo próprio, sem reescrever falhas anteriores.
    pasta = Path(pasta) if pasta is not None else PROJETO / "04_avaliacao_e_evidencias/resultados"
    pasta.mkdir(parents=True, exist_ok=True)
    instante = datetime.now(timezone.utc)
    caminho = pasta / f"fase01_{modo}_{instante.strftime('%Y%m%dT%H%M%S%fZ')}.json"
    versoes = {p: version(p) for p in ("langchain-core", "langchain-openai", "pydantic", "python-dotenv")}
    payload = {"fase": 1, "modo": modo, "data_utc": instante.isoformat(), "versoes": versoes,
               "modelo": "gpt-4o-mini" if modo == "real" else "FakeListChatModel (saídas roteirizadas)",
               "resultados": registros, "passaram": sum(r["passou"] for r in registros), "total": len(registros),
               "limite": "Testes de fase 1; não verificam catálogo, compatibilidade, ferramentas, memória, RAG ou qualidade geral."}
    caminho.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return caminho
