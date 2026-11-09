# Totais dos itens — 08/11

## Falha observada

Em fase05_20261109T023553805987Z.json, o cliente pediu três litros de P024 (3990 centavos cada), um jogo P022 (8990) e uma peneira P019 (2490), com entrega em Curitiba. A ferramenta calculou 23450 centavos e frete zero; prazo indefinido. O juiz considerou a resposta sustentada, mas Python bloqueou 11970 como valor sem evidência e comparou cada rótulo Total dos itens ao total geral 23450. O reparo continuou bloqueado pelo valor derivado 11970.

## Decisão D52

Derivar somente multiplicações inteiras a partir dos itens do retorno de calcular_orcamento com status ok/parcial e total não nulo. Quantidades/preços declarados pelo cliente não autorizam valores. O conjunto de valores monetários inclui esses resultados calculados.

Na verificação de rótulos, Total/Subtotal dentro de item numerado e indentado corresponde ao item daquela posição no orçamento. Total do item/da linha também identifica valor do item. Rótulos fora do bloco e Total geral/do pedido continuam comparados ao total do pedido. Frete continua separado. Formatações ambíguas podem exigir reparo; a interpretação não é universal para qualquer layout.

A associação semântica entre produto, quantidade e preço continua sujeita ao juiz; não foi substituída por aprovação automática só porque o número aparece na ferramenta.

## Verificação local

Oito regressões cobrem a resposta original e reparada, erro de um centavo, total geral substituído pelo total de um item, frete errado, valor de outro item dentro de bloco numerado, Markdown, fonte declarada sem ferramenta, orçamento pendente e preservação da reprovação semântica.

O parecer real já gravado foi reutilizado em um replay local: a resposta original passou sem reparo após a correção das regras. Isso não é uma nova execução de LLM nem uma métrica do LangSmith. Evidência original preservada. Suíte completa: 158 testes locais passaram.

## Repetição manual

Reinicie atendimento_verificado.py, selecione /cliente teste_orcamento_itens e liste os produtos do Fusca 1982 1600 a ar. Depois envie: vou querer 3L de óleo, 1 jogo de cabos de ignição e uma peneira. Quanto fica o frete para 81910-160?

Esperado: óleo R$ 119,70; cabos R$ 89,90; peneira R$ 24,90; frete R$ 0,00; total R$ 234,50. Prazo sem definição. Esse orçamento não comprova a especificação técnica do óleo nem capacidade do motor.
