"""Falhas da API não derrubam o terminal nem confirmam visitas."""
import io
import tempfile
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))


class ErroAgenteTest(unittest.TestCase):
    def test_chave_expirada_mostra_orientacao(self):
        from openai import AuthenticationError
        from secretaria.cli import conversar_sobre_visita
        from secretaria.banco import Banco, Contexto
        resposta = Mock(status_code=401)
        agente = Mock()
        agente.invoke.side_effect = AuthenticationError('expirada', response=resposta, body={})
        saida = io.StringIO()
        with tempfile.TemporaryDirectory() as pasta:
            with Banco(Path(pasta)/'agente.sqlite3') as banco:
                banco.preparar_demo()
                with patch('secretaria.agente_agenda.criar_agente_agenda',return_value=agente), \
                     patch('builtins.input',return_value='Agende uma visita'), redirect_stdout(saida):
                    conversar_sobre_visita(banco,Contexto('demo','bruno'))
        self.assertIn('chave OPENAI_API_KEY foi recusada ou expirou',saida.getvalue())
        self.assertNotIn('Traceback',saida.getvalue())


if __name__ == '__main__':
    unittest.main()
