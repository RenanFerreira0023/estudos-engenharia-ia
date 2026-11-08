"""Repete perguntas dos testes assistidos; --real faz chamadas pagas à OpenAI e ViaCEP."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from auto_super_parts.agente_fase02 import AtendimentoFase02
from auto_super_parts.chain_inicial import criar_modelo
from auto_super_parts.configuracao import localizar_projeto


# CASOS REAIS ANTERIORES: mesmos pedidos, sem gabarito enviado ao modelo.
CASOS = [
    ("oleo", "Tenho um Fusca 1982 1600 a ar, gasolina. Qual viscosidade de óleo devo usar e quantos litros vão no motor?"),
    ("correia", "Tenho um Fusca 1982 1600 a ar, gasolina. Quero uma correia dentada."),
    ("frete_sem_distancia", "Oi, qual fica o frete para 01001000?"),
    ("frete_cadastrado", "Qual fica o frete para o CEP 84010000?"),
    ("retirada", "Quero 2 unidades do P003 para retirada. Consulte preço e estoque e calcule o orçamento."),
    ("sem_estoque", "Quero 1 unidade do P023 para retirada. Tem estoque?"),
]


def conferir(caso, observado):
    chamadas = [c["name"] for m in observado["trajetoria"] for c in m.get("tool_calls", [])]
    retornos = [(m["ferramenta"], json.loads(m["conteudo"])) for m in observado["trajetoria"] if m["tipo"] == "tool"]
    texto = observado.get("resposta", "").casefold()
    checks = {"execucao_ok": observado["status"] == "ok",
              "sem_avisos_repetitivos": not re.search(r"simula|fict[ií]ci|acad[eê]mic", texto)}
    if caso == "oleo":
        checks.update(consulta_tecnica="consultar_informacao_tecnica" in chamadas,
                      especificacao_nao_inventada=not re.search(r"\d\s*[wW]|\d[,.]\d+\s*litro", texto),
                      limite_informado="não tenho especificações verificadas" in texto)
    elif caso == "correia":
        checks.update(consulta_tecnica="consultar_informacao_tecnica" in chamadas,
                      resposta_distingue_tipos="engrenagens" in texto and "não a substitui" in texto,
                      sem_indicacao_p023="p023" not in texto)
    elif caso.startswith("frete_"):
        entrega = next((r for f, r in retornos if f == "consultar_entrega"), {})
        cep = next((r for f, r in retornos if f == "consultar_cep"), {})
        checks.update(cep_real=cep.get("origem") == "viacep_real" and cep.get("codigo_http") == 200,
                      consulta_regra="consultar_entrega" in chamadas,
                      cep_antes_regra=("consultar_entrega" in chamadas and "consultar_cep" in chamadas
                                      and chamadas.index("consultar_cep") < chamadas.index("consultar_entrega")),
                      sem_exigir_produtos="calcular_orcamento" not in chamadas)
        if caso == "frete_sem_distancia":
            checks.update(frete_indisponivel=entrega.get("status") == "cotacao_entrega_pendente"
                          and entrega.get("frete_centavos") is None,
                          falta_distancia_explicada=bool(re.search(r"dist[aâ]ncia|cadastrad|tabela", texto)))
        else:
            checks.update(frete_correto=entrega.get("frete_centavos") == 531,
                          prazo_correto=entrega.get("prazo_dias_uteis") == 4)
    elif caso == "retirada":
        calculo = next((r for f, r in retornos if f == "calcular_orcamento"), {})
        checks["total_correto"] = calculo.get("total_centavos") == 3700
    else:
        catalogo = next((r for f, r in retornos if f == "consultar_catalogo"), {})
        checks["estoque_zero"] = any(p["id"] == "P023" and p["estoque"] == 0 for p in catalogo.get("produtos", []))
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real", action="store_true", help="Autoriza chamadas reais para estes seis casos.")
    parser.add_argument("--env", type=Path, help="Arquivo .env explícito; padrão: projeto atual.")
    args = parser.parse_args()
    if not args.real:
        parser.error("Use --real para executar APIs; para testes locais, execute a suíte unittest.")
    sistema = AtendimentoFase02(modelo=criar_modelo(arquivo_env=args.env))
    resultados = []
    try:
        for caso, pergunta in CASOS:
            observado = sistema.atender(pergunta)
            checks = conferir(caso, observado)
            resultados.append({"caso": caso, "entrada": pergunta, "observado": observado,
                               "verificacoes": checks, "aprovado": all(checks.values())})
            print(caso, checks, flush=True)
    finally:
        sistema.fechar()
    pasta = localizar_projeto() / "04_avaliacao_e_evidencias/resultados"
    arquivo = pasta / ("correcao_08_11_real_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    arquivo.write_text(json.dumps({"modo": "OpenAI e ViaCEP reais", "casos": resultados,
                                   "limite": "Critérios específicos e checagens textuais; não é avaliação semântica universal."},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
    print("Evidência:", arquivo)
    raise SystemExit(0 if all(r["aprovado"] for r in resultados) else 1)


if __name__ == "__main__":
    main()
