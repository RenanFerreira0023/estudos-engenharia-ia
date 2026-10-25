# Aula 06-10 - Organizar solicitacoes de suporte em lote

Exercicio em Python para transformar mensagens livres de clientes em fichas
estruturadas com LangChain. O exercicio e interativo: voce digita mensagens no
terminal, monta um lote e depois o `batch` processa tudo de uma vez.

```text
input -> mensagens -> lista de entradas -> prompt -> modelo estruturado -> batch -> fichas
```

## Objetivo do exercicio

Praticar:

- `BaseModel` e `Field`, do Pydantic
- `ChatPromptTemplate.from_messages`
- `with_structured_output`
- LCEL com `prompt | modelo_estruturado`
- `input()`
- `batch`
- leitura dos atributos do objeto retornado

## Campos da ficha

Cada mensagem deve virar uma `FichaSuporte` com:

- `cliente`: nome informado na mensagem; quando ausente, usar `Nao informado`;
- `resumo`: descricao curta da solicitacao, sem adicionar fatos;
- `categoria`: `erro` quando houver falha relatada, ou `duvida` quando o cliente
  pedir orientacao.

## Mensagens de exemplo

```python
MENSAGENS_EXEMPLO = [
    "Sou Ana. Nao consigo entrar no sistema desde hoje cedo.",
    "Meu nome e Bruno. Gostaria de saber como alterar meu e-mail.",
    "O relatorio de vendas aparece em branco quando abro a pagina.",
]
```

## Ideia principal

O Pydantic define o formato da resposta esperada:

```python
class FichaSuporte(BaseModel):
    cliente: str = Field(description="...")
    resumo: str = Field(description="...")
    categoria: str = Field(description="...")
```

Depois, o modelo e configurado para devolver esse formato:

```python
modelo_estruturado = modelo.with_structured_output(FichaSuporte)
```

A chain conecta prompt e modelo estruturado:

```python
chain = prompt | modelo_estruturado
```

O `input()` coleta mensagens no terminal. Se voce pressionar Enter sem digitar
nada, o script usa as mensagens de exemplo do desafio.

Para processar varias mensagens, a lista digitada vira uma lista de dicionarios
com a chave `mensagem`:

```python
entradas = [{"mensagem": mensagem} for mensagem in mensagens]
fichas = chain.batch(entradas)
```

## Como executar

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install langchain-openai
python "Agentes Cognitivos com LangChain\aula 06-10\organizar solicitacoes suporte em lote\organizar_suporte_lote.py"
```

Antes de executar, coloque a chave no `.env` da raiz do repositorio:

```env
OPENAI_API_KEY=sua_chave_aqui
```

## Resultado esperado

Ao executar, digite uma mensagem por vez. Use `fim` para processar o lote. Se
pressionar Enter sem digitar nenhuma mensagem, devem aparecer tres fichas com
os exemplos do desafio. A terceira ficha deve usar `Nao informado` como cliente,
porque a mensagem nao informa um nome.

Usar saida estruturada ajuda a proxima etapa do sistema porque o codigo recebe
campos previsiveis, em vez de precisar interpretar um paragrafo livre.
