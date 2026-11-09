# Regras fictícias de troca e garantia — 08/11/2026

## Autorização, decisão e motivo

Após definir 30 dias de garantia, Renan pediu explicitamente que o assistente criasse as demais regras. As condições abaixo foram propostas pelo assistente para o exercício e cadastradas por essa delegação; não foram extraídas de uma loja real.

- Garantia de 30 dias corridos contados do recebimento na entrega ou da retirada.
- Cobertura de defeito de fabricação confirmado após avaliação; exclusões de desgaste natural, mau uso e instalação inadequada.
- Solicitação de troca por preferência ou compra incorreta em até 7 dias corridos, com peça sem uso/instalação, embalagem original, acessórios completos e comprovante.
- Peça já usada/instalada não atende à troca por preferência, mesmo dentro dos 7 dias. Isso não decide automaticamente uma avaliação de defeito dentro dos 30 dias.
- Identificar peça, motivo e comprovante ao atendimento. O assistente explica e encaminha; não aprova troca, reembolso, reserva ou compra.
- Frete de devolução e prazo de avaliação continuam sujeitos à confirmação pelo atendimento.

Alternativa: continuar sem condições cadastradas e responder apenas a lacuna. A autorização para inventar regras motivou preencher o cenário acadêmico em vez de manter essa ausência. O prazo de 30 dias definido pelo usuário foi preservado, sem ser confundido com os 7 dias da troca por preferência.

## Implementação

Documento politicas_loja.txt V3 e loja_regras.json sincronizados; FAISS reconstruído com embeddings reais dos quatro parágrafos. Instrução do agente passou a exigir aplicar condições aos fatos já declarados, evitando repetir requisitos genericamente quando a peça já foi instalada. Regras de fonte/documento prevalecem sobre memória e sobre gabaritos antigos.

Foi corrigida também a indicação contraditória de documento ausente: se o planejador sugerir ausência de uma seção recuperada e documentada, o retorno preserva a sugestão em assuntos_sem_documento_sugeridos e remove essa seção de assuntos_sem_documento. Isso não confirma todos os campos de uma seção. O prompt do planejador deixou explícito que não deve presumir falta de prazo apenas a partir do título.

## Testes e evidências

- 124 testes unittest passaram no repositório com a política e o índice atualizados.
- Regressão documental confere 30 dias, 7 dias, requisitos distintos e ausência de aprovação automática.
- Regressão de proveniência reproduz seção documentada marcada como ausente e verifica a preservação da sugestão original.
- [Três atendimentos com API](./fase05_regras_troca_garantia_20261109T012104272272Z.json): troca de peça sem uso em 3 dias; defeito em 20 dias com avaliação sem aprovação automática; pedido sobre peça já instalada.
- A primeira resposta à peça instalada enumerou as condições sem concluir diretamente sobre o impedimento. Fonte e instrução foram explicitadas.
- [Repetição com API após a explicitação](./fase05_troca_instalacao_20261109T012449395585Z.json): explicou que instalação impede a modalidade de troca por preferência e distinguiu a avaliação de defeito dentro dos 30 dias. Verificação aprovada.
- Inspeção técnica do assistente conferiu as respostas e retornos, não apenas a nota do juiz. Todos os atendimentos usaram banco/sessões temporários, sem alterar memória pessoal.

## Limites

São condições fictícias do projeto. Não representam políticas legais de uma loja real ou validação jurídica. Não houve reembolso, troca efetiva ou envio de mensagem ao atendimento; essas operações continuam fora do sistema.

Fixtures manuais sobre garantia desconhecida representam cenário independente. Evidências históricas e gabaritos antigos não foram reescritos como se a política V3 já existisse. As decisões D41 e D42 documentam a delegação de regra e o ajuste de proveniência. Sem commit/push neste ajuste.

Reinicie atendimento_verificado.py para carregar as regras e a instrução novas.
