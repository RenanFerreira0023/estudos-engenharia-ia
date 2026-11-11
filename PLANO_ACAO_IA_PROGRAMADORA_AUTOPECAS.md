# Plano de ação — Auto Super Parts CWB

> **PLANO DESCONTINUADO — 09/11/2026.** Preservado para estudo. O plano vigente é [Secretária IA](./Agentes%20Cognitivos%20com%20LangChain/Projeto%20final%202/PLANO_PROJETO_SECRETARIA_IA.md). Não continuar autopeças nem reaproveitar regras do domínio por padrão.

> Instruções para a IA programadora. Revisão de escopo de 08/11/2026: base manual e manutenção básica.
> Continue o projeto existente. Não recomece do zero, não duplique a implementação e não declare requisitos atendidos sem evidência.

## 1. Missão e forma de trabalhar

Construir e concluir um assistente conversacional de uma autopeças fictícia em Curitiba. Renan utiliza IA para programar e precisa compreender e defender as decisões. Explique cada incremento em linguagem simples: o que faz, por que existe, como executar e como verificar.

Antes de alterar código, leia as instruções do repositório, os documentos do projeto, o enunciado disponível e as dependências instaladas. Faça um inventário do estado atual por requisito, com caminhos reais dos arquivos e evidências. Não confunda arquivo existente com funcionalidade executada.

Execute incrementos na ordem deste plano, aproveitando tudo que já estiver correto. Resolva decisões rotineiras autonomamente; pergunte apenas quando faltar uma decisão de negócio, credencial ou informação indispensável. Não substitua regras pendentes por suposições silenciosas. Não remova validação para fazer um teste passar.

Este documento é um plano de implementação e verificação, não uma afirmação de que o sistema já está pronto. O enunciado e as orientações verificáveis do professor têm precedência em caso de conflito. Registre divergências.

## 2. Produto e limites

O usuário é um cliente leigo ou experiente. O assistente deve:

- Identificar intenção, peça, quantidade e dados do veículo necessários à consulta.
- Perguntar pelos dados faltantes ou ambíguos antes de afirmar aplicação.
- Consultar aplicações, preço e estoque no catálogo local fictício.
- Calcular orçamento com regras determinísticas.
- Consultar CEP e estimar entrega com regras da loja.
- Consultar políticas documentais via RAG, mostrando a fonte.
- Consultar a base técnica manual em JSON, com fontes por veículo, assunto e condição de uso. Não depender de APIs de catálogo, busca Algolia de lojas ou scraping para atender.
- Manter contexto entre turnos e recuperar dados confirmados em outra sessão.
- Verificar respostas e registrar/avaliar sua execução no LangSmith.
- Oferecer uma interface Streamlit.

Fora desta entrega: diagnóstico por sintomas, procedimentos de reparo, compra ou pagamento real, WhatsApp, implantação comercial, estoque de fornecedores, catálogo externo dinâmico e múltiplos agentes. Essas possibilidades ficam documentadas como evolução.

## 3. Decisões já tomadas

### Stack e organização

- Python com lógica modular em `.py`.
- Notebooks demonstrativos importando essa mesma implementação; sem segunda versão da lógica.
- LangChain como framework principal.
- OpenAI: chat `gpt-4o-mini`; embeddings `text-embedding-3-small`.
- SQLite para catálogo e persistência estruturada quando apropriado.
- FAISS para recuperar políticas em índice previamente preparado.
- Memória com controle por sessão e cliente; estratégia detalhada abaixo.
- Streamlit para interface. LangSmith para tracing e avaliação: ambos são escolhas explícitas de Renan.
- Preservar a estrutura de pastas atual. Localizar os diretórios reais antes de escrever; não reorganizar o repositório inteiro.
- Fixar versões compatíveis e documentar comandos que funcionem no ambiente do projeto.

### Regras da loja

- Loja fictícia Auto Super Parts CWB, em Curitiba; Museu Oscar Niemeyer como referência geográfica fictícia, sem associação real.
- Frete grátis para Curitiba/PR.
- Fora de Curitiba: frete proporcional de R$ 8,85 por 200 km, sem arredondar quilômetros em blocos para o preço.
- Calcular em Decimal/centavos, com arredondamento monetário explícito. Exemplo: 250 km → R$ 11,06 usando ROUND_HALF_UP.
- Prazo externo: 2 dias úteis por bloco de 100 km, arredondando para cima. Exemplo: 250 km → 6 dias úteis.
- Distâncias atuais são simuladas e devem aparecer assim: Curitiba 0 km; São José dos Pinhais 25 km; Ponta Grossa 120 km; Guarapuava 250 km; Londrina 400 km. Conferir os arquivos existentes e resolver inconsistências antes de alterar dados.
- Município/UF sem distância cadastrada: informar que não é possível cotar. Não retornar frete zero nem inventar distância.
- ViaCEP fornece endereço; não fornece distância, frete nem prazo.
- Site: Pix antecipado. Balcão: Pix ou dinheiro. Não há pagamento ao entregador, cartão ou parcelamento.
- Não implementar processamento de pagamento.
- Confirmar com Renan o prazo de Curitiba e o início da contagem do prazo; não criar essas regras silenciosamente. Datas exatas exigem calendário de dias úteis e regras explicitadas; até lá, apresentar estimativa em dias úteis.
- Preservar as demais políticas já aprovadas nos documentos. Se troca/garantia estiverem incompletas, perguntar em vez de inventar.

