"""Interface local da Secretária IA: streamlit run app.py."""
from datetime import datetime, timedelta
from pathlib import Path
import json
import os
import sys
import tempfile
from uuid import uuid4
from zoneinfo import ZoneInfo

import streamlit as st

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / 'src'))
from secretaria.agenda import Agenda, consultar_cep
from secretaria.banco import Banco, Contexto
from secretaria.financeiro import Financeiro
from secretaria.fila_revisao import FilaRevisao
from secretaria.memoria import MemoriaConversas
from secretaria.terminal_financeiro import centavos, moeda

BANCO = Path(os.environ.get('SECRETARIA_BANCO', str(RAIZ / 'dados/privados/secretaria.sqlite3')))
FUSO = ZoneInfo('America/Sao_Paulo')


def abrir():
    banco = Banco(BANCO)
    banco.preparar_demo()
    return banco


def exibir_erro(erro):
    st.error(f'Operação não concluída: {erro}')


st.set_page_config(page_title='Secretária IA', page_icon='📋', layout='wide')
st.title('Secretária IA')
st.caption('Projeto acadêmico • dados locais no SQLite • identidade de demonstração')

usuario = st.sidebar.selectbox('Usuário de demonstração', ['ana', 'bruno', 'carla'])
ctx = Contexto('demo', usuario)
if st.session_state.get('usuario_atual') != usuario:
    st.session_state['usuario_atual'] = usuario
    st.session_state.pop('sessao_atual', None)
    st.session_state.pop('previa_aplicacao', None)
    st.session_state.pop('chave_pagamento', None)
with abrir() as banco:
    memoria = MemoriaConversas(banco)
    if 'sessao_atual' not in st.session_state:
        st.session_state['sessao_atual'] = memoria.ultima_ativa(ctx) or memoria.iniciar(ctx)
sessao = st.session_state['sessao_atual']
st.sidebar.caption(f'Conversa: {sessao[:12]}')
st.sidebar.info('A escolha de usuário é só para testar permissões. Não é autenticação.')

aba_chat, aba_fontes, aba_revisao, aba_agenda, aba_financeiro = st.tabs(
    ['Conversa', 'Fontes', 'Revisão', 'Agenda', 'Financeiro'])

with aba_chat:
    if st.button('Nova conversa'):
        with abrir() as banco:
            memoria = MemoriaConversas(banco)
            memoria.encerrar(ctx, sessao)
            st.session_state['sessao_atual'] = memoria.iniciar(ctx)
        st.rerun()
    with abrir() as banco:
        memoria = MemoriaConversas(banco)
        memoria._sessao(ctx, sessao)
        turnos = banco.con.execute(
            '''SELECT pergunta,resposta FROM turnos_agente WHERE empresa_id=?
               AND usuario_id=? AND sessao_id=? ORDER BY id''',
            (ctx.empresa_id, ctx.usuario_id, sessao)).fetchall()
    for turno in turnos:
        with st.chat_message('user'):
            st.write(turno['pergunta'])
        with st.chat_message('assistant'):
            st.write(turno['resposta'])
    pergunta = st.chat_input('Peça uma consulta ou proposta')
    if pergunta:
        with st.chat_message('user'):
            st.write(pergunta)
        with st.chat_message('assistant'):
            try:
                from secretaria.atendimento_web import responder_turno
                with abrir() as banco, st.spinner('Consultando...'):
                    resultado = responder_turno(banco, ctx, sessao, pergunta)
                st.write(resultado['resposta'])
                st.caption('Rota: ' + resultado['rota'] + ' | Ferramentas: '
                           + (', '.join(resultado['ferramentas']) or 'nenhuma')
                           + ' | Eventos: ' + str(resultado['eventos'])
                           + ' | Verificação: ' + resultado['verificacao']['estado'])
            except Exception as erro:
                exibir_erro(erro)
    st.caption('Confirmar visita ou cliente exige ação explícita na aba Agenda. O agente só propõe.')

