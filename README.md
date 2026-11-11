# estudos-engenharia-ia

Repositório para estudos, exercícios e projetos do MBA em Engenharia de IA,
Machine Learning e Deep Learning.

## Organização

- [Agentes Cognitivos com LangChain](./Agentes%20Cognitivos%20com%20LangChain/)
- [Arquiteturas Multiagentes com LangGraph](./Arquiteturas%20Multiagentes%20com%20LangGraph/)
- [Codex skills do projeto](./codex-skills/)

## Guia de estudo por exercício

Cada exercício abaixo indica o objetivo, os conceitos usados no código e o fluxo
para revisar. Os READMEs das pastas trazem os comandos de execução e os testes.

### [Aula 06-10 — Prompts, LLMs e primeiras chains](./Agentes%20Cognitivos%20com%20LangChain/aula%2006-10/)

#### [Assistente de oficina](./Agentes%20Cognitivos%20com%20LangChain/aula%2006-10/assistente%20oficina/)

Responder perguntas sobre serviços e horários usando o contexto fixo da oficina.

- **LLM com ChatOpenAI:** chamar o modelo de linguagem para gerar uma resposta.
- **Prompt e contexto:** `ChatPromptTemplate`, mensagens `system` e `human` e
  variáveis `{contexto}` e `{pergunta}` organizam regras e informações disponíveis.
- **Chain e LCEL:** `prompt | modelo` define as etapas; `invoke()` executa a
  pergunta e `.content` acessa a resposta. Cada pergunta usa só o contexto fixo,
  sem acumular histórico de conversa.

**Fluxo:** contexto + pergunta → prompt → LLM → resposta em texto.

#### [Organizar solicitações de suporte em lote](./Agentes%20Cognitivos%20com%20LangChain/aula%2006-10/organizar%20solicitacoes%20suporte%20em%20lote/)

Transformar mensagens livres em fichas com cliente, resumo e categoria.

- **Extração estruturada:** `BaseModel` e `Field` definem os campos da
  `FichaSuporte`; `with_structured_output()` retorna objetos nesse formato.
- **Prompt e chain:** `ChatPromptTemplate` orienta a extração e LCEL conecta
  o prompt ao modelo estruturado.
- **Processamento em lote:** `batch()` aplica a chain a várias mensagens;
  o código lê atributos como `ficha.cliente` e `ficha.categoria`.

**Fluxo:** lista de mensagens → batch da chain → lista de fichas estruturadas.

### [Aula 14-10 — Encadeamento e roteamento](./Agentes%20Cognitivos%20com%20LangChain/aula%2014-10/)

#### [Transformar reclamações de uma oficina em ações](./Agentes%20Cognitivos%20com%20LangChain/aula%2014-10/Transformar%20reclama%C3%A7%C3%B5es%20de%20uma%20oficina%20em%20a%C3%A7%C3%B5es/)

Resumir feedbacks, separar reclamações e elogios e consolidar um relatório geral.

- **Chains em etapas:** prompts diferentes para resumo, análise e consolidação;
  `StrOutputParser` transforma as respostas do modelo em texto.
- **LCEL e adaptação de entradas:** funções lambda preparam a saída de uma etapa
  para o próximo prompt e reúnem as análises com seus IDs.
- **Batch e consolidação:** `batch()` processa os relatos com concorrência
  limitada; `invoke()` gera o relatório sobre o conjunto de análises.
- **Validação e rastreabilidade:** Python confere o limite de palavras dos
  resumos e permite tentativas limitadas de correção; IDs permitem conferir
  as sugestões nos relatos originais.

**Fluxo:** feedbacks → resumos → análises individuais → relatório com ações.

#### [Encaminhar pedidos para o atendimento certo](./Agentes%20Cognitivos%20com%20LangChain/aula%2014-10/Encaminhar%20pedidos%20para%20o%20atendimento%20certo/)

Classificar uma mensagem de autopeças e encaminhá-la para vendas ou pós-venda.

- **Classificação com LLM:** um prompt produz o rótulo usado para escolher
  o atendimento; `StrOutputParser` extrai o texto da classificação.
- **Preservação da entrada:** `RunnablePassthrough` mantém a mensagem original
  junto do rótulo para a próxima etapa.
- **Roteamento entre chains:** `RunnableLambda` executa a função de decisão;
  Python normaliza e valida o rótulo antes de chamar a chain selecionada.

**Fluxo:** mensagem → classificação + texto original → rota → resposta da chain escolhida.

