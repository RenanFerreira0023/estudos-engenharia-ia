"""Fixtures verificam decisões, sem fingir execução de LLM ou LangSmith."""
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from secretaria.avaliacao import avaliar_caso, carregar_casos, julgar_resposta, Julgamento
from secretaria.verificador import verificar_deterministico


def ferramenta(nome, dados):
    return SimpleNamespace(type='tool', name=nome,
                           content=json.dumps(dados, ensure_ascii=False))


class AvaliacaoTest(unittest.TestCase):
    def test_fixture_oferta_consulta_reprovada(self):
        raiz = Path(__file__).resolve().parents[1]
        casos = carregar_casos(raiz)
        caso = next(c for c in casos if c['id']=='oferta_consulta')
        resultado = avaliar_caso(caso, caso['fixture_resposta'], caso['fixture_ferramentas'])
        self.assertEqual((resultado['nota_ferramentas'],resultado['nota_resposta']),(0,0))
        self.assertEqual(resultado['origem'],'fixture_manual')

    def test_juiz_nao_aprova_oferta_mesmo_com_nota_bruta_positiva(self):
        class ModeloFixture:
            def with_structured_output(self, esquema):
                self.esquema = esquema
                return self

            def invoke(self, mensagens):
                return Julgamento(nota=1, responde_pergunta=False, cobre_referencia=False,
                    sem_contradicao=True, somente_oferece_consulta=True,
                    justificativa='Apenas oferece consultar.')

        caso = next(c for c in carregar_casos(Path(__file__).resolve().parents[1])
                    if c['id']=='oferta_consulta')
        self.assertEqual(julgar_resposta(caso,caso['fixture_resposta'],ModeloFixture())['nota'],0)

    def test_contagem_exige_total_estruturado(self):
        msgs = [ferramenta('consultar_mensagens_estruturado',
                          {'status':'ok','plano':{'tipo':'contagem'},'total':1})]
        self.assertTrue(verificar_deterministico('Quantas?',
            'Foi encontrada 1 mensagem.',msgs,'consulta')['aprovada'])
        self.assertFalse(verificar_deterministico('Quantas?',
            'Foram encontradas 3 mensagens.',msgs,'consulta')['aprovada'])
        self.assertFalse(verificar_deterministico('Quantas?',
            'Foram encontradas 3 mensagens.',[],'consulta')['aprovada'])

    def test_financeiro_nao_aceita_valor_sem_retorno(self):
        msgs = [ferramenta('consultar_financeiro_projeto',{'status':'acesso_negado'})]
        self.assertFalse(verificar_deterministico('Qual o saldo?',
            'O saldo é R$ 10.000,00.',msgs)['aprovada'])
        self.assertFalse(verificar_deterministico('Qual o saldo do projeto?',
            'O saldo é R$ 10.000,00.',[], 'projeto')['aprovada'])

    def test_oferta_de_consulta_nao_responde(self):
        self.assertFalse(verificar_deterministico('Qual o prazo?',
            'Posso consultar a política.',[])['aprovada'])


if __name__=='__main__':
    unittest.main()
