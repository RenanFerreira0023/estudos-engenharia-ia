"""Demonstra a mesma fachada com modelo real ou respostas roteirizadas identificadas."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from .atendimento_memoria import AtendimentoComMemoria, criar_embeddings
from .chain_inicial import criar_modelo
from .memoria import MemoriaSQLite
from .viacep import criar_cliente_dummy


class ModeloFixture(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


class EmbeddingsFixture:
    model = 'fixture-vetorial-sem-API'
    def embed_documents(self, textos):
        return [[1.,0.] for _ in textos]
    def embed_query(self, texto):
        return [1.,0.]


def demonstrar(modo='simulado', arquivo_env=None):
    if modo not in ('real','simulado'):
        raise ValueError('Modo deve ser real ou simulado.')
    # DUMMY valida infraestrutura; não serve como evidência de compreensão da LLM.
    respostas = ['[SIMULAÇÃO] Anotei o Fusca nesta conversa.',
                 '[SIMULAÇÃO] Você informou Fusca 1982 1600 a ar gasolina.',
                 '[SIMULAÇÃO] O veículo salvo é Celta 2012; uso urbano em percursos curtos.',
                 '[SIMULAÇÃO] Você ainda não informou veículo neste cliente.',
                 '[SIMULAÇÃO] O veículo salvo agora é S10 2014 diesel.',
                 '[SIMULAÇÃO] Não tenho veículo salvo. Qual seu veículo?']
    modelo = criar_modelo(arquivo_env) if modo=='real' else ModeloFixture(responses=[AIMessage(content=r) for r in respostas])
    embeddings = criar_embeddings(arquivo_env) if modo=='real' else EmbeddingsFixture()
    registros = []
    with tempfile.TemporaryDirectory(prefix='autopecas_memoria_demo_') as tmp:
        banco = Path(tmp)/'memoria.sqlite3'
        memoria = MemoriaSQLite(banco,embeddings=embeddings)
        sistema = AtendimentoComMemoria(memoria,modelo=modelo,cliente_cep=None if modo=='real' else criar_cliente_dummy())
        a = memoria.abrir_sessao('cliente_A_demo')
        b = memoria.abrir_sessao('cliente_B_demo')
        try:
            def turno(nome, cliente, sessao, pergunta, termos=(), proibidos=()):
                r = sistema.atender(cliente,sessao,pergunta,salvar=False)
                texto = (r.get('resposta') or '').lower()
                passou = r['status']=='ok' and all(t.lower() in texto for t in termos) and not any(t.lower() in texto for t in proibidos)
                item = {'caso':nome,'criterio_local_atendido':passou,'resultado':r}
                registros.append(item)
                print(nome,'OK' if passou else 'DIVERGENCIA',flush=True)
                return r
            turno('informar_na_sessao','cliente_A_demo',a,'Meu carro é um Fusca 1982 1600 a ar, gasolina.')
            turno('lembrar_na_sessao','cliente_A_demo',a,'Qual carro eu informei?',('Fusca','1982'))
            sistema.confirmar_veiculo('cliente_A_demo',a,'V003')
            memoria.guardar_resumo('cliente_A_demo','Minha rotina é urbana, com percursos curtos de menos de 6 km e anda e para frequente.')
            memoria.fechar()
            memoria = None
            # PROCESSO NOVO lê o banco fechado; diferencia persistência em disco de uma variável Python.
            codigo = "import json,sys; sys.path.insert(0,sys.argv[1]); from auto_super_parts.memoria import MemoriaSQLite; m=MemoriaSQLite(sys.argv[2]); print(json.dumps({'A':m.perfil('cliente_A_demo'),'B':m.perfil('cliente_B_demo')})); m.fechar()"
            leitura = subprocess.run([sys.executable,'-B','-c',codigo,str(Path(__file__).parent.parent),str(banco)],capture_output=True,text=True,check=True)
            persistencia = json.loads(leitura.stdout)
            memoria = MemoriaSQLite(banco,embeddings=embeddings)
            # O serviço anterior não retém contexto; reabrimos a fachada sobre o novo store.
            sistema.fechar()
            sistema = AtendimentoComMemoria(memoria,modelo=modelo,cliente_cep=None if modo=='real' else criar_cliente_dummy())
            nova = memoria.abrir_sessao('cliente_A_demo')
            r = turno('nova_sessao_perfil_e_resumo','cliente_A_demo',nova,
                      'Qual carro está salvo e o que sabe sobre meus percursos urbanos?',('Celta','2012'))
            recuperou = bool(r['memoria_utilizada']['recuperacao']['resumos'])
            turno('outro_cliente_sem_vazamento','cliente_B_demo',b,'Qual é o meu carro?',proibidos=('Fusca','Celta','S10'))
            sistema.confirmar_veiculo('cliente_A_demo',nova,'V005')
            nova2 = memoria.abrir_sessao('cliente_A_demo')
            turno('correcao_persistida','cliente_A_demo',nova2,'Qual é meu veículo atual confirmado?',('S10','2014'),('Celta',))
            memoria.esquecer('cliente_A_demo')
            turno('apos_exclusao','cliente_A_demo',nova2,'Qual é meu carro?',proibidos=('Fusca','Celta','S10'))
            return {'modo':modo,'modelos_simulados':modo=='simulado','resumos':'explicitamente confirmados; não extraídos automaticamente por LLM',
                    'persistencia_processo_separado':persistencia,
                    'persistencia_ok':persistencia['A']['veiculo_confirmado']['id']=='V003' and persistencia['B'] is None,
                    'recuperacao_vetorial_executada':recuperou,'casos':registros}
        finally:
            sistema.fechar()
            if memoria:
                memoria.fechar()
