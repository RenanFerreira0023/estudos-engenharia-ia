"""Aula 04-11: histórico por sessão, enviado explicitamente ao agente."""

from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langsmith import tracing_context
import streamlit as st


# SYSTEM_PROMPT: o veículo precisa vir do cliente; não há catálogo nem recomendação de peças.
INSTRUCOES = """Você é um atendente de uma autopeças fictícia em um exercício de memória de sessão.
Sua única tarefa é reconhecer e recordar o veículo informado pelo cliente nesta conversa.
Use exclusivamente as mensagens deste histórico; não invente veículo, ano ou outros dados.
Se o cliente perguntar pelo veículo sem tê-lo informado nesta conversa, peça que informe o veículo.
Se ele corrigir o veículo, considere a informação mais recente fornecida por ele.
Responda em português, de forma curta. Não recomende peças, não consulte fontes externas
e não afirme que lembra de conversas anteriores ou que salva dados permanentemente."""


# DOTENV: a configuração compartilhada fica na raiz, sem copiar segredos para a aula.
def carregar_ambiente():
    raiz = next((p for p in Path(__file__).resolve().parents if (p / ".git").exists()), None)
    if raiz:
        load_dotenv(raiz / ".env", override=False)


# SESSION_STATE: só inicializamos chaves ausentes; reruns preservam a conversa atual.
def inicializar_sessao():
    for chave, padrao in {"mensagens": [], "eventos": [], "ultima_entrada": [], "erro": None}.items():
        if chave not in st.session_state:
            st.session_state[chave] = deepcopy(padrao)


# NOVA CONVERSA: limpa o histórico e os estados derivados, apenas desta sessão.
# Também é usada ao trocar o modo para não misturar respostas simuladas e reais.
def nova_conversa():
    st.session_state.mensagens = []
    st.session_state.eventos = []
    st.session_state.ultima_entrada = []
    st.session_state.erro = None


# CALLBACKS: registram eventos reais emitidos pelo modelo, sem inventar uma trajetória.
# O handler básico não depende dos blocos de pensamento do StreamlitCallbackHandler legado.
class EventosModelo(BaseCallbackHandler):
    def __init__(self):
        self.eventos = []

    def on_chat_model_start(self, serialized, messages, **kwargs):
        self.eventos.append({"evento": "modelo_iniciado", "mensagens": sum(len(lote) for lote in messages)})

    def on_llm_end(self, response, **kwargs):
        self.eventos.append({"evento": "modelo_concluido"})

    def on_llm_error(self, error, **kwargs):
        self.eventos.append({"evento": "erro_modelo", "tipo": type(error).__name__})


# CREATE_AGENT: sem checkpointer, store ou cache global; a memória é o histórico recebido.
def responder_com_agente(historico):
    modelo = ChatOpenAI(model=os.getenv("MODELO_CHAT_VEICULO", "gpt-4o-mini"), temperature=0)
    agente = create_agent(modelo, tools=[], system_prompt=INSTRUCOES)
    observador = EventosModelo()
    # INVOKE/MESSAGES: enviamos uma cópia de TODA a conversa desta sessão.
    # Não enviamos traces ao LangSmith por uma configuração herdada de outro exercício.
    with tracing_context(enabled=False):
        resultado = agente.invoke({"messages": deepcopy(historico)},
                                  config={"callbacks": [observador], "recursion_limit": 6})
    ultima = resultado["messages"][-1]
    # AI MESSAGE / CONTENT: registramos só a nova resposta, não o histórico retornado inteiro.
    if not isinstance(ultima, AIMessage) or not ultima.text.strip():
        raise ValueError("O agente não devolveu resposta final em texto.")
    return ultima.text, observador.eventos


# SIMULAÇÃO LOCAL: regra determinística para testar a interface; não é compreensão de LLM.
# Lemos somente mensagens do cliente presentes na sessão, sem manter outra memória oculta.
def responder_simulado(historico):
    veiculo = None
    for mensagem in historico:
        if mensagem["role"] != "user":
            continue
        encontrado = re.search(r"meu (?:carro|ve[íi]culo)\s+(?:é|e)\s+(?:(?:um|uma)\s+)?([^.!?\n]+)",
                               mensagem["content"], re.IGNORECASE)
        # FIXTURE CURTA: reconhecemos também Fusca isolado, com ano opcional.
        # É uma entrada de teste prevista, não identificação geral de carros por uma LLM.
        if not encontrado:
            encontrado = re.fullmatch(r"\s*(fusca(?:\s+\d{4})?)[.!]?\s*",
                                       mensagem["content"], re.IGNORECASE)
        if encontrado:
            veiculo = encontrado.group(1).strip()
    resposta = (f"Você informou: {veiculo}." if veiculo else
                "Você ainda não informou o veículo nesta conversa. Qual é o seu carro e ano?")
    return "[SIMULAÇÃO LOCAL] " + resposta, [{"evento": "simulacao_local", "llm_executado": False}]


