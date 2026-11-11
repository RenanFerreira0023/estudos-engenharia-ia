"""Índice de fontes: preparo separado da busca, versão e permissão."""
import tempfile
import unittest
from pathlib import Path

from secretaria.banco import Banco, Contexto
from secretaria.indice_fontes import IndiceFontes


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
