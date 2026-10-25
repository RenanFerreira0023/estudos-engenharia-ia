# Aula 06-10

Exercicios da aula de LangChain focados em prompts, modelos de chat, LCEL e
saida estruturada.

## Exercicios

- [Assistente de oficina](./assistente%20oficina/)
- [Organizar solicitacoes de suporte em lote](./organizar%20solicitacoes%20suporte%20em%20lote/)

## O que estudar em cada exercício

| Exercício | Conceitos e aplicação |
| --- | --- |
| Assistente de oficina | ChatOpenAI chama a LLM; ChatPromptTemplate separa system/human e recebe contexto/pergunta; LCEL conecta a chain; invoke executa e .content lê o texto. |
| Suporte em lote | BaseModel e Field definem a ficha; with_structured_output extrai dados nesse formato; batch aplica a chain a uma lista de mensagens. |

O primeiro exercício pratica resposta em texto com contexto fixo; o segundo
pratica extração em objetos estruturados. Os dois usam chains definidas no código.

## Observacao sobre `.env`

Todos os exercicios carregam o `.env` da raiz do repositorio, ao lado do
README principal. Defina `OPENAI_API_KEY` nele ou no ambiente. Nao versione chaves.
