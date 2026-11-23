"""Desafio 2 · Orçamento em etapas com replanejamento (aula 18/11).

Plan-and-Execute:
    START -> planner -> executor -> replanner --(continuar?)--+--> executor   (volta)
                                                              +--> END
    executor = subgrafo ReAct (model <-> tools) que resolve UMA etapa por vez.

Adaptação didática: o estado conta as rodadas (rodada / max_rodadas), como o
iteration / max_iterations do Reflection, para o grafo sempre parar.

Como rodar (a partir da raiz do repositório, com a .venv):
    python "Arquiteturas Multiagentes com LangGraph/aula 18-11/Desafio 2 - Orcamento em etapas com replanejamento/orcamento_plan_execute.py"          # simulado
    python "Arquiteturas Multiagentes com LangGraph/aula 18-11/Desafio 2 - Orcamento em etapas com replanejamento/orcamento_plan_execute.py" --real   # gpt-4o-mini

Modo simulado: planner, executor e replanner seguem roteiros fixos (regex). Confere as
ligações, o estado e as paradas; NÃO demonstra planejamento real de uma LLM.
"""

import ast
import operator
import re
import sys
from typing import Annotated, Literal, Optional, TypedDict
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolCall
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

PEDIDO = ("Verifique se há 4 velas de ignição VL-30 em estoque, calcule o frete de 2 kg "
          "para o CEP 41810-000 e me diga o total com as velas a R$ 32,50 cada.")
PEDIDO_SKU_INEXISTENTE = PEDIDO.replace("VL-30", "VL-99")

ESTOQUE = {"VL-30": 18, "PF-221": 12}  # fictício


# 1) Ferramentas do executor
@tool
def consultar_estoque(sku: str) -> str:
    """Consulta quantas unidades de um SKU existem no estoque da loja.

    Args:
        sku: código da peça, ex: 'VL-30'.
    """
    sku = sku.strip().upper()
    if sku not in ESTOQUE:
        return f"SKU '{sku}' não encontrado no estoque."
    return f"{sku}: {ESTOQUE[sku]} unidades em estoque."


@tool
def calcular_frete(peso_kg: float, cep: str) -> str:
    """Calcula o frete de um envio pela fórmula da loja: R$ 25,00 + R$ 4,50 por kg.

    Args:
        peso_kg: peso total do envio em kg.
        cep: CEP de destino, ex: '41810-000'.
    """
    valor = 25 + peso_kg * 4.5
    return f"Frete de {peso_kg} kg para o CEP {cep}: R$ {valor:.2f}"


