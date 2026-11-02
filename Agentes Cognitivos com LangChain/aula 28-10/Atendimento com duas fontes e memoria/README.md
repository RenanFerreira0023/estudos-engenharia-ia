# Atendimento com duas fontes e memória

Um agente responde sobre preço, estoque e retirada usando a fonte adequada.
Uma pergunta seguinte pode mencionar “desse produto”: a memória identifica o SKU,
mas o estoque atual deve vir de uma nova leitura SQL.

## Executar

Na raiz do repositório, com o ambiente virtual existente:

```powershell
.\.venv\Scripts\python.exe ".\Agentes Cognitivos com LangChain\aula 28-10\Atendimento com duas fontes e memoria\atendimento_duas_fontes.py"
```

Para rodar somente a demonstração e encerrar, acrescente `--demo`.
Dependências: `langchain`, `langchain-openai`, `langchain-community`, `langgraph`,
`faiss-cpu`, `sqlalchemy` e `python-dotenv`.
Defina `OPENAI_API_KEY` no ambiente ou no `.env` compartilhado da raiz.
Usa `gpt-4o-mini` e `text-embedding-3-small`, com chamadas à API.

O modo interativo mantém a sessão até `/sessao`; `/sair` encerra. Enter na sessão
inicial usa `s1`. As sessões `demo-*` são da demonstração; o chat usa `s1` por
padrão para começar separado dela. Voltar a um identificador usado recupera
seu histórico enquanto o programa estiver aberto.

## Conceitos praticados

- **SQLite e SQLAlchemy:** tabela `produtos` com os dois registros fictícios;
  `StaticPool` mantém o banco em memória acessível às threads das ferramentas.
  Após a carga, `query_only` restringe escritas acidentais. É um laboratório
  isolado, sem dados reais e sem uma barreira pronta para produção.
- **SQLDatabaseToolkit:** expõe ferramentas de consulta, schema, listagem e
  verificação SQL. O agente usa o esquema real para conhecer as colunas;
  `preco_centavos` contém preço unitário em centavos e `estoque` contém unidades.
- **Schema com amostras:** `sample_rows_in_table_info=2` inclui os dois produtos
  no retorno de `sql_db_schema`. Receber esses dados também é consultar a fonte
  SQL. A conferência aceita query ou schema com amostras, sem exigir uma única
  chamada. `sql_db_query_checker` revisa SQL com a LLM, mas não lê estoque.
- **Document, embeddings e FAISS:** somente a política de retirada entra no
  índice, criado uma vez por execução, com fonte `RET-01` e chunk explícito.
- **create_retriever_tool:** transforma o retriever em `buscar_politica_retirada`;
  `PromptTemplate` inclui fonte e texto no retorno. Essa fonte não contém preços
  nem saldos.
- **create_agent e MemorySaver:** integram ferramentas e guardam o histórico
  completo por `thread_id`. A memória resolve o produto, sem substituir a nova
  leitura do saldo atual.
- **HumanMessage, AIMessage e ToolMessage:** a última entrada humana delimita
  o recorte exibido; chamadas, argumentos, IDs e retornos antigos permanecem no
  histórico, mas não são impressos como se pertencessem ao novo turno.

## Como conferir

| Turno | Esperado |
| --- | --- |
| `demo-s1`: Qual o preço e o estoque do FIL-01? Até que horas retiro? | SQL informa 3500 centavos e estoque 4; documento informa segunda a sexta, 09h–17h. |
| Mesma thread: E ainda temos quantas unidades desse produto? | Identifica FIL-01 pelo histórico e executa nova leitura SQL. Exibe somente as chamadas e retornos novos. |
| Thread nova: e esse produto? | Pede identificação sem herdar SKU de outra sessão. |
| Outra thread: Qual o preço e o estoque do VEL-02? Está disponível? | Produto existe, custa 2000 centavos e tem saldo zero; indisponível não significa inexistente. |

A demonstração confere leitura SQL efetiva, retorno documental, continuidade do
histórico, IDs de chamadas sem repetição e reconhecimento do saldo zero.
O listener do SQLAlchemy captura instruções executadas durante cada `invoke()`;
os retornos das tools mostram os dados usados. Não basta aparecer o nome de uma
ferramenta: o checker, sozinho, não é evidência de consulta ao banco.

O arquivo `auditoria_atendimento.jsonl` guarda configuração das fontes, mensagens
apenas do turno atual, SQL e conferências de esperado/observado. Ele é acrescentado
a cada execução e ignorado pelo Git. Não contém uma cópia impressa de todo o
histórico em cada turno. A fidelidade completa das respostas exige comparar
os dados retornados com o texto final.

Reiniciar perde banco, índice e histórico. O exercício não faz venda, reserva,
agendamento ou confirmação de retirada real.

Referências: [create_retriever_tool](https://reference.langchain.com/python/langchain-core/tools/retriever/create_retriever_tool)
e [schema com amostras do toolkit SQL](https://reference.langchain.com/python/langchain-community/tools/sql_database/tool/InfoSQLDatabaseTool/description).
