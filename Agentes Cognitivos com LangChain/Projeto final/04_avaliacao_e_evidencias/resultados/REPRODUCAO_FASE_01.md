# Revisão de reprodução da fase 1 — 02/11/2026

Somente configuração, ambiente, kernel e entrega da fase 1. Não houve nova
chamada à OpenAI nem implementação de outras fases nesta revisão.

## Alterações

- A aplicação prioriza `OPENAI_API_KEY` do ambiente. Sem a variável, lê somente
  `.env` na pasta do próprio projeto. Não procura configuração em pastas externas.
- A raiz é localizada pelo marcador de projeto, sem depender de `parents[5]`.
- O README documenta criação da `.venv`, instalação, configuração e registro do
  kernel `auto-super-parts-fase01` dentro desse ambiente.
- O executor permite escolher `--kernel` e dá preferência aos registros da
  `.venv` que está executando o comando.
- O `.gitignore` local cobre configuração privada, `.venv`, caches e checkpoints.
  `gerar_pacote.py` gera o ZIP excluindo esses arquivos.

## Verificações realmente executadas

[Preparação e instalação desde zero](./fase01_reproducao_preparacao_20261102T192943505182Z.json):
cópia em pasta temporária renomeada como `pacote_independente`, sem copiar `.env`,
`.venv` ou caches. Uma nova `.venv` foi criada com `include-system-site-packages=false`
e as dependências foram instaladas a partir de `02_codigo/requirements.txt`.

[Resultados das dez verificações](./fase01_reproducao_verificacoes_20261102T193213355049Z.json):

| Verificação | Resultado observado |
| --- | --- |
| pip check na nova .venv | Sem dependências incompatíveis. |
| Origem do Python e das bibliotecas | Python, langchain-core e Pydantic localizados na .venv da cópia, não na original. |
| Registro do kernel | Criado dentro da .venv da cópia. |
| Executável do kernel | argv aponta para o Python da nova .venv. |
| Testes locais na cópia | 23 executados, sem falhas ou erros. |
| CLI a partir de outra pasta | --help funcionou sem PYTHONPATH. |
| Sem configuração local ou variável | Erro claro, código 2; o .env fictício colocado na pasta pai não foi lido. |
| Arquivo .env local | Inicialização e encerramento da CLI funcionaram, sem chamada HTTP. |
| Variável sobre arquivo | A instância do cliente usou a variável, apesar de existir outro valor no arquivo local. Sem chamada HTTP. |
| Notebook com kernel registrado | Sete células de código executadas; nove casos simulados aprovados; interpretador da cópia confirmado na saída. |

Os valores usados para testar a configuração eram fixtures fictícias, não
credenciais reais. A execução simulada verifica infraestrutura e validação;
não constitui uma nova avaliação da extração pelo modelo real.

O [notebook executado na cópia](./fase01_notebook_reproducao_simulada.ipynb) foi
preservado como evidência. O notebook principal também apresenta essa execução
simulada identificada, com uma nota de portabilidade; nenhuma saída foi inventada
para substituir uma nova chamada real.

## Tentativa interrompida

A [primeira preparação](./fase01_reproducao_preparacao_20261102.json) criou uma
cópia e uma .venv dentro do sandbox. O processo de instalação fora do sandbox
não encontrou esse executável temporário, portanto essa tentativa não comprovou
reprodução completa. A preparação e instalação seguintes foram executadas no
mesmo contexto e suas saídas estão no registro vinculado acima.

## Preservação e limites

O [inventário anterior à revisão](./fase01_portabilidade_baseline_20261102T192139249104Z.json)
registra os hashes SHA-256 das 19 evidências existentes. Eles foram conferidos
sem alteração de bytes. O notebook principal anterior foi preservado em um
[snapshot integral](./fase01_notebook_antes_portabilidade_20261102T192139249104Z.ipynb),
com o mesmo hash original. Os resultados reais anteriores de 9/9 continuam
históricos; não são apresentados como execução real nesta nova .venv.

O ZIP anterior continha caches. O pacote é regenerado pelo comando abaixo,
com conferência de integridade e exclusão de `.env`, `.venv` e bytecode:

```powershell
.\.venv\Scripts\python.exe -B .\02_codigo\gerar_pacote.py
```

Ele fica ao lado da pasta do projeto, substituindo o ZIP de entrega anterior.
As novas evidências de limpeza e integridade são registradas separadamente,
sem modificar os resultados históricos.

Conferências executadas:

- [Limpeza dos três diretórios de cache; zero restantes](./fase01_limpeza_caches_20261102.json).
- [Hashes preservados, ZIP íntegro e regras locais do Git](./fase01_verificacao_entrega_20261102.json).

O pacote final foi conferido sem caches, `.venv` ou `.env` real. As evidências
anteriores também permanecem no ZIP com os mesmos hashes.
