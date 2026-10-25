# Agentes Cognitivos com LangChain

Estudos e exercícios da disciplina, desde chamadas a LLMs e chains até agentes
com ferramentas e memória. O [guia principal](../README.md#guia-de-estudo-por-exercício)
explica os conceitos e o fluxo de cada projeto.

## Mapa dos conceitos

| Aula | Exercício | O que estamos estudando |
| --- | --- | --- |
| 06-10 | Assistente de oficina | LLM com ChatOpenAI, contexto fixo, prompt com system/human, variáveis, chain em LCEL, invoke e .content. |
| 06-10 | Suporte em lote | Extração estruturada com BaseModel/Field e with_structured_output; batch e leitura de objetos. |
| 14-10 | Reclamações em ações | Chains de resumo, análise e consolidação; StrOutputParser, lambdas, batch, validação de resumos e IDs de apoio. |
| 14-10 | Encaminhar pedidos | Classificação por LLM, RunnablePassthrough, RunnableLambda e roteamento validado entre chains. |
| 19-10 | Classificar feedbacks | Few-shot, esquema Pydantic, parsers, validação, tratamento de erro e uma tentativa de reparo. |
| 19-10 | Consultar regras | Embeddings, FAISS, busca por similaridade, metadados, agente com @tool, RAG e callbacks. |
| 21-10 | Preferências entre conversas | Agente com ferramentas, MemorySaver/thread_id, store por usuário, namespace, upsert, exclusão e auditoria. |
| 21-10 | Avaliação simulada | Intenções com Literal, extração estruturada, estado por sessão em Python, correções e campos faltantes. |

## Aulas

- [Aula 06-10](./aula%2006-10/)
  - [Assistente de oficina](./aula%2006-10/assistente%20oficina/)
  - [Organizar solicitacoes de suporte em lote](./aula%2006-10/organizar%20solicitacoes%20suporte%20em%20lote/)

- [Aula 14-10](./aula%2014-10/)
  - [Transformar reclamações de uma oficina em ações](./aula%2014-10/Transformar%20reclama%C3%A7%C3%B5es%20de%20uma%20oficina%20em%20a%C3%A7%C3%B5es/)

  - [Encaminhar pedidos para o atendimento certo](./aula%2014-10/Encaminhar%20pedidos%20para%20o%20atendimento%20certo/)

- [Aula 19-10](./aula%2019-10/)
  - [Classificar feedbacks e validar a ficha](./aula%2019-10/Classificar%20feedbacks%20e%20validar%20a%20ficha/)
  - [Consultar regras de uma loja e registrar a busca](./aula%2019-10/Consultar%20regras%20de%20uma%20loja%20e%20registrar%20a%20busca/)

- [Aula 21-10](./aula%2021-10/)
  - [Preferências da oficina entre conversas](./aula%2021-10/Preferencias%20da%20oficina%20entre%20conversas/)
  - [Agendar uma avaliação sem perder o contexto](./aula%2021-10/Agendar%20uma%20avaliacao%20sem%20perder%20o%20contexto/)

## Padrao de organizacao

Cada aula deve ficar em uma pasta propria, com:

- `README.md`: explicacao do exercicio e dos conceitos estudados.
- Arquivos `.py`: codigos da aula ou exercicio.

O `.env` e unico e fica na raiz do repositorio, compartilhado por todos os
exercicios. Variaveis ja definidas no ambiente tem prioridade.

Arquivos `.env` nao devem ser enviados para o GitHub.
