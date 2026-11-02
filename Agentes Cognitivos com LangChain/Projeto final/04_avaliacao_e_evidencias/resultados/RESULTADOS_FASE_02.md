# Fase 2 — correção, demonstração e reprodução

Revisão de 02/11/2026. Implementação com apoio de Codex/OpenAI.
Este relatório atualiza o estado descrito em `fase02_revisao_20261102.md`, que
permanece preservado como registro da etapa anterior.
O escopo executável desta fase está implementado e testado. A conferência literal
da rubrica permanece limitada pela ausência do enunciado original do professor;
as equivalências não foram presumidas. Nenhuma fase 3 foi iniciada.

## Investigação de minItems

A falha original está intacta em
`fase02_20261102T195701244602Z.json`: o agente tentou duas vezes chamar
`calcular_orcamento` com `minItems: 1` no nível dos argumentos. BaseModel rejeitou
o campo extra e a função de cálculo não executou nesse caminho. A resposta final
desse turno não comprova um cálculo válido e não foi reclassificada como sucesso.

O snapshot `fase02_correcao_baseline_20261102T213921052336Z.json` conserva o
schema Pydantic, sua conversão anterior para OpenAI e os hashes dos arquivos
protegidos antes desta correção. A comparação mostrou:

| Camada | Antes | Depois |
| --- | --- | --- |
| Pydantic local | `extra=forbid`, lista com `min_length=1`, itens/quantidades validados | Preservado |
| JSON Schema de itens | `properties.itens.minItems=1`, corretamente colocado como restrição | Preservado nessa posição |
| Schema convertido para o provedor | Sem `strict`; objeto raiz sem `additionalProperties:false`, apesar da configuração local | Binding estrito, objetos sem propriedades extras; opcionais são obrigatórios no JSON do provedor e aceitam null |
| Argumentos gerados no caso de entrega | Incluíam `minItems` indevidamente | Chamadas reais posteriores só incluíram as propriedades declaradas |
| Tratamento local do argumento indevido | Rejeitado | Continua rejeitado no teste que reproduz os argumentos da falha |

O schema original não declarava `minItems` como argumento. A falha observada foi
de geração em chamada não estrita; não é evidência de que Pydantic precisaria
aceitar esse campo. A falta de restrição no provedor permitia argumentos fora
do contrato. O middleware `ferramentas_estritas` configura o `bind_tools` feito
por `create_agent` com `strict=True` e `parallel_tool_calls=False`. O prompt também
explicita consulta de catálogo/endereço antes do cálculo. Não há remoção silenciosa
de argumentos, aceitação de extras ou redução das restrições de quantidade.

