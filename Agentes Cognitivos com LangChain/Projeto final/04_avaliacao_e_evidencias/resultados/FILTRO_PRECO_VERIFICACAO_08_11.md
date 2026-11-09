# Teto de busca confundido com preço — 08/11/2026

## Falha observada e diagnóstico

A ferramenta retornou corretamente P009 (R$ 16,90, estoque 7) e P003 (R$ 18,50, estoque 16), filtrados até R$ 20 e ordenados por preço. O juiz semântico aprovou todas as afirmações. A checagem determinística bloqueou o cabeçalho “até R$ 20,00”, pois só aceitava os preços retornados como valores monetários.

O reparador preservou corretamente o teto e foi bloqueado outra vez pela mesma regra. Portanto, o problema desta execução era uma confusão de papéis na checagem Python, não uma falha do catálogo ou do juiz.

[Evidência original preservada](./fase05_20261109T011010952628Z.json).

## Decisão e alternativa

Aceitar uma ocorrência como teto somente quando ela estiver contextualizada como “até”, “teto”, “limite” ou “preço máximo” e coincidir com preco_max_centavos no plano de consulta estruturada efetivamente retornado com status ok.

Alternativa rejeitada: incluir o teto no conjunto global de preços permitidos. Isso poderia autorizar um preço de peça ou total de R$ 20 sem suporte. A correção não transforma o valor informado pelo cliente em preço comercial; associação de valores e condições continua também sob julgamento semântico.

## Testes e resultado

- 123 testes unittest passaram na cópia temporária, incluindo dois novos cenários de regressão.
- Replay da evidência original, usando o parecer real gravado como fixture: a resposta correta deixou de ser bloqueada. Esse replay não é uma nova chamada de LLM.
- Preço/total de R$ 20 sem suporte, teto de R$ 21 e teto sem plano observado continuam reprovados pelos casos negativos.
- [Nova execução com API](./fase05_teto_preco_corrigido_20261109T011414303680Z.json): listagem correta, verificação aprovada e zero reparos. Banco temporário, sem alterar a memória pessoal.
- Testes em test_verificacao.py; nenhuma troca de modelo nem nova dependência.

## Limites e continuidade

A identificação determinística de teto usa formas explícitas e delimitadas; não é interpretação universal de papéis monetários. O juiz continua necessário para associação peça/preço e coerência. A suíte anterior de 14 fixtures não continha esta listagem com teto no cabeçalho: passar uma amostra não garantia este caso. A falha foi acrescentada à regressão, preservando o registro anterior.

Decisão D40 no registro central. Reiniciar o atendimento carrega a correção. Não houve commit/push neste ajuste.
