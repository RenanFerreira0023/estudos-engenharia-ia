# Fase 2 — orquestração observável da Secretária IA

O menu 9 usa `create_agent` com ferramentas `@tool` para consultar cliente, disponibilidade, ViaCEP e Minha Receita, além de criar **propostas**. Gravações definitivas exigem comandos de confirmação no serviço Python. Os retornos de ferramentas e as trajetórias reais já foram observados nos testes manuais descritos em [andamento](andamento_fases.md) e [execuções/falhas](execucoes_e_falhas.md).

## Escolha do orquestrador

| Opção | Papel neste projeto | Decisão |
|---|---|---|
| Chain LCEL / `@chain` | Etapas fixas de extração e validação estruturada; executadas nos notebooks 02 e 03. | Usada onde a sequência é conhecida. |
| LangChain `create_agent` | O modelo escolhe chamadas de ferramentas conforme o pedido, com ciclo de mensagens AI/Tool. | Usado no atendimento porque a ordem das consultas varia. |
| Grafo LangGraph escrito à mão | Permite explicitar nós e transições quando o fluxo exigir controle mais detalhado. | Não implementado aqui: propostas e confirmações já têm limites no serviço, e o agente atual é pequeno. |

Segundo a [documentação oficial da LangChain](https://docs.langchain.com/oss/python/learn), os agentes LangChain usam primitivas LangGraph e um grafo próprio é opção para personalização mais profunda. Esta é uma comparação de arquitetura e escolha, não um experimento de desempenho entre bibliotecas.

## Prompt e decisão

`montar_prompt_agenda()` separa **Pessoa, Tarefa, Contexto/regras e Formato** (PTCF). Exemplos curtos ensinam que ausência de cliente exige pergunta, CNPJ exige conferência local, e proposta de visita não é confirmação. Isso é few-shot no prompt. O executor registra chamadas e observações; não lê nem publica pensamentos internos do modelo. A identidade no prompt é apenas contexto de demonstração: autorização real do protótipo está no serviço SQLite.

`roteador_pedido` é uma etapa `RunnableLambda` chamada antes do agente. Classifica o pedido como `visita`, `cliente` ou `geral`; pergunta explícita prevalece e seguimento curto pode herdar a rota anterior. A rota é uma **dica**, não um filtro de ferramentas ou autorização. O agente ainda decide qual `@tool` usar, e as ferramentas verificam dados e permissões. Esta é uma adaptação funcional de roteamento; **não implementa literalmente `RouterChain`**. Uma troca de assunto ambígua pode ser classificada de forma imperfeita, por isso a rota não bloqueia ferramentas.

As ferramentas `buscar_cliente` e `consultar_disponibilidade` aplicam consultas e regras determinísticas sobre SQLite; `consultar_cep_viacep` e `consultar_cnpj_minha_receita` adaptam respostas de APIs externas; o modelo interpreta o pedido e escolhe a próxima ferramenta. Não atribuímos raciocínio semântico ao SQL ou à validação de CEP/CNPJ. Consulta externa não grava cadastro por conta própria.

## Logging e limites

`RastroAgente` é um `BaseCallbackHandler` passado em `agent.invoke(config=...)`. Registra início, fim e falha de modelo/ferramenta, com instante, ID da execução e nome da ferramenta. O arquivo privado `dados/privados/rastros_agente.jsonl` guarda esses **metadados** por conversa e usuário. Argumentos, retornos, perguntas e respostas não entram nesse arquivo. O terminal ainda mostra chamadas e retornos para estudo; não copie dados reais desse terminal para o Git. O callback prova que eventos ocorreram, mas não julga se a resposta estava correta. LangSmith e avaliação de resposta/trajetória continuam pendentes.

O [notebook 05b](../notebooks/05b_orquestracao_agente.ipynb) reproduz prompt, rota e callback sem API. No [reteste real](../evidencias/fase2_roteamento_callback_manual.json), a pergunta sobre Alfa produziu rota `cliente`, chamada `buscar_cliente`, resposta sustentada pelo retorno e seis eventos do callback; o rastro privado foi conferido. Isso valida esse percurso, não a qualidade geral do agente. A fase 2 mantém pendências de integração e dos requisitos que dependem de FAISS ou avaliação.
