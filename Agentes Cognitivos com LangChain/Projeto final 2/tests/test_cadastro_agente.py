"""Cadastro PJ por consulta, proposta e confirmação, sem rede nem LLM."""
import sys
import tempfile
import unittest
from io import StringIO
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from secretaria.banco import Banco, Contexto
from secretaria.agenda import Agenda
from secretaria.agente_agenda import criar_ferramentas_agenda


class CadastroAgenteTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.caminho=Path(self.tmp.name)/'teste.sqlite3'
        self.banco=Banco(self.caminho)
        self.banco.preparar_demo()
        self.ana=Contexto('demo','ana')
        self.bruno=Contexto('demo','bruno')
        self.agenda=Agenda(self.banco)
        self.agora=datetime(2026,11,10,12,tzinfo=timezone.utc)
        self.dados={'origem':'fixture_local','cnpj':'33683111000280',
                    'razao_social':'Empresa Exemplo','nome_fantasia':'Exemplo',
                    'consultado_em':self.agora.isoformat()}

    def tearDown(self):
        self.banco.fechar()
        self.tmp.cleanup()

    def consulta_e_proposta(self,ctx=None):
        ctx=ctx or self.ana
        consulta_id=self.agenda.registrar_consulta_cnpj(ctx,self.dados)
        return self.agenda.propor_cadastro_cliente(ctx,consulta_id,agora=self.agora)

    def test_confirma_uma_vez_com_origem_e_auditoria(self):
        proposta=self.consulta_e_proposta()
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM clientes').fetchone()[0],0)
        primeira=self.agenda.confirmar_cadastro_cliente(self.ana,proposta['proposta_id'],agora=self.agora)
        segunda=self.agenda.confirmar_cadastro_cliente(self.ana,proposta['proposta_id'],agora=self.agora)
        self.assertEqual(primeira['cliente_id'],segunda['cliente_id'])
        self.assertEqual(segunda['estado'],'ja_confirmada')
        salvo=self.banco.con.execute('SELECT * FROM clientes WHERE id=?',(primeira['cliente_id'],)).fetchone()
        self.assertEqual((salvo['nome'],salvo['nome_fantasia'],salvo['origem_cadastro']),
                         ('Empresa Exemplo','Exemplo','fixture_local'))
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM auditoria_clientes').fetchone()[0],1)

    def test_outro_usuario_nao_propoe_nem_confirma(self):
        consulta_id=self.agenda.registrar_consulta_cnpj(self.ana,self.dados)
        with self.assertRaises(PermissionError):
            self.agenda.propor_cadastro_cliente(self.bruno,consulta_id,agora=self.agora)
        proposta=self.agenda.propor_cadastro_cliente(self.ana,consulta_id,agora=self.agora)
        with self.assertRaises(PermissionError):
            self.agenda.confirmar_cadastro_cliente(self.bruno,proposta['proposta_id'],agora=self.agora)
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM clientes').fetchone()[0],0)

    def test_expiracao_e_conflito_com_cadastro_existente(self):
        proposta=self.consulta_e_proposta()
        with self.assertRaisesRegex(ValueError,'expirada'):
            self.agenda.confirmar_cadastro_cliente(self.ana,proposta['proposta_id'],
                agora=self.agora+timedelta(minutes=31))
        existente=self.agenda.cadastrar_cliente(self.bruno,'Empresa já cadastrada','PJ',self.dados['cnpj'])
        conflito=self.agenda.confirmar_cadastro_cliente(self.ana,proposta['proposta_id'],agora=self.agora)
        self.assertEqual((conflito['estado'],conflito['cliente_id']),('conflito',existente))
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM clientes').fetchone()[0],1)

    def test_ferramentas_consultam_e_propõem_sem_cadastrar(self):
        dados={**self.dados,'consultado_em':datetime.now(timezone.utc).isoformat()}
        with patch('secretaria.agenda.consultar_cnpj',return_value=dados):
            ferramentas={f.name:f for f in criar_ferramentas_agenda(self.caminho,self.ana)}
            consulta=ferramentas['consultar_cnpj_minha_receita'].invoke({'cnpj':dados['cnpj']})
            proposta=ferramentas['propor_cadastro_cliente'].invoke({'consulta_id':consulta['consulta_id']})
        self.assertEqual(consulta['status'],'nao_cadastrado')
        self.assertEqual(proposta['estado'],'pendente')
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM clientes').fetchone()[0],0)

    def test_comando_terminal_confirma_sem_invocar_llm(self):
        from secretaria.cli import conversar_sobre_visita
        consulta_id=self.agenda.registrar_consulta_cnpj(self.ana,
            {**self.dados,'consultado_em':datetime.now(timezone.utc).isoformat()})
        proposta=self.agenda.propor_cadastro_cliente(self.ana,consulta_id)
        with patch('secretaria.agente_agenda.criar_agente_agenda',return_value=object()), \
             patch('builtins.input',side_effect=[f"/confirmar-cliente {proposta['proposta_id']}",'/voltar']), \
             redirect_stdout(StringIO()) as saida:
            conversar_sobre_visita(self.banco,self.ana)
        self.assertIn("'estado': 'confirmada'",saida.getvalue())
        self.assertEqual(self.banco.con.execute('SELECT COUNT(*) FROM clientes').fetchone()[0],1)


if __name__=='__main__':
    unittest.main()
