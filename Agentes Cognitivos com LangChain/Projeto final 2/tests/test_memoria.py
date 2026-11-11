"""Prova local de persistência, janela e separação entre usuários/conversas."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from secretaria.banco import Banco, Contexto
from secretaria.memoria import MemoriaConversas


class TestMemoriaConversas(unittest.TestCase):
    def test_reabrir_janela_e_isolamento(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'teste.sqlite3'
            ana, bruno = Contexto('demo', 'ana'), Contexto('demo', 'bruno')
            with Banco(caminho) as banco:
                banco.preparar_demo()
                memoria = MemoriaConversas(banco)
                sessao = memoria.iniciar(ana)
                memoria.registrar(ana, sessao, 'Cliente Alfa', 'Encontrei Alfa Serviços.')
                memoria.registrar(ana, sessao, 'Quando?', 'A visita é às 14h.')
                memoria.registrar(ana, sessao, 'Qual endereço?', 'Ainda não informado.')
                self.assertEqual(len(memoria.mensagens(ana, sessao, 2)), 4)
                self.assertEqual(memoria.mensagens(ana, sessao, 2)[0]['content'], 'Quando?')
                with self.assertRaises(PermissionError):
                    memoria.mensagens(bruno, sessao)
            with Banco(caminho) as banco:
                memoria = MemoriaConversas(banco)
                self.assertEqual(memoria.ultima_ativa(ana), sessao)
                self.assertIsNone(memoria.ultima_ativa(bruno))
                self.assertEqual(len(memoria.ultimos(ana, sessao)), 3)
                memoria.encerrar(ana, sessao)
                nova = memoria.iniciar(ana)
                self.assertEqual(memoria.ultimos(ana, nova), [])
                self.assertEqual(len(memoria.ultimos(ana, sessao)), 3)
                with self.assertRaises(ValueError):
                    memoria.registrar(ana, sessao, 'Nova pergunta', 'Resposta')

    def test_terminal_repassa_historico_sem_duplicar(self):
        from langchain_core.messages import AIMessage
        from secretaria.cli import conversar_sobre_visita

        class AgenteLocal:
            def __init__(self):
                self.entradas = []

            def invoke(self, dados, _config):
                self.entradas.append(dados['messages'])
                return {'messages': dados['messages'] + [AIMessage(content='Resposta local')]}

        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'chat.sqlite3'
            agente = AgenteLocal()
            with Banco(caminho) as banco:
                banco.preparar_demo()
                with patch('secretaria.agente_agenda.criar_agente_agenda', return_value=agente), \
                     patch('builtins.input', side_effect=['Primeira pergunta', '/voltar']):
                    conversar_sobre_visita(banco, Contexto('demo', 'ana'))
            with Banco(caminho) as banco:
                with patch('secretaria.agente_agenda.criar_agente_agenda', return_value=agente), \
                     patch('builtins.input', side_effect=['Segunda pergunta', '/voltar']):
                    conversar_sobre_visita(banco, Contexto('demo', 'ana'))
                memoria = MemoriaConversas(banco)
                sessao = memoria.ultima_ativa(Contexto('demo', 'ana'))
                self.assertEqual(len(memoria.ultimos(Contexto('demo', 'ana'), sessao)), 2)
                self.assertEqual(agente.entradas[1][0]['content'], 'Primeira pergunta')
                self.assertEqual(agente.entradas[1][1]['content'], 'Resposta local')

    def test_ctrl_c_preserva_conversa_sem_traceback(self):
        from secretaria.cli import conversar_sobre_visita
        with tempfile.TemporaryDirectory() as pasta:
            with Banco(Path(pasta) / 'chat.sqlite3') as banco:
                banco.preparar_demo()
                with patch('secretaria.agente_agenda.criar_agente_agenda'), \
                     patch('builtins.input', side_effect=KeyboardInterrupt):
                    conversar_sobre_visita(banco, Contexto('demo', 'ana'))
                self.assertIsNotNone(MemoriaConversas(banco).ultima_ativa(Contexto('demo', 'ana')))


if __name__ == '__main__':
    unittest.main()
