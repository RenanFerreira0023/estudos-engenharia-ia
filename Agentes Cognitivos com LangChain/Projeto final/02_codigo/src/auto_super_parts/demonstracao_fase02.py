"""Demonstrações importadas pelo notebook; modo simulado nunca aciona rede."""
import json

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_core.utils.function_calling import convert_to_openai_tool

from .agente_fase02 import AtendimentoFase02, exibir_turno, registrar_execucao
from .viacep import ClienteViaCEP, criar_cliente_dummy


# CASOS separam expectativas dos retornos efetivamente produzidos por ferramentas e modelo.
CASOS = {
    "retirada": {
        "mensagem": "Quero 2 unidades do P003 para retirada. Consulte preço e estoque e calcule o orçamento.",
        "esperado": {"status": "ok", "subtotal_centavos": 3700, "frete_centavos": 0, "total_centavos": 3700},
    },
    "entrega_cadastrada": {
        "mensagem": "Consulte o CEP 84010000 no ViaCEP e calcule 2 unidades do P003 para entrega nesse endereço.",
        "cep": "84010000", "municipio": "Ponta Grossa", "uf": "PR",
        "esperado": {"status": "parcial", "subtotal_centavos": 3700, "frete_centavos": 531,
                     "total_centavos": 4231, "prazo_dias_uteis": 4},
    },
    "entrega_sem_distancia": {
        "mensagem": "Consulte o CEP 01001000 no ViaCEP e calcule 2 unidades do P003 para entrega nesse endereço. Se faltar distância cadastrada, informe a pendência.",
        "cep": "01001000", "municipio": "São Paulo", "uf": "SP",
        "esperado": {"status": "cotacao_entrega_pendente", "subtotal_centavos": 3700,
                     "frete_centavos": None, "total_centavos": None, "prazo_dias_uteis": None},
    },
}


class ModeloRoteirizadoFase02(FakeMessagesListChatModel):
    # INJEÇÃO testa o ciclo do agente; não representa extração nem decisão de uma LLM real.
    def bind_tools(self, tools, **kwargs):
        return self


def modelo_simulado(caso):
    chamadas = [("consultar_catalogo", {"produto_id": "P003"})]
    argumentos = {"itens": [{"produto_id": "P003", "quantidade": 2}],
                  "modalidade": "entrega" if caso.get("cep") else "retirada"}
    if caso.get("cep"):
        chamadas.append(("consultar_cep", {"cep": caso["cep"]}))
        argumentos.update(municipio=caso["municipio"], uf=caso["uf"])
    chamadas.append(("calcular_orcamento", argumentos))
    respostas = [AIMessage(content="", tool_calls=[{"name": nome, "args": args, "id": f"simulado_{i}"}])
                 for i, (nome, args) in enumerate(chamadas)]
    respostas.append(AIMessage(content="Demonstração roteirizada: consulte os retornos reais das funções acima. Não houve geração por LLM nem chamada HTTP real."))
    return ModeloRoteirizadoFase02(responses=respostas)


def conferir_caso(resultado, caso):
    # AUDITORIA LOCAL compara dados das ferramentas; não transforma uma frase final em prova do cálculo.
    trajetoria = resultado["trajetoria"]
    retornos = [(i, t["ferramenta"], json.loads(t["conteudo"]))
                for i, t in enumerate(trajetoria) if t["tipo"] == "tool"]
    calculos = [(i, r) for i, nome, r in retornos if nome == "calcular_orcamento"]
    consultas = [(i, r) for i, nome, r in retornos if nome == "consultar_catalogo" and r.get("status") == "ok"]
    checks = {"execucao_ok": resultado["status"] == "ok",
              "sem_argumentos_invalidos": all(r.get("status") != "entrada_invalida" for _, _, r in retornos),
              "calculo_executado": bool(calculos)}
    if calculos:
        indice, calculo = calculos[-1]
        checks.update({f"calculo.{k}": calculo.get(k) == v for k, v in caso["esperado"].items()})
        checks["catalogo_antes_calculo"] = any(i < indice for i, _ in consultas)
        if consultas:
            preco = next((p["preco_centavos"] for _, r in consultas for p in r["produtos"] if p["id"] == "P003"), None)
            checks["subtotal_independente"] = preco is not None and calculo.get("subtotal_centavos") == preco * 2
        if caso.get("cep"):
            ceps = [(i, r) for i, nome, r in retornos if nome == "consultar_cep" and r.get("status") == "ok"]
            checks["cep_antes_calculo"] = any(i < indice for i, _ in ceps)
            args_calculo = [c["args"] for t in trajetoria for c in t.get("tool_calls", []) if c["name"] == "calcular_orcamento"]
            checks["destino_do_retorno_cep"] = bool(ceps and args_calculo and
                args_calculo[-1].get("municipio") == ceps[-1][1]["endereco"]["localidade"] and
                args_calculo[-1].get("uf") == ceps[-1][1]["endereco"]["uf"])
    return checks


def executar_caso(nome, modo="real"):
    if modo not in ("real", "simulado"):
        raise ValueError("Use real ou simulado explicitamente.")
    caso = CASOS[nome]
    sistema = AtendimentoFase02(modelo=modelo_simulado(caso) if modo == "simulado" else None,
                               cliente_cep=criar_cliente_dummy() if modo == "simulado" else None)
    try:
        resultado = sistema.atender(caso["mensagem"])
    finally:
        sistema.fechar()
    verificacoes = conferir_caso(resultado, caso)
    relatorio = {"fase": 2, "modo": modo, "caso": nome, "entrada": caso["mensagem"],
                 "esperado": caso["esperado"], "observado": resultado, "verificacoes": verificacoes,
                 "aprovado_dados_e_trajetoria": all(verificacoes.values()),
                 "limite": "Verificações automáticas não certificam toda a semântica da resposta final; inspecione o texto e as fontes."}
    arquivo = registrar_execucao(relatorio, f"fase02_caso_{nome}_{modo}")
    print("Modo:", modo, "| Caso:", nome, "| Mensagem:", caso["mensagem"])
    exibir_turno(resultado)
    print("[conferência]", json.dumps(verificacoes, ensure_ascii=False))
    print("[relatório]", arquivo.name)
    return relatorio


def esquemas_para_estudo(sistema):
    # JSON SCHEMA distingue propriedades de argumentos de restrições como minItems.
    return {"validacao_local": sistema.ferramentas[-1].args_schema.model_json_schema(),
            "openai_estrito": [convert_to_openai_tool(t, strict=True) for t in sistema.ferramentas]}


def demonstrar_falhas_cep():
    # TRANSPORTE INJETADO demonstra falhas reproduzíveis sem fingir indisponibilidade real da API.
    def timeout(*args):
        raise TimeoutError("Falha simulada")
    resultados = {"entrada_invalida": criar_cliente_dummy().consultar("123"),
                  "nao_encontrado_simulado": criar_cliente_dummy().consultar("99999999"),
                  "timeout_simulado": ClienteViaCEP(timeout).consultar("01001000")}
    print(json.dumps(resultados, ensure_ascii=False, indent=2))
    print("[evidência]", registrar_execucao(resultados, "fase02_falhas_cep_simuladas").name)
    return resultados
