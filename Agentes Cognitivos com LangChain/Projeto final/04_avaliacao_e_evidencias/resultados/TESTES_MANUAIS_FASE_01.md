# Testes manuais e conferência da CLI — fase 1

Registro elaborado em 02/11/2026. As origens abaixo são distintas: o usuário
relatou um erro; o assistente conferiu a versão corrigida com subprocessos e
entrada de terminal roteirizada. Não foi fornecida nesta conversa uma saída
JSON de teste manual executado pelo usuário na fase 1.

## M01 — Erro de importação relatado pelo usuário

Origem: transcrição enviada por Renan nesta conversa, antes da correção da CLI.
O horário exato da execução original não foi informado. Este é um relato
observado, não uma reexecução da versão anterior pelo assistente.

Comando transcrito:

```powershell
& c:\Users\Renan\Documents\GIT_PROJETOS\estudos-engenharia-ia\.venv\Scripts\python.exe "c:/Users/Renan/Documents/GIT_PROJETOS/estudos-engenharia-ia/Agentes Cognitivos com LangChain/Projeto final/02_codigo/src/auto_super_parts/chain_inicial.py"
```

Saída transcrita:

```text
Traceback (most recent call last):
  File "c:\Users\Renan\Documents\GIT_PROJETOS\estudos-engenharia-ia\Agentes Cognitivos com LangChain\Projeto final\02_codigo\src\auto_super_parts\chain_inicial.py", line 11, in <module>
    from .prompts import criar_templates
ImportError: attempted relative import with no known parent package
```

Diagnóstico: executar o arquivo diretamente não definia seu pacote pai,
necessário para o import relativo `.prompts`. A linha 11 acima é a posição
histórica do traceback, não a numeração do arquivo após a correção.

Correção já implementada em `chain_inicial.py`: somente quando executado
diretamente, o script acrescenta `src` ao caminho de importação e define
`__package__ = "auto_super_parts"`. Importação pelo notebook e execução com
`python -m` mantêm o contexto normal do pacote.

## M02 — Comando recomendado após a correção

No PowerShell, na raiz do repositório:

```powershell
.\.venv\Scripts\python.exe ".\Agentes Cognitivos com LangChain\Projeto final\02_codigo\src\auto_super_parts\chain_inicial.py"
```

Não exige configuração de `PYTHONPATH`. Após `Mensagem:`, digite uma solicitação.
Enter vazio ou `/sair` encerra. O botão **Executar arquivo Python** do VS Code
usa a forma direta de execução que originou o erro; a conferência foi do comando
Python equivalente, sem automatizar ou alegar um clique observado na interface.

## M03 — Verificações executadas pelo assistente

Evidência bruta: [comandos, stdin, stdout, stderr e códigos de saída](./fase01_cli_assistida_20261102T190918839535Z.json).

Os três subprocessos foram iniciados na pasta temporária, com `PYTHONPATH`
removido do ambiente, para conferir que a execução direta não depende da pasta
atual nem daquela variável. A evidência preserva o comando absoluto efetivamente
executado; ele equivale ao comando relativo acima quando usado na raiz.

| Caso | Entrada | Resultado realmente observado |
| --- | --- | --- |
| CLI01 | `chain_inicial.py --help` | Código 0; ajuda apresentou `--mensagem`; sem erro de importação. Sem chamada ao modelo. |
| CLI02 | Execução direta; Enter vazio | Código 0; conceitos e prompt `Mensagem` exibidos; encerrou. Sem chamada ao modelo. |
| CLI03 | Mensagem abaixo, seguida de `/sair` | Código 0; uma chamada real a OpenAI / gpt-4o-mini; JSON validado retornado; encerrou. |

Entrada de CLI03:

```text
Tenho um Gol 2010 1.0 e quero duas velas
/sair
```

JSON observado em CLI03, também preservado sem alteração no arquivo bruto:

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

O código não acrescentou `8V` nem combustível. Esta execução verifica uma
mensagem na CLI; não é garantia de acerto de qualquer mensagem futura.

## Regressão automatizada e limites

O teste `test_execucao_direta_fora_do_projeto_sem_pythonpath` reproduz a
inicialização por caminho de arquivo com `--help`, sem API. Faz parte dos
[16 testes locais aprovados](./fase01_unittest_20261102T184419294226Z.json).
Os [nove casos reais do notebook](./fase01_real_20261102T183637172353Z.json)
permanecem separados desta conferência de terminal.

Não foram executadas ferramentas, consultas ao catálogo, ViaCEP, memória, RAG
ou outras fases para produzir essas evidências. Os arquivos das fases 2–5
continuam placeholders de planejamento, não entregas executadas.
