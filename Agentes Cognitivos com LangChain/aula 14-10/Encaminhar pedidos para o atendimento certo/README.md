# Encaminhar pedidos para o atendimento certo

Simula a chegada de uma mensagem à loja de autopeças. A cada execução,
`random.choice()` sorteia um registro de `mensagens-clientes-autopecas.json` e
usa seu texto como se tivesse sido digitado pelo cliente. O sorteio pode repetir
uma mensagem em execuções diferentes.

```text
JSON → sorteio de uma mensagem → invoke(texto)
  → mensagem original preservada + classificação
  → função de roteamento
      vendas    → coleta dados do veículo e da peça
      pos_venda → coleta pedido e descrição do problema
      outro rótulo → “Não consegui definir o atendimento”
```

## Conceitos praticados

- `ChatPromptTemplate`: cria os prompts de classificação, vendas e pós-venda.
- `StrOutputParser`: obtém o texto de cada resposta do modelo.
- LCEL (`|`): conecta as etapas; montar o fluxo ainda não chama o modelo.
- `RunnablePassthrough`: mantém a mensagem original na chave `mensagem`.
- `RunnableLambda`: executa a função que escolhe a chain de atendimento.
- `strip().lower()`: normaliza o rótulo; só `vendas` e `pos_venda` são aceitos.
- `invoke`: executa o fluxo para a mensagem sorteada e a chain selecionada.

O dicionário intermediário é montado assim:

```python
{
    "mensagem": RunnablePassthrough(),
    "classificacao": classificadora,
}
```

A classificadora recebe a string e produz o rótulo, enquanto o passthrough
preserva o mesmo texto. A função registra a rota e entrega à chain escolhida
`{"mensagem": dados["mensagem"]}`. A outra chain não é executada.

## Executar

Com o ambiente virtual ativado, instale `langchain-openai`, entre nesta pasta e rode:

```powershell
python -m pip install langchain-openai
python encaminhar_pedidos.py
```

Defina `OPENAI_API_KEY` no ambiente ou no `.env` da raiz do repositório.
Não versione chaves. O modelo usado é `gpt-4o-mini`.

Pressione Enter para sortear e enviar uma mensagem. O terminal exibe o ID,
o texto original, a rota escolhida e a resposta. Execute novamente para outro
sorteio. Cada simulação válida faz duas chamadas ao modelo: uma para classificar
e outra para responder. Nenhuma mensagem é enviada a clientes reais.

## Como conferir

Antes do sorteio, o script testa a função isoladamente com classificação
fictícia `outro`. Deve registrar esse rótulo e retornar exatamente
`Não consegui definir o atendimento`, sem executar nenhuma chain de atendimento.

- Consulta antes da compra → `vendas`: pedir modelo, ano e identificação da peça,
  aproveitando os dados já informados, sem inventar preço ou disponibilidade.
- Problema de compra realizada → `pos_venda`: pedir número do pedido e descrição
  do problema, aproveitando os dados já informados, sem prometer troca, prazo ou reembolso.
- Um rótulo como ` VENDAS ` é normalizado; `vendas.` ou `pós-venda` são rejeitados.

Os prompts orientam o modelo; confira se a rota combina com a mensagem e se a
resposta respeita essas restrições. Nomes dos clientes não entram nos prompts.
