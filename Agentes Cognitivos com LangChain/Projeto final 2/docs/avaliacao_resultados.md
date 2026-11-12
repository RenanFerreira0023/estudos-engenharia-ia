# Avaliação do agente: resultados e análise

Execuções reais em 12/11/2026 (UTC), com `python avaliar.py --modo api --langsmith`. Agente e juiz usam `gpt-4o-mini` com `temperature=0`. Os casos são **fictícios** (`dados/ficticios/casos_avaliacao.json`), cada um num banco SQLite temporário. Nenhum dado da conversa real foi enviado ao LangSmith.

## O que é medido

| Métrica | Como é calculada | Por quê |
| --- | --- | --- |
| `ferramentas_exatas` (oficial) | 1 se a lista de ferramentas chamadas é **idêntica** à esperada (ordem, repetição e extras contam) | Mesmo critério demonstrado na aula 08 para a trajetória |
| `ferramentas_sem_repeticao` (diagnóstico) | Igual à anterior, ignorando chamadas repetidas em sequência | Separar "ferramenta errada ou ausente" de "chamada redundante" |
| `resposta_semantica` | Juiz LLM com saída estruturada: `nota`, `responde_pergunta`, `cobre_referencia`, `sem_contradicao`, `somente_oferece_consulta`. **A nota final é 1 só se todos os critérios forem favoráveis**, regra aplicada em Python | Não depender só da nota do juiz |
| Teste do juiz | O juiz real julga duas respostas fixas (sem agente); a resposta "Posso consultar as mensagens para você." deve receber 0 | Avaliar o próprio avaliador |

## Resultados (4 execuções × 4 casos do agente)

| Caso | Trajetória esperada | Exata | Sem repetição | Resposta |
| --- | --- | --- | --- | --- |
| saudação | nenhuma | 4/4 | 4/4 | 4/4 |
| cliente | `buscar_cliente` | 4/4 | 4/4 | 4/4 |
| fonte | `listar_corpora_acessiveis` → `buscar_mensagens_fonte` | 4/4 | 4/4 | 4/4 |
| contagem | `listar_corpora_acessiveis` → `consultar_mensagens_estruturado` | **0/4** | 4/4 | 4/4 |
| **Total** | | **12/16 (75%)** | 16/16 | 16/16 |

Por execução, a média da trajetória exata foi 0,75 em todas as quatro (desvio padrão 0); a das respostas, 1,0 (desvio 0). Com `temperature=0`, o comportamento se repetiu sem variação.

Teste do juiz (3 execuções; a primeira ainda não o incluía): `proposta_visita` aprovada 3/3 (correto); `oferta_consulta` com **nota bruta 1 em 3/3** e **nota final 0 em 3/3**.

## Análise

1. **Resposta certa, trajetória com chamada a mais (contagem).** Em todas as execuções o agente chamou `listar_corpora_acessiveis` duas vezes seguidas e depois a consulta estruturada. A contagem (1 mensagem) estava correta, conferida pelo SQL. É o inverso do exemplo da aula: lá o agente deixou de chamar a ferramenta; aqui chamou uma a mais. A chamada extra não muda o resultado, mas gasta tempo e tokens. A métrica exata a penaliza, a complementar não; as duas juntas mostram que o problema é eficiência, não escolha errada de ferramenta. **O trace no LangSmith (experimento `secretaria-ia-d535a39c`, linha 2) mostra que as duas chamadas saem do mesmo passo do modelo**: o primeiro `model` gera dois nós `tools` com `listar_corpora_acessiveis` (0,02 s e 0,00 s); só o passo seguinte chama `consultar_mensagens_estruturado`. Foram chamadas paralelas redundantes emitidas de uma vez, não uma nova tentativa depois de ler o resultado. Hipótese complementar, não verificada: o prompt pede `listar_corpora_acessiveis` em duas regras diferentes (fonte e contagem).
2. **Falso positivo do juiz, contido pela regra de composição.** Diante de "Posso consultar as mensagens para você.", o juiz devolveu `nota: 1`, embora ele mesmo tenha marcado `responde_pergunta: false` e `somente_oferece_consulta: true`. É o falso positivo discutido na aula 08. A nota final ficou 0 porque o código só aprova quando todos os critérios estão favoráveis. Conclusão: a nota única de um juiz LLM não é confiável sozinha; critérios separados combinados em código são mais seguros.
3. **Leniência do juiz no caso fonte.** A referência diz que o orçamento proposto **não comprova recebimento**; as respostas citaram a mensagem e o valor corretamente, mas não repetiram esse aviso, e o juiz marcou `cobre_referencia: true`. Como a resposta não afirma pagamento, o caso foi aceito na revisão humana, mas mostra que o juiz não cobra avisos de negócio.
4. **Problema de redação.** "Existem 1 mensagem" (concordância), repetido em todas as execuções. Não afeta a nota.

## Limites

- Quatro casos de um turno; não cobrem memória multi-turno, propostas, financeiro nem cadastro PJ. Esses fluxos foram observados em testes manuais (`evidencias/`), não nesta bateria.
- Com `temperature=0`, as repetições não exploram a variação do modelo; medir variação exigiria temperatura maior ou outros modelos.
- A revisão humana dos JSONs foi feita pelo assistente e precisa ser confirmada por Renan.

## Melhorias possíveis

- Reduzir a chamada paralela duplicada: desligar chamadas paralelas (`parallel_tool_calls=False`) ou instruir no prompt uma única chamada a `listar_corpora_acessiveis`; reexecutar a bateria para comparar antes e depois. Desligar o paralelismo pode deixar mais lentos os pedidos que se beneficiam de chamadas simultâneas.
- Incluir no juiz a exigência de avisos de negócio ("orçamento proposto não é recebimento").
- Ampliar o dataset com casos multi-turno e com propostas.

Evidências: `evidencias/fase5_avaliacao_api_langsmith_execucao1.json` a `execucao4.json`. Experimentos no LangSmith: `secretaria-ia-6c1261ec`, `secretaria-ia-d535a39c`, `secretaria-ia-e080fcf4`, `secretaria-ia-d64e9b2b`; os dois últimos no dataset fixo `secretaria-ia-casos-ficticios`, comparáveis lado a lado.
