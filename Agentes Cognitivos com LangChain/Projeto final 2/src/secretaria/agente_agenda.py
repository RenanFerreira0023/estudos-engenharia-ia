"""Agente opcional para consultas e propostas de visita; confirmação fica fora do LLM."""
import os
from pathlib import Path


def criar_ferramentas_agenda(caminho_banco, ctx):
    """Cada chamada usa conexão própria: LangGraph pode executar @tool em outra thread."""
    from langchain_core.tools import tool
    from .banco import Banco
    from .agenda import Agenda, consultar_cep, consultar_cnpj

    caminho_banco = Path(caminho_banco)

    # @TOOL: leitura exata no SQLite antes de qualquer consulta externa ou proposta.
    @tool
    def buscar_cliente(termo: str) -> list[dict] | dict:
        """Busca clientes existentes por nome ou CNPJ na empresa do usuário atual."""
        try:
            with Banco(caminho_banco) as conexao:
                return Agenda(conexao).buscar_cliente(ctx,termo)
        except ValueError as erro:
            return {'status':'termo_necessario','mensagem':str(erro)}

    @tool
    def consultar_disponibilidade(inicio_iso: str, fim_iso: str, atendente_id: str = '') -> dict:
        """Verifica conflitos para o usuário atual por padrão; informe outro ID só se solicitado explicitamente."""
        try:
            with Banco(caminho_banco) as conexao:
                return Agenda(conexao).consultar_disponibilidade(ctx,atendente_id or ctx.usuario_id,inicio_iso,fim_iso)
        except (ValueError,PermissionError) as erro:
            return {'status':'dados_invalidos','mensagem':str(erro)}

    @tool
    def consultar_cep_viacep(cep: str) -> dict:
        """Consulta endereço no ViaCEP real quando a visita exige novo local; não fornece número."""
        try:
            return consultar_cep(cep)
        except ValueError as erro:
            return {'status':'falha','mensagem':str(erro)}

    @tool
    def consultar_cnpj_minha_receita(cnpj: str) -> dict:
        """Consulta banco local primeiro; só chama Minha Receita se o CNPJ não estiver cadastrado."""
        try:
            with Banco(caminho_banco) as conexao:
                existentes = [cliente for cliente in Agenda(conexao).buscar_cliente(ctx,cnpj)
                              if cliente['cnpj'] == ''.join(caractere for caractere in cnpj if caractere.isdigit())]
            if existentes:
                return {'status':'ja_cadastrado','origem':'banco_local','api_externa_chamada':False,
                        'cliente':existentes[0]}
            cadastro = consultar_cnpj(cnpj)
            with Banco(caminho_banco) as conexao:
                consulta_id = Agenda(conexao).registrar_consulta_cnpj(ctx,cadastro)
            return {'status':'nao_cadastrado','api_externa_chamada':True,
                    'consulta_id':consulta_id,'cadastro_externo_sugerido':cadastro,
                    'aviso':'Consulta salva para revisão; cliente ainda não cadastrado.'}
        except ValueError as erro:
            return {'status':'falha','mensagem':str(erro)}

    @tool
    def propor_cadastro_cliente(consulta_id: int) -> dict:
        """Propõe cadastro PJ da consulta salva do usuário atual; não grava cliente."""
        try:
            with Banco(caminho_banco) as conexao:
                return Agenda(conexao).propor_cadastro_cliente(ctx,consulta_id)
        except (ValueError,PermissionError) as erro:
            return {'status':'dados_invalidos','mensagem':str(erro)}

    @tool
    def propor_visita(cliente_id: int, inicio_iso: str, fim_iso: str,
                      logradouro: str, numero: str, cidade: str, uf: str,
                      atendente_id: str = '', cep: str = '') -> dict:
        """Cria proposta pendente para o usuário atual por padrão; não confirma compromisso."""
        try:
            with Banco(caminho_banco) as conexao:
                return Agenda(conexao).propor_visita(ctx,cliente_id,inicio_iso,fim_iso,
                    {'logradouro':logradouro,'numero':numero,'cidade':cidade,'uf':uf,
                     'cep':cep,'origem':'informado_pelo_usuario_e_viacep' if cep else 'informado_pelo_usuario'},
                    atendente_id or ctx.usuario_id)
        except (ValueError,PermissionError) as erro:
            return {'status':'dados_invalidos','mensagem':str(erro)}

    return [buscar_cliente,consultar_disponibilidade,consultar_cep_viacep,
            consultar_cnpj_minha_receita,propor_cadastro_cliente,propor_visita]


