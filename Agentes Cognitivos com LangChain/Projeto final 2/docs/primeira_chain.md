# Marco 2 — chain de interpretação

## Fluxo e classificação

SQLite/snapshot autorizado -> lotes com vizinhos -> ChatPromptTemplate -> modelo -> PydanticOutputParser ->
checagem de IDs/trechos/valores -> propostas aguardando revisão -> arquivo JSON privado.
A aplicação atual é um fluxo de importação e uma chain de interpretação, não agente autônomo.

A composição LCEL é a padrão por tornar etapas explícitas. A versão imperativa usa @chain com as mesmas
etapas para comparação. invoke, batch e stream de objeto completo são demonstrados no notebook.
Esse stream não equivale a streaming de tokens; propostas parciais não são exibidas como fatos verificados.

PTCF: persona secretária, tarefa de interpretar, contexto de mensagens e formato de propostas com fontes.
Few-shot usa Delta e Zeta, separados dos exemplos Alfa/Beta/Gama. Isso não significa que haja dataset
de avaliação independente concluído; o gabarito de avaliação será reservado em etapa posterior.

## Contrato e origem

propostas.py define áreas, natureza, contratos financeiros e agenda. Dinheiro é inteiro em centavos;
percentual é string decimal 0-100; data/hora de agenda exige fuso. Campos ausentes ficam null.
Confirmação na conversa ainda é proposta; não existe campo que permita ao modelo confirmar gravação.
Status aguardando_revisao e identidade da análise são injetados por Python, não escolhidos pelo modelo.

Financeiro distingue orcamento_proposto/aceito, condicao_prevista, pagamento_informado e saldo_indefinido.
A extração não calcula saldos nem transforma condição prevista em pagamento.
A interpretação precisa de revisão: Pydantic só valida estrutura e as checagens locais não provam
toda associação semântica, data inferida ou resumo. O verificador completo é incremento posterior.

## Lotes e cobertura

O snapshot lê todas as mensagens autorizadas, até 5000 neste incremento, sem top-k/LIMIT silencioso.
Cada foco tem até oito mensagens e uma vizinha de cada lado. Fontes são limitadas ao lote; toda proposta
precisa citar ao menos uma mensagem de foco. Há limite de entrada por lote; excesso gera erro, não truncamento.
batch processa leituras independentes com concorrência máxima 2. Falha é registrada por lote e produz estado parcial.
Completa significa cobertura de lotes, não acerto universal do conteúdo ou extração exaustiva de todos os fatos.

Trecho deve corresponder literalmente à fonte (normalização apenas de espaços).
Valor/percentual devem aparecer nas fontes citadas. Valores derivados de soma/percentual são rejeitados:
essa etapa extrai; cálculos do domínio virão depois. Edições/correções ficam pendentes.
Só duplicatas estruturais idênticas são eliminadas; consolidação semântica entre lotes ainda não existe.

## Dados e efeitos

Opções 4/5 analisam somente a demonstração fictícia. A hash dos lotes importados precisa corresponder
ao arquivo fictício atual; corpus com arquivo adicional é bloqueado antes da chamada ao modelo.
O backup privado não é enviado a API por esse fluxo. O modelo baixo nível pode ser usado por código Python
explícito; a restrição de dados está na entrada de serviço analisar_demonstracao, não no nome de uma variável.

Não há escrita de clientes, pagamentos, agenda ou projetos. Uma análise pode ser salva em
dados/privados/analises como artefato de revisão; isso não equivale a aplicar alterações operacionais.
Confirmação/gravação será serviço transacional próprio no próximo fluxo, não uma frase do prompt.

## Validação atual

40 testes locais passaram. Notebook 01: cinco células de código; notebook 02: seis; ambos sem erro.
Fixture manual: oito propostas, 40 mensagens em cinco lotes, zero gravações operacionais.
Esses números não medem compreensão de LLM. A chamada real foi executada; veja o fechamento abaixo e suas limitações.


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
