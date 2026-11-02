import json
import re
import socket
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def requisitar_https(url, timeout):
    # API REAL tem destino fixo HTTPS; CEP validado nunca pode escolher outra URL.
    with urlopen(url, timeout=timeout) as resposta:
        return resposta.status, resposta.read().decode("utf-8")


class ClienteViaCEP:
    def __init__(self, transporte=None, timeout=10):
        # INJEÇÃO permite simular falhas sem chamar a rede; a origem nunca é apresentada como real nesse caso.
        self.transporte = transporte or requisitar_https
        self.origem = "viacep_real" if transporte is None else "transporte_injetado_teste"
        self.timeout = timeout

    def consultar(self, cep):
        cep_normalizado = cep.replace("-", "") if isinstance(cep, str) and re.fullmatch(r"[0-9]{5}-[0-9]{3}", cep) else cep
        base = {"origem": self.origem, "cep": cep_normalizado, "endereco": None, "tentativa_http_real": False}
        # VALIDAÇÃO LOCAL preserva zero inicial; entrada inválida não aciona transporte.
        if not isinstance(cep_normalizado, str) or not re.fullmatch(r"[0-9]{8}", cep_normalizado):
            return {**base, "status": "cep_invalido", "pendencias": ["Informe CEP com oito dígitos."]}
        url = f"https://viacep.com.br/ws/{cep_normalizado}/json/"
        base.update(url=url, tentativa_http_real=self.origem == "viacep_real")
        try:
            codigo, corpo = self.transporte(url, self.timeout)
            base["codigo_http"] = codigo
            if codigo != 200:
                return {**base, "status": "erro_http"}
            dados = json.loads(corpo)
            if not isinstance(dados, dict):
                return {**base, "status": "resposta_invalida"}
            if dados.get("erro") in (True, "true"):
                return {**base, "status": "cep_nao_encontrado"}
            if (not isinstance(dados.get("localidade"), str) or not dados["localidade"].strip()
                    or not isinstance(dados.get("uf"), str) or not re.fullmatch(r"[A-Z]{2}", dados["uf"])
                    or str(dados.get("cep", "")).replace("-", "") != cep_normalizado):
                return {**base, "status": "resposta_invalida"}
            endereco = {k: dados.get(k) for k in ("cep", "logradouro", "complemento", "bairro", "localidade", "uf", "ibge")}
            return {**base, "status": "ok", "endereco": endereco,
                    "limite": "ViaCEP informa endereço; não fornece distância, frete ou prazo."}
        except HTTPError as erro:
            return {**base, "status": "erro_http", "codigo_http": erro.code}
        except (TimeoutError, socket.timeout):
            return {**base, "status": "timeout"}
        except (URLError, OSError):
            return {**base, "status": "indisponivel"}
        except (ValueError, UnicodeError):
            return {**base, "status": "resposta_invalida"}


def criar_cliente_dummy():
    # FIXTURES estão separadas das respostas observadas. Nunca há fallback real -> dummy.
    from .configuracao import localizar_projeto
    arquivo = localizar_projeto() / "04_avaliacao_e_evidencias/casos/viacep_dummy_fase02.json"
    fixtures = json.loads(arquivo.read_text(encoding="utf-8"))["respostas_simuladas"]

    def transporte(url, timeout):
        cep = url.split("/")[-3]
        return 200, json.dumps(fixtures.get(cep, {"erro": True}), ensure_ascii=False)

    return ClienteViaCEP(transporte=transporte)