### Catálogo e aplicação

Manter os 24 produtos comerciais didáticos e os quatro veículos originais: Gol 2010 1.0 8V flex, Palio 2010 1.0 Fire 8V flex, Celta 2012 1.0 8V flex e Fusca 1982 1600 a ar, gasolina. Incluir somente um recorte adicional diesel: Chevrolet S10 2014 2.8 CTDI, com manual oficial brasileiro disponível. A S10 pode ter informação técnica sem produto/preço/estoque cadastrado. Não ampliar para Chevette, Corsa Wind, Jetta ou Fusca TSI; eles foram apenas sondagens de fontes externas. Preservar IDs e dados comerciais existentes.

- Preços, estoque e aplicações são fictícios para o exercício e precisam ser identificados como tais.
- Não apresentar cadastros fictícios como homologação real de fabricante.
- Consultar aplicação exata e perguntar por dados realmente necessários à peça.
- Não inventar versão, número de válvulas, combustível, referência de fabricante ou código original.
- No planejamento, P003 custa R$ 18,50; duas unidades → R$ 37,00. P023 existe com estoque zero. Confirmar esses dados no arquivo atual antes de usá-los como referência de teste.
- Preservar as particularidades cadastradas do Fusca; não sugerir correia dentada para o motor clássico a ar.
- Óleo: não preencher viscosidade, norma ou capacidade ausentes por suposição. Exigir fonte aplicável ao veículo/motor/mercado.

## 4. Estado anterior informado — precisa de auditoria atual

No último relato da implementação:

- Fase 1: 23 testes locais aprovados e extração real de veículo/peça/quantidade.
- Fase 2: SQLite com consultas parametrizadas, orçamento em centavos, ViaCEP real, quatro ferramentas, terminal e logs; 15 testes locais aprovados.
- Exemplos reais relatados: P003 × 2 → R$ 37,00; P023 reconhecido sem estoque; ViaCEP com endereço retornado.
- Falha conhecida: orçamento com entrega rejeitou argumento extra `minItems` enviado pelo modelo.
- Faltavam concluir o notebook da fase 2, dependências e reprodução em ambiente novo.

Esses números são históricos, não resultados desta execução. Verifique o estado atual e reporte o que foi confirmado. Não avance sobre uma falha conhecida sem diagnóstico e evidência da correção.

## 5. Fluxo do atendimento-alvo

1. Streamlit recebe a mensagem e identifica sessão/cliente de demonstração.
2. Recupera o contexto curto e as memórias relevantes autorizadas daquele cliente.
3. O agente interpreta intenção e entidades com contratos validados.
4. Se faltar dado necessário, pergunta e aguarda a próxima mensagem.
5. Se houver dados, escolhe a ferramenta pertinente.
6. Recebe o resultado e decide se precisa de outra ferramenta ou esclarecimento.
7. Produz uma resposta candidata acompanhada das evidências utilizadas.
8. Verifica números, regras, suporte factual e coerência.
9. Se houver falha, tenta correção limitada com a evidência; se persistir, responde com limitação explícita, sem entrar em loop.
10. Apresenta a resposta, atualiza o histórico e persiste somente memórias apropriadas/confirmadas.
11. LangSmith registra a execução e permite avaliar qualidade e trajetória.

As ferramentas não precisam ser todas chamadas em toda mensagem. Uma saudação não precisa de banco. Uma política de pagamento não precisa de motor/ano. Um orçamento não pode ser calculado com preço inventado.

## 6. Base manual: especialidade e curadoria técnica

Decisão de Renan em 08/11: retirar integração de catálogo externo do caminho ativo. As provas AutoTools e catálogos públicos ficam apenas como histórico, sem requisito de integração ou trabalho adicional para tentar fazê-las passar. ViaCEP continua como a API externa real já demonstrada.

### Especialidade do atendente

Óleo e manutenção básica, freios, pneus, velas, correia dentada, correias de acessórios e alternador, dentro dos cinco recortes cadastrados. Não assumir que todas as categorias se aplicam a todos os carros. Distinguir Fusca a ar de versões modernas, ignição flex/gasolina de aquecimento diesel e correia dentada de acessórios.

