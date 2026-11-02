# Revisão observada das fases 1 e 2 — 02/11/2026

A fase 2 está parcialmente implementada e pode ser testada pelo terminal. Não é uma entrega concluída: o notebook está vazio e houve falha de argumentos no teste real de entrega. Nenhuma fase posterior foi implementada nesta revisão.

## Código presente

- `02_codigo/src/auto_super_parts/catalogo_fase02.py`: importa 4 veículos, 24 produtos e 24 aplicações em SQLite em memória; consulta parametrizada e banco somente leitura após a carga. Preserva IDs, centavos e limites dos dados simulados.
- `02_codigo/src/auto_super_parts/orcamento_fase02.py`: valida itens com BaseModel, consulta preços no banco, agrega quantidades e calcula subtotal/frete sem cálculo pela LLM. Rejeita quantidade não inteira positiva e preço extra; não reserva estoque. Cidade sem distância mantém frete e total desconhecidos.
- `02_codigo/src/auto_super_parts/viacep.py`: consulta HTTPS real com CEP validado; trata entrada inválida, CEP inexistente, timeout, indisponibilidade e resposta inválida. Transporte de teste é explicitamente identificado; não substitui a API real silenciosamente.
- `02_codigo/src/auto_super_parts/agente_fase02.py`: ChatOpenAI e create_agent com quatro ferramentas: listar_veiculos, consultar_catalogo, consultar_cep e calcular_orcamento. CLI interativa, argumentos/retornos e evidências JSON por execução. Cada mensagem é independente; ainda não há memória entre turnos.

## Testes realmente executados nesta revisão

| Verificação | Observado | Evidência |
| --- | --- | --- |
| Fase 1: testes locais | 23 executados, zero falhas/erros | `fase01_unittest_20261102T195527160634Z.json` |
| Fase 2: testes locais | 15 executados, zero falhas/erros | `fase02_verificacoes_locais_20261102T195646603397Z.json` |
| Primeira tentativa de agente na rede restrita | OpenAIConnectionError; nenhuma operação de ferramenta | `fase02_20261102T195545525455Z.json` |
| Agente real: duas unidades de P003, retirada | Consulta retornou 1850 centavos e estoque 16; ferramenta calculou 3700 centavos, frete zero | `fase02_20261102T195600917176Z.json` |
| Agente real: P023 sem estoque | Consulta retornou produto existente com estoque zero; resposta informou indisponibilidade | `fase02_20261102T195710884100Z.json` |
| Agente real + ViaCEP 01001000 + orçamento de entrega | HTTP 200, São Paulo/SP. Modelo enviou `minItems` extra duas vezes no cálculo; validação rejeitou. Cálculo não concluído | `fase02_20261102T195701244602Z.json` |
| Sintaxe e preservação | 11 arquivos compilados com py_compile; 46 arquivos protegidos sem alteração; CLI interativa abriu e encerrou com /sair, código zero | `fase02_auditoria_20261102T195745465290Z.json` |

Os 15 testes locais estão em `02_codigo/verificar_fase02.py`: importação do catálogo, aplicações, estoque zero versus inexistência, SQL parametrizado e bloqueio de escrita, subtotal independente, quantidades inválidas, preço externo, duplicatas versus saldo, cidade desconhecida, Curitiba/UF e prazo pendente, arredondamento/faixas do frete, validação de CEP, dummy explícito, falhas de transporte e ciclo de ferramenta/validação de argumentos. O modelo roteirizado verifica a execução; não é evidência de compreensão de linguagem natural.

A nova execução real da fase 1 usou:

```powershell
& ".\.venv\Scripts\python.exe" -B ".\Agentes Cognitivos com LangChain\Projeto final\02_codigo\src\auto_super_parts\chain_inicial.py" --mensagem "Tenho um Gol 2010 1.0 e quero duas velas"
```

Saída observada no terminal, transcrita sem alteração dos valores:

```json
{
  "status": "ok",
  "dados": {
    "intencao": "consulta_peca",
    "veiculo": {
      "modelo": "Gol",
      "ano_modelo": 2010,
      "motor": "1.0",
      "combustivel": null
    },
    "peca": "vela",
    "quantidade": 2,
    "cep": null,
    "campos_faltantes": ["veiculo.combustivel"]
  },
  "erros": []
}
```

## Reprodução manual

Na raiz do repositório, no PowerShell:

```powershell
& ".\.venv\Scripts\python.exe" -B ".\Agentes Cognitivos com LangChain\Projeto final\02_codigo\src\auto_super_parts\agente_fase02.py"
```

É necessário OPENAI_API_KEY no ambiente ou `.env` local em `Agentes Cognitivos com LangChain/Projeto final`; o arquivo da raiz do repositório não é buscado automaticamente. Nenhuma credencial foi exibida nesta revisão.

Perguntas independentes sugeridas:

1. `Quero 2 unidades do P003 para retirada. Consulte preço e estoque e calcule o orçamento.` Esperado: consulta e cálculo, total R$ 37,00.
2. `Quero 1 unidade do P023 para retirada. Tem estoque?` Esperado: produto existe, saldo zero.
3. `Quero 2 unidades do ABC-99 para retirada.` Esperado: produto não encontrado, sem preço inventado. Este cenário não foi executado com modelo real nesta revisão.
4. `Quero zero unidades do P003 para retirada.` Esperado: pedir quantidade positiva; se houver chamada inválida, validação rejeita. Comportamento em linguagem natural ainda não executado nesta revisão.
5. `Tenho um Gol 2010 1.0 e quero duas velas.` Esperado: esclarecer configuração e modalidade antes de concluir orçamento; não inferir combustível/versão. Comportamento do agente ainda não executado nesta revisão.
6. `Consulte o CEP 01001000 no ViaCEP e calcule 2 unidades do P003 para entrega nesse endereço.` Esperado: endereço pela API; São Paulo/SP sem distância cadastrada deve manter frete/total pendentes. Há falha observada nos argumentos do cálculo neste caminho.

Não use “e esse produto?” como continuação: memória pertence à fase 3. `/sair` encerra.

Para repetir os testes locais:

```powershell
& ".\.venv\Scripts\python.exe" -B ".\Agentes Cognitivos com LangChain\Projeto final\02_codigo\executar_testes.py"
& ".\.venv\Scripts\python.exe" -B ".\Agentes Cognitivos com LangChain\Projeto final\02_codigo\verificar_fase02.py"
```

## Pendências

1. Corrigir a interação modelo/schema que levou ao argumento extra `minItems`, reforçar consulta antes do cálculo e repetir o caminho real de entrega. A resposta final mencionou ausência de distância, mas a ferramenta de cálculo não chegou a confirmar isso nesse turno; não classificar como aprovação do fluxo completo.
2. Criar e executar `03_notebooks/fase_02_agente_ferramentas.ipynb`, atualmente com zero bytes.
3. Incluir as dependências novas (`langchain` e `langgraph`) no requirements e conferir instalação limpa/portabilidade da fase 2. No ambiente atual estão instaladas as versões 1.4.7 e 1.2.17, respectivamente; isso não comprova reprodução em ambiente novo.
4. Ampliar testes reais do agente para ambiguidade do veículo, produto inexistente, quantidade inválida e falhas de CEP. Os testes offline não substituem essa avaliação.
5. Atualizar os índices/READMEs e o pacote de entrega ao concluir a fase 2. O código da fase 1 e suas evidências anteriores foram preservados.

Memória, busca documental/FAISS, text-to-SQL e avaliação integrada continuam reservados às fases posteriores. As regras comerciais e técnicas originalmente pendentes continuam sem valores inventados.
