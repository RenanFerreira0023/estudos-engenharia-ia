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
| Memória e estado | Dados mantidos pela aplicação e reutilizados nas interações seguintes. | Os dois exercícios da aula 21-10. |

A pasta [Arquiteturas Multiagentes com LangGraph](./Arquiteturas%20Multiagentes%20com%20LangGraph/)
ainda não contém exercícios. Os conceitos acima correspondem aos projetos já
implementados em Agentes Cognitivos com LangChain.

## Observações

Todos os exercicios compartilham o arquivo `.env` na raiz deste repositorio,
ao lado deste README. Coloque `OPENAI_API_KEY` nele; nao crie copias nas aulas
ou nos exercicios. Os scripts localizam esse arquivo a partir de sua propria
localizacao, independentemente da pasta do terminal. Variaveis ja definidas no
ambiente tem prioridade. O `.env` e ignorado pelo Git e nao deve ser versionado.

Este repositorio deve crescer com anotacoes, exemplos de codigo e pequenos
projetos praticos. Cada aula pode ter sua propria pasta com README, codigo e
arquivos de apoio.

As skills em `codex-skills/` sao fontes versionadas. Para ficarem ativas no
Codex, elas tambem precisam existir em `C:\Users\Renan\.codex\skills`.