### [Aula 19-10 — Exemplos, validação e ferramentas de busca](./Agentes%20Cognitivos%20com%20LangChain/aula%2019-10/)

#### [Classificar feedbacks e validar a ficha](./Agentes%20Cognitivos%20com%20LangChain/aula%2019-10/Classificar%20feedbacks%20e%20validar%20a%20ficha/)

Classificar relatos de polaridade clara como positivos ou negativos e justificar
o resultado em uma ficha validada.

- **Few-shot prompting:** `FewShotChatMessagePromptTemplate` apresenta exemplos,
  incluindo ironia, para orientar a classificação sem treinar o modelo.
- **Esquema e parser:** `BaseModel`, `Field` e `field_validator` definem as
  restrições; `PydanticOutputParser` converte o texto em uma ficha validada.
- **Tratamento de falhas:** `OutputParserException` aciona uma única tentativa
  de reparo com saída inválida, erro, esquema e feedback original.
- **Estrutura e conteúdo:** uma ficha válida ainda precisa ter sentimento e
  motivo coerentes com o relato; o exercício confere também um gabarito.

**Fluxo:** feedback + exemplos → LLM → texto → validação → ficha ou reparo limitado.

#### [Consultar regras de uma loja e registrar a busca](./Agentes%20Cognitivos%20com%20LangChain/aula%2019-10/Consultar%20regras%20de%20uma%20loja%20e%20registrar%20a%20busca/)

Responder perguntas sobre regras da loja com uma ferramenta de busca na base local.

- **Embeddings e busca vetorial:** `OpenAIEmbeddings` representa textos por
  vetores; FAISS indexa as regras e `similarity_search()` recupera trechos por
  proximidade de sentido, com `k` e filtro por metadados.
- **Agente e ferramenta:** `create_agent` conecta `ChatOpenAI` a uma função
  `@tool`; o agente pede a busca e usa o retorno para responder com base nos trechos
  recuperados, em um fluxo de RAG.
- **Observação da execução:** callbacks de `BaseCallbackHandler` registram
  início e fim das ferramentas e gerações da LLM. Os logs permitem conferir
  o que foi buscado e se os trechos sustentam a resposta.

**Fluxo:** pergunta → agente → ferramenta de busca → trechos → resposta fundamentada.

### [Aula 21-10 — Memória, estado e continuidade](./Agentes%20Cognitivos%20com%20LangChain/aula%2021-10/)

#### [Preferências da oficina entre conversas](./Agentes%20Cognitivos%20com%20LangChain/aula%2021-10/Preferencias%20da%20oficina%20entre%20conversas/)

Guardar, consultar e excluir o canal de orçamento de cada usuário entre sessões.

- **Agente com ferramentas:** `create_agent`, `ChatOpenAI` e `@tool` permitem
  executar escrita, consulta e exclusão; closures fixam a identidade do usuário
  nas ferramentas, sem deixar o modelo escolher outro perfil.
- **Memória da conversa:** `MemorySaver` e `thread_id` separam o histórico
  de cada par usuário/sessão.
- **Perfil entre conversas:** um dicionário compartilhado usa namespace por
  usuário e a chave `canal_orcamento`; upsert substitui a preferência antiga.
- **Auditoria:** `date`, logs e inspeção do dicionário comprovam as operações.
  Histórico e perfil ficam somente em memória durante o processo.

**Fluxo:** mensagem → agente → ferramenta do usuário → store → resposta e auditoria.

#### [Agendar uma avaliação sem perder o contexto](./Agentes%20Cognitivos%20com%20LangChain/aula%2021-10/Agendar%20uma%20avaliacao%20sem%20perder%20o%20contexto/)

Coletar veículo, dia, horário e nome por turnos e preparar uma solicitação simulada.

- **Intenção e extração estruturada:** `BaseModel`, `Field` e `Literal` definem
  `agendar`, `cancelar` ou `duvida` e campos opcionais; `with_structured_output()`
  devolve a análise validada.
- **Contexto explícito:** `ChatPromptTemplate` recebe estado anterior e mensagem
  atual; a chain usa esses dados para preservar valores e extrair correções.
- **Estado e regras em Python:** um dicionário separa as sessões; funções aplicam
  atualizações, recalculam faltantes e tratam cancelamentos antes da confirmação.
- **Continuidade e limites:** uma correção pode mudar só o horário; dias como
  “terça-feira” continuam como texto. A confirmação é uma solicitação simulada,
  sem reserva real e sem persistência após reiniciar o programa.

