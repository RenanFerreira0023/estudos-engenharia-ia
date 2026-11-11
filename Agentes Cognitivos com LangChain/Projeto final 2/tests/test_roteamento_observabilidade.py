"""Rota e callback possuem contratos observáveis sem chamada à API."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from secretaria.banco import Banco, Contexto
from secretaria.cli import conversar_sobre_visita
from secretaria.observabilidade import RastroAgente
from secretaria.roteamento import roteador_pedido


class RoteamentoObservabilidadeTest(unittest.TestCase):
    def test_create_agent_emite_callback_de_modelo_sem_api(self):
        rastro = RastroAgente()
        agente = create_agent(FakeListChatModel(responses=['Olá']), [])
        resposta = agente.invoke({'messages':[{'role':'user','content':'Oi'}]},
                                 {'callbacks':[rastro]})
        self.assertEqual(resposta['messages'][-1].content,'Olá')
        self.assertEqual([item['evento'] for item in rastro.eventos],
                         ['modelo_iniciado','modelo_concluido'])

    def test_terminal_passa_callback_e_salva_rota_sem_pergunta(self):
        class AgenteLocal:
            def invoke(self, dados, configuracao):
                callback = configuracao['callbacks'][0]
                identificador = uuid4()
                callback.on_chat_model_start({}, [], run_id=identificador)
                callback.on_llm_end(None, run_id=identificador)
                return {'messages': dados['messages'] + [AIMessage(content='Resposta local')]}

        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta)/'chat.sqlite3'
            with Banco(caminho) as banco:
                banco.preparar_demo()
                with patch('secretaria.agente_agenda.criar_agente_agenda',return_value=AgenteLocal()), \
                     patch('builtins.input',side_effect=['O CNPJ PRIVADO está cadastrado?','/voltar']):
                    conversar_sobre_visita(banco,Contexto('demo','ana'))
            texto = (caminho.parent/'rastros_agente.jsonl').read_text(encoding='utf-8')
            registro = json.loads(texto)
            self.assertEqual(registro['rota'],'cliente')
            self.assertEqual(len(registro['eventos']),2)
            self.assertNotIn('PRIVADO',texto)

    def test_rotas_e_seguimento_curto(self):
        self.assertEqual(roteador_pedido.invoke({'pergunta':'Agende visita para Alfa'})['rota'],'visita')
        self.assertEqual(roteador_pedido.invoke({'pergunta':'O CNPJ está cadastrado?'})['rota'],'cliente')
        self.assertEqual(roteador_pedido.invoke({'pergunta':'Estou falando do cleinte Alfa'})['rota'],'cliente')
        self.assertEqual(roteador_pedido.invoke({'pergunta':'Olá'})['rota'],'geral')
        atual = roteador_pedido.invoke({'pergunta':'Às 15h',
                                        'anteriores':[{'pergunta':'Agende visita para Alfa'}]})
        self.assertEqual(atual['rota'],'visita')

    def test_callback_registra_eventos_sem_conteudo(self):
        rastro = RastroAgente()
        identificador = uuid4()
        rastro.on_chat_model_start({}, [], run_id=identificador)
        rastro.on_tool_start({'name':'buscar_cliente'}, 'CNPJ_PRIVADO', run_id=identificador)
        rastro.on_tool_end('RESPOSTA_PRIVADA', run_id=identificador)
        rastro.on_llm_end(None, run_id=identificador)
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta)/'rastros.jsonl'
            rastro.salvar(caminho,sessao_id='sessao',usuario_id='ana',rota='cliente')
            texto = caminho.read_text(encoding='utf-8')
            registro = json.loads(texto)
            self.assertEqual(registro['rota'],'cliente')
            self.assertEqual(len(registro['eventos']),4)
            self.assertNotIn('CNPJ_PRIVADO',texto)
            self.assertNotIn('RESPOSTA_PRIVADA',texto)


if __name__ == '__main__':
    unittest.main()
