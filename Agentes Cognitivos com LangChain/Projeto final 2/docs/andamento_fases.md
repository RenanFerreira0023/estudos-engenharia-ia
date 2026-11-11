# Andamento nas cinco fases do trabalho

Referência: [plano, seção 13](../PLANO_PROJETO_SECRETARIA_IA.md) e [matriz dos 29 itens](matriz_requisitos.md).
As cinco fases são incrementos do mesmo projeto. Os dois notebooks atuais são demonstrações da fase 1,
não duas fases concluídas. A etapa 0 é preparação; não é uma sexta fase da entrega.

| Fase | Conteúdo | Estado atual | Próxima evidência |
|---|---|---|---|
| 1 | Importação e chain estruturada | Em validação: importação, contratos, LCEL/@chain e fontes implementados; 54 testes e notebook 02 executado. Sem declarar todos os itens da fase concluídos. | Revisar cobertura de candidatos cliente/projeto e documentação de anatomia/maturidade/decomposição; consolidar casos reais e limites. |
| 2 | Agente, ferramentas e gravação confiável | Iniciada: fila de revisão, fluxo local de visita com confirmação auditada e agente opcional com ferramentas. | Chamada real do agente/APIs; cadastro PJ e integração completa. |
| 3 | Contexto e persistência entre sessões | Planejada. SQLite das fontes não comprova memória conversacional. | Diálogo multi-turno, reinício e isolamento. |
| 4 | RAG, text-to-query e diagnóstico | Planejada. FAISS ainda não implementado. | Consultas com fontes e falha de recuperação analisada. |
| 5 | Integração, verificação, interface, Excel e avaliação | Planejada. | Agente integrado, Streamlit, relatórios e avaliação LangSmith. |

Atualização de 10/11/2026: fase 2 ganhou fluxo local de visita (migração v3, proposta, confirmação transacional, agenda por atendente e auditoria), menu 7/8 e agente opcional com ferramentas no menu 9. O campo de atendente aceita ID ou nome completo sem diferenciar maiúsculas. Os 79 testes locais passaram. Nenhuma chamada real ao agente, ViaCEP ou Minha Receita foi comprovada neste incremento; a fase permanece em andamento. A fila de interpretações continua separada da agenda operacional.

Teste manual posterior da opção 9: a chamada à OpenAI retornou HTTP 401 com código `expired_secret_key` antes de qualquer ferramenta do agente. A chave foi encontrada no `.env`, mas está expirada. O terminal agora trata esse erro sem traceback; o teste de regressão passou (80 testes locais). A trajetória do agente ainda não foi avaliada.

Após substituir a chave, a chamada real alcançou `buscar_cliente`, mas a ferramenta falhou porque reutilizava a conexão SQLite da thread do terminal na thread de execução do LangGraph. Cada ferramenta de banco agora abre e fecha sua própria conexão; o teste de busca e disponibilidade em threads passou. Total atual: 81 testes locais. A resposta final do agente ainda precisa ser observada em nova execução.

Execução real seguinte: `buscar_cliente` encontrou Alfa e `consultar_disponibilidade` retornou sem conflito registrado para Bruno. Em outra mensagem, `consultar_cep_viacep` retornou Praça da Sé para 01001000. O agente pediu número novamente apesar de o usuário ter informado `s/n`; prompt e contrato da proposta foram ajustados para preservar número e CEP. Essa correção ainda exige nova observação manual; nenhuma proposta ou confirmação do agente foi demonstrada nessa conversa.

Continuação manual da mesma conversa: o usuário informou número 546; o agente chamou `propor_visita` e recebeu proposta #4 pendente. O usuário digitou `/confirmar 4`; o serviço devolveu agendamento #4 confirmado. A opção 8 de Bruno exibiu #4 das 17h às 18h UTC (14h às 15h em São Paulo), seguido de #3 a partir de 18h UTC. [Registro conciso da evidência](../evidencias/fase2_visita_agente_revisao_manual.json). A proposta #4 não continha CEP porque a execução começou antes do ajuste no contrato da ferramenta; não alegar validação desse ajuste nem fase 2 concluída.

Nova execução manual: o agente buscou Alfa, consultou disponibilidade, chamou ViaCEP e criou a proposta #5 com CEP 01001-000 e número `s/n`, sem repetir pergunta sobre número. `/confirmar 5` criou agendamento #5; a repetição retornou `já_confirmada` com o mesmo ID; a agenda de Bruno exibiu #5. [Evidência](../evidencias/fase2_visita_cep_idempotencia_manual.json). Ainda faltam teste de conflito via agente, cadastro PJ e demais itens da fase 2. A resposta "disponível" foi mais forte que o retorno da ferramenta ("sem conflito registrado").

