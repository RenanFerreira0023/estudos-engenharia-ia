# Aula 26-10

Prática de agente com consulta SQL e cálculo determinístico, usando somente
catálogo fictício e registrando a origem dos dados para conferência.
Também inclui busca vetorial de políticas, reescrita de consultas e respostas
fundamentadas em trechos, sem inventar benefícios ausentes.

- [Conferir estoque e calcular um orçamento](./Conferir%20estoque%20e%20calcular%20um%20orcamento/)
- [Buscar uma regra sem inventar um benefício](./Buscar%20uma%20regra%20sem%20inventar%20um%20beneficio/)

## O que estudar

| Exercício | Conceitos e aplicação |
| --- | --- |
| Estoque e orçamento | sqlite3 mantém produtos; o esquema no prompt orienta SQL; create_agent usa duas ferramentas @tool; Python calcula em centavos; logs e testes conferem consulta, origem do preço, estoque e total. |
| Busca de políticas | Document preserva fontes; OpenAIEmbeddings/FAISS indexam o corpus; o agente reescreve queries e usa @tool com filtro opcional; scores, trechos e comparação original/reescrita tornam a recuperação auditável. |

O `.env` é compartilhado na raiz. O banco fica em memória; os logs JSONL ficam
localmente na pasta do exercício, ignorados pelo Git.
