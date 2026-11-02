# Buscar uma regra sem inventar um benefício

Responder dúvidas coloquiais de uma autopeças com base em três políticas fictícias,
preservando as fontes. A ausência de uma informação não confirma nem proíbe um benefício.

## Executar

Na raiz do repositório, use o ambiente virtual com `langchain`, `langchain-openai`,
`langchain-community`, `faiss-cpu` e `python-dotenv`:

```powershell
.\.venv\Scripts\python.exe ".\Agentes Cognitivos com LangChain\aula 26-10\Buscar uma regra sem inventar um beneficio\buscar_regra.py"
```

O programa oferece demonstração e depois chat com `input()`. Para executar somente
o roteiro, acrescente `--demo`. Enter ou `/sair` encerra o chat.
Use `OPENAI_API_KEY` no ambiente ou no `.env` compartilhado da raiz.
Chat (`gpt-4o-mini`) e embeddings (`text-embedding-3-small`) fazem chamadas à API.

## Conceitos praticados

- **Document e metadados:** cada política curta é um chunk com `id`, `fonte`,
  `dominio` e `chunk_id`. O texto e a referência permanecem juntos.
- **OpenAIEmbeddings e FAISS:** os três documentos são indexados uma vez por
  execução. As buscas seguintes reutilizam o índice em memória, mas cada consulta
  também gera um embedding. Não há PDF, divisão adicional de texto ou índice em disco.
- **Reescrita pelo agente:** a instrução em `system_prompt` pede uma consulta
  objetiva, mantendo a necessidade do usuário. Não há chain separada de reescrita.
- **@tool e create_agent:** `buscar_politicas(query_otimizada, dominio=None)`
  permite buscar até dois trechos, com filtro opcional de domínio.
- **similarity_search_with_score:** retorna conteúdo, metadados e score de cada
  resultado. Com o índice padrão deste script, o score é distância L2 ao quadrado;
  menor significa mais próximo no espaço vetorial, não mais verdadeiro.
- **RAG e auditoria:** a resposta deve citar ID e trecho útil. O JSONL registra
  corpus, modelo de embeddings, query, filtro, score, fontes, tool calls e resposta.

## Como conferir

| Pergunta | Evidência e resposta esperadas |
| --- | --- |
| “Comprei aí, tô enrolado com o trabalho. Que horas busco a peça?” | Reescrever para horário de retirada; citar RET-01: segunda a sexta, das 09h às 17h. |
| “A peça chegou zoada, como faço pra vocês verem isso?” | Reescrever para análise de avaria; citar AVA-01: enviar número do pedido e fotos. |
| “Vocês dão carro reserva por cinco dias?” | Consultar a base e reconhecer que ela não informa esse benefício. Não inventar direito nem afirmar proibição. |

A demonstração exige busca efetiva, reescrita nas duas primeiras perguntas e
citação do ID com as informações úteis do trecho. Não exige copiar a frase inteira.
No terceiro caso, confere ausência declarada.
Essas verificações não provam fidelidade semântica: leia as respostas e os trechos.

## Comparar original e reescrita

Após a primeira resposta, o script pega a query realmente usada pelo agente e
executa duas buscas: pergunta original e reescrita, **no mesmo índice, com k=2 e
sem filtro em ambas**. A comparação isola a mudança do texto, mesmo se a busca
anterior do agente tiver usado filtro de domínio.

O log mostra todos os documentos, textos e scores reais. A posição de RET-01 é
comparada: melhora, mesma posição ou piora. Se a pergunta original já recuperar a
regra na mesma posição, registra **sem melhoria observada**. Isso não significa
que os scores serão iguais nem prova qualidade geral da reescrita.

Não há limiares universais como 0,85/1,15. Um resultado próximo pode não responder
à pergunta. Um resultado distante não demonstra que a loja proíbe o serviço.
O domínio `pos_venda` também não torna AVA-01 evidência sobre carro reserva.

Os eventos são acrescentados a `auditoria_busca.jsonl`, na pasta do exercício,
ignorados pelo Git. O índice é reconstruído a cada execução; o log preserva as
execuções anteriores. Cada pergunta é independente, sem histórico de conversa.

Referência: [implementação FAISS no LangChain](https://github.com/langchain-ai/langchain-community/blob/main/libs/community/langchain_community/vectorstores/faiss.py).
