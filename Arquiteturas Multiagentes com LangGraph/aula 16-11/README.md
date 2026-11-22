# Aula 16-11 — Primeiro grafo, checkpoints, estado e router

Material: [apostila da aula](./apostila_langgraph_aula_01%20(1).html).

## Exercícios

- [Desafio 1 · A recepção lembra de cada conversa](./Desafio%201%20-%20A%20recepcao%20lembra%20de%20cada%20conversa/):
  chat de oficina em que Ana e Bruno acompanham veículos diferentes. Cada
  `thread_id` guarda o próprio histórico; `update_state` grava um fato só na
  sessão da Ana, sem chamar o modelo. Teste automático e modo `--chat`.

- [Desafio 2 · A secretária consulta o manual certo](./Desafio%202%20-%20A%20secretaria%20consulta%20o%20manual%20certo/):
  router que classifica a pergunta como agenda ou financeiro, consulta só a
  base correspondente e responde com os documentos, registrando a rota com
  `stream`. Rótulo inválido é rejeitado em vez de virar outra rota.

## Conceitos praticados

- **Estado e reducer:** `TypedDict` + `Annotated[list, add_messages]`; o nó
  devolve só a atualização e o reducer acrescenta ao histórico.
- **Checkpoints:** `MemorySaver` + `thread_id` separam conversas no mesmo grafo;
  `get_state` lê o snapshot e `update_state` corrige sem nova resposta.
- **Contratos:** `input_schema`/`output_schema` separam a entrada e a saída
  públicas do estado interno.
- **Router:** `RouteDecision` (`Literal`) + `with_structured_output` classifica;
  `add_conditional_edges` escolhe o nó; `InMemoryVectorStore` guarda cada base.

**Fluxos:**

- Desafio 1: `START → atendimento → END`, com histórico por thread.
- Desafio 2: `START → classificar → (buscar_agenda | buscar_financeiro) → responder → END`.

Os dois rodam em modo simulado por padrão (sem API) e aceitam `--real`
(OpenAI, `.env` da raiz). Comandos e evidências estão no README de cada desafio.
