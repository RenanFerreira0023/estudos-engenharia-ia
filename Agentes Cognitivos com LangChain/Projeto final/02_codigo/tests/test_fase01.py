import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from langchain_core.exceptions import OutputParserException
from langchain_core.runnables import RunnableLambda
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from auto_super_parts.chain_inicial import criar_chains, processar_mensagem
from auto_super_parts.demonstracao_fase01 import avaliar_casos, carregar_casos, criar_modelo_simulado
from auto_super_parts.prompts import criar_templates
from auto_super_parts.schemas import PedidoIdentificado


class ContratoTest(unittest.TestCase):
    def test_nao_inventa_veiculo_ou_unidade(self):
        pedido = PedidoIdentificado(intencao="consulta_peca", peca="filtro")
        self.assertIsNone(pedido.quantidade)
        self.assertIsNone(pedido.veiculo.motor)
        self.assertIn("peca.tipo", pedido.campos_faltantes)

    def test_pendencias_dependem_da_intencao(self):
        self.assertEqual(PedidoIdentificado(intencao="pagamento").campos_faltantes, [])
        self.assertEqual(PedidoIdentificado(intencao="entrega").campos_faltantes, ["cep"])
        self.assertEqual(PedidoIdentificado(intencao="desconhecida").campos_faltantes, ["intencao"])

    def test_quantidade_obrigatoria_so_no_orcamento(self):
        consulta = PedidoIdentificado(intencao="consulta_peca", peca="P001")
        orcamento = PedidoIdentificado(intencao="orcamento_entrega", peca="P001")
        self.assertEqual(consulta.campos_faltantes, [])
        self.assertEqual(orcamento.campos_faltantes, ["quantidade", "cep"])

    def test_quantidades_invalidas_nao_sao_convertidas(self):
        for valor in (0, -1, 1.5, True, "2"):
            with self.subTest(valor=valor), self.assertRaises(ValidationError):
                PedidoIdentificado(intencao="consulta_peca", quantidade=valor)

    def test_cep_preserva_zero_e_normaliza_hifen(self):
        self.assertEqual(PedidoIdentificado(intencao="entrega", cep="01001-000").cep, "01001000")
        for valor in ("123", "abc01001000", 1001000):
            with self.subTest(valor=valor), self.assertRaises(ValidationError):
                PedidoIdentificado(intencao="entrega", cep=valor)

    def test_recalcula_lista_alegada_pelo_modelo(self):
        pedido = PedidoIdentificado(intencao="pagamento", campos_faltantes=["veiculo.motor", "cep"])
        self.assertEqual(pedido.campos_faltantes, [])

    def test_veiculo_null_normaliza_sem_inventar(self):
        pedido = PedidoIdentificado(intencao="pagamento", veiculo=None)
        self.assertTrue(all(v is None for v in pedido.veiculo.model_dump().values()))
        with self.assertRaises(ValidationError):
            PedidoIdentificado(intencao="consulta_peca", veiculo="Gol")

    def test_rejeita_preco_e_compativel_adicionados(self):
        with self.assertRaises(ValidationError):
            PedidoIdentificado(intencao="consulta_peca", preco=10, compativel=True)


class ComposicaoTest(unittest.TestCase):
    def test_execucao_direta_fora_do_projeto_sem_pythonpath(self):
        arquivo = Path(__file__).resolve().parents[1] / "src/auto_super_parts/chain_inicial.py"
        ambiente = dict(os.environ)
        ambiente.pop("PYTHONPATH", None)
        processo = subprocess.run(
            [sys.executable, str(arquivo), "--help"], cwd=tempfile.gettempdir(),
            env=ambiente, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(processo.returncode, 0, processo.stderr)
        self.assertIn("--mensagem", processo.stdout)

    def test_templates_e_composicoes_mesmo_contrato(self):
        caso = carregar_casos()[0]
        for template in ("chat", "texto"):
            modelo = criar_modelo_simulado([caso["saida_simulada"]] * 2)
            fluxos = criar_chains(modelo=modelo, template=template)
            entrada = {"mensagem": caso["mensagem"]}
            a, b = fluxos.lcel.invoke(entrada), fluxos.decorada.invoke(entrada)
            self.assertEqual(a, b)
            self.assertEqual(a.quantidade, 2)
            self.assertIsNone(a.veiculo.combustivel)
            self.assertEqual(a.veiculo.motor, "1.0")

    def test_formato_e_instrucoes_no_prompt(self):
        texto, chat, parser = criar_templates()
        self.assertIn("campos_faltantes", texto.invoke({"mensagem": "oi"}).to_string())
        self.assertEqual([m.type for m in chat.invoke({"mensagem": "oi"}).to_messages()], ["system", "human"])
        self.assertEqual(parser.pydantic_object, PedidoIdentificado)

    def test_json_invalido_e_falha_sem_repeticao(self):
        chamadas = []
        def responder(entrada):
            chamadas.append(entrada)
            return "isto não é JSON"
        fluxos = criar_chains(modelo=RunnableLambda(responder))
        resultado = processar_mensagem(fluxos.lcel, "Quero velas.")
        self.assertEqual(resultado.status, "erro_validacao")
        self.assertIsNone(resultado.dados)
        self.assertEqual(len(chamadas), 1)

    def test_parser_rejeita_zero(self):
        parser = criar_templates()[2]
        with self.assertRaises(OutputParserException):
            parser.invoke(json.dumps({"intencao": "consulta_peca", "quantidade": 0}))

    def test_entrada_vazia_nao_chama_modelo(self):
        def nao_chamar(entrada):
            raise AssertionError("Não deveria executar")
        self.assertEqual(processar_mensagem(RunnableLambda(nao_chamar), "  ").status, "erro_entrada")

    def test_falha_modelo_nao_vira_dado(self):
        def indisponivel(entrada):
            raise ConnectionError("mensagem interna que não deve aparecer")
        resultado = processar_mensagem(RunnableLambda(indisponivel), "Oi")
        self.assertEqual(resultado.status, "erro_modelo")
        self.assertIsNone(resultado.dados)
        self.assertNotIn("mensagem interna", resultado.model_dump_json())

    def test_batch_simulado_nove_casos(self):
        resultados = avaliar_casos("simulado")
        self.assertEqual(len(resultados), 9)
        self.assertTrue(all(r["passou"] for r in resultados), resultados)
        self.assertEqual(json.loads(resultados[3]["saida_modelo_nao_validada"])["quantidade"], 0)


if __name__ == "__main__":
    unittest.main()