**Fluxo:** estado + mensagem → extração → atualização em Python → pergunta ou solicitação simulada pronta.

### [Aula 26-10 — SQL, cálculo e busca de políticas com ferramentas](./Agentes%20Cognitivos%20com%20LangChain/aula%2026-10/)

#### [Conferir estoque e calcular um orçamento](./Agentes%20Cognitivos%20com%20LangChain/aula%2026-10/Conferir%20estoque%20e%20calcular%20um%20orcamento/)

Consultar produto e estoque em um catálogo fictício antes de calcular um orçamento.

- **SQLite e SQL gerado pela LLM:** `sqlite3` guarda o catálogo; o esquema no
  prompt descreve as colunas para o agente gerar a consulta SELECT.
- **Agente com ferramentas separadas:** `create_agent` e `@tool` expõem consulta
  e cálculo; o preço usado no orçamento deve vir da leitura do mesmo SKU.
- **Função determinística:** Python valida quantidade e multiplica inteiros em
  centavos. Produto sem estoque ou SKU inexistente não gera orçamento.
- **Barreiras e auditoria:** filtro didático, `query_only` e authorizer restringem
  operações no banco isolado. JSONL registra SQL, linhas, tool calls, argumentos,
  resultados e comparações de esperado/observado, incluindo tentativas de escrita.

**Fluxo:** pedido → agente → SELECT → conferência de estoque → cálculo Python → resposta e auditoria.

#### [Buscar uma regra sem inventar um benefício](./Agentes%20Cognitivos%20com%20LangChain/aula%2026-10/Buscar%20uma%20regra%20sem%20inventar%20um%20beneficio/)

Interpretar dúvidas coloquiais e recuperar políticas sem inventar benefícios ausentes.

- **Document e metadados:** cada política curta é um chunk com ID, fonte e domínio,
  permitindo citar o conteúdo útil e conferir sua origem.
- **Embeddings e busca com scores:** `OpenAIEmbeddings` e FAISS indexam uma vez;
  `similarity_search_with_score` retorna até dois trechos, com filtro opcional.
- **Reescrita pelo agente:** `create_agent` recebe instruções para transformar
  linguagem coloquial em `query_otimizada`, preservando a necessidade, e chama `@tool`.
- **Comparação e limites da recuperação:** original e reescrita usam o mesmo índice
  e k; os resultados reais ficam no JSONL. Distância não comprova benefício nem
  proibição, e ausência de melhoria na comparação também é registrada.

**Fluxo:** pergunta → reescrita → busca com metadados e scores → conferência de evidência → resposta com fonte ou ausência de informação.

### [Aula 28-10 — Duas fontes, memória e auditoria de respostas](./Agentes%20Cognitivos%20com%20LangChain/aula%2028-10/)

#### [Atendimento com duas fontes e memória](./Agentes%20Cognitivos%20com%20LangChain/aula%2028-10/Atendimento%20com%20duas%20fontes%20e%20memoria/)

Responder sobre produtos e retirada usando fontes distintas e manter o produto
identificado entre perguntas da mesma sessão.

- **SQLDatabaseToolkit e SQLite:** ferramentas SQL consultam preço e estoque;
  o schema pode incluir amostras com dados, que também pertencem à fonte SQL.
- **Retriever documental:** `Document`, `OpenAIEmbeddings` e FAISS indexam a
  política; `create_retriever_tool` expõe a busca com sua fonte ao agente.
- **Agente com memória:** `create_agent`, `MemorySaver` e `thread_id` preservam
  a conversa para resolver “desse produto”. O saldo atual exige nova consulta.
- **Trajetória por turno:** `HumanMessage` delimita o recorte; `AIMessage/tool_calls`
  e `ToolMessage` mostram só chamadas e retornos novos, preservando todo o histórico
  dentro da sessão. SQL executado e conferências ficam no JSONL.

**Fluxo:** mensagem + histórico da sessão → agente → fonte SQL e/ou documental → resposta e trajetória do turno atual.

#### [Auditor de frete para um orçamento](./Agentes%20Cognitivos%20com%20LangChain/aula%2028-10/Auditor%20de%20frete%20para%20um%20orcamento/)

Conferir números e conclusões de uma resposta usando regra e referência independentes.

- **Extração de afirmações:** `BaseModel`, `Field`, `Literal` e
  `with_structured_output` registram trechos, chaves canônicas, valores e unidades,
  incluindo conclusões e métricas sem mapeamento, sem fixar quantidade de afirmações.
