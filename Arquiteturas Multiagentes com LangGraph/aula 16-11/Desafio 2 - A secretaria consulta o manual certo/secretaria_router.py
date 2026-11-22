"""Desafio 2 · A secretária consulta o manual certo (aula 16/11).

Router: classifica a pergunta como "agenda" ou "financeiro", consulta SÓ a base
correspondente e gera a resposta a partir dos documentos recuperados.

Fluxo:
    START -> classificar --(escolher_rota)--+--> buscar_agenda ------+--> responder -> END
                                            +--> buscar_financeiro --+

Como rodar (a partir da raiz do repositório, com a .venv):
    python "Arquiteturas Multiagentes com LangGraph/aula 16-11/Desafio 2 - A secretaria consulta o manual certo/secretaria_router.py"          # simulado
    python "Arquiteturas Multiagentes com LangGraph/aula 16-11/Desafio 2 - A secretaria consulta o manual certo/secretaria_router.py" --real   # OpenAI
    ... secretaria_router.py --chat [--real]   # você digita as perguntas e vê a rota

Modo simulado: classificação por palavras-chave e recuperação por palavras em comum.
Ele testa as LIGAÇÕES do grafo; NÃO é busca vetorial nem classificação por LLM.
No modo --real: gpt-4o-mini + OpenAIEmbeddings + InMemoryVectorStore.
"""

import sys
from typing import Literal, TypedDict

from langchain_core.documents import Document
from pydantic import BaseModel, Field, ValidationError
from langgraph.graph import END, START, StateGraph


# 1) Bases fictícias (regras inventadas só para o exercício)
DOCS_AGENDA = [
    Document("Visitas são marcadas de segunda a sexta, das 9h às 17h.",
             metadata={"base": "agenda", "id": "agenda-1"}),
    Document("Cada visita dura 60 minutos.", metadata={"base": "agenda", "id": "agenda-2"}),
]
DOCS_FINANCEIRO = [
    Document("O orçamento é dividido em 30% na contratação e 70% na conclusão.",
             metadata={"base": "financeiro", "id": "financeiro-1"}),
    Document("O pagamento é feito por Pix.", metadata={"base": "financeiro", "id": "financeiro-2"}),
]


# 2) Estado interno x contrato público
class SecretariaState(TypedDict):
    pergunta: str
    dominio: Literal["agenda", "financeiro"]
    documentos: list[Document]
    resposta: str


class Entrada(TypedDict):        # o que quem chama o grafo envia
    pergunta: str


class Saida(TypedDict):          # o que o grafo devolve (domínio fica interno)
    documentos: list[Document]
    resposta: str


# 3) Saída estruturada: só dois domínios aceitos
class RouteDecision(BaseModel):
    dominio: Literal["agenda", "financeiro"] = Field(
        description="agenda: horários, dias e duração de visitas; "
                    "financeiro: orçamento, percentuais e forma de pagamento."
    )


# 4) Versões simuladas (sem API)
class ClassificadorSimulado:
    """Imita structured_llm.invoke(pergunta) -> RouteDecision, por palavras-chave."""

    def invoke(self, pergunta: str) -> RouteDecision:
        p = pergunta.lower()
        financeiro = any(t in p for t in ("pag", "percent", "orçamento", "pix", "contrata", "valor"))
        return RouteDecision(dominio="financeiro" if financeiro else "agenda")


class RecuperadorSimulado:
    """Imita retriever.invoke(pergunta) com k=1: mais radicais de palavra em comum.

    Compara os 5 primeiros caracteres das palavras com 4+ letras
    ("marcar" ~ "marcadas"). É regra de texto, não similaridade de embeddings.
    """

    def __init__(self, docs):
        self.docs = docs

    @staticmethod
    def _radicais(texto: str) -> set[str]:
        limpo = "".join(c if c.isalnum() else " " for c in texto.lower())
        return {w[:5] for w in limpo.split() if len(w) >= 4}

    def invoke(self, pergunta: str) -> list[Document]:
        alvo = self._radicais(pergunta)
        melhor = max(self.docs, key=lambda d: len(alvo & self._radicais(d.page_content)))
        return [melhor]


class RespondedorSimulado:
    def invoke(self, pergunta: str, documentos: list[Document]) -> str:
        return "Segundo o manual: " + " ".join(d.page_content for d in documentos)