with aba_fontes:
    st.subheader('Conversas importadas')
    with abrir() as banco:
        corpora = [dict(r) for r in banco.con.execute(
            'SELECT id,nome,criado_por FROM corpora WHERE empresa_id=? AND criado_por=? ORDER BY id',
            (ctx.empresa_id, ctx.usuario_id))]
    st.dataframe(corpora, hide_index=True)
    if st.button('Importar demonstração fictícia'):
        try:
            with abrir() as banco:
                corpus = banco.selecionar_corpus(ctx, 'Demonstração fictícia')
                resultado = banco.importar(ctx, corpus, RAIZ / 'dados/ficticios/conversa_empresa.txt')
            st.success(f'Importação concluída: {resultado}')
        except (ValueError, OSError, PermissionError) as erro:
            exibir_erro(erro)
    with st.form('importar_arquivo'):
        nome = st.text_input('Nome do corpus privado')
        arquivo = st.file_uploader('WhatsApp TXT ou ZIP', type=['txt', 'zip'])
        enviar = st.form_submit_button('Importar arquivo local')
    if enviar:
        if not arquivo or not nome.strip() or nome.strip() == 'Demonstração fictícia':
            st.error('Informe arquivo e nome próprio para o corpus privado.')
        else:
            temporario = None
            try:
                (RAIZ / 'dados/privados').mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=RAIZ / 'dados/privados',
                                                  suffix=Path(arquivo.name).suffix, delete=False) as tmp:
                    tmp.write(arquivo.getvalue())
                    temporario = Path(tmp.name)
                with abrir() as banco:
                    corpus = banco.selecionar_corpus(ctx, nome.strip())
                    resultado = banco.importar(ctx, corpus, temporario)
                st.success(f'Importação concluída: {resultado}')
            except (ValueError, OSError, PermissionError) as erro:
                exibir_erro(erro)
            finally:
                if temporario and temporario.exists():
                    temporario.unlink()
    st.caption('A importação é local. A indexação de fontes exige confirmação separada abaixo.')
    if corpora:
        with st.form('preparar_indice'):
            corpus_indice = st.selectbox('Corpus a indexar', corpora,
                                         format_func=lambda c: f"#{c['id']} {c['nome']}")
            autoriza_envio = st.checkbox('Autorizo enviar os textos deste corpus à OpenAI para gerar embeddings')
            if st.form_submit_button('Preparar índice de fontes'):
                if not autoriza_envio:
                    st.error('Confirme o envio antes de indexar.')
                else:
                    try:
                        from langchain_openai import OpenAIEmbeddings
                        from secretaria.agente_agenda import obter_chave_api
                        from secretaria.indice_fontes import IndiceFontes, pasta_indice_do_banco
                        with abrir() as banco:
                            embeddings = OpenAIEmbeddings(model='text-embedding-3-small',
                                api_key=obter_chave_api(), max_retries=0, timeout=45)
                            resultado = IndiceFontes(banco, pasta_indice_do_banco(banco)).preparar(
                                ctx, corpus_indice['id'], embeddings, 'text-embedding-3-small')
                        st.success(resultado)
                    except Exception as erro:
                        exibir_erro(erro)

