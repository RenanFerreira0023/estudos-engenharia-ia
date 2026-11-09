# Vários produtos no pedido

Em fase05_20261109T024540849106Z.json, o cliente informou correia de acessórios e filtro de óleo para Celta 2012 1.0 8V flex. A ferramenta voltou consulta_pendente e a resposta pediu categoria já informada. O juiz aprovou essa resposta inadequada. Não registrar esse caso como sucesso.

## D53

PlanoCatalogo.categoria aceita categoria única, null ou lista de até dez categorias da enumeração permitida. Listas vazias, valores arbitrários e SQL não são aceitos. Python expande o grupo correias e elimina duplicatas; múltiplas categorias viram IN com parâmetros. Veículo, estoque, preço máximo, ordenação e limite continuam compartilhados. Isso não suporta filtros independentes por item nem vários veículos no mesmo plano; nesses casos usar consultas separadas.

As instruções do atendente pedem consulta de todas as categorias identificadas e envio de todos os itens e quantidades ao cálculo Python. O cliente não precisa informar códigos. Filtro sem tipo continua ambíguo e deve motivar pergunta. A pendência D51 do juiz sobre esclarecimentos permanece separada desta alteração.

## Verificação

Cinco regressões locais cobrem P013 e P017 no Celta, total 5480 centavos com frete zero para Curitiba, agrupamento sem duplicação, rejeição de categorias inválidas, manutenção de pendência para filtro ambíguo e fluxo completo com modelos/juiz roteirizados. Esses modelos locais não são execução real de LLM. A suíte completa passou com 163 testes locais. Revalidação com API real em fase05_multiplos_produtos_20261109T030302907865Z.json: plano categoria=[correia_acessorios,filtro_oleo], consulta retornou P013/P017 e calcular_orcamento recebeu ambos, total 5480 centavos. A verificação aprovou a resposta.

Revisão manual: consulta, itens, preços, estoque e soma estão corretos. A resposta acrescentou "informação de frete não disponível" junto de frete R$ 0,00; isso é contraditório, pois o retorno confirmou frete_centavos=0 e deixou somente prazo pendente. Portanto, aprovação do juiz não comprova acerto completo. Falha de linguagem/juiz registrada separadamente em D54, pendente; não esconder esse resultado.

Teste manual: Quero 1 correia de acessórios e 1 filtro de óleo para Celta 2012 1.0 8V flex, entrega no CEP 81910-160. Consulte preço e estoque e calcule o pedido completo.

Esperado: filtro P013 R$ 24,90; correia P017 R$ 29,90; frete zero; total R$ 54,80; prazo não definido. Não confundir orçamento com compra/reserva nem associação cadastrada com homologação mecânica.
