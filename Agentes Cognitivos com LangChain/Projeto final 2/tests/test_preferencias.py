"""Preferência explícita atravessa sessões e correção substitui o valor antigo."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_core.messages import AIMessage
from secretaria.banco import Banco, Contexto
from secretaria.cli import conversar_sobre_visita
from secretaria.memoria import MemoriaConversas
from secretaria.preferencias import PreferenciasUsuario


class PreferenciasTest(unittest.TestCase):
    def test_correcao_reinicio_isolamento_e_exclusao(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta)/'memoria.sqlite3'
            ana, bruno = Contexto('demo','ana'), Contexto('demo','bruno')
            with Banco(caminho) as banco:
                banco.preparar_demo()
                memoria = MemoriaConversas(banco)
                primeira = memoria.iniciar(ana)
                preferencias = PreferenciasUsuario(banco)
                self.assertEqual(preferencias.salvar(ana,'estilo','curto')['versao'],1)
                self.assertEqual(preferencias.salvar(ana,'estilo','curto')['estado'],'sem_alteracao')
                self.assertEqual(preferencias.salvar(ana,'estilo','detalhado')['versao'],2)
                self.assertEqual(preferencias.listar(bruno),[])
                with self.assertRaises(ValueError):
                    preferencias.salvar(ana,'senha','secreta')
                memoria.encerrar(ana,primeira)
                memoria.iniciar(ana)
            with Banco(caminho) as banco:
                preferencias = PreferenciasUsuario(banco)
                self.assertEqual(preferencias.listar(ana),
                                 [{'chave':'estilo','valor':'detalhado','versao':2}])
                self.assertEqual(preferencias.listar(bruno),[])
                self.assertEqual(preferencias.apagar(ana,'estilo')['estado'],'apagada')
                self.assertEqual(preferencias.listar(ana),[])
                self.assertEqual(banco.con.execute(
                    'SELECT COUNT(*) FROM historico_preferencias WHERE usuario_id=?',('ana',)
                ).fetchone()[0],0)

    def test_comandos_locais_sem_modelo_e_preferencia_atual_no_prompt(self):
        class AgenteLocal:
            def __init__(self):
                self.entradas = []

            def invoke(self, dados, _config):
                self.entradas.append(dados['messages'][-1]['content'])
                return {'messages': dados['messages'] + [AIMessage(content='Resposta local')]}

        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta)/'chat.sqlite3'
            with Banco(caminho) as banco:
                banco.preparar_demo()
                with patch('secretaria.agente_agenda.criar_agente_agenda',
                           side_effect=AssertionError('Comando local não chama modelo')), \
                     patch('builtins.input',side_effect=['/lembrar estilo=curto','/nova','/memorias','/voltar']):
                    conversar_sobre_visita(banco,Contexto('demo','ana'))
            with Banco(caminho) as banco:
                agente = AgenteLocal()
                with patch('secretaria.agente_agenda.criar_agente_agenda',return_value=agente), \
                     patch('builtins.input',side_effect=['/lembrar estilo=detalhado',
                                                        'Qual minha preferência?','/voltar']):
                    conversar_sobre_visita(banco,Contexto('demo','ana'))
                self.assertIn('detalhado',agente.entradas[0])
                self.assertNotIn('"valor": "curto"',agente.entradas[0])


if __name__ == '__main__':
    unittest.main()
