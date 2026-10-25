# Consultar regras de uma loja e registrar a busca

Prática complementar: consultar as regras de uma loja de peças e observar nos
logs como o agente usa a ferramenta, sem completar respostas com outras políticas.

```text
regras.json → embeddings → FAISS (texto + categoria)
pergunta → agente → ferramenta de busca → até dois trechos → resposta
                    ↳ callbacks: início, fim e fim de cada geração da LLM
```

## Conceitos praticados

- `OpenAIEmbeddings`: transforma regras e consultas em vetores para comparar sentido.
- `FAISS.from_texts`: indexa textos e preserva a categoria nos metadados.
- `similarity_search`: recupera vizinhos; `k` limita a quantidade, sem garantir relevância.
- `filter`: restringe a categoria por uma condição explícita definida no código.
- `@tool`: descreve a busca geral para o modelo; retorna texto e categoria de até dois trechos.
- `create_agent`: monta o ciclo de chamadas ao modelo e à ferramenta.
- `BaseCallbackHandler` e `config={"callbacks": [logger]}`: registram entrada real
  da ferramenta, resultado, fim das gerações da LLM e eventuais erros no terminal.
- `invoke()` executa cada pergunta; `input()` permite experimentar novas consultas.

Os dados ficam em `regras.json` e `perguntas.json`, ao lado do script. Os arquivos
são localizados a partir do script. Editar uma pergunta não altera as regras.

## Executar

Com o ambiente virtual do projeto ativado, a partir da raiz:

```powershell
python -m pip install langchain langchain-openai langchain-community faiss-cpu
cd "Agentes Cognitivos com LangChain/aula 19-10/Consultar regras de uma loja e registrar a busca"
python consultar_regras.py
```

Defina `OPENAI_API_KEY` no ambiente ou no `.env` da raiz do repositório.
Não versione a chave. O chat segue o padrão da aula: `gpt-4o-mini`,
`temperature=0`. Os vetores usam `text-embedding-3-small`.

O índice fica em memória e é reconstruído a cada execução. A indexação e cada
busca fazem chamadas de embeddings; o agente também faz chamadas ao modelo de
chat. Os logs aparecem no terminal, sem arquivo de log persistente.

## Como conferir

Antes de criar o agente, o programa executa a primeira pergunta diretamente no
índice: uma vez com `filter={"categoria": "retirada"}` e `k=1`, e outra sem
filtro com o mesmo `k`. Compare os resultados. O filtro foi escolhido no código;
ele não significa que a busca compreendeu a pergunta.

Depois, as duas perguntas passam pelo agente. Confira:

1. “Em que horário posso buscar minha encomenda?” deve localizar a regra de
   retirada e responder de segunda a sexta, das 09h às 17h.
2. “Qual é o prazo de reembolso?” deve reconhecer que esse prazo não consta nos
   trechos consultados. Nenhuma das três regras informa prazo de reembolso.
3. `[log ferramenta início]` mostra a consulta realmente enviada pelo modelo,
   que pode reformular a pergunta. `[log ferramenta fim]` mostra os trechos e
   categorias retornados. Os IDs relacionam início e fim da mesma chamada.
4. `[log LLM fim]` pode aparecer mais de uma vez por pergunta: o modelo primeiro
   pede uma busca e depois gera a resposta usando o retorno da ferramenta.

**Nenhum trecho recuperado** significa retorno vazio da busca. **Trecho
recuperado que não responde** significa retorno não vazio sem evidência para a
pergunta. Neste corpus pequeno, a busca geral com `k=2` costuma devolver dois
trechos inclusive para reembolso; isso não autoriza inventar um prazo.

O código verifica se houve uso observado da ferramenta e callbacks da LLM.
A fidelidade da resposta precisa ser conferida comparando os logs com a resposta;
as instruções do prompt não são uma garantia automática de correção semântica.
Falhas são exibidas e encerram o programa com código 1.

Referências: [agentes LangChain](https://docs.langchain.com/oss/python/langchain/agents),
[implementação FAISS](https://github.com/langchain-ai/langchain-community/blob/main/libs/community/langchain_community/vectorstores/faiss.py)
e [callbacks](https://reference.langchain.com/python/langchain-core/callbacks/base/BaseCallbackHandler).