O agente primeiro identifica o veículo, consulta a base e faz as perguntas pertinentes ainda não respondidas. Exemplos: eixo e tipo do freio; medida/carga e rodas originais para pneus; equipamentos e referência instalada para alternador/correia externa; motor exato, combustível e uso para óleo. Se faltar evidência, informa o campo pendente em vez de completar com conhecimento geral.

### Estrutura e origem

- `veiculos.json`: identidade e configuração. `produtos.json` e `aplicacoes.json`: dados comerciais didáticos preservados.
- `conhecimento_tecnico.json`: dados técnicos por veículo/assunto, especificações, perguntas necessárias, status, fontes, localização no documento e data da consulta.
- `fontes.json`: URL, edição/mercado e limites de cada referência. Priorizar manual do proprietário brasileiro e catálogo oficial do fabricante.
- `catalogo_auto_super_parts_cwb.json`: visão agregada sincronizada com os arquivos acima, sem uma segunda cópia divergente.
- Separar `verificado_manual`, referência parcial, regra de modelagem e `pendente`; `null` significa desconhecido. Fonte genérica ou de outro ano/motor não valida a configuração.
- A recomendação técnica do manual não certifica o óleo/peça fictícia à venda. Não preencher atributo de produto ou `validada_para_uso_real` automaticamente.

### Óleo e periodicidade

Registrar viscosidade SAE, norma/homologação, capacidade com/sem filtro quando confirmada e intervalos em km e meses, valendo o primeiro limite. Manter intervalos por norma do óleo quando o manual diferenciar. Não responder com média genérica de troca: distinguir uso normal e severo, perguntar pela rotina e preservar ressalvas.

Se não houver identificação técnica suficiente ou o manual aplicável não estiver confirmado, manter viscosidade, litros e prazo pendentes. Capacidade é referência de serviço, não autorização para completar sem medir o nível. Não inferir vida útil universal de pneus, pastilhas e lonas em km. Para correias e velas, conferir visualmente os quadros antes de transcrever as colunas do PDF.

### Critérios de aceite deste incremento

1. Consultar óleo verificado do Celta e diferenciar uso normal/severo.
2. Consultar S10 diesel e diferenciar normas/intervalos, sem usar a regra do motor flex.
3. Manter óleo do Fusca clássico e demais lacunas como pendentes sem fonte aplicável.
4. Retornar perguntas de freios, pneus, velas, correias e alternador sem inventar aplicação.
5. Impedir que uma fonte de outro veículo/ano libere recomendação de óleo; preservar fontes na resposta e trajetória.
6. Comprovar que P003, P023, preços, estoque e frete anteriores continuam corretos.

Esta base é curada manualmente. Não é RAG, consulta online de peças, certificação de instalação ou garantia de cobertura total. A falha das fontes externas não altera os demais requisitos acadêmicos.

## 7. Plano incremental de implementação

### Incremento 0 — inventário e mapa de requisitos

- Ler arquivos atuais, dependências, documentação e evidências.
- Mapear os 29 itens da seção 10 e as quatro entregas.
- Marcar cada item: não iniciado, parcial, implementado sem evidência ou demonstrado.
- Para cada status, citar arquivo e teste/saída quando existirem.
- Identificar divergências entre o texto antigo da rubrica e as orientações da última aula.
- Não calcular porcentagem concluída sem critério explícito e auditoria. 29/29 planejados não é nota nem progresso real.

**Saída:** inventário curto, lacunas e sequência dos próximos incrementos.

### Incremento 1 — fechar a base e a fase 2

- Preservar a chain inicial e os exemplos de composição.
- Diagnosticar o argumento `minItems`: schema exposto, argumentos gerados, conversão de tipos e validação. Não assumir a causa sem reproduzir.
- Corrigir a causa e adicionar regressão significativa para o orçamento com entrega.
- Validar quantidade positiva, produto inexistente, estoque insuficiente e cidade não coberta.
- Garantir que duas unidades de P003 retornem o total esperado se o preço atual for o documentado.
- Completar/executar o notebook da fase 2 e dependências.
- Concluir e verificar a curadoria manual da seção 6. Provas externas anteriores permanecem históricas e não bloqueiam o avanço.
- Iniciar tracing LangSmith desde esta fase, quando credencial estiver disponível.

**Concluído quando:** caminho de consulta/orçamento/entrega e consulta técnica local funciona, falhas são tratadas, fontes e campos pendentes são preservados e há evidências reais e simuladas identificadas, com instruções reproduzíveis.

### Incremento 2 — memória curta e longa

