"""Cliente de prova AutoTools: consulta técnica externa sem inferir cobertura."""
import json
import re

import httpx


BASE_URL = "https://autotools.brightcoding.dev"
ATRIBUICAO = "Dados consultados na AutoTools — https://autotools.brightcoding.dev"


# HTTP COM CONTRATO: sucesso de rede, Content-Type e estrutura JSON são verificações distintas.
# Transporte injetado permite exercitar erros sem apresentá-los como chamadas reais.
class ClienteAutoTools:
    def __init__(self, transporte=None, timeout=12):
        self.transporte = transporte
        self.timeout = timeout
        self.origem = "autotools_real" if transporte is None else "transporte_injetado_teste"

    def _consultar(self, caminho, parametros=None):
        url = BASE_URL + caminho
        base = {"origem": self.origem, "atribuicao": ATRIBUICAO,
                "url": url, "parametros": parametros or {}, "http_status": None,
                "content_type": None, "json": None}
        try:
            if self.transporte is None:
                with httpx.Client(timeout=self.timeout, follow_redirects=False) as cliente:
                    resposta = cliente.get(url, params=parametros, headers={
                        "Accept": "application/json", "User-Agent": "AutoSuperPartsCWB-academic-probe/1.0"})
                codigo, tipo, corpo = resposta.status_code, resposta.headers.get("content-type", ""), resposta.text
            else:
                codigo, tipo, corpo = self.transporte(url, parametros or {}, self.timeout)
            base.update(http_status=codigo, content_type=tipo)
            if codigo != 200:
                return {**base, "status": "erro_http", "amostra_corpo": corpo[:1500]}
            media_type = tipo.split(";", 1)[0].strip().lower()
            if media_type != "application/json" and not media_type.endswith("+json"):
                return {**base, "status": "content_type_invalido", "amostra_corpo": corpo[:1500]}
            try:
                dados = json.loads(corpo)
            except (ValueError, TypeError):
                return {**base, "status": "json_invalido", "amostra_corpo": corpo[:1500]}
            if not isinstance(dados, dict):
                return {**base, "status": "contrato_invalido", "json": dados}
            return {**base, "status": "ok", "json": dados}
        except httpx.TimeoutException:
            return {**base, "status": "timeout"}
        except (httpx.RequestError, OSError):
            return {**base, "status": "indisponivel"}

    # BUSCA: a consulta ampla investiga cobertura, não autoriza assumir equivalência técnica.
    def buscar(self, veiculo, ampla=False):
        params = {"q": veiculo["modelo"], "per_page": 10}
        if not ampla:
            params.update(make=veiculo["marca"], model=veiculo["modelo"], year=veiculo["ano_modelo"],
                          engine=veiculo["motor"], fuel=veiculo["combustivel"])
        retorno = self._consultar("/api/vehicles/search", params)
        if retorno["status"] == "ok":
            dados = retorno["json"].get("data")
            if not isinstance(dados, list) or any(not isinstance(item, dict) for item in dados):
                retorno["status"] = "contrato_invalido"
            else:
                retorno["status"] = "candidatos_retornados" if dados else "sem_resultados"
        return retorno

    def detalhe(self, identificador):
        # IDs vêm da busca, nunca de exemplos da documentação ou do código de produto local.
        if isinstance(identificador, bool) or not re.fullmatch(r"[0-9]+", str(identificador)):
            raise ValueError("ID externo numérico obtido da busca é obrigatório.")
        retorno = self._consultar(f"/api/vehicles/{identificador}")
        if retorno["status"] == "ok" and not isinstance(retorno["json"].get("data"), dict):
            retorno["status"] = "contrato_invalido"
        return retorno

    def secao(self, identificador, secao):
        if secao not in ("parts", "oil"):
            raise ValueError("Seção permitida: parts ou oil.")
        if isinstance(identificador, bool) or not re.fullmatch(r"[0-9]+", str(identificador)):
            raise ValueError("ID externo numérico obtido da busca é obrigatório.")
        retorno = self._consultar(f"/api/vehicles/{identificador}/{secao}")
        if retorno["status"] == "ok":
            disponivel = retorno["json"].get("available")
            if disponivel is False:
                retorno["status"] = "secao_indisponivel"
            elif disponivel is True and isinstance(retorno["json"].get("data"), dict):
                retorno["status"] = "secao_disponivel"
            else:
                retorno["status"] = "contrato_invalido"
        return retorno
