# O atendente consultou a política?

Exercício da aula 04-11. A política da autopeças é uma **simulação**:
balcão aceita Pix ou dinheiro; entrega exige pagamento antecipado;
não há pagamento ao entregador.

## O que observar

| Avaliação | Evidência | Aprovação |
| --- | --- | --- |
| Trajetória | Nomes em chamadas AI e retornos Tool com IDs correspondentes | As duas listas devem ser exatamente iguais à esperada, inclusive ordem e repetições. |
| Resposta | Texto final, pergunta, referência e política fictícia | LLM juiz confirma resposta completa, cobertura, ausência de invenção e que não é só oferta de consulta. |

As notas são independentes, binárias: **1** ou **0**. Uma resposta correta sem
consulta pode receber 1 em resposta e 0 em trajetória. Uma consulta correta com
resposta incompleta pode receber o inverso. Não se calcula uma média que esconda isso.

## Três casos

| Pergunta | Referência | Ferramentas esperadas |
| --- | --- | --- |
| Posso pagar ao entregador? | Não; pagamento antecipado, sem pagamento ao entregador. | `["consultar_politica"]` |
| Quais formas de pagamento no balcão? | Pix ou dinheiro. | `["consultar_politica"]` |
| Olá | Cumprimentar e oferecer ajuda. | `[]` |

## Execução no PowerShell

A partir da raiz do repositório:

```powershell
.\.venv\Scripts\Activate.ps1
cd 'Agentes Cognitivos com LangChain\aula 04-11\O atendente consultou a politica'
python avaliar_atendente.py
```

O menu usa `input()`. Escolha **1** para fixtures sem chamadas externas, ou **2**
para executar o agente e o juiz reais. A seguir, registre sua revisão nos três
casos e na fixture adversarial. Enter deixa explicitamente PENDENTE.

Dependências, caso ainda não estejam instaladas:

```powershell
python -m pip install langchain langchain-openai langsmith python-dotenv pydantic
```

O modo real lê `OPENAI_API_KEY` do ambiente ou do `.env` **na raiz do repositório**.
Não crie outro `.env` na aula. Modelos opcionais: `MODELO_ATENDENTE` e `MODELO_JUIZ`;
o padrão de ambos é `gpt-4o-mini`. Chamadas reais usam a API e podem consumir créditos.

Para executar diretamente:

```powershell
python avaliar_atendente.py --modo fixtures
python avaliar_atendente.py --modo api
python -m unittest -v
```

Cada execução salva JSON com trajetória, pareceres e comentários, além de uma tabela
Markdown e um relatório **HTML** em `resultados/`. Arquivos recebem timestamp para preservar evidências.
O terminal informa o caminho do HTML; abra-o com dois cliques no navegador.
Ele apresenta notas separadas, referências, respostas, ferramentas chamadas e executadas,
pareceres do juiz, comentários humanos e fixture adversarial.
Funciona sem internet, tem tema claro/escuro, detalhes expansíveis e impressão/PDF.

Para gerar HTML do JSON mais recente sem chamar novamente a API:

```powershell
python relatorio_html.py
```

Para uma execução específica:

```powershell
python relatorio_html.py resultados\execucao-20261108T182523407801Z.json
```
`--sem-revisao` desativa perguntas, mas mantém comentários humanos PENDENTES.

## Fixture para testar o juiz

**“Posso consultar a política”** é uma resposta escrita manualmente para a pergunta
sobre pagamento ao entregador. Ela oferece uma consulta; não responde à pergunta.
Nota esperada: **0**. Não é uma falha observada do agente.

No modo API, a mesma fixture é submetida a um critério inicial propositalmente
fraco e ao critério estrito. Os dois pareceres são preservados. Se o inicial aprovar,
o programa registra o falso positivo observado. Se não aprovar, não inventa um.
Se o estrito também aprovar, o teste do juiz continua falhando e o critério exige
nova revisão antes de confiar nos resultados. Leia a justificativa e registre sua
discordância/concordância no comentário humano.

Nos resultados locais, os julgamentos do LLM e a ocorrência de falso positivo ficam
`null`/PENDENTES. Não há LLM juiz no modo fixtures, nem uma heurística apresentada
como julgamento semântico. A revisão textual feita pelo assistente identifica a
oferta como incompleta; o comentário humano de Renan permanece pendente.

## LangSmith opcional

Com `LANGSMITH_API_KEY` no ambiente ou `.env` da raiz:

```powershell
python avaliar_atendente.py --modo api --publicar-langsmith
```

`Client` cadastra um novo conjunto com os três casos. `evaluate` publica as saídas
reais **já coletadas naquela execução** e suas duas notas; não chama agente ou juiz
de novo. O experimento identifica essa reutilização nos metadados. Não representa
uma trajetória interna reexecutada no LangSmith. Sem essa opção, tracing é
desativado durante a coleta, mesmo se houver configuração herdada de outros estudos.
Fixtures locais não são aceitas para publicação como resultados reais.

## Conceitos praticados

- `@tool`: disponibiliza a política fictícia por uma função descrita.
- `create_agent` e `invoke`: o atendente escolhe consultar e processa cada caso isolado.
- `HumanMessage`, `AIMessage`, `ToolMessage`: distinguem pergunta, chamada, retorno e resposta.
- Comparador exato: não perde repetições/ordem transformando listas em conjuntos.
- LLM juiz e `with_structured_output`: critérios explícitos com campos validados por Pydantic.
- Fixture adversarial: avalia a sensibilidade do juiz sem imputar ao agente uma falha inventada.
- `Client`/`evaluate`: conjunto de referências e avaliação opcional em LangSmith.
- Revisão humana: pode discordar do juiz; não altera silenciosamente sua nota.

**Fluxo:** casos → agente isolado → resposta + trajetória → duas avaliações → revisão → tabela.

## Verificação e limites

`test_avaliar_atendente.py` verifica localmente ordem, repetições, chamadas extras,
retornos ausentes/com erro/ID incorreto, saudação e condições de reprovação do juiz.
O dublê de juiz nesses testes não comprova qualidade semântica de um LLM real.
As fixtures demonstram a extração e a tabela; resultados reais exigem executar a API.
A revisão humana solicitada pelo enunciado só estará concluída após seu comentário.

### Evidência desta preparação — 08/11/2026

- Sintaxe validada e oito testes locais aprovados.
- Agente e juiz executados de verdade com a API OpenAI: três casos com nota 1
  em trajetória e nota 1 em resposta. Isso descreve esta execução, não uma garantia geral.
- Fixture de oferta: nota 0 no critério inicial e no estrito. Nenhum falso positivo observado.
- Renan revisou o julgamento da fixture no chat e concordou com a reprovação.
  A concordância está registrada no resultado real; comentários humanos individuais
  dos três casos continuam PENDENTES, sem serem inventados pelo assistente.
- Uma primeira tentativa de API encontrou bloqueio de conexão no ambiente restrito;
  a execução autorizada fora dessa restrição concluiu os casos.
- Sem `LANGSMITH_API_KEY` configurada: nenhum conjunto/experimento foi publicado.
- `resultados/` distingue explicitamente a execução local com fixtures da execução real.

Implementação preparada com auxílio de IA a partir do enunciado fornecido.

Referências técnicas: [create_agent](https://reference.langchain.com/python/langchain/agents/factory/create_agent),
[create_examples](https://reference.langchain.com/python/langsmith/client/Client/create_examples),
[avaliação LangSmith](https://github.com/langchain-ai/docs/blob/main/src/langsmith/evaluation-quickstart.mdx).