- Separar `session_id` e `cliente_id`; a interface deve explicar que se trata de identidade de demonstração, sem fingir autenticação real.
- Manter contexto na mesma sessão e passá-lo ao agente; histórico apenas visual não basta.
- Persistir veículo confirmado por cliente e permitir consultar, corrigir e excluir esse dado.
- Definir política de janela: limite de mensagens/tokens ou resumo e recuperação de memória relevante.
- Para contemplar o requisito de memória aumentada, planejar recuperação vetorial de resumos úteis, isolada por cliente. Não confundir o índice de memória com o índice das políticas.
- Documentar CoALA: memória semântica, episódica e procedural com exemplos do domínio; declarar o que é de fato implementado.
- Comparar pelo menos duas ferramentas especializadas, como LangMem e Mem0, por arquitetura/caso de uso e justificar adoção ou solução própria. Não instalar ambas só para constar.

**Concluído quando:** conversa multi-turno mantém veículo, outra sessão recupera dado confirmado, correção/exclusão funcionam e outro cliente não recebe a memória anterior. Explicar como a janela e a recuperação foram usadas.

### Incremento 3 — RAG e consultas estruturadas

- Preparar o índice de políticas em etapa separada e reprodutível; carregar índice existente durante o atendimento, evitando reindexar a cada pergunta.
- Usar `text-embedding-3-small` e FAISS conforme arquitetura aprovada, preservando documentos-fonte e metadados.
- Recuperar trechos para pagamento, entrega, troca e garantia apenas quando documentadas.
- Resposta sem evidência suficiente deve assumir limitação.
- Encontrar uma falha REAL de recuperação, inspecionar os documentos retornados e aplicar transformação de consulta pertinente: reescrita, múltiplas consultas ou outra técnica justificada.
- Comparar antes/depois na mesma pergunta, sem inventar falhas nem manipular dados para declarar melhora.
- Implementar text-to-query de forma restrita e verificável. A pergunta deve ser traduzida em consulta executável; apenas ter SQL parametrizado não prova essa capacidade.
- Preferir consulta estruturada por contrato validado e compilação segura, documentando o alcance. Se gerar SQL, restringir a SELECT, tabelas/colunas permitidas, parâmetros, limite de linhas e banco de leitura. Justificar a escolha e sua relação com a rubrica.

**Concluído quando:** políticas têm fontes verificáveis; há falha de RAG diagnosticada/corrigida com evidências; pergunta → consulta → resultado é demonstrado para dados estruturados.

### Incremento 4 — verificação dentro do agente

- Conferir valores e regras com funções determinísticas.
- Verificar afirmações da resposta em relação às evidências das ferramentas/documentos.
- Cobrir sustentação, contradição e ausência de suporte; avaliar coerência entre premissas e conclusão.
- O enunciado descreve inferência de linguagem natural/NLI. Escolher e justificar a implementação concreta, diferenciando classificador/modelo NLI, juiz LLM e checagens determinísticas. Não declarar equivalência automática nem chamar comparação de números de NLI.
- Se adaptar a abordagem para seguir o exemplo da aula, documentar explicitamente a adaptação e o que ela cobre/não cobre.
- Limitar tentativas de correção e impedir resposta final assertiva sem suporte.
- Avaliar o próprio verificador com casos sustentados, contraditórios e sem informação.

**Concluído quando:** uma resposta inválida é identificada dentro do fluxo real, corrigida ou substituída por uma limitação apropriada, e as decisões são registradas.

### Incremento 5 — interface Streamlit e agente único

- Construir uma interface mínima de chat usando o mesmo serviço Python dos notebooks/terminal.
- Recursos: enviar mensagem, nova conversa, identificação de demonstração, confirmação/correção/exclusão de veículo salvo e painel de evidências.
- Painel: fontes utilizadas, ferramentas chamadas, resultado da verificação e referência do trace quando disponível.
- Não expor segredos nem prompts técnicos desnecessários ao cliente. O painel de demonstração pode explicar dados fictícios e limitações.
- Diferenciar “nova conversa” de “apagar memória persistida”.
- Consolidar catálogo, orçamento, políticas, APIs e memórias em um único agente integrador.
- Demonstrar pelo menos duas categorias de ferramenta no mesmo atendimento composto.

**Concluído quando:** o usuário consegue realizar o atendimento pela interface, com memória real, chamadas verificáveis e tratamento de erros, sem duplicação de lógica.

### Incremento 6 — avaliação LangSmith e fechamento

