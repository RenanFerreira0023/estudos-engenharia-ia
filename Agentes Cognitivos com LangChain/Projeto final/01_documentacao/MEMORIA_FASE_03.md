# Fase 3 — memória com isolamento por cliente

## Implementação e execução

O [serviço com memória](../02_codigo/src/auto_super_parts/atendimento_memoria.py) usa o mesmo agente/ferramentas da fase 2, fornecendo o contexto explicitamente. O [store SQLite](../02_codigo/src/auto_super_parts/memoria.py) conserva sessões, pares pergunta/resposta, perfil de veículo confirmado e resumos autorizados. Dados locais ficam em `02_codigo/estado_local`, ignorados pelo Git e pelo gerador de ZIP.

Na pasta `Projeto final`, com o ambiente configurado conforme o README:

```powershell
python -B 02_codigo/src/auto_super_parts/atendimento_memoria.py --cliente cliente_demo
```

Sem ativar o ambiente, substitua `python` pelo caminho de `.venv/Scripts/python.exe`. O modelo é `gpt-4o-mini`; os resumos usam `text-embedding-3-small`. Não exige nova dependência ou chave além da OpenAI configurada no projeto. A interface neste incremento é terminal; Streamlit continua pendente.

| Comando | Efeito |
|---|---|
| `/veiculos` | Lista configurações cadastradas e seus IDs |
| `/veiculo V003` | Confirma ou corrige o veículo atual no perfil e registra a confirmação na sessão |
| `/perfil` | Exibe o perfil confirmado do cliente selecionado |
| `/guardar Uso urbano com trajetos curtos` | Guarda um resumo explicitamente autorizado e seu embedding |
| `/nova` | Abre sessão sem histórico anterior; preserva perfil/resumos |
| `/cliente outro_cliente` | Troca a identidade de demonstração e abre nova sessão isolada |
| `/esquecer` | Apaga perfil, resumos e históricos daquele cliente para não recuperar dados apagados |
| `/sair` | Fecha conexões; dados confirmados permanecem no arquivo |

`--sessao ID` retoma uma sessão existente do mesmo cliente. `--sem-vetores` desativa explicitamente apenas os resumos vetoriais. `--banco CAMINHO` escolhe outro arquivo; esse caminho precisa ser excluído manualmente do Git/ZIP se estiver fora de `estado_local`.

Identidades são de demonstração, **sem autenticação**. A verificação de propriedade impede misturar sessões por engano, mas não prova a identidade de quem digita um `cliente_id`. Não disponibilizar esse mecanismo como login real.

## Conceitos e arquitetura

- **Histórico/buffer:** últimos seis turnos completos são enviados a `invoke`, antes de registrar o novo par. Não há duplicação da pergunta atual nem gravação de uma resposta que falhou. O histórico completo permanece no banco até exclusão; a janela enviada ao modelo é limitada por turnos, não por contagem exata de tokens.
- **Namespace/chave:** perfil por cliente; sessão vinculada ao cliente; resumos filtrados por cliente e modelo de embedding antes da busca. Não há coleção global compartilhada de lembranças.
- **UPSERT e confirmação:** somente `/veiculo` confirma/substitui o perfil. O modelo não escreve um veículo inferido automaticamente. Correções na conversa valem para aquele diálogo; persistência exige confirmação explícita.
- **Recuperação vetorial:** resumos autorizados são vetorizados uma vez e persistidos. Cosseno em Python sobre os vetores normalizados armazenados no SQLite recupera até três resumos com similaridade mínima de 0,2, apenas no mesmo espaço/modelo. É uma escolha para coleção acadêmica pequena, não um banco vetorial escalável. O limiar é inicial, não calibrado em dataset amplo.
- **CoALA:** perfil é memória semântica estruturada; resumos autorizados podem registrar episódios/contexto de uso, sem extração automática da experiência do agente. Código/prompt representam procedimentos fixos, sem aprendizagem procedural. A janela é memória de trabalho.
- **Dados e instruções:** o contexto é uma mensagem de dados do cliente, nunca uma nova instrução de sistema. Memória de uso não valida óleo, preço ou aplicação. O agente continua consultando suas ferramentas para esses fatos.
- **Falhas:** erro de recuperação é registrado, sem resultados fictícios; perfil e histórico continuam utilizáveis. Falha ao gerar embedding impede salvar o resumo. Vetores nulos, inválidos ou de dimensões incompatíveis são rejeitados.

Não usamos `MemorySaver`, LangMem ou Mem0 na implementação. Não declarar equivalência literal a classes legadas da rubrica sem confirmação do professor.

## Comparação de ferramentas de memória

| Alternativa | Arquitetura/caso de uso | Decisão neste projeto |
|---|---|---|
| [LangMem](https://langchain-ai.github.io/langmem/reference/) | Utilitários para extrair/atualizar/recuperar memória integráveis a stores do ecossistema LangGraph | Interessante para extração automática; não adotado, pois a confirmação explícita e a coleção pequena permitem acompanhar cada escrita sem outra camada |
| [Mem0](https://github.com/mem0ai/mem0/blob/main/docs/core-concepts/how-it-works.mdx) | Camada de memória com operações de adição/busca e escopos de usuário/agente/execução | Interessante para gestão de fatos em aplicações maiores; não adotado para evitar infraestrutura/processamento adicional neste recorte |
| SQLite + embeddings via LangChain | Perfil determinístico, histórico e poucos resumos com gravação autorizada | Escolhido: inspeção local, exclusão simples e isolamento testável; extração/deduplicação automática e escala ficam fora |

Referência de taxonomia: [visão oficial de memória no LangGraph](https://langchain-ai.github.io/langgraph/concepts/memory/). Referência de embeddings: [OpenAIEmbeddings no LangChain](https://reference.langchain.com/python/langchain-openai/embeddings/base/OpenAIEmbeddings). A comparação foi documental, não benchmark de desempenho dos três produtos.

## Como verificar

```powershell
python -B 02_codigo/executar_testes.py
python -B 02_codigo/verificar_fase02.py
python -B 02_codigo/validar_memoria.py
python -B 02_codigo/validar_memoria.py --real
python -B 02_codigo/executar_notebook.py --fase 3 --modo simulado
```

O script sem `--real` usa respostas/vetores roteirizados identificados e um banco temporário. O notebook importa esse mesmo módulo. No modo real há consumo de chat e embeddings; o banco temporário usa apenas clientes de demonstração e é descartado.

Situações: lembrar Fusca na sessão; confirmar Celta e um resumo de uso; fechar o banco e ler o perfil por outro processo Python; abrir nova sessão e recuperar perfil/resumo; conferir outro cliente; corrigir para S10 e excluir as memórias. As checagens automáticas são de contratos e trechos esperados, não um juiz semântico universal.

Lembrar numa sessão isoladamente não prova persistência após reiniciar: poderia ser apenas RAM. A demonstração adicional fecha o banco e lê o perfil em um processo separado antes de reabrir a fachada; os testes ainda conferem janela e isolamento. Isso comprova esse caminho de armazenamento local, sem prometer recuperação de toda conversa ou sobrevivência à exclusão do arquivo.

Memória não substitui especificações técnicas ou políticas. O índice de políticas em FAISS, text-to-query e verificador geral permanecem nos próximos incrementos. [Evidências desta fase](../04_avaliacao_e_evidencias/resultados/MEMORIA_08_11.md).
