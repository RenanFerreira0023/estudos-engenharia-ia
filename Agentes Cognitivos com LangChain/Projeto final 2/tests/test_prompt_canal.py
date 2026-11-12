"""O prompt indica a confirmação que existe no canal em uso (terminal ou Streamlit).

Regressão de falha real: no Streamlit, o agente sugeriu `/confirmar-visita 1`, comando que não
existe; o prompt só descrevia os comandos do terminal.
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from secretaria.agente_agenda import montar_prompt_agenda


class PromptPorCanalTest(unittest.TestCase):
    def test_web_aponta_botoes_e_nao_comandos(self):
        prompt = montar_prompt_agenda('ana', canal='web')
        self.assertIn('Confirmar visita no banco', prompt)
        self.assertIn('Confirmar cadastro PJ proposto', prompt)
        self.assertIn('Preparar índice de fontes', prompt)
        self.assertNotIn('/confirmar', prompt)
        self.assertNotIn('opção 11', prompt)
        self.assertIn('não invente comandos', prompt)

    def test_terminal_mantem_comandos_existentes(self):
        prompt = montar_prompt_agenda('ana')
        self.assertIn('/confirmar ID', prompt)
        self.assertIn('/confirmar-cliente ID', prompt)
        self.assertIn('opção 11', prompt)
        self.assertNotIn('aba Agenda', prompt)

    def test_canal_desconhecido_falha(self):
        with self.assertRaises(ValueError):
            montar_prompt_agenda('ana', canal='whatsapp')

    def test_prompt_pede_proposta_sem_oferta_quando_dados_completos(self):
        for canal in ('terminal', 'web'):
            self.assertIn('chame propor_visita no mesmo turno', montar_prompt_agenda('ana', canal))

    def test_atendimento_web_cria_agente_no_canal_web(self):
        import tempfile
        from langchain_core.messages import AIMessage
        from secretaria.banco import Banco, Contexto
        from secretaria.atendimento_web import responder_turno

        class AgenteLocal:
            def invoke(self, dados, config=None):
                return {'messages': dados['messages'] + [AIMessage(content='Olá.')]}

        with tempfile.TemporaryDirectory() as pasta:
            with Banco(Path(pasta) / 'web.sqlite3') as banco:
                banco.preparar_demo()
                from secretaria.memoria import MemoriaConversas
                ctx = Contexto('demo', 'ana')
                sessao = MemoriaConversas(banco).iniciar(ctx)
                with patch('secretaria.atendimento_web.criar_agente_agenda',
                           return_value=AgenteLocal()) as criar, \
                     patch('secretaria.atendimento_web.verificar_e_reparar',
                           side_effect=lambda pergunta, texto, *a, **k: (texto, {'estado': 'local'})):
                    responder_turno(banco, ctx, sessao, 'Olá')
                self.assertEqual(criar.call_args.kwargs.get('canal'), 'web')


if __name__ == '__main__':
    unittest.main()