- **Comparação em Python:** `Decimal` aplica diferença absoluta e tolerância
  somente a métricas equivalentes. Subtotal e total com frete não são intercambiáveis.
- **Avaliação lógica por LLM:** outra chain julga APOIA/REFUTA/NEUTRA com a regra
  completa; números certos não autorizam concluir frete grátis e prazo sem fonte
  permanece não verificado.
- **Relatórios separados:** auditoria numérica e lógica registram observações,
  justificativas e divergências. O gabarito fica fora dos prompts e falhas são preservadas.

**Fluxo:** resposta → extração estruturada → comparação numérica Python → avaliação lógica com fontes → relatórios e conferência.

### [Projeto final — Auto Super Parts CWB: fases 1 e 2](./Agentes%20Cognitivos%20com%20LangChain/Projeto%20final/)

Extrair intenção, veículo, peça, quantidade e CEP de uma mensagem, mantendo dados
ausentes desconhecidos e produzindo JSON validado com as pendências necessárias.

- **Templates e PTCF:** `PromptTemplate` e `ChatPromptTemplate` apresentam a mesma
  tarefa; a composição principal separa regras `system` do conteúdo `human`.
- **Schema e output parser:** `BaseModel`, `Field` e `PydanticOutputParser` validam
  a extração; Python normaliza formatos conhecidos e recalcula pendências por intenção.
- **@chain e LCEL:** duas composições da mesma transformação, demonstradas com
  `invoke` e `batch`, sem ferramentas nem memória nesta fase.
- **Código e evidências:** módulos `.py` são importados pelo notebook; testes
  locais e saídas simuladas são identificados separadamente das chamadas reais.

**Fluxo:** mensagem → template → LLM → parser/BaseModel → JSON ou erro tratado.
A fase 2 acrescenta **agente e ferramentas**: `create_agent` escolhe consultas
`@tool` ao SQLite e ViaCEP; Python calcula orçamento/frete em centavos com Decimal.
`BaseModel` valida argumentos e o modo estrito restringe o esquema enviado ao modelo.
Callbacks e mensagens AI/Tool registram esquema, argumentos e retornos; o notebook
distingue APIs reais de simulações. Destino sem distância mantém frete/prazo pendentes.
**Fluxo da fase 2:** mensagem → agente → consulta de catálogo/endereço → cálculo
determinístico → resposta com evidências e limites. As fases 3–5 continuam pendentes;
memória entre mensagens e RAG ainda não foram implementados.

### [Aula 04-11 — Avaliação de resposta e trajetória](./Agentes%20Cognitivos%20com%20LangChain/aula%2004-11/)

#### [O atendente consultou a política?](./Agentes%20Cognitivos%20com%20LangChain/aula%2004-11/O%20atendente%20consultou%20a%20politica/)

Avaliar separadamente a resposta sobre pagamento e a consulta de uma política fictícia.

- **Agente e ferramenta:** `create_agent`/`@tool`; cada `invoke` recebe uma pergunta isolada.
- **Trajetória observada:** mensagens AI/Tool registram chamadas e retornos com IDs; Python compara listas exatas, preservando ordem e repetições.
- **LLM juiz:** saída estruturada com critérios explícitos; oferecer consulta não equivale a responder. Uma fixture testa o próprio avaliador.
- **Conjunto e avaliação:** três referências independentes; `Client`/`evaluate` opcionais no LangSmith; tabela separa origem, notas e revisão humana.

**Fluxo:** casos → agente isolado → resposta + trajetória → notas separadas → revisão → tabela.

#### [Chat que lembra o veículo na sessão](./Agentes%20Cognitivos%20com%20LangChain/aula%2004-11/Chat%20que%20lembra%20o%20veiculo%20na%20sessao/)

Recordar o veículo fornecido pelo cliente na mesma conversa e pedir essa informação após limpar o contexto.

- **Interface de chat:** `st.chat_input` recebe mensagens e `st.chat_message` renderiza o histórico.
- **Estado de sessão:** `st.session_state` mantém mensagens entre reruns; Nova conversa limpa histórico, eventos e erros.
- **Contexto explícito:** `create_agent` recebe uma cópia de toda a conversa em `invoke(messages)`; somente a nova resposta é anexada.
- **Eventos e evidências:** callbacks reais do modelo, exportação de conversa e AppTest para verificar limpeza, duplicação e isolamento; simulação local identificada.

