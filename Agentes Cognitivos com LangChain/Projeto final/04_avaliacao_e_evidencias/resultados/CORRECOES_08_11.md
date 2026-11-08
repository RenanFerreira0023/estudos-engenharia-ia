# Correções após os testes assistidos — 08/11/2026

## Falhas preservadas

- Frete sem produtos: `fase02_20261108T204418846658Z.json` consultou só o CEP e não a regra da loja.
- Correia: `fase02_20261108T204903908930Z.json` apresentou acessórios para um pedido de correia dentada.
- Óleo: `fase02_20261108T205000772452Z.json` respondeu 20W50/3,5 litros sem consulta técnica.

## Alterações

- Seis ferramentas, incluindo frete sem itens e consulta técnica estruturada aos arquivos existentes.
- Regra de entrega compartilhada: não há segunda fórmula de cálculo.
- Proteção do tipo pedido no catálogo e cálculo, com contexto restrito à chamada atual.
- Respostas específicas para óleo sem especificação e correia dentada, mesmo quando o modelo gera candidata inadequada.
- Candidata, resposta entregue e regra aplicada registradas separadamente. Não é um verificador geral.
- Avisos repetitivos removidos das respostas; metadados e dados-fonte preservados.

## Repetição real

Evidência: [correcao_08_11_real_20261108T205930568981Z.json](./correcao_08_11_real_20261108T205930568981Z.json). OpenAI/gpt-4o-mini; ViaCEP real nos dois casos de frete.

| Caso | Resposta entregue | Critérios específicos |
| --- | --- | --- |
| oleo | Não tenho especificações verificadas de viscosidade, norma e capacidade de óleo para essa configuração na base disponível. Preciso de uma fonte técnica aplicável ao veículo e ao motor antes de recomendar o óleo ou a quantidade de litros. | Passaram |
| correia | Para o Fusca 1982 1600 a ar, a informação técnica cadastrada indica que o sincronismo do comando é por engrenagens, não por correia dentada. A correia externa em V do alternador/dínamo tem outra função e não a substitui. A referência cadastrada é parcial; não valida código ou dimensões de uma peça. | Passaram |
| frete_sem_distancia | Infelizmente, não conseguimos calcular o frete para o CEP 01001-000, pois a cidade de São Paulo não possui distância cadastrada na tabela da loja. Portanto, não é possível fornecer uma cotação automática de frete ou total com entrega. Se precisar de mais informações ou ajuda, estou à disposição! | Passaram |
| frete_cadastrado | O frete para o CEP 84010-000 (Ponta Grossa - PR) é de R$ 5,31 e o prazo estimado para entrega é de 4 dias úteis. <br><br>Porém, não posso prometer uma data específica para a entrega, pois o marco inicial da contagem do prazo ainda está pendente. | Passaram |
| retirada | O orçamento para 2 unidades da Vela de ignição — Gol é o seguinte:<br><br>- **Preço unitário:** R$ 18,50<br>- **Subtotal:** R$ 37,00<br>- **Frete:** R$ 0,00 (retirada)<br>- **Total:** R$ 37,00<br><br>O produto está disponível em estoque. Se precisar de mais informações ou quiser prosseguir, é só avisar! | Passaram |
| sem_estoque | O produto "Correia em V do alternador/dínamo — Fusca" (SKU: CWB-SIM-P023) está com estoque zero, portanto não está disponível para retirada. Se precisar de outra informação ou de um produto diferente, estou à disposição! | Passaram |

As seis execuções passaram nos critérios registrados. As respostas finais foram lidas e conferidas pelo assistente.
As notas são checagens finitas de ferramenta, valores e texto; não certificam semântica universal.

## Testes locais

Resultado e log completo: [correcao_08_11_testes_locais.json](./correcao_08_11_testes_locais.json).
As regressões repetem as respostas/chamadas das falhas anteriores com modelo roteirizado, sem API.
Cobrem também cálculo direto de peça divergente, destino incompleto, mesma regra de frete, ausência de fonte e saudação.

## Limites

- Fontes técnicas são as já registradas; referências parciais continuam identificadas. Nenhuma especificação de óleo foi cadastrada.
- A resposta de óleo não é liberada enquanto não houver contrato/fonte verificada; adicionar fontes exigirá ampliar a regra e os testes.
- Reconhecimento das perguntas protegidas tem alcance lexical; não é NLI nem proteção de todos os possíveis enunciados.
- AutoTools, memória, RAG, auditor semântico geral e LangSmith continuam pendentes.
- Notebooks anteriores e falhas históricas foram mantidos. Esta revisão tem execução CLI/API e testes próprios.
- A interface CLI deve ser reiniciada para carregar o código novo.
