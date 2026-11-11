# Uso de IA

Codex auxiliou a planejar/escrever parser, SQLite, terminal, dataset fictício, notebook, testes e documentação.
A revisão incluiu testes, execução real de notebook e inspeção local. A falha inicial de CRLF e correção estão registradas.

O código deste marco não usa LLM. O backup real não foi enviado a APIs externas, OpenAI ou LangSmith;
foi lido/importado somente localmente. Exemplos públicos e notebook usam apenas dados fictícios.

Não foram medidas métricas semânticas de agente, tokens/custos de API ou LangSmith.
Renan precisa compreender e revisar o código/decisões para a apresentação acadêmica.

## Marco 2

Codex auxiliou contratos, prompts, LCEL/@chain, validação de fontes, snapshots/lotes, fixtures e notebook.
O executável passa a oferecer análise opcional por OpenAI gpt-4o-mini. O modo fixture continua explícito,
sem uso de LLM. Somente dados fictícios serão usados na validação externa; backup real permanece privado.
Não há registro de decisões de negócio efetivadas, avaliação LangSmith ou precisão semântica medida.


D013 — Contratos separados por área, JSON Schema na geração e validação local mantida. As três chamadas reais ficaram parciais (8/40, 24/40 e 32/40 mensagens). Falhas e revisão assistida documentadas em docs/execucoes_e_falhas.md. Não equivale a avaliação semântica completa, agente pronto ou integração das APIs de negócio. A confirmação/gravação operacional e FAISS continuam pendentes.


D014 — Revisão conservadora baseada em trechos explícitos: cancelamentos recebem trilha de ajuste; edições ficam visíveis independentemente do LLM, sem escolher a versão válida. 47 testes e replay local da saída enviada por Renan; detalhes em primeira_chain.md. Não há nova chamada de API nem aplicação operacional nesta validação.


D015 — Validação de fontes por proposta, com rejeições preservadas fora da lista utilizável e estado parcial mantido. Teste manual controlado, 54 testes locais e notebook executado; sem nova API. A fase 1 não foi declarada concluída. Ver andamento_fases.md e primeira_chain.md.


D016 — Início da fase 2: fila de interpretações revisadas, separada dos registros operacionais. Migração SQLite v2 preserva fontes; decisões exigem proprietário/perfil, versão e comentário no serviço. Não há agente nem gravação operacional. 72 testes locais, notebook 03 (seis células) e roteiro terminal com fixture executados; nenhuma API chamada. Teste anterior de versão v1 atualizado e migração com dados existentes testada. Ver revisao_persistente.md e evidencias/marco3_revisao_persistente.json.