Teste de conflito via agente: para Bruno em 12/11/2026 das 14h30 às 15h30, `consultar_disponibilidade` retornou false; o agente pediu outro horário e não chamou `propor_visita`. [Evidência manual](../evidencias/fase2_conflito_agente_manual.json). Permanecem cadastro PJ/API, integração com projetos/fontes e avaliação sistemática.

Teste PJ em banco separado: menu 7 consultou Minha Receita real para o CNPJ público de exemplo 33683111000280, apresentou razão social/nome fantasia, recebeu confirmação e salvou uma visita fictícia de Ana em 13/11/2026 10h–11h10. [Evidência](../evidencias/fase2_pj_minha_receita_manual.json). A consulta foi do fluxo guiado, não uma chamada escolhida pelo agente. Migração v4 posterior guarda origem, instante e nome fantasia em novos cadastros PJ; registros anteriores recebem `origem_nao_registrada`, sem inventar retroativamente a origem. O texto inicial do menu foi corrigido. 83 testes locais passaram, inclusive migração de cliente legado e persistência da origem em cadastro novo.

Teste seguinte via agente: à pergunta se o CNPJ já estava cadastrado, o modelo chamou apenas `consultar_cnpj_minha_receita`, executou a API externa e afirmou cadastro local sem evidência do SQLite. [Falha registrada](../evidencias/fase2_falha_busca_local_cnpj_manual.json). A ferramenta agora verifica a base antes da API e distingue `ja_cadastrado` de `nao_cadastrado`; o prompt exige busca local. 85 testes locais passaram, inclusive bloqueio de chamada externa com CNPJ existente e ausência de gravação para consulta externa de CNPJ novo. Repetição real pelo usuário ainda pendente; não contar como trajetória aprovada.

Reteste manual com o mesmo CNPJ: o modelo escolheu diretamente `consultar_cnpj_minha_receita`, mas a ferramenta consultou SQLite e retornou `ja_cadastrado`, `origem=banco_local`, `api_externa_chamada=false`. [Evidência](../evidencias/fase2_cnpj_existente_reteste_manual.json). A proteção de não consultar API externa e a resposta baseada no banco passaram; a preferência de trajetória por `buscar_cliente` primeiro ainda não foi observada. Não atribuir ao banco origem retroativa da consulta anterior: registro legado mostra `origem_nao_registrada`.

Em banco novo isolado, o agente chamou `consultar_cnpj_minha_receita`; a ferramenta retornou `nao_cadastrado`, `api_externa_chamada=true`, com dados públicos. O agente disse corretamente que o cliente não estava cadastrado. Consulta SQL local após a conversa: zero clientes e zero propostas. [Evidência](../evidencias/fase2_cnpj_novo_agente_manual.json). Ainda falta proposta e confirmação de cadastro PJ conduzidas pelo agente; a consulta sozinha não fecha esse fluxo.

No mesmo banco isolado, o usuário usou menu 7, confirmou cadastro PJ após nova consulta real da Minha Receita, e a consulta SQL local encontrou razão social, nome fantasia, `origem_cadastro=minha_receita_real` e instante da consulta persistidos. [Evidência](../evidencias/fase2_pj_origem_persistida_manual.json). A visita desse novo atendimento ainda não tinha sido concluída no momento da evidência.

Continuação: usuário confirmou visita fictícia #1 para Ana em 13/11/2026 14h–15h com endereço manual. Depois reiniciou e perguntou ao agente pelo mesmo CNPJ; a ferramenta devolveu `ja_cadastrado`, `api_externa_chamada=false`, nome fantasia e origem persistidos. [Evidência de reuso](../evidencias/fase2_pj_reuso_sem_api_manual.json). O conjunto de testes manuais deste fluxo passou; fase 2 ainda depende de cadastro PJ por proposta/confirmacao dentro do agente, vínculo com projetos/fontes, tracing/eval e demais critérios da matriz.

Evidências atuais: [importação](../notebooks/01_importacao_sqlite.ipynb),
[chain](../notebooks/02_extracao_estruturada.ipynb),
[fontes por proposta](../evidencias/marco2_fontes_por_proposta.json).
Requisitos legados de classes/frameworks devem continuar explícitos na matriz; uma alternativa moderna
não será apresentada como implementação literal da classe antiga sem justificativa.

As quatro entregas finais continuam sendo acompanhadas pelo plano, seção 17.
Ainda não estão concluídos o conjunto de cinco demonstrações/fases, PDF final, avaliação LangSmith e vídeo.
Novas regras do professor devem ser comparadas com o plano antes de alterar a matriz.


Incremento atual da fase 2: [revisão persistente](revisao_persistente.md) e [notebook 03](../notebooks/03_revisao_persistente.ipynb). 72 testes locais passaram. A numeração dos três notebooks não equivale a três fases concluídas; 01/02 são fase 1 e 03 inicia a fase 2.