- Criar dataset de pelo menos 15 casos iniciais propostos, ampliando se necessário: catálogo, orçamento, políticas, APIs e contexto/verificação.
- Incluir diálogos completos para memória, separação de clientes e uma avaliação separada da persistência entre sessões.
- Avaliar qualidade da resposta e trajetória das ferramentas separadamente.
- Conferir ferramentas, argumentos e dependências de ordem; não exigir uma sequência única quando trajetórias diferentes forem válidas.
- Incluir erros esperados e respostas de limitação corretas. “Não há dado” pode ser um sucesso de comportamento.
- Usar métricas determinísticas para números e contratos; avaliação semântica com critérios explícitos para texto.
- Revisar falsos positivos do avaliador: dizer “vou consultar” não comprova consulta executada.
- Comparar uma versão inicial e uma corrigida no mesmo conjunto, registrando mudanças e limitações.
- Registrar latência/tokens/custos somente se disponíveis e realmente medidos; não fabricar métricas.
- Revisar dependências, execução em ambiente novo, `.env.example`, README e modo dummy identificado.
- Consolidar as quatro entregas da seção 11.

**Concluído quando:** agente final executável, resultados reais acessíveis, análise de falhas e documentação suficiente para reprodução e defesa.

## 8. Onde entram os conceitos das aulas

| Conceito | Aplicação e evidência no projeto |
|---|---|
| `BaseModel` / Pydantic | Contratos de intenção, veículo, ferramenta e orçamento; sucesso e rejeição de entrada inválida. Não é o modelo de linguagem. |
| `PromptTemplate` / `ChatPromptTemplate` | Templates reutilizáveis demonstrados na fase 1; regras e mensagens do agente. |
| PTCF | Persona, Task, Context e Format descritos no prompt e explicados no relatório. |
| Zero-shot | Versão de instruções sem exemplos, se usada como referência de comparação. |
| One-shot | Um exemplo de entrada/saída; alternativa didática, não etapa obrigatória nem algo que precise coexistir em produção. |
| Few-shot | Alguns exemplos relevantes para ambiguidades e dados faltantes. Comparar com baseline quando útil e justificar. Não colocar dezenas de exemplos sem necessidade. |
| Output parser | Saída estruturada com tratamento de erros; distinguir parser, validação estrutural e verificação factual. |
| Runnable | `invoke` e `batch`; `stream` quando fizer sentido e for demonstrado, ou justificar sua ausência. |
| LCEL e `@chain` | Mostrar ambos no incremento inicial e justificar o padrão adotado, sem manter duas aplicações finais. |
| Chains sequenciais/paralelas | Compor etapas pertinentes; paralelizar apenas consultas independentes, sem romper dependências. |
| Roteamento | Escolha dinâmica de caminhos/ferramentas com exemplos e justificativa da implementação atual. |
| ReAct / ciclo do agente | Decisão observável de ferramenta, execução, observação e continuação; trace real. |
| Tools / function calling | Nome, descrição, contrato validado, lógica, erros, retorno e chamadas reais. |
| Memória / CoALA | Sessão, dado confirmado persistido, recuperação contextual e estratégia explicada. |
| Embeddings / FAISS / RAG | Busca semântica com fontes, índice existente, falha real e correção. |
| Text-to-query | Pergunta traduzida em consulta restrita e executada; demonstrar a tradução. |
| Callbacks / tracing | Entradas, chamadas, retornos, erros e saídas observáveis. |
| Verificação factual / coerência | Resposta conferida contra evidências dentro do atendimento, com alcance documentado. |
| LangSmith | Dataset, experimentos, qualidade, trajetória e análise comparativa. |

Não adicionar um conceito apenas para mencioná-lo. Exemplos no prompt (few-shot) são diferentes de casos de avaliação no dataset. Não solicitar nem apresentar pensamentos internos do modelo; justificar decisões usando chamadas, argumentos, evidências e resultados observáveis. Se a rubrica usar “chain-of-thought”, explicar a abordagem de transparência observável adotada, sem alegar acesso ao raciocínio privado.

## 9. Atualizações do professor e métodos legados

Na aula de 04/11/2026, aproximadamente 00:13–00:17, o professor explicou que prioriza conceitos, funcionamento e capacidade de explicar, sem exigir literalmente métodos antigos. Citou executor, histórico e alternativas de implementação. Isso não é dispensa geral dos requisitos.

- Não instalar versões antigas só para exibir `initialize_agent`, `RouterChain`, `ConversationBufferMemory`, `create_openai_tools_agent`, `AgentExecutor` ou `RunnableWithMessageHistory`.
- Verificar a documentação e as versões atuais do ambiente antes de escolher a API de implementação.
- Para cada substituição, registrar o método citado na rubrica, o componente adotado e a equivalência funcional demonstrada.
- Se persistir ambiguidade relevante que a aula não resolva, apontar a lacuna, sem declarar atendimento integral.
- Streamlit e LangSmith serão usados por decisão de Renan, mesmo com a flexibilidade mencionada na aula.

