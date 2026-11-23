"""Desafio 1 · O balcão consulta o catálogo antes de pensar (aula 18/11).

Compara dois grafos para a mesma pergunta:
  ReAct padrão:  START -> model <-> tools -> END           (o modelo decide a 1ª busca)
  First Model:   START -> first_model -> tools <-> model -> END
                 (first_model monta a ToolCall de buscar_catalogo SEM chamar a LLM)

Como rodar (a partir da raiz do repositório, com a .venv):
    python "Arquiteturas Multiagentes com LangGraph/aula 18-11/Desafio 1 - O balcao consulta o catalogo antes de pensar/balcao_first_model.py"          # simulado
    python "Arquiteturas Multiagentes com LangGraph/aula 18-11/Desafio 1 - O balcao consulta o catalogo antes de pensar/balcao_first_model.py" --real   # gpt-4o-mini

Modo simulado: o "modelo" é um roteiro fixo (busca -> calcula -> responde). Serve para
conferir as ligações dos grafos; os tempos medidos NÃO representam latência de LLM.
"""

import ast
import operator
import re
import sys
import time
import unicodedata
from typing import Annotated, TypedDict
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolCall
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

PERGUNTA = "Pastilha de freio dianteira para Onix 2019 1.0. Quanto ficam 2 jogos?"

# 1) Catálogo fictício (chave = termo de busca normalizado)
CATALOGO = {
    "pastilha dianteira onix 2019 1.0": "PF-221 · R$ 189,90 · 12 em estoque",
    "pastilha dianteira hb20 2020 1.0": "PF-305 · R$ 172,50 · 8 em estoque",
    "filtro oleo onix 2019 1.0": "FO-110 · R$ 39,90 · 25 em estoque",
    "amortecedor dianteiro onix 2019": "AM-402 · R$ 459,00 · 4 em estoque",
}
VOCABULARIO = {palavra for chave in CATALOGO for palavra in chave.split()}


