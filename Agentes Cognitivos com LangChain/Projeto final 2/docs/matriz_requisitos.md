# Matriz de requisitos — atualização da fase 2

Importação/SQLite, chain de propostas, revisão persistente e agente de visitas com ferramentas estão implementados. Cadastro PJ por proposta e confirmação humana foi observado manualmente em [evidência](../evidencias/fase2_cadastro_pj_reteste_manual.json). Projetos e anotações com FKs para mensagens-fonte foram implementados com confirmação separada e fixture local no [notebook 05](../notebooks/05_projetos_fontes.ipynb); isso não equivale a ledger financeiro ou fase 2 completa. Não atribuir testes de autopeças à nova aplicação.

| ID | Item da rubrica | Estado |
|---|---|---|
| R01 | O aluno estruturou a anatomia e a arquitetura cognitiva do agente, classificando seu tipo e nível de maturidade agêntica? | Planejado |
| R02 | O aluno projetou uma arquitetura de planejamento e memória aumentada para o agente? | Planejado |
| R03 | O aluno construiu templates de prompt reutilizáveis com PromptTemplate ou ChatPromptTemplate? | Implementado; testes/notebook locais, API testada com resultado parcial. |
| R04 | O aluno implementou um output parser para gerar saída estruturada em JSON a partir da chain? | Implementado; testes/notebook locais, API testada com resultado parcial. |
| R05 | O aluno aplicou a interface Runnable (invoke, batch, stream) e implementou composição imperativa com o decorador @chain? | Demonstrado com fixture: invoke/batch/@chain e stream de objeto completo; não tokens. |
| R06 | O aluno implementou a composição declarativa da chain com LCEL e justificou a escolha entre composição imperativa e declarativa? | Implementado; testes/notebook locais, API testada com resultado parcial. |
| R07 | O aluno comparou orquestradores de agentes autônomos e justificou a escolha do LangChain para o problema? | Parcial: comparação de LCEL, `create_agent` e grafo LangGraph explícito documentada; falta comparação mais ampla se exigida na rubrica. |
| R08 | O aluno construiu um agente com ferramentas e memória e implementou o padrão ReAct com initialize_agent? | Parcial: `create_agent` usa ferramentas, callbacks e janela persistida; há diálogo real com retomada. A implementação literal de `initialize_agent` não foi feita; adaptação documentada. |
| R09 | O aluno construiu chains sequenciais ou paralelas e implementou roteamento dinâmico com RouterChain? | Parcial: `RunnableLambda` classifica cliente/visita/geral antes do agente; não é `RouterChain` literal nem controla acesso/ferramentas. Chains de extração já existem. |
| R10 | O aluno integrou pelo menos uma API externa como ferramenta do agente via function calling? | Implementado: ViaCEP e Minha Receita como ferramentas; chamadas reais e trajetórias manuais registradas. |
| R11 | O aluno estruturou o prompt do agente com o framework PTCF e aplicou few-shot learning e chain-of-thought? | Parcial: prompt PTCF e exemplos few-shot versionados; reteste real de cliente executado. Trajetória observável substitui alegação de acesso ao raciocínio interno. |
| R12 | O aluno implementou os componentes de confiabilidade do agente (output parsers com tratamento de erros, memória configurada na chain, ferramenta de busca semântica com FAISS e callbacks de logging), justificando as escolhas técnicas? | Parcial: parser/erros na extração, memória no agente e callback real com seis eventos observados; FAISS nos recortes de memória testado offline, mas busca semântica nas mensagens com fontes e reteste real ainda pendentes. |
| R13 | O aluno diferenciou memória de curto e longo prazo para o agente com base na taxonomia CoALA? | Parcial: janela, recortes episódicos, registros estruturados, regras procedurais e preferências pessoais confirmadas no SQLite v9 classificados em [memória fase 3](memoria_fase3.md). |
| R14 | O aluno gerenciou janelas de contexto combinando sliding window ou sumarização com busca vetorial? | Parcial: janela de seis turnos, recortes extrativos no SQLite e FAISS com embeddings no menu 9; [notebook 09](../notebooks/09_recuperacao_vetorial_memoria.ipynb) e [reteste real](../evidencias/fase3_faiss_reteste_manual.json) recuperaram Alfa. Filtro posterior para evitar recuperação irrelevante ainda aguarda reteste real. |
| R15 | O aluno comparou ferramentas especializadas de memória por arquitetura e caso de uso? | Documentado: [LangMem e Mem0 comparados](memoria_fase3.md), com justificativa para manter preferências explícitas no SQLite. |
| R16 | O aluno construiu um chatbot conversacional com ConversationBufferMemory? | Adaptado: buffer equivalente em SQLite alimenta `create_agent.invoke` com até seis turnos. [Equivalência e limite da classe legada](memoria_fase3.md) documentados; retestes reais mostraram retomada após reinício e recuperação de Alfa depois da janela. A classe literal não foi usada. |
| R17 | O aluno estruturou fluxos de conversação com reconhecimento de intenção e extração de entidades? | Parcial: propostas por área/natureza/entidades; fluxo conversacional ainda não. |
| R18 | O aluno validou, com evidência de uma conversa real, que o agente manteve contexto e decompôs consultas complexas em diálogos multi-turno? | Planejado |
| R19 | O aluno estruturou ferramentas do agente diferenciando funções hardcoded de funções semânticas? | Documentado: SQLite/regras e APIs são determinísticos; interpretação e escolha de ferramenta são do modelo. Ver [orquestração](fase2_orquestracao.md). |
| R20 | O aluno integrou o agente a APIs internas ou externas conforme o tipo de uso de cada uma? | Parcial: SQLite, ViaCEP e Minha Receita no fluxo de visitas/clientes; outras áreas ainda pendentes. |
| R21 | O aluno implementou o padrão text-to-query para consultar dados estruturados? | Implementado para mensagens importadas com plano tipado e SQL parametrizado; [trajetória real observada](../evidencias/fase4_text_to_query_reteste_manual.json) com `COUNT(*)=1`. [Guia](consulta_estruturada_fase4.md) |
| R22 | O aluno construiu um agente de recuperação usando um índice FAISS existente? | Parcial com evidência real: menu 11 preparou índice separado de 40 mensagens; no [reteste](../evidencias/fase4_falha_busca_fonte_manual.json), o agente chamou `buscar_mensagens_fonte` e citou M0004 corretamente. A autorização e versão são revalidadas no serviço. Falta avaliação sistemática. |
| R23 | O aluno diagnosticou uma falha real de recuperação a partir dos documentos-fonte retornados e justificou a técnica de correção aplicada? | Evidência real de ranking: M0023 interrogativa acima de M0024 explicativa; reordenação condicional elevou M0024. O reteste do agente citou M0024 após reformular a consulta. [Antes/depois](../evidencias/fase4_falha_ranking_gama.json). |
| R24 | O aluno construiu um mecanismo de verificação de consistência factual e coerência lógica das respostas do agente? | Planejado |
| R25 | O aluno consolidou um agente único integrando ferramentas de RAG, SQL ou API sob um mesmo executor? | Parcial: um agente reúne SQLite e APIs para visitas/clientes; RAG e financeiro ainda não integrados. |
| R26 | O aluno construiu o executor do agente com create_openai_tools_agent e AgentExecutor? | Planejado |
| R27 | O aluno integrou o histórico de conversa ao agente com RunnableWithMessageHistory? | Planejado |
| R28 | O aluno integrou o agente completo a uma interface Streamlit? | Planejado |
| R29 | O aluno avaliou a qualidade das respostas e a trajetória de chamadas de ferramentas do agente com o LangSmith, justificando as conclusões a partir das métricas obtidas? | Planejado |