## 10. Matriz de conferência dos 29 itens

Use esta matriz como checklist de evidência, não como confirmação de conclusão. A rubrica original disponível no repositório deve ser conferida para a redação exata.

| # | Requisito | Evidência a produzir ou localizar |
|---|---|---|
| 01 | Anatomia, arquitetura e maturidade | Componentes do domínio, classificação e evolução inicial/final. |
| 02 | Planejamento e memória aumentada | Tarefa decomposta, memórias e estratégia de recuperação. |
| 03 | Templates reutilizáveis | Código e notebook com template de texto/chat. |
| 04 | Parser JSON | Saída real validada e tratamento de erro. |
| 05 | Runnable e composição imperativa | `invoke`, `batch`, `@chain`; uso/justificativa de `stream`. |
| 06 | LCEL e escolha de composição | Ambas as formas e justificativa técnica. |
| 07 | Comparar orquestradores | Pelo menos dois, com critérios objetivos e decisão. |
| 08 | Agente com ferramentas, memória e ReAct | Trace do ciclo e equivalência documentada ao método legado. |
| 09 | Composição e roteamento dinâmico | Fluxos pertinentes e demonstração da escolha de caminho; adaptação justificada. |
| 10 | API real via function calling | Chamada do agente, argumentos, retorno real e falhas tratadas. |
| 11 | PTCF, few-shot e transparência da decisão | Prompt, exemplos e evidências observáveis; adaptação descrita para CoT. |
| 12 | Confiabilidade | Parser/erros, memória, busca FAISS, callbacks e justificativas. |
| 13 | CoALA e tipos de memória | Estratégia aplicada ao domínio e limites. |
| 14 | Janela e recuperação vetorial | Limite/resumo combinado à busca de memória relevante, com teste. |
| 15 | Comparação de ferramentas de memória | Pelo menos duas, arquitetura, caso de uso e decisão. |
| 16 | Chatbot com buffer/contexto | Multi-turno e equivalência funcional ao método legado. |
| 17 | Intenção e entidades | Entrada real, extração e roteamento/fluxo correspondente. |
| 18 | Consulta complexa multi-turno | Diálogo real com contexto e decomposição. |
| 19 | Tipos de ferramenta | Documentar função fixa, semântica, API e text-to-query. |
| 20 | Integração de APIs | Cliente HTTP robusto e uso real adequado ao domínio. |
| 21 | Text-to-query | Pergunta → consulta executável restrita → resultado. |
| 22 | Recuperação sobre índice existente | Carregamento do índice FAISS e fontes recuperadas. |
| 23 | Falha real de RAG e correção | Pergunta, documentos antes/depois e técnica justificada. |
| 24 | Consistência factual e coerência | Verificador no fluxo, casos de erro e alcance da inferência. |
| 25 | Agente integrador | Duas ou mais categorias de ferramenta no mesmo atendimento. |
| 26 | Executor do agente | Construção atual e equivalência às classes solicitadas. |
| 27 | Histórico integrado | Contexto realmente consumido pelo agente final. |
| 28 | Streamlit | Interface funcional usando a mesma implementação. |
| 29 | Avaliação LangSmith | Qualidade e trajetória, métricas disponíveis e conclusões. |

Meta: contemplar os 29 itens, com adaptações justificadas conforme a orientação do professor. Não prometer 100% de nota. Pesos e julgamento acadêmico não são deduzidos desta contagem.

## 11. Quatro entregas finais — diferentes das cinco fases

1. **Código/notebook completo:** organizado, reproduzível, com dependências e instruções. `.py` + notebook(s) importando a lógica. Dummy funcional claramente identificado para avaliação sem credenciais; execução real também precisa de evidência.
2. **Relatório técnico PDF:** problema, arquitetura, decisões por fase, resultados, comparação, limitações, melhorias, fontes, evidências e declaração de uso de IA. Padrão do enunciado: `nome_sobrenome_ai-agents_langchain-agents.pdf`.
3. **Registro de avaliação LangSmith:** dataset/experimentos, qualidade e trajetória, resultados e análise acessíveis ao professor. Não depender apenas de print sem contexto.
4. **Vídeo:** tela e webcam de Renan, interação com agente em execução, decisão/chamada real de ferramenta e API externa, memória entre turnos e explicação das escolhas. Preparar roteiro de demonstração; não simular uma execução real com texto pré-escrito.

O texto original indicava 09/11/2026; em 04/11, por volta de 01:35:23, o professor anunciou entrega em 13/11/2026. Confirmar o prazo/horário vigente no ambiente acadêmico. A fala não informou horário final.

## 12. Registro de decisões, falhas e commits

Aproveitar o registro de decisões já existente. Para cada mudança relevante, guardar:

