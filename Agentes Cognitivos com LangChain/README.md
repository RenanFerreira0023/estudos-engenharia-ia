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
| 04-11 | Chat do veículo | Streamlit/session_state/chat_input/chat_message, create_agent/invoke com histórico, callbacks reais, Nova conversa, AppTest e limites de memória de sessão. |
| Projeto final — fase 1 | Auto Super Parts CWB | PromptTemplate/ChatPromptTemplate, BaseModel, PydanticOutputParser, composições @chain/LCEL, invoke/batch e notebook importando módulos .py. |
| Projeto final — fase 2 | Auto Super Parts CWB | create_agent/@tool, SQLite parametrizado, ViaCEP real, cálculo em centavos/Decimal, argumentos validados, modo estrito e auditoria de chamadas/retornos. |
| Projeto final — fase 3 | Auto Super Parts CWB | Janela de histórico, perfil confirmado em SQLite, resumos vetoriais por cliente e exclusão. |
| Projeto final — fase 4 | Auto Super Parts CWB | Índice FAISS existente, recuperação com fontes, decomposição de consulta, text-to-query restrito e rastro SQL. |
| Projeto final — fase 5 | Auto Super Parts CWB | Regras financeiras, juiz LLM de três classes, um reparo reavaliado e resposta final persistida; adaptação documentada à verificação por inferência. |

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
  - [Chat que lembra o veículo na sessão](./aula%2004-11/Chat%20que%20lembra%20o%20veiculo%20na%20sessao/)

## Projeto final

- [Auto Super Parts CWB — fases 1 a 5](./Projeto%20final/)
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

## Revisão da fase 2 do projeto final — 08/11

Consulta de frete sem itens, fonte técnica estruturada, proteção de tipo de peça por pedido
(`ContextVar`) e regras de resposta para óleo/correia. A regra de frete é compartilhada
com o cálculo do orçamento; candidata e resposta entregue ficam separadas na evidência.
Não representa implementação de RAG ou de um verificador semântico geral.
Consulte o [registro da revisão](./Projeto%20final/04_avaliacao_e_evidencias/resultados/CORRECOES_08_11.md).

### Prova AutoTools do projeto final — 08/11

Cliente HTTP com validação de Content-Type/JSON e tratamento de falhas; busca externa comparada com a configuração local e o mercado, sem inferir aplicação. As consultas reais não confirmaram cobertura dos quatro veículos. AutoTools permanece fora das ferramentas do agente; ViaCEP continua funcional. Veja a [evidência e os limites](./Projeto%20final/04_avaliacao_e_evidencias/resultados/PROVA_AUTOTOOLS_08_11.md).

### Base técnica manual do projeto final — 08/11

[Escopo, fontes e execução](./Projeto%20final/01_documentacao/BASE_TECNICA_MANUAL.md): consulta estruturada em JSON por configuração/assunto, com fontes e lacunas explícitas. Cinco veículos (quatro originais e uma S10 diesel), mantendo 24 produtos comerciais. Óleo diferencia norma e uso normal/severo; ViaCEP continua como API externa. Catálogos externos deixam o caminho ativo; memória, RAG e avaliação continuam na sequência planejada.

### Memória do projeto final — fase 3

[Guia e evidências](./Projeto%20final/01_documentacao/MEMORIA_FASE_03.md): janela de turnos realmente enviada a `invoke`, perfil confirmado em SQLite e recuperação vetorial de resumos autorizados, isolados por cliente. Nova conversa preserva dados salvos; esquecer apaga contexto curto/longo. CLI e notebook importam a mesma fachada do agente; sem autenticação ou resumo automático. Comparação documental LangMem/Mem0 e decisão por store local.

### RAG e text-to-query do projeto final — fase 4

[Guia, execução e evidências](./Projeto%20final/01_documentacao/RAG_FASE_04.md): políticas em índice FAISS preparado separadamente, reescrita/decomposição de consultas por LCEL/saída estruturada e resposta do agente com fontes. Pergunta de catálogo vira plano Pydantic e SELECT compilado com filtros permitidos; sem SQL livre. Memória permanece integrada. Comparação real antes/depois, falhas de trajetória/avaliação preservadas e notebook com fixtures identificadas.

### Projeto final — fase 5

[Verificação antes de responder](./Projeto%20final/01_documentacao/VERIFICACAO_FASE_05.md): checagens determinísticas, juiz LLM de três classes, cobertura/coerência, um reparo e reavaliação. [Notebook](./Projeto%20final/03_notebooks/fase_05_verificacao.ipynb). Não equivale automaticamente a classificador NLI; fontes e falhas do avaliador permanecem auditáveis.

## Projeto atual — Secretária IA

[Projeto final 2](./Projeto%20final%202/) substitui autopeças como direção da entrega acadêmica. Já há importação TXT/ZIP, extração de propostas, revisão persistente, visitas com agente, cadastro PJ por confirmação, projetos/anotações com mensagens-fonte e memória curta por sessão no SQLite. Prompt PTCF, rota leve e callbacks locais integram o menu 9; 103 testes locais passaram. Financeiro operacional, RAG, relatórios e avaliação final ainda estão pendentes. Conceitos previstos e matriz dos 29 itens estão no [plano](./Projeto%20final%202/PLANO_PROJETO_SECRETARIA_IA.md).

[Orquestração da fase 2](./Projeto%20final%202/docs/fase2_orquestracao.md) · [notebook 05b](./Projeto%20final%202/notebooks/05b_orquestracao_agente.ipynb): `create_agent`, PTCF/few-shot, rota com `RunnableLambda` e callback de eventos; fixture local não é chamada real de LLM. [Memória da fase 3](./Projeto%20final%202/notebooks/06_memoria_conversacional.ipynb): turnos SQLite, janela curta e retomada após reinício observada manualmente.

As fases e conceitos de autopeças listados acima são histórico de um projeto descontinuado. Seus testes não validam a nova aplicação.

### Projeto final 2 — marco 1

[Notebook de importação e SQLite](./Projeto%20final%202/notebooks/01_importacao_sqlite.ipynb):
parser determinístico, fontes por linha, transações e idempotência por arquivo/mensagem/ocorrência.
[Como executar](./Projeto%20final%202/README.md). Não há LLM ou FAISS neste marco; importação não é extração semântica.


### Projeto final 2 — primeira chain de propostas

[Notebook 02](./Projeto%20final%202/notebooks/02_extracao_estruturada.ipynb):
ChatPromptTemplate, PydanticOutputParser, LCEL/@chain, invoke/batch/stream de objeto completo,
fontes e cobertura por lote. Modos fixture e OpenAI separados; ainda sem agente ou gravação operacional.
[Contratos e limites](./Projeto%20final%202/docs/primeira_chain.md).


### Projeto final 2 — revisão persistente (início da fase 2)

[Serviço e roteiro](./Projeto%20final%202/docs/revisao_persistente.md) · [Notebook 03](./Projeto%20final%202/notebooks/03_revisao_persistente.ipynb). SQLite v2 mantém fila, versão, autoria e histórico de decisões; confirmação da interpretação é separada da gravação operacional. Testes incluem rejeição, correção, isolamento e concorrência por versão. 72 testes locais; seis células executadas sem API. Agente/ferramentas/APIs permanecem pendentes.
