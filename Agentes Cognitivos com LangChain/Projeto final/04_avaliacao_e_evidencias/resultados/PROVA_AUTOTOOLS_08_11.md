# AutoTools — prova real de cobertura em 08/11/2026

## Resultado

Foram executadas **nove requisições HTTP reais**, todas com HTTP 200, Content-Type
application/json e JSON válido: quatro buscas restritas, quatro amplas e uma busca
alternativa pelo nome Beetle. Não foi confirmada identidade útil dos veículos locais.

| Veículo local | Busca restrita | Busca ampla | Conclusão limitada às consultas feitas |
| --- | --- | --- | --- |
| Gol 2010 1.0 8V flex | Sem resultados | Dois Golf 2019, motores DADA e CRBC | Golf não é Gol; configurações rejeitadas. |
| Palio 2010 1.0 Fire 8V flex | Sem resultados | Sem resultados | Nenhum candidato retornado. |
| Celta 2012 1.0 8V flex | Sem resultados | Sem resultados | Nenhum candidato retornado. |
| Fusca 1982 1600 a ar gasolina | Sem resultados | Sem resultados | Busca adicional Beetle também vazia. |

Os filtros incluíram marca, modelo, ano, motor e combustível. Busca ampla removeu esses
filtros e manteve somente o nome, com limite de dez resultados. Os totais retornados foram
zero ou dois; não havia resultados adicionais nessas respostas. Isso é evidência pontual,
não prova de ausência definitiva em toda a base ou de impossibilidade de integração futura.

## Evidências reais

- [Quatro veículos, buscas restritas/amplas e comparações](./autotools_real_20261108T211206838473Z.json).
- [Busca exploratória Beetle](./autotools_alias_beetle_real.json).
- [68 testes locais e log](./autotools_testes_locais.json).

O JSON inicial preserva o diagnóstico da primeira versão: a comparação buscava `fuel`,
enquanto a resposta real utiliza `fuel_type`. O cliente de prova foi ajustado para ler
esse campo, e o teste de contrato confere Petrol sem tratá-lo como flex. Isso não altera
a rejeição dos Golf por modelo, ano e motor; os retornos HTTP originais foram mantidos.
Outra adaptação usa o ID da api_url oficial retornada pela busca, sem inventar IDs.

## O que foi e não foi testado

- Rede, status HTTP, Content-Type e contrato da busca: executados de verdade.
- Retornos reais lidos: Gol trouxe Golf 2019; demais buscas retornaram data vazia.
- Timeout, indisponibilidade, HTML com HTTP 200, JSON inválido e contrato incorreto:
  testados com transporte injetado e explicitamente identificados como fixtures.
- Versão ambígua/incompleta e mercado ausente: não autorizam leitura de óleo/peças como se
  fossem do nosso carro. Golf não foi usado como demonstração substituta.
- Detalhes, parts e oil: contratos locais testados, **sem execução HTTP real dessas seções**,
  pois nenhum veículo local foi identificado. Não afirmar que óleo está disponível ou indisponível
  para nossos motores com base apenas nas buscas.
- Não foram feitas chamadas à OpenAI, alterações no catálogo ou recomendações técnicas.

## Documentação e termos

Fontes consultadas nesta revisão:

- [API pública AutoTools](https://autotools.brightcoding.dev/docs): anuncia acesso sem chave,
  uso justo e atribuição. A origem deve ser citada em eventual uso dos dados.
- [Termos AutoTools](https://autotools.brightcoding.dev/terms): uso educacional, sem garantia,
  especificações variáveis por ano/mercado e restrição a cópia substancial para reutilização comercial.

A redação da documentação sobre uso comercial é mais ampla que a dos termos gerais.
Esta prova é acadêmica; ela não presume licença irrestrita para redistribuir uma base comercial.
Dados externos não substituem manual aplicável, preço/estoque local ou mapeamento de aplicação.

## Decisão

Manter `ClienteAutoTools` e `provar_autotools.py` como prova reproduzível, sem expor uma
ferramenta técnica AutoTools no atendente neste momento. Nenhum produto local foi relacionado
a código externo, e nenhuma especificação de óleo foi preenchida. O agente continua usando
as seis ferramentas existentes e a API real ViaCEP.

Uma futura ampliação/troca do catálogo exige decisão de Renan. Não foi escolhido outro carro
ou mercado para fazer a integração parecer concluída. O próximo incremento independente é memória.
