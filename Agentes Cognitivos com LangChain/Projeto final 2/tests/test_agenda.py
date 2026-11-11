"""Casos centrais da agenda, sem LLM nem rede."""
import sys
import tempfile
import unittest
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from secretaria.banco import Banco, Contexto
from secretaria.agenda import Agenda, consultar_cep, consultar_cnpj


class AgendaTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.banco = Banco(Path(self.tmp.name)/'teste.sqlite3')
        self.banco.preparar_demo()
        self.ana = Contexto('demo','ana')
        self.bruno = Contexto('demo','bruno')
        self.agenda = Agenda(self.banco)
        self.cliente = self.agenda.cadastrar_cliente(self.ana,'Alfa Serviços')
        self.endereco = {'logradouro':'Rua Exemplo','numero':'10','cidade':'Curitiba','uf':'PR'}
        self.agora = datetime(2026,11,10,12,tzinfo=timezone.utc)
        self.inicio = datetime(2026,11,11,17,tzinfo=timezone.utc)
        self.fim = self.inicio + timedelta(hours=1)

    def tearDown(self):
        self.banco.fechar()
        self.tmp.cleanup()

    def proposta(self, inicio=None, fim=None, atendente=None, ctx=None):
        return self.agenda.propor_visita(ctx or self.ana,self.cliente,inicio or self.inicio,
            fim or self.fim,self.endereco,atendente,agora=self.agora)

    def test_confirmacao_idempotente_e_auditoria(self):
        p = self.proposta()
        self.assertEqual(self.agenda.listar_agenda(self.ana),[])
        a = self.agenda.confirmar_visita(self.ana,p['proposta_id'],agora=self.agora)
        b = self.agenda.confirmar_visita(self.ana,p['proposta_id'],agora=self.agora)
        self.assertEqual(a['agendamento_id'],b['agendamento_id'])
        self.assertEqual(len(self.agenda.listar_agenda(self.ana)),1)
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM auditoria_agenda').fetchone()[0],1)

    def test_conflito_adjacencia_e_outro_atendente(self):
        self.agenda.confirmar_visita(self.ana,self.proposta()['proposta_id'],agora=self.agora)
        with self.assertRaisesRegex(ValueError,'compromisso'):
            self.proposta(self.inicio+timedelta(minutes=30),self.fim+timedelta(minutes=30))
        self.proposta(self.fim,self.fim+timedelta(hours=1))
        self.proposta(atendente='bruno')

    def test_nome_do_atendente_aceita_maiusculas(self):
        self.assertEqual(self.agenda.resolver_atendente(self.ana,'Bruno'),'bruno')
        self.assertEqual(self.agenda.resolver_atendente(self.ana,' ANA '),'ana')
        p=self.proposta(atendente='Bruno')
        self.assertEqual(p['atendente'],'bruno')

    def test_conflito_surgido_antes_de_confirmar(self):
        p1 = self.proposta()
        p2 = self.proposta(self.inicio+timedelta(minutes=30),self.fim+timedelta(minutes=30))
        self.agenda.confirmar_visita(self.ana,p1['proposta_id'],agora=self.agora)
        self.assertEqual(self.agenda.confirmar_visita(self.ana,p2['proposta_id'],agora=self.agora)['estado'],'conflito')

    def test_proposta_de_outro_usuario_nao_pode_ser_confirmada(self):
        p = self.proposta()
        with self.assertRaises(PermissionError):
            self.agenda.confirmar_visita(self.bruno,p['proposta_id'],agora=self.agora)

    def test_cep_fixture_nao_vira_api_real(self):
        resultado = consultar_cep('80000-000', lambda url: {'cep':'80000-000','logradouro':'Rua A',
            'bairro':'Centro','localidade':'Curitiba','uf':'PR'})
        self.assertEqual(resultado['origem'],'fixture_local')
        with self.assertRaises(ValueError):
            consultar_cep('abc')

    def test_cnpj_fixture_exige_mesmo_documento(self):
        cnpj = '33683111000280'
        dado = consultar_cnpj(cnpj,lambda url:{'cnpj':cnpj,'razao_social':'Empresa Exemplo',
                                               'nome_fantasia':'Exemplo'})
        self.assertEqual(dado['origem'],'fixture_local')
        self.assertEqual(dado['razao_social'],'Empresa Exemplo')
        with self.assertRaisesRegex(ValueError,'não corresponde'):
            consultar_cnpj(cnpj,lambda url:{'cnpj':'00000000000000','razao_social':'Outra'})

    def test_cadastro_pj_guarda_origem_e_nome_fantasia(self):
        cnpj='33683111000280'
        consulta=consultar_cnpj(cnpj,lambda url:{'cnpj':cnpj,'razao_social':'Empresa Exemplo',
                                                 'nome_fantasia':'Exemplo'})
        cliente_id=self.agenda.cadastrar_cliente(self.ana,'Empresa Exemplo','PJ',cnpj,cadastro_api=consulta)
        salvo=self.banco.con.execute('SELECT * FROM clientes WHERE id=?',(cliente_id,)).fetchone()
        self.assertEqual(salvo['nome_fantasia'],'Exemplo')
        self.assertEqual(salvo['origem_cadastro'],'fixture_local')
        self.assertIsNotNone(salvo['consultado_cnpj_em'])
        self.assertEqual(self.agenda.cadastrar_cliente(self.ana,'Empresa Exemplo','PJ',cnpj,cadastro_api=consulta),cliente_id)

    def test_migracao_v3_preserva_cliente_sem_inventar_origem(self):
        caminho=Path(self.tmp.name)/'legado_v3.sqlite3'
        with Banco(caminho) as legado:
            legado.preparar_demo()
            Agenda(legado).cadastrar_cliente(self.ana,'Empresa Antiga','PJ','33683111000280')
        con=sqlite3.connect(caminho)
        con.execute('DROP TABLE fontes_anotacao')
        con.execute('DROP TABLE anotacoes_projeto')
        con.execute('DROP TABLE projetos')
        con.execute('DROP TABLE auditoria_clientes')
        con.execute('DROP TABLE propostas_cliente')
        con.execute('DROP TABLE consultas_cnpj')
        con.execute('ALTER TABLE clientes DROP COLUMN consultado_cnpj_em')
        con.execute('ALTER TABLE clientes DROP COLUMN origem_cadastro')
        con.execute('ALTER TABLE clientes DROP COLUMN nome_fantasia')
        con.execute('PRAGMA user_version=3')
        con.commit();con.close()
        with Banco(caminho) as novo:
            linha=novo.con.execute('SELECT nome,origem_cadastro FROM clientes').fetchone()
            self.assertEqual(tuple(linha),('Empresa Antiga','origem_nao_registrada'))
            self.assertEqual(novo.con.execute('PRAGMA user_version').fetchone()[0],8)


if __name__ == '__main__':
    unittest.main()