with aba_revisao:
    st.subheader('Interpretações pendentes')
    if st.button('Gerar propostas da demonstração fictícia, sem LLM'):
        try:
            from secretaria.extracao import analisar_demonstracao
            from secretaria.fixtures_extracao import criar_modelo_fixture
            with abrir() as banco:
                analise = analisar_demonstracao(banco, ctx, criar_modelo_fixture(), 'fixture_manual')
                fila_nova = FilaRevisao(banco).registrar_resultado(ctx, analise)
            st.success(f"Propostas novas: {fila_nova['novas']}; origem: fixture manual.")
            st.rerun()
        except (ValueError, PermissionError) as erro:
            exibir_erro(erro)
    if st.button('Gerar propostas OpenAI da demonstração fictícia'):
        try:
            from secretaria.chain_extracao import criar_modelo
            from secretaria.extracao import analisar_demonstracao
            with abrir() as banco, st.spinner('Analisando somente a demonstração fictícia...'):
                analise = analisar_demonstracao(banco, ctx, criar_modelo(), 'api_real')
                fila_nova = FilaRevisao(banco).registrar_resultado(ctx, analise)
            st.success(f"Propostas novas: {fila_nova['novas']}; lotes: {analise['status']}.")
            st.rerun()
        except Exception as erro:
            exibir_erro(erro)
    with abrir() as banco:
        propostas = FilaRevisao(banco).listar(ctx)
    if not propostas:
        st.info('Sem propostas acessíveis. Gere propostas fictícias ou OpenAI no terminal (opções 4/5).')
    for proposta in propostas:
        with st.expander(f"#{proposta['id']} • {proposta['estado']} • {proposta['dados']['area']} • "
                         f"{proposta['dados']['projeto']} • v{proposta['versao']}"):
            st.json(proposta['dados'])
            if proposta['estado'] == 'pendente':
                with st.form(f"revisar_{proposta['id']}"):
                    decisao = st.radio('Decisão', ['aceitar', 'rejeitar', 'corrigir'], horizontal=True)
                    comentario = st.text_input('Comentário da revisão')
                    correcao = st.text_area('Correção JSON, somente se corrigir', value='{}')
                    if st.form_submit_button('Salvar revisão'):
                        try:
                            with abrir() as banco:
                                fila = FilaRevisao(banco)
                                if decisao == 'corrigir':
                                    resultado = fila.corrigir(ctx, proposta['id'], proposta['versao'],
                                                              json.loads(correcao), comentario)
                                else:
                                    resultado = fila.decidir(ctx, proposta['id'], proposta['versao'],
                                                             decisao, comentario)
                            st.success(f"Revisão salva: {resultado['estado']} v{resultado['versao']}")
                            st.rerun()
                        except (ValueError, PermissionError) as erro:
                            exibir_erro(erro)
    aceitas = [p for p in propostas if p['estado'] == 'aceita']
    if aceitas:
        st.subheader('Aplicar interpretação aceita ao projeto')
        with st.form('prever_aplicacao'):
            escolhida = st.selectbox('Interpretação aceita', aceitas,
                format_func=lambda p: f"#{p['id']} {p['dados']['area']} • {p['dados']['projeto']}")
            vinculo = st.text_input('ID do projeto existente; se a interpretação cria projeto, deixe vazio')
            cliente_vinculo = st.text_input('ID do cliente para novo projeto, se conhecido')
            if st.form_submit_button('Conferir prévia'):
                try:
                    from secretaria.projetos_fontes import ProjetosFontes
                    projeto_id = int(vinculo) if vinculo.strip() else None
                    cliente_id = int(cliente_vinculo) if cliente_vinculo.strip() else None
                    with abrir() as banco:
                        previa = ProjetosFontes(banco).prever(ctx, escolhida['id'],
                                                              projeto_id, cliente_id)
                    st.session_state['previa_aplicacao'] = {
                        'proposta_id': escolhida['id'], 'projeto_id': projeto_id,
                        'cliente_id': cliente_id, 'dados': previa}
                except (ValueError, PermissionError) as erro:
                    exibir_erro(erro)
        previa_atual = st.session_state.get('previa_aplicacao')
        if previa_atual:
            st.json(previa_atual['dados'])
            if st.button('Confirmar gravação da prévia exibida'):
                try:
                    from secretaria.projetos_fontes import ProjetosFontes
                    with abrir() as banco:
                        resultado = ProjetosFontes(banco).confirmar(
                            ctx, previa_atual['proposta_id'], previa_atual['dados']['versao'],
                            previa_atual['projeto_id'], previa_atual['cliente_id'])
                    st.session_state.pop('previa_aplicacao', None)
                    st.success(resultado)
                except (ValueError, PermissionError) as erro:
                    exibir_erro(erro)

