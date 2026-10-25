# estudos-engenharia-ia

Repositorio para estudos, exercicios e projetos do MBA em Engenharia de IA,
Machine Learning e Deep Learning.

## Organizacao

- [Agentes Cognitivos com LangChain](./Agentes%20Cognitivos%20com%20LangChain/)
- [Arquiteturas Multiagentes com LangGraph](./Arquiteturas%20Multiagentes%20com%20LangGraph/)
- [Codex skills do projeto](./codex-skills/)

## Aulas e exercicios

### Agentes Cognitivos com LangChain

- [Aula 06-10](./Agentes%20Cognitivos%20com%20LangChain/aula%2006-10/)
  - [Assistente de oficina](./Agentes%20Cognitivos%20com%20LangChain/aula%2006-10/assistente%20oficina/)
  - [Organizar solicitacoes de suporte em lote](./Agentes%20Cognitivos%20com%20LangChain/aula%2006-10/organizar%20solicitacoes%20suporte%20em%20lote/)

- [Aula 14-10](./Agentes%20Cognitivos%20com%20LangChain/aula%2014-10/)
  - [Transformar reclamações de uma oficina em ações](./Agentes%20Cognitivos%20com%20LangChain/aula%2014-10/Transformar%20reclama%C3%A7%C3%B5es%20de%20uma%20oficina%20em%20a%C3%A7%C3%B5es/)

  - [Encaminhar pedidos para o atendimento certo](./Agentes%20Cognitivos%20com%20LangChain/aula%2014-10/Encaminhar%20pedidos%20para%20o%20atendimento%20certo/)

- [Aula 19-10](./Agentes%20Cognitivos%20com%20LangChain/aula%2019-10/)
  - [Classificar feedbacks e validar a ficha](./Agentes%20Cognitivos%20com%20LangChain/aula%2019-10/Classificar%20feedbacks%20e%20validar%20a%20ficha/)
  - [Consultar regras de uma loja e registrar a busca](./Agentes%20Cognitivos%20com%20LangChain/aula%2019-10/Consultar%20regras%20de%20uma%20loja%20e%20registrar%20a%20busca/)

- [Aula 21-10](./Agentes%20Cognitivos%20com%20LangChain/aula%2021-10/)
  - [Preferências da oficina entre conversas](./Agentes%20Cognitivos%20com%20LangChain/aula%2021-10/Preferencias%20da%20oficina%20entre%20conversas/)
  - [Agendar uma avaliação sem perder o contexto](./Agentes%20Cognitivos%20com%20LangChain/aula%2021-10/Agendar%20uma%20avaliacao%20sem%20perder%20o%20contexto/)

## Observacoes

Todos os exercicios compartilham o arquivo `.env` na raiz deste repositorio,
ao lado deste README. Coloque `OPENAI_API_KEY` nele; nao crie copias nas aulas
ou nos exercicios. Os scripts localizam esse arquivo a partir de sua propria
localizacao, independentemente da pasta do terminal. Variaveis ja definidas no
ambiente tem prioridade. O `.env` e ignorado pelo Git e nao deve ser versionado.

Este repositorio deve crescer com anotacoes, exemplos de codigo e pequenos
projetos praticos. Cada aula pode ter sua propria pasta com README, codigo e
arquivos de apoio.

As skills em `codex-skills/` sao fontes versionadas. Para ficarem ativas no
Codex, elas tambem precisam existir em `C:\Users\Renan\.codex\skills`.