def normalizar(texto: str) -> list[str]:
    """Minúsculas, sem acento; mantém números como '1.0' inteiros."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.findall(r"\d+\.\d+|\w+", sem_acento.lower())


def extrair_termo(pergunta: str) -> str:
    """Extração determinística: mantém só palavras do vocabulário do catálogo, na ordem."""
    return " ".join(p for p in normalizar(pergunta) if p in VOCABULARIO)


# 2) Ferramentas (a docstring é o que o modelo lê)
@tool
def buscar_catalogo(termo: str) -> str:
    """Consulta o catálogo de peças da loja e devolve código, preço unitário e estoque.

    Use SEMPRE antes de informar preço ou disponibilidade de uma peça.

    Args:
        termo: peça + posição + modelo + ano + motor, em minúsculas e sem preposições
            (ex: 'pastilha dianteira onix 2019 1.0').
    """
    chave = " ".join(normalizar(termo))
    if chave in CATALOGO:
        return f"{chave}: {CATALOGO[chave]}"
    return f"Não encontrado: '{chave}'. Termos disponíveis: {list(CATALOGO)}"


@tool
def calculator(expression: str) -> str:
    """Calculadora matemática segura para expressões aritméticas.
    Use esta ferramenta sempre que precisar calcular somas, subtrações, multiplicações,
    divisões ou potências exatas.

    Args:
        expression: Expressão matemática válida em sintaxe Python (ex: '2 * 189.90').
    """
    allowed_operators = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
    }

    def _eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            return allowed_operators[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            return allowed_operators[type(node.op)](_eval(node.operand))
        else:
            raise ValueError(f"Operação não suportada: {ast.dump(node)}")

    parsed = ast.parse(expression.strip(), mode="eval")
    return str(round(_eval(parsed.body), 2))  # round: evita 379.79999999999995


TOOLS = [buscar_catalogo, calculator]


# 3) Modelo: real ou roteiro simulado
SISTEMA = SystemMessage(
    "Você é o atendente do balcão de uma autopeças. Consulte o preço com buscar_catalogo "
    "e faça QUALQUER conta com calculator, nunca de cabeça. Responda em português, "
    "com valores em R$."
)


class ModeloSimulado:
    """Roteiro fixo que imita as decisões de um modelo com bind_tools (sem API)."""

    def invoke(self, messages):
        ferramentas_usadas = {m.name: m.content for m in messages if m.type == "tool"}
        pergunta = next(m.content for m in messages if m.type == "human")
        if "buscar_catalogo" not in ferramentas_usadas:
            chamada = ToolCall(name="buscar_catalogo", args={"termo": extrair_termo(pergunta)},
                               id=uuid4().hex)
            return AIMessage(content="", tool_calls=[chamada])
        if "calculator" not in ferramentas_usadas:
            preco = re.search(r"R\$ ([\d.]+),(\d{2})", ferramentas_usadas["buscar_catalogo"])
            qtd = re.search(r"(\d+)\s+jogos?", pergunta)
            expr = f"{qtd.group(1)} * {preco.group(1).replace('.', '')}.{preco.group(2)}"
            return AIMessage(content="", tool_calls=[
                ToolCall(name="calculator", args={"expression": expr}, id=uuid4().hex)])
        total = ferramentas_usadas["calculator"]
        return AIMessage(content=f"O total fica R$ {float(total):.2f}".replace(".", ","))


def criar_modelo(real: bool):
    if not real:
        return ModeloSimulado()
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI

    load_dotenv()
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.1).bind_tools(TOOLS)


# 4) Estado e grafos
class ReActState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def montar_grafos(model):
    def model_node(state: ReActState) -> dict:
        res = model.invoke([SISTEMA, *state["messages"]])
        return {"messages": [res]}

    def first_model(state: ReActState) -> dict:
        """Sem LLM: monta a ToolCall obrigatória de buscar_catalogo."""
        termo = extrair_termo(state["messages"][-1].content)
        forced_call = ToolCall(name=buscar_catalogo.name, args={"termo": termo}, id=uuid4().hex)
        return {"messages": [AIMessage(content="", tool_calls=[forced_call])]}

    react = StateGraph(ReActState)
    react.add_node("model", model_node)
    react.add_node("tools", ToolNode(TOOLS))
    react.add_edge(START, "model")
    react.add_conditional_edges("model", tools_condition)
    react.add_edge("tools", "model")

    forced = StateGraph(ReActState)
    forced.add_node("first_model", first_model)
    forced.add_node("model", model_node)
    forced.add_node("tools", ToolNode(TOOLS))
    forced.add_edge(START, "first_model")
    forced.add_edge("first_model", "tools")
    forced.add_edge("tools", "model")
    forced.add_conditional_edges("model", tools_condition)

    return react.compile(), forced.compile()


# 5) Execução com stream + perf_counter
def executar(nome, graph):
    print(f"\n=== {nome} ===")
    passos = []
    inicio = anterior = time.perf_counter()
    for idx, chunk in enumerate(graph.stream({"messages": [HumanMessage(PERGUNTA)]}), 1):
        agora = time.perf_counter()
        no = next(iter(chunk))
        msg = chunk[no]["messages"][-1]
        dur, acum = (agora - anterior) * 1000, (agora - inicio) * 1000
        anterior = agora
        if getattr(msg, "tool_calls", None):
            detalhe = "ToolCall: " + ", ".join(f"{tc['name']}({tc['args']})" for tc in msg.tool_calls)
        elif msg.type == "tool":
            detalhe = f"Resultado ({msg.name}): {msg.content[:90]}"
        else:
            detalhe = f"Resposta final: {msg.content}"
        print(f"[{dur:8.1f} ms | acum {acum:8.1f} ms] Passo {idx} | {no:<11} -> {detalhe}")
        passos.append({"no": no, "ms": dur, "msg": msg})
    return passos, (time.perf_counter() - inicio) * 1000


def resumo(passos, total_ms):
    chamadas = [tc for p in passos for tc in (getattr(p["msg"], "tool_calls", None) or [])]
    calc = [p["msg"].content for p in passos
            if p["msg"].type == "tool" and p["msg"].name == "calculator"]
    return {
        "primeiro_no": passos[0]["no"],
        "ms_passo1": passos[0]["ms"],
        "passos": len(passos),
        "model": sum(p["no"] == "model" for p in passos),
        "primeira_ferramenta": chamadas[0]["name"] if chamadas else "-",
        "ms_ate_1a_busca": next(sum(q["ms"] for q in passos[:i + 1])
                                for i, p in enumerate(passos) if p["no"] == "tools"),
        "total_ms": total_ms,
        "calculadora": calc,
        "resposta": passos[-1]["msg"].content,
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    real = "--real" in sys.argv
    print("Modo:", "REAL (gpt-4o-mini)" if real
          else "SIMULADO (roteiro fixo; tempos não representam LLM)")
    print("Pergunta:", PERGUNTA)

    react_graph, forced_graph = montar_grafos(criar_modelo(real))
    print("\nGrafo ReAct (Mermaid):\n" + react_graph.get_graph().draw_mermaid())
    print("Grafo First Model (Mermaid):\n" + forced_graph.get_graph().draw_mermaid())

    # Argumento do first_model: a pergunta inteira serve como chave do dicionário?
    termo = extrair_termo(PERGUNTA)
    busca_inteira = buscar_catalogo.invoke({"termo": PERGUNTA})
    busca_termo = buscar_catalogo.invoke({"termo": termo})
    print(f"Pergunta inteira como termo -> {busca_inteira[:60]}...")
    print(f"Termo extraído '{termo}' -> {busca_termo}")

    r = resumo(*executar("ReAct padrão", react_graph))
    f = resumo(*executar("First Model", forced_graph))

    print("\nComparação:")
    print(f"| {'Grafo':<12} | Passos | Chamadas ao model | 1ª ferramenta   | Até a 1ª busca | Total      |")
    print(f"|{'-' * 14}|--------|-------------------|-----------------|----------------|------------|")
    for nome, x in (("ReAct", r), ("First Model", f)):
        print(f"| {nome:<12} | {x['passos']:^6} | {x['model']:^17} | {x['primeira_ferramenta']:<15} "
              f"| {x['ms_ate_1a_busca']:>11.1f} ms | {x['total_ms']:>7.1f} ms |")

    verificacoes = [
        ("Pergunta inteira NÃO encontra no dicionário", busca_inteira.startswith("Não encontrado")),
        ("Termo extraído encontra PF-221", "PF-221" in busca_termo),
        (f"First Model: passo 1 é first_model em poucos ms ({f['ms_passo1']:.1f} ms < 50)",
         f["primeiro_no"] == "first_model" and f["ms_passo1"] < 50),
        ("First Model: 1ª ferramenta é buscar_catalogo", f["primeira_ferramenta"] == "buscar_catalogo"),
        # "menos", não "exatamente 1 a menos": no ReAct real a LLM pode errar o termo e
        # gastar chamadas extras para se corrigir (aconteceu na 1ª execução --real).
        (f"First Model chama menos o model ({f['model']} x {r['model']})", f["model"] < r["model"]),
        ("ReAct: conta saiu da calculadora (379.8)", r["calculadora"] == ["379.8"]),
        ("First Model: conta saiu da calculadora (379.8)", f["calculadora"] == ["379.8"]),
        ("Respostas finais citam 379,80",
         all("379,80" in x["resposta"] or "379.80" in x["resposta"] for x in (r, f))),
    ]
    print(f"\nReAct: o modelo escolheu '{r['primeira_ferramenta']}' como 1ª ferramenta "
          "(decisão da LLM, não garantida pelo grafo).")
    print("\nVerificações:")
    for nome, ok in verificacoes:
        print(f"  [{'OK' if ok else 'FALHOU'}] {nome}")
    if not real:
        print("\nLimite: modelo SIMULADO por roteiro; confere ligações e a origem da conta, "
              "não a decisão real de uma LLM nem a latência real.")
    sys.exit(0 if all(ok for _, ok in verificacoes) else 1)


if __name__ == "__main__":
    main()
