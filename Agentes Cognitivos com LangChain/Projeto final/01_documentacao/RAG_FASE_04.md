# Fase 4 — políticas com fontes e consulta estruturada do catálogo

## Executar

A partir da pasta `Projeto final`, com o ambiente/configuração do README:

```powershell
python -B 02_codigo/src/auto_super_parts/atendimento_rag.py --cliente cliente_demo
```

O índice de quatro trechos, preparado com embeddings reais, acompanha este incremento. O atendimento o carrega; não vetoriza os documentos novamente a cada pergunta. Se a fonte, o modelo ou a integridade do artefato não corresponder, o programa pede preparação explícita:

```powershell
python -B 02_codigo/preparar_politicas.py --real
```

Esse comando consome embeddings OpenAI. A chave continua somente no ambiente ou `.env` local do projeto. O atendimento usa `gpt-4o-mini` e `text-embedding-3-small`. `faiss-cpu==1.15.1` e `numpy==2.5.4` já estavam instalados no ambiente usado; foram acrescentados aos requirements por serem dependências diretas. Não houve atualização geral da stack.

Os comandos de memória continuam disponíveis: `/veiculos`, `/veiculo V003`, `/perfil`, `/guardar RESUMO`, `/nova`, `/cliente outro_cliente`, `/esquecer`, `/sair`. A identidade permanece de demonstração, sem autenticação. A CLI antiga da fase 3 continua disponível com as funcionalidades anteriores.

## O que consultar

- `Posso pagar ao entregador?`
- `Posso pagar com cartão em três vezes e tenho frete grátis em Curitiba?`
- `Se eu fizer orçamento já fica reservado? E posso pagar no cartão?`
- `Qual o prazo de garantia vocês oferecem?`
- `Liste as velas do catálogo com estoque disponível até R$ 20,00, da mais barata para a mais cara.`
- `Qual o horário de funcionamento da loja?` — informação não cadastrada.
- Depois de `/veiculo V003`: `Qual é meu veículo salvo e posso pagar com dinheiro na retirada?`

Pagamento, entrega e orçamento usam somente as políticas existentes. Troca/garantia, prazo local, início da contagem e horário continuam sem regras novas; ausência de cadastro não significa negar direitos. ViaCEP e os cálculos determinísticos continuam sendo usados para endereço e cotação de frete; a busca documental não cria distâncias.

## Fluxos e conceitos

### Preparação e carregamento

[rag_politicas.py](../02_codigo/src/auto_super_parts/rag_politicas.py) separa a política em quatro parágrafos completos. Cada trecho tem ID, seção, fonte e estado. `preparar_indice` gera embeddings, normaliza os vetores e grava `IndexFlatIP` do FAISS; produto interno de vetores normalizados corresponde ao cosseno.

Os arquivos ficam em [indices/politicas](../02_codigo/indices/politicas/): binário FAISS e manifesto JSON com modelo, dimensões, metadados e hashes. Não há pickle. O carregamento verifica correspondência da fonte/modelo e integridade; mudança da fonte exige nova preparação. Carregar artefatos próprios do projeto não equivale a confiar em índices arbitrários externos.

### Recuperação, transformação e geração

`consultar_politicas` é uma ferramenta do mesmo agente que mantém memória e consulta catálogo. A pergunta passa por um reescritor com contrato `PlanoBusca`: até três consultas por assunto, sem respostas ou novas regras. O sistema consulta a pergunta original e as reescritas, recupera um trecho por consulta e elimina repetições por ID. Assunto sem cobertura pode resultar em consultas vazias e ausência de evidência, sem fabricar documento.

Uma pergunta composta perdeu trechos com o baseline top-1. A decomposição foi testada nas mesmas perguntas com embeddings reais, sem mudar as políticas ou fornecer o gabarito ao reescritor. O depois usa mais consultas/contextos, o que pode explicar parte do ganho; não é um experimento com orçamento idêntico nem prova de superioridade geral.

