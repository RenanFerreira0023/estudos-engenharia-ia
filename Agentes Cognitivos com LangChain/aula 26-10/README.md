# Aula 26-10

Prática de agente com consulta SQL e cálculo determinístico, usando somente
catálogo fictício e registrando a origem dos dados para conferência.

- [Conferir estoque e calcular um orçamento](./Conferir%20estoque%20e%20calcular%20um%20orcamento/)

## O que estudar

| Exercício | Conceitos e aplicação |
| --- | --- |
| Estoque e orçamento | sqlite3 mantém produtos; o esquema no prompt orienta SQL; create_agent usa duas ferramentas @tool; Python calcula em centavos; logs e testes conferem consulta, origem do preço, estoque e total. |

O `.env` é compartilhado na raiz. O banco fica em memória; os logs JSONL ficam
localmente na pasta do exercício, ignorados pelo Git.
