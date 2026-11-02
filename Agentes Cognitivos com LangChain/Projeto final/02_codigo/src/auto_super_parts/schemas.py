import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator


# LITERAL define o vocabulário proposto da fase 1; nenhuma intenção executa uma ação.
Intencao = Literal["consulta_peca", "orcamento", "orcamento_entrega", "entrega", "pagamento", "politica", "desconhecida"]
Campo = Literal["veiculo.modelo", "veiculo.ano_modelo", "veiculo.motor", "veiculo.combustivel", "peca", "peca.tipo", "quantidade", "cep", "intencao"]
Texto = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]


# BASEMODEL e FIELD validam estrutura, tipos e restrições; não comprovam que a LLM foi fiel.
class EntradaMensagem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    mensagem: str = Field(strict=True, min_length=1, max_length=4000)


class VeiculoIdentificado(BaseModel):
    model_config = ConfigDict(extra="forbid")
    modelo: Texto | None = Field(default=None, description="Modelo explicitamente informado; não acrescentar fabricante ou versão.")
    ano_modelo: int | None = Field(default=None, strict=True, ge=1000, le=9999, description="Ano informado com quatro dígitos, sem deduzir por geração.")
    motor: Texto | None = Field(default=None, description="Motorização como informada; 1.0 não autoriza acrescentar 8V, Fire ou outra versão.")
    combustivel: Texto | None = Field(default=None, description="Combustível explicitamente escrito, inclusive flex. Se a mensagem diz flex, registre flex; null só se não informado. Não inferir pelo modelo/ano.")


class PedidoIdentificado(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intencao: Intencao = Field(description="Finalidade principal da mensagem, incluindo desconhecida quando não identificável.")
    veiculo: VeiculoIdentificado = Field(default_factory=VeiculoIdentificado)
    peca: Texto | None = Field(default=None, description="Peça solicitada, em singular quando inequívoco, ou código informado. Não consultar catálogo.")
    quantidade: int | None = Field(default=None, strict=True, gt=0, description="Inteiro positivo explicitamente informado; não assumir uma unidade.")
    cep: str | None = Field(default=None, strict=True, pattern=r"^[0-9]{8}$", description="Oito dígitos como string; preservar zeros iniciais. Não consultar endereço.")
    campos_faltantes: list[Campo] = Field(default_factory=list, description="Dados necessários à intenção; o Python recalcula esta lista.")

    # NORMALIZAÇÃO DE AUSÊNCIA preserva o contrato veiculo={campos:null}, sem preencher nenhum fato.
    @field_validator("veiculo", mode="before")
    @classmethod
    def normalizar_veiculo_ausente(cls, valor):
        return {} if valor is None else valor

    # FIELD_VALIDATOR normaliza só um formato conhecido; letras e tamanhos inválidos não são apagados.
    @field_validator("cep", mode="before")
    @classmethod
    def normalizar_cep(cls, valor):
        if isinstance(valor, str) and re.fullmatch(r"[0-9]{5}-[0-9]{3}", valor.strip()):
            return valor.strip().replace("-", "")
        return valor

    # ESTADO DERIVADO calcula pendências no Python, evitando confiar na completude alegada pela LLM.
    # Estas regras são propostas para coleta inicial; não validam compatibilidade mecânica.
    @model_validator(mode="after")
    def calcular_campos_faltantes(self):
        faltantes = []
        if self.intencao in ("consulta_peca", "orcamento", "orcamento_entrega"):
            codigo_explicito = self.peca is not None and re.fullmatch(r"(?:CWB-SIM-)?P[0-9]{3}", self.peca, re.IGNORECASE)
            if not codigo_explicito:
                for campo in ("modelo", "ano_modelo", "motor", "combustivel"):
                    if getattr(self.veiculo, campo) is None:
                        faltantes.append(f"veiculo.{campo}")
            if self.peca is None:
                faltantes.append("peca")
            elif self.peca.casefold() in ("filtro", "filtros", "correia", "correias"):
                faltantes.append("peca.tipo")
            if self.intencao in ("orcamento", "orcamento_entrega") and self.quantidade is None:
                faltantes.append("quantidade")
        if self.intencao in ("entrega", "orcamento_entrega") and self.cep is None:
            faltantes.append("cep")
        if self.intencao == "desconhecida":
            faltantes.append("intencao")
        self.campos_faltantes = faltantes
        return self


# ENVELOPE distingue dados validados de falhas: JSON inválido não é exposto como sucesso.
class ResultadoProcessamento(BaseModel):
    status: Literal["ok", "erro_entrada", "erro_validacao", "erro_modelo"]
    dados: PedidoIdentificado | None = None
    erros: list[str] = Field(default_factory=list)
