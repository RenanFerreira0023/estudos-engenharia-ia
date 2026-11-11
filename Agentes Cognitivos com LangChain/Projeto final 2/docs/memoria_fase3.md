# Fase 3 — janela, recortes antigos e recuperação

O menu 9 envia ao agente as **seis interações mais recentes** da conversa atual. O SQLite guarda o histórico completo por `(empresa_id, usuario_id, sessao_id)`, inclusive após reiniciar o programa. `/nova` cria outra sessão; os turnos da anterior não entram no novo contexto.

Ao registrar um turno, o serviço grava em `resumos_turnos_agente` um **resumo extrativo** para cada turno que saiu da janela: a fala do usuário (até 500 caracteres) e o ID do turno original. A resposta do modelo é descartada desse recorte para não transformar uma resposta possivelmente errada em fato lembrado. O texto original continua em `turnos_agente`; portanto, o recorte não substitui a fonte. Não há segunda chamada de LLM nem inferência semântica nessa etapa.

Antes de `invoke`, `buscar_resumos()` compara palavras da pergunta com os 500 recortes mais recentes **da mesma sessão e usuário**, ordena por correspondência e recência, e entrega no máximo dois. O agente recebe esses textos rotulados como falas antigas **não confirmadas**. Dados operacionais, como cadastro e agenda, ainda exigem ferramentas. Busca por palavras pode perder paráfrases, e o limite de 500 recortes pode omitir fatos muito antigos; FAISS e seu diagnóstico específico pertencem à fase 4.

Um [teste real](../evidencias/fase3_falha_lexical_cleinte.json) mostrou a limitação: `cleinte alfa` no turno antigo não correspondia a `cliente` na pergunta. A busca foi ajustada para aceitar palavras longas muito parecidas, dando prioridade a correspondências exatas. No reteste real, o agente retomou a sessão, recuperou o turno 9 e respondeu `Alfa` à pergunta sobre a conversa, sem chamar ferramenta. A correção reduz erros de digitação, mas pode trazer falsos candidatos e não resolve paráfrases semânticas.

Na taxonomia CoALA aplicada aqui, os seis turnos são contexto de trabalho; os recortes de conversa são memória episódica do que o usuário disse, sem validação; cadastros e projetos confirmados no SQLite são fatos estruturados, não resumos de chat; regras de confirmação ficam no serviço e no prompt como comportamento procedural. Esta classificação descreve o protótipo, não afirma que toda memória cognitiva da fase 3 esteja pronta.

O [notebook 07](../notebooks/07_resumos_recuperacao.ipynb) usa fixture local para mostrar que uma menção a Alfa sai da janela, reaparece como recorte relevante e não vaza para Bruno ou para `/nova`. O teste de integração local verifica que o recorte entra no pedido enviado ao agente. O reteste real citado acima observou uma resposta do LLM após mais de seis turnos.

## Preferências pessoais confirmadas

O SQLite v9 guarda `estilo=curto/detalhado` e `idioma=portugues/ingles` por empresa e usuário. No menu 9, `/lembrar chave=valor` grava uma preferência explícita, `/memorias` lista os valores atuais e `/esquecer-memoria chave` apaga o valor e suas versões anteriores. `/nova` limpa o contexto da conversa, mas conserva essas preferências. Uma correção incrementa a versão; o agente recebe apenas o valor atual. [Notebook 08](../notebooks/08_preferencias_confirmadas.ipynb) demonstra correção, reinício, isolamento e exclusão sem LLM. Os testes locais comprovam que o valor é enviado no contexto do agente, mas ainda falta observar a mudança de estilo em uma resposta real.

## Ferramentas de memória consideradas

| Ferramenta | Arquitetura e caso de uso | Decisão neste protótipo |
|---|---|---|
| [LangMem](https://langchain-ai.github.io/langmem/) | Ferramentas para o agente gravar/buscar memórias e gerenciador que extrai e atualiza memórias a partir da conversa; integra com o Store do LangGraph. | Não adotado agora: as duas preferências são explícitas, enumeradas e auditáveis no SQLite; extração automática aumentaria o risco de registrar uma inferência como fato. |
| [Mem0](https://docs.mem0.ai/platform/quickstart) | API/SDK de memória com `add` e `search`, busca filtrada por `user_id`; útil para personalização em conversas numerosas. | Não adotado agora: o escopo é pequeno e o corpus pode ser privado. Uma API hospedada exigiria decisão separada sobre envio de dados. |

Ambas podem ajudar em memória de longo prazo, mas não substituem autorização, confirmação nem separação por usuário. A busca atual de recortes é lexical, não vetorial. A fase 3 ainda precisa de recuperação vetorial relevante e testes de troca explícita de projeto e referência como “dele”; o índice FAISS das mensagens com fontes está planejado para a fase 4.

## Falha observada: projeto tratado como cliente

No teste manual de Alfa → Beta, o agente chamou `buscar_cliente` para “saldo dele”. Para Alfa, respondeu sobre o cadastro do cliente; para Beta, disse que não encontrou cliente. `/nova` funcionou: depois dela, pediu identificação. A causa verificada no código era a ausência de ferramenta de consulta a projetos no menu 9. Agora `consultar_projeto` pesquisa projetos da empresa e só devolve anotações de corpus e área acessíveis ao usuário; o roteador reconhece projeto e saldo. O prompt proíbe usar orçamento ou pagamento informado como saldo confirmado. No [reteste real](../evidencias/fase3_troca_projeto_reteste_manual.json), o agente chamou `consultar_projeto` para Alfa e depois Beta, inclusive nas perguntas “saldo dele”. Os dois retornaram `projeto_nao_encontrado`; consulta local somente leitura confirmou que o banco padrão tinha zero projetos operacionais. O reteste comprova a troca do referente, mas não consulta bem sucedida a projetos existentes nem cálculo de saldo.