Base implementada: [evidência do marco 1](../evidencias/marco1_importacao.json) e [notebook](../notebooks/01_importacao_sqlite.ipynb). Não equivalem a cumprimento dos requisitos de LLM/memória/RAG/avaliação.

Marco 2: [chain e limites](./primeira_chain.md), [notebook](../notebooks/02_extracao_estruturada.ipynb) e [fixture](../evidencias/marco2_fixture.json). A API de geração já foi executada com dados fictícios, inclusive uma execução enviada por Renan com 40/40 mensagens; isso não comprova avaliação semântica, agente com ferramentas ou APIs de negócio.


D013 — Contratos separados por área, JSON Schema na geração e validação local mantida. As três chamadas reais ficaram parciais (8/40, 24/40 e 32/40 mensagens). Falhas e revisão assistida documentadas em docs/execucoes_e_falhas.md. Não equivale a avaliação semântica completa, agente pronto ou integração das APIs de negócio. A confirmação/gravação operacional e FAISS continuam pendentes.


Controle de evolução: [cinco fases](andamento_fases.md). Última validação local: 54 testes; fontes por proposta e rejeições explícitas ainda pertencem ao ajuste da fase 1.


Fase 2 iniciada com [fila de revisão](revisao_persistente.md): autoria, versões, permissões restritas e histórico no serviço. Não satisfaz por si só os itens de agente, chamadas de ferramentas, memória conversacional ou verificador semântico. 72 testes locais; notebook 03 executado sem API. Estado das fases em andamento_fases.md.
