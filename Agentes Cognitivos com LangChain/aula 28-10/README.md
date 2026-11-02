# Aula 28-10

Integração de duas fontes com memória de conversa e conferência da trajetória
de cada turno.
Também inclui auditoria numérica e lógica de orçamento e frete com referência independente.

- [Atendimento com duas fontes e memória](./Atendimento%20com%20duas%20fontes%20e%20memoria/)
- [Auditor de frete para um orçamento](./Auditor%20de%20frete%20para%20um%20orcamento/)

## O que estudar

| Exercício | Conceitos e aplicação |
| --- | --- |
| Atendimento com duas fontes e memória | SQLite/SQLDatabaseToolkit fornecem dados de produtos; Document/FAISS/create_retriever_tool fornecem a política; create_agent integra as fontes e MemorySaver/thread_id preservam a conversa. HumanMessage delimita as chamadas e os retornos do turno atual. |
| Auditor de frete | BaseModel/Field/Literal e with_structured_output extraem e avaliam afirmações; Python/Decimal comparam métricas equivalentes e tolerâncias; a lógica usa regra e referência independentes, mantendo ausência de cobertura explícita. |

Use o `.env` compartilhado da raiz. Os dados são fictícios; banco, índice e
histórico existem somente durante o processo. A auditoria JSONL fica localmente
na pasta do exercício, ignorada pelo Git.
