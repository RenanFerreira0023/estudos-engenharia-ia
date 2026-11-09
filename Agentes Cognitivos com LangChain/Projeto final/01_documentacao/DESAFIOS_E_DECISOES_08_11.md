# Desafios e decisões — testes de 08/11/2026

Este registro explica decisões de engenharia a partir de chamadas, argumentos e resultados observáveis. Não representa pensamentos internos do modelo. Os nomes dos JSON usam UTC; arquivos com 20261109T00 correspondem à noite de 08/11 em São Paulo.

## 1. Dados iguais dificultavam conferir ordenação

**Problema:** as quatro velas custavam R$ 18,50 e tinham estoque 16; a listagem não exercitava exclusão por preço/estoque nem uma ordenação com valores distintos.

**Decisão e motivo:** variar a base comercial nos dois JSON sincronizados: P003 R$ 18,50/saldo 16; P009 R$ 16,90/saldo 7; P015 R$ 24,90/saldo 12; P021 R$ 14,90/saldo 0. Alternativa: manter os dados e testar apenas empates; não demonstraria todos os filtros solicitados.

**Evidência:** [antes](../04_avaliacao_e_evidencias/resultados/fase04_20261108T235944123361Z.json) e [depois](../04_avaliacao_e_evidencias/resultados/fase04_20261109T000756177581Z.json). A busca real até R$ 20 com saldo retornou P009 e P003, nessa ordem. Na cópia temporária, 100 testes unittest passaram.

**Limite:** valores didáticos; a alteração não homologa aplicação mecânica.

## 2. “Velas” não correspondia a “vela”

**Problema observado:** o agente identificou V002, mas enviou categoria `velas`. A comparação SQL literal com `vela` voltou vazia e a resposta confundiu ausência de correspondência com possível falta de estoque.

**Decisão e motivo:** normalizar acentos, caixa e espaços e traduzir aliases explícitos nas dez categorias reconhecidas pela consulta. Alternativa: só instruir o LLM a sempre emitir singular; uma regra local evita depender dessa geração.

**Evidência:** [falha](../04_avaliacao_e_evidencias/resultados/fase04_20261109T000956017873Z.json) e [consulta corrigida](../04_avaliacao_e_evidencias/resultados/fase04_20261109T001430848414Z.json). O mesmo argumento `velas` passou a consultar `vela`, localizou P009 e o orçamento sinalizou pedido de 8 para saldo 7. Os 103 testes locais passaram; regressões em [test_categorias_catalogo.py](../02_codigo/tests/test_categorias_catalogo.py).

**Limite:** aliases são uma lista explícita, não compreensão universal de sinônimos. “Filtro” e “correia” não escolhem automaticamente um tipo. Correia dentada permanece distinta de correia de acessórios.

## 3. “Pode ser” perdeu o código da peça

**Problema observado:** após oferecer 7 velas do Palio, o agente enviou V001 como produto. A validação recusou a operação; não ocorreu reserva ou cálculo de outra peça.

**Decisão e motivo:** conservar IDs de produtos, veículo do pedido e argumentos do último orçamento observados nas ferramentas em contexto SQLite por cliente/sessão. Não guardar preços como fonte atual. Alternativa: depender apenas do texto final da conversa, que não preservava esses IDs de forma confiável.

**Evidência:** [falha real da continuação](../04_avaliacao_e_evidencias/resultados/fase04_20261109T001649479530Z.json) e [validação real após a correção](../04_avaliacao_e_evidencias/resultados/fase04_contexto_real_20261109T002432900471Z.json). Com perfil Celta e pedido Palio, a sequência 8 velas → saldo 7 → “pode ser” calculou P009, quantidade 7 e total R$ 118,30.

**Limite:** o modelo ainda decide como resolver a continuação. Contexto não garante todas as paráfrases; múltiplos itens ambíguos exigem esclarecimento. Saldo anterior é contextual, não reserva. Nova sessão inicia contexto vazio; /esquecer apaga esse contexto; confirmação explícita /veiculo limpa o pedido anterior.

## 4. Veículo salvo contaminou consulta por produto

**Problema observado:** a busca P009 recebeu V003 (Celta), embora o atendimento tratasse do Palio. O filtro conjunto escondeu um produto existente.

**Decisão e motivo:** perfil é padrão, com prioridade para o veículo do pedido da sessão. Consulta por código explícito sem pergunta de aplicação/veículo ignora filtros adicionais herdados e registra o descarte no retorno. Alternativas: apagar o perfil ou trocar de cliente para cada orçamento; o isolamento ajudou no diagnóstico, mas não solucionava a causa.

**Evidência:** [falha com filtro V003](../04_avaliacao_e_evidencias/resultados/fase04_20261109T001748177100Z.json), [controle com cliente separado](../04_avaliacao_e_evidencias/resultados/fase04_20261109T001838351190Z.json) e [depois com perfil Celta no mesmo teste](../04_avaliacao_e_evidencias/resultados/fase04_contexto_real_20261109T002432900471Z.json).

**Limite:** a identificação de pedido direto por código usa critérios determinísticos delimitados. Perguntas sobre servir/aplicar no veículo mantêm filtros de aplicação; localizar um código não prova compatibilidade.

## Validação e limites gerais

- 107 testes unittest passaram na cópia temporária final; os quatro testes novos também passaram no repositório após aplicar a correção. Sintaxe dos cinco arquivos Python afetados validada com py_compile.
- Modelo roteirizado/fixtures locais testam contratos e passagem de contexto; não são evidências de compreensão por LLM.
- Integração real: três mensagens com API, banco temporário e perfil Celta; os três critérios de ferramenta/cálculo passaram. A memória pessoal de Renan não foi usada ou alterada.
- Uma tentativa anterior no sandbox terminou em erro de conexão e não validou o comportamento; o teste real foi repetido com acesso à rede. Nenhuma métrica LangSmith foi produzida.
- O teste real valida esses três casos, não todas as conversas. Verificador geral, interface e avaliação LangSmith continuam incrementos posteriores.
- Referência de commit: ainda não associada por este registro; nenhum commit/push foi executado pelo assistente neste incremento.
