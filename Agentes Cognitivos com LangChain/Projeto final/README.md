# Auto Super Parts CWB — Projeto de disciplina

Renan · Agentes Cognitivos com LangChain · Fases 1 e 2 · 02/11/2026

## Comece aqui
1. Leia 01_documentacao/definicao_projeto.html para entender o problema e as regras.
2. Leia INSTRUCOES_PARA_IA_PROGRAMADORA.md antes de gerar código.
3. Use o catálogo e contratos de 02_codigo/dados e os casos de 04_avaliacao_e_evidencias/casos.

O projeto tem a **fase 1 (chain inicial)** e a **fase 2 (agente com ferramentas)**:
extração em JSON validado; consultas ao catálogo, orçamento determinístico e ViaCEP.
A fase 3 agora oferece memória em uma fachada separada, com CLI e notebook; fases 4–5 continuam pendentes. Cada mensagem da CLI antiga da fase 2 permanece independente.
Os documentos HTML são a arquitetura inicial e foram preservados como referência;
as decisões desta implementação estão identificadas como propostas no CSV.

## Organização para correção
| Pasta | Conteúdo |
|---|---|
| 01_documentacao | Definição do problema, decisões, matriz de requisitos e futuro PDF técnico. |
| 02_codigo | Módulos das fases 1 e 2 em src/auto_super_parts; testes da fase 1 em tests e verificação da fase 2 em verificar_fase02.py. |
| 03_notebooks | Fases 1–3 importam os .py; fase 3 executada com fixtures identificadas; fases 4–5 permanecem pendentes. |
| 04_avaliacao_e_evidencias | Expectativas separadas de testes locais, simulações e chamadas reais. Falhas históricas preservadas. LangSmith permanece pendente. |
| 05_demonstracao | Orientações para o futuro vídeo e seu link. |

Cinco fases de construção não são cinco entregas. As quatro entregas finais são: (1) código/notebooks reprodutíveis, (2) relatório técnico PDF, (3) registro de avaliação LangSmith, (4) vídeo de demonstração.
Essa estrutura é proposta para facilitar correção e reprodução; os nomes das pastas não são uma exigência formal.

## Como executar

Python testado: **3.12.6**. As versões exatas das dependências estão em
[requirements.txt](./02_codigo/requirements.txt). A pasta deste projeto pode ser
copiada e renomeada sem precisar das demais aulas ou do `.env` do repositório.
Todos os comandos abaixo partem da pasta que contém este README:

```powershell
Set-Location "CAMINHO_DA_COPIA_DO_PROJETO"
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\02_codigo\requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

Não é necessário ativar o ambiente: os comandos usam seu Python explicitamente.
Se o comando `py` não existir, use um Python 3.12 instalado para criar a `.venv`.
Uma `.venv` não é portátil: não a copie no ZIP. Recrie-a após copiar ou mover o projeto.

### Configuração local sem dependência externa

1. `OPENAI_API_KEY` já definida no ambiente tem prioridade. O programa não modifica
   essa variável e não imprime seu valor. Uma variável definida vazia gera erro claro,
   sem recorrer silenciosamente a outro arquivo.
2. Se a variável não estiver definida, o programa lê somente `.env` **nesta pasta
   do projeto**. Para usar essa opção:

```powershell
Copy-Item .\.env.example .\.env
```

Edite o `.env` local e substitua o valor de exemplo pela sua chave. Não versionar
esse arquivo. Não há busca automática no diretório de execução ou nas pastas
ancestrais. O marcador `INSTRUCOES_PARA_IA_PROGRAMADORA.md` identifica a raiz do
projeto, sem contar níveis com `parents[5]`. Mantenha a estrutura interna ao copiar.

Chamadas Python podem indicar um arquivo opcional com `criar_modelo(arquivo_env=...)`;
caminhos relativos são resolvidos nesta pasta e o ambiente continua prioritário.
Se escolher outro nome de arquivo com segredo, inclua-o no seu `.gitignore`.
As chamadas reais usam OpenAI / `gpt-4o-mini`; não há embeddings nesta fase.

### Registrar e selecionar o kernel

Registre o kernel **depois** de criar a `.venv` e instalar as dependências:

```powershell
.\.venv\Scripts\python.exe -m ipykernel install --prefix .\.venv --name auto-super-parts-fase01 --display-name "Auto Super Parts CWB (.venv)"
.\.venv\Scripts\python.exe -m jupyter kernelspec list
```

O registro fica dentro da `.venv`, não exige configuração global. O executor dá
preferência ao kernel registrado no ambiente que está executando o script.
Ao mover o projeto, recrie a `.venv` e registre o kernel novamente: o `kernel.json`
contém o caminho absoluto do Python daquela instalação.

No VS Code, abra `03_notebooks/fase_01_chain_inicial.ipynb`, clique em **Selecionar
Kernel** e escolha o Python `.venv\Scripts\python.exe` desta cópia em **Ambientes
Python**, ou o kernel **Auto Super Parts CWB (.venv)** quando listado. Confira
`sys.executable` na primeira célula de ambiente. Não selecione a `.venv` do
repositório original.

### Executar testes, notebook e CLI

```powershell
.\.venv\Scripts\python.exe -B .\02_codigo\executar_testes.py
.\.venv\Scripts\python.exe -B .\02_codigo\executar_notebook.py --modo simulado --saida .\04_avaliacao_e_evidencias\resultados\notebook_simulado_local.ipynb
.\.venv\Scripts\python.exe -B .\02_codigo\executar_notebook.py --modo real
```

`--kernel OUTRO_NOME` permite escolher outro kernel já registrado. O padrão é
`auto-super-parts-fase01`, igual ao comando de registro acima. Sem chave, use o
modo simulado para conferir infraestrutura; o modo real exige a configuração.

Para executar o notebook sem API, use `--modo simulado --saida CAMINHO.ipynb`.
O dummy reproduz JSONs roteirizados: testa infraestrutura e validação, não extração
real da linguagem. Não há fallback automático de API para dummy.

Para usar a CLI diretamente, ainda na pasta deste projeto:

```powershell
.\.venv\Scripts\python.exe -B .\02_codigo\src\auto_super_parts\chain_inicial.py
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

Na fase 1 não há consultas ao catálogo, cálculo de preço/frete ou ferramentas.
Memória, RAG, auditor integrado, LangSmith, PDF técnico e vídeo continuam pendentes.

## Fase 2: agente com ferramentas

O agente escolhe entre `listar_veiculos`, `consultar_catalogo`, `consultar_cep` e
`calcular_orcamento`. SQLite preserva o catálogo fictício e seus metadados;
consultas são parametrizadas, sem SQL livre gerado pela LLM. A função Python
reconsulta preços/estoque e calcula centavos com Decimal. ViaCEP identifica
município/UF; distância e regra de frete vêm dos arquivos simulados do projeto.

**Conceitos:** `create_agent` executa o ciclo modelo → ferramenta → modelo;
`@tool` descreve argumentos; `BaseModel` valida localmente; middleware configura
`bind_tools(strict=True)` e chamadas sequenciais. Callbacks guardam o esquema
enviado, e mensagens AI/Tool mostram argumentos e retornos. O modo estrito não
substitui validação local nem comprova veracidade. O prompt explicita PTCF e
exemplos de estratégia que não são apresentados como execuções observadas.

Na pasta deste projeto:

```powershell
.\.venv\Scripts\python.exe -B .\02_codigo\src\auto_super_parts\agente_fase02.py
.\.venv\Scripts\python.exe -B .\02_codigo\verificar_fase02.py
.\.venv\Scripts\python.exe -B .\02_codigo\executar_notebook.py --fase 2 --modo real
```