- Problema ou requisito.
- Decisão e alternativa considerada.
- Motivo técnico ou de negócio.
- Teste executado, ambiente e resultado observado.
- Evidência antes/depois quando houver correção.
- Limitação remanescente e referência do commit, se disponível.

Não é necessário diário de cada linha. Falhas reais devem ser preservadas, não apagadas para o histórico parecer perfeito. Diferenciar relato antigo, teste local simulado, teste de integração e chamada real.

Propor commits por incremento coerente depois dos testes pertinentes; verificar diff, segredos e arquivos gerados antes de commitar. Não fazer push ou publicar sem instrução. Não versionar `.env`, chaves, ambiente virtual ou caches. Não apagar trabalho do usuário.

## 13. Reprodução e critérios de aceite gerais

- README com instalação, ambiente, modelos, modo real/dummy e comandos corretos a partir de uma pasta explicitada.
- `.env.example` apenas com nomes de variáveis e placeholders; nunca imprimir chave.
- Não pedir a Renan que cole segredos na conversa.
- Usar ambiente do projeto, kernel correto e dependências fixadas compatíveis.
- Notebooks executam do início ao fim e importam os módulos sem ajustes manuais escondidos.
- Casos de erro, ausência de informação e limite de estoque funcionam sem inventar resposta.
- Cliente A e cliente B não compartilham memória.
- Interface, notebook e terminal usam a mesma lógica.
- Logs e LangSmith permitem conferir chamadas/retornos; dados de demonstração evitam informações pessoais desnecessárias.
- Testes são pertinentes aos riscos: cálculo, validação, memória, integração e evidência. Não criar testes apenas para espelhar implementação.
- Ambiente novo é conferido antes de declarar reprodução concluída.

## 14. Primeira ação solicitada à IA programadora

Confira o inventário e as evidências existentes dos **Incrementos 0 e 1**; não refaça as fases 1/2 do zero. Feche a base manual da seção 6 com testes e prossiga na ordem original: memória curta/longa → RAG/text-to-query → verificação → Streamlit → avaliação e entregas. O requisito de memória vetorial e a avaliação real no LangSmith continuam pendentes até demonstração. Não substituir a auditoria por reescrita ou testes fictícios.

Ao concluir cada incremento, responda brevemente:

1. O que foi feito e quais arquivos mudaram.
2. Como Renan pode executar e conferir, com comandos reais.
3. O que foi testado de verdade, o que foi simulado e o que não pôde ser testado.
4. Requisitos demonstrados e evidências correspondentes.
5. Próximo incremento e eventuais decisões de negócio pendentes.

Continue pelos incrementos autorizados quando os anteriores estiverem verificados. Se faltar credencial, política ou cobertura externa, conclua o trabalho independente e explique exatamente o impedimento, sem fabricar sucesso nem usar uma simulação como prova de integração real.

## 15. Progresso verificado em 08/11 — base manual e memória

- Incremento 1 / seção 6: base manual ampliada, somente quatro veículos originais mais uma S10 diesel; campos sem fonte mantidos pendentes. ViaCEP preservado. Evidência: `Agentes Cognitivos com LangChain/Projeto final/04_avaliacao_e_evidencias/resultados/BASE_MANUAL_08_11.md`.
- Incremento 2: janela de seis turnos completos, perfil confirmado/corrigível, resumos explicitamente autorizados e recuperação vetorial por cliente/modelo em SQLite. Exclusão remove também históricos. Sem extração ou aprendizagem procedural automática. Comparação LangMem/Mem0 documentada, sem instalar ambas. Evidência: `Agentes Cognitivos com LangChain/Projeto final/04_avaliacao_e_evidencias/resultados/MEMORIA_08_11.md`.
- Próximo trabalho: Incremento 3, RAG de políticas e text-to-query restrito. Não tratar a busca vetorial de memórias como RAG de políticas já concluído. Verificador geral, Streamlit, LangSmith, reprodução final, PDF e vídeo seguem pendentes.

## 16. Incremento 3 verificado — RAG e consulta estruturada

- FAISS sobre políticas existentes, embeddings text-embedding-3-small e carregamento de índice preparado, com fontes/modelo/integridade verificados. Decomposição de consulta após falha real top-1 em perguntas compostas; comparação nas mesmas perguntas e custo/contextos adicionais explicitados.
- Text-to-query restrito: pergunta → plano Pydantic por LLM → SELECT compilado por Python → dados do SQLite somente leitura. A alternativa não é SQL livre gerado pela LLM; alcance e relação com rubrica documentados.
- Atendimento com memória integra duas ferramentas novas, exige consulta no turno para políticas explícitas e apresenta fonte efetivamente recuperada. Falhas reais e falso positivo inicial da avaliação preservados.
- Evidências: `Agentes Cognitivos com LangChain/Projeto final/04_avaliacao_e_evidencias/resultados/RAG_08_11.md`. Notebook fase 4 executado com fixtures identificadas; rodada final com chat/embeddings reais. Não declarar qualidade universal a partir das checagens locais.
- Próximo incremento autorizado na ordem: verificação factual/lógica dentro do agente, depois interface Streamlit e avaliação LangSmith/entregas. Os passos pendentes não foram declarados concluídos por existir fonte no rodapé.

