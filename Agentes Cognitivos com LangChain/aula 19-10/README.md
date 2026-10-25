# Aula 19-10

Prática complementar de exemplos no prompt, classificação de feedbacks e
validação de saídas estruturadas com uma tentativa de reparo, busca vetorial e
observação de ferramentas com callbacks.

- [Classificar feedbacks e validar a ficha](./Classificar%20feedbacks%20e%20validar%20a%20ficha/)
- [Consultar regras de uma loja e registrar a busca](./Consultar%20regras%20de%20uma%20loja%20e%20registrar%20a%20busca/)

## O que estudar em cada exercício

| Exercício | Conceitos e aplicação |
| --- | --- |
| Classificar feedbacks | FewShotChatMessagePromptTemplate mostra exemplos; Pydantic define restrições e PydanticOutputParser valida a ficha. OutputParserException permite uma tentativa de reparo com o feedback original. |
| Consultar regras | OpenAIEmbeddings gera vetores e FAISS recupera trechos por similaridade. create_agent usa uma @tool de busca para fundamentar a resposta (RAG); callbacks registram as chamadas reais. |

Na classificação, confira estrutura e fidelidade ao relato. Na busca, compare
os trechos recuperados com a resposta e as chamadas registradas nos logs.

A chave `OPENAI_API_KEY` pode ficar no ambiente ou no `.env` da raiz do
repositório, compartilhado por todos os exercícios. Não versione chaves.
