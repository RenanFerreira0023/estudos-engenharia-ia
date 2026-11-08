# Base manual — implementação e verificação em 08/11/2026

Plano revisado conforme decisão de Renan: catálogo externo fora do atendimento; base JSON curada; quatro veículos originais e uma S10 2014 2.8 CTDI diesel. ViaCEP preservado. Preços/estoques e 24 aplicações comerciais não foram alterados. Especialidade planejada: óleo/manutenção básica, freios, pneus, velas, correias e alternador.

## O que foi implementado

42 registros técnicos com status/fontes e perguntas por assunto. Onze registros têm campos verificados em manuais oficiais nesta revisão; vários campos continuam pendentes. Consulta técnica ampliada; apresentação de óleo baseada no retorno estruturado do turno, com proteção contra fonte de outro modelo/ano explicitamente informado. Intervalos por norma e uso, sem média genérica. Consulta técnica não homologa produto comercial fictício.

## Testes locais

- Suíte em tests/: 63 testes aprovados, dos quais 13 novos de base manual.
- verificar_fase02.py: 18 testes aprovados (expectativa de veículos atualizada de quatro para cinco; quantidades comerciais mantidas).
- Total: 81 verificações locais, sem rede e sem LLM real. Modelos roteirizados verificam contratos/ciclo de ferramentas, não compreensão de linguagem.
- A primeira cópia temporária de teste não incluía fixtures antigas; houve erros de arquivo ausente. As fixtures e a evidência histórica referenciada foram copiadas, sem remover testes nem alterar regras para fazê-los passar. As execuções finais acima passaram.
- Após a rodada real: corrigida a pontuação de apresentação dos intervalos e acrescentada uma guarda para preservar a condição ar-condicionado e/ou direção hidráulica na resposta de alternador do Celta. Regressões locais pertinentes foram repetidas.

## Seis casos com modelo real

Arquivo: [base_manual_real_20261108T224916554603Z.json](./base_manual_real_20261108T224916554603Z.json).

| Caso | Consulta técnica observada | Resultado observado |
|---|---|---|
| Celta 2012, óleo | V003 / oleo | Especificação, capacidades e dois regimes documentados |
| S10 diesel 2014, óleo | V005 / oleo | Normas/intervalos distintos; capacidade mantida pendente |
| Fusca 1982, óleo | V004 / oleo | Sem recomendar viscosidade/litros sem fonte |
| Celta, pneus originais, até três pessoas | V003 / pneus | Pressão de 27 psi a frio |
| Celta com ar-condicionado, alternador | V003 / alternador | 90 A, sem inventar código da peça |
| Celta 8V, correia dentada | V003 / sincronismo | Tipo confirmado; código e intervalo mantidos pendentes |

As seis chamadas usaram OpenAI/gpt-4o-mini com a configuração existente, sem copiar ou expor a chave. Os seis critérios locais (consulta correta e trechos esperados) foram atendidos. A trajetória registra as chamadas e os retornos. Na revisão humana assistida, a resposta de alternador acertou 90 A para o pedido com ar, mas simplificou a configuração sem ar e omitiu direção hidráulica ao acrescentar essa informação. A resposta original foi preservada; uma guarda específica e um teste de regressão corrigem essa condição na versão atual. Portanto, seis critérios atendidos não significam seis respostas integralmente verificadas sem ressalvas.

Não houve execução real de ViaCEP nesta rodada: nenhum dos seis pedidos precisava de CEP. Não houve nova execução dos notebooks, instalação limpa, avaliação LangSmith ou juiz semântico. A checagem de trechos não é taxa geral de acerto nem avaliação completa de segurança técnica.

## Lacunas e continuidade

Gol, Palio e Fusca continuam sem especificação de óleo liberada até manual aplicável; o recorte S10 não tem produtos/preços comerciais. Código/intervalo de correias, manutenção de velas e várias aplicações exigem mais curadoria. Nada disso foi preenchido por palpite.

As fases de memória, RAG/text-to-query, verificação geral, interface, LangSmith e entregas continuam na ordem do plano. A fase 2 ainda recebe mensagens independentes. Esta revisão fecha o escopo e a infraestrutura da base manual; não declara todas as fases prontas.
