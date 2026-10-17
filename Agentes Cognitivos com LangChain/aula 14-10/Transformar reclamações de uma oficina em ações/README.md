# Transformar reclamações de uma oficina em ações

Exercício da aula 14-10: transformar dois feedbacks longos em listas curtas de
melhorias para discutir com a equipe.

```text
feedback → resumo (até 30 palavras) → problemas → duas ações práticas
```

## Conceitos praticados

- `ChatOpenAI`: modelo de chat com chave lida do ambiente.
- `ChatPromptTemplate`: um prompt para cada variável: `feedback`, `resumo` e `problemas`.
- `StrOutputParser`: converte a resposta do chat em texto.
- LCEL (`|`): conecta as três etapas na ordem do exercício.
- Lambdas: convertem os textos em `{"resumo": texto}` e `{"problemas": texto}`.
- `invoke`: executa resumo e problemas separadamente para conferir as etapas.
- `batch`: processa `[{"feedback": relato}, ...]` e retorna um resultado por entrada.

## Executar

Na raiz do repositório, com o ambiente virtual ativado:

```powershell
python -m pip install langchain-openai
python "Agentes Cognitivos com LangChain\aula 14-10\Transformar reclamações de uma oficina em ações\transformar_reclamacoes.py"
```

Defina `OPENAI_API_KEY` no ambiente ou em um `.env` local na pasta deste exercício
ou na pasta `aula 14-10`. Não versione a chave.

O arquivo `lista-feedbacks.json` contém os 100 registros fornecidos. O terminal
pede dois IDs separados por vírgula. Enter seleciona `1,2`; digite, por exemplo,
`1,3` para escolher outros relatos. Apenas o campo `feedback` é enviado ao
modelo; os nomes e os demais campos não entram no prompt.

## Como conferir

O script imprime resumo, contagem de palavras e problemas de cada relato antes
de executar o fluxo completo. Se algum resumo estiver vazio ou ultrapassar
30 palavras (contadas por espaços), interrompe a execução para revisão.

Depois, `fluxo.batch(entradas)` executa novamente as três etapas e imprime duas
respostas independentes. Cada uma deve conter duas ações relacionadas apenas
ao respectivo relato. Confira se os resumos preservam os fatos, se os problemas
estão no texto e se as propostas evitam misturar clientes ou afirmar causas
não descritas. Para os IDs padrão, espere propostas sobre conferência do
alinhamento/retrabalho no primeiro e previsão de prazo do diagnóstico no segundo.
O JSON também contém elogios: se selecionar um relato sem problemas explícitos,
a resposta deve informar que faltam problemas para fundamentar ações.

A conferência e o batch fazem chamadas separadas: os textos podem variar,
mesmo com `temperature=0`. A contagem exibida confere os resumos da execução
separada; o limite no batch depende do prompt. O modelo não garante fidelidade:
revise as saídas antes de usá-las. A execução padrão faz dez chamadas ao modelo
(quatro na conferência e seis no fluxo completo).
