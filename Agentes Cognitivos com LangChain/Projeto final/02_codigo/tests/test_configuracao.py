import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from auto_super_parts.configuracao import ErroConfiguracao, localizar_projeto, obter_chave_api


class ConfiguracaoTest(unittest.TestCase):
    def test_variavel_de_ambiente_tem_prioridade_sem_ler_arquivo(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "valor-ficticio-do-ambiente"}, clear=True):
            with patch("auto_super_parts.configuracao.localizar_projeto", side_effect=AssertionError("Não deveria procurar arquivo")):
                self.assertEqual(obter_chave_api(), "valor-ficticio-do-ambiente")

    def test_env_local_sem_modificar_ambiente(self):
        with tempfile.TemporaryDirectory() as pasta, patch.dict(os.environ, {}, clear=True):
            projeto = Path(pasta)
            (projeto / ".env").write_text("OPENAI_API_KEY=valor-ficticio-local\n", encoding="utf-8")
            with patch("auto_super_parts.configuracao.localizar_projeto", return_value=projeto):
                self.assertEqual(obter_chave_api(), "valor-ficticio-local")
            self.assertNotIn("OPENAI_API_KEY", os.environ)

    def test_nao_procura_env_fora_do_projeto(self):
        with tempfile.TemporaryDirectory() as pasta, patch.dict(os.environ, {}, clear=True):
            pai = Path(pasta)
            (pai / ".env").write_text("OPENAI_API_KEY=nao-deve-ser-lido\n", encoding="utf-8")
            projeto = pai / "copia-renomeada"
            projeto.mkdir()
            with patch("auto_super_parts.configuracao.localizar_projeto", return_value=projeto):
                with self.assertRaises(ErroConfiguracao):
                    obter_chave_api()

    def test_variavel_vazia_nao_dispara_fallback(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": " "}, clear=True):
            with patch("auto_super_parts.configuracao.localizar_projeto", side_effect=AssertionError("Não deveria ler arquivo")):
                with self.assertRaises(ErroConfiguracao):
                    obter_chave_api()

    def test_arquivo_explicitado_relativo_ao_projeto(self):
        with tempfile.TemporaryDirectory() as pasta, patch.dict(os.environ, {}, clear=True):
            projeto = Path(pasta)
            (projeto / "alternativo.env").write_text("OPENAI_API_KEY=valor-ficticio-alternativo\n", encoding="utf-8")
            with patch("auto_super_parts.configuracao.localizar_projeto", return_value=projeto):
                self.assertEqual(obter_chave_api("alternativo.env"), "valor-ficticio-alternativo")

    def test_localizacao_por_marcador_em_projeto_renomeado(self):
        with tempfile.TemporaryDirectory() as pasta:
            projeto = Path(pasta) / "outro-nome"
            origem = projeto / "02_codigo/src/auto_super_parts/configuracao.py"
            origem.parent.mkdir(parents=True)
            origem.touch()
            (projeto / "INSTRUCOES_PARA_IA_PROGRAMADORA.md").touch()
            self.assertEqual(localizar_projeto(origem), projeto.resolve())

    def test_sem_marcador_falha_claramente(self):
        with tempfile.TemporaryDirectory() as pasta:
            with self.assertRaises(ErroConfiguracao):
                localizar_projeto(pasta)


if __name__ == "__main__":
    unittest.main()
