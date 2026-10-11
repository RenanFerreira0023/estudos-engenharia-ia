---
name: organizar-estudos-ia
description: Organizar aulas, READMEs e exercicios no repositorio estudos-engenharia-ia. Use quando Renan pedir para criar, mover, documentar ou organizar materiais de aula, especialmente LangChain, LangGraph, agentes e estudos do MBA.
metadata:
  short-description: Organiza aulas e READMEs de IA
---

# Organizar Estudos IA

Use esta skill quando Renan pedir para organizar materiais no repositorio `estudos-engenharia-ia`, criar pastas de aula, ajustar READMEs, mover exercicios ou padronizar pequenos estudos de IA.

## Contexto do repositorio

O repositorio e usado para estudos, exercicios e projetos do MBA em Engenharia de IA, Machine Learning e Deep Learning.

A organizacao preferida e:

```text
estudos-engenharia-ia/
|-- README.md
|-- Agentes Cognitivos com LangChain/
|   |-- README.md
|   `-- aula DD-MM/
|       |-- README.md
|       |-- exercicio.py
|       `-- .env
`-- Arquiteturas Multiagentes com LangGraph/
    `-- README.md
```

## Padrao de trabalho

Quando criar ou organizar uma aula:

- Coloque cada aula em uma pasta propria, como `aula 06-10`.
- Mantenha o README da aula focado somente naquele exercicio.
- Use o README da disciplina como indice das aulas.
- Use o README raiz como indice geral do repositorio.
- Proteja segredos: `.env` pode existir localmente, mas nunca exponha chaves no chat ou em README.
- Prefira explicacoes curtas, didaticas e ligadas aos conceitos estudados.

## README da aula

O README de uma aula deve ser enxuto e conter, quando fizer sentido:

- titulo da aula ou exercicio;
- objetivo do exercicio;
- conceitos praticados;
- pequeno resumo do contexto;
- comandos essenciais para executar;
- observacao sobre `.env` quando houver API key.

Evite transformar o README da aula em apostila longa. O objetivo e servir como nota de estudo e referencia rapida.

Quando o exercicio tiver conceitos novos, registre no README uma secao curta de conceitos praticados. Explique somente o que ajuda Renan a revisar a aula: o papel do conceito no exercicio, um exemplo pequeno do proprio codigo e a ligacao com o fluxo geral. Nao crie teoria extensa nem acrescente assuntos que nao apareceram na aula.

## Codigo de exercicios

Para exercicios em Python:

- mantenha tudo simples e em poucos arquivos;
- crie sempre uma versao interativa com `input()` para exercicios executaveis no terminal, a menos que Renan peça explicitamente um script nao interativo;
- comente somente os conceitos estudados, evitando comentarios operacionais obvios;
- use comentarios de estudo para explicar o papel dos conceitos no fluxo do codigo, como contexto, prompt, `system`, `human`, variaveis do template, modelo, LCEL, chain, `input()`, `invoke` e `.content`;
- prefira comentarios curtos antes do bloco relevante, em linguagem de aluno, explicando por que aquele bloco existe no exercicio;
- evite comentar linhas obvias, como atribuicoes simples, imports ou prints comuns, a menos que a linha esteja demonstrando um conceito da aula;
- inclua uma funcao curta de estudo, como `exibir_conceitos_estudados()`, quando o exercicio for didatico. Ela deve usar `print()` para mostrar no terminal o fluxo mental do exercicio antes da execucao principal;
- use mensagens de terminal marcadas como estudo, por exemplo `[estudo]`, para mostrar o passo que esta acontecendo sem poluir a resposta final do assistente;
- para exercicios de LangChain, os `print()` de estudo devem citar os conceitos realmente usados, como `input()`, `BaseModel`, `Field`, `PROMPT`, `MODELO`, `LCEL`, `invoke`, `batch`, `.content` ou objeto estruturado;
- use nomes claros;
- leia chaves de API por variavel de ambiente ou `.env`;
- nao coloque chaves diretamente no codigo;
- valide sintaxe com `python -m py_compile` quando alterar scripts Python.

## Comentarios de estudo

O padrao de comentarios deve ajudar Renan a abrir o arquivo depois e lembrar o raciocinio da aula. Use este tipo de comentario quando estiver criando ou ajustando exercicios didaticos:

- nomeie o conceito em caixa alta quando isso facilitar a leitura, como `PROMPT TEMPLATE`, `LCEL`, `INVOKE` ou `CONTENT`;
- explique o conceito com uma ou duas frases, sempre ligado ao codigo logo abaixo;
- mostre o fluxo mental do exercicio: entrada, prompt, modelo, chain, execucao e resposta;
- mantenha os comentarios dentro do codigo, e nao como texto solto demais no chat;
- se a explicacao crescer, leve o resumo para o README da aula e deixe no codigo apenas o comentario essencial.

## Prints de estudo no terminal

Para os proximos exercicios didaticos em Python, prefira este padrao quando houver execucao no terminal:

```python
def exibir_conceitos_estudados():
    """Mostra no terminal o fluxo do exercicio em linguagem de estudo."""
    print("Como este exercicio funciona:")
    print("1. O PROMPT organiza a entrada enviada ao modelo.")
    print("2. O MODELO gera a resposta seguindo as regras do prompt.")
    print("3. A CHAIN liga prompt e modelo com LCEL.")
    print()
```

No `main()`, chame essa funcao antes da execucao principal e use uma linha
`[estudo]` para marcar o momento em que a chain sera executada:

```python
exibir_conceitos_estudados()
print("[estudo] Agora a chain vai processar a entrada.")
```

Adapte os itens aos conceitos do exercicio. Explique sempre `input()` quando o
script rodar no terminal. Se o exercicio usar `batch`, explique `batch`; se usar
`with_structured_output`, explique saida estruturada; se usar resposta de chat,
explique `invoke()` e `.content`.

## Estilo das respostas

Renan costuma estar estudando enquanto organiza o material. Seja calmo, direto e explique o suficiente para ele entender o que foi feito sem virar uma aula enorme.
