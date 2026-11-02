# Auto Super Parts CWB — Projeto de disciplina

Renan · Agentes Cognitivos com LangChain · Fase 1: chain inicial · 02/11/2026

## Comece aqui
1. Leia 01_documentacao/definicao_projeto.html para entender o problema e as regras.
2. Leia INSTRUCOES_PARA_IA_PROGRAMADORA.md antes de gerar código.
3. Use o catálogo e contratos de 02_codigo/dados e os casos de 04_avaliacao_e_evidencias/casos.

O pacote inicial de planejamento e dados agora tem **somente a fase 1 implementada**:
extração de uma mensagem em JSON validado. As fases 2–5 continuam pendentes.
Os documentos HTML são a arquitetura inicial e foram preservados como referência;
as decisões desta implementação estão identificadas como propostas no CSV.

## Organização para correção
| Pasta | Conteúdo |
|---|---|
| 01_documentacao | Definição do problema, decisões, matriz de requisitos e futuro PDF técnico. |
| 02_codigo | Dados preservados; módulos da chain inicial em src/auto_super_parts e testes locais em tests. |
| 03_notebooks | fase_01_chain_inicial.ipynb importa os .py; placeholders das fases seguintes permanecem vazios. |
| 04_avaliacao_e_evidencias | Casos esperados e resultados separados de testes locais, dummy e chamadas reais da fase 1. LangSmith permanece pendente. |
| 05_demonstracao | Orientações para o futuro vídeo e seu link. |

Cinco fases de construção não são cinco entregas. As quatro entregas finais são: (1) código/notebooks reprodutíveis, (2) relatório técnico PDF, (3) registro de avaliação LangSmith, (4) vídeo de demonstração.
Essa estrutura é proposta para facilitar correção e reprodução; os nomes das pastas não são uma exigência formal.

## Como executar

Python testado: **3.12.6**. As versões exatas das dependências estão em
[requirements.txt](./02_codigo/requirements.txt). Comandos a partir da raiz do repositório:

```powershell
.\.venv\Scripts\python.exe -m pip install -r ".\Agentes Cognitivos com LangChain\Projeto final\02_codigo\requirements.txt"
.\.venv\Scripts\python.exe ".\Agentes Cognitivos com LangChain\Projeto final\02_codigo\executar_testes.py"
.\.venv\Scripts\python.exe ".\Agentes Cognitivos com LangChain\Projeto final\02_codigo\executar_notebook.py" --modo real
```

Configure `OPENAI_API_KEY` no ambiente ou no `.env` da **raiz do repositório**.
O [.env.example](./.env.example) não contém segredo; não crie outra cópia de `.env` aqui.
As chamadas reais usam OpenAI / `gpt-4o-mini`; não há embeddings nesta fase.

Para executar o notebook sem API, use `--modo simulado --saida CAMINHO.ipynb`.
O dummy reproduz JSONs roteirizados: testa infraestrutura e validação, não extração
real da linguagem. Não há fallback automático de API para dummy.

Para usar a CLI diretamente, rode na raiz do repositório:

```powershell
.\.venv\Scripts\python.exe ".\Agentes Cognitivos com LangChain\Projeto final\02_codigo\src\auto_super_parts\chain_inicial.py"
```

Também funciona pelo botão **Executar arquivo Python** do VS Code. Quando aparecer
`Mensagem:`, digite a solicitação e veja o JSON. Enter vazio ou `/sair` encerra.