Referência: [documentação oficial de function calling](https://developers.openai.com/api/docs/guides/function-calling).
O modo estrito restringe o formato; não substitui a validação local nem prova a
veracidade dos dados. Todos os schemas efetivamente usados ficam registrados
por callback em `esquemas_modelo`, sem headers ou credenciais.

## Testes e regressões

- **18 testes locais da fase 2**, sem falhas/erros:
  `fase02_verificacoes_locais_20261102T214551663771Z.json`.
  Incluem interceptação do pedido HTTP serializado pelo SDK com MockTransport,
  conferindo `strict`, propriedades permitidas, posição de `minItems`, objetos
  fechados e sequência de chamadas. O mock não é uma chamada real à OpenAI.
- O replay dos argumentos da falha original continua retornando `entrada_invalida`.
  O teste compara separadamente argumentos válidos do mesmo caso; a função retorna
  pendência para São Paulo, sem frete/prazo inventados. Lista vazia, quantidade
  zero/negativa/fracionária/booleana e preço externo continuam inválidos.
- Catálogo, metadados, SQL parametrizado, proibição de escrita, estoque zero,
  agregação de itens, subtotal independente, arredondamento/faixas de frete,
  cidade/UF e falhas de CEP continuam cobertos.
- **23 testes da fase 1**, sem falhas/erros:
  `fase01_unittest_20261102T214554503627Z.json`.
- O executor compartilhado também executou o notebook da fase 1 em modo simulado,
  salvando `fase01_notebook_regressao_fase02.ipynb`, sem alterar o notebook original.

## API e orçamento após a correção

Os três cenários abaixo foram executados no notebook com OpenAI/gpt-4o-mini.
Nos dois cenários de entrega, ViaCEP foi chamado de fato e retornou HTTP 200.
Catálogo, preços, aplicações e distâncias continuam fictícios.

| Cenário | Observado nas ferramentas e na resposta |
| --- | --- |
| Retirada: 2 × P003 | Catálogo: 1850 centavos por unidade e estoque 16; subtotal/total 3700 centavos, frete zero. Resposta: R$ 37,00. |
| CEP 84010000 → Ponta Grossa/PR | Município/UF reais alimentaram o cálculo; distância **simulada** de 120 km; frete 531 centavos; total 4231; 4 dias úteis, sem data de calendário. Marco inicial continua pendente. |
| CEP 01001000 → São Paulo/SP | Endereço real; subtotal 3700; sem distância cadastrada: frete, prazo e total com entrega null. A resposta informa que não foi possível cotar a entrega. |

Relatórios com esperado/observado e conferências de trajetória:

- `fase02_caso_retirada_real_20261102T214248284509Z.json`
- `fase02_caso_entrega_cadastrada_real_20261102T214254411105Z.json`
- `fase02_caso_entrega_sem_distancia_real_20261102T214300764463Z.json`

As conferências automáticas passaram nos três casos: consulta antes do cálculo,
CEP antes do cálculo de entrega, município/UF correspondentes ao retorno,
subtotal independente e valores/pêndencias esperados. A resposta final também
foi inspecionada: não inventou valor de entrega para São Paulo nem data de
calendário para Ponta Grossa. Essa avaliação finita não garante toda resposta
futura em linguagem natural. LangSmith e verificador integrado não foram
declarados como implementados.

A primeira repetição real após a correção, anterior à execução do notebook,
também passou nos dois destinos e está preservada em
`fase02_caso_entrega_sem_distancia_real_20261102T214123514629Z.json` e
`fase02_caso_entrega_cadastrada_real_20261102T214130140484Z.json`.

## Notebook e instalação limpa

O [notebook da fase 2](../../03_notebooks/fase_02_agente_ferramentas.ipynb) foi
executado de cima para baixo em kernel novo: **7 células de código, sem erros**.
Mostra o prompt, ferramentas/schemas, chamadas escolhidas, argumentos, retornos,
respostas finais e conferências dos três cenários. A lógica é importada de `.py`.
A versão offline está separada em `fase02_notebook_simulado.ipynb`; nela, decisões
são roteirizadas e o transporte é injetado explicitamente. Timeout e CEP inexistente
nessa demonstração são simulações identificadas, não incidentes reais alegados.

`requirements.txt` agora inclui também `langchain==1.4.7`,
`langgraph==1.2.17` e `httpx==0.28.1`, preservando as versões anteriores da fase 1.

A reprodução registrada em `fase02_reproducao_20261102T214328656198Z.json`
concluiu os **8 passos** esperados:

1. Criar `.venv` do zero numa cópia renomeada fora do repositório.
2. Instalar `requirements.txt` nessa `.venv`.
3. Executar `pip check`: `No broken requirements found.`
4. Executar os 23 testes da fase 1.
5. Executar os 18 testes da fase 2.
6. Registrar o kernel no prefixo da `.venv` nova.
7. Executar integralmente o notebook da fase 2 em modo simulado.
8. Confirmar que a CLI sem chave encerra com código 2 e pede configuração,
   sem procurar o segredo do projeto original.

Cópia preservada para inspeção:
`C:\Users\Renan\AppData\Local\Temp\fase02_reproducao_hkb6wh7m\pacote_renomeado`.
Nenhum `.env` privado foi copiado; OPENAI_API_KEY/PYTHONPATH foram removidos do
ambiente dos subprocessos. A instalação limpa comprova execução offline;
as APIs reais estão comprovadas separadamente no notebook principal e relatórios.
Cada comando, código esperado/observado e stdout/stderr constam no JSON.

## Como repetir

Na raiz do repositório, para conversar com o agente real:

```powershell
& ".\.venv\Scripts\python.exe" -B ".\Agentes Cognitivos com LangChain\Projeto final\02_codigo\src\auto_super_parts\agente_fase02.py"
```

Na pasta `Projeto final`, usando sua `.venv` local recriada conforme o README:

```powershell
.\.venv\Scripts\python.exe -B .\02_codigo\verificar_fase02.py
.\.venv\Scripts\python.exe -B .\02_codigo\executar_notebook.py --fase 2 --modo real
.\.venv\Scripts\python.exe -B .\02_codigo\reproduzir_fase02.py
```

Cada mensagem da CLI é independente; `/sair` encerra. API exige variável
OPENAI_API_KEY ou `.env` dentro de `Projeto final`, sem busca automática na raiz
externa. O nome histórico do kernel `auto-super-parts-fase01` é reutilizado pelos
dois notebooks; ele aponta para a `.venv` na qual foi registrado.

## Limites e conferência de requisitos

Veja a [matriz da fase 2](../../01_documentacao/MATRIZ_FASE_02.md). A ausência do
enunciado original impede afirmar equivalência acadêmica de `create_agent`
a `AgentExecutor`/ReAct ou a parâmetros legados, caso sejam exigidos literalmente.
Não foi instalada outra stack nem alegada uma comparação que não foi feita.

Prazo Curitiba, início da contagem, troca/garantia e homologação técnica de peças
continuam pendentes nos dados de domínio. Memória, RAG/text-to-SQL, LangSmith,
PDF e vídeo não foram antecipados. A fase 1 e as evidências anteriores continuam
protegidas por hashes; a falha original permanece acessível integralmente.

A conferência final `fase02_conferencia_final_20261102T214843784871Z.json`
registrou **58 arquivos protegidos sem alteração**, 18 arquivos Python compilados
com py_compile, links locais existentes, nenhum cache no projeto e nenhuma chave
detectada no conteúdo entregável. Os notebooks das fases 3–5 permanecem vazios.
