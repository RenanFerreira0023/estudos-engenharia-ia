# Classificar feedbacks e validar a ficha

Prática complementar: uma oficina precisa transformar opiniões de clientes em
fichas com `sentimento` e `motivo`. Usamos apenas feedbacks claramente positivos
ou negativos, incluindo ironia, sem relatos neutros ou mistos.

```text
Feedback → prompt com três exemplos → modelo → texto → parser → ficha
                                                        ↓ falha
                           saída + esquema + feedback → reparo → parser
                                                                  ↓ falha
                                                             erro explícito
```

## Conceitos praticados

- `BaseModel` e `Field`: descrevem os dois campos obrigatórios. O motivo deve
  ter entre 1 e 200 caracteres; campos extras são rejeitados.
- `field_validator`: valida no código que `sentimento: str` seja `positivo`
  ou `negativo`. O `pattern` também apresenta essa restrição no esquema.
- `FewShotChatMessagePromptTemplate`: fornece exemplos positivo, negativo
  direto e negativo irônico, diferentes dos três textos de teste.
- `ChatPromptTemplate` e `get_format_instructions()`: reúnem diretrizes,
  exemplos, esquema do parser e nova avaliação.
- LCEL (`|`) e `invoke()`: conectam e executam as etapas. `StrOutputParser`
  preserva a saída textual para que um eventual reparo receba o que falhou.
- `PydanticOutputParser`: transforma e valida a saída como `FichaFeedback`.
- `OutputParserException` e `try/except`: detectam falhas de estrutura e
  encaminham a saída para uma única tentativa de reparo, validada novamente.
- `input()`: permite experimentar outro feedback depois dos testes obrigatórios.

Os exemplos ficam na constante `EXEMPLOS`, dentro do script, pois fazem parte
do prompt. `json.dumps()` converte cada ficha de demonstração em texto JSON.

Os relatos de teste ficam em `feedbacks.json`, com os campos `feedback` e
`sentimento_esperado`. O sentimento esperado serve apenas para conferência no
código; somente o feedback é enviado à chain de classificação.

## Executar

Com o ambiente virtual do projeto ativado (Python 3.10 ou superior):

```powershell
python -m pip install langchain-openai "pydantic>=2,<3"
cd "Agentes Cognitivos com LangChain/aula 19-10/Classificar feedbacks e validar a ficha"
python classificar_feedbacks.py
```

Defina `OPENAI_API_KEY` no ambiente ou no `.env` da aula/exercício. Não versione
a chave. O modelo segue o padrão do projeto: `gpt-4o-mini`, `temperature=0`.

O script processa os três feedbacks e imprime as fichas como uma lista JSON.
Depois, envia ao parser um objeto sem `motivo`, mostra a rejeição e chama a
chain de reparo com a saída inválida, o esquema, o erro e o feedback original.
Essa demonstração fica separada das três fichas. Enter encerra a etapa interativa.

São quatro chamadas ao modelo no fluxo sem imprevistos: três classificações e
um reparo do teste inválido. Cada classificação inválida permite um reparo extra;
cada entrada interativa também faz uma classificação. Não há repetição automática
de chamadas da API (`max_retries=0`) nem segunda tentativa de reparo.

## Como conferir

**Estrutura:** os três resultados precisam passar pelo parser. Campos ausentes,
motivo vazio, tipos incorretos ou sentimento fora das opções provocam erro.

**Conteúdo:** os sentimentos esperados são `positivo`, `negativo` e `positivo`.
O script compara esses valores e informa divergências. Confira também os motivos
ao lado dos relatos: rapidez e orçamento explicado; espera de três horas sem
aviso apesar do elogio irônico; problema resolvido e bom atendimento. Essa revisão
do motivo é humana: validar o esquema não comprova fidelidade ao relato.

**Tratamento:** o teste sem `motivo` precisa mostrar a rejeição e executar um
único reparo. Se a saída reparada continuar inválida, o erro aparece e o programa
encerra com código 1. Falhas de API e divergências de sentimento também são
informadas, sem desaparecer silenciosamente.

Referências: [FewShotChatMessagePromptTemplate](https://reference.langchain.com/python/langchain-core/prompts/few_shot/FewShotChatMessagePromptTemplate)
e [PydanticOutputParser](https://reference.langchain.com/python/langchain-core/output_parsers/pydantic/PydanticOutputParser).
