"""Verificações locais dos critérios; não chamam modelos nem LangSmith."""
import unittest

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from avaliar_atendente import (
    CASOS, Julgamento, avaliar_resposta, comparar_trajetoria,
    extrair_observado, mensagens_fixture, testar_oferta,
)


class JuizFixture:
    """Dublê determinístico para testar o contrato da nota, não um LLM juiz."""
    def __init__(self, **campos):
        self.campos = campos

    def invoke(self, _):
        return Julgamento(**self.campos)


class AvaliacaoTests(unittest.TestCase):
    def test_tres_casos_e_trajetorias_das_fixtures(self):
        self.assertEqual(len(CASOS), 3)
        for caso in CASOS:
            observado = extrair_observado(mensagens_fixture(caso))
            self.assertEqual(comparar_trajetoria(caso['ferramentas'], observado), 1)

    def test_ordem_repeticao_e_ferramenta_extra_reprovam(self):
        for lista in [['a', 'a'], ['b', 'a'], ['a', 'b']]:
            self.assertEqual(comparar_trajetoria(['a'], {'chamadas': lista, 'executadas': lista}), 0)
        self.assertEqual(comparar_trajetoria(['a', 'b'], {'chamadas': ['b', 'a'], 'executadas': ['b', 'a']}), 0)

    def test_chamada_sem_retorno_nao_e_consulta_realizada(self):
        mensagens = mensagens_fixture(CASOS[0])
        observado = extrair_observado([m for m in mensagens if not isinstance(m, ToolMessage)])
        self.assertEqual(comparar_trajetoria(['consultar_politica'], observado), 0)

    def test_erro_ou_id_errado_nao_conta_como_execucao(self):
        for identificador, status in [('fixture-entrega', 'error'), ('outro', 'success')]:
            mensagens = mensagens_fixture(CASOS[0])
            mensagens[2] = ToolMessage(content='Falha simulada', name='consultar_politica',
                                      tool_call_id=identificador, status=status)
            self.assertEqual(extrair_observado(mensagens)['executadas'], [])

    def test_saudacao_sem_ferramenta(self):
        observado = extrair_observado([HumanMessage(content='Olá'), AIMessage(content='Olá!')])
        self.assertEqual(observado['resposta'], 'Olá!')
        self.assertEqual(comparar_trajetoria([], observado), 1)

    def test_oferta_nao_passa_mesmo_com_outros_campos_positivos(self):
        juiz = JuizFixture(responde_pergunta=True, cobre_referencia=True,
                           sem_contradicao_ou_invencao=True, somente_oferece_consulta=True,
                           justificativa='Dublê deliberadamente positivo nos outros critérios.')
        resultado = avaliar_resposta(juiz, CASOS[0], 'Posso consultar a política')
        self.assertEqual(resultado['nota'], 0)

    def test_qualquer_criterio_essencial_ausente_reprova(self):
        for campo in ['responde_pergunta', 'cobre_referencia', 'sem_contradicao_ou_invencao']:
            campos = dict(responde_pergunta=True, cobre_referencia=True,
                          sem_contradicao_ou_invencao=True, somente_oferece_consulta=False,
                          justificativa='Contrato local de avaliação.')
            campos[campo] = False
            self.assertEqual(avaliar_resposta(JuizFixture(**campos), CASOS[0], 'Fixture')['nota'], 0)

    def test_sem_llm_nao_inventa_falso_positivo(self):
        fixture = testar_oferta()
        self.assertIsNone(fixture['falso_positivo_observado'])
        self.assertIsNone(fixture['nota_juiz_estrito'])


if __name__ == '__main__':
    unittest.main()