def exibir_conceitos_estudados():
    with st.sidebar.expander("Como funciona este exercício"):
        st.markdown("1. `st.chat_input` recebe sua mensagem.\n"
                    "2. `st.session_state` guarda o histórico desta sessão.\n"
                    "3. `invoke(messages=...)` recebe a conversa completa.\n"
                    "4. Só a nova resposta entra na lista, uma única vez.\n"
                    "5. **Nova conversa** limpa o contexto e os eventos.")


def main():
    st.set_page_config(page_title="Veículo na sessão · Aula 04-11", page_icon="🚘", layout="centered")
    carregar_ambiente()
    inicializar_sessao()
    st.title("🚘 Qual veículo você informou?")
    st.caption("Aula 04-11 · Chat com histórico por sessão · Autopeças fictícia")

    with st.sidebar:
        st.header("Conversa atual")
        # Trocar o modo limpa a conversa para não reutilizar simulações como falas reais.
        modo = st.radio("Modo", ["Simulação local", "API OpenAI"], key="modo",
                        on_change=nova_conversa)
        st.button("Nova conversa", on_click=nova_conversa, type="primary", use_container_width=True)
        st.markdown("**Experimente:**\n1. Meu carro é um Fusca 1982\n"
                    "2. Qual carro eu informei?\n3. Nova conversa\n4. Qual carro eu informei?")
        exibir_conceitos_estudados()
        st.caption("Cada sessão tem seu próprio histórico. Para atender outro cliente, inicie uma nova conversa.")

    if modo == "Simulação local":
        st.info("SIMULAÇÃO LOCAL: sem LLM. Para testar, use Fusca, Fusca 1982, "
                "Meu carro é… ou Meu veículo é… (também aceita veiculo sem acento).")
    else:
        st.info("API OpenAI: o agente recebe o histórico desta sessão. As chamadas podem consumir créditos.")
    habilitado = modo == "Simulação local" or bool(os.getenv("OPENAI_API_KEY"))
    if not habilitado:
        st.warning("Configure OPENAI_API_KEY no .env da raiz ou use a simulação local.")

    # CHAT_MESSAGE: o rerun desenha o histórico existente sem acrescentar mensagens novamente.
    for mensagem in st.session_state.mensagens:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])

    # CHAT_INPUT: a pergunta é acrescentada uma vez antes de chamar o agente.
    pergunta = st.chat_input("Informe seu carro ou pergunte qual veículo informou", disabled=not habilitado)
    if pergunta and pergunta.strip():
        st.session_state.erro = None
        st.session_state.mensagens.append({"role": "user", "content": pergunta.strip()})
        with st.chat_message("user"):
            st.markdown(pergunta.strip())
        entrada = deepcopy(st.session_state.mensagens)
        try:
            with st.chat_message("assistant"):
                with st.spinner("Respondendo com o contexto desta conversa…"):
                    resposta, eventos = (responder_simulado(entrada) if modo == "Simulação local"
                                         else responder_com_agente(entrada))
                st.markdown(resposta)
            st.session_state.mensagens.append({"role": "assistant", "content": resposta})
            st.session_state.ultima_entrada = entrada
            st.session_state.eventos.append({"turno": len(st.session_state.mensagens) // 2,
                                            "modo": modo, "eventos": eventos})
        except Exception as erro:
            # Falha não vira resposta inventada nem deixa pergunta pendente duplicada na próxima tentativa.
            st.session_state.mensagens.pop()
            st.session_state.erro = type(erro).__name__
    if st.session_state.erro:
        st.error("Não foi possível obter a resposta. A pergunta não foi salva; tente novamente. "
                 f"Verifique conexão e credenciais. Tipo: {st.session_state.erro}")

    with st.expander("Histórico enviado e eventos observados"):
        st.caption("Uma resposta correta só comprova uso do contexto que foi enviado nesta execução.")
        st.json({"ultima_entrada": st.session_state.ultima_entrada, "eventos": st.session_state.eventos})

    # EVIDÊNCIA: exportação explícita só da conversa atual; Nova conversa não mantém histórico oculto.
    evidencia = {"modo": modo, "mensagens": st.session_state.mensagens,
                 "ultima_entrada": st.session_state.ultima_entrada, "eventos": st.session_state.eventos,
                 "limite": "Estado de sessão; não comprova recuperação após reiniciar o servidor."}
    with st.sidebar:
        st.caption(f"Mensagens nesta conversa: {len(st.session_state.mensagens)}")
        st.download_button("Baixar evidência desta conversa", json.dumps(evidencia, ensure_ascii=False, indent=2),
                           file_name="conversa-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json",
                           mime="application/json")
    st.caption("O histórico vive na sessão atual. Sem banco ou arquivo de memória, não há garantia de recuperação "
               "após recarregar a página, encerrar a sessão ou reiniciar o servidor.")


if __name__ == "__main__":
    main()
