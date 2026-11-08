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
| 26-10 | Estoque e orçamento | SQLite, esquema SQL no prompt, agente com ferramentas de consulta e cálculo, centavos inteiros e auditoria da origem do preço. |
| 26-10 | Busca de políticas | Document/metadados, embeddings e FAISS, reescrita pelo agente, similarity_search_with_score, filtro opcional e comparação de queries sem limiar universal. |
| 28-10 | Atendimento com duas fontes e memória | SQLDatabaseToolkit, retriever documental, create_agent, MemorySaver/thread_id e recorte da trajetória após a última HumanMessage. |
| 28-10 | Auditor de frete | Extração estruturada de afirmações, comparação Python com Decimal/tolerância, avaliação lógica fundamentada e relatórios separados. |
| 04-11 | Atendente e política | Três casos isolados, @tool/create_agent, mensagens AI/Tool, comparador exato, LLM juiz, fixture adversarial, revisão humana e Client/evaluate opcionais. |
| Projeto final — fase 1 | Auto Super Parts CWB | PromptTemplate/ChatPromptTemplate, BaseModel, PydanticOutputParser, composições @chain/LCEL, invoke/batch e notebook importando módulos .py. |
| Projeto final — fase 2 | Auto Super Parts CWB | create_agent/@tool, SQLite parametrizado, ViaCEP real, cálculo em centavos/Decimal, argumentos validados, modo estrito e auditoria de chamadas/retornos. |

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

- [Aula 26-10](./aula%2026-10/)
  - [Conferir estoque e calcular um orçamento](./aula%2026-10/Conferir%20estoque%20e%20calcular%20um%20orcamento/)
  - [Buscar uma regra sem inventar um benefício](./aula%2026-10/Buscar%20uma%20regra%20sem%20inventar%20um%20beneficio/)

- [Aula 28-10](./aula%2028-10/)
  - [Atendimento com duas fontes e memória](./aula%2028-10/Atendimento%20com%20duas%20fontes%20e%20memoria/)
  - [Auditor de frete para um orçamento](./aula%2028-10/Auditor%20de%20frete%20para%20um%20orcamento/)

- [Aula 04-11](./aula%2004-11/)
  - [O atendente consultou a política?](./aula%2004-11/O%20atendente%20consultou%20a%20politica/)

## Projeto final

- [Auto Super Parts CWB — fases 1 e 2](./Projeto%20final/)
  - [Fase 1: chain inicial](./Projeto%20final/03_notebooks/fase_01_chain_inicial.ipynb)
  - [Fase 2: agente, ferramentas e ViaCEP](./Projeto%20final/03_notebooks/fase_02_agente_ferramentas.ipynb)
  - Na fase 2 o agente escolhe fontes; Python calcula valores e logs mostram a trajetória. Cada mensagem é independente; memória e RAG ficam para fases seguintes.

## Padrao de organizacao

Cada aula deve ficar em uma pasta propria, com:

- `README.md`: explicacao do exercicio e dos conceitos estudados.
- Arquivos `.py`: codigos da aula ou exercicio.

Nas aulas, o `.env` compartilhado fica na raiz do repositorio. O Projeto final
e independente: prioriza o ambiente e aceita um `.env` local em sua propria
pasta, conforme seu README. Ele nao procura a configuracao das demais aulas.

Arquivos `.env` nao devem ser enviados para o GitHub.