def montar_prompt_agenda(usuario_id):
    """Prompt versionável: regras do domínio e exemplos sem depender da API."""
    # SYSTEM_PROMPT / PTCF: Pessoa, Tarefa, Contexto e Formato organizam as instruções.
    # FEW-SHOT: exemplos curtos mostram a distinção entre consultar, propor e confirmar.
    return f'''[PESSOA]
Você é a secretária acadêmica da empresa demo. Usuário atual e atendente padrão: {usuario_id}.
[TAREFA]
Entenda o pedido, consulte ferramentas quando necessário e responda somente com fatos sustentados. A rota sugerida no pedido ajuda a organizar o atendimento, mas não substitui sua análise nem autoriza ações.
[CONTEXTO E REGRAS]
Data/hora atual com fuso: use a informação de tempo recebida no pedido; se não houver, peça data absoluta.
Para pergunta sobre cadastro de cliente identificado por nome ou CNPJ, chame buscar_cliente primeiro. Se o usuário perguntar "qual cliente mencionei?", use somente a conversa atual; se não houver cliente mencionado nela, diga que não sabe e peça o nome. Não busque todos os clientes para adivinhar o referente. Um retorno da Minha Receita não prova cadastro local. Se nenhum ou vários, peça identificação; nunca invente ID.
Só consulte Minha Receita para CNPJ que não existe no banco. A ferramenta de CNPJ verifica isso novamente e devolve status ja_cadastrado ou nao_cadastrado. Responda "cadastrado" apenas quando o banco local confirmar.
Se o usuário pedir cadastro de um CNPJ novo, consulte-o e chame propor_cadastro_cliente com o consulta_id retornado. Mostre razão social, CNPJ, nome fantasia e proposta_id. A consulta e a proposta não criam cliente. Oriente o usuário a confirmar com /confirmar-cliente ID; você não tem ferramenta de confirmação.
Se o pedido não citar outro atendente, use {usuario_id}; não peça seu ID. Consulte disponibilidade antes de propor. Peça duração, tipo/local e endereço completo.
Quando a consulta retornar sem_conflito_registrado=true, diga "não há compromisso registrado nesse intervalo"; não afirme disponibilidade garantida.
Para endereço novo com CEP, consulte ViaCEP; ele não traz número. Use o número que o usuário informou antes ou depois da consulta. "s/n" significa sem número e é um valor válido quando confirmado pelo usuário; não peça o número novamente nesse caso. Inclua o CEP consultado na proposta.
Nunca chame propor_visita sem dados completos. Não diga que proposta é reserva.
Não confirme agendamento: confirmação explícita ocorre no terminal por ID, fora do modelo.
Não invente pagamentos, horário de expediente ou dados de outra pessoa.
[EXEMPLOS]
Usuário: "Qual cliente mencionei?" sem cliente na conversa atual.
Resposta: "Ainda não sei qual cliente você mencionou nesta conversa. Pode informar o nome?"
Usuário: "O CNPJ 33683111000280 está cadastrado?"
Ação: consultar cadastro local pela ferramenta; somente responder "cadastrado" se a ferramenta confirmar.
Usuário: "Agende uma visita ao cliente Alfa amanhã às 14h."
Resposta: solicitar data absoluta ou dados obrigatórios ausentes antes de propor; não dizer que foi confirmado.
[FORMATO]
Responda em português claro e curto. Diga o que foi encontrado, o que falta e, se houver proposta, seu ID e estado. Não exponha raciocínio interno; chamadas e retornos de ferramenta são registrados pelo executor para auditoria.'''


def criar_agente_agenda(banco, ctx, arquivo_env=None):
    from dotenv import dotenv_values
    from langchain.agents import create_agent
    from langchain_openai import ChatOpenAI

    chave = os.environ.get('OPENAI_API_KEY')
    if not chave:
        if arquivo_env:
            candidatos = [Path(arquivo_env)]
        else:
            projeto = Path(__file__).resolve().parents[2]
            candidatos = [projeto/'.env', projeto.parents[1]/'.env']
        for arquivo in candidatos:
            if arquivo.is_file():
                chave = dotenv_values(arquivo,encoding='utf-8').get('OPENAI_API_KEY')
                if chave:
                    break
    if not chave:
        raise ValueError('Configure OPENAI_API_KEY no ambiente ou .env deste projeto.')

    # CHATOPENAI + CREATE_AGENT: o modelo decide quando chamar @tool.
    # Serviços Python validam identidade, escopo e gravação; o prompt não concede permissões.
    modelo = ChatOpenAI(model='gpt-4o-mini',api_key=chave,temperature=0,max_retries=0,timeout=45)
    sistema = montar_prompt_agenda(ctx.usuario_id)
    return create_agent(modelo,criar_ferramentas_agenda(banco.caminho,ctx),
                        system_prompt=sistema)