**Fluxo:** pergunta → histórico da sessão → agente → nova resposta → histórico. Isso não comprova memória após reiniciar.

## Conceitos para revisar

| Conceito | Significado neste repositório | Onde começar |
| --- | --- | --- |
| LLM | Modelo de linguagem chamado por `ChatOpenAI` para interpretar ou gerar texto. | Assistente de oficina, aula 06-10. |
| Prompt e contexto | Regras, dados e mensagem organizados como entrada do modelo. | Assistente de oficina, aula 06-10. |
| Chain e LCEL | Etapas conectadas por `\|`, com fluxo definido no código. | Assistente de oficina e relatório de reclamações. |
| Saída estruturada | Resposta organizada em campos de um esquema para o Python consumir. | Suporte em lote e avaliação simulada. |
| Parser e validação | Conversão da resposta e conferência dos tipos e restrições do esquema. | Classificar feedbacks, aula 19-10. |
| Roteamento | Escolha de uma chain a partir da classificação da mensagem. | Encaminhar pedidos, aula 14-10. |
| Agente e ferramenta | Ciclo em que o modelo solicita funções disponíveis e usa seus retornos. | Consulta de regras e preferências. |
| RAG | Recuperação de trechos de uma base para fundamentar a resposta do modelo. | Consultar regras, aula 19-10. |
| Reescrita e score vetorial | Reformulação fiel da consulta e inspeção das distâncias e documentos, sem tratar proximidade como verdade. | Busca de políticas, aula 26-10. |
| Histórico em interface de chat | Session State conserva mensagens entre reruns e as envia ao agente; limpar a conversa remove o contexto. | Chat do veículo, aula 04-11. |
| Memória e estado | Dados mantidos pela aplicação e reutilizados nas interações seguintes. | Os dois exercícios da aula 21-10. |
| Consulta SQL com LLM | Modelo escreve uma consulta a partir de um esquema; o código controla sua execução no banco fictício. | Estoque e orçamento, aula 26-10. |
| Cálculo determinístico | Função Python produz o total em centavos a partir do preço consultado e da quantidade válida. | Estoque e orçamento, aula 26-10. |
| Duas fontes com memória | Ferramentas distintas fornecem produtos e políticas; a conversa identifica o produto, e uma nova leitura atualiza seu saldo. | Atendimento, aula 28-10. |
| Avaliação de resposta e trajetória | Comparação exata de consultas e LLM juiz com critérios explícitos; fixtures avaliam o juiz sem inventar falhas do agente. | Atendente e política, aula 04-11. |
| Auditoria numérica e lógica | Valores são comparados com tolerância em Python; conclusões e cobertura são avaliadas separadamente contra fontes independentes. | Auditor de frete, aula 28-10. |

A pasta [Arquiteturas Multiagentes com LangGraph](./Arquiteturas%20Multiagentes%20com%20LangGraph/)
ainda não contém exercícios. Os conceitos acima correspondem aos projetos já
implementados em Agentes Cognitivos com LangChain.

## Observações

Os exercicios das aulas compartilham o arquivo `.env` na raiz deste repositorio,
ao lado deste README. Coloque `OPENAI_API_KEY` nele; nao crie copias nas aulas
ou nos exercicios. Os scripts localizam esse arquivo a partir de sua propria
localizacao, independentemente da pasta do terminal. Variaveis ja definidas no
ambiente tem prioridade. O `.env` e ignorado pelo Git e nao deve ser versionado.

O **Projeto final** usa configuração independente para permitir cópia isolada:
variável de ambiente primeiro e `.env` opcional dentro da pasta do próprio projeto.
Seu README documenta a criação da `.venv` e o registro do kernel desde o início.

Este repositorio deve crescer com anotacoes, exemplos de codigo e pequenos
projetos praticos. Cada aula pode ter sua propria pasta com README, codigo e
arquivos de apoio.

As skills em `codex-skills/` sao fontes versionadas. Para ficarem ativas no
Codex, elas tambem precisam existir em `C:\Users\Renan\.codex\skills`.

### Revisão do projeto final — consultas e respostas da fase 2 (08/11)

