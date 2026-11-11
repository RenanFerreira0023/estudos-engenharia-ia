# Execuções e falhas — marco 1

## F-001 — Quebras de linha Windows

A primeira suíte rodou 20 testes com uma falha: uma rejeição preservava CRLF e o teste esperava LF.
Inspeção adicional encontrou mistura de quebras no texto lógico multilinha.
Correção: normalizar apenas texto lógico, preservar fonte física; expectativa do teste reflete a fonte original.
Foi acrescentada regressão que importa LF/CRLF sem duplicar mensagens. Resultado: 22 testes passaram.

## E-001 — Núcleo

22 testes locais: parser, fusos/datas inválidas e ambíguas, rejeições, mídia, repetição,
ZIP, sobreposição, repetições legítimas, edições, rollback, FKs, contexto, isolamento e concorrência.
CLI também foi executada a partir de outra pasta. Não são métricas de agente ou LangSmith.

## E-002 — Notebook

Execução real com nbclient e kernel Python local: cinco células de código, zero erros.
TXT, SQLite automático, reabertura, repetição e ZIP passaram. Houve avisos do runtime Jupyter/Windows,
sem falha das células. Saídas do notebook são somente fictícias; nenhuma API externa foi usada.

## E-003 — Backup real

Importação local em banco temporário: 322 entradas/mensagens, zero rejeições, zero novas na repetição.
A contagem anterior de 161 cabeçalhos era da versão inspecionada anteriormente, não do arquivo atual.
A fonte não foi alterada pelo importador; nenhuma credencial/conteúdo/autor foi copiada para evidências públicas.

## Limites

Ainda não há resolução automática de edições, identidade autenticada de autores, interpretação empresarial,
chain, agente, RAG ou chamadas externas. Parsing não comprova recebimento de pagamentos nem execução de serviços.

O CLI também foi testado recusando arquivo próprio sem corpus explícito, antes de criar o banco, evitando misturar dados reais com a demonstração.

## F-002 — Valor monetário seguido de ponto final

A primeira execução da fixture concluiu apenas 24/40 mensagens em lotes: o validador não reconhecia
R$ 10.000,00. com ponto final da frase, bloqueando lotes válidos.
A regex foi ajustada para distinguir pontuação de frase e decimal incompleto. Regressões cobrem a
quantia com ponto final, valor inventado, percentual sem fonte e cálculo indevido.
Depois: cinco lotes concluídos, oito propostas manuais e 40/40 mensagens, sem escrita operacional.

## E-004 — Marco 2 local

40 testes passaram (22 anteriores e 15 novos). Fontes inválidas, JSON inválido, dinheiro float,
percentual impossível, agenda sem fuso, lote grande e lote com falha são rejeitados explicitamente.
Snapshot respeita o corpus do usuário; mistura de arquivo extra bloqueia envio ao modelo.
Foi conferido que a análise de demonstração já importada não altera o banco.
Notebooks 01 e 02 executados com cinco e seis células, zero erros; respostas de 02 são fixtures manuais,
sem alegação de interpretação real por LLM. Execução OpenAI ainda pendente.


## Fechamento da validação do marco 2

40 testes locais passaram após os ajustes; notebook 02 executado novamente, seis células sem erro.
A fixture manual produziu oito propostas com cobertura de 40/40 mensagens; não executa LLM.

Foram preservadas três execuções reais com gpt-4o-mini, somente com as 40 mensagens fictícias:
- marco2_api_real_20261110T020146555304Z.json: parcial, 8/40 mensagens, três propostas.
- marco2_api_real_20261110T021210978750Z.json: parcial, 24/40 mensagens, sete propostas.
- marco2_api_real_20261110T021400551051Z.json: parcial, 32/40 mensagens, onze propostas.

Os arquivos estão em evidencias/. São observações de execução, não taxas de qualidade.
O último lote rejeitado citou percentual sem o correspondente trecho literal. Não foi aprovado nem apagado.
Zero gravações operacionais nas três execuções. Datas dos nomes de arquivo estão em UTC.

F003: o primeiro retorno real misturou área projeto com objeto financeiro e foi rejeitado pelo parser.
A geração passou a usar JSON Schema estrito com três contratos de área separados; Pydantic continua validando
as regras locais. Horário sem fuso e valor sem fonte também foram observados na segunda execução;
o prompt recebeu instruções explícitas de offset e de não calcular valores nesta etapa.
A terceira execução ainda foi parcial. Não há reparo automático nem garantia de extração completa.

Revisão manual assistida do último artefato:
- Recebimento Alfa de R$ 2.000,00 mantém pagamento_informado e cita as mensagens 37/38: coerente com o relato,
  sem tratar conversa como comprovante.
- Cancelamento Beta cita a mensagem 35, mas deixou projeto=null: exige revisão de completude.
- Conflito de agenda contém horários que não aparecem nos trechos citados dessa proposta:
  a verificação atual não valida toda associação de datas/contexto.
Esta é revisão do assistente, não avaliação humana de Renan nem nota de juiz LLM.
Próximo passo: fortalecer rastreabilidade semântica e revisão/confirmacão transacional antes de aplicar propostas.


## Revisão de cancelamentos e mensagens editadas

