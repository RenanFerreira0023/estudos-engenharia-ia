# Matriz de requisitos — estado na entrega (12/11/2026)

Cada item da rubrica aparece com o estado e a evidência que o comprova. **Adaptado** significa que o conceito foi implementado com a API atual do LangChain, e não com a classe antiga citada no enunciado. Na aula 08 (04/11/2026, 00:12–00:17), o professor orientou explicitamente que funções antigas não são exigidas e que se deve justificar a escolha e mostrar o conceito funcionando; a [revisão do enunciado](revisao_enunciado_aula08.md) registra essa orientação.

Legenda: ✅ atendido · ✅ adaptado · ⚠️ atendido com limite declarado.

Notebooks de entrega: [fase 1](../notebooks/fase1_chain_extracao.ipynb) · [fase 2](../notebooks/fase2_agente_ferramentas.ipynb) · [fase 3](../notebooks/fase3_memoria.ipynb) · [fase 4](../notebooks/fase4_rag_consulta.ipynb) · [fase 5](../notebooks/fase5_financeiro_verificacao_avaliacao.ipynb). Todos executam sem chave de API, com dados fictícios.

| ID | Item da rubrica (resumido) | Estado | Como foi atendido | Evidência |
| --- | --- | --- | --- | --- |
| R01 | Anatomia, arquitetura cognitiva, tipo e maturidade do agente | ✅ | Arquitetura **híbrida**: o modelo decide caminhos e ferramentas; regras em Python controlam parsing, dinheiro, datas e gravações. Evolução de chain de extração (fase 1) para agente integrador com ferramentas, memória, RAG e avaliação (fase 5). | [Plano §8](../PLANO_PROJETO_SECRETARIA_IA.md), [decisões](decisoes.md) |
| R02 | Arquitetura de planejamento e memória aumentada | ✅ | Fluxo análise → consulta → **proposta** → **confirmação humana** → atualização. Memória curta (janela) + longa (SQLite, recortes, FAISS, preferências). | [Plano §4 e §10](../PLANO_PROJETO_SECRETARIA_IA.md), [memória](memoria_fase3.md), notebooks fase 2 e 3 |
| R03 | Templates com `ChatPromptTemplate` | ✅ | Prompt de extração com `ChatPromptTemplate`. | Notebook fase 1, `src/secretaria/chain_extracao.py` |
| R04 | Output parser com saída JSON | ✅ | `PydanticOutputParser`; saída inválida vira falha explícita do lote. | Notebook fase 1, [primeira chain](primeira_chain.md), [execuções reais](../evidencias/marco2_api_real_20261110T021400551051Z.json) |
| R05 | Runnable (`invoke`, `batch`, `stream`) e `@chain` | ⚠️ | `invoke`, `batch` e `@chain` demonstrados; `stream` emite objeto completo, não tokens (justificado: saída estruturada só vale validada). | Notebook fase 1 |
| R06 | LCEL e justificativa imperativo × declarativo | ✅ | `prompt \| modelo \| parser` em LCEL e versão equivalente com `@chain`; comparação documentada. | Notebook fase 1, [primeira chain](primeira_chain.md) |
| R07 | Comparar orquestradores e justificar LangChain | ✅ | Chain fixa × `create_agent` × grafo LangGraph explícito, por critérios. | [Orquestração](fase2_orquestracao.md) |
| R08 | Agente com ferramentas e memória, padrão ReAct (`initialize_agent`) | ✅ adaptado | `create_agent` executa o ciclo ReAct (modelo → ferramenta → observação → modelo) com 11 ferramentas e histórico persistido. | Notebook fase 2, [trace no LangSmith](avaliacao_resultados.md), [visita real](../evidencias/fase5_streamlit_visita_reteste_manual.json) |
| R09 | Chains sequenciais/paralelas e roteamento (`RouterChain`) | ✅ adaptado | Extração em lotes sequenciais com `batch`; `roteador_pedido` (`RunnableLambda`) classifica visita/cliente/projeto/geral antes do agente. | Notebook fase 2, [rota e callback](../evidencias/fase2_roteamento_callback_manual.json) |
| R10 | API externa como ferramenta via function calling | ✅ | ViaCEP e Minha Receita são ferramentas do agente. | [CNPJ novo](../evidencias/fase2_cnpj_novo_agente_manual.json), [CEP](../evidencias/fase2_visita_cep_idempotencia_manual.json) |
| R11 | Prompt PTCF, few-shot e chain-of-thought | ⚠️ | PTCF e exemplos few-shot versionados em `montar_prompt_agenda`. Em vez de pedir raciocínio oculto, a trajetória é observável (ferramentas, rota, eventos), como orientado na aula 08. | Notebook fase 2, `src/secretaria/agente_agenda.py` |
| R12 | Confiabilidade: parser com erros, memória, FAISS e callbacks | ✅ | Parser com falha explícita; memória SQLite; FAISS em fontes e em recortes de memória; callback `RastroAgente` registra modelo/ferramentas sem conteúdo privado. | Notebooks fase 1, 3 e 4, `src/secretaria/observabilidade.py` |
| R13 | Memória curta × longa (CoALA) | ✅ | Janela (curta), episódica (recortes), semântica (registros), procedural (regras do prompt) e preferências confirmadas. | [Memória](memoria_fase3.md), notebook fase 3 |
| R14 | Janela de contexto + sumarização + busca vetorial | ⚠️ | Janela de 6 turnos; turnos antigos viram recortes; FAISS com embeddings escolhe os relevantes, após filtrar usuário e sessão. Limite: filtro contra recuperação irrelevante sem reteste real. | Notebook fase 3, [reteste FAISS](../evidencias/fase3_faiss_reteste_manual.json) |
| R15 | Comparar ferramentas de memória | ✅ | LangMem × Mem0, com justificativa para SQLite. | [Memória](memoria_fase3.md) |
| R16 | Chatbot com `ConversationBufferMemory` | ✅ adaptado | Buffer equivalente em SQLite alimenta `create_agent.invoke`; retomada após reiniciar observada. | [Memória](memoria_fase3.md), [execuções e falhas](execucoes_e_falhas.md) (teste de 11/11) |
| R17 | Reconhecimento de intenção e extração de entidades | ✅ | Intenção: roteador da conversa. Entidades: chain extrai projeto, valores, datas e tipo de ato, com fonte. | Notebooks fase 1 e 2 |
| R18 | Conversa real com contexto e decomposição multi-turno | ✅ | "e o saldo dele?" resolvido para o projeto Beta após troca de referente; retomada de "qual cliente mencionei?" após reinício; pedido composto de visita decomposto em `buscar_cliente → consultar_disponibilidade → propor_visita`. | [Troca de projeto](../evidencias/fase3_troca_projeto_reteste_manual.json), [visita no Streamlit](../evidencias/fase5_streamlit_visita_reteste_manual.json) |
| R19 | Ferramentas hardcoded × semânticas | ✅ | Parsing, cálculos, SQL e APIs determinísticos; interpretação, RAG e escolha de ferramenta pelo modelo. | [Orquestração](fase2_orquestracao.md) |
| R20 | APIs internas/externas conforme o uso | ✅ | Interna: SQLite (agenda, clientes, financeiro, mensagens). Externas: ViaCEP, Minha Receita, OpenAI (embeddings). Timeout e validação em cada uma. | `src/secretaria/agenda.py`, evidências da fase 2 |
| R21 | Text-to-query | ✅ | Plano tipado gerado pelo modelo; Python valida e executa `SELECT` parametrizado. | Notebook fase 4, [reteste real](../evidencias/fase4_text_to_query_reteste_manual.json), [guia](consulta_estruturada_fase4.md) |
| R22 | Agente de recuperação com índice FAISS existente | ✅ | Índice preparado uma vez e carregado na busca; fonte citada com ID. Caso "fonte" passou 4/4 na avaliação. | Notebook fase 4, [falha e reteste](../evidencias/fase4_falha_busca_fonte_manual.json), [avaliação](avaliacao_resultados.md) |
| R23 | Diagnóstico de falha real de recuperação | ✅ | Mensagem interrogativa ranqueada acima da explicativa (Gama); reordenação condicional com antes/depois. | Notebook fase 4, [evidência](../evidencias/fase4_falha_ranking_gama.json) |
| R24 | Verificação factual e de coerência | ⚠️ | Regras para contagens e valores; juiz LLM com uma tentativa de reparo; resposta segura se falhar. Observado em uso real ("corrigida"). Limite: aprovou uma resposta com comando inexistente. | Notebook fase 5, [execuções e falhas](execucoes_e_falhas.md) |
| R25 | Agente único com RAG, SQL e API | ✅ | O mesmo agente usa consulta estruturada (SQL), RAG de fontes, APIs externas e financeiro. | [Avaliação](avaliacao_resultados.md), [visita real](../evidencias/fase5_streamlit_visita_reteste_manual.json) |
| R26 | Executor com `create_openai_tools_agent` e `AgentExecutor` | ✅ adaptado | `create_agent` (sucessor atual) com function calling da OpenAI; equivalência documentada. | [Revisão do enunciado](revisao_enunciado_aula08.md), `src/secretaria/agente_agenda.py` |
| R27 | Histórico com `RunnableWithMessageHistory` | ✅ adaptado | Histórico por usuário e sessão carregado do SQLite e passado em `messages` ao `invoke`, padrão mostrado pelo professor na aula 08. | `src/secretaria/atendimento_web.py`, notebook fase 3 |
| R28 | Agente integrado ao Streamlit | ✅ | `app.py` com abas Conversa, Fontes, Revisão, Agenda e Financeiro, mesmo agente e mesmo SQLite; fluxo de visita testado na tela com correções. | [Visita no Streamlit](../evidencias/fase5_streamlit_visita_reteste_manual.json), [execuções e falhas](execucoes_e_falhas.md) |
| R29 | Avaliação de respostas e trajetória com LangSmith | ✅ | 4 execuções reais: resposta 16/16, trajetória exata 12/16; teste do juiz mostrou falso positivo contido pela regra de composição. | [Avaliação e análise](avaliacao_resultados.md), `evidencias/fase5_avaliacao_api_langsmith_execucao1.json` a `4` |

## Limites gerais

- Usuários de demonstração (ana, bruno, carla) testam permissões; **não há autenticação**.
- A avaliação usa 4 casos fictícios de um turno. Fluxos de memória, propostas e financeiro foram comprovados por testes automatizados, notebooks e testes manuais, não pelo dataset.
- O financeiro foi testado manualmente pela interface em 12/11/2026 (orçamento, pagamento informado, confirmação, estorno e permissão negada a carla): [evidência](../evidencias/fase5_financeiro_streamlit_manual.json).
- Verificação "aprovada" não prova que a resposta está certa (ver R24).

Histórico do desenvolvimento: [andamento das fases](andamento_fases.md), [execuções e falhas](execucoes_e_falhas.md).