with aba_agenda:
    st.subheader('Minha agenda')
    with abrir() as banco:
        st.dataframe(Agenda(banco).listar_agenda(ctx), hide_index=True)
        clientes = [dict(r) for r in banco.con.execute(
            'SELECT id,nome FROM clientes WHERE empresa_id=? ORDER BY nome', (ctx.empresa_id,))]
    with st.form('confirmar_cliente'):
        cliente_proposta_id = st.number_input('ID da proposta de cadastro PJ', min_value=1, step=1)
        if st.form_submit_button('Confirmar cadastro PJ proposto'):
            try:
                with abrir() as banco:
                    resultado = Agenda(banco).confirmar_cadastro_cliente(ctx, int(cliente_proposta_id))
                st.success(resultado)
            except (ValueError, PermissionError) as erro:
                exibir_erro(erro)
    with st.form('cadastrar_cliente_manual'):
        st.caption('Cadastro manual de demonstração; CNPJ informado aqui não é verificado por API.')
        nome_cliente = st.text_input('Nome do novo cliente')
        tipo_cliente = st.selectbox('Tipo de cliente', ['PF', 'PJ'])
        cnpj_cliente = st.text_input('CNPJ, se PJ')
        if st.form_submit_button('Cadastrar cliente manualmente'):
            try:
                with abrir() as banco:
                    cliente_id = Agenda(banco).cadastrar_cliente(
                        ctx, nome_cliente, tipo_cliente, cnpj_cliente or None)
                st.success(f'Cliente cadastrado: #{cliente_id}')
            except (ValueError, PermissionError) as erro:
                exibir_erro(erro)
    if clientes:
        with st.form('propor_visita'):
            cliente = st.selectbox('Cliente cadastrado', clientes,
                                   format_func=lambda c: f"#{c['id']} {c['nome']}")
            dia = st.date_input('Data')
            hora = st.time_input('Início')
            duracao = st.number_input('Duração (minutos)', min_value=1, max_value=720, value=60)
            cep = st.text_input('CEP (opcional)')
            logradouro = st.text_input('Logradouro (se não usar CEP)')
            numero = st.text_input('Número ou s/n')
            cidade = st.text_input('Cidade (se não usar CEP)')
            uf = st.text_input('UF (se não usar CEP)')
            if st.form_submit_button('Criar proposta, sem reservar'):
                try:
                    endereco = {'logradouro': logradouro.strip(), 'numero': numero.strip(),
                                'cidade': cidade.strip(), 'uf': uf.strip().upper()}
                    if cep.strip():
                        dados = consultar_cep(cep.strip())
                        endereco.update({'logradouro': dados['logradouro'],
                                         'cidade': dados['localidade'], 'uf': dados['uf'],
                                         'cep': dados['cep'], 'origem': dados['origem']})
                    inicio = datetime.combine(dia, hora, FUSO)
                    fim = inicio + timedelta(minutes=int(duracao))
                    with abrir() as banco:
                        agenda = Agenda(banco)
                        if not agenda.consultar_disponibilidade(ctx, ctx.usuario_id, inicio, fim)['sem_conflito_registrado']:
                            raise ValueError('Já existe compromisso registrado neste intervalo.')
                        proposta = agenda.propor_visita(ctx, cliente['id'], inicio, fim, endereco)
                    st.success(f"Proposta #{proposta['proposta_id']} pendente. Confirme abaixo pelo ID.")
                except (ValueError, KeyError, PermissionError) as erro:
                    exibir_erro(erro)
    else:
        st.info('Cadastre um cliente acima antes de propor a visita.')
    with st.form('confirmar_visita'):
        proposta_id = st.number_input('ID da proposta de visita', min_value=1, step=1)
        if st.form_submit_button('Confirmar visita no banco'):
            try:
                with abrir() as banco:
                    resultado = Agenda(banco).confirmar_visita(ctx, int(proposta_id))
                st.success(resultado)
            except (ValueError, PermissionError) as erro:
                exibir_erro(erro)

