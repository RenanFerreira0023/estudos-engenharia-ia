# Memória — implementação e verificação em 08/11/2026

## O que mudou

Fachada `AtendimentoComMemoria` usa o mesmo agente/ferramentas e envia janela explícita de mensagens. Store SQLite persiste por cliente/sessão, perfil confirmado/corrigível e resumos autorizados com embeddings. Janela padrão de seis pares completos; sem escrita de perfil inferida pela LLM. Busca de até três resumos por cosseno, com filtro de cliente/modelo e limiar inicial 0,2. Sem FAISS, RAG de políticas ou autenticação.

## Verificações locais

- `executar_testes.py`: 78 testes aprovados, incluindo 15 de memória.
- `verificar_fase02.py`: 18 testes aprovados. Total: 96, sem rede nos testes.
- Casos específicos: pares sem duplicação; sessão de outro cliente rejeitada; nova sessão; correção; exclusão; persistência ao fechar/reabrir o arquivo; vetores filtrados por cliente/modelo; rejeição de vetor inválido; contexto realmente enviado ao modelo roteirizado; falha de API sem resultado fictício; banco de uso fora do ZIP.
- Notebook fase 3 executado integralmente em kernel novo com fixtures. Primeira tentativa encontrou string malformada numa célula de exibição; erro preservado em notebook separado e corrigido antes da execução final.
- Fixtures conferem infraestrutura e isolamento, não compreensão da LLM nem resistência universal a injeção de instruções.

## API real: seis situações

[Execução real](./fase03_real_20261108T230041996062Z.json), com OpenAI/gpt-4o-mini e embeddings text-embedding-3-small. Usados apenas clientes fictícios e banco temporário.

| Caso | Observado |
|---|---|
| Informar Fusca na sessão | Resposta registrada e enviada no histórico do próximo turno |
| Perguntar pelo carro informado | Resposta lembrou Fusca 1982 |
| Outra sessão após confirmar Celta e resumo de uso | Recuperou perfil Celta e resumo de percursos urbanos; histórico antigo não enviado |
| Cliente B | Não recebeu veículo do cliente A; pediu informação |
| Corrigir perfil para S10 | Nova sessão respondeu S10 2014 |
| Esquecer cliente A | Resposta passou a pedir o veículo, sem recuperar Fusca/Celta/S10 |

As seis verificações locais de resposta esperada foram atendidas. O script também fechou o banco, iniciou outro processo Python para ler perfis e comprovou Celta no cliente A e ausência de perfil no B. A fachada foi reaberta sobre o mesmo arquivo antes de testar a nova sessão. A recuperação vetorial registrou resumos reais e origem do embedding, sem usar vetores fixture na execução real.

As respostas finais foram inspecionadas manualmente de forma assistida. Não foi usado juiz LLM nem LangSmith. Checagens por trechos não são métricas universais de qualidade. A primeira entrada verifica sucesso de atendimento; a lembrança é verificada no segundo turno.

## Reproduzir

Na pasta Projeto final:

```powershell
python -B 02_codigo/validar_memoria.py
python -B 02_codigo/validar_memoria.py --real
python -B 02_codigo/executar_notebook.py --fase 3 --modo simulado
python -B 02_codigo/src/auto_super_parts/atendimento_memoria.py --cliente cliente_demo
```

O modo real consome API. A CLI usa banco local ignorado pelo Git/ZIP; a demonstração descarta seu banco temporário. `.env` não foi copiado ou exposto. A identidade permanece de demonstração, sem autenticação. Não houve instalação limpa nova, notebook real de fase 3, RAG de políticas ou avaliação LangSmith. O próximo incremento segue o plano atualizado.

Na inspeção da primeira resposta real, o agente antecipou perguntas sobre óleo quando o cliente apenas informou o veículo. O prompt da fachada foi ajustado para reconhecer os dados e aguardar o pedido. A suíte local foi repetida após esse ajuste; a execução real preservada é anterior a essa última instrução, e não alegamos uma nova medição real desse comportamento.