## 17. Incremento 4 verificado — resposta apoiada nas evidências

- Nova CLI atendimento_verificado.py mantém agente, ferramentas, RAG e memória; checagens financeiras e juiz LLM de três classes rodam antes de persistir/exibir. Não é classificador NLI especializado: adaptação e limites documentados.
- Um reparo no máximo, seguido de nova avaliação; juiz indisponível/reparo inválido produzem limitação segura. Candidata e resultados intermediários ficam nas evidências.
- 121 testes locais, notebook fase 5 executado com fixtures e comparação real: erros do juiz inicial preservados; modelo de verificação separado escolhido após 14 casos e três integrações. Não é qualidade universal ou relatório LangSmith.
- Evidências e decisões: Agentes Cognitivos com LangChain/Projeto final/04_avaliacao_e_evidencias/resultados/VERIFICACAO_08_11.md e registro D35 a D38.
- Próximo incremento: interface Streamlit usando o mesmo AtendimentoVerificado; depois avaliação LangSmith e entregas. Esses itens e reprodução final continuam pendentes.

## 18. Regra vigente: garantia de 30 dias

Renan definiu 30 dias de garantia para as pecas. Documento, JSON e indice FAISS atualizados; garantia deixa de ser prazo pendente. Regras de troca e demais condicoes nao foram definidas. Consultar o registro D39 e a evidencia GARANTIA_30_DIAS_08_11.md; registros anteriores e fixtures com garantia desconhecida sao historicos ou cenarios independentes.

## 19. Condicoes ficticias de troca e garantia por delegacao

Renan autorizou criar regras: garantia 30 dias corridos e troca por preferencia em 7 dias corridos, contados do recebimento/retirada, com condicoes na politica V3 e loja_regras.json. Peca instalada nao atende a troca por preferencia; defeito segue para avaliacao separada de garantia. Frete da devolucao e prazo de avaliacao seguem com o atendimento. Documento, JSON e FAISS atualizados; 124 testes e cenarios com API registrados em REGRAS_TROCA_GARANTIA_08_11.md. Decisoes D41 e D42.

## 20. Referencias explicitas de veiculo e citacoes

Protecoes locais validam modelo/ID declarado no pedido contra argumentos de consulta e produto escolhido; V004 explicito e tratado como veiculo. O estado comercial aprende a referencia executada, nao filtros descartados. Citacoes toleram diacriticos e formatacao mantendo palavras/valores. 132 testes locais e tres atendimentos com API registrados em REFERENCIA_VEICULO_08_11.md; decisoes D43-D44. Identificacao ambigua, compatibilidade real e limitacoes do juiz continuam explicitas.

## 21. Fusca TSI autorizado e desambiguacao

Renan autorizou incluir Fusca TSI. V006 representa 2014 2.0 TSI gasolina com manual VW como fonte; base passa a seis recortes, sem copiar produtos do V004 classico. Fonte e lacunas em FUSCA_TSI_08_11.md; 144 testes locais e fluxo hibrido com duas respostas por API registrados. Identificacao pendente e pergunta controlada sem LLM/juiz, nao nota semantica. Declaracao de geracao e ano atualiza referencia da sessao, preservando perfil permanente. Decisoes D45-D46.


## 22. BrasilAPI e distância geográfica

Renan autorizou substituir a consulta ativa ViaCEP por BrasilAPI CEP V2, sem conta/chave. Localização por CEP e cálculo Haversine em Python, com origem fixa do cadastro Ibram do Museu Oscar Niemeyer. Distância em linha reta aproximada, não rodoviária; Curitiba permanece grátis por município, sem inventar limiar gratuito em km. Coordenadas ausentes deixam frete externo pendente. Política V4 e reindexação FAISS acompanham a mudança; fixtures e evidências antigas preservadas como legado. Ver registro D55 e BRASILAPI_DISTANCIA_09_11.md.

Validação D55: 175 testes locais passaram; API real retornou 337.238 km em linha reta e frete de R$ 14,92 para 01002-020. Pedido P013 + P017 totalizou R$ 69,72 com entrega. Índice FAISS V4 atualizado; evidências e tentativa inicial de sequência preservadas. Python resolve o CEP declarado quando o agente tenta calcular antes da localização.
