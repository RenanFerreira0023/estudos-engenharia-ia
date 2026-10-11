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

## Codigo de exercicios

Para exercicios em Python:

- mantenha tudo simples e em poucos arquivos;
- prefira uma versao interativa com `input()` quando isso deixar o estudo mais dinamico;
- comente somente os conceitos estudados, evitando comentarios operacionais obvios;
- use comentarios para marcar conceitos como contexto, prompt, `system`, `human`, variaveis do template, modelo, LCEL, chain, `input()`, `invoke` e `.content`;
- use nomes claros;
- leia chaves de API por variavel de ambiente ou `.env`;
- nao coloque chaves diretamente no codigo;
- valide sintaxe com `python -m py_compile` quando alterar scripts Python.

## Estilo das respostas

Renan costuma estar estudando enquanto organiza o material. Seja calmo, direto e explique o suficiente para ele entender o que foi feito sem virar uma aula enorme.
