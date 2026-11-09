"""Reprodução local do orçamento observado; não chama LLM nem mede sua acurácia."""
import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from auto_super_parts.configuracao import localizar_projeto
from auto_super_parts.verificacao import checar_valores,coletar_evidencias,VerificadorResposta,totais_de_itens
from test_verificacao import parecer

class TotaisItensTest(unittest.TestCase):
    def setUp(self):
        f=localizar_projeto()/'04_avaliacao_e_evidencias/resultados/fase05_20261109T023553805987Z.json'
        self.resultado=json.loads(f.read_text(encoding='utf-8'))
        self.evidencias=coletar_evidencias(self.resultado)
        self.original=self.resultado['resposta_antes_da_verificacao']
        self.reparada=self.resultado['verificacao_geral']['resposta_reparada']

    def test_resposta_original_e_reparada_passam_regras_financeiras(self):
        for texto in (self.original,self.reparada):
            self.assertEqual(checar_valores(texto,self.evidencias),[],texto)

    def test_total_geral_nao_pode_ser_total_de_um_item(self):
        for texto in ('Total: R$ 119,70.','Total geral: R$ 119,70.','Subtotal: R$ 119,70.'):
            self.assertTrue(any(p['regra']=='valor_diverge_do_orcamento' for p in checar_valores(texto,self.evidencias)))

    def test_erro_de_um_centavo_continua_bloqueado(self):
        self.assertTrue(checar_valores(self.original.replace('R$ 119,70','R$ 119,71'),self.evidencias))

    def test_total_de_outro_item_nao_passa_no_bloco_numerado(self):
        texto=self.original.replace('R$ 119,70','R$ 89,90')
        self.assertTrue(any(p['regra']=='valor_diverge_do_item' for p in checar_valores(texto,self.evidencias)))

    def test_rotulos_explicitos_e_markdown(self):
        texto='1. **Óleo**\n   - **Total do item:** R$ 119,70\n2. **Cabos**\n   - **Subtotal do item:** R$ 89,90\n**Subtotal:** R$ 234,50\n**Frete:** R$ 0,00\n**Total geral:** R$ 234,50'
        self.assertEqual(checar_valores(texto,self.evidencias),[])
        self.assertTrue(checar_valores('Frete: R$ 89,90.',self.evidencias))

    def test_cliente_e_orcamento_pendente_nao_autorizam_multiplicacao(self):
        sem_tool=[{'id':'M001','tipo':'declaracao_cliente','dados':{'quantidade':3,'preco_unitario_centavos':3990}}]
        self.assertTrue(checar_valores('Óleo: R$ 119,70.',sem_tool))
        copia=copy.deepcopy(self.evidencias)
        for e in copia:
            if e.get('ferramenta')=='calcular_orcamento':
                e['dados'].update(status='estoque_insuficiente',total_centavos=None)
                self.assertEqual(totais_de_itens(e['dados']),[])
        self.assertTrue(checar_valores('Óleo: R$ 119,70.',copia))

    def test_parecer_real_gravado_aprova_sem_reparo(self):
        # REPLAY: o juiz original aprovou o conteúdo; só as regras numéricas bloqueavam.
        registrado=self.resultado['verificacao_geral']['avaliacoes'][0]['parecer']
        def nao_reparar(_):
            self.fail('Não deve reparar a candidata já sustentada pelo parecer gravado.')
        v=VerificadorResposta(lambda _:registrado,nao_reparar,origem='replay de parecer gravado; sem API')
        resposta,auditoria=v.processar({**self.resultado,'resposta':self.original})
        self.assertEqual(auditoria['status'],'aprovada')
        self.assertEqual(auditoria['reparos_executados'],0)
        self.assertEqual(resposta,self.original)

    def test_juiz_ainda_pode_reprovar_associacao_dos_produtos(self):
        v=VerificadorResposta(lambda p:parecer(p,'contradita'),lambda p:'')
        self.assertFalse(v.avaliar(self.resultado,self.original)['aprovada'])

if __name__=='__main__':
    unittest.main()
