# Revisão do projeto perante o enunciado e a aula 08

> Revisão histórica do plano inicial. Decisão posterior de Renan substituiu Excel pelo relatório financeiro em tela; consulte o plano e a matriz atuais para o escopo vigente.

**Data da revisão:** 11/11/2026. **Fontes:** enunciado obrigatório enviado por Renan nesta conversa; [apostila da aula 08](../../aula%2004-11/apostila_agentes_cognitivos_aula_08.html); [plano](../PLANO_PROJETO_SECRETARIA_IA.md), [matriz](matriz_requisitos.md) e código do Projeto final 2. A apostila é um resumo da aula, não uma nova rubrica oficial.

## Conclusão

O domínio **Secretária IA** cabe no projeto: a disciplina permite escolher um agente que consulta dados, usa ferramenta externa e conversa com contexto. A construção incremental em cinco fases e os quatro entregáveis finais estão mapeados no plano. **A implementação ainda não cobre o trabalho completo.** Conforme a matriz atual, 5 dos 29 itens estão implementados/demonstrados, 4 são parciais e 20 continuam planejados. Essa contagem é de documentação, não uma nota ou porcentagem de qualidade.

| Fase | Evidência existente | Lacuna que impede declará-la concluída |
|---|---|---|
| 1 — chain | Importação, `ChatPromptTemplate`, saída estruturada, LCEL, `@chain`, `invoke`/`batch`/`stream` e notebooks 01–02. | Anatomia/maturidade, planejamento e memória aumentada ainda precisam ser explicados com o próprio domínio e ligados a uma demonstração de ponta a ponta. |
| 2 — agente | `create_agent`, ferramentas SQLite/ViaCEP/Minha Receita, chamadas reais observadas, proposta e confirmação de visitas/PJ, fontes e notebooks 03–05. | Comparação de orquestradores, PTCF/few-shot, roteamento entre áreas, logging/callbacks e demonstração integrada ainda não estão fechados. Os notebooks 03–05 pertencem à fase 2; cinco arquivos não significam cinco fases. |
| 3 — memória | O menu 9 mantém `historico` durante a conversa em execução. SQLite persiste dados confirmados, não o diálogo. | Histórico por usuário/sessão entre reinícios, limite de janela, recuperação de memória, isolamento, CoALA e diálogo real de múltiplos turnos com evidência. |
| 4 — recuperação | Mensagens e IDs de fonte ficam no SQLite. | Índice FAISS carregado como ferramenta, text-to-query seguro e falha real de recuperação com antes/depois. |
| 5 — integração/avaliação | Serviços e testes locais dão base para integrar. | Agente único com verificador, avaliação de resposta **e** trajetória, Streamlit escolhido por Renan, relatório PDF e vídeo real. |

## Enunciado escrito e orientação da aula

- O enunciado nomeia `initialize_agent`, `RouterChain`, `ConversationBufferMemory`, `create_openai_tools_agent`, `AgentExecutor` e `RunnableWithMessageHistory`. A apostila atribui ao professor a orientação de aceitar métodos atuais equivalentes, desde que o conceito funcione e a equivalência seja explicada. Não marcar um item como atendido apenas porque `create_agent` existe; mostrar o comportamento correspondente.
- O enunciado pede **registro de avaliação no LangSmith**. A apostila relata que uma avaliação própria com registros, trajetória e análise pode ser aceita oralmente. Para reduzir risco perante o texto escrito, priorizar LangSmith se houver acesso; uma alternativa deve ter evidência equivalente e justificativa explícita.
- A apostila diz que Streamlit é opcional, mas Renan decidiu usá-lo. Portanto, entra na entrega planejada, reutilizando os serviços Python e mantendo sessões separadas.
- FAISS é preferido na aula e escolhido no plano. Outro índice só deve substituí-lo com justificativa e capacidade de inspecionar documentos retornados. A avaliação e o diagnóstico de uma falha real de recuperação continuam necessários.
- A menção a chain-of-thought não autoriza alegar acesso ao pensamento interno do modelo. Registrar decisões observáveis: mensagens, chamadas de ferramentas, argumentos, resultados e fontes.
- A aula aceita um notebook com cinco seções **ou** vários notebooks. Os notebooks existentes usam o mesmo código modular, mas ainda precisam cobrir as fases 3–5. Fixtures locais devem permanecer identificadas; o vídeo precisa mostrar interação real.

## Quatro entregáveis ainda a preparar

1. **Código/notebook reprodutível:** organizar os marcos em um roteiro de execução, dependências e dados dummy; concluir as fases restantes.
2. **PDF técnico:** problema, arquitetura, decisões por fase, resultados/limites, evidências e citação do uso de IA. Nome pedido no enunciado: `nome_sobrenome_ai-agents_langchain-agents.pdf`.
3. **Avaliação:** dataset, qualidade semântica, trajetória de ferramentas, revisão de falso positivo e análise dos resultados; preferir LangSmith pelo enunciado escrito. Não inventar métricas.
4. **Vídeo:** Renan e tela visíveis; execução real com pelo menos uma ferramenta/API externa e memória entre turnos. O vídeo não substitui o código.

O enunciado enviado mostra **13/11/2026 às 23h59** como prazo de entrega. A apostila registra que o professor anunciou o dia 13/11, mas não especificou horário na fala. Conferir o ambiente da disciplina antes da submissão.

## Prioridade recomendada

Conservar o que já funciona e **priorizar os conceitos centrais ainda ausentes antes de ampliar ERP financeiro e Excel**. Próxima sequência: (1) fechar arquitetura e decisões curtas da fase 1/2; (2) memória por sessão/usuário com teste multi-turno e reinício; (3) FAISS, text-to-query e diagnóstico; (4) agente integrador, verificação e dataset de avaliação; (5) interface Streamlit; (6) PDF e vídeo. Financeiro e Excel permanecem no escopo aprovado; a profundidade dessas partes deve caber no prazo, com dados fictícios, estados distintos e fontes.

Esta revisão não muda o estado dos 29 itens: cada um precisa de evidência específica antes de ser marcado como demonstrado.