A execução como módulo continua disponível: entre na pasta `02_codigo`, com o ambiente virtual ativado:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
python -m auto_super_parts.chain_inicial
python -m auto_super_parts.chain_inicial --mensagem "Tenho um Gol 2010 1.0 e quero duas velas"
```

A CLI retorna `status`, `dados` e `erros`. Em sucesso, `dados` contém o contrato
de extração sugerido em `contratos.json`. Em falha, `dados` é `null`: não há
resposta inválida apresentada como validada. Não há repetição automática.

## O que estamos estudando na fase 1

- **BaseModel e Field:** contrato tipado para intenção, veículo, peça, quantidade,
  CEP e campos faltantes. Quantidade precisa ser inteira positiva; CEP preserva zeros.
- **PromptTemplate e ChatPromptTemplate:** a mesma tarefa PTCF como string ou
  mensagens `system`/`human`, com instruções de formato fornecidas pelo parser.
- **Output parser:** `PydanticOutputParser` converte o texto em objeto validado;
  o Python recalcula as pendências conforme a intenção. O formato não prova fidelidade.
- **@chain e LCEL:** duas composições com as mesmas etapas, importadas no notebook.
  Adotamos chat + LCEL por clareza da sequência fixa, sem autonomia de agente.
- **invoke e batch:** execução individual e lote independente com conferência
  esperado/observado. O JSON só é exposto como validado após completo; não há stream parcial.

**Fluxo:** mensagem → validação da entrada → template → LLM → parser/BaseModel
→ pendências por intenção → JSON validado ou erro tratado.

## Propostas de coleta e limites

O vocabulário de intenções é `consulta_peca`, `orcamento`, `orcamento_entrega`,
`entrega`, `pagamento`, `politica` e `desconhecida`. O contrato inicial contempla
uma peça e a intenção principal, sem decompor pedidos com vários itens.

Consulta por nome pede modelo/ano/motor/combustível ainda ausentes; filtro ou
correia genéricos também pedem tipo. Quantidade só é obrigatória no orçamento;
CEP, na entrega; pagamento e política não exigem veículo. Código explícito de
peça permite simples consulta sem declarar compatibilidade. São propostas de
coleta, não regras técnicas homologadas.

`veiculo: null` pode ser normalizado para objeto com quatro campos `null`, sem
inventar valores. CEP aceita oito dígitos ou o formato com hífen; outras formas
inválidas geram erro. Quantidade zero, negativa ou fracionária não vira 1.
O exemplo do Gol mantém `motor="1.0"` e combustível desconhecido se não informado.

Não há consultas ao catálogo, cálculo de preço/frete, ViaCEP, ferramentas, memória,
RAG, auditor integrado, LangSmith, PDF técnico ou vídeo implementados nesta entrega.

## Testes e evidências

Resultado final: **16 testes locais e 9/9 casos com modelo real passaram**;
o notebook foi executado do início ao fim. Veja a
[explicação dos resultados e das revisões](./04_avaliacao_e_evidencias/resultados/RESULTADOS_FASE_01.md).
O [registro de testes manuais e CLI](./04_avaliacao_e_evidencias/resultados/TESTES_MANUAIS_FASE_01.md)
preserva o erro de importação relatado e as saídas da conferência assistida após a correção.

[Testes locais](./02_codigo/tests/test_fase01.py) conferem esquema, erros,
normalização, templates, composição e batch simulado. Os
[nove casos da fase 1](./04_avaliacao_e_evidencias/casos/casos_fase_01.json)
separam expectativas e saídas dummy; o gabarito não é enviado ao modelo real.
Os 17 casos gerais de aceitação permanecem expectativas de fases futuras.

Cada execução grava um arquivo próprio em
[resultados](./04_avaliacao_e_evidencias/resultados/), com modo, versões, entradas,
esperado, observado e divergências. A saída bruta do modelo é identificada como
não validada. A primeira execução real detectou o formato `veiculo: null` em
quatro casos; essa falha foi preservada e motivou a normalização e um novo teste.
Falhas de rede/ambiente também ficam separadas de falhas de extração.

O notebook principal deve ser executado de cima para baixo em kernel novo com
o Python da `.venv`; o script limpa saídas antigas antes de executar. Falhas geram
um notebook parcial separado e não substituem o arquivo principal por um sucesso fictício.

Implementação com apoio de Codex/OpenAI e revisão de Renan. Referências de API:
[decorador chain](https://reference.langchain.com/python/langchain-core/runnables/base/chain)
e [execução de notebooks com nbclient](https://nbclient.readthedocs.io/en/latest/client.html).

## Atenção aos dados
São 4 configurações propostas e 24 produtos fictícios. Preços em centavos. Aplicações simuladas NÃO homologam compatibilidade real. Especificações de óleo continuam pendentes. Fontes e limites estão em fontes.json e conhecimento_tecnico.json. Distâncias são inventadas para teste. Casos de aceitação são expectativas, não resultados obtidos.

## Pendências
Prazo em Curitiba; marco inicial da contagem; troca e garantia; validação técnica de peças/óleos/configurações. Conferir requisitos explícitos do enunciado e orientações do professor antes de decidir equivalências de framework ou omissões.
