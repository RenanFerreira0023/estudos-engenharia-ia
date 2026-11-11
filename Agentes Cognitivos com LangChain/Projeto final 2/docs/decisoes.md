# Decisões iniciais — Secretária IA

## D-001 — Novo projeto isolado

- Data: 09/11/2026.
- Decisão: descontinuar autopeças como entrega ativa e iniciar Secretária IA em Projeto final 2.
- Origem: decisão expressa de Renan nesta conversa e novo plano fornecido.
- Motivo: nova direção mais próxima da organização de informações de uma empresa a partir de conversas.
- Consequência: preservar código/testes/evidências anteriores; reaproveitar componentes genéricos somente após revisão. Não atribuir seus testes ao novo projeto.
- Estado: escopo aprovado; implementação nova ainda não iniciada.

## D-002 — Corrigir a identificação do corpus

- Observação: o plano 1.1 descrevia exportação de grupo da turma, mas o _chat.txt recebido é conversa interna de trabalho.
- Verificação: leitura local e contagem preliminar de 161 cabeçalhos; não é importador funcional nem análise empresarial exaustiva.
- Decisão: ajustar a seção 5 para o arquivo realmente disponível, sem alterar o original.
- Limite: mensagens de suporte/reuniões e relatos encaminhados não fornecem automaticamente projetos, parcelas e pagamentos completos.

## D-003 — Backup real privado; demonstração fictícia

- Motivo concreto: o arquivo tem nomes, informações internas e uma credencial escrita na conversa.
- Decisão: ignorar o original no Git e não copiá-lo para prompts de APIs, exemplos públicos ou LangSmith sem autorização específica.
- Demonstração: corpus fictício separado, com gabarito; sem atribuir eventos inventados a pessoas reais.
- Estado: proteção de versionamento aplicada; anonimização/importador ainda não implementados. Gitignore não apaga versões já publicadas; na inspeção, o arquivo não estava rastreado.

## D-004 — Começar pequeno, conforme plano

- Primeiro incremento: parsing local fiel, fontes, importação idempotente e uma chain pequena com saída estruturada.
- Depois: fluxo usuário -> cliente -> agenda -> proposta -> confirmação -> gravação.
- Limites: sem Meta/Google Calendar, sem envio automático a terceiros e sem ERP. Identidade/permissões de demonstração devem ser explícitas.
- APIs previstas: Minha Receita para cadastro PJ e ViaCEP para endereço de visita; integração real ainda não realizada neste projeto.


## D-005 — Importação local e fontes antes do LLM

Dataclasses representam mensagens lidas; SQLite recebe migração 1 com empresas/usuários/corpora/lotes/mensagens/fontes/avisos.
BEGIN IMMEDIATE torna atômicas a checagem de repetição e a gravação, com autoria pelo Contexto da aplicação.
Hash do TXT no corpus impede repetir lote. Data/autor/texto/ocorrência identificam mensagens em sobreposições.
Não há IDs nativos: repetições indistinguíveis geram aviso. Edição sinalizada mantém originais e candidatas sem resolver o conflito.
Fuso é premissa do corpus, não informação alegadamente presente no export. Estado: marco 1 implementado.

## D-006 — Notebook e terminal usam os mesmos módulos

Banco nasce automaticamente, sem servidor. Núcleo usa biblioteca padrão; tzdata fornece fusos IANA no Windows.
Notebook usa banco temporário isolado; CLI conserva arquivo em dados/privados.
40 mensagens fictícias com três funcionários/projetos e gabarito independente, não saída de LLM.
22 testes locais e cinco células executadas sem erro; não houve instalação em ambiente limpo.

## D-007 — Corpus bruto privado no primeiro incremento

Importador e administrador podem ler o corpus bruto; outro usuário precisa de corpus próprio.
Empresa/usuário/corpus são conferidos no serviço e em FKs. Seleção de demonstração não é autenticação.
Regras completas sobre financeiro/RAG/Excel ainda não estão implementadas.
Backup real processado somente localmente; evidência pública não contém autores, texto, credenciais ou dump do SQLite.

## D-008 — SQLite complementará FAISS

Renan perguntou se FAISS seria mais adequado. SQLite conserva a fonte/registro e permite integridade/cálculos.
FAISS fará busca por significado. Não usar top-k como inventário exaustivo.
Persistência de mensagens no banco não é memória cognitiva/agente implementado; índice vetorial continua planejado.