@tool
def calculator(expression: str) -> str:
    """Calculadora matemática segura para expressões aritméticas.
    Use esta ferramenta sempre que precisar calcular somas, subtrações, multiplicações,
    divisões ou potências exatas.

    Args:
        expression: Expressão matemática válida em sintaxe Python (ex: '4 * 32.50 + 34.00').
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
    return str(round(_eval(parsed.body), 2))


EXECUTOR_TOOLS = [consultar_estoque, calcular_frete, calculator]


# 2) Contratos (saída estruturada) e estado
class PlanSchema(BaseModel):
    """Plano ordenado de etapas para resolver o objetivo do usuário."""
    steps: list[str] = Field(
        description="Lista sequencial de etapas claras e atômicas. Cada etapa deve ser uma ação verificável."
    )


class ReplanDecision(BaseModel):
    """Decisão do replanner após inspecionar o progresso das etapas executadas."""
    is_complete: bool = Field(
        description="True se já é possível responder ao objetivo com o que está em past_steps "
                    "(inclusive se uma etapa mostrou que o pedido não pode ser atendido)."
    )
    updated_remaining_steps: list[str] = Field(
        description="Se is_complete=False, só as etapas que AINDA faltam. Se True, lista vazia []."
    )
    final_response: Optional[str] = Field(
        default=None,
        description="Se is_complete=True, a resposta final ao cliente, só com números vindos dos resultados.",
    )


class PlanExecuteState(TypedDict):
    objective: str
    plan: list[str]
    past_steps: Annotated[list[tuple[str, str]], operator.add]  # só acrescenta
    final_response: str
    rodada: int        # adaptação didática: quantas etapas o executor já rodou
    max_rodadas: int   # limite de segurança


# 3) Versões simuladas (sem API)
def _extrair(objetivo: str) -> dict:
    return {
        "sku": re.search(r"\b([A-Z]{2,3}-\d{2,3})\b", objetivo).group(1),
        "qtd": re.search(r"há (\d+)", objetivo).group(1),
        "kg": re.search(r"(\d+(?:[.,]\d+)?)\s*kg", objetivo).group(1),
        "cep": re.search(r"\d{5}-\d{3}", objetivo).group(0),
        "preco": re.search(r"R\$\s*([\d.]+),(\d{2})", objetivo).expand(r"\1.\2"),
    }


class PlannerSimulado:
    def invoke(self, messages) -> PlanSchema:
        d = _extrair(messages[-1].content)
        return PlanSchema(steps=[
            f"Consultar o estoque do SKU {d['sku']} e verificar se há {d['qtd']} unidades.",
            f"Calcular o frete de {d['kg']} kg para o CEP {d['cep']}.",
            f"Calcular com a calculadora o total: {d['qtd']} x R$ {d['preco']} + frete.",
        ])


class ExecutorModeloSimulado:
    """Imita o modelo do subgrafo: pede UMA ferramenta e depois relata o resultado."""

    def invoke(self, messages):
        if messages[-1].type == "tool":
            return AIMessage(content=messages[-1].content)
        prompt = messages[-1].content
        etapa = re.search(r"SUA TAREFA ATUAL: .*?'(.+)'", prompt, re.S).group(1)
        if "estoque" in etapa:
            nome, args = "consultar_estoque", {"sku": re.search(r"[A-Z]{2,3}-\d{2,3}", etapa).group(0)}
        elif "frete" in etapa and "total" not in etapa:
            nome, args = "calcular_frete", {
                "peso_kg": float(re.search(r"([\d.]+) kg", etapa).group(1)),
                "cep": re.search(r"\d{5}-\d{3}", etapa).group(0)}
        else:
            qtd, preco = re.search(r"(\d+) x R\$ ([\d.]+)", etapa).groups()
            frete = re.search(r"Frete .*?R\$ ([\d.]+)", prompt).group(1)
            nome, args = "calculator", {"expression": f"{qtd} * {preco} + {frete}"}
        return AIMessage(content="", tool_calls=[ToolCall(name=nome, args=args, id=uuid4().hex)])


class ReplannerSimulado:
    def invoke(self, messages) -> ReplanDecision:
        texto = messages[-1].content
        restantes = ast.literal_eval(texto.split("Etapas que restavam na fila:\n")[1].split("\n")[0])
        if "não encontrado" in texto:
            sku = re.search(r"SKU '([^']+)' não encontrado", texto).group(1)
            return ReplanDecision(is_complete=True, updated_remaining_steps=[], final_response=(
                f"Não há o item {sku} no estoque, então não calculei frete nem total."))
        if restantes:
            return ReplanDecision(is_complete=False, updated_remaining_steps=restantes)
        def brl(valor):
            return f"R$ {float(valor):.2f}".replace(".", ",")

        estoque = re.search(r"\d+ unidades em estoque", texto).group(0)
        frete = re.search(r"Frete .*?R\$ ([\d.]+)", texto).group(1)
        feitos = texto.split("(past_steps):\n")[1].split("\n\nEtapas que restavam")[0]
        total = feitos.strip().split("\n")[-1].split(": ")[-1]  # último resultado = calculator
        return ReplanDecision(is_complete=True, updated_remaining_steps=[], final_response=(
            f"Há {estoque}. Frete: {brl(frete)}. Total: {brl(total)}."))


def criar_modelos(real: bool):
    """Devolve (planner_llm, executor_llm_bound, replanner_llm)."""
    if not real:
        return PlannerSimulado(), ExecutorModeloSimulado(), ReplannerSimulado()
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI

    load_dotenv()
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return (llm.with_structured_output(PlanSchema),
            llm.bind_tools(EXECUTOR_TOOLS),
            llm.with_structured_output(ReplanDecision))


# 4) Subgrafo executor (ReAct) e grafo principal
class SubExecutorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def montar_grafo(planner_llm, executor_llm_bound, replanner_llm):
    def sub_model_node(state: SubExecutorState) -> dict:
        return {"messages": [executor_llm_bound.invoke(state["messages"])]}

    sub = StateGraph(SubExecutorState)
    sub.add_node("model", sub_model_node)
    sub.add_node("tools", ToolNode(EXECUTOR_TOOLS))
    sub.add_edge(START, "model")
    sub.add_conditional_edges("model", tools_condition)
    sub.add_edge("tools", "model")
    task_executor_agent = sub.compile()

    def planner_node(state: PlanExecuteState) -> dict:
        # LÊ: objective | GRAVA: plan
        sys_prompt = (
            "Você é o planejador do balcão de uma autopeças. Decomponha o pedido em 3 a 4 "
            "etapas sequenciais, sem etapas supérfluas. Cada etapa será executada por um "
            "agente com as ferramentas: consultar_estoque, calcular_frete e calculator."
        )
        plano: PlanSchema = planner_llm.invoke([
            SystemMessage(content=sys_prompt), HumanMessage(content=f"Objetivo: {state['objective']}")])
        return {"plan": plano.steps}

    def executor_node(state: PlanExecuteState) -> dict:
        # LÊ: plan[0], past_steps, objective | GRAVA: +1 tupla em past_steps, rodada + 1
        etapa = state["plan"][0]
        contexto = "\n".join(f"- Etapa concluída: {s} => Resultado: {r}" for s, r in state["past_steps"])
        prompt = (
            f"Objetivo Global: {state['objective']}\n"
            f"Contexto de Etapas Anteriores:\n{contexto or 'Nenhuma etapa executada ainda.'}\n\n"
            f"SUA TAREFA ATUAL: Execute APENAS a seguinte etapa e retorne o resultado exato obtido: '{etapa}'"
        )
        res = task_executor_agent.invoke({"messages": [HumanMessage(content=prompt)]})
        return {"past_steps": [(etapa, res["messages"][-1].content)], "rodada": state["rodada"] + 1}

    def replanner_node(state: PlanExecuteState) -> dict:
        # LÊ: objective, plan, past_steps | GRAVA: final_response (e plan=[]) OU plan restante
        feitos = "\n".join(f"- {s}: {r}" for s, r in state["past_steps"])
        prompt = (
            f"Objetivo Original do Usuário:\n{state['objective']}\n\n"
            f"Plano Original:\n{state['plan']}\n\n"
            f"Etapas Já Executadas e Seus Resultados (past_steps):\n{feitos}\n\n"
            f"Etapas que restavam na fila:\n{state['plan'][1:]}\n\n"
            "Avalie: se as informações pedidas já constam nos resultados, OU se algum resultado "
            "mostra que o pedido não pode ser atendido (ex.: item inexistente), marque "
            "is_complete=True e escreva a final_response usando só números dos resultados, "
            "sem inventar estoque. Caso contrário, is_complete=False e updated_remaining_steps "
            "apenas com o que falta."
        )
        decisao: ReplanDecision = replanner_llm.invoke([
            SystemMessage(content="Você é o replanner de uma arquitetura Plan-and-Execute."),
            HumanMessage(content=prompt)])
        if decisao.is_complete:
            return {"final_response": decisao.final_response or "", "plan": []}
        return {"plan": decisao.updated_remaining_steps}

    def should_continue_plan(state: PlanExecuteState) -> Literal["executor", "__end__"]:
        if state.get("final_response"):          # replanner concluiu
            return "__end__"
        if not state.get("plan"):                # nada mais a executar
            return "__end__"
        if state["rodada"] >= state["max_rodadas"]:  # limite de segurança
            return "__end__"
        return "executor"

    g = StateGraph(PlanExecuteState)
    g.add_node("planner", planner_node)
    g.add_node("executor", executor_node)
    g.add_node("replanner", replanner_node)
    g.add_edge(START, "planner")
    g.add_edge("planner", "executor")
    g.add_edge("executor", "replanner")
    g.add_conditional_edges("replanner", should_continue_plan)
    return g.compile()


# 5) Execução com registro
def executar(graph, objetivo, max_rodadas, titulo):
    print(f"\n{'=' * 70}\n{titulo}\nPedido: {objetivo}\nLimite: {max_rodadas} rodadas")
    entrada = {"objective": objetivo, "plan": [], "past_steps": [], "final_response": "",
               "rodada": 0, "max_rodadas": max_rodadas}
    registro = {"plano": [], "tamanhos_past_steps": [], "estado": None}
    for modo, dado in graph.stream(entrada, stream_mode=["updates", "values"]):
        if modo == "values":  # estado completo após cada passo
            registro["estado"] = dado
            tam = len(dado["past_steps"])
            if not registro["tamanhos_past_steps"] or registro["tamanhos_past_steps"][-1] != tam:
                registro["tamanhos_past_steps"].append(tam)
            continue
        no, upd = next(iter(dado.items()))
        if no == "planner":
            registro["plano"] = upd["plan"]
            print(f"\n[PLANNER] Plano com {len(upd['plan'])} etapas:")
            for i, etapa in enumerate(upd["plan"], 1):
                print(f"   {i}. {etapa}")
        elif no == "executor":
            etapa, resultado = upd["past_steps"][0]
            print(f"\n---> [EXECUTOR] Rodada {upd['rodada']} | Etapa: {etapa}\n     Resultado: {resultado}")
        elif no == "replanner":
            if upd.get("final_response"):
                print(f"     [REPLANNER] Concluído -> {upd['final_response']}")
            else:
                print(f"     [REPLANNER] Faltam {len(upd['plan'])} etapa(s): {upd['plan']}")
    estado = registro["estado"]
    print(f"\n     Tamanho de past_steps ao longo da execução: {registro['tamanhos_past_steps']}")
    if not estado["final_response"]:
        print(f"\n     [PARADA] Limite de {max_rodadas} rodada(s) atingido sem resposta final.")
    return registro, estado


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    real = "--real" in sys.argv
    print("Modo:", "REAL (gpt-4o-mini)" if real else "SIMULADO (roteiros fixos; não é planejamento de LLM)")
    graph = montar_grafo(*criar_modelos(real))
    print("\nGrafo (Mermaid):\n" + graph.get_graph().draw_mermaid())

    r1, e1 = executar(graph, PEDIDO, 6, "EXECUÇÃO 1 · pedido normal")
    r2, e2 = executar(graph, PEDIDO_SKU_INEXISTENTE, 6, "EXECUÇÃO 2 · SKU inexistente (VL-99)")
    r3, e3 = executar(graph, PEDIDO, 1, "EXECUÇÃO 3 · limite de 1 rodada")

    resp1, resp2 = e1["final_response"], e2["final_response"]
    verificacoes = [
        ("Plano tem 3 ou 4 etapas", 3 <= len(r1["plano"]) <= 4),
        ("past_steps cresce 1 tupla por rodada (0, 1, 2, ...)",
         r1["tamanhos_past_steps"] == list(range(e1["rodada"] + 1))),
        ("Resposta 1 traz o total R$ 164,00", bool(re.search(r"164[,.]00", resp1))),
        ("Total veio de uma etapa executada (164 em past_steps)",
         any("164" in r for _, r in e1["past_steps"])),
        ("VL-99: resposta diz que não há o item",
         "VL-99" in resp2 and bool(re.search(r"n[ãa]o (h[áa]|existe|encontr|consta|est[áa] dispon)", resp2, re.I))),
        ("VL-99: não inventa estoque (nenhum 'N unidades')",
         not re.search(r"\d+\s+unidades", resp2)),
        ("Execuções 1 e 2 dentro do limite (6)", e1["rodada"] <= 6 and e2["rodada"] <= 6),
        ("Limite 1: parou com exatamente 1 rodada", e3["rodada"] == 1),
    ]
    print(f"\n{'=' * 70}\nRodadas: exec1={e1['rodada']} | exec2={e2['rodada']} | exec3={e3['rodada']}")
    print("Conta manual: 4 x 32,50 + (25 + 2 x 4,5) = 130,00 + 34,00 = R$ 164,00")
    print("\nVerificações:")
    for nome, ok in verificacoes:
        print(f"  [{'OK' if ok else 'FALHOU'}] {nome}")
    if not real:
        print("\nLimite: planner, executor e replanner SIMULADOS; testam ligações, estado e paradas,"
              " não o planejamento real de uma LLM.")
    sys.exit(0 if all(ok for _, ok in verificacoes) else 1)


if __name__ == "__main__":
    main()
