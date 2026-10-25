# Agendar uma avaliação sem perder o contexto

Coleta de veículo, dia, horário e nome ao longo da conversa, preservando os dados
e aceitando correções. A saída completa é **“Solicitação simulada pronta”**;
nenhum horário real é reservado.

## Executar

Na raiz do repositório:

```powershell
.\.venv\Scripts\python.exe ".\Agentes Cognitivos com LangChain\aula 21-10\Agendar uma avaliacao sem perder o contexto\agendar_avaliacao.py"
```

O programa oferece demonstração guiada e chat interativo. A sessão é pedida uma
vez e mantida nas mensagens seguintes. Use `/sessao` para trocar e `/sair` para
encerrar. Voltar ao identificador anterior recupera seu estado durante a execução.
O chat começa vazio, separado dos dados da demonstração.

Para executar somente a demonstração, acrescente `--demo` ao comando.
Dependências: `langchain-core`, `langchain-openai`, `pydantic` e `python-dotenv`.
Usa `gpt-4o-mini` e faz chamadas à API. Defina `OPENAI_API_KEY` no ambiente ou
no `.env` compartilhado da raiz, sem criar cópia neste exercício.

## Conceitos praticados

- **BaseModel, Field e Literal:** `AnaliseTurno` define intenção (`agendar`,
  `cancelar`, `duvida`), campos opcionais e lista de faltantes. Pydantic valida
  formato e tipos; a fidelidade dos dados ainda precisa ser conferida.
- **ChatPromptTemplate:** recebe `{estado_anterior}` e `{mensagem}`. O prompt
  pede preservação do contexto, correções explícitas e ausência como `None`.
- **with_structured_output e LCEL:** `prompt | extrator` retorna um objeto
  `AnaliseTurno` validado a cada `invoke()`, sem precisar ler `.content`.
- **Estado em Python:** um dicionário separa as sessões. O estado anterior é
  enviado explicitamente ao modelo; este exercício não usa MemorySaver ou store.
- **Processamento por turno:** Python mantém dados anteriores quando a extração
  retorna `None`, aplica valores novos e recalcula os campos obrigatórios.
  A resposta de continuidade e a confirmação são montadas no código.

## Como conferir

| Turno em s1 | Resultado esperado |
| --- | --- |
| Quero marcar uma avaliação para meu Fusca 1600. | Guarda veículo; pede dia, horário e nome. |
| Na terça-feira às 14h. | Preserva veículo; guarda dia e horário; pede nome. |
| Meu nome é Renan. | Solicitação simulada pronta com os quatro campos. |
| Na verdade, prefiro às 15h. | Troca somente horário e reapresenta a solicitação simulada. |

A demonstração confere o estado após cada turno, mantém “terça-feira” como texto
e testa ainda:

- **s2 vazia + “às 16h”:** pede veículo, dia e nome, sem herdar dados de s1.
- **Cancelamento em s1:** identifica `cancelar`, encerra a coleta e limpa os campos
  dessa sessão, sem alterar s2 nem criar um novo agendamento.

Uma dúvida apresenta o escopo e conserva os campos, sem confirmar solicitação.
O cancelamento afeta somente a coleta local: não cancela reservas reais. Depois
dele, um novo pedido precisa preencher os dados novamente. Não há persistência
em disco; reiniciar o programa perde os estados.

Referência: [with_structured_output no LangChain](https://reference.langchain.com/python/langchain-core/language_models/chat_models/BaseChatModel/with_structured_output).
