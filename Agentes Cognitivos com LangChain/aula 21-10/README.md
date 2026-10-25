# Aula 21-10

Prática guiada de memória de conversa e preferências por usuário, com ferramentas
de escrita, consulta e exclusão e auditoria das operações. Também inclui coleta
estruturada de uma avaliação simulada, com estado por sessão e correções por turno.

- [Preferências da oficina entre conversas](./Preferencias%20da%20oficina%20entre%20conversas/)
- [Agendar uma avaliação sem perder o contexto](./Agendar%20uma%20avaliacao%20sem%20perder%20o%20contexto/)

## O que estudar em cada exercício

| Exercício | Conceitos e aplicação |
| --- | --- |
| Preferências entre conversas | create_agent e @tool executam operações; MemorySaver/thread_id guardam histórico por conversa; um store separado usa namespace e chave por usuário para compartilhar preferências entre sessões, com auditoria. |
| Avaliação simulada | BaseModel/Field/Literal definem intenção e campos; ChatPromptTemplate recebe estado e mensagem; with_structured_output extrai dados; Python mantém estado por sessão, aceita correções e recalcula faltantes. |

No primeiro, o perfil do mesmo usuário pode ser consultado em outra sessão.
No segundo, cada sessão mantém sua própria coleta, sem herdar dados das demais.
Ambos perdem os dados ao reiniciar o processo.

Os exercícios usam o `.env` compartilhado na raiz do repositório.
