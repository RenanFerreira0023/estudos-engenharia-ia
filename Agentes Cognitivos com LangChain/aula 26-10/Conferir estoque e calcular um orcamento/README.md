# Conferir estoque e calcular um orçamento

Um agente consulta um catálogo fictício em SQLite e usa uma ferramenta separada
para calcular o total em centavos. Nenhuma venda, reserva ou retirada real é feita.

## Executar

Na raiz, com as dependências `langchain`, `langchain-openai` e `python-dotenv`
disponíveis no ambiente virtual:

```powershell
.\.venv\Scripts\python.exe ".\Agentes Cognitivos com LangChain\aula 26-10\Conferir estoque e calcular um orcamento\conferir_estoque.py"
```

O script oferece demonstração e depois pedidos com `input()`. Enter ou `/sair`
encerra. Para rodar apenas os testes, acrescente uma das opções:

- `--demo`: três pedidos com o agente e testes diretos das barreiras.
- `--sem-api`: testes diretos de cálculo e restrição de escrita, sem modelo.

As chamadas a `gpt-4o-mini` usam `OPENAI_API_KEY` do ambiente ou do `.env` da
raiz, preservando variáveis existentes. Não crie cópia da chave nesta pasta.

## Conceitos praticados

- **sqlite3 e esquema no prompt:** o banco `:memory:` contém só `FIL-01`
  (3500 centavos, estoque 4) e `VEL-02` (2000 centavos, estoque 0). A LLM recebe
  nomes e finalidade das colunas para escrever SQL, sem receber os preços no prompt.
- **ChatOpenAI, create_agent e @tool:** o agente pode pedir `consultar_estoque(sql)`
  e `calcular_orcamento(preco_centavos, quantidade)`; consulta e cálculo têm funções
  diferentes. Não é uma chain LCEL nem há memória entre pedidos.
- **Leitura restrita:** filtro didático aceita SELECT e rejeita palavras de escrita;
  `execute()` aceita uma instrução. `PRAGMA query_only` e `set_authorizer()` adicionam
  barreiras no SQLite, permitindo leitura das colunas da tabela fictícia.
- **Cálculo determinístico:** `calcular_total_centavos()` valida os números e
  multiplica inteiros em Python. Zero e negativos não são quantidades válidas.
  A função devolve número, sem gerar texto comercial.
- **Auditoria da trajetória:** SQL, colunas, linhas, argumentos e retornos são
  registrados; AIMessage/ToolMessage relacionam tool calls aos respectivos IDs.
  A frase final é inspecionada junto das evidências.

## Como conferir

| Entrada | Esperado |
| --- | --- |
| Quanto ficam 2 unidades do FIL-01? Tem para retirar? | Consulta FIL-01, obtém preço 3500 e estoque 4; depois calcula 3500 × 2 = 7000 centavos (R$ 70,00). |
| Quero 1 unidade do VEL-02. Está disponível? | Produto existe, mas saldo é zero; sem cálculo de orçamento. |
| Quero 2 unidades do ABC-99. Qual o total? | Linhas vazias: produto não encontrado, sem preço inventado ou cálculo. |
| Quantidade 0 ou -2 na ferramenta | Erro de validação da quantidade. |
| UPDATE ou SELECT seguido de DELETE | Rejeição, sem alterar o banco. |

A demonstração confere SKU, colunas, linhas, preço passado ao cálculo,
quantidade, ordem consulta → cálculo e retorno. Compara o total com uma conta
Python independente e o catálogo antes/depois das tentativas de escrita.
As conferências registram **entrada, esperado, observado e passou**.
Uma falha encerra o roteiro com erro, em vez de aceitar só a resposta textual.

Os eventos aparecem no terminal e são acrescentados a `auditoria_estoque.jsonl`,
nesta pasta, ignorado pelo Git. O banco é recriado a cada execução; o log local
preserva execuções anteriores. No JSONL, `entrada` inicia um pedido e `conferencia`
registra sua verificação. Tool calls e respostas ficam registradas após o invoke;
as operações das ferramentas são registradas durante sua execução.

## Limite da barreira didática

O filtro por palavras não interpreta a gramática SQL e pode bloquear texto legítimo.
O banco isolado, `query_only` e o authorizer reduzem as operações permitidas neste
exemplo; não constituem uma solução pronta para produção. Não há limite de custo
ou complexidade de consultas. Não conecte este exemplo a bancos reais.
As instruções da LLM também não garantem fidelidade; por isso conferimos a trajetória.

Referências: [sqlite3 no Python](https://docs.python.org/3/library/sqlite3.html)
e [create_agent no LangChain](https://reference.langchain.com/python/langchain/agents/factory/create_agent).
