"""Regressões das falhas reais registradas em 08/11; modelos locais sem API."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from auto_super_parts.agente_fase02 import AtendimentoFase02
from auto_super_parts.catalogo_fase02 import Catalogo
from auto_super_parts.configuracao import localizar_projeto
from auto_super_parts.consultas_complementares import consultar_tecnica, pede_especificacao_oleo
from auto_super_parts.orcamento_fase02 import calcular_orcamento, consultar_entrega
from auto_super_parts.viacep import criar_cliente_dummy


class ModeloRoteirizado(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


class CorrecoesFase02Test(unittest.TestCase):
    def criar(self, respostas):
        sistema = AtendimentoFase02(modelo=ModeloRoteirizado(responses=respostas), cliente_cep=criar_cliente_dummy())
        self.addCleanup(sistema.fechar)
        return sistema

    def test_frete_sem_produtos_e_sem_distancia(self):
        r = consultar_entrega("São Paulo", "SP")
        self.assertIsNone(r["frete_centavos"])
        self.assertIsNone(r["prazo_dias_uteis"])
        self.assertEqual(r["status"], "cotacao_entrega_pendente")

    def test_mesma_regra_frete_isolado_e_orcamento(self):
        catalogo = Catalogo()
        self.addCleanup(catalogo.fechar)
        for cidade, esperado in [("Ponta Grossa", 531), ("Guarapuava", 1106), ("Curitiba", 0)]:
            entrega = consultar_entrega(cidade, "PR")
            orcamento = calcular_orcamento(catalogo, [{"produto_id": "P003", "quantidade": 2}], "entrega", cidade, "PR")
            self.assertEqual(entrega["frete_centavos"], esperado)
            self.assertEqual(orcamento["frete_centavos"], entrega["frete_centavos"])
            self.assertEqual(orcamento["total_centavos"], 3700 + esperado)

    def test_destino_incompleto_nao_vira_frete_zero(self):
        self.assertIsNone(consultar_entrega("Curitiba", None)["frete_centavos"])
        self.assertIsNone(consultar_entrega("Curitiba", "SC")["frete_centavos"])

    def test_oleo_pendente_nao_tem_especificacoes(self):
        r = consultar_tecnica("V004", "oleo")
        self.assertEqual(r["status"], "informacao_pendente")
        self.assertEqual(r["fontes"], [])
        self.assertEqual(consultar_tecnica("V999", "oleo")["status"], "veiculo_nao_encontrado")

    def test_compra_por_volume_nao_e_pedido_de_especificacao(self):
        self.assertFalse(pede_especificacao_oleo("Quero 1 litro de óleo P024 para retirada."))
        self.assertTrue(pede_especificacao_oleo("Qual viscosidade de óleo e quantos litros vão no motor?"))

    def test_sincronismo_preserva_fonte_e_limites(self):
        r = consultar_tecnica("V004", "sincronismo")
        self.assertEqual(r["status"], "informacao_disponivel")
        self.assertEqual(r["fontes"][0]["id"], "SRC02")
        self.assertTrue(r["fontes"][0]["limite"])

    def test_resposta_original_oleo_sem_ferramenta_e_bloqueada(self):
        arquivo = localizar_projeto() / "04_avaliacao_e_evidencias/resultados/fase02_20261108T205000772452Z.json"
        anterior = json.loads(arquivo.read_text(encoding="utf-8"))
        sistema = self.criar([AIMessage(content=anterior["resposta"])])
        r = sistema.atender(anterior["mensagem"], salvar=False)
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["resposta_candidata"], anterior["resposta"])
        self.assertNotIn("20W50", r["resposta"])
        self.assertNotIn("3,5", r["resposta"])
        self.assertTrue(r["verificacao_especifica"]["substituida"])
        self.assertFalse(r["verificacao_especifica"]["consulta_tecnica_executada"])

    def test_troca_original_de_categoria_e_bloqueada(self):
        arquivo = localizar_projeto() / "04_avaliacao_e_evidencias/resultados/fase02_20261108T204903908930Z.json"
        anterior = json.loads(arquivo.read_text(encoding="utf-8"))
        chamada = next(c for m in anterior["trajetoria"] for c in m.get("tool_calls", []) if c["name"] == "consultar_catalogo")
        sistema = self.criar([AIMessage(content="", tool_calls=[{**chamada, "id": "replay"}]),
                              AIMessage(content="Resposta inadequada de teste.")])
        r = sistema.atender(anterior["mensagem"], salvar=False)
        retorno = json.loads(next(m["conteudo"] for m in r["trajetoria"] if m["tipo"] == "tool"))
        self.assertEqual(retorno["status"], "tipo_peca_divergente")
        self.assertEqual(retorno["produtos"], [])
        self.assertIn("Não vou substituí-la", r["resposta"])
        self.assertEqual(sistema.pedido_atual.get(), "")

    def test_info_sincronismo_consumida_no_atendimento(self):
        sistema = self.criar([
            AIMessage(content="", tool_calls=[{"name": "consultar_informacao_tecnica",
                      "args": {"veiculo_id": "V004", "assunto": "sincronismo"}, "id": "tecnica"}]),
            AIMessage(content="Não vou oferecer outra peça.")])
        r = sistema.atender("Tenho um Fusca 1982 1600 a ar, gasolina. Quero uma correia dentada.", salvar=False)
        self.assertIn("engrenagens", r["resposta"])
        self.assertTrue(r["verificacao_especifica"]["consulta_tecnica_executada"])

    def test_nao_calcula_outra_correia_se_pular_consulta(self):
        sistema = self.criar([
            AIMessage(content="", tool_calls=[{"name": "calcular_orcamento", "args": {
                "itens": [{"produto_id": "P023", "quantidade": 1}],
                "modalidade": "retirada", "municipio": None, "uf": None}, "id": "pular"}]),
            AIMessage(content="Resposta roteirizada.")])
        r = sistema.atender("Quero uma correia dentada para o Fusca 1982.", salvar=False)
        retorno = json.loads(next(m["conteudo"] for m in r["trajetoria"] if m["tipo"] == "tool"))
        self.assertEqual(retorno["status"], "tipo_peca_divergente")
        self.assertNotIn("total_centavos", retorno)

    def test_saudacao_nao_exige_fonte_tecnica(self):
        sistema = self.criar([AIMessage(content="Olá! Como posso ajudar?")])
        r = sistema.atender("Olá", salvar=False)
        self.assertEqual(r["resposta"], "Olá! Como posso ajudar?")
        self.assertFalse(r["verificacao_especifica"]["substituida"])


if __name__ == "__main__":
    unittest.main()
