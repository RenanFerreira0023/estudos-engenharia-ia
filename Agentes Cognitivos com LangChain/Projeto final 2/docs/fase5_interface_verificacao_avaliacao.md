# Interface, verificação e avaliação

## O que está implementado

- `app.py` abre uma interface Streamlit com conversa, importação, propostas, agenda e financeiro. Ela usa os serviços Python e o mesmo SQLite do terminal. A escolha de `ana`, `bruno` ou `carla` é uma identidade **de demonstração**, sem senha. O histórico exibido e enviado ao agente é filtrado por usuário e sessão.
- A aba Revisão permite analisar um corpus privado importado com `analisar_snapshot`, somente após autorização explícita para enviar as mensagens à OpenAI. A análise em lotes salva o resultado em `dados/privados/analises` e cria propostas pendentes; cobertura dos lotes não comprova acerto semântico. A importação inicial permanece local.
- `src/secretaria/verificador.py` aplica regras determinísticas para contagem e valores financeiros. Quando há retorno de ferramenta, um juiz LLM compara a resposta às evidências; se reprovar, há uma tentativa de reescrita sem repetir ferramentas. Se ainda falhar, a resposta exibida e salva informa a limitação. O parecer não comprova por si só verdade de uma fonte incorreta.
- O financeiro registra uma revisão de orçamento em `substituicoes_orcamento` e cancelamentos/estornos em `reversoes_pagamento`. Registros anteriores permanecem auditáveis. Não se substitui orçamento com pagamentos vinculados automaticamente: o caso requer reconciliação humana.
- `avaliar.py --modo fixture` usa seis casos locais identificados, compara listas de ferramentas e mostra notas **esperadas de fixtures**. A oferta “Posso consultar...” recebe zero. Isso não é avaliação do agente nem execução do LangSmith.
- `avaliar.py --modo api` executa quatro casos isolados com o agente em SQLite temporário e usa juiz semântico; o caso de fonte prepara um índice de 40 mensagens por embeddings. Dois casos adicionais são fixtures locais de critério e não são atribuídos ao agente. `--langsmith` cria dataset e experimento **somente com dados fictícios**; requer credenciais válidas e não foi executado automaticamente.

## Executar

Na pasta `Projeto final 2`, com o ambiente virtual ativo:

```powershell
python -m pip install -r requirements-ia.txt
python -m streamlit run app.py
python avaliar.py --modo fixture
python -m unittest discover -s tests -q
```

Para uma avaliação real, configure `OPENAI_API_KEY` no `.env` do projeto ou no ambiente. Para publicar o experimento fictício no LangSmith, configure também `LANGSMITH_API_KEY`, `LANGSMITH_TRACING=true` e execute `python avaliar.py --modo api --langsmith`. Não use o backup privado da conversa nesse comando. A contagem de ferramentas é exata; chamadas adicionais ou ausentes recebem zero. Revise manualmente julgamentos difíceis e escreva comentário na saída local antes de concluir a análise.

## Limites

O relatório financeiro é exibido no console e na interface e substitui a exportação Excel neste projeto, conforme decisão do usuário. O verificador não substitui conferência de pagamentos ou identidade. A interface de demonstração não deve ser publicada como sistema autenticado. Métricas do LangSmith dependem da execução real e não constam como concluídas neste documento.
