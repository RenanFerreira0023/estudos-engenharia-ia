"""Verificações locais da fase 2; não chama OpenAI nem ViaCEP real."""
import io
import json
import sqlite3
import sys
import unittest
import httpx
from pathlib import Path
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from auto_super_parts.agente_fase02 import AtendimentoFase02, criar_ferramentas, registrar_execucao
from auto_super_parts.catalogo_fase02 import Catalogo
from auto_super_parts.configuracao import localizar_projeto
from auto_super_parts.orcamento_fase02 import ItemOrcamento, calcular_orcamento, frete_por_distancia
from auto_super_parts.viacep import ClienteViaCEP, criar_cliente_dummy


# MODELO ROTEIRIZADO verifica a execução das ferramentas, sem avaliar compreensão de linguagem natural.
class ModeloRoteirizado(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


class CatalogoOrcamentoTest(unittest.TestCase):
    def setUp(self):
        self.catalogo = Catalogo()
        self.addCleanup(self.catalogo.fechar)

    def test_importa_todos_os_registros(self):
        for tabela, quantidade in [("veiculos", 4), ("produtos", 24), ("aplicacoes", 24)]:
            self.assertEqual(len(self.catalogo.ler(f"SELECT id FROM {tabela}")), quantidade)

    def test_consulta_aplicacao_preserva_limite(self):
        consulta = self.catalogo.consultar(veiculo_id="V001", categoria="vela")
        self.assertEqual(consulta["produtos"][0]["id"], "P003")
        self.assertFalse(consulta["aplicacoes"][0]["validada_para_uso_real"])
        self.assertTrue(consulta["sql_executado"])

    def test_zero_estoque_nao_e_inexistente(self):
        self.assertEqual(self.catalogo.consultar(produto_id="P023")["produtos"][0]["estoque"], 0)
        self.assertEqual(self.catalogo.consultar(produto_id="ABC-99")["status"], "produto_nao_encontrado")

    def test_sql_parametrizado_e_banco_sem_escrita(self):
        self.assertEqual(self.catalogo.consultar(produto_id="P003' OR 1=1 --")["produtos"], [])
        with self.assertRaises(sqlite3.DatabaseError):
            self.catalogo.ler("DELETE FROM produtos")
        self.assertEqual(len(self.catalogo.ler("SELECT id FROM produtos")), 24)

    def test_total_independente_e_estoque_preservado(self):
        r = calcular_orcamento(self.catalogo, [{"produto_id": "P003", "quantidade": 2}], "retirada")
        self.assertEqual(r["total_centavos"], 2 * 1850)
        self.assertFalse(r["reserva_efetuada"])
        self.assertEqual(self.catalogo.consultar(produto_id="P003")["produtos"][0]["estoque"], 16)

    def test_quantidade_invalida_e_preco_externo(self):
        for quantidade in [0, -1, 1.5, True, "2"]:
            with self.subTest(quantidade=quantidade), self.assertRaises(ValidationError):
                ItemOrcamento(produto_id="P003", quantidade=quantidade)
        with self.assertRaises(ValidationError):
            ItemOrcamento(produto_id="P003", quantidade=2, preco_centavos=1)

    def test_duplicatas_nao_contornam_estoque(self):
        r = calcular_orcamento(self.catalogo, [{"produto_id": "P003", "quantidade": 9},
                                               {"produto_id": "CWB-SIM-P003", "quantidade": 8}], "retirada")
        self.assertEqual(r["status"], "pendencia_estoque")
        self.assertIsNone(r["total_centavos"])

    def test_cidade_desconhecida_nao_tem_total(self):
        r = calcular_orcamento(self.catalogo, [{"produto_id": "P003", "quantidade": 2}], "entrega", "São Paulo", "SP")
        self.assertEqual(r["subtotal_centavos"], 3700)
        self.assertIsNone(r["frete_centavos"])
        self.assertIsNone(r["total_centavos"])

    def test_curitiba_prazo_pendente_e_uf_obrigatoria(self):
        itens = [{"produto_id": "P003", "quantidade": 2}]
        r = calcular_orcamento(self.catalogo, itens, "entrega", "CURITIBA", "pr")
        self.assertEqual(r["frete_centavos"], 0)
        self.assertIsNone(r["prazo_dias_uteis"])
        self.assertTrue(r["pendencias"])
        self.assertIsNone(calcular_orcamento(self.catalogo, itens, "entrega", "Curitiba", "SP")["total_centavos"])

    def test_arredondamento_e_faixas_de_frete(self):
        regras = json.loads((localizar_projeto() / "02_codigo/dados/loja_regras.json").read_text(encoding="utf-8"))
        for distancia, esperado in [(100, (443, 2)), (101, (447, 4)), (150, (664, 4)), (200, (885, 4)), (201, (889, 6))]:
            with self.subTest(distancia=distancia):
                self.assertEqual(frete_por_distancia(distancia, regras), esperado)


class ViaCEPTest(unittest.TestCase):
    def test_invalido_nao_chama_rede(self):
        def transporte(*args):
            self.fail("CEP inválido acionou transporte")
        self.assertEqual(ClienteViaCEP(transporte).consultar("123")["status"], "cep_invalido")

    def test_dummy_explicitamente_identificado(self):
        r = criar_cliente_dummy().consultar("01001-000")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["cep"], "01001000")
        self.assertEqual(r["origem"], "transporte_injetado_teste")
        self.assertFalse(r["tentativa_http_real"])
        self.assertEqual(criar_cliente_dummy().consultar("99999999")["status"], "cep_nao_encontrado")

    def test_erros_nao_viram_endereco(self):
        for corpo, esperado in [("[]", "resposta_invalida"), ("não JSON", "resposta_invalida"), ('{"erro":true}', "cep_nao_encontrado")]:
            with self.subTest(corpo=corpo):
                self.assertEqual(ClienteViaCEP(lambda *args: (200, corpo)).consultar("01001000")["status"], esperado)
        for erro, esperado in [(TimeoutError(), "timeout"), (URLError("simulado"), "indisponivel")]:
            def falhar(*args):
                raise erro
            r = ClienteViaCEP(falhar).consultar("01001000")
            self.assertEqual(r["status"], esperado)
            self.assertIsNone(r["endereco"])


