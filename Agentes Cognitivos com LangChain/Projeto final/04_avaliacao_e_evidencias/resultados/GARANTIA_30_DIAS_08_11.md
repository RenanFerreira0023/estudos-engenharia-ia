# Garantia de 30 dias — decisão de Renan em 08/11/2026

## Problema e decisão

A política anterior mantinha garantia sem prazo cadastrado. Renan definiu explicitamente que as peças têm 30 dias de garantia. O sistema deve responder esse prazo a partir da fonte consultada.

Foi atualizado o parágrafo Troca e garantia em politicas_loja.txt (V2) e o JSON loja_regras.json, com garantia.prazo_dias = 30. Garantia deixou a lista de políticas pendentes. Prazo inicial da contagem, cobertura e regras de troca não foram deduzidos.

Alternativa descartada: alterar apenas o prompt ou a resposta exibida. Isso deixaria o índice e a fonte estruturada divergentes da regra vigente. O FAISS foi preparado novamente com embeddings reais dos quatro documentos e os hashes foram atualizados.

## Verificação executada

- 121 testes unittest passaram no repositório após a alteração.
- O teste documental agora exige 30 dias de garantia e conserva a ausência de regra de troca.
- A checagem de integração de políticas passou a esperar o prazo cadastrado.
- Teste com atendente e juiz reais, em banco temporário: pergunta sobre prazo de garantia e possibilidade de troca depois de 30 dias. A resposta informou 30 dias de garantia e explicou que o prazo não autoriza inferir troca; verificação aprovada, sem alterar memória pessoal.
- [Evidência real](./fase05_garantia_30_dias_20261109T010802318672Z.json).

As fixtures manuais com garantia desconhecida continuam representando um cenário independente de avaliação. Evidências e relatórios antigos não foram reescritos como se essa política já existisse.

## Limites e continuidade

A regra é da loja fictícia deste projeto. Somente o prazo foi definido. O índice já foi atualizado; o atendimento que estava aberto precisa ser reiniciado para carregar a versão nova. Sem commit ou publicação neste ajuste.
