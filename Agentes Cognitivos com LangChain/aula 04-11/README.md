# Aula 04-11 — Avaliação e histórico de chat

Material: [apostila da aula](./apostila_agentes_cognitivos_aula_08.html).

## Exercícios

- [O atendente consultou a política?](./O%20atendente%20consultou%20a%20politica/):
  avaliar separadamente resposta sobre pagamento e uso efetivo da ferramenta.
  Três casos independentes, comparador exato, LLM juiz com critérios explícitos,
  fixture adversarial e tabela com revisão humana.

- [Chat que lembra o veículo na sessão](./Chat%20que%20lembra%20o%20veiculo%20na%20sessao/):
  interface Streamlit com histórico por sessão enviado ao agente, Nova conversa,
  callbacks reais e evidências de lembrança e ausência de contexto após limpar.

## Conceitos praticados

`@tool` fornece uma política fictícia; `create_agent`/`invoke` processam perguntas
isoladas; mensagens AI/Tool registram chamadas e retornos. Python compara listas;
o LLM juiz avalia significado com saída estruturada. `Client` e `evaluate` permitem
cadastrar o conjunto e publicar resultados reais opcionalmente no LangSmith.

**Fluxo:** casos → execução isolada → resposta/consulta → notas separadas → revisão.

Consulte o README do exercício para comandos. O `.env` compartilhado é o da raiz.
Fixtures locais não são execuções reais do agente nem métricas de LangSmith.

No chat do veículo, `st.session_state` mantém mensagens entre reruns; `st.chat_input`/`st.chat_message` recebem e exibem a conversa. `invoke` recebe o histórico completo e só a nova resposta é acrescentada. Limpar remove esse contexto; não há persistência após reiniciar.
