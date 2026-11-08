# Aula 04-11 — Avaliação de resposta e trajetória

Material: [apostila da aula](./apostila_agentes_cognitivos_aula_08.html).

## Exercício

- [O atendente consultou a política?](./O%20atendente%20consultou%20a%20politica/):
  avaliar separadamente resposta sobre pagamento e uso efetivo da ferramenta.
  Três casos independentes, comparador exato, LLM juiz com critérios explícitos,
  fixture adversarial e tabela com revisão humana.

## Conceitos praticados

`@tool` fornece uma política fictícia; `create_agent`/`invoke` processam perguntas
isoladas; mensagens AI/Tool registram chamadas e retornos. Python compara listas;
o LLM juiz avalia significado com saída estruturada. `Client` e `evaluate` permitem
cadastrar o conjunto e publicar resultados reais opcionalmente no LangSmith.

**Fluxo:** casos → execução isolada → resposta/consulta → notas separadas → revisão.

Consulte o README do exercício para comandos. O `.env` compartilhado é o da raiz.
Fixtures locais não são execuções reais do agente nem métricas de LangSmith.
