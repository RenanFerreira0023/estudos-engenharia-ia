# Fusca TSI e desambiguação — 08/11/2026

## Solicitação e recortes

Renan pediu incluir Fusca TSI para que “Fusca” não seja escolhido automaticamente como clássico. Foi escolhido um recorte de estudo com manual oficial disponível:

| ID | Configuração | Uso na base |
|---|---|---|
| V004 | Fusca 1982, 1600 a ar, gasolina | Clássico; mantém seus produtos e aplicações anteriores. |
| V006 | Fusca 2014, 2.0 TSI, gasolina | Recorte técnico moderno; sem novos produtos ou aplicações comerciais. |

O ano 2014 foi uma escolha de implementação, não uma declaração de que o carro pessoal de Renan tenha esse ano. Não se estendeu a cobertura automaticamente para todos os anos ou códigos de motor TSI.

## Fonte, informações e lacunas

[SRC08: manual oficial Volkswagen Fusca 2014, edição 07/2013](https://www.vw.com.br/idhub/content/dam/onehub_pkw/importers/br/literatura-de-bordo/manual-fusca/manual-fusca-my-2014-edicao-072013/141.5B1.B5C_66_2_FUSCA_MANUAL_INSTRUCOES.pdf), localizado no [portal da Volkswagen](https://www.vw.com.br/pt/servicos-e-acessorios/servicos-e-produtos/manuais-e-garantia/manuais.html). A leitura textual confirmou motorização TSI a gasolina, referência ao sistema de arrefecimento líquido e norma de fluido de freio VW 501 14. A captura de imagem do PDF não ficou disponível na ferramenta; não foi declarada inspeção visual das tabelas.

Foram cadastrados arquitetura/arrefecimento e referência de freios. Óleo, capacidade, intervalo, sincronismo, código de bomba, velas, pneus e alternador permanecem pendentes onde não houve confirmação específica. Não se combinou uma tabela genérica de lubrificantes com código de motor não confirmado para sugerir viscosidade ou litros.

Documentos estruturados e agregado JSON sincronizados. A carga em SQLite lê os novos dados ao iniciar. As políticas da loja e seu FAISS não mudaram neste incremento: a base técnica é consultada como registros estruturados, não como RAG de políticas.

## Decisões

**D45 — separar a geração:** manter o nome Fusca nos dois recortes e distinguir ano, motor, geração e refrigeração. Alternativa rejeitada: renomear o clássico de forma a esconder a ambiguidade ou copiar peças para o TSI. V006 não recebeu produtos fictícios, estoques ou preços do V004.

**D46 — validar identificação antes de gerar e conservar referência na sessão:** quando uma pergunta sobre peça/especificação diz apenas Fusca, o controlador pede identificação com as duas opções. É uma pergunta controlada de dados faltantes, sem executar LLM ou juiz; a verificação usa status identificacao_pendente, não uma aprovação semântica fictícia. Políticas gerais como garantia ou pagamento não exigem escolher o Fusca.

Uma declaração de ID ou de ano + geração que identifica um único recorte atualiza somente a referência da sessão. O perfil permanente continua dependendo de confirmação explícita. Pronomes delimitados como “nele” usam essa referência observada para validar os argumentos; a mensagem original do cliente é preservada no registro. Filtro declarado por ID/ano/geração não desaparece quando o planejador o omite, e plano original/e efetivo ficam registrados.

Produto existente sem aplicação para o recorte recebe aplicacao_nao_cadastrada, com identificação e vínculos existentes separados, sem tratar isso como preço do TSI ou inexistência global. Isso não prova incompatibilidade física; significa que a aplicação não foi confirmada na base.

## Testes, falhas e resultados

- 144 testes unittest passaram no repositório. Oito casos iniciais e quatro de fluxo cobrem nova configuração, enum V006, falta de produtos vinculados, ambiguidade, ano/geração, consulta técnica, contexto declarado, pronome, pergunta controlada sem modelo/juiz e preservação de filtros.
- [Primeira integração](./fase05_fusca_tsi_20261109T015416800851Z.json): arrefecimento foi respondido corretamente, mas a identificação genérica terminou em explicação pouco direta e a continuação ainda podia usar o perfil clássico. O juiz aprovou uma resposta genérica sobre P021 que não esclarecia o vínculo ao TSI. Essa rodada não foi tratada como sucesso completo.
- A falha motivou o esclarecimento anterior à geração, referência declarada na sessão e distinção explícita entre produto existente e aplicação ausente.
- [Integração final](./fase05_fusca_tsi_final_20261109T020723512012Z.json): a pergunta genérica pediu escolher V004 ou V006 sem executar modelo/juiz; a resposta seguinte informou arrefecimento líquido do TSI; a pergunta sobre usar P021 explicou ausência de aplicação cadastrada ao Fusca TSI.
- As duas respostas geradas da rodada final passaram após o único reparo permitido. O esclarecimento inicial não teve nota LLM.
- O perfil de teste permaneceu V004 e a referência final da conversa ficou V006. Banco temporário, sem acessar ou alterar a memória pessoal de Renan.

Não se fez teste de todas as formulações possíveis. Apelidos, pronomes e comparações arbitrárias não são resolvidos universalmente. “Identificação pendente” não significa falta de estoque; “aplicação não cadastrada” não significa peça inexistente ou incompatibilidade física comprovada. Especificação e compatibilidade reais exigem os dados corretos da versão.

Registros D45–D46, README e plano atualizados. Sem commit ou publicação. Reinicie atendimento_verificado.py para carregar a base e o código novos.
