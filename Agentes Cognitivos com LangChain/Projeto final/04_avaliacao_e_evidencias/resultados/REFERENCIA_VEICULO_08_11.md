# Referência de veículo, tipo de ID e citação — 08/11/2026

## Evidências recebidas

- [Listagem corrigida](./fase05_20261109T011707264375Z.json): valores, estoque e ordem corretos; o reparo removeu uma oferta de ajuda que o juiz tratou como sem suporte. Corrigida não significa preço errado neste caso.
- [Fusca consultado como Celta](./fase05_20261109T012015470569Z.json): o argumento V003 retornou P015, embora o cliente pedisse Fusca. O verificador impediu a publicação da candidata como resposta aprovada; não substituía a correção da consulta.
- [V004 enviado como produto](./fase05_20261109T012051607643Z.json): o agente confundiu o identificador de veículo com produto. A validação de citação ainda rejeitou trechos do juiz que haviam perdido acentos.

## Decisão D43: validar referência e guardar a referência efetiva

Uma regra local confere modelos e IDs explicitamente presentes no pedido atual contra as configurações cadastradas. Um pedido de Fusca não aceita consulta de Celta sem esclarecer a divergência. A consulta estruturada recebe o texto real do pedido, não apenas a paráfrase escolhida pelo agente.

Um V004 explicitamente informado pelo cliente e colocado indevidamente em produto_id é interpretado como veiculo_id, com registro do ajuste. Só ocorre se o ID existir e houver categoria; não se adivinha peça ou ID ausente. Produto escolhido pelo agente para outro modelo também não pode gerar orçamento quando diverge da referência declarada. Códigos de produto que o próprio cliente informou continuam sendo consultados pelo seu código; consulta não homologa aplicação mecânica.

Alternativa descartada: apenas repetir instruções no prompt. As falhas mostraram que isso não bastava. As validações usam a base e o pedido observado, sem outro modelo ou API.

O contexto comercial passou a guardar referencia_consulta, efetivamente executada, em vez de aprender V003 de um argumento descartado/normalizado. Isso corrige a origem de contaminação do estado identificada durante o diagnóstico. Perfil confirmado não é alterado por essa correção.

## Decisão D44: citação tolera diferença de acento, não novo conteúdo

A comparação de trechos do juiz aceita diferenças de espaços, Markdown e diacríticos, como Não/Nao e ignição/ignicao. Palavras, ordem e números ainda devem corresponder; referências de evidência continuam obrigatórias para afirmações sustentadas. Essa tolerância de grafia não substitui a verificação semântica nem aprova sozinha uma afirmação.

Alternativa descartada: desativar a validação de trechos ou aceitar paráfrases arbitrárias. Casos negativos continuam rejeitando número alterado e outra palavra.

## Testes e depois

132 testes unittest passaram na cópia temporária, incluindo oito novos cenários. Sintaxe dos sete arquivos Python validada. Os casos novos cobrem divergência Fusca/Celta, outros modelos cadastrados, V004 como veículo, ID não declarado, peça ambígua, orçamento de produto adivinhado para outro carro, consulta planejada, referência efetiva no estado e citações sem acento. Algumas condições são verificadas no mesmo caso de teste.

[Três atendimentos com API, perfil Celta e banco temporário](./fase05_referencia_veiculo_corrigida_20261109T013441535433Z.json):

1. Pedido do valor da vela do Fusca a ar: P021 cadastrada a R$ 14,90 e estoque zero, resposta aprovada.
2. Pedido de vela V004: mesmo preço/estoque, referência a veículo corretamente tratada, resposta aprovada.
3. Orçamento de 7 P009 para retirada: R$ 118,30, resposta final corrigida e liberada.

A memória pessoal não foi usada. O perfil de teste permaneceu Celta; a referência do pedido não foi gravada como nova confirmação permanente de veículo. As evidências anteriores foram preservadas, sem reescrever os erros.

## Limites e continuidade

As regras reconhecem nomes/IDs dos veículos cadastrados e referências explícitas; não são compreensão universal de apelidos, negações, comparações ou de todo o histórico. Pedido ambíguo ainda exige esclarecimento. Versão cadastrada e preço não comprovam compatibilidade da peça com o carro real. A especificação da vela do Fusca continua a confirmar.

O juiz ainda pode exigir reparo desnecessário, como no fechamento cordial da listagem. Isso foi registrado como limitação, sem remover salvaguardas indiscriminadamente. O presente ajuste não alterou o modelo nem a regra de no máximo um reparo.

Decisões D43 e D44. Sem commit/push. Reiniciar atendimento_verificado.py carrega a nova validação.
