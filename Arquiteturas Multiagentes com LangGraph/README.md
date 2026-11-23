# Arquiteturas Multiagentes com LangGraph

Estudos e exercícios da disciplina de grafos com LangGraph. O [guia principal](../README.md#guia-de-estudo-por-exercício)
explica os conceitos e o fluxo de cada exercício.

## Mapa dos conceitos

| Aula | Exercício | O que estamos estudando |
| --- | --- | --- |
| 16-11 | [A recepção lembra de cada conversa](./aula%2016-11/Desafio%201%20-%20A%20recepcao%20lembra%20de%20cada%20conversa/) | TypedDict/Annotated com add_messages, StateGraph com um nó entre START e END, MemorySaver/thread_id, get_state/update_state e limite da memória em RAM. |
| 16-11 | [A secretária consulta o manual certo](./aula%2016-11/Desafio%202%20-%20A%20secretaria%20consulta%20o%20manual%20certo/) | input_schema/output_schema, RouteDecision com Literal e with_structured_output, duas InMemoryVectorStore, add_conditional_edges, stream da rota e rejeição de rótulo inválido. |
| 18-11 | [O balcão consulta o catálogo antes de pensar](./aula%2018-11/Desafio%201%20-%20O%20balcao%20consulta%20o%20catalogo%20antes%20de%20pensar/) | @tool com docstring, bind_tools, ToolNode/tools_condition, laço ReAct, nó first_model com AIMessage/ToolCall/uuid4, stream com perf_counter e comparação de chamadas e tempo. |
| 18-11 | [Orçamento em etapas com replanejamento](./aula%2018-11/Desafio%202%20-%20Orcamento%20em%20etapas%20com%20replanejamento/) | Plan-and-Execute: PlanSchema/ReplanDecision com with_structured_output, subgrafo ReAct como executor, past_steps com operator.add, limite de rodadas e parada segura com SKU inexistente. |
