# Aula 18-11 — ReAct, First Model e Plan-and-Execute

Material: [apostila da aula](./apostila_langgraph_aula_02.html).

## Exercícios

- [Desafio 1 · O balcão consulta o catálogo antes de pensar](./Desafio%201%20-%20O%20balcao%20consulta%20o%20catalogo%20antes%20de%20pensar/):
  compara o ReAct padrão com o First Model, que dispara `buscar_catalogo` sem
  chamar a LLM. Registra passos e tempos com `stream` + `perf_counter`; a conta
  (2 × R$ 189,90) sai da `calculator`.

- [Desafio 2 · Orçamento em etapas com replanejamento](./Desafio%202%20-%20Orcamento%20em%20etapas%20com%20replanejamento/):
  Plan-and-Execute com planner, executor (subgrafo ReAct) e replanner para
  estoque, frete e total (R$ 164,00). Limite de rodadas no estado; SKU
  inexistente encerra sem inventar estoque.

## Conceitos praticados

- **Ferramentas:** `@tool` com docstring (o schema que o modelo lê);
  `bind_tools` liga as ferramentas ao modelo.
- **Laço ReAct:** `model_node` + `ToolNode` + `tools_condition`, com a volta
  fixa `tools → model`.
- **First Model:** nó Python que monta `AIMessage` com `ToolCall` (id `uuid4`)
  e vai direto para `tools`, sem LLM.
- **Plan-and-Execute:** `PlanSchema`/`ReplanDecision` com `with_structured_output`;
  `past_steps` com `operator.add`; aresta condicional que volta ao executor ou
  encerra (resposta, plano vazio ou limite de rodadas).

**Fluxos:**

- ReAct: `START → model ⇄ tools → END`.
- First Model: `START → first_model → tools ⇄ model → END`.
- Plan-and-Execute: `START → planner → executor → replanner → (executor | END)`.
