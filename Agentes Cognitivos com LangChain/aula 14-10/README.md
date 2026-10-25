# Aula 14-10

Exercícios de encadeamento de prompts com LCEL, parsers, processamento em lote
e roteamento entre chains de atendimento.

- [Transformar reclamações de uma oficina em ações](./Transformar%20reclama%C3%A7%C3%B5es%20de%20uma%20oficina%20em%20a%C3%A7%C3%B5es/)
- [Encaminhar pedidos para o atendimento certo](./Encaminhar%20pedidos%20para%20o%20atendimento%20certo/)

## O que estudar em cada exercício

| Exercício | Conceitos e aplicação |
| --- | --- |
| Reclamações em ações | Prompts em etapas, LCEL e StrOutputParser produzem resumos e análises; lambdas adaptam entradas; batch processa os relatos e invoke consolida o relatório. Python valida resumos e mantém IDs de apoio. |
| Encaminhar pedidos | Uma LLM classifica a mensagem; RunnablePassthrough preserva o texto original e RunnableLambda executa o roteamento para uma chain de vendas ou pós-venda, após validar o rótulo. |

A chave `OPENAI_API_KEY` pode ficar no ambiente ou no `.env` da raiz do
repositório, compartilhado por todos os exercícios. Não versione chaves.
