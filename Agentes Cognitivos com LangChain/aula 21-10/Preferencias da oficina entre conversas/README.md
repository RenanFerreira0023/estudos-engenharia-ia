# Preferências da oficina entre conversas

A oficina guarda o canal preferido de orçamento de cada cliente e o recupera
em outra sessão. Tudo existe **somente durante a execução do processo**.

O assistente gerencia somente o canal preferido: e-mail, telefone ou WhatsApp.
Ele não agenda serviços, não confirma reservas, não entra em contato com clientes
e não cadastra nomes ou números. Uma data mencionada na conversa é apenas um
pedido no histórico. O prompt exige esclarecer esses limites e perguntar o canal
quando a preferência estiver ambígua.

## Executar

Na raiz do repositório, use o ambiente virtual existente:

```powershell
.\.venv\Scripts\python.exe ".\Agentes Cognitivos com LangChain\aula 21-10\Preferencias da oficina entre conversas\preferencias_oficina.py"
```

O programa oferece a demonstração e depois um chat com `input()`. Usuário e
sessão são pedidos uma vez e mantidos nas mensagens seguintes. A sessão inicial
usa `s1` se você pressionar Enter. O campo de mensagem mostra o usuário e a sessão
ativos; mensagem vazia apenas aguarda outra entrada.

- `/sessao`: pede outro identificador de sessão, mantendo o usuário.
- `/usuario`: pede usuário e sessão. Enter em qualquer campo mantém o valor atual.
- `/sair`: encerra o chat.

Esses comandos são locais e não são enviados ao modelo. Trocar para um par
usuário/sessão já usado retoma o histórico daquele par nesta execução.

Para executar somente a demonstração e encerrar:

```powershell
.\.venv\Scripts\python.exe ".\Agentes Cognitivos com LangChain\aula 21-10\Preferencias da oficina entre conversas\preferencias_oficina.py" --demo
```

Dependências: `langchain`, `langchain-openai`, `langgraph` e `python-dotenv`.
Defina `OPENAI_API_KEY` no ambiente ou no `.env` da **raiz**; variáveis existentes
têm prioridade. As interações usam `gpt-4o-mini` e fazem chamadas à API.

## Conceitos praticados

- **ChatOpenAI e create_agent:** o modelo pede ferramentas e usa seus retornos
  para responder. O prompt orienta a guardar preferências explícitas e consultar
  sempre que houver pergunta sobre elas.
- **@tool e identidade:** as ferramentas fecham sobre o usuário escolhido pela
  aplicação; seus argumentos não permitem escolher outro perfil. No laboratório,
  o `input()` de usuário simula a identidade da execução. Em uma aplicação real,
  ela viria da autenticação, e não de um campo livre fornecido pelo cliente.
- **MemorySaver e thread_id:** guardam o histórico por par usuário/sessão.
  Outra sessão começa sem o histórico anterior. O mesmo identificador de sessão
  em usuários diferentes também produz threads diferentes.
- **Namespace e dicionário:** `store.dados["u1/preferencias"]["canal_orcamento"]`
  contém `valor` e `atualizado_em`. É separado do histórico; todas as sessões
  compartilham a mesma instância do store durante a execução.
- **Upsert, consulta e exclusão:** atualizar substitui a mesma chave; consulta sem
  registro retorna `None` (`null` no JSON); excluir remove a chave.
- **date e auditoria:** cada operação registra data, operação, usuário, namespace,
  chave e resultado. Os logs e retornos reais das ferramentas aparecem no terminal.

## Como conferir

A demonstração executa as quatro interações do enunciado e consultas adicionais:

1. u1 guarda e-mail em s1; u2 guarda telefone em s2.
2. u1 consulta em s3: a ferramenta precisa retornar e-mail do store.
3. Os dois perfis são inspecionados separadamente no dicionário.
4. u1 atualiza para WhatsApp em s4 e consulta em s5. A mesma chave deve ter
   somente o valor novo; u2 continua com telefone.
5. u3 consulta sem registro e recebe ausência.
6. u1 pede exclusão em s7; uma consulta em s8 precisa retornar ausência.
   O perfil de u2 é conferido novamente.

As verificações interrompem a demonstração se faltar uma operação esperada ou
se o dicionário tiver um estado incorreto. “Salvei” na resposta não é evidência.
O fluxo usa sessões distintas para que a recuperação dependa do store.

Excluir do store não apaga mensagens antigas do histórico nem os logs de
auditoria. O prompt exige consulta ao store para responder sobre o valor atual.
Reiniciar o programa perde **store, logs e checkpoints**; não há banco ou arquivo
de persistência.

Referência: [memória de conversa no LangChain](https://github.com/langchain-ai/docs/blob/main/src/oss/langchain/short-term-memory.mdx).
