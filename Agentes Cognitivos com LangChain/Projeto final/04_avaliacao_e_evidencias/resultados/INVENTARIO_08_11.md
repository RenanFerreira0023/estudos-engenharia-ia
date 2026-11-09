# Listagem de inventário — 08/11

O teste manual retornou `consulta_pendente` para todos os produtos do Fusca 1982 por falta de categoria. Perguntas sobre correias do Palio e produtos do Gol não chamaram ferramenta. Esses casos não demonstravam ausência de produtos.

A consulta estruturada agora aceita categoria opcional e explica essa regra no prompt. Uma correção restrita remove somente a pendência indevida de categoria em listagens explícitas, preservando o plano original. Pendências de motor, ano e operações proibidas continuam bloqueadas.

O middleware exige consulta estruturada no turno de inventário. Política tem prioridade em pedidos compostos. A consulta não é repetida depois do retorno da ferramenta no mesmo turno.

O grupo `correias` lista correias dentadas e de acessórios sem tratá-las como equivalentes. O retorno informa configurações cadastradas e se o limite da lista foi atingido. Uma pergunta por todos os anos do Gol deve esclarecer que só existe o recorte 2010 na base.

Validação: 150 testes locais passaram, incluindo seis regressões de inventário com SQLite e SDK HTTP roteirizado. São fixtures locais, não avaliação de compreensão por LLM. A tentativa inicial de API sofreu OpenAIConnectionError por restrição de rede; não foi aprovada nem tratada como resposta do agente. Revalidação real executada nos arquivos abaixo. As três listagens foram verificadas manualmente contra os retornos das ferramentas; isso não prova acerto universal do agente.

- fase05_inventario_real_20261109T022959064698Z.json: Fusca retornou seis produtos; Gol retornou seis produtos e explicitou recorte 2010. Palio ainda pediu ano/motor por confundir inventário com aplicação.
- fase05_inventario_palio_20261109T023142882148Z.json: após esclarecer o contrato no prompt, Palio retornou correia de acessórios, R$ 29,90 e estoque 5, identificando Palio 2010 1.0 Fire 8V. O juiz executou um reparo por considerar a despedida sem suporte; os valores centrais já estavam corretos.

O teste extra "Qual correia serve no meu Palio?" não confirmou aplicação indevida: o gerador pediu ano/motor. Porém, o juiz reprovou esse esclarecimento por ausência de suporte e a saída final virou limitação genérica. D51 registra essa falha observada como pendente. Não confundir correção do inventário com correção do juiz.

Não foram adicionados produtos para S10/TSI: D49 continua pendente. A remoção dos avisos repetitivos e a confusão entre estoque zero e existência seguem nos registros D47/D48.

Repetir no atendimento_verificado.py:

1. Consulte o catálogo e liste todos os produtos cadastrados para o Fusca 1982 1600 a ar, não apenas velas. Informe preço e estoque.
2. Quais correias você tem do Palio?
3. Quais produtos você tem do Gol? Todos os anos.
