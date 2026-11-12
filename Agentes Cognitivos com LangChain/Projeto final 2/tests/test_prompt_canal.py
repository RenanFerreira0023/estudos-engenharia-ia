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

    def test_orientacao_de_confirmacao_vem_do_retorno_da_ferramenta(self):
        # Regressão: com "Verificação: corrigida", a reescrita perdeu a indicação do botão.
        import json
        from langchain_core.messages import ToolMessage
        from secretaria.atendimento_web import orientacao_confirmacao

        visita = ToolMessage(name='propor_visita', tool_call_id='1', content=json.dumps(
            {'proposta_id': 3, 'estado': 'pendente', 'reutilizada': True,
             'expira_em': '2026-11-11T23:33:11-03:00'}))
        cliente = ToolMessage(name='propor_cadastro_cliente', tool_call_id='2', content=json.dumps(
            {'proposta_id': 1, 'estado': 'pendente'}))
        erro = ToolMessage(name='propor_visita', tool_call_id='3', content=json.dumps(
            {'status': 'dados_invalidos', 'mensagem': 'x'}))
        texto = orientacao_confirmacao([visita, cliente, erro])
        self.assertIn('"Confirmar visita no banco", ID 3 até 11/11/2026 23:33', texto)
        self.assertIn('já existia', texto)
        self.assertIn('"Confirmar cadastro PJ proposto", ID 1', texto)
        self.assertNotIn('/confirmar', texto)
        self.assertEqual(orientacao_confirmacao([erro]), '')

    def test_comando_com_barra_no_web_nao_vai_ao_agente(self):
        # Regressão: "/confirmar-cliente 1" chegou ao LLM, que respondeu "cadastro confirmado"
        # sem gravar nada; "/confirmar-visita 2" fez o agente criar outra proposta.
        import tempfile
        from secretaria.banco import Banco, Contexto
        from secretaria.memoria import MemoriaConversas
        from secretaria.atendimento_web import responder_turno

        with tempfile.TemporaryDirectory() as pasta:
            with Banco(Path(pasta) / 'web.sqlite3') as banco:
                banco.preparar_demo()
                ctx = Contexto('demo', 'ana')
                sessao = MemoriaConversas(banco).iniciar(ctx)
                with patch('secretaria.atendimento_web.criar_agente_agenda',
                           side_effect=AssertionError('não deveria chamar o agente')):
                    for comando in ('/confirmar-cliente 1', '/confirmar-visita 2', '  /confirmar 3'):
                        r = responder_turno(banco, ctx, sessao, comando)
                        self.assertEqual(r['rota'], 'comando_local')
                        self.assertEqual(r['ferramentas'], [])
                        self.assertIn('aba Agenda', r['resposta'])
                turnos = banco.con.execute('SELECT COUNT(*) FROM turnos_agente').fetchone()[0]
                self.assertEqual(turnos, 0)


if __name__ == '__main__':
    unittest.main()
