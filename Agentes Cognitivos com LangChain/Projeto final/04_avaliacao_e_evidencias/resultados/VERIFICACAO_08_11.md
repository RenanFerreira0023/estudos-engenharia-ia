# Verificação: resultados e decisões em 08/11/2026

Os nomes dos JSON usam UTC; arquivos com 20261109T00 foram gerados na noite de 08/11 em São Paulo. Gabaritos e candidatas de avaliação foram escritos para teste, não observados como falhas espontâneas do agente. A revisão abaixo foi feita pelo assistente; revisão de Renan permanece pendente.

## Antes e depois do juiz

| Evidência real | Modelo do juiz | Casos | Coincidências com todos os critérios | Integração |
|---|---|---:|---:|---:|
| [fase05_verificacao_real_20261109T004416631871Z.json](./fase05_verificacao_real_20261109T004416631871Z.json) | ChatOpenAI:gpt-4o-mini | 11 | 9 | 1/3 |
| [fase05_verificacao_real_20261109T004807748325Z.json](./fase05_verificacao_real_20261109T004807748325Z.json) | ChatOpenAI:gpt-4o-mini | 11 | 8 | 3/3 |
| [fase05_verificacao_real_20261109T005252670988Z.json](./fase05_verificacao_real_20261109T005252670988Z.json) | ChatOpenAI:gpt-4o-mini | 14 | 11 | 3/3 |
| [fase05_verificacao_modelo_comparado_20261109T005534252389Z.json](./fase05_verificacao_modelo_comparado_20261109T005534252389Z.json) | ChatOpenAI:gpt-5.4-mini | 14 | 14 | 3/3 |

As duas primeiras rodadas usaram 11 fixtures de desenvolvimento. A terceira acrescentou três variações de óleo/saudação ausentes nos exemplos few-shot; a comparação final repetiu os mesmos 14 casos. Os números são comparação com este gabarito, não acurácia geral, teste independente amplo ou relatório LangSmith.

O gpt-4o-mini confundiu ausência de prazo com contradição e bloqueou respostas corretas de lacuna/saudação. As candidatas inválidas foram rejeitadas, mas isso não torna a classificação de três classes correta. A primeira rodada também teve falso bloqueio por formatação de citação; a checagem passou a ignorar apenas espaços/Markdown, preservando palavras e valores.

Revisão do prompt, separação da candidata e três exemplos few-shot não eliminaram os erros do juiz mini inicial. Por isso foi comparado gpt-5.4-mini, mantendo o mesmo gabarito e sem trocar o modelo do atendente. O modelo escolhido para juiz/reparo usa esforço low, teto de saída 4096 e não tem fallback silencioso para o modelo anterior. Decisão limitada a esta amostra, com maior custo potencial por julgamento.

## Tabela final das fixtures

| Caso identificado | Aceite esperado | Aceite observado | Classes observadas | Conferiu gabarito |
|---|---|---|---|---|
| orcamento_correto | True | True | sustentada | True |
| total_incorreto | False | False | contradita | True |
| saldo_insuficiente | False | False | contradita | True |
| garantia_inventada | False | False | sem_suporte | True |
| lacuna_explicada | True | True | sustentada | True |
| cartao_contrario | False | False | contradita | True |
| oferta_nao_responde | False | False | sem_suporte | True |
| precos_trocados | False | False | contradita | True |
| homologacao_inventada | False | False | contradita | True |
| injecao_na_candidata | False | False | contradita, sem_suporte | True |
| saudacao | True | True | sustentada | True |
| viscosidade_sem_fonte | False | False | sem_suporte | True |
| lacuna_tecnica_explicada | True | True | sustentada | True |
| saudacao_variante | True | True | sustentada | True |

Exemplos revisados tecnicamente pelo assistente: garantia de 30 dias diante de cadastro pendente é sem_suporte; explicar essa lacuna é sustentado; cartão em três vezes diante de proibição explícita é contradito. Preços de duas peças trocados podem passar pela presença numérica e foram rejeitados pelo juiz semântico. “Posso consultar” não foi tratado como resposta completa. A instrução maliciosa da candidata não foi aceita como comando de avaliação. Esses acertos não garantem resistência universal a injeção.

## Verificação dentro do fluxo

A integração final registrou três cenários:

- **Falha controlada:** modelo de atendimento roteirizado produziu “Total: R$ 100,00.” após consulta/cálculo efetivos. Não foi uma falha observada do LLM atendente. O juiz e o reparador usaram a API real; a candidata foi bloqueada e corrigida ou substituída conforme a auditoria do JSON. A memória contém somente a resposta liberada.
- **Orçamento real:** agente com API consultou/calculou 7 unidades de P009 para retirada; resposta final R$ 118,30, conferida pelo juiz.
- **Garantia real:** agente com API consultou o RAG e explicou informação pendente sem inventar 30 dias; a verificação liberou a resposta apropriada.

Bancos temporários e identidades de teste, sem usar/alterar a memória pessoal de Renan. Nenhuma compra, reserva ou pagamento foi executado. A API ViaCEP não foi acionada por esses cenários.

## Regressões e reprodução local

[121 testes unittest](./fase05_regressoes_locais_20261109T005254956446Z.json) passaram na cópia temporária, incluindo os 107 anteriores e 14 testes novos. Fixtures/juiz roteirizado verificam contratos, não qualidade semântica de um LLM. Cobrem valores, orçamento nulo, citações inválidas, resposta de oferta, um reparo, falha de juiz/reparo, persistência da resposta final e inicialização Windows/cp1252.

A primeira versão local teve quatro falhas de teste porque um ponto final após R$ 100,00 impedia reconhecer a moeda. Isso foi corrigido antes da validação real; o cenário permanece na regressão. O notebook da fase 5 executou em kernel novo no modo simulado, sem juiz/relatório semântico fictício. Não foi feita reprodução final em ambiente novo neste incremento; não houve nova dependência.

## Decisões, limites e próximo passo

[Guia e comandos](../../01_documentacao/VERIFICACAO_FASE_05.md) e [registro D35–D38](../../01_documentacao/registro_decisoes.csv). Modelo atual tem suporte documentado a [saída estruturada e esforço low](https://developers.openai.com/api/docs/models/gpt-5.4-mini); a decisão de uso foi motivada pelos resultados acima, não por promessa de qualidade universal.

A abordagem é juiz LLM com classes de inferência + regras determinísticas, não classificador NLI especializado. Exige explicar a adaptação à rubrica. Até um reparo, sempre reavaliado; falha fecha com limitação segura. Um juiz probabilístico pode errar, e acrescenta custo/latência; valores faturados não foram medidos aqui. O verificador também não amplia cobertura da base técnica ou do RAG.

Não houve commit/push neste incremento. Streamlit, avaliação real LangSmith, reprodução final, relatório PDF e vídeo continuam pendentes. Próximo incremento: interface usando AtendimentoVerificado, sem recriar outra lógica de atendimento.