O [projeto Auto Super Parts](./Agentes%20Cognitivos%20com%20LangChain/Projeto%20final/)
passou a consultar entrega sem produtos e informações técnicas estruturadas com fontes.
A regra de frete é compartilhada com o orçamento. `ContextVar` mantém o pedido atual
no escopo da chamada para impedir troca de tipo de peça; proteções específicas impedem
recomendações de óleo sem especificação e preservam candidata/resultado na evidência.
Essas proteções não são RAG, NLI ou verificador geral. Os avisos repetitivos de simulação
foram retirados das respostas, mantendo a origem identificada nos registros técnicos.
Veja [falhas, correções e testes](./Agentes%20Cognitivos%20com%20LangChain/Projeto%20final/04_avaliacao_e_evidencias/resultados/CORRECOES_08_11.md).

### Prova AutoTools do projeto final — 08/11

Cliente HTTP com validação de Content-Type/JSON e tratamento de falhas; busca externa comparada com a configuração local e o mercado, sem inferir aplicação. As consultas reais não confirmaram cobertura dos quatro veículos. AutoTools permanece fora das ferramentas do agente; ViaCEP continua funcional. Veja a [evidência e os limites](./Agentes%20Cognitivos%20com%20LangChain/Projeto%20final/04_avaliacao_e_evidencias/resultados/PROVA_AUTOTOOLS_08_11.md).

### Base técnica manual do projeto final — 08/11

[Escopo, fontes e execução](./Agentes%20Cognitivos%20com%20LangChain/Projeto%20final/01_documentacao/BASE_TECNICA_MANUAL.md): consulta estruturada em JSON por configuração/assunto, com fontes e lacunas explícitas. Cinco veículos (quatro originais e uma S10 diesel), mantendo 24 produtos comerciais. Óleo diferencia norma e uso normal/severo; ViaCEP continua como API externa. Catálogos externos deixam o caminho ativo; memória, RAG e avaliação continuam na sequência planejada.

### Memória do projeto final — fase 3

[Guia e evidências](./Agentes%20Cognitivos%20com%20LangChain/Projeto%20final/01_documentacao/MEMORIA_FASE_03.md): janela de turnos realmente enviada a `invoke`, perfil confirmado em SQLite e recuperação vetorial de resumos autorizados, isolados por cliente. Nova conversa preserva dados salvos; esquecer apaga contexto curto/longo. CLI e notebook importam a mesma fachada do agente; sem autenticação ou resumo automático. Comparação documental LangMem/Mem0 e decisão por store local.

### RAG e text-to-query do projeto final — fase 4

[Guia, execução e evidências](./Agentes%20Cognitivos%20com%20LangChain/Projeto%20final/01_documentacao/RAG_FASE_04.md): políticas em índice FAISS preparado separadamente, reescrita/decomposição de consultas por LCEL/saída estruturada e resposta do agente com fontes. Pergunta de catálogo vira plano Pydantic e SELECT compilado com filtros permitidos; sem SQL livre. Memória permanece integrada. Comparação real antes/depois, falhas de trajetória/avaliação preservadas e notebook com fixtures identificadas.

### Projeto final — verificação por evidências

[Auto Super Parts: fase 5](./Agentes%20Cognitivos%20com%20LangChain/Projeto%20final/01_documentacao/VERIFICACAO_FASE_05.md). Regras em Python conferem valores e um juiz LLM classifica sustentação, contradição e falta de suporte. O ciclo permite um reparo, reavalia e grava somente a resposta final. A avaliação separa fixtures locais de chamadas reais; falhas do juiz são preservadas. É uma adaptação por LLM da verificação por inferência, sem alegar classificador NLI especializado.

## Projeto de disciplina atual

- [Secretária IA — Projeto final 2](./Agentes%20Cognitivos%20com%20LangChain/Projeto%20final%202/): projeto acadêmico atual; importação TXT/ZIP/SQLite, propostas com fontes, revisão persistente e visitas com agente, APIs externas e confirmação humana implementados. Os testes locais passaram (85 testes). Cadastro PJ completo pelo chat, vínculo com projetos/fontes, memória e relatórios continuam pendentes.
- [Auto Super Parts CWB](./Agentes%20Cognitivos%20com%20LangChain/Projeto%20final/): descontinuado em 09/11/2026; código, decisões e evidências preservados como histórico.


Secretária IA: [revisão persistente (início da fase 2)](./Agentes%20Cognitivos%20com%20LangChain/Projeto%20final%202/docs/revisao_persistente.md) e [notebook executado](./Agentes%20Cognitivos%20com%20LangChain/Projeto%20final%202/notebooks/03_revisao_persistente.ipynb). Decisão humana aceita/corrige/rejeita interpretações; não cria pagamentos/agenda. 72 testes locais.
