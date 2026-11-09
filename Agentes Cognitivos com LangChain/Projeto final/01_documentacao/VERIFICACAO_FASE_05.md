# Fase 5 — verificar a resposta antes de exibir e gravar

## Problema e decisão

O agente pode consultar corretamente e ainda associar preço à peça errada, extrapolar compatibilidade ou inventar uma política. A verificação usa somente a pergunta, o contexto declarado e os retornos efetivamente observados no turno. Consultar uma fonte não prova que a conclusão está correta.

A implementação combina checagens determinísticas de valores com juiz LLM de três classes. Essa é uma adaptação da verificação por inferência descrita no plano e da abordagem de auditoria estudada: não é um classificador NLI especializado ou prova formal de implicação. Checagens de centavos não são NLI. A adequação dessa adaptação à rubrica precisa ser explicada na defesa, sem prometer equivalência automática.

Alternativas: somente regras seriam insuficientes para condições e associação entre peça/preço; instalar classificador NLI exigiria selecionar modelo, idioma e avaliar domínio. O juiz usa o modelo já configurado, preserva evidências e evita nova infraestrutura, mas custa chamadas adicionais e pode errar.

## Fluxo

1. O mesmo agente executa ferramentas, RAG e memória.
2. Os retornos atuais recebem IDs E; mensagens do cliente recebem M; contexto declarado recebe C. Perfil, pergunta e fala antiga do assistente não comprovam preço, política ou especificação.
3. Python confere valores monetários observados e total/subtotal/frete rotulados contra o orçamento. A associação semântica de cada valor à peça ainda depende do juiz; números existentes podem estar trocados entre produtos.
4. O juiz avalia trechos da candidata como sustentada, contradita ou sem_suporte. Cobertura, resposta efetiva e coerência são campos separados. Python calcula a aprovação e rejeita parecer incompleto, referência inexistente ou trecho que não está na resposta.
5. Se reprovar, há no máximo uma reescrita usando as mesmas evidências, seguida de nova avaliação. Nenhuma nova reserva, pagamento ou alteração de dados é executada pelo verificador.
6. Se continuar inválida, se o juiz falhar ou se o reparo falhar, sai uma limitação segura. A memória recebe somente essa resposta liberada. Candidata, pareceres, regras e reparo ficam no JSON de evidência.

Uma garantia não cadastrada torna “30 dias de garantia” sem suporte, não contradita. Uma regra explícita diferente pode produzir contradição. “Não consegui confirmar o prazo nesta base; consulte o atendimento” pode ser resposta correta. Isso difere de “Posso consultar” quando a política já está disponível.

A validação de trechos ignora somente espaços, diacríticos e formatação Markdown básica; palavras, números e ordem não podem mudar. A proveniência do rodapé continua controlada pelo programa.

## Executar

A partir da pasta Projeto final, com a .venv e o mesmo .env local:

```powershell
python -B 02_codigo/src/auto_super_parts/atendimento_verificado.py
python -B 02_codigo/validar_verificacao.py
python -B 02_codigo/validar_verificacao.py --real
python -B 02_codigo/executar_notebook.py --fase 5 --modo simulado
```

A nova CLI conserva os comandos de memória e mostra Verificacao: aprovada, corrigida ou limitacao. A CLI antiga atendimento_rag.py continua sendo a fase anterior, sem este juiz geral. Não há nova dependência nem uma segunda chave. O atendente e o planejamento permanecem em gpt-4o-mini. O juiz/reparador usa gpt-5.4-mini com esforço low e teto de saída 4096, escolhido pela comparação real; veja o relatório antes/depois. A mesma chave local é usada, sem fallback silencioso para um juiz que falhou nos critérios.

Sem --real, a avaliação mostra 14 candidatas escritas para teste e as regras locais. Notas do juiz e comparação com gabarito ficam ausentes, não simuladas como métricas reais. No notebook, o modo simulado tem o mesmo comportamento.

Com --real, o script avalia as mesmas 14 fixtures com a API, incluindo total errado, estoque insuficiente, garantia desconhecida, cartão proibido, preços trocados, homologação indevida, saudação e instrução maliciosa na candidata. Depois executa uma falha controlada (candidata manual injetada; ferramentas, juiz e reparador efetivos) e dois atendimentos com modelo real. Cada sessão e banco são temporários; não se usa a memória pessoal de Renan.

## Teste manual

No atendimento_verificado.py, informe: “Calcule 7 unidades do P009 para retirada.” O retorno esperado é R$ 118,30, sem reserva. Pergunte também: “Qual o prazo de garantia das peças? Posso trocar depois de 30 dias?” A resposta deve explicar a informação pendente sem inventar um prazo. Confira a verificação e as chamadas no JSON, não apenas uma resposta plausível.

## Limites

O juiz é probabilístico e pode aceitar uma afirmação inválida ou bloquear uma resposta correta. O gabarito foi preparado no projeto; revisão de Renan continua desejável. Não se mede qualidade geral com 14 exemplos. As regras financeiras são delimitadas e não fazem compreensão universal de texto, matemática ou associação entre todos os produtos. A correção não aumenta cobertura das fontes nem resolve dados técnicos pendentes.

Uma consulta normal acrescenta um julgamento. Uma candidata reprovada pode acrescentar reparo e novo julgamento: até três chamadas adicionais ao modelo. Isso aumenta custo e latência. Não existe loop ilimitado. Erro do juiz reduz disponibilidade ao produzir limitação; não libera uma resposta sem verificação.

Ver [resultados, falhas do juiz e antes/depois](../04_avaliacao_e_evidencias/resultados/VERIFICACAO_08_11.md), [registro central](./registro_decisoes.csv) e [notebook](../03_notebooks/fase_05_verificacao.ipynb). Streamlit, avaliação LangSmith, reprodução final em ambiente novo, PDF e vídeo continuam pendentes.

## Escolha do modelo do juiz

As três rodadas com gpt-4o-mini preservam confusões entre informação desconhecida e contradição, além de bloqueios indevidos de lacunas explicadas. Revisões de critérios, apresentação da candidata e few-shot não eliminaram essas falhas. Foi comparado gpt-5.4-mini na mesma configuração de critérios, mantendo o modelo do atendente separado. O resultado é evidência nesta amostra, não superioridade universal.

A [documentação oficial OpenAI](https://developers.openai.com/api/docs/models/gpt-5.4-mini) confirma Chat Completions, saída estruturada e esforço low. A escolha acrescenta custo específico do juiz; o projeto não mediu custo faturado por execução. Consulte a tabela oficial para preços atuais. Os perfis de orçamento, dados comerciais e regras continuam em Python.

## Identificacao antes da geracao

Com os dois recortes de Fusca, o controlador pode responder uma pergunta de identificacao antes de chamar o modelo. Nesse caso status identificacao_pendente, geracao_executada=false e juiz_executado=false deixam claro que nao houve julgamento LLM. A pergunta controlada e registrada no historico; nao deve ser apresentada como resposta comercial ou como nota positiva do juiz.
