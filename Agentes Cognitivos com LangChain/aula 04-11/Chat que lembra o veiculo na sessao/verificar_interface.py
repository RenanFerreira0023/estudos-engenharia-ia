"""Testa o app via AppTest: sem API por padrão; --api acrescenta execução real."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from unittest.mock import patch

from dotenv import load_dotenv
from streamlit.testing.v1 import AppTest

PASTA = Path(__file__).resolve().parent


def verificar_sem_erros(app):
    assert not app.exception, [e.message for e in app.exception]
    assert app.session_state["erro"] is None, app.session_state["erro"]


def fotografar_estado(app):
    return {chave: deepcopy(app.session_state[chave]) for chave in
            ["mensagens", "ultima_entrada", "eventos"]}


def enviar(app, texto):
    app.chat_input[0].set_value(texto).run(timeout=90)
    verificar_sem_erros(app)


# APPTEST simula interações da interface Streamlit, incluindo seus reruns e callbacks.
def verificar_cenarios(modo):
    app = AppTest.from_file(str(PASTA / "app.py"), default_timeout=90).run()
    verificar_sem_erros(app)
    if modo == "API OpenAI":
        app.radio[0].set_value(modo).run()
        verificar_sem_erros(app)

    enviar(app, "Meu carro é um Fusca 1982")
    assert len(app.session_state["mensagens"]) == 2
    enviar(app, "Qual carro eu informei?")
    mesma_conversa = fotografar_estado(app)
    resposta = mesma_conversa["mensagens"][-1]["content"]
    assert "fusca" in resposta.lower() and "1982" in resposta, resposta
    assert len(mesma_conversa["mensagens"]) == 4
    assert len(mesma_conversa["ultima_entrada"]) == 3
    assert mesma_conversa["ultima_entrada"][0]["content"] == "Meu carro é um Fusca 1982"
    assert len(app.chat_message) == 4

    # RERUN sem entrada nova não deve anexar mensagens nem fazer nova chamada ao modelo.
    app.run()
    verificar_sem_erros(app)
    assert fotografar_estado(app) == mesma_conversa
    assert len(app.chat_message) == 4

    app.button[0].click().run()
    verificar_sem_erros(app)
    assert fotografar_estado(app) == {"mensagens": [], "ultima_entrada": [], "eventos": []}
    assert len(app.chat_message) == 0
    enviar(app, "Qual carro eu informei?")
    apos_limpar = fotografar_estado(app)
    resposta_sem_contexto = apos_limpar["mensagens"][-1]["content"]
    assert "fusca" not in resposta_sem_contexto.lower() and "1982" not in resposta_sem_contexto
    assert re.search(r"carro|ve[íi]culo", resposta_sem_contexto, re.IGNORECASE), resposta_sem_contexto
    assert len(apos_limpar["mensagens"]) == 2
    assert apos_limpar["ultima_entrada"] == [{"role": "user", "content": "Qual carro eu informei?"}]

    if modo == "API OpenAI":
        eventos = [e["evento"] for turno in mesma_conversa["eventos"] for e in turno["eventos"]]
        assert "modelo_iniciado" in eventos and "modelo_concluido" in eventos, eventos
    return {"modo": modo, "mesma_conversa": mesma_conversa, "apos_limpar": apos_limpar,
            "verificacoes": {"veiculo_na_mesma_sessao": True, "sem_veiculo_apos_limpar": True,
                              "sem_duplicacao_em_rerun": True, "limpeza_de_estados": True},
            "limite": "Não testa recuperação após reiniciar; não há persistência durável."}


def verificar_isolamento_e_troca():
    cliente_a = AppTest.from_file(str(PASTA / "app.py")).run()
    enviar(cliente_a, "Meu carro é um Fusca 1982")
    cliente_b = AppTest.from_file(str(PASTA / "app.py")).run()
    enviar(cliente_b, "Qual carro eu informei?")
    assert "Fusca" not in cliente_b.session_state["mensagens"][-1]["content"]
    assert len(cliente_a.session_state["mensagens"]) == 2
    cliente_a.radio[0].set_value("API OpenAI").run()
    assert cliente_a.session_state["mensagens"] == []
    assert cliente_a.session_state["eventos"] == []
    cliente_a.radio[0].set_value("Simulação local").run()
    assert cliente_a.session_state["mensagens"] == []
    return {"origem": "AppTest com simulação local", "sessoes_independentes": True,
            "troca_de_modo_limpa_contexto": True}


def verificar_variantes_simuladas():
    # Casos escritos manualmente após observar a limitação do simulador no uso da interface.
    observados = []
    for declaracao in ["fusca", "meu veiculo é um fusca", "Meu veículo é um Fusca 1974"]:
        app = AppTest.from_file(str(PASTA / "app.py")).run()
        enviar(app, declaracao)
        enviar(app, "Qual carro eu informei?")
        resposta = app.session_state["mensagens"][-1]["content"]
        assert "fusca" in resposta.lower(), resposta
        if "1974" in declaracao:
            assert "1974" in resposta
        else:
            assert not re.search(r"\b\d{4}\b", resposta), resposta
        enviar(app, "Meu carro é um Fusca 1974")
        enviar(app, "Qual carro eu informei?")
        assert "1974" in app.session_state["mensagens"][-1]["content"]
        app.button[0].click().run()
        enviar(app, "Qual carro eu informei?")
        assert "fusca" not in app.session_state["mensagens"][-1]["content"].lower()
        observados.append({"entrada": declaracao, "resposta_simulada": resposta,
                           "ano_nao_inventado": True, "correcao_e_limpeza": True})
    return observados


def verificar_falha_sem_duplicacao():
    # Falha injetada localmente; não é uma falha observada de API ou do agente real.
    with patch.dict(os.environ, {"OPENAI_API_KEY": "chave-ficticia-para-teste"}):
        app = AppTest.from_file(str(PASTA / "app.py")).run()
        app.radio[0].set_value("API OpenAI").run()
        with patch("langchain.agents.create_agent", side_effect=RuntimeError("Falha de teste")):
            app.chat_input[0].set_value("Meu carro é um Fusca 1982").run()
        assert not app.exception
        assert app.session_state["mensagens"] == []
        assert app.session_state["erro"] == "RuntimeError"
        app.button[0].click().run()
        assert app.session_state["erro"] is None
    return {"origem": "falha injetada localmente", "pergunta_nao_duplicada": True,
            "nova_conversa_limpa_erro": True}


# EVIDÊNCIAS distinguem respostas simuladas de chamadas reais, preservando entradas e eventos.
def salvar(evidencia, tipo):
    pasta = PASTA / "evidencias"
    pasta.mkdir(exist_ok=True)
    base = pasta / (tipo + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    base.with_suffix(".json").write_text(json.dumps(evidencia, ensure_ascii=False, indent=2), encoding="utf-8")
    principal = evidencia["chat"]
    def celula(texto):
        return texto.replace("|", "\\|").replace("\n", "<br>")
    linhas = ["# Evidências — " + principal["modo"], "",
              "Execução pela interface de teste AppTest; não é um teste manual no navegador.", "",
              "| Situação | Entrada enviada ao agente | Resposta observada |",
              "| --- | --- | --- |"]
    for chave, rotulo in [("mesma_conversa", "Mesma conversa"), ("apos_limpar", "Após Nova conversa")]:
        estado = principal[chave]
        entradas = json.dumps(estado["ultima_entrada"], ensure_ascii=False)
        resposta = estado["mensagens"][-1]["content"]
        linhas.append(f"| {rotulo} | {celula(entradas)} | {celula(resposta)} |")
    linhas.extend(["", "As verificações textuais passaram. Leia as respostas para conferir seu significado.",
                   "O JSON registra também os callbacks, os reruns e a limpeza de estados.", "",
                   "Não comprova recuperação após reinício: o veículo foi reenviado no histórico da mesma sessão."])
    base.with_suffix(".md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("Evidência:", base.with_suffix(".md"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", action="store_true")
    args = parser.parse_args()
    raiz = next((p for p in PASTA.parents if (p / ".git").exists()), None)
    if raiz:
        load_dotenv(raiz / ".env", override=False)
    simulacao = {"chat": verificar_cenarios("Simulação local"),
                 "isolamento": verificar_isolamento_e_troca(),
                 "falha": verificar_falha_sem_duplicacao(),
                 "variantes_simuladas": verificar_variantes_simuladas()}
    salvar(simulacao, "simulacao")
    if args.api:
        if not os.getenv("OPENAI_API_KEY"):
            parser.error("Configure OPENAI_API_KEY para testar a API.")
        salvar({"chat": verificar_cenarios("API OpenAI")}, "api-real")
    print("Verificações concluídas.")


if __name__ == "__main__":
    main()
