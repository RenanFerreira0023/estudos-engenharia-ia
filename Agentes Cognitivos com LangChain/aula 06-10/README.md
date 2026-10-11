# Aula 06-10 - Assistente de Oficina

Exercicio simples em Python para estudar o fluxo basico do LangChain:

```text
contexto + pergunta -> prompt -> modelo -> resposta
```

O assistente responde duvidas de uma oficina mecanica usando apenas o contexto
informado no codigo.

## Objetivo do exercicio

Praticar:

- `ChatOpenAI`
- `ChatPromptTemplate.from_messages`
- mensagens `system` e `human`
- variaveis no template
- LCEL com `prompt | modelo`
- `invoke`
- `.content`

## Contexto usado

O assistente sabe apenas que:

- a oficina abre de segunda a sexta, das 08:00 as 18:00;
- faz troca de oleo e alinhamento;
- o alinhamento custa R$ 120;
- nao realiza servicos de pintura.

Por isso, se a pergunta pedir algo que nao esta no contexto, o assistente deve
dizer que a informacao nao consta no contexto.

## Conceitos

### ChatOpenAI

Classe do LangChain usada para chamar um modelo de chat da OpenAI.

```python
modelo = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

### ChatPromptTemplate

Cria o prompt em formato de conversa.

```python
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Responda em portugues usando somente o contexto."),
        ("human", "Contexto:\n{contexto}\n\nPergunta:\n{pergunta}"),
    ]
)
```

`system` define as regras do assistente.

`human` recebe o contexto e a pergunta.

### Variaveis do template

`{contexto}` e `{pergunta}` sao variaveis preenchidas no momento da execucao.

### LCEL

LCEL conecta as etapas com o operador `|`.

```python
chain = prompt | modelo
```

### invoke

Executa a chain uma vez.

```python
resposta = chain.invoke(
    {
        "contexto": CONTEXTO_OFICINA,
        "pergunta": pergunta,
    }
)
```

### .content

O retorno do modelo e um objeto de mensagem. O texto fica em:

```python
resposta.content
```

## Como executar

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install langchain-openai
python assistente_oficina.py
```

Antes de executar, coloque a chave no `.env`:

```env
OPENAI_API_KEY=sua_chave_aqui
```
