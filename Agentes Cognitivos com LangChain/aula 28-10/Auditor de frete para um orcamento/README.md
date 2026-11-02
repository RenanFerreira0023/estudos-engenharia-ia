# Auditor de frete para um orçamento

Audita afirmações de uma resposta, separando comparação numérica de avaliação
lógica. O texto auditado não é sua própria prova: regra e referência são fixas
e independentes, com subtotal de R$ 70,00, limiar de R$ 100,00 e taxa de R$ 10,00.

## Executar

Na raiz do repositório:

```powershell
.\.venv\Scripts\python.exe ".\Agentes Cognitivos com LangChain\aula 28-10\Auditor de frete para um orcamento\auditor_frete.py"
```

O script oferece demonstração e depois `input()` para auditar outras respostas
contra a **mesma referência fixa**. Não é um atendente que muda o orçamento a
cada mensagem. Enter ou `/sair` encerra.

- `--demo`: audita as três respostas fornecidas e testa dois desvios numéricos.
- `--sem-api`: testa somente os dois desvios diretamente na função Python.

Dependências: `langchain-core`, `langchain-openai`, `pydantic` e `python-dotenv`.
As duas chains usam `gpt-4o-mini`. Defina `OPENAI_API_KEY` no ambiente ou no
`.env` compartilhado da raiz. São duas chamadas por resposta, sem memória de sessão.

## Conceitos praticados

- **BaseModel, Field e Literal:** definem afirmações com trecho literal, chave
  canônica, valor e unidade; uma lista sem tamanho fixo; e pareceres por índice,
  relação geral, coerência e justificativa.
- **with_structured_output e LCEL:** uma chain extrai e outra avalia. O extrator
  recebe o texto e definições das chaves, sem os valores de referência.
  `include_raw=True` preserva também a resposta bruta e eventuais erros de conversão.
- **Métricas equivalentes:** subtotal, limiar e taxa padrão usam chaves distintas.
  Total acrescido de frete e prazo usam `unmapped_metric`. Uma conclusão sem número,
  como “você ganhou frete grátis”, também é registrada, com valor `None`.
- **Comparação determinística:** Python usa `Decimal` para calcular diferença
  absoluta e tolerância sem arredondar o desvio. Só compara valor numérico em BRL
  com a mesma métrica da referência; unidade incompatível não ganha aprovação.
- **Avaliação lógica fundamentada:** a segunda LLM recebe a regra completa,
  a referência independente, o original, a extração e o relatório numérico.
  Para cada índice, registra o trecho avaliado, a evidência e a justificativa
  antes de classificar. Verifica também conclusões e eventuais omissões da extração.
- **Auditoria:** relatórios numérico e lógico ficam separados no terminal e no
  JSONL. O gabarito é usado só no Python, sem instruir a LLM a devolver o esperado.

## Status numéricos e relações lógicas

| Status numérico | Regra em Python |
| --- | --- |
| CONFIRMADO | Diferença exatamente zero. |
| PARCIAL | Diferença não nula, menor ou igual à tolerância. |
| CONTRADITÓRIO | Diferença maior que a tolerância. |
| NÃO VERIFICADO | Sem chave equivalente, unidade incompatível ou sem valor numérico. |

Na avaliação lógica, **APOIA** significa sustentado pelas fontes; **REFUTA**,
contradito; **NEUTRA**, sem cobertura suficiente. O relatório geral é REFUTA se
houver contradição; senão NEUTRA se houver falta de cobertura; só é APOIA com
apoio integral. A coerência com as fontes é, respectivamente, INCOERENTE,
INDETERMINADA ou COERENTE. Não é uma nota sobre a qualidade da escrita.

`unmapped_metric` não obriga NEUTRA: frete grátis pode ser refutado pela regra,
apesar de não ser uma métrica numérica comparável. Já um prazo sem fonte não
pode ser aprovado. A taxa padrão de R$ 10,00, sozinha, não prova que esse é o
frete devido em qualquer orçamento.

## Como conferir

| Caso | Resultado esperado |
| --- | --- |
| Subtotal 70, limiar 100, frete 10 | Números CONFIRMADOS e lógica APOIA/COERENTE. |
| Subtotal 70, limiar 100, mas ganhou frete grátis | Números explícitos CONFIRMADOS; conclusão REFUTA/INCOERENTE. |
| Subtotal 70 e entrega em 24 horas | Subtotal CONFIRMADO; prazo NÃO VERIFICADO e NEUTRA; geral NEUTRA/INDETERMINADA. |
| Subtotal alegado 70,03 | Desvio 0,03 dentro de 0,05: PARCIAL, sem ser igualdade. |
| Subtotal alegado 70,10 | Desvio 0,10 acima de 0,05: CONTRADITÓRIO. |

Os dois últimos testes são diretos na função Python, sem extração pela LLM,
para isolar a aplicação da tolerância. O limite de R$ 100,00 é inclusivo para
a regra de gratuidade; tolerância numérica não muda o limite comercial.

Inspecione a extração no relatório numérico: ela pode omitir valores ou mapear
uma chave errada mesmo com esquema válido. Não há quantidade fixa de afirmações.
O código confere ancoragem dos trechos no original, cobertura dos índices e os cenários conhecidos;
esses controles não garantem fidelidade semântica para qualquer entrada.
Variações apenas de pontuação/espaços são anotadas sem reprovar o conteúdo;
o trecho observado não é reescrito no log para parecer uma citação literal.

Os registros são acrescentados a `auditoria_frete.jsonl`, ignorado pelo Git.
Uma divergência fica preservada com esperado e observado; a demonstração avalia
os casos e termina com erro se houver falhas. Revise o contexto/prompt e registre
uma nova execução, sem alterar o observado anterior para simular acerto.

Referência: [with_structured_output](https://reference.langchain.com/python/langchain-openai/chat_models/base/ChatOpenAI/with_structured_output).