O kernel registrado acima serve aos dois notebooks. No VS Code selecione o Python
da `.venv` local também para `fase_02_agente_ferramentas.ipynb`. O modo simulado
usa `--fase 2 --modo simulado --saida CAMINHO.ipynb`, sem chamar OpenAI/ViaCEP.
O notebook principal da fase 2 registra execução real; a simulação fica separada.
`executar_testes.py` continua executando somente os testes da fase 1/configuração;
`verificar_fase02.py` registra separadamente a fase 2.

Perguntas independentes para testar:

- `Quero 2 unidades do P003 para retirada. Consulte preço e estoque e calcule o orçamento.`
- `Consulte o CEP 84010000 no ViaCEP e calcule 2 unidades do P003 para entrega nesse endereço.`
- `Consulte o CEP 01001000 no ViaCEP e calcule 2 unidades do P003 para entrega nesse endereço.`
- `Quero 1 unidade do P023 para retirada. Tem estoque?`
- `Tenho um Gol 2010 1.0 e quero duas velas.`

Espera-se R$ 37,00 na retirada e R$ 42,31 para Ponta Grossa, usando 120 km
**fictícios**. São Paulo não tem distância cadastrada: frete, prazo e total com
entrega permanecem desconhecidos. P023 existe com estoque zero. Configuração
incompleta exige esclarecimento; não há reserva nem compra. `/sair` encerra.

Veja [resultados, correção e reprodução](./04_avaliacao_e_evidencias/resultados/RESULTADOS_FASE_02.md)
e a [matriz de requisitos e equivalências](./01_documentacao/MATRIZ_FASE_02.md).
Para repetir a instalação limpa, `python -B 02_codigo/reproduzir_fase02.py` cria
uma cópia temporária sem `.env`, instala requirements em uma `.venv` nova,
executa as duas suítes e o notebook da fase 2 no modo simulado. A cópia fica
preservada para inspeção; a demonstração real da API é registrada separadamente.

## Testes e evidências da fase 1 (histórico)

Revisão de portabilidade: veja a [reprodução em cópia isolada](./04_avaliacao_e_evidencias/resultados/REPRODUCAO_FASE_01.md).
Foram executados 23 testes locais e o notebook **simulado** em uma `.venv` criada
do zero fora da pasta original. Não houve nova chamada à OpenAI nesta revisão.
O notebook principal apresenta essa execução simulada; o notebook real anterior
está preservado integralmente no snapshot indicado no relatório.

Resultado final: **16 testes locais e 9/9 casos com modelo real passaram**;
o notebook foi executado do início ao fim na entrega inicial. Esses são resultados
históricos preservados, não uma nova avaliação da revisão de portabilidade. Veja a
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

### Arquivos locais e entrega

O `.gitignore` desta pasta exclui `.env`, `.venv`, `__pycache__`, bytecode e
checkpoints do notebook, inclusive quando esta pasta é usada fora do repositório.
O ZIP deve conter o projeto e suas evidências, sem esses arquivos locais.
Caches podem ser recriados pelo Python durante o uso; não são parte da entrega.

Para regenerar o ZIP limpo, na pasta do projeto:

```powershell
.\.venv\Scripts\python.exe -B .\02_codigo\gerar_pacote.py
```

O arquivo fica ao lado da pasta do projeto, sem incluir `.venv`, `.env` real,
`__pycache__` ou bytecode. O comando confere a integridade antes de substituir
um ZIP anterior.

