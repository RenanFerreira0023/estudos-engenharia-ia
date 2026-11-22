# Aula 16-11 — Primeiro grafo, checkpoints e estado

Material: [apostila da aula](./apostila_langgraph_aula_01%20(1).html).

## Exercícios

- [Desafio 1 · A recepção lembra de cada conversa](./desafio1_recepcao.py):
  chat de oficina em que Ana e Bruno acompanham veículos diferentes. Cada
  `thread_id` guarda o próprio histórico; `update_state` grava um fato só na
  sessão da Ana, sem chamar o modelo. [Desenho do fluxo e registro dos testes](./desafio1_registro.md).

## Conceitos praticados

`TypedDict` + `Annotated[list, add_messages]` definem o estado; o reducer
acrescenta a resposta ao histórico. `StateGraph` liga `START → atendimento → END`.
`MemorySaver` + `thread_id` separam as conversas no mesmo grafo; `get_state`
lê o snapshot e `update_state` corrige o contexto sem nova resposta.

**Fluxo:** mensagem + histórico da thread → nó `atendimento` → resposta nova → histórico.

## Como rodar

Da raiz do repositório, com a `.venv`:

```powershell
.venv\Scripts\python "Arquiteturas Multiagentes com LangGraph\aula 16-11\desafio1_recepcao.py"           # teste automático (8 verificações)
.venv\Scripts\python "Arquiteturas Multiagentes com LangGraph\aula 16-11\desafio1_recepcao.py" --chat    # você conversa
```

No `--chat`: `/sessao NOME`, `/fato TEXTO`, `/estado`, `/sair`.
`--real` usa `gpt-4o-mini` com a `OPENAI_API_KEY` do `.env` da raiz; sem ele,
roda um modelo simulado por regras. O simulado testa a organização do histórico,
não a compreensão de uma LLM. `MemorySaver` fica só na RAM: reiniciar apaga tudo.
