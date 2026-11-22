"""Desafio 1 · A recepção lembra de cada conversa (aula 16/11).

Uma oficina tem um chat de recepção. Ana e Bruno acompanham veículos
diferentes; cada conversa (thread_id) precisa lembrar só o próprio veículo.

Fluxo:  START -> atendimento -> END

Como rodar (a partir da raiz do repositório, com a .venv):
    python "Arquiteturas Multiagentes com LangGraph/aula 16-11/desafio1_recepcao.py"          # modelo simulado
    python "Arquiteturas Multiagentes com LangGraph/aula 16-11/desafio1_recepcao.py" --real   # gpt-4o-mini (usa OPENAI_API_KEY)
    python "Arquiteturas Multiagentes com LangGraph/aula 16-11/desafio1_recepcao.py" --chat   # você conversa (pode somar --real)

Limite do modo simulado: o "modelo" só procura texto no histórico com regra fixa.
Ele prova que o histórico está organizado por sessão, NÃO prova compreensão de uma LLM.
"""

import re
import sys
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


# 1) Estado: um campo de mensagens com o reducer add_messages
#    (cada retorno do nó é ACRESCENTADO ao histórico, não substitui a lista).
class State(TypedDict):
    messages: Annotated[list, add_messages]


# 2) Modelo: real (OpenAI) ou simulado
class ModeloSimulado:
    """Imita model.invoke(mensagens): lê SÓ o histórico recebido e responde por regra."""

    def invoke(self, messages):
        textos = [m.content for m in messages if isinstance(m, HumanMessage)]
        pergunta = textos[-1].lower()
        historico = " ".join(textos[:-1])
        # ABC1234 / Mercosul ABC1D23 (aceita 1 dígito a mais, para digitação de teste)
        placa_br = r"\b([A-Za-z]{3}-?\d[A-Za-z0-9]\d{2,3})\b"
        fato_visita = r"visita\b.*?\b(?:ser[aá]|vai ser) (.+)"  # aceita "visita na verdade vai ser ..."

        if re.search(placa_br, pergunta):
            placa = re.search(placa_br, pergunta).group(1).upper()
            resposta = f"Anotado: você está acompanhando o veículo {placa}."
        elif re.search(fato_visita, pergunta) and "?" not in pergunta:
            resposta = "Anotado: visita registrada."
        elif "visita" in pergunta:
            # pega o fato MAIS RECENTE e copia o resto da frase (regra fixa, não entende texto)
            fatos = [re.search(fato_visita, t, re.I) for t in textos[:-1]]
            fatos = [f.group(1).rstrip(".") for f in fatos if f]
            resposta = (f"A visita será {fatos[-1]}."
                        if fatos else "Não há visita registrada nesta conversa.")
        elif "qual" in pergunta or "?" in pergunta:
            placas = re.findall(placa_br, historico)
            resposta = (f"Você está acompanhando o veículo {placas[-1].upper()}."
                        if placas else "Não encontrei nenhum veículo nesta conversa.")
        else:
            resposta = "Anotado."
        return AIMessage(content=resposta)


def criar_modelo(real: bool):
    if not real:
        return ModeloSimulado()
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI

    load_dotenv()
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


# 3) Grafo com um único nó entre START e END
def montar_grafo(model, checkpointer):
    def atendimento(state: State) -> dict:
        resposta = model.invoke(state["messages"])  # lê todo o histórico da thread
        return {"messages": [resposta]}             # devolve só a resposta nova

    builder = StateGraph(State)
    builder.add_node("atendimento", atendimento)
    builder.add_edge(START, "atendimento")
    builder.add_edge("atendimento", END)
    return builder.compile(checkpointer=checkpointer)


def perguntar(graph, config, texto):
    resultado = graph.invoke({"messages": [HumanMessage(content=texto)]}, config=config)
    return resultado["messages"][-1].content


def mensagens(graph, config):
    return graph.get_state(config).values.get("messages", [])


