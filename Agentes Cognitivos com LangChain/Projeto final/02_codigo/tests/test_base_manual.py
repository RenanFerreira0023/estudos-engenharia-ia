"""Regressões de curadoria e liberação por evidência; sem rede e sem LLM real."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from langchain_core.messages import AIMessage, ToolMessage
from auto_super_parts.agente_fase02 import AtendimentoFase02
from auto_super_parts.catalogo_fase02 import Catalogo
from auto_super_parts.configuracao import localizar_projeto
from auto_super_parts.consultas_complementares import consultar_tecnica, conferir_resposta, pede_especificacao_oleo
from auto_super_parts.viacep import criar_cliente_dummy
from test_correcao_fase02 import ModeloRoteirizado


def mensagem_tecnica(vid, assunto='oleo'):
    return ToolMessage(content=json.dumps(consultar_tecnica(vid, assunto)), name='consultar_informacao_tecnica', tool_call_id='teste')


class BaseManualTest(unittest.TestCase):
    def test_fontes_identidades_e_agregado_consistentes(self):
        pasta = localizar_projeto() / '02_codigo/dados'
        carregar = lambda n: json.loads((pasta / (n+'.json')).read_text(encoding='utf-8-sig'))
        agregado = carregar('catalogo_auto_super_parts_cwb')
        for nome in ('veiculos','produtos','aplicacoes','fontes','conhecimento_tecnico'):
            self.assertEqual(agregado[nome],carregar(nome),nome)
        ids = {v['id'] for v in carregar('veiculos')}
        fontes = {f['id'] for f in carregar('fontes')['fontes']}
        registros = carregar('conhecimento_tecnico')
        self.assertEqual(len({r['id'] for r in registros}),len(registros))
        for r in registros:
            self.assertTrue(r.get('veiculo_id') is None or r['veiculo_id'] in ids)
            self.assertTrue(set(r['fontes']) <= fontes)
            if r.get('status') == 'verificado_manual':
                self.assertTrue(r['fontes'])
                self.assertTrue(r['localizacao'])

    def test_celta_intervalos_nao_sao_media(self):
        texto, regra = conferir_resposta('Qual óleo para meu Celta 2012 1.0 flex?', [mensagem_tecnica('V003')], 'Use 20W-60 e troque com 7500 km.')
        self.assertIn('5W-30',texto)
        self.assertIn('API SL',texto)
        self.assertIn('10.000 km ou 12 meses',texto)
        self.assertIn('5.000 km ou 6 meses',texto)
        self.assertNotIn('7500',texto)
        self.assertNotIn('20W-60',texto)
        self.assertIn('3,5 litros',texto)
        self.assertIn('https://meu.chevrolet.com.br/',texto)
        self.assertEqual(regra['regra'],'oleo_com_fonte_cadastrada')

    def test_diesel_preserva_norma_e_regime(self):
        texto, _ = conferir_resposta('Qual óleo da S10 2014 2.8 diesel?', [mensagem_tecnica('V005')], 'Resposta errada')
        self.assertIn('dexos2',texto)
        self.assertIn('20.000 km ou 12 meses',texto)
        self.assertIn('API CI-4',texto)
        self.assertIn('15W-40',texto)
        self.assertIn('5.000 km ou 6 meses',texto)
        self.assertIn('Capacidade em litros ainda não confirmada',texto)
        self.assertNotIn('5,7 litros',texto)

    def test_sem_chamada_nao_libera_oleo_nem_para_veiculo_com_manual(self):
        texto, regra = conferir_resposta('Qual óleo do Celta 2012?', [], '5W-30 conforme meu conhecimento')
        self.assertEqual(regra['regra'],'oleo_sem_especificacao_verificada')
        self.assertNotIn('5W-30',texto)

    def test_nao_empresta_manual_para_outro_veiculo_ou_ano(self):
        for pergunta in ('Qual óleo do Fusca 1982?', 'Qual óleo do Celta 2003?'):
            texto, regra = conferir_resposta(pergunta,[mensagem_tecnica('V003')],'5W-30')
            self.assertEqual(regra['regra'],'oleo_sem_especificacao_verificada')
            self.assertNotIn('5W-30',texto)

    def test_lacunas_nos_tres_veiculos_originais(self):
        for vid in ('V001','V002','V004'):
            consulta = consultar_tecnica(vid,'oleo')
            self.assertEqual(consulta['status'],'informacao_pendente')
            self.assertTrue(consulta['informacoes'][0]['perguntas_necessarias'])

    def test_consulta_tecnica_nao_cria_estoque_diesel(self):
        c = Catalogo()
        self.addCleanup(c.fechar)
        self.assertEqual(len(c.listar_veiculos()['veiculos']),5)
        self.assertEqual(c.consultar(veiculo_id='V005')['produtos'],[])
        self.assertEqual(c.consultar(produto_id='P003')['produtos'][0]['preco_centavos'],1850)
        self.assertEqual(c.consultar(produto_id='P023')['produtos'][0]['estoque'],0)
        self.assertFalse(c.consultar(produto_id='P003')['aplicacoes'][0]['validada_para_uso_real'])

    def test_condicoes_importam_para_pneu_e_alternador(self):
        pneus = consultar_tecnica('V003','pneus')['informacoes'][0]
        self.assertEqual(pneus['dados']['pressao_fria_psi']['carga_plena']['traseira'],36)
        self.assertNotEqual(pneus['dados']['pressao_fria_psi']['ate_3_pessoas'],pneus['dados']['pressao_fria_psi']['carga_plena'])
        self.assertTrue(pneus['perguntas_necessarias'])
        self.assertIsNone(pneus['dados']['troca_km'])
        alternador = consultar_tecnica('V003','alternador')['informacoes'][0]
        self.assertEqual(alternador['dados']['com_ar_ou_direcao_hidraulica_a'],90)
        self.assertIsNone(alternador['dados']['codigo_peca'])

    def test_troca_oleo_aciona_guarda_mas_compra_volume_nao(self):
        self.assertTrue(pede_especificacao_oleo('Quando trocar o óleo?'))
        self.assertFalse(pede_especificacao_oleo('Quero 1 litro de óleo P024 para retirada.'))

    def test_correia_celta_consultada_nao_e_negada_pela_guarda_antiga(self):
        texto, _ = conferir_resposta('Quero correia dentada para Celta 2012.',[mensagem_tecnica('V003','sincronismo')],'Use a de acessórios')
        self.assertIn('confirma correia dentada',texto)
        self.assertIn('intervalo de troca',texto)
        self.assertNotIn('Use a de acessórios',texto)

    def test_ferramenta_executada_fornece_evidencia_ao_guardiao(self):
        modelo = ModeloRoteirizado(responses=[
            AIMessage(content='',tool_calls=[{'name':'consultar_informacao_tecnica','args':{'veiculo_id':'V003','assunto':'oleo'},'id':'manual'}]),
            AIMessage(content='Troque com 50000 km.')])
        sistema = AtendimentoFase02(modelo=modelo,cliente_cep=criar_cliente_dummy())
        self.addCleanup(sistema.fechar)
        r = sistema.atender('Tenho um Celta 2012 1.0 8V flex. Qual viscosidade e troca de óleo?',salvar=False)
        self.assertEqual(r['status'],'ok')
        self.assertIn('5W-30',r['resposta'])
        self.assertNotIn('50000',r['resposta'])
        self.assertTrue(r['eventos_ferramentas'])
        self.assertEqual(r['verificacao_especifica']['regra'],'oleo_com_fonte_cadastrada')

    def test_freio_fora_de_cobertura_pede_dados_sem_medidas_inventadas(self):
        r = consultar_tecnica('V004','freios')
        self.assertEqual(r['status'],'informacao_pendente')
        self.assertTrue(r['informacoes'][0]['perguntas_necessarias'])
        self.assertEqual(r['fontes'],[])
        self.assertEqual(consultar_tecnica('V999','freios')['status'],'veiculo_nao_encontrado')

    def test_alternador_nao_omite_direcao_hidraulica(self):
        texto, regra = conferir_resposta('Celta 2012 sem ar mas com direção hidráulica: qual alternador?',
                                        [mensagem_tecnica('V003','alternador')],
                                        'Sem ar, são 60 A em todos os casos.')
        self.assertIn('90 A com ar-condicionado e/ou direção hidráulica',texto)
        self.assertNotIn('todos os casos',texto)
        self.assertEqual(regra['regra'],'alternador_equipamentos')


if __name__ == '__main__':
    unittest.main()
