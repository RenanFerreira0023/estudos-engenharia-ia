# Consulta estruturada das mensagens — fase 4

A pergunta em linguagem natural vira um `PlanoConsultaMensagens` tipado: contagem ou lista, autor, até quatro termos, período local, ordem e limite. O modelo não produz SQL executável. Python valida o plano e compila apenas `SELECT` sobre `mensagens_importadas`, sempre limitado à empresa e ao corpus autorizado. Valores entram por parâmetros, inclusive caracteres especiais de `LIKE`.

Exemplo com o corpus fictício: “Quantas mensagens de Bruno mencionam orçamento e Alfa?” produz `tipo=contagem`, `autor=Bruno`, `termos=[orçamento, Alfa]`. A consulta de fixture retorna **1** mensagem, a M0004. Isso é uma contagem dos textos que satisfazem os filtros, não um valor financeiro. A lista é limitada a 50 itens; `COUNT(*)` é a operação exaustiva.

No menu 9, o agente dispõe de `listar_corpora_acessiveis` e `consultar_mensagens_estruturado`. O planejamento com OpenAI exige chave configurada. O [notebook 11](../notebooks/incrementos/11_text_to_query_mensagens.ipynb) mostra o mesmo fluxo sem API por um plano fixture identificado. O teste local cobre contagem, lista, autorização entre usuários, fuso e tentativa de inserir SQL em um termo.

Esta consulta lê mensagens importadas. Não confirma pagamentos, não calcula saldo e não altera registros operacionais.

No primeiro teste real, a pergunta abreviada “Quantas msng o bruno mencionam orçamento e alfa?” foi roteada como projeto. O agente usou apenas busca top-k e respondeu “1”. Esse acerto aparente não é evidência de contagem: outros trechos poderiam ficar fora do top-k. A rota e o prompt foram ajustados, e o terminal agora substitui a resposta por uma limitação quando não há resultado estruturado de contagem.

No reteste, a pergunta completa foi roteada como `consulta`. O agente listou o corpus acessível e chamou `consultar_mensagens_estruturado`; o plano tinha `tipo=contagem`, `autor=Bruno` e os termos `orçamento` e `Alfa`. O `COUNT(*)` parametrizado retornou 1, e a resposta exibiu 1. [Registro da observação manual](../evidencias/fase4_text_to_query_reteste_manual.json).