## D-009 — LCEL padrão e @chain equivalente

ChatPromptTemplate, modelo e PydanticOutputParser compõem a primeira chain. @chain preserva sequência
equivalente para estudo. Modelos/ferramentas de autopeças não são importados. Stream imperativo retorna
objeto completo; não alegar streaming de tokens.

## D-010 — Extração por lotes com cobertura e fontes

Snapshot autorizado lê todas as mensagens; foco de oito com uma vizinha. IDs e trechos devem corresponder
ao lote; pelo menos uma fonte é de foco. JSON/contrato ou fonte inválida falha o lote, sem declarar
cobertura completa. Números precisam estar escritos nas fontes; cálculos de negócio ficam para depois.

## D-011 — Propostas ainda não são gravações nem prova externa

Natureza de pergunta/previsão/relato/correção/confirmacao é preservada; pagamento só informado.
Status aguardando revisão vem do serviço. Não há tabelas operacionais novas nem confirmação aplicada.
Consistência estrutural/numérica não comprova toda interpretação; revisão semântica fica pendente.

## D-012 — API somente com demonstração; fixture identificada

Menu 4 usa oito respostas manuais do corpus fictício, sem compreensão LLM.
Menu 5 usa OpenAI apenas sobre corpus fictício autorizado e sem outro arquivo importado.
Leitura de chave: variável de ambiente ou .env local/explicitamente escolhido. Não copiar nem procurar
segredos silenciosamente em outros projetos. Saídas de análise ficam privadas por padrão.


D013 — Contratos separados por área, JSON Schema na geração e validação local mantida. As três chamadas reais ficaram parciais (8/40, 24/40 e 32/40 mensagens). Falhas e revisão assistida documentadas em docs/execucoes_e_falhas.md. Não equivale a avaliação semântica completa, agente pronto ou integração das APIs de negócio. A confirmação/gravação operacional e FAISS continuam pendentes.


D014 — Revisão conservadora baseada em trechos explícitos: cancelamentos recebem trilha de ajuste; edições ficam visíveis independentemente do LLM, sem escolher a versão válida. 47 testes e replay local da saída enviada por Renan; detalhes em primeira_chain.md. Não há nova chamada de API nem aplicação operacional nesta validação.


D015 — Validação de fontes por proposta, com rejeições preservadas fora da lista utilizável e estado parcial mantido. Teste manual controlado, 54 testes locais e notebook executado; sem nova API. A fase 1 não foi declarada concluída. Ver andamento_fases.md e primeira_chain.md.


D016 — Início da fase 2: fila de interpretações revisadas, separada dos registros operacionais. Migração SQLite v2 preserva fontes; decisões exigem proprietário/perfil, versão e comentário no serviço. Não há agente nem gravação operacional. 72 testes locais, notebook 03 (seis células) e roteiro terminal com fixture executados; nenhuma API chamada. Teste anterior de versão v1 atualizado e migração com dados existentes testada. Ver revisao_persistente.md e evidencias/marco3_revisao_persistente.json.

D017 — Primeiro fluxo vertical de visita: migração v3 cria clientes, propostas e agendamentos. O serviço usa `BEGIN IMMEDIATE` para conferir conflito novamente antes de confirmar, preserva autoria/endereço e retorna o mesmo ID numa repetição. Menu 7 é demonstração local; menu 9 usa `create_agent` opcional com ferramentas de consulta/proposta, ViaCEP e Minha Receita, sem gravação direta pelo modelo. Confirmação permanece no serviço e exige usuário da proposta. 78 testes locais passaram; nenhuma chamada real de OpenAI/ViaCEP/Minha Receita foi observada neste incremento. Falta integrar cadastro PJ completo, projetos e fontes, persistir diálogo e produzir evidência real de ferramenta. Não declarar fase 2 concluída.

# Cadastro PJ conduzido pelo agente — 10/11/2026

Consulta externa, proposta e cadastro confirmado são estados distintos. A consulta ao CNPJ salva um snapshot mínimo com origem e autoria; a ferramenta de proposta aceita apenas o `consulta_id` do usuário atual. O modelo não recebe ferramenta de confirmação. `/confirmar-cliente ID` executa transação com rechecagem de prazo e duplicidade, grava a origem da consulta e registra auditoria. O menu 7 permanece como fluxo guiado. Notebook 04 usa fixture identificada; a trajetória real completa deste incremento ainda precisa ser observada.