# 5) Versões reais (OpenAI)
class RespondedorLLM:
    def __init__(self, model):
        self.model = model

    def invoke(self, pergunta: str, documentos: list[Document]) -> str:
        trechos = "\n".join(f"- [{d.metadata['id']}] {d.page_content}" for d in documentos)
        # v1 e v2 recusavam perguntas como "posso pagar com cartão?" mesmo com a regra
        # do Pix em mãos: a saída "não encontrei" pesava mais que a permissão de concluir.
        # v3: regras numeradas + exemplos com OUTRAS palavras (não as do teste).
        sistema = (
            "Você é a secretária da empresa e responde em uma frase.\n"
            "1. Use somente os documentos fornecidos; não invente informações.\n"
            "2. Se o documento trata do mesmo assunto da pergunta, APLIQUE a regra, mesmo "
            "que a pergunta use outras palavras. Exemplos:\n"
            "   - Regra 'O pagamento é feito por Pix.' + 'Aceitam boleto?' -> "
            "'Não, o pagamento é feito por Pix.'\n"
            "   - Regra 'Atendemos de segunda a sexta.' + 'Abrem no domingo?' -> "
            "'Não, o atendimento é de segunda a sexta.'\n"
            "3. Responda 'Não encontrei a regra.' SOMENTE se o documento for de outro "
            "assunto (ex.: pergunta sobre endereço e documento sobre horários)."
        )
        usuario = f"Documentos:\n{trechos}\n\nPergunta: {pergunta}"
        return self.model.invoke([("system", sistema), ("human", usuario)]).content


def criar_componentes(real: bool):
    """Devolve (classificador, recuperador_agenda, recuperador_financeiro, respondedor)."""
    if not real:
        return (ClassificadorSimulado(), RecuperadorSimulado(DOCS_AGENDA),
                RecuperadorSimulado(DOCS_FINANCEIRO), RespondedorSimulado())

    from dotenv import load_dotenv
    from langchain_core.vectorstores import InMemoryVectorStore
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    load_dotenv()
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    embeddings = OpenAIEmbeddings()
    agenda = InMemoryVectorStore.from_documents(DOCS_AGENDA, embeddings)
    financeiro = InMemoryVectorStore.from_documents(DOCS_FINANCEIRO, embeddings)
    return (model.with_structured_output(RouteDecision),
            agenda.as_retriever(search_kwargs={"k": 1}),
            financeiro.as_retriever(search_kwargs={"k": 1}),
            RespondedorLLM(model))


# 6) Função da aresta condicional: só devolve o NOME do próximo nó
def escolher_rota(state: SecretariaState) -> Literal["buscar_agenda", "buscar_financeiro"]:
    if state["dominio"] == "agenda":
        return "buscar_agenda"
    if state["dominio"] == "financeiro":
        return "buscar_financeiro"
    # sem "else" amplo: rótulo inválido para o grafo em vez de cair em outra rota
    raise ValueError(f"Domínio inválido: {state['dominio']!r}")


# 7) Grafo
def montar_grafo(classificador, rec_agenda, rec_financeiro, respondedor):
    def classificar(state: SecretariaState) -> dict:
        decisao: RouteDecision = classificador.invoke(state["pergunta"])
        return {"dominio": decisao.dominio}

    def buscar_agenda(state: SecretariaState) -> dict:
        return {"documentos": rec_agenda.invoke(state["pergunta"])}

    def buscar_financeiro(state: SecretariaState) -> dict:
        return {"documentos": rec_financeiro.invoke(state["pergunta"])}

    def responder(state: SecretariaState) -> dict:
        return {"resposta": respondedor.invoke(state["pergunta"], state["documentos"])}

    builder = StateGraph(SecretariaState, input_schema=Entrada, output_schema=Saida)
    builder.add_node("classificar", classificar)
    builder.add_node("buscar_agenda", buscar_agenda)
    builder.add_node("buscar_financeiro", buscar_financeiro)
    builder.add_node("responder", responder)
    builder.add_edge(START, "classificar")
    builder.add_conditional_edges("classificar", escolher_rota)
    builder.add_edge("buscar_agenda", "responder")
    builder.add_edge("buscar_financeiro", "responder")
    builder.add_edge("responder", END)
    return builder.compile()