O agente gera a resposta a partir dos retornos. O middleware exige consulta no turno atual para perguntas explicitamente reconhecidas sobre política, inclusive se a regra já aparecer no histórico. A detecção é delimitada por expressões; não é um classificador universal de intenção. `tool_choice` usa o campo próprio de `ModelRequest`, preservando o binding estrito existente.

O rodapé de fontes é montado com as seções/documentos efetivamente retornados, antes de salvar a resposta no histórico. Isso comprova proveniência consultada, não que toda frase da LLM esteja sustentada. O verificador semântico geral permanece no próximo incremento.

### Text-to-query restrito

[planos_consulta.py](../02_codigo/src/auto_super_parts/planos_consulta.py) converte a pergunta em `PlanoCatalogo` validado por Pydantic. Filtros: veículo cadastrado confirmado, categoria, estoque, preço máximo em centavos, ordenação e limite de até 20 linhas. O compilador Python usa tabelas/operadores fixos e parâmetros; o SQLite permanece somente leitura.

Fluxo verificável: pergunta → plano da LLM → SELECT compilado → parâmetros → produtos. A ferramenta aceita a pergunta em linguagem natural e retorna todo esse rastro. Um plano válido estruturalmente ainda pode interpretar mal o pedido; por isso a validação real confere também os filtros e os resultados esperados.

É diferente de somente expor uma função com filtros preenchidos pelo programador; também é diferente de pedir SQL livre à LLM. A opção restrita foi escolhida para limitar operações e facilitar a defesa. Não afirmar equivalência literal a uma exigência de SQL livre gerado pela LLM sem confirmar a rubrica.

Uma lista global por preço/estoque não exige veículo nem comprova aplicação no carro. Se a pergunta pedir aplicação e faltar configuração, o planejador deve devolver pendência. O exemplo de velas até vinte reais no prompt ensina a conversão de unidade/filtros; não fornece produtos ou preços do banco como resposta pronta.

## Arquivos principais

- [Atendimento integrado](../02_codigo/src/auto_super_parts/atendimento_rag.py): duas ferramentas novas, política por turno e fontes na resposta.
- [Contratos/planejadores](../02_codigo/src/auto_super_parts/planos_consulta.py): LCEL, saída estruturada e compilação segura.
- [Preparação explícita](../02_codigo/preparar_politicas.py): geração do artefato fora do atendimento.
- [Demonstração compartilhada](../02_codigo/src/auto_super_parts/demonstracao_rag.py) e [notebook fase 4](../03_notebooks/fase_04_consultas_rag.ipynb).
- [Testes locais](../02_codigo/tests/test_rag_query.py) e [validação real](../02_codigo/validar_rag.py).
- [Resultados e falhas preservadas](../04_avaliacao_e_evidencias/resultados/RAG_08_11.md).

## Conferir

```powershell
python -B 02_codigo/executar_testes.py
python -B 02_codigo/verificar_fase02.py
python -B 02_codigo/executar_notebook.py --fase 4 --modo simulado
python -B 02_codigo/validar_rag.py --real
```

As fixtures usam vetores/planos/respostas identificados e índices temporários, separados do índice real. O notebook padrão é executado sem API; não comprova compreensão da LLM. A validação real consome chat/embeddings e preserva versões com divergências. LangSmith não é usado nem simulado neste incremento.

## Referências de implementação

[FAISS: índices e cosseno](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes), [FAISS: introdução](https://github.com/facebookresearch/faiss/wiki/Getting-started), [LangChain: transformação de consultas](https://www.langchain.com/blog/query-transformations). O comportamento de binding do middleware também foi conferido no código instalado de `langchain.agents.factory` e `ModelRequest`.

Próximo incremento: verificação factual/lógica dentro do agente; depois Streamlit, avaliação LangSmith e entregas. Consulta de fonte, parser e SQL restrito não substituem essa verificação.
