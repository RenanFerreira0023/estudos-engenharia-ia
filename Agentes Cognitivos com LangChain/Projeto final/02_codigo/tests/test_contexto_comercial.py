"""Contexto da sessão e regressões observadas; modelo roteirizado local."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextvars import ContextVar
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from langchain_core.messages import AIMessage
from auto_super_parts.atendimento_memoria import AtendimentoComMemoria
from auto_super_parts.memoria import MemoriaSQLite
from auto_super_parts.agente_fase02 import criar_ferramentas
from auto_super_parts.catalogo_fase02 import Catalogo
from auto_super_parts.viacep import criar_cliente_dummy
from test_memoria import ModeloObservador


def call(nome,args,id):
    return AIMessage(content='',tool_calls=[{'name':nome,'args':args,'id':id}])


class ContextoComercialTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.mem=MemoriaSQLite(Path(self.tmp.name)/'m.sqlite3')
        self.addCleanup(self.mem.fechar)
        self.s=self.mem.abrir_sessao('a')

    def test_pedido_observado_chega_ao_proximo_turno_sem_precos(self):
        modelo=ModeloObservador(responses=[
            call('consultar_catalogo',{'veiculo_id':'V002','categoria':'velas'},'p'),
            call('calcular_orcamento',{'itens':[{'produto_id':'P009','quantidade':8}],'modalidade':'retirada'},'o'),
            AIMessage(content='Temos 7. Posso calcular para essa quantidade?'),
            call('calcular_orcamento',{'itens':[{'produto_id':'P009','quantidade':7}],'modalidade':'retirada'},'o2'),
            AIMessage(content='Total R$ 118,30.')])
        sistema=AtendimentoComMemoria(self.mem,modelo=modelo,cliente_cep=criar_cliente_dummy())
        self.addCleanup(sistema.fechar)
        self.mem.confirmar_veiculo('a',sistema.atendente.catalogo.listar_veiculos()['veiculos'][2])
        r=sistema.atender('a',self.s,'Tenho um Palio 2010 1.0 Fire 8V flex. Quero 8 velas para retirada.',salvar=False)
        self.assertEqual(r['status'],'ok')
        c=self.mem.contexto_atendimento('a',self.s)
        self.assertEqual(c['veiculo_do_pedido'],'V002')
        self.assertEqual(c['ultimo_orcamento']['itens'][0]['produto_id'],'P009')
        self.assertEqual(c['ultimo_orcamento']['itens'][0]['saldo_observado'],7)
        self.assertNotIn('preco',json.dumps(c))
        r=sistema.atender('a',self.s,'pode ser',salvar=False)
        recebido=r['memoria_utilizada']['contexto_comercial']
        self.assertEqual(recebido,c)
        retorno=json.loads(next(m['conteudo'] for m in r['trajetoria'] if m.get('ferramenta')=='calcular_orcamento'))
        self.assertEqual(retorno['total_centavos'],11830)
        self.assertEqual(self.mem.perfil('a')['veiculo_confirmado']['id'],'V003')

    def test_isolamento_nova_sessao_persistencia_e_exclusao(self):
        self.mem.guardar_contexto_atendimento('a',self.s,{'produtos_consultados':[{'id':'P009'}]})
        outra=self.mem.abrir_sessao('a')
        self.assertEqual(self.mem.contexto_atendimento('a',outra),{})
        with self.assertRaises(PermissionError):
            self.mem.contexto_atendimento('b',self.s)
        with self.assertRaises(PermissionError):
            self.mem.guardar_contexto_atendimento('b',self.s,{})
        mem2=MemoriaSQLite(Path(self.tmp.name)/'m.sqlite3')
        try:
            self.assertEqual(mem2.contexto_atendimento('a',self.s)['produtos_consultados'][0]['id'],'P009')
        finally:
            mem2.fechar()
        self.mem.esquecer('a')
        self.assertEqual(self.mem.contexto_atendimento('a',self.s),{})

    def test_codigo_explicito_ignora_filtro_herdado_mas_nao_pedido_de_aplicacao(self):
        c=Catalogo()
        self.addCleanup(c.fechar)
        pedido=ContextVar('teste',default='Calcule 7 unidades do produto P009 para retirada.')
        ferramenta={t.name:t for t in criar_ferramentas(c,criar_cliente_dummy(),pedido)}['consultar_catalogo']
        r=ferramenta.invoke({'produto_id':'P009','veiculo_id':'V003','categoria':'vela'})
        self.assertEqual(r['status'],'ok')
        self.assertEqual(r['produtos'][0]['id'],'P009')
        self.assertEqual(r['filtros_descartados']['veiculo_id'],'V003')
        self.assertNotIn('JOIN',r['sql_executado'][0]['sql'])
        pedido.set('P009 serve no Celta 2012?')
        r=ferramenta.invoke({'produto_id':'P009','veiculo_id':'V003'})
        self.assertEqual(r['produtos'],[])
        self.assertNotIn('filtros_descartados',r)

    def test_confirmacao_explicita_de_veiculo_limpa_pedido_anterior(self):
        self.mem.guardar_contexto_atendimento('a',self.s,{'veiculo_do_pedido':'V002'})
        sistema=AtendimentoComMemoria(self.mem,modelo=ModeloObservador(responses=[AIMessage(content='fixture')]),cliente_cep=criar_cliente_dummy())
        self.addCleanup(sistema.fechar)
        sistema.confirmar_veiculo('a',self.s,'V003')
        self.assertEqual(self.mem.contexto_atendimento('a',self.s),{})