A execução enviada por Renan concluiu 40/40 mensagens e gerou 17 propostas, mas classificou
o cancelamento Beta como correção sem projeto e não exibiu claramente a visita Gama editada.
A regra local reconhece apenas pedido explícito no início do trecho, como
Cancelar reunião Beta de 12/11/2026, sem interrogação. Corrige natureza/projeto,
preserva os valores anteriores em ajustes_revisao e exige vincular/confirmar antes de aplicar.
Perguntas, negações e nomes conflitantes não são convertidos por essa regra.

Toda mensagem marcada como editada é exibida separadamente, com seu texto literal.
Outros textos do mesmo autor/instante são apenas candidatos ao vínculo, nunca versões comprovadas.
Assim, o exemplo Gama mostra 15h e 16h sem escolher horário ou alterar compromisso.
O prompt também orienta o modelo, mas a apresentação das edições independe de sua resposta.

47 testes passaram (sete regressões novas). Reprocessamento local da análise real já salva:
17 propostas preservadas; cancelamento Beta corrigido; edição M0030 e candidato M0029 exibidos.
Não houve nova chamada de LLM para essa evidência. Zero gravações operacionais.
Arquivo: evidencias/marco2_revisao_cancelamento_edicao.json.
Reexecute a opção 4 para ver o aviso da edição; a opção 5 faz uma nova chamada real e pode variar.


## Fontes validadas por proposta

A execução enviada por Renan em analise_022682fedead47178e8c3aee88ca0cd6.json teve cobertura 24/40:
os lotes 1 e 3 falharam com uma mensagem que agrupava IDs repetidos e ausência de fonte de foco.
O artefato antigo não contém as propostas rejeitadas; não é possível atribuir a causa específica retroativamente.

Agora cada proposta estruturada passa pela validação de fontes separadamente. Uma rejeição não remove as
demais propostas válidas do lote. O relatório guarda número, causa e conteúdo da proposta rejeitada
com estado rejeitada_por_fonte, fora da lista de propostas para revisão/aplicação.
IDs repetidos e ausência de fonte de foco têm mensagens distintas. Não se inventam fontes nem se aprovam
propostas de vizinhos. JSON/contrato inválido e falha de API ainda bloqueiam o lote inteiro.

Um lote com rejeições continua parcial. A cobertura estrita continua contando somente mensagens de lotes
sem rejeições; propostas preservadas de lotes parciais não tornam a cobertura completa.
O terminal mostra propostas preservadas e rejeitadas separadamente. Não há reparo automático ou nova chamada
de API neste ajuste; o prompt recebeu instruções sobre foco e IDs únicos.

Validação: 54 testes passaram; notebook 02 reexecutado (seis células).
A evidência marco2_fontes_por_proposta.json é uma fixture manual: uma proposta válida preservada e uma
com IDs repetidos rejeitada, zero gravações operacionais. Não representa nova saída de LLM.


D016 — Início da fase 2: fila de interpretações revisadas, separada dos registros operacionais. Migração SQLite v2 preserva fontes; decisões exigem proprietário/perfil, versão e comentário no serviço. Não há agente nem gravação operacional. 72 testes locais, notebook 03 (seis células) e roteiro terminal com fixture executados; nenhuma API chamada. Teste anterior de versão v1 atualizado e migração com dados existentes testada. Ver revisao_persistente.md e evidencias/marco3_revisao_persistente.json.
# Memória conversacional — teste manual de 11/11/2026

Renan informou `Estou falando do cliente alfa`; o agente chamou `buscar_cliente` e recebeu Alfa Serviços. Na pergunta seguinte (`qual clinte eu falei agora?`), respondeu Alfa Serviços sem nova ferramenta: evidência de contexto na conversa corrente. Após `/voltar` e retorno à opção 9, o identificador da conversa permaneceu o mesmo. Renan usou `/nova`, que criou outro identificador, mas a pergunta `qual cliente eu mencionei?` acionou uma busca com termo vazio e saiu do chat com `Informe nome ou CNPJ do cliente.` O teste não incluiu fechamento e reabertura do programa, portanto ainda não comprova persistência após reinício por observação manual.

Correção: `buscar_cliente` agora devolve `termo_necessario` para termo vazio, sem encerrar o chat; o prompt instrui a pedir o nome quando não há cliente mencionado na conversa atual. Teste local da ferramenta e suíte completa passaram (99 testes). Naquele momento ainda faltava o reteste real descrito abaixo.

**Reteste manual concluído por Renan em 11/11/2026:** após `/nova`, a sessão `f934cd9fece5417291bc3b675fde251e` respondeu que não sabia qual cliente havia sido mencionado e pediu o nome. Renan informou `Estou falando do cliente Alfa.`; o agente chamou `buscar_cliente` e recebeu `Alfa Serviços`. Renan saiu com `/voltar`, encerrou o programa com `0`, reabriu `executar.py` usando o mesmo banco e usuário padrão, e a opção 9 retomou **o mesmo ID de sessão**. À pergunta `Qual cliente eu mencionei?`, a resposta foi `Alfa Serviços`, sem nova chamada de ferramenta mostrada no terminal. Isso demonstra recuperação do histórico após reinício para esse usuário e essa sessão. Não demonstra ainda busca vetorial, sumarização, autenticação real ou isolamento manual entre usuários; o último é coberto por teste local.