def executar_com_registro(graph, pergunta):
    """Usa stream para registrar cada nó percorrido e os documentos usados."""
    print(f"\nPergunta: {pergunta}")
    etapas, documentos = [], []
    for chunk in graph.stream({"pergunta": pergunta}):
        no, atualizacao = next(iter(chunk.items()))
        etapas.append(no)
        if "dominio" in atualizacao:
            print(f"  [{no}] domínio = {atualizacao['dominio']}")
        elif "documentos" in atualizacao:
            documentos = atualizacao["documentos"]
            ids = [f"{d.metadata['id']}: {d.page_content}" for d in documentos]
            print(f"  [{no}] documentos = {ids}")
        else:
            print(f"  [{no}] resposta = {atualizacao['resposta']}")
    print("  Sequência:", " -> ".join(etapas))
    return etapas, documentos


def chat(graph):
    """Modo interativo: cada pergunta mostra a rota e os documentos. /sair encerra."""
    while True:
        pergunta = input("\nVocê > ").strip()
        if pergunta == "/sair":
            break
        if pergunta:
            try:
                executar_com_registro(graph, pergunta)
            except ValueError as erro:  # rótulo inválido
                print("  Erro de rota:", erro)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    real = "--real" in sys.argv
    if "--chat" in sys.argv:
        print("Modo:", "REAL" if real else "SIMULADO", "| digite /sair para encerrar")
        return chat(montar_grafo(*criar_componentes(real)))
    print("Modo:", "REAL (gpt-4o-mini + OpenAIEmbeddings + InMemoryVectorStore)" if real
          else "SIMULADO (palavras-chave; não é busca vetorial nem LLM)")

    componentes = criar_componentes(real)
    graph = montar_grafo(*componentes)
    print("\nDesenho do grafo (Mermaid):")
    print(graph.get_graph().draw_mermaid())

    etapas_1, docs_1 = executar_com_registro(graph, "Em quais horários posso marcar uma visita?")
    etapas_2, docs_2 = executar_com_registro(graph, "Qual percentual é pago na contratação?")
    saida = graph.invoke({"pergunta": "Qual percentual é pago na contratação?"})

    # Rótulo inválido: (a) o schema Pydantic recusa; (b) se passar, o grafo para
    try:
        RouteDecision(dominio="suporte")
        pydantic_recusa = False
    except ValidationError:
        pydantic_recusa = True

    class ClassificadorQuebrado:  # contorna a validação de propósito (model_construct)
        def invoke(self, pergunta):
            return RouteDecision.model_construct(dominio="suporte")

    grafo_quebrado = montar_grafo(ClassificadorQuebrado(), *componentes[1:])
    etapas_invalidas = []
    try:
        for chunk in grafo_quebrado.stream({"pergunta": "Vocês fazem suporte?"}):
            etapas_invalidas += list(chunk)
        grafo_para = False
    except ValueError as erro:
        grafo_para = True
        print(f"\nRótulo inválido -> erro: {erro} | nós executados: {etapas_invalidas}")

    verificacoes = [
        ("Horários -> classificar, buscar_agenda, responder",
         etapas_1 == ["classificar", "buscar_agenda", "responder"]),
        ("Horários usou só documentos da base agenda",
         bool(docs_1) and all(d.metadata["base"] == "agenda" for d in docs_1)),
        ("Horários recuperou a regra de horários (agenda-1)",
         [d.metadata["id"] for d in docs_1] == ["agenda-1"]),
        ("Percentual -> classificar, buscar_financeiro, responder",
         etapas_2 == ["classificar", "buscar_financeiro", "responder"]),
        ("Percentual usou só documentos da base financeiro",
         bool(docs_2) and all(d.metadata["base"] == "financeiro" for d in docs_2)),
        ("Resposta do percentual cita 30%", "30" in saida["resposta"]),
        ("Saída pública tem só documentos e resposta", set(saida) == {"documentos", "resposta"}),
        ("RouteDecision recusa o rótulo 'suporte'", pydantic_recusa),
        ("Rótulo inválido para o grafo sem entrar em nenhuma busca",
         grafo_para and not any(e.startswith("buscar") for e in etapas_invalidas)),
    ]
    print("\nVerificações:")
    for nome, ok in verificacoes:
        print(f"  [{'OK' if ok else 'FALHOU'}] {nome}")
    if not real:
        print("\nLimite: classificação e recuperação SIMULADAS; testam as ligações do grafo,"
              " não a busca vetorial nem a compreensão de uma LLM.")
    sys.exit(0 if all(ok for _, ok in verificacoes) else 1)


if __name__ == "__main__":
    main()
