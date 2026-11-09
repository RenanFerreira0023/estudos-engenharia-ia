import json
import unicodedata
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .configuracao import localizar_projeto


# BASEMODEL valida o contrato do item; não existe argumento de preço ditado pelo cliente/modelo.
class ItemOrcamento(BaseModel):
    model_config = ConfigDict(extra="forbid")
    produto_id: str = Field(min_length=1, description="ID ou SKU retornado pela consulta do catálogo.")
    quantidade: int = Field(strict=True, gt=0, description="Unidades inteiras positivas explicitamente solicitadas.")


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto.strip().casefold()) if not unicodedata.combining(c))


def frete_por_distancia(distancia_km, regras):
    # DECIMAL aplica a regra fictícia sem arredondar a distância; só o valor final vira centavos inteiros.
    distancia = Decimal(str(distancia_km))
    if not distancia.is_finite() or distancia < 0:
        raise ValueError("Distância deve ser finita e não negativa.")
    externo = regras["frete"]["externo"]
    taxa = distancia * Decimal(str(externo["valor_base_centavos"])) / Decimal(str(externo["distancia_base_km"]))
    prazo = regras["prazo"]["externo"]
    faixas = (distancia / Decimal(str(prazo["faixa_km"]))).to_integral_value(rounding=ROUND_CEILING)
    return int(taxa.quantize(Decimal("1"), rounding=ROUND_HALF_UP)), int(faixas) * prazo["dias_uteis_por_faixa"]


def consultar_entrega(municipio=None, uf=None):
    # CONSULTA DE ENTREGA: a mesma regra atende frete isolado e orçamento, sem exigir produtos.
    pasta = localizar_projeto() / "02_codigo/dados"
    regras = json.loads((pasta / "loja_regras.json").read_text(encoding="utf-8"))
    registros = json.loads((pasta / "distancias_simuladas.json").read_text(encoding="utf-8"))
    base = {"frete_centavos": None, "prazo_dias_uteis": None,
            "distancia_km_simulada": None, "pendencias": [],
            "fontes_regras": ["loja_regras.json", "distancias_simuladas.json"]}
    if not municipio or not uf:
        return {**base, "status": "destino_pendente", "pendencias": ["Consulte o CEP e informe município e UF retornados antes de cotar entrega."]}
    cidade = next((c for c in registros["cidades"] if normalizar(c["municipio"]) == normalizar(municipio) and normalizar(c["uf"]) == normalizar(uf)), None)
    if cidade is None:
        return {**base, "status": "cotacao_entrega_pendente", "pendencias": ["Cidade/UF sem distância simulada cadastrada; sem cotação automática de frete/total com entrega."]}
    base["distancia_km_simulada"] = cidade["distancia_km"]
    if normalizar(municipio) == normalizar(regras["loja"]["municipio"]) and normalizar(uf) == normalizar(regras["loja"]["uf"]):
        frete, prazo = regras["frete"]["curitiba_pr_centavos"], regras["prazo"]["curitiba_dias_uteis"]
        base["pendencias"].append("Prazo local ainda não definido.")
    else:
        frete, prazo = frete_por_distancia(cidade["distancia_km"], regras)
    if regras["prazo"]["inicio_contagem"] is None:
        base["pendencias"].append("Marco inicial da contagem do prazo pendente; não prometer data de calendário.")
    return {**base, "status": "parcial" if base["pendencias"] else "ok",
            "frete_centavos": frete, "prazo_dias_uteis": prazo}


def calcular_orcamento(catalogo, itens, modalidade: Literal["retirada", "entrega"], municipio=None, uf=None, *, cotacao_entrega=None):
    regras = json.loads((localizar_projeto() / "02_codigo/dados/loja_regras.json").read_text(encoding="utf-8"))
    base = {"itens": [], "subtotal_centavos": None, "frete_centavos": None, "total_centavos": None,
            "prazo_dias_uteis": None, "distancia_km_simulada": None, "pendencias": [],
            "natureza": "orcamento_academico_simulado", "reserva_efetuada": False}
    if modalidade not in ("retirada", "entrega") or not itens:
        return {**base, "status": "entrada_invalida", "pendencias": ["Informe itens e modalidade retirada/entrega."]}
    # AGREGAÇÃO evita contornar saldo ao repetir o mesmo produto em linhas separadas.
    agregados = {}
    for valor in itens:
        item = valor if isinstance(valor, ItemOrcamento) else ItemOrcamento.model_validate(valor)
        consulta = catalogo.consultar(produto_id=item.produto_id)
        if consulta["status"] != "ok":
            return {**base, "status": "produto_nao_encontrado", "pendencias": [f"Produto não encontrado: {item.produto_id}."]}
        produto = consulta["produtos"][0]
        if produto["id"] not in agregados:
            agregados[produto["id"]] = {"produto": produto, "quantidade": 0}
        agregados[produto["id"]]["quantidade"] += item.quantidade
    for registro in agregados.values():
        produto, quantidade = registro["produto"], registro["quantidade"]
        base["itens"].append({"produto_id": produto["id"], "sku": produto["sku"], "quantidade": quantidade,
                              "preco_unitario_centavos": produto["preco_centavos"], "estoque_consultado": produto["estoque"]})
        if quantidade > produto["estoque"]:
            base["pendencias"].append(f"{produto['id']}: solicitado {quantidade}, saldo {produto['estoque']}. Regra de falta/reserva de estoque ainda pendente.")
    if base["pendencias"]:
        return {**base, "status": "pendencia_estoque"}
    # CÁLCULO DETERMINÍSTICO usa somente preços lidos do SQLite, sem alterar o estoque.
    base["subtotal_centavos"] = sum(i["quantidade"] * i["preco_unitario_centavos"] for i in base["itens"])
    if modalidade == "retirada":
        return {**base, "status": "ok", "frete_centavos": regras["frete"]["retirada_centavos"],
                "total_centavos": base["subtotal_centavos"] + regras["frete"]["retirada_centavos"]}
    entrega = cotacao_entrega if cotacao_entrega is not None else consultar_entrega(municipio, uf)
    return {**base, **entrega,
            "total_centavos": (base["subtotal_centavos"] + entrega["frete_centavos"]
                               if entrega["frete_centavos"] is not None else None)}