def chat(real: bool):
    """Modo interativo: você digita e escolhe a sessão."""
    graph = montar_grafo(criar_modelo(real), MemorySaver())
    sessao = "ana"
    print("Comandos: /sessao NOME (troca de conversa) | /fato TEXTO (update_state, sem modelo)"
          " | /estado (mostra o snapshot) | /sair")
    while True:
        config = {"configurable": {"thread_id": sessao}}
        texto = input(f"[{sessao}] você > ").strip()
        if not texto:
            continue
        if texto == "/sair":
            break
        if texto.startswith("/sessao "):
            sessao = texto.split(maxsplit=1)[1]
        elif texto.startswith("/fato "):
            graph.update_state(config, {"messages": [HumanMessage(content=texto[6:])]})
            print("  (fato gravado no estado, modelo não foi chamado)")
        elif texto == "/estado":
            for m in mensagens(graph, config):
                print(f"  {type(m).__name__}: {m.content}")
        else:
            print(f"[{sessao}] recepção >", perguntar(graph, config, texto))


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # acentos no terminal do Windows
    real = "--real" in sys.argv
    if "--chat" in sys.argv:
        return chat(real)
    print(f"Modo: {'gpt-4o-mini (real)' if real else 'modelo SIMULADO'}\n")

    graph = montar_grafo(criar_modelo(real), MemorySaver())
    print("Desenho do fluxo (Mermaid):")
    print(graph.get_graph().draw_mermaid())

    # 4) Duas threads distintas = duas conversas separadas
    ana = {"configurable": {"thread_id": "recepcao_ana"}}
    bruno = {"configurable": {"thread_id": "recepcao_bruno"}}

    print("Ana   >", perguntar(graph, ana, "Estou acompanhando o veículo ABC1D23"))
    print("Bruno >", perguntar(graph, bruno, "Estou acompanhando o veículo XYZ9A87"))

    resp_ana = perguntar(graph, ana, "Qual veículo estou acompanhando?")
    resp_bruno = perguntar(graph, bruno, "Qual veículo estou acompanhando?")
    print("Ana   > Qual veículo?", resp_ana)
    print("Bruno > Qual veículo?", resp_bruno)

    # 5) Correção manual de contexto: update_state NÃO chama o modelo
    antes_ana = len(mensagens(graph, ana))
    antes_bruno = len(mensagens(graph, bruno))
    graph.update_state(ana, {"messages": [HumanMessage(content="A visita será na sexta-feira")]})
    snap_ana = mensagens(graph, ana)
    snap_bruno = mensagens(graph, bruno)
    print(f"\nSnapshot Ana: {antes_ana} -> {len(snap_ana)} mensagens | "
          f"última: {type(snap_ana[-1]).__name__}: {snap_ana[-1].content!r}")
    print(f"Snapshot Bruno: {antes_bruno} -> {len(snap_bruno)} mensagens")

    # Nova resposta, só depois da atualização manual
    resp_visita = perguntar(graph, ana, "Quando será a visita?")
    resp_visita_bruno = perguntar(graph, bruno, "Quando será a visita?")
    print("Ana   > Quando será a visita?", resp_visita)
    print("Bruno > Quando será a visita?", resp_visita_bruno)

    # 6) Novo MemorySaver (como reiniciar o processo): memória vazia
    graph_novo = montar_grafo(criar_modelo(real), MemorySaver())
    apos_reinicio = len(mensagens(graph_novo, ana))

    # 7) Registro das verificações
    texto_bruno = " ".join(m.content for m in snap_bruno)
    verificacoes = [
        ("Ana recupera o próprio veículo (ABC1D23)", "ABC1D23" in resp_ana),
        ("Bruno recupera o próprio veículo (XYZ9A87)", "XYZ9A87" in resp_bruno),
        ("Resposta de Ana não cita o veículo de Bruno", "XYZ9A87" not in resp_ana),
        ("Sessão de Bruno não contém dados de Ana",
         "ABC1D23" not in texto_bruno and "sexta" not in texto_bruno.lower()),
        ("update_state acrescentou 1 mensagem só na Ana (sem resposta do modelo)",
         len(snap_ana) == antes_ana + 1 and isinstance(snap_ana[-1], HumanMessage)
         and len(snap_bruno) == antes_bruno),
        ("Após o update, a Ana responde com a sexta-feira", "sexta" in resp_visita.lower()),
        ("Bruno não sabe da visita da Ana", "sexta" not in resp_visita_bruno.lower()),
        ("Novo MemorySaver começa vazio (memória NÃO é durável)", apos_reinicio == 0),
    ]
    print("\nVerificações:")
    for nome, ok in verificacoes:
        print(f"  [{'OK' if ok else 'FALHOU'}] {nome}")
    if not real:
        print("\nLimite: modelo simulado; o teste valida a organização do histórico,"
              " não a compreensão real de uma LLM.")
    sys.exit(0 if all(ok for _, ok in verificacoes) else 1)


if __name__ == "__main__":
    main()