with aba_financeiro:
    st.subheader('Financeiro operacional')
    try:
        with abrir() as banco:
            relatorio = Financeiro(banco).relatorio(ctx)
        for projeto in relatorio['projetos']:
            with st.expander(f"#{projeto['projeto_id']} {projeto['projeto']} • saldo {moeda(projeto['saldo_centavos'])}"):
                st.write('Orçamento aceito:', moeda(projeto['valor_aceito_centavos']))
                st.write('Recebido confirmado:', moeda(projeto['recebido_confirmado_centavos']))
                st.dataframe(projeto['parcelas'], hide_index=True)
        if not relatorio['projetos']:
            st.info('Sem projetos operacionais; aplique uma interpretação aceita no terminal (opção 10).')
        with st.form('propor_orcamento'):
            projeto_id = st.number_input('ID do projeto', min_value=1, step=1)
            valor = st.text_input('Valor do orçamento, ex.: 10000,00')
            percentual = st.number_input('Entrada acordada (%)', min_value=0, max_value=100, value=0)
            if st.form_submit_button('Propor orçamento'):
                with abrir() as banco:
                    resultado = Financeiro(banco).criar_orcamento(
                        ctx, int(projeto_id), centavos(valor), int(percentual))
                st.success(resultado)
        with st.form('aceitar_orcamento'):
            orcamento_id = st.number_input('ID do orçamento proposto', min_value=1, step=1)
            if st.form_submit_button('Aceitar orçamento'):
                with abrir() as banco:
                    resultado = Financeiro(banco).aceitar_orcamento(ctx, int(orcamento_id))
                st.success(resultado)
        with st.form('definir_parcelas'):
            orcamento_parcelas = st.number_input('ID do orçamento aceito', min_value=1, step=1)
            parcelas_json = st.text_area('Parcelas JSON', value='[{"descricao":"Entrada","valor_centavos":300000,"vencimento":"2026-11-20"},{"descricao":"Restante","valor_centavos":700000}]')
            st.caption('Os valores de cada parcela estão em centavos; a soma deve igualar o orçamento.')
            if st.form_submit_button('Gravar parcelas'):
                with abrir() as banco:
                    resultado = Financeiro(banco).definir_parcelas(
                        ctx, int(orcamento_parcelas), json.loads(parcelas_json))
                st.success(resultado)
        with st.form('informar_pagamento'):
            parcela_id = st.number_input('ID da parcela', min_value=1, step=1)
            valor_pago = st.text_input('Valor informado, ex.: 3000,00')
            dia_pagamento = st.date_input('Data informada do pagamento', key='data_pagamento')
            observacao = st.text_input('Observação do relato')
            st.session_state.setdefault('chave_pagamento', uuid4().hex)
            st.caption('Chave do lançamento atual: ' + st.session_state['chave_pagamento'][:12])
            if st.form_submit_button('Informar pagamento, sem contabilizar'):
                with abrir() as banco:
                    resultado = Financeiro(banco).informar_pagamento(
                        ctx, int(parcela_id), centavos(valor_pago), dia_pagamento.isoformat(),
                        st.session_state['chave_pagamento'], observacao)
                st.success(resultado)
        if st.button('Novo lançamento de pagamento'):
            st.session_state['chave_pagamento'] = uuid4().hex
            st.rerun()
        with st.form('confirmar_pagamento'):
            pagamento_id = st.number_input('ID do pagamento conferido', min_value=1, step=1)
            concordo = st.checkbox('Conferi o recebimento; quero contabilizá-lo')
            if st.form_submit_button('Confirmar pagamento'):
                if not concordo:
                    raise ValueError('Marque a conferência explícita antes de confirmar.')
                with abrir() as banco:
                    resultado = Financeiro(banco).confirmar_pagamento(ctx, int(pagamento_id))
                st.success(resultado)
        with st.form('substituir_orcamento'):
            novo_id = st.number_input('ID da nova revisão proposta', min_value=1, step=1)
            motivo_substituicao = st.text_input('Motivo da substituição')
            if st.form_submit_button('Substituir orçamento ativo'):
                with abrir() as banco:
                    resultado = Financeiro(banco).substituir_orcamento(
                        ctx, int(novo_id), motivo_substituicao)
                st.success(resultado)
        with st.form('reverter_pagamento'):
            reversao_id = st.number_input('ID do pagamento a cancelar ou estornar', min_value=1, step=1)
            motivo_reversao = st.text_input('Motivo da reversão')
            if st.form_submit_button('Registrar reversão auditada'):
                with abrir() as banco:
                    resultado = Financeiro(banco).reverter_pagamento(
                        ctx, int(reversao_id), motivo_reversao)
                st.success(resultado)
    except (ValueError, PermissionError) as erro:
        exibir_erro(erro)
