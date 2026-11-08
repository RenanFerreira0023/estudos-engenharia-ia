"""Fixtures de contrato AutoTools: não são evidência de cobertura técnica real."""
import json
from pathlib import Path
import sys
import unittest

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from auto_super_parts.autotools import ClienteAutoTools
from provar_autotools import conferir_identidade, extrair_id, investigar


VEICULO_FIXTURE = {'marca': 'Volkswagen', 'modelo': 'Gol', 'ano_modelo': 2010,
                  'motor': '1.0 8V', 'combustivel': 'flex'}


def transporte_json(dados):
    return lambda *args: (200, 'application/json; charset=utf-8', json.dumps(dados))


class AutoToolsTest(unittest.TestCase):
    def test_lista_vazia_e_origem_de_teste(self):
        r = ClienteAutoTools(transporte_json({'data': []})).buscar(VEICULO_FIXTURE)
        self.assertEqual(r['status'], 'sem_resultados')
        self.assertEqual(r['origem'], 'transporte_injetado_teste')
        self.assertEqual(r['http_status'], 200)

    def test_golf_nao_e_gol(self):
        externo = {'make': 'Volkswagen', 'model': 'Golf', 'year': 2019,
                   'engine': 'DADA', 'fuel_type': 'Petrol'}
        r = conferir_identidade(VEICULO_FIXTURE, externo)
        self.assertFalse(r['confirmada'])
        self.assertIn('modelo', r['pendencias'])
        self.assertEqual(r['campos_externos']['combustivel'], 'Petrol')

    def test_nome_e_ano_nao_confirmam_motor_mercado(self):
        externo = {'make': 'Volkswagen', 'model': 'Gol', 'year': 2010}
        r = conferir_identidade(VEICULO_FIXTURE, externo)
        self.assertFalse(r['confirmada'])
        self.assertIn('motor', r['pendencias'])
        self.assertIn('mercado_brasileiro_nao_confirmado', r['pendencias'])

    def test_identidade_completa_em_fixture_e_apenas_contrato(self):
        externo = {'make': 'Volkswagen', 'model': 'Gol', 'year': 2010,
                   'engine': '1.0 8V', 'fuel_type': 'flex', 'market': 'Brazil'}
        self.assertTrue(conferir_identidade(VEICULO_FIXTURE, externo)['confirmada'])

    def test_id_da_api_url_oficial(self):
        self.assertEqual(extrair_id({'api_url': 'https://autotools.brightcoding.dev/api/vehicles/8'}), '8')
        for url in ['https://outro.exemplo/api/vehicles/8', 'https://autotools.brightcoding.dev@outro.exemplo/api/vehicles/8',
                    'https://autotools.brightcoding.dev/api/vehicles/8?extra=1', '/api/vehicles/8']:
            self.assertIsNone(extrair_id({'api_url': url}))

    def test_ids_arbitrarios_e_secoes_nao_sao_urls(self):
        cliente = ClienteAutoTools(transporte_json({}))
        for identificador in ['../outro', 'https://outro.exemplo', True, None]:
            with self.assertRaises(ValueError):
                cliente.detalhe(identificador)
        with self.assertRaises(ValueError):
            cliente.secao(8, 'outro')

    def test_timeout_sem_fallback(self):
        def falhar(*args):
            raise httpx.ReadTimeout('Fixture de timeout')
        r = ClienteAutoTools(falhar).buscar(VEICULO_FIXTURE)
        self.assertEqual(r['status'], 'timeout')
        self.assertIsNone(r['json'])

    def test_indisponibilidade_nao_vira_lista_vazia(self):
        def falhar(*args):
            raise httpx.ConnectError('Fixture de conexão')
        self.assertEqual(ClienteAutoTools(falhar).buscar(VEICULO_FIXTURE)['status'], 'indisponivel')

    def test_erro_http_preserva_codigo(self):
        r = ClienteAutoTools(lambda *args: (503, 'text/html', 'Indisponível')).buscar(VEICULO_FIXTURE)
        self.assertEqual(r['status'], 'erro_http')
        self.assertEqual(r['http_status'], 503)

    def test_html_com_200_nao_e_json(self):
        r = ClienteAutoTools(lambda *args: (200, 'text/html', '<html>fixture</html>')).buscar(VEICULO_FIXTURE)
        self.assertEqual(r['status'], 'content_type_invalido')

    def test_json_invalido(self):
        r = ClienteAutoTools(lambda *args: (200, 'application/json', '{')).buscar(VEICULO_FIXTURE)
        self.assertEqual(r['status'], 'json_invalido')

    def test_contrato_de_busca_invalido(self):
        for dados in [[], {}, {'data': {}}, {'data': [1]}]:
            self.assertEqual(ClienteAutoTools(transporte_json(dados)).buscar(VEICULO_FIXTURE)['status'], 'contrato_invalido')

    def test_secao_ausente_nao_e_especificacao(self):
        r = ClienteAutoTools(transporte_json({'available': False, 'message': 'Fixture sem dados'})).secao(8, 'oil')
        self.assertEqual(r['status'], 'secao_indisponivel')
        self.assertEqual(r['origem'], 'transporte_injetado_teste')

    def test_secao_e_detalhe_exigem_formato(self):
        self.assertEqual(ClienteAutoTools(transporte_json({'data': {}})).detalhe(8)['status'], 'ok')
        self.assertEqual(ClienteAutoTools(transporte_json({'available': True, 'data': {}})).secao(8, 'parts')['status'], 'secao_disponivel')
        self.assertEqual(ClienteAutoTools(transporte_json({'available': True})).secao(8, 'parts')['status'], 'contrato_invalido')

    def test_candidato_ambiguo_nao_dispara_consulta_oleo(self):
        urls = []
        def responder(url, params, timeout):
            urls.append(url)
            if url.endswith('/search'):
                return 200, 'application/json', json.dumps({'data': [{'id': 9, 'make': 'Volkswagen', 'model': 'Gol', 'year': 2010}]})
            return 200, 'application/json', json.dumps({'data': {'vehicle': {'id': 9}}})
        r = investigar(VEICULO_FIXTURE, ClienteAutoTools(responder))
        self.assertEqual(r['cobertura'], 'candidatos_sem_configuracao_exata_confirmada')
        self.assertEqual(r['secoes'], [])
        self.assertFalse(any(url.endswith('/oil') or url.endswith('/parts') for url in urls))

    def test_retorno_amplo_invalido_permanece_inconclusivo(self):
        def responder(url, params, timeout):
            if 'year' in params:
                return 200, 'application/json', '{"data":[]}'
            return 200, 'text/html', '<html>fixture</html>'
        r = investigar(VEICULO_FIXTURE, ClienteAutoTools(responder))
        self.assertEqual(r['cobertura'], 'inconclusiva')


if __name__ == '__main__':
    unittest.main()