class AgenteTest(unittest.TestCase):
    def test_regressao_schema_no_pedido_http_real_do_sdk(self):
        pedidos = []

        # MOCK HTTP observa o JSON serializado pelo SDK, sem rede nem compreensão pela LLM.
        def responder(request):
            pedido = json.loads(request.content)
            pedidos.append(pedido)
            resposta = {"id": "chatcmpl-teste", "object": "chat.completion", "created": 0,
                        "model": "gpt-4o-mini", "choices": [{"index": 0,
                        "finish_reason": "stop", "message": {"role": "assistant", "content": "Teste de transporte."}}]}
            return httpx.Response(200, json=resposta)

        with httpx.Client(transport=httpx.MockTransport(responder)) as cliente:
            modelo = ChatOpenAI(model="gpt-4o-mini", api_key="chave-ficticia-teste", http_client=cliente, max_retries=0)
            sistema = AtendimentoFase02(modelo=modelo, cliente_cep=criar_cliente_dummy())
            self.addCleanup(sistema.fechar)
            resultado = sistema.atender("Teste do esquema enviado", salvar=False)
        self.assertEqual(resultado["status"], "ok")
        self.assertFalse(pedidos[0]["parallel_tool_calls"])
        funcoes = [t["function"] for t in pedidos[0]["tools"]]
        for funcao in funcoes:
            self.assertTrue(funcao["strict"])
            esquema = funcao["parameters"]
            self.assertIs(esquema["additionalProperties"], False)
            self.assertEqual(set(esquema.get("required", [])), set(esquema.get("properties", {})))
        esquema = next(f["parameters"] for f in funcoes if f["name"] == "calcular_orcamento")
        self.assertNotIn("minItems", esquema["properties"])
        self.assertEqual(esquema["properties"]["itens"]["minItems"], 1)
        self.assertIs(esquema["properties"]["itens"]["items"]["additionalProperties"], False)
        self.assertTrue(resultado["esquemas_modelo"])

    def test_regressao_rejeita_argumentos_da_falha_preservada(self):
        falha = localizar_projeto() / "04_avaliacao_e_evidencias/resultados/fase02_20261102T195701244602Z.json"
        registro = json.loads(falha.read_text(encoding="utf-8"))
        argumentos = next(c["args"] for m in registro["trajetoria"] for c in m.get("tool_calls", [])
                          if c["name"] == "calcular_orcamento")
        self.assertEqual(argumentos["minItems"], 1)
        catalogo = Catalogo()
        self.addCleanup(catalogo.fechar)
        ferramenta = next(t for t in criar_ferramentas(catalogo, criar_cliente_dummy()) if t.name == "calcular_orcamento")
        self.assertEqual(json.loads(ferramenta.invoke(argumentos))["status"], "entrada_invalida")
        corrigidos = {k: v for k, v in argumentos.items() if k != "minItems"}
        retorno = ferramenta.invoke(corrigidos)
        self.assertEqual(retorno["status"], "cotacao_entrega_pendente")
        self.assertIsNone(retorno["frete_centavos"])
        self.assertIsNone(retorno["prazo_dias_uteis"])

    def test_lista_vazia_continua_invalida(self):
        from auto_super_parts.agente_fase02 import EntradaOrcamento
        with self.assertRaises(ValidationError):
            EntradaOrcamento(itens=[], modalidade="retirada")

    def test_ciclo_real_de_ferramenta_com_modelo_roteirizado(self):
        modelo = ModeloRoteirizado(responses=[
            AIMessage(content="", tool_calls=[{"name": "calcular_orcamento", "args": {
                "itens": [{"produto_id": "P003", "quantidade": 2}], "modalidade": "retirada"}, "id": "teste_1"}]),
            AIMessage(content="Resposta roteirizada de teste, sem geração real.")])
        sistema = AtendimentoFase02(modelo=modelo, cliente_cep=criar_cliente_dummy())
        self.addCleanup(sistema.fechar)
        r = sistema.atender("Mensagem de teste", salvar=False)
        self.assertEqual(r["status"], "ok")
        retorno = next(i for i in r["trajetoria"] if i["tipo"] == "tool")
        self.assertEqual(json.loads(retorno["conteudo"])["total_centavos"], 3700)
        self.assertTrue(r["eventos_ferramentas"])

    def test_tool_rejeita_quantidade_zero(self):
        catalogo = Catalogo()
        self.addCleanup(catalogo.fechar)
        ferramenta = next(t for t in criar_ferramentas(catalogo, criar_cliente_dummy()) if t.name == "calcular_orcamento")
        r = ferramenta.invoke({"itens": [{"produto_id": "P003", "quantidade": 0}], "modalidade": "retirada"})
        self.assertEqual(json.loads(r)["status"], "entrada_invalida")


def main():
    # EVIDÊNCIAS separam a execução offline da avaliação do agente com modelo e API reais.
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    log = io.StringIO()
    resultado = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    print(log.getvalue())
    arquivo = registrar_execucao({"fase": 2, "modo": "offline; modelo roteirizado e transporte injetado",
                                 "executados": resultado.testsRun, "falhas": len(resultado.failures),
                                 "erros": len(resultado.errors), "log": log.getvalue()}, "fase02_verificacoes_locais")
    print("Evidência:", arquivo.name)
    raise SystemExit(0 if resultado.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
