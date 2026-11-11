"""Índice de fontes: preparo separado da busca, versão e permissão."""
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from secretaria.banco import Banco, Contexto
from secretaria.indice_fontes import IndiceFontes, pasta_indice_do_banco
from secretaria.agente_agenda import criar_ferramentas_agenda


class EmbeddingsFixture:
    def __init__(self):
        self.chamadas = 0

    def vetor(self, texto):
        texto = texto.lower()
        return [1.0 if 'alfa' in texto else 0.0,
                1.0 if 'beta' in texto else 0.0, 0.1]

    def embed_documents(self, textos):
        self.chamadas += 1
        return [self.vetor(texto) for texto in textos]

    def embed_query(self, texto):
        return self.vetor(texto)


class IndiceFontesTest(unittest.TestCase):
    def test_menu_prepara_indice_apos_confirmacao(self):
        from secretaria.cli import preparar_indice_no_terminal
        with tempfile.TemporaryDirectory() as pasta:
            with Banco(Path(pasta)/'dados.sqlite3') as banco:
                banco.preparar_demo()
                ana = Contexto('demo','ana')
                corpus = banco.selecionar_corpus(ana,'Conversa fictícia')
                banco.importar(ana,corpus,Path(__file__).resolve().parents[1] /
                              'dados/ficticios/conversa_empresa.txt')
                fixture = EmbeddingsFixture()
                with patch('builtins.input',side_effect=[str(corpus),'s']), \
                     patch('secretaria.agente_agenda.obter_chave_api',return_value='fixture'), \
                     patch('langchain_openai.OpenAIEmbeddings',return_value=fixture), \
                     redirect_stdout(StringIO()) as saida:
                    preparar_indice_no_terminal(banco,ana,None)
                self.assertIn('Índice: preparado',saida.getvalue())
                self.assertEqual(fixture.chamadas,1)
                self.assertTrue(IndiceFontes(banco,pasta_indice_do_banco(banco))
                                .buscar(ana,corpus,'Alfa',fixture,'text-embedding-3-small'))

    def test_menu_cancela_antes_de_enviar_textos(self):
        from secretaria.cli import preparar_indice_no_terminal
        with tempfile.TemporaryDirectory() as pasta:
            with Banco(Path(pasta)/'dados.sqlite3') as banco:
                banco.preparar_demo()
                ana = Contexto('demo','ana')
                corpus = banco.selecionar_corpus(ana,'Conversa fictícia')
                with patch('builtins.input',side_effect=[str(corpus),'n']), \
                     patch('langchain_openai.OpenAIEmbeddings') as embeddings, \
                     redirect_stdout(StringIO()) as saida:
                    preparar_indice_no_terminal(banco,ana,None)
                embeddings.assert_not_called()
                self.assertIn('nenhum texto enviado',saida.getvalue())

    def test_ferramenta_carrega_indice_preparado_e_bloqueia_outro_usuario(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'dados.sqlite3'
            ana, bruno = Contexto('demo','ana'), Contexto('demo','bruno')
            with Banco(caminho) as banco:
                banco.preparar_demo()
                corpus = banco.selecionar_corpus(ana,'Conversa fictícia')
                banco.importar(ana,corpus,Path(__file__).resolve().parents[1] /
                              'dados/ficticios/conversa_empresa.txt')
                fixture = EmbeddingsFixture()
                ferramentas_ana = {f.name:f for f in criar_ferramentas_agenda(caminho,ana)}
                ferramentas_bruno = {f.name:f for f in criar_ferramentas_agenda(caminho,bruno)}
                self.assertEqual(ferramentas_bruno['listar_corpora_acessiveis'].invoke({})['corpora'],[])
                self.assertEqual(ferramentas_ana['listar_corpora_acessiveis'].invoke({})['corpora'][0]['id'],corpus)
                self.assertEqual(ferramentas_ana['buscar_mensagens_fonte'].invoke(
                    {'corpus_id':corpus,'pergunta':'Alfa'})['status'],'indice_pendente')
                IndiceFontes(banco,pasta_indice_do_banco(banco)).preparar(
                    ana,corpus,fixture,'text-embedding-3-small')
                with patch('secretaria.agente_agenda.obter_chave_api',return_value='fixture'), \
                     patch('langchain_openai.OpenAIEmbeddings',return_value=fixture):
                    resposta = ferramentas_ana['buscar_mensagens_fonte'].invoke(
                        {'corpus_id':corpus,'pergunta':'Alfa'})
                self.assertEqual(resposta['status'],'ok')
                self.assertIn('Alfa',resposta['fontes'][0]['texto'])
                self.assertEqual(ferramentas_bruno['buscar_mensagens_fonte'].invoke(
                    {'corpus_id':corpus,'pergunta':'Alfa'})['status'],'acesso_negado')

    def test_preparo_busca_escopo_e_versao(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'dados.sqlite3'
            ana, bruno = Contexto('demo','ana'), Contexto('demo','bruno')
            with Banco(caminho) as banco:
                banco.preparar_demo()
                corpus = banco.selecionar_corpus(ana,'Conversa fictícia')
                banco.importar(ana,corpus,Path(__file__).resolve().parents[1] /
                              'dados/ficticios/conversa_empresa.txt')
                embeddings = EmbeddingsFixture()
                indice = IndiceFontes(banco,Path(pasta)/'indices')
                with self.assertRaisesRegex(ValueError,'não preparado'):
                    indice.buscar(ana,corpus,'Alfa',embeddings,'fixture')
                preparado = indice.preparar(ana,corpus,embeddings,'fixture')
                self.assertEqual(preparado['estado'],'preparado')
                self.assertEqual(indice.preparar(ana,corpus,embeddings,'fixture')['estado'],'atual')
                self.assertEqual(embeddings.chamadas,1)
                achados = indice.buscar(ana,corpus,'Alfa',embeddings,'fixture',limite=2)
                self.assertIn('Alfa',achados[0]['texto'])
                self.assertIsInstance(achados[0]['mensagem_id'],int)
                with self.assertRaises(PermissionError):
                    indice.buscar(bruno,corpus,'Alfa',embeddings,'fixture')
                with banco.transacao():
                    banco.con.execute('UPDATE mensagens_importadas SET texto=? WHERE id=?',
                                      ('Texto corrigido para teste',achados[0]['mensagem_id']))
                with self.assertRaisesRegex(ValueError,'desatualizado'):
                    indice.buscar(ana,corpus,'Alfa',embeddings,'fixture')


if __name__ == '__main__':
    unittest.main()