Implementação com apoio de Codex/OpenAI e revisão de Renan. Referências de API:
[decorador chain](https://reference.langchain.com/python/langchain-core/runnables/base/chain)
e [execução de notebooks com nbclient](https://nbclient.readthedocs.io/en/latest/client.html).

## Atenção aos dados
São 5 configurações propostas (4 originais e uma S10 2014 2.8 CTDI diesel) e 24 produtos fictícios. Preços em centavos. Aplicações simuladas NÃO homologam compatibilidade real. A base técnica do Celta e da S10 possui campos de óleo verificados em manual; outras configurações/campos permanecem pendentes. Produtos comerciais não foram homologados. Fontes e limites estão em fontes.json e conhecimento_tecnico.json. Distâncias são inventadas para teste. Casos de aceitação são expectativas, não resultados obtidos.

## Pendências
Prazo em Curitiba; marco inicial da contagem; troca e garantia; validação técnica de peças/óleos/configurações. Conferir requisitos explícitos do enunciado e orientações do professor antes de decidir equivalências de framework ou omissões.

## Revisão após os testes assistidos de 08/11

As falhas de frete isolado, troca de correia e recomendação de óleo sem fonte foram
preservadas. Veja o [antes/depois e os resultados](./04_avaliacao_e_evidencias/resultados/CORRECOES_08_11.md).

O agente agora expõe **seis ferramentas**: as quatro anteriores e `consultar_entrega`
e `consultar_informacao_tecnica`. Frete isolado usa CEP → regra de entrega, sem exigir itens.
`orcamento_fase02.py` compartilha a mesma consulta de entrega com o cálculo do orçamento.
`consultas_complementares.py` lê o conhecimento técnico já cadastrado com fontes/limites:
não é busca vetorial nem integração AutoTools. Esse era o estado no teste histórico; a curadoria manual descrita abaixo passou a liberar somente especificações documentadas.

`ContextVar` mantém o pedido da chamada atual para bloquear troca silenciosa de correia
dentada por acessórios, inclusive se o modelo tentar calcular diretamente outra peça.
Regras específicas de resposta bloqueiam as duas falhas observadas; não são NLI nem
verificador semântico universal. `resposta_candidata`, `resposta` e `verificacao_especifica`
permitem conferir quando houve substituição pela regra.

As respostas ao cliente deixam de repetir avisos de simulação. Os JSONs de origem,
preços, produtos e metadados técnicos continuam preservados. Não foram inventadas
especificações, alteradas aplicações ou homologados dados de catálogo.

Para repetir os seis casos reais, na pasta deste projeto:

```powershell
python -B 02_codigo/validar_correcao_08_11.py --real
```

Esse comando usa a configuração do projeto e consome API. Para conferir as regressões
locais, sem rede, execute a suíte `tests/` e `verificar_fase02.py` conforme as instruções.
`executar_testes.py` passou a incluir também `test_correcao_fase02.py`; seu rótulo histórico
de fase 1 não deve ser confundido com a divisão dos novos casos, listada no relatório.

Os notebooks principais continuam como evidência histórica de 02/11. A revisão de 08/11
está demonstrada pelos mesmos módulos, CLI, suíte e relatórios separados. Não houve nova
execução real dos notebooks, nem implementação antecipada de memória, RAG ou LangSmith.

## AutoTools — prova de cobertura em 08/11

O cliente HTTP foi implementado e a busca real dos quatro veículos foi executada.
**Não foi confirmada cobertura útil para nenhum deles nas consultas feitas.**
Gol retornou apenas Golf 2019 na busca ampla; Palio, Celta, Fusca e a busca alternativa
Beetle não retornaram candidatos. Consulta que responde HTTP 200 não comprova aplicação técnica.

Veja o [relatório e os retornos reais](./04_avaliacao_e_evidencias/resultados/PROVA_AUTOTOOLS_08_11.md).
O agente mantém suas seis ferramentas atuais; AutoTools não foi ligada como fonte
de óleo/peças. ViaCEP segue como integração externa real demonstrada.

Para repetir a prova, a partir da pasta Projeto final:

```powershell
python -B 02_codigo/provar_autotools.py --catalogo 02_codigo/dados/veiculos.json --saida 04_avaliacao_e_evidencias/resultados
```

`02_codigo/src/auto_super_parts/autotools.py` separa HTTP, Content-Type, JSON e contrato,
trata timeout/indisponibilidade e identifica testes com transporte injetado.
O script compara nome, ano, motor, combustível e mercado antes de aceitar identidade.
IDs externos só vêm do resultado da busca ou da api_url oficial; não são códigos locais.
As seções de óleo/peças só são consultadas após identidade confirmada, o que não ocorreu
nos veículos deste catálogo. Não houve recomendação de viscosidade, aplicação ou preço pela AutoTools.

Os 16 testes de `test_autotools.py` são fixtures de contrato/erros, não evidência de
dados técnicos reais. A suíte completa desta revisão passou com 68 testes locais.
Não houve nova instalação de dependências: httpx já constava nos requirements.

## Base manual e especialidade — revisão de 08/11

O plano passa a priorizar óleo/manutenção básica, freios, pneus, velas, correias e alternador. A S10 diesel é o único recorte adicional; não tem produtos à venda vinculados. As provas AutoTools e demais catálogos externos são históricas e não participam do atendimento. ViaCEP permanece ativo.

Veja [fontes, perguntas e limites por veículo](./01_documentacao/BASE_TECNICA_MANUAL.md). A ferramenta `consultar_informacao_tecnica` mantém fonte/status por assunto e consulta os JSON locais; não é RAG. A guarda de óleo usa somente o contrato documentado retornado no próprio turno e distingue norma, km/meses e uso normal/severo.

Exemplos para a CLI da fase 2 (cada mensagem ainda é independente):

- `Tenho um Celta 2012 1.0 8V flex. Qual óleo e intervalo de troca?`
- `Tenho uma S10 2014 2.8 CTDI diesel. Qual viscosidade e intervalo de troca do óleo?`
- `Tenho um Celta 2012 1.0 flex com ar-condicionado. Qual amperagem do alternador?`
- `Tenho um Fusca 1982 1600 a ar gasolina. Qual óleo devo usar?` — deve manter a pendência.

Testes offline: `python -B 02_codigo/executar_testes.py` e `python -B 02_codigo/verificar_fase02.py`. O [relatório deste incremento](./04_avaliacao_e_evidencias/resultados/BASE_MANUAL_08_11.md) separa regressões locais de execução com modelo real. Memória e demais fases seguem o plano, sem serem declaradas concluídas nesta curadoria.

## Fase 3 — chat com memória

[Guia, arquitetura e comandos](./01_documentacao/MEMORIA_FASE_03.md). Histórico efetivamente enviado ao agente; veículo persistido somente por confirmação; resumos autorizados com embeddings e recuperação por cliente. SQLite local, janela de seis turnos e busca por cosseno para a coleção pequena. Não é FAISS/políticas, autenticação ou aprendizagem automática.

```powershell
python -B 02_codigo/src/auto_super_parts/atendimento_memoria.py --cliente cliente_demo
python -B 02_codigo/validar_memoria.py
python -B 02_codigo/validar_memoria.py --real
python -B 02_codigo/executar_notebook.py --fase 3 --modo simulado
```

Use `/veiculos`, `/veiculo V003`, `/guardar Uso urbano com percursos curtos`, `/nova`, `/cliente outro_cliente`, `/perfil` e `/esquecer`. O último apaga perfil/resumos/histórico apenas do cliente selecionado. A identidade é de demonstração, sem login real. O banco da CLI fica em `02_codigo/estado_local` e não entra no Git/ZIP; a demonstração usa banco temporário.

[Evidências e limites](./04_avaliacao_e_evidencias/resultados/MEMORIA_08_11.md): 96 testes locais (78 + 18), seis situações com modelo/embeddings reais e leitura do banco por processo separado. Notebook da fase 3 executado em kernel novo com fixtures; isso não é compreensão por LLM. O próximo incremento continua sendo RAG/text-to-query, seguido de verificação, Streamlit e avaliação.
