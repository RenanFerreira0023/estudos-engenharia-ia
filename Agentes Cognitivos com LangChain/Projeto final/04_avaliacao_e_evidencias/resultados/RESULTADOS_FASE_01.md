# Resultados da fase 1 — 02/11/2026

Somente chain inicial, em Python 3.12.6. As versões diretas estão fixadas em
`02_codigo/requirements.txt`. O notebook principal foi executado em kernel novo,
do início ao fim, com modo **real**, OpenAI / `gpt-4o-mini`.

## Verificações finais

| Verificação | Resultado observado |
| --- | --- |
| Testes locais com unittest | 16 executados, zero falhas e zero erros, incluindo execução direta do arquivo. |
| Nove casos com dummy roteirizado | 9/9; verifica encadeamento e validação, não compreensão por LLM. |
| Nove casos com modelo real, após revisões | 9/9 no lote registrado abaixo. |
| Composições @chain e LCEL, modelo real | Mesmo JSON observado para o exemplo do Gol; etapas e contrato são os mesmos. |
| Notebook real | Todas as células executadas sem erro não tratado. |
| Dependências | `pip check`: No broken requirements found. |

Evidências finais:

- [unittest — 16 testes](./fase01_unittest_20261102T184419294226Z.json)
- [lote real — 9 casos](./fase01_real_20261102T183637172353Z.json)
- [notebook executado com modelo real](../../03_notebooks/fase_01_chain_inicial.ipynb)
- [notebook executado em modo simulado](./fase01_notebook_simulado.ipynb)
- [testes manuais e conferência da CLI](./TESTES_MANUAIS_FASE_01.md)
- [saídas brutas da CLI assistida](./fase01_cli_assistida_20261102T190918839535Z.json)

## O que os resultados demonstram

No exemplo “Tenho um Gol 2010 1.0 e quero duas velas”, o modelo identificou
`consulta_peca`, `Gol`, `2010`, `1.0`, `vela` e quantidade `2`. Combustível ficou
`null`, com `veiculo.combustivel` em `campos_faltantes`. Não acrescentou `8V`.

O combustível foi preservado quando explicitamente informado. Filtro genérico
continuou ambíguo; pagamento não exigiu veículo. O CEP `01001-000` resultou em
`01001000`, sem perder o zero inicial. Quantidade zero e CEP de três dígitos
foram rejeitados, sem dados apresentados como validados. A saudação ficou com
intenção desconhecida. Orçamento sem quantidade pediu somente a quantidade
quando os demais campos necessários estavam presentes.

Os testes locais também cobrem quantidade negativa/fracionária, booleano ou
string no lugar de inteiro, campos extras de preço/compatibilidade, JSON inválido,
entrada vazia sem chamada à LLM e falha de modelo sem exposição de detalhes internos.
Falhas deliberadas de parser/conexão nesses testes são simulações identificadas,
não incidentes atribuídos ao provedor.

A CLI também foi conferida por execução direta do `.py` a partir de outra pasta,
sem `PYTHONPATH`, usando `--help` sem chamar a API. Isso cobre o erro de importação
relativa observado ao usar o botão do VS Code. As composições importadas pelo
notebook mantêm o mesmo comportamento.

A conferência posterior de terminal também executou uma mensagem real ao modelo
e encerramento com `/sair`. A transcrição do erro enviada pelo usuário e os testes
assistidos estão identificados por origem no registro manual vinculado acima.

## Falhas reais preservadas e correções

| Execução real | Observação | Revisão |
| --- | --- | --- |
| [5/9](./fase01_real_20261102T183027241397Z.json) | Ausência de veículo foi devolvida como `veiculo: null` em quatro casos; o schema exigia objeto. | Prompt explicita o objeto; normalização converte somente a ausência em campos nulos, sem inventar fatos. Novo teste local. |
| [0/9 por ambiente](./fase01_real_20261102T183140100401Z.json) | Rede bloqueada no sandbox; os casos retornaram erro de modelo. | Reexecutar com acesso autorizado; sem fallback para dummy. |
| [8/9](./fase01_real_20261102T183231362697Z.json) | A mensagem de orçamento continha “flex”, mas o modelo o omitiu. | Reforçar descrição do campo e preservação de combustível explícito. |
| [9/9 final](./fase01_real_20261102T183637172353Z.json) | Os nove resultados atenderam às expectativas registradas. | Saídas finais no notebook; observados anteriores permanecem intactos. |

Há também notebooks parciais de falha, incluindo a primeira tentativa de iniciar
o kernel no sandbox. Eles não são apresentados como execuções completas.

## Limites

9/9 é o resultado deste lote, não uma garantia de fidelidade para qualquer texto
ou execução futura. Pydantic comprova estrutura e restrições, não veracidade.
O dummy usa saídas pré-escritas e não faz extração de linguagem natural.
O contrato cobre uma peça e uma intenção principal; as regras de pendências são
propostas identificadas no registro de decisões.

As fases 2–5 permanecem não implementadas: não há catálogo consultado, orçamento
calculado, ViaCEP, memória, RAG, agente com ferramentas ou avaliação LangSmith.
Os casos gerais das fases futuras não foram executados como se fossem desta fase.

Implementação e revisão assistidas por Codex/OpenAI, com decisões e limitações
expostas para revisão de Renan.
