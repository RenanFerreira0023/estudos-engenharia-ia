# Transformar reclamações de uma oficina em ações

Analisa **todos os 100 feedbacks** de `lista-feedbacks.json` e gera um relatório
geral em tópicos: principais reclamações com sugestões de melhoria e pontos
positivos que a equipe deve manter. Um relato pode conter reclamações e elogios.

```text
Todos os feedbacks → batch de resumos → batch de análises → relatório geral
```

## Conceitos praticados

- `ChatPromptTemplate`: monta os prompts; nessa montagem nenhum ID é processado.
- `ChatOpenAI`: gera respostas com a chave do ambiente ou `.env` local.
- `StrOutputParser`: transforma cada resposta em texto.
- LCEL (`|`): conecta prompt, modelo, parser e adaptação da entrada.
- Lambda: coloca o texto na chave `resumo` esperada pelo prompt de análise.
- Lambda final: reúne todas as análises na variável `analises` do prompt geral.
- `batch`: aplica cada etapa individual a todos os registros, mantendo a ordem.
- `invoke`: executa a consolidação uma vez, sobre o conjunto inteiro.
- `input()`: escolhe quantas etapas intermediárias exibir, sem filtrar dados.

As etapas são executadas separadamente para permitir a conferência. Os resumos
e análises conferidos são os mesmos usados na consolidação, sem refazê-los.

## Executar

Com o ambiente virtual ativado (Python 3.10 ou superior), instale a dependência:

```powershell
python -m pip install langchain-openai
```

Entre na pasta deste exercício e execute:

```powershell
python transformar_reclamacoes.py
```

Defina `OPENAI_API_KEY` no ambiente ou no `.env` da pasta deste exercício ou da
aula. Não versione a chave. O script usa `gpt-4o-mini`, com `temperature=0`.

Enter mostra os dois primeiros exemplos de resumo/análise; `s` mostra todos.
**Ambas as opções processam todos os registros.** São duas chamadas por feedback
e uma chamada final: 201 chamadas para 100 feedbacks, com até cinco em paralelo,
mais eventuais tentativas extras para corrigir resumos inválidos.
Os nomes dos clientes não são enviados ao modelo, apenas feedbacks e IDs.

O relatório aparece no terminal e é salvo em `relatorio_oficina.md`, na pasta do
exercício. Uma nova execução substitui esse relatório.

## Como conferir

Todos os resumos são validados: entre 1 e 30 palavras, contadas por espaços.
Um resumo vazio ou longo demais é refeito individualmente a partir do feedback
original, com metas de 20, 15 e 10 palavras, em até três novas tentativas. Os
resumos válidos são reaproveitados. Se ainda falhar, o fluxo é interrompido
antes da análise, sem cortar o texto automaticamente. Confira o original,
o resumo e as seções RECLAMAÇÕES/ELOGIOS.

O relatório deve reunir até cinco sugestões de melhoria e até cinco pontos
positivos a manter. Temas semelhantes são agrupados, priorizando os recorrentes.
Cada tópico cita os IDs de apoio; confira as referências no JSON. As ações devem
ser propostas práticas, sem afirmar causas ausentes dos relatos. Elogios não
devem virar problemas; ausência de reclamação não deve virar elogio.

A classificação, o agrupamento e a prioridade são produzidos pelo modelo, sem
garantia de precisão estatística. O prompt não pede contagens ou percentuais.
O limite de 30 palavras pode perder nuances: compare os tópicos importantes
com os relatos originais antes de discutir decisões com a equipe.
