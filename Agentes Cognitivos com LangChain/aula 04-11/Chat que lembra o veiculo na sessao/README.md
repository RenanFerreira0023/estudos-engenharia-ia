# Chat que lembra o veículo na sessão

Exercício da aula 04-11: reconhecer o veículo informado pelo cliente e recordá-lo
na mesma conversa, sem recomendar peças nem inventar informações.

## Executar

Na raiz do repositório, com a `.venv` ativa:

```powershell
python -m streamlit run "Agentes Cognitivos com LangChain\aula 04-11\Chat que lembra o veiculo na sessao\app.py"
```

O Streamlit abre uma página local, normalmente em `http://localhost:8501`.
O terminal precisa continuar aberto. Para encerrar, use **Ctrl+C**.
Não execute apenas `python app.py`: a interface precisa do servidor Streamlit.

Dependências, caso necessário:

```powershell
python -m pip install streamlit langchain langchain-openai langsmith python-dotenv
```

## Como testar

1. **Simulação local** funciona sem API. Cada resposta tem essa identificação.
   Usa uma regra determinística para verificar a interface, não um LLM.
   Reconhece `Meu carro é…`, `Meu veículo é…` (com ou sem acento em veículo)
   e a fixture curta `Fusca`, com ano opcional. Sem ano informado, não inventa um.
   Outras frases livres podem não ser reconhecidas; para compreensão por modelo, use API OpenAI.
2. Para testar compreensão real, selecione **API OpenAI** na lateral.
   A configuração usa `OPENAI_API_KEY` do ambiente ou `.env` da raiz do repositório.
   Não copie `.env` para a aula. Modelo opcional: `MODELO_CHAT_VEICULO`; padrão `gpt-4o-mini`.
3. Envie **Meu carro é um Fusca 1982**.
4. Envie **Qual carro eu informei?**. A resposta deve mencionar **Fusca 1982**.
5. Baixe a evidência desta conversa antes de limpar, se quiser guardá-la.
6. Clique em **Nova conversa** e envie **Qual carro eu informei?** novamente.
   O atendente deve pedir o veículo, sem mencionar o Fusca como se ainda soubesse dele.
7. Baixe essa segunda evidência. O expander exibe o histórico enviado e os eventos.

Trocar o modo também limpa o contexto para não misturar respostas simuladas e reais.
Para outro cliente, use Nova conversa. Não há uma lista global de mensagens nem cache
compartilhado de conversa. Sessões independentes recebem históricos independentes;
isso não cria autenticação de clientes nem separa pessoas usando a mesma sessão aberta.

## Por que lembra? E por que isso não é memória permanente?

`st.session_state.mensagens` conserva a lista durante os reruns **da mesma sessão**.
O app inicializa essa chave somente quando ela ainda não existe. Cada envio adiciona
a pergunta, passa uma cópia da lista inteira a `agente.invoke({"messages": historico})`,
extrai a última `AIMessage` e acrescenta somente essa resposta, uma vez.

O modelo não guarda o carro por conta própria: ele o recebe novamente no histórico.
O app não usa checkpointer, store, banco, cache global de mensagens ou arquivo de memória.
**Nova conversa** limpa mensagens, última entrada, eventos e erro da sessão.
Baixar evidência é uma exportação para estudo; o app não a importa como memória.

Acertar na mesma sessão **não comprova recuperação após reiniciar**: o teste só demonstra
que o histórico atual foi enviado ao agente. Encerrar a sessão ou reiniciar o servidor
elimina o estado em memória; recarregar a página pode criar uma sessão nova. Recuperação
durável exigiria persistência e identificação de usuário/sessão, fora deste exercício.

## Conceitos praticados

- `st.session_state`: histórico e eventos exclusivos da sessão.
- `st.chat_input` / `st.chat_message`: entrada e renderização do chat.
- `create_agent` e `system_prompt`: agente limitado aos dados fornecidos pelo cliente.
- `invoke` com `messages`: contexto completo da conversa; sem memória interna adicional.
- `AIMessage.text`: extração da nova resposta, evitando duplicar o histórico retornado.
- Callbacks: `BaseCallbackHandler` registra início, término e erro reais do modelo.
- Evidências: exportação JSON antes e depois de limpar, sem alegar memória persistente.

**Fluxo:** pergunta → histórico da sessão → agente com `messages` → nova resposta → histórico.

O `StreamlitCallbackHandler` é opcional no enunciado. Esta implementação usa
`BaseCallbackHandler` para observar os eventos do agente atual sem depender de widgets
de pensamento do handler legado. Não exibe raciocínio interno nem inventa chamadas de ferramentas.

## Verificações

`verificar_interface.py` usa o `AppTest` oficial para submeter mensagens e clicar em Nova conversa,
verificando contexto, ausência de duplicação, reruns, troca de modo e isolamento de sessões.
Por padrão, os testes são simulados e identificados como tais. `--api` executa também os dois
cenários com OpenAI e registra entradas, respostas e eventos observados em `evidencias/`.

```powershell
python verificar_interface.py
python verificar_interface.py --api
```

Uma checagem textual de Fusca/1982 ajuda a localizar o resultado; leia as respostas
registradas para confirmar significado. Não é um LLM juiz nem uma certificação geral.

Implementação preparada com auxílio de IA a partir do enunciado.

Referências: [AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest),
[create_agent](https://reference.langchain.com/python/langchain/agents/factory/create_agent).
