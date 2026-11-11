"""Terminal dos marcos 1/2 e fila de revisão: importação e propostas; modo demonstração sem autenticação."""
import argparse
import json
from pathlib import Path
from .banco import Banco,Contexto


def localizar_projeto():
    for p in Path(__file__).resolve().parents:
        if (p/'PLANO_PROJETO_SECRETARIA_IA.md').is_file() and (p/'src/secretaria').is_dir():
            return p
    raise ValueError('Projeto não localizado. Copie a pasta completa.')


def exibir_conceitos_estudados():
    print('[estudo] Importação/listagem são locais; análise é opcional por fixture ou LLM.')
    print('[estudo] SQLite preserva fontes; transação e hash tornam a reimportação idempotente.')
    print('[estudo] Opção 6 revisa interpretações com versão e histórico; não aplica registros operacionais.')
    print('[estudo] Usuário de demonstração identifica o importador; isso não é autenticação real.')


def exibir_ferramentas_do_turno(mensagens):
    """Associa cada retorno ao ID da chamada, inclusive quando o agente chama em paralelo."""
    chamadas = [chamada for mensagem in mensagens
                for chamada in getattr(mensagem,'tool_calls',[])]
    retornos = {mensagem.tool_call_id: mensagem for mensagem in mensagens
                if getattr(mensagem,'type',None)=='tool'}
    print('\nFERRAMENTAS CONSULTADAS')
    if not chamadas:
        print('Nenhuma ferramenta chamada neste turno.')
    for chamada in chamadas:
        print('\nCHAMADA:',chamada['name'])
        print('Argumentos:',json.dumps(chamada['args'],ensure_ascii=False))
        retorno_mensagem = retornos.get(chamada.get('id'))
        if retorno_mensagem is None:
            print('RETORNO: não registrado')
            continue
        try:
            retorno = json.loads(retorno_mensagem.content)
        except (TypeError,ValueError):
            retorno = None
        if isinstance(retorno,dict) and retorno.get('status'):
            print('STATUS:',str(retorno['status']).upper())
        print('Retorno:',retorno_mensagem.content)


def _consulta_estruturada_comprovada(mensagem, exige_contagem=False):
    if getattr(mensagem,'type',None) != 'tool':
        return False
    try:
        retorno = json.loads(mensagem.content)
    except (TypeError,ValueError):
        return False
    if not isinstance(retorno,dict) or retorno.get('status') != 'ok':
        return False
    if exige_contagem:
        return retorno.get('plano',{}).get('tipo') == 'contagem' and type(retorno.get('total')) is int
    return (retorno.get('plano',{}).get('tipo') in ('contagem','lista')
            and ('total' in retorno or 'mensagens' in retorno))


def agendar_no_terminal(banco, ctx):
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from .agenda import Agenda, consultar_cep, consultar_cnpj
    agenda = Agenda(banco)
    print('VISITA — proposta e confirmação. Usuário de demonstração:', ctx.usuario_id)
    termo = input('Cliente (nome ou CNPJ): ').strip()
    encontrados = agenda.buscar_cliente(ctx, termo)
    if len(encontrados) > 1:
        print('Mais de um cliente encontrado:', encontrados)
        print('Informe nome/CNPJ mais específico.')
        return
    if encontrados:
        cliente_id = encontrados[0]['id']
        print('Cliente encontrado no banco:', encontrados[0]['nome'])
    else:
        print('Cliente não encontrado. Informe PF/PJ; para PJ, consultaremos o CNPJ antes de propor o cadastro.')
        nome = input('Nome completo do cliente: ').strip()
        tipo = input('Tipo PF ou PJ: ').strip().upper()
        cnpj = input('CNPJ (se PJ; deixe vazio se desconhecido): ').strip() or None
        cadastro = None
        if tipo == 'PJ' and not cnpj:
            print('Informe o CNPJ para consultar o cadastro PJ; não vou adivinhar a empresa.')
            return
        if tipo == 'PJ':
            existentes = [c for c in agenda.buscar_cliente(ctx,cnpj) if c['cnpj'] == ''.join(x for x in cnpj if x.isdigit())]
            if existentes:
                cliente_id = existentes[0]['id']
                print('Cliente PJ já cadastrado; consulta externa dispensada:',existentes[0]['nome'])
                nome = None
            else:
                try:
                    cadastro = consultar_cnpj(cnpj)
                    print('Minha Receita:',cadastro)
                    nome = cadastro['razao_social']
                except ValueError as erro:
                    print(erro,'Nome informado manualmente; origem da API não confirmada.')
        if nome is None:
            pass
        elif input('Confirmar cadastro local? [s/N] ').strip().lower() != 's':
            return
        else:
            cliente_id = agenda.cadastrar_cliente(ctx,nome,tipo,cnpj,cadastro_api=cadastro)
    atendente = input(f'Atendente [{ctx.usuario_id}]: ').strip() or ctx.usuario_id
    inicio = input('Início (AAAA-MM-DD HH:MM, horário de São Paulo): ').strip()
    duracao_texto = input('Duração em minutos: ').strip()
    if not duracao_texto.isdecimal() or not 1 <= int(duracao_texto) <= 720:
        raise ValueError('Informe duração em minutos de 1 a 720, por exemplo 60.')
    duracao = int(duracao_texto)
    try:
        local = datetime.strptime(inicio,'%Y-%m-%d %H:%M').replace(tzinfo=ZoneInfo('America/Sao_Paulo'))
    except ValueError as erro:
        raise ValueError('Informe o início como AAAA-MM-DD HH:MM, por exemplo 2026-11-11 14:00.') from erro
    fim = local + timedelta(minutes=duracao)
    livre = agenda.consultar_disponibilidade(ctx,atendente,local,fim)
    print(livre)
    if not livre['sem_conflito_registrado']:
        return
    cep = input('CEP da visita (8 dígitos; Enter para informar manualmente): ').strip()
    endereco = {}
    if cep:
        try:
            endereco = consultar_cep(cep)
            print('ViaCEP:', endereco)
        except ValueError as erro:
            print(erro)
    endereco = {'logradouro':endereco.get('logradouro') or input('Logradouro: ').strip(),
                'numero':input('Número (ou s/n confirmado): ').strip(),
                'cidade':endereco.get('localidade') or input('Cidade: ').strip(),
                'uf':endereco.get('uf') or input('UF: ').strip(),
                'cep':endereco.get('cep') or cep,
                'origem':endereco.get('origem') or 'informado_manualmente'}
    proposta = agenda.propor_visita(ctx,cliente_id,local,fim,endereco,atendente)
    print(json.dumps(proposta,ensure_ascii=False,indent=2))
    if input('Confirmar esta visita no banco? [s/N] ').strip().lower() == 's':
        print(agenda.confirmar_visita(ctx,proposta['proposta_id']))
    else:
        print('Proposta pendente; nenhum horário reservado.')


def conversar_sobre_visita(banco, ctx, arquivo_env=None):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from openai import APIConnectionError, AuthenticationError, RateLimitError, OpenAIError
    from .agente_agenda import criar_agente_agenda, obter_chave_api
    from .memoria import MemoriaConversas, pede_contexto_antigo
    from .preferencias import PreferenciasUsuario
    from .observabilidade import RastroAgente
    from .roteamento import roteador_pedido
    agente = None
    embeddings = None
    memoria = MemoriaConversas(banco)
    preferencias = PreferenciasUsuario(banco)
    sessao_id = memoria.ultima_ativa(ctx) or memoria.iniciar(ctx)
    print('Agente com ferramentas. Conversa:',sessao_id)
    print('/nova inicia outra conversa; /lembrar estilo=curto; /memorias lista; /esquecer-memoria estilo apaga; /voltar sai.')
    print('/confirmar ID confirma visita; /confirmar-cliente ID confirma cadastro PJ.')
    while True:
        try:
            pergunta = input('Você: ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nConversa preservada. Use a opção 9 para retomá-la.')
            return
        if pergunta == '/voltar':
            return
        if pergunta == '/nova':
            memoria.encerrar(ctx,sessao_id)
            sessao_id = memoria.iniciar(ctx)
            print('Nova conversa:',sessao_id)
            continue
        if pergunta == '/memorias':
            print('Preferências confirmadas:',json.dumps(preferencias.listar(ctx),ensure_ascii=False))
            continue
        if pergunta.startswith('/lembrar '):
            try:
                chave, valor = pergunta[len('/lembrar '):].split('=',1)
                print('Preferência:',preferencias.salvar(ctx,chave.strip(),valor.strip().lower()))
            except (ValueError,PermissionError) as erro:
                print('Preferência não salva:',erro)
            continue
        if pergunta.startswith('/esquecer-memoria '):
            try:
                chave = pergunta[len('/esquecer-memoria '):].strip()
                print('Preferência:',preferencias.apagar(ctx,chave))
            except (ValueError,PermissionError) as erro:
                print('Preferência não apagada:',erro)
            continue
        if pergunta.startswith('/confirmar-cliente '):
            from .agenda import Agenda
            try:
                partes=pergunta.split()
                if len(partes)!=2:
                    raise ValueError('Use /confirmar-cliente ID.')
                print(Agenda(banco).confirmar_cadastro_cliente(ctx,int(partes[1])))
            except (ValueError,PermissionError) as erro:
                print('Cadastro não confirmado:',erro)
            continue
        if pergunta.startswith('/confirmar '):
            from .agenda import Agenda
            try:
                print(Agenda(banco).confirmar_visita(ctx,int(pergunta.split()[1])))
            except (ValueError,PermissionError) as erro:
                print('Não confirmado:',erro)
            continue
        if not pergunta:
            continue
        if agente is None:
            # CREATE_AGENT é adiado: comandos locais de memória funcionam sem chave de API.
            agente = criar_agente_agenda(banco,ctx,arquivo_env)
        agora = datetime.now(ZoneInfo('America/Sao_Paulo')).isoformat()
        # ROUTER + MEMÓRIA: a rota orienta o pedido; a janela fornece contexto recente.
        # Nenhuma das duas substitui as validações das ferramentas do agente.
        anteriores = memoria.ultimos(ctx,sessao_id)
        rota = roteador_pedido.invoke({'pergunta':pergunta,'anteriores':anteriores})['rota']
        historico = memoria.mensagens(ctx,sessao_id)
        # RECUPERAÇÃO: o SQLite limita a sessão/usuário antes da busca FAISS.
        # Embeddings da OpenAI recebem apenas recortes antigos que já seriam enviados ao chat.
        # Se a API falhar, a busca lexical local mantém a conversa funcional.
        ha_recortes = memoria.banco.con.execute(
            'SELECT 1 FROM resumos_turnos_agente WHERE sessao_id=? AND empresa_id=? AND usuario_id=? LIMIT 1',
            (sessao_id,ctx.empresa_id,ctx.usuario_id)).fetchone() is not None
        recuperados = []
        estrategia_recuperacao = 'não solicitada para este pedido'
        if ha_recortes and pede_contexto_antigo(pergunta):
            try:
                if embeddings is None:
                    from langchain_openai import OpenAIEmbeddings
                    embeddings = OpenAIEmbeddings(model='text-embedding-3-small',
                                                   api_key=obter_chave_api(arquivo_env),
                                                   max_retries=0,timeout=20)
                recuperados = memoria.buscar_resumos_vetoriais(ctx,sessao_id,pergunta,embeddings)
                estrategia_recuperacao = 'FAISS + embeddings' if recuperados else 'FAISS sem resultado'
            except (OpenAIError,ImportError,ValueError) as erro:
                recuperados = memoria.buscar_resumos(ctx,sessao_id,pergunta)
                estrategia_recuperacao = 'busca lexical local (falha na busca vetorial)'
                print('Aviso: busca vetorial indisponível:',type(erro).__name__)
        contexto_antigo = (' Trechos antigos da conversa, não confirmados: '
                           + json.dumps(recuperados,ensure_ascii=False) + '.') if recuperados else ''
        # MEMÓRIA CONFIRMADA: preferências enumeradas são do usuário atual e sobrevivem a /nova.
        # Não entram como cadastro, agenda ou autorização operacional.
        contexto_pessoal = json.dumps(preferencias.listar(ctx),ensure_ascii=False)
        # CALLBACK + INVOKE: os eventos mostram modelo/ferramenta sem guardar conteúdo no log.
        rastro = RastroAgente()
        try:
            resposta = agente.invoke({'messages':historico+[{'role':'user','content':f'Agora: {agora}. Rota sugerida: {rota}. Preferências confirmadas deste usuário: {contexto_pessoal}.{contexto_antigo} Pedido: {pergunta}'}]},
                                    {'recursion_limit':12,'callbacks':[rastro]})
        except AuthenticationError:
            print('A chave OPENAI_API_KEY foi recusada ou expirou. Gere outra chave e atualize o .env; nenhum agendamento foi confirmado.')
            return
        except RateLimitError:
            print('A API recusou a chamada por limite de uso ou créditos. Verifique sua conta; nenhum agendamento foi confirmado.')
            return
        except APIConnectionError:
            print('Não foi possível conectar à API OpenAI. Confira a conexão e tente novamente; nenhum agendamento foi confirmado.')
            return
        finally:
            try:
                rastro.salvar(banco.caminho.parent/'rastros_agente.jsonl',sessao_id=sessao_id,
                             usuario_id=ctx.usuario_id,rota=rota)
            except OSError:
                print('Aviso: não foi possível salvar o rastro de eventos deste atendimento.')
        novas = resposta['messages'][len(historico):]
        ultima = resposta['messages'][-1]
        texto_resposta = str(ultima.content)
        if rota == 'consulta':
            # Um resultado top-k não sustenta contagem. Exigir retorno estruturado bem-sucedido.
            consultas = [mensagem for mensagem in novas
                         if getattr(mensagem,'name',None)=='consultar_mensagens_estruturado']
            exige_contagem = pergunta.lower().lstrip().startswith(('quantas ', 'quantos ', 'qtd '))
            if not any(_consulta_estruturada_comprovada(mensagem,exige_contagem) for mensagem in consultas):
                texto_resposta = ('Não consegui confirmar a contagem ou lista por consulta estruturada. '
                                  'A busca de trechos não permite afirmar um total. Tente novamente.')
        from .verificador import verificar_e_reparar
        texto_resposta, verificacao = verificar_e_reparar(
            pergunta, texto_resposta, novas, rota, arquivo_env)
        memoria.registrar(ctx,sessao_id,pergunta,texto_resposta)
        print('\n' + '=' * 64)
        print('RESPOSTA DA SECRETÁRIA')
        print('-' * 64)
        print(texto_resposta)
        print('\nVerificação:',verificacao['estado'],'| reparos:',verificacao['reparos'])
        print('\nCONTEXTO DO ATENDIMENTO')
        print('Rota sugerida:',rota,'| eventos observados:',len(rastro.eventos))
        if ha_recortes:
            print('Memória antiga do chat:',estrategia_recuperacao)
        if recuperados:
            print('Recortes antigos recuperados dos turnos:',[item['turno_id'] for item in recuperados])
        exibir_ferramentas_do_turno(novas)
        print('=' * 64 + '\n')


def aplicar_interpretacao_no_terminal(banco, ctx):
    """Prévia e segunda confirmação: aceitar a interpretação não grava projeto."""
    from .fila_revisao import FilaRevisao
    from .projetos_fontes import ProjetosFontes

    fila=FilaRevisao(banco)
    servico=ProjetosFontes(banco)
    aceitas=[p for p in fila.listar(ctx) if p['estado']=='aceita']
    if not aceitas:
        print('Nenhuma interpretação aceita para este usuário. Use a opção 6 primeiro.')
        return
    for p in aceitas:
        print(f"#{p['id']} | {p['dados']['area']} | {p['dados']['projeto']} | v{p['versao']}")
    proposta_id=int(input('ID da interpretação aceita (Enter volta): ').strip() or '0')
    if not proposta_id:
        return
    proposta=fila.obter(ctx,proposta_id)
    if proposta['dados']['area']=='projeto':
        texto=input('ID do cliente, se já cadastrado (Enter deixa vínculo pendente): ').strip()
        cliente_id=int(texto) if texto else None
        projeto_id=None
    else:
        projeto_id=int(input('ID do projeto existente: ').strip())
        cliente_id=None
    previa=servico.prever(ctx,proposta_id,projeto_id,cliente_id)
    print(json.dumps(previa,ensure_ascii=False,indent=2))
    if input('Confirmar gravação desta interpretação com estas fontes? [s/N] ').strip().lower()!='s':
        print('Nada foi gravado.')
        return
    resultado=servico.confirmar(ctx,proposta_id,previa['versao'],projeto_id,cliente_id)
    print(json.dumps(resultado,ensure_ascii=False,indent=2))
    print('Fontes vinculadas:',json.dumps(servico.fontes(ctx,resultado['anotacao_id']),ensure_ascii=False,indent=2))


def exibir_resultado(banco,ctx,corpus,arquivo,listar=False):
    resultado=banco.importar(ctx,corpus,arquivo)
    print(json.dumps(resultado,ensure_ascii=False,indent=2))
    print('Total de mensagens no corpus:',banco.contar(ctx,corpus))
    for aviso in banco.avisos(ctx,corpus,resultado['importacao_id']):
        # AVISOS: mostra motivo/linhas, sem despejar trechos potencialmente privados no log padrão.
        detalhes={k:v for k,v in aviso['detalhes'].items() if k!='original'}
        print('Aviso:',json.dumps({'tipo':aviso['tipo'],**detalhes},ensure_ascii=False))
    if listar:
        for m in banco.listar(ctx,corpus,50):
            print(f"M{m['id']:04d} | {m['data_original']} | {m['autor'] or '[sistema]'} | {m['tipo']}")
            print(m['texto'])
            print()
    return resultado



def executar_analise(banco,ctx,modo,estilo,arquivo_env,raiz):
    # IMPORT LAZY: importar/listar continuam funcionando sem dependências de LLM instaladas.
    try:
        from .chain_extracao import criar_modelo
        from .extracao import analisar_demonstracao
        from .fixtures_extracao import criar_modelo_fixture
        from .apresentacao import exibir_analise,salvar_analise
    except ImportError:
        raise ValueError('Instale requirements-ia.txt para usar as opções de análise.') from None
    modelo=criar_modelo_fixture() if modo=='fixture' else criar_modelo(arquivo_env)
    resultado=analisar_demonstracao(banco,ctx,modelo,'fixture_manual' if modo=='fixture' else 'api_real',estilo)
    exibir_analise(resultado)
    arquivo=salvar_analise(resultado,raiz/'dados/privados/analises')
    print('Análise salva em:',arquivo)
    from .fila_revisao import FilaRevisao
    fila=FilaRevisao(banco).registrar_resultado(ctx,resultado)
    print('Fila de revisão:',fila['novas'],'novas propostas; use a opção 6 para revisar.')
    return resultado


def preparar_indice_no_terminal(banco,ctx,arquivo_env):
    """Indexação explícita: nunca envia corpus privado à API durante uma pergunta."""
    from openai import OpenAIError
    from .agente_agenda import obter_chave_api
    from .indice_fontes import IndiceFontes, corpora_acessiveis, pasta_indice_do_banco

    corpora = corpora_acessiveis(banco,ctx)
    if not corpora:
        print('Nenhum corpus acessível. Importe a conversa fictícia pela opção 1 ou um arquivo pela opção 2.')
        return
    print('CORPORA ACESSÍVEIS')
    for corpus in corpora:
        print(f"#{corpus['id']} | {corpus['nome']} | importador: {corpus['criado_por']}")
    corpus_id = int(input('ID do corpus a indexar (Enter cancela): ').strip() or '0')
    if corpus_id == 0:
        return
    banco._corpus(ctx,corpus_id)
    if input('Enviar textos deste corpus à OpenAI para gerar embeddings? [s/N] ').strip().lower() != 's':
        print('Preparação cancelada; nenhum texto enviado.')
        return
    try:
        from langchain_openai import OpenAIEmbeddings
        embeddings = OpenAIEmbeddings(model='text-embedding-3-small',
                                       api_key=obter_chave_api(arquivo_env),
                                       max_retries=0,timeout=45)
        resultado = IndiceFontes(banco,pasta_indice_do_banco(banco)).preparar(
            ctx,corpus_id,embeddings,'text-embedding-3-small')
        print('Índice:',resultado['estado'],'| mensagens:',resultado['mensagens'],
              '| versão:',resultado['versao_corpus'][:12])
    except OpenAIError as erro:
        print('Indexação não concluída pela API:',type(erro).__name__)

def main():
    raiz=localizar_projeto()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arquivo',type=Path,help='TXT/ZIP local; caminho relativo à pasta atual.')
    parser.add_argument('--banco',type=Path,default=raiz/'dados/privados/secretaria.sqlite3')
    parser.add_argument('--corpus',help='Nome do corpus; obrigatório para arquivo próprio.')
    parser.add_argument('--usuario',choices=['ana','bruno','carla'],default='ana')
    parser.add_argument('--fuso',default='America/Sao_Paulo')
    parser.add_argument('--arquivo-env',type=Path,help='Arquivo .env explícito para análise real; não é usado no modo local.')
    parser.add_argument('--analisar',choices=['fixture','api'],help='Analisa somente a demonstração e encerra.')
    parser.add_argument('--estilo',choices=['lcel','imperativa'],default='lcel')
    parser.add_argument('--listar',action='store_true',help='Exibe mensagens em terminal local.')
    args=parser.parse_args()
    demo=raiz/'dados/ficticios/conversa_empresa.txt'
    if args.arquivo and not args.corpus and args.arquivo.resolve()!=demo.resolve():
        parser.error('Para arquivo próprio informe --corpus; não misturar backup real com a demonstração.')
    exibir_conceitos_estudados()
    try:
        with Banco(args.banco) as banco:
            banco.preparar_demo()
            ctx=Contexto('demo',args.usuario)
            # CORPUS: agenda compartilhada não exige abrir mensagens privadas de outro importador.
            corpus=None
            if args.arquivo or args.analisar or args.corpus:
                corpus=banco.selecionar_corpus(ctx,args.corpus or 'Demonstração fictícia',args.fuso)
            if args.analisar:
                executar_analise(banco,ctx,args.analisar,args.estilo,args.arquivo_env,raiz)
                return 0
            if args.arquivo:
                exibir_resultado(banco,ctx,corpus,args.arquivo,args.listar)
                return 0
            # INPUT: o terminal permite testar importar/reimportar sem editar o código.
            while True:
                print('\n1 Importar fictícios | 2 Importar local | 3 Listar | 4 Propostas fixture | 5 Propostas OpenAI | 6 Revisar interpretações | 7 Agendar visita | 8 Minha agenda | 9 Agente de visitas | 10 Aplicar interpretação ao projeto | 11 Preparar índice de fontes | 12 Financeiro | 0 Sair')
                try:
                    escolha=input('Opção: ').strip()
                except (EOFError, KeyboardInterrupt):
                    return 0
                if escolha in ('0','/sair'):
                    return 0
                try:
                    if escolha=='1':
                        corpus=banco.selecionar_corpus(ctx,'Demonstração fictícia',args.fuso)
                        exibir_resultado(banco,ctx,corpus,raiz/'dados/ficticios/conversa_empresa.txt',True)
                    elif escolha=='2':
                        arquivo=input('Caminho do TXT/ZIP (aspas opcionais): ').strip().strip('"')
                        nome=input('Nome do corpus para este arquivo privado: ').strip()
                        if nome=='Demonstração fictícia':
                            raise ValueError('Escolha outro corpus para não misturar com os exemplos.')
                        corpus=banco.selecionar_corpus(ctx,nome,args.fuso)
                        exibir_resultado(banco,ctx,corpus,arquivo,args.listar)
                    elif escolha=='3':
                        if corpus is None:
                            corpus=banco.selecionar_corpus(ctx,args.corpus or 'Demonstração fictícia',args.fuso)
                        for m in banco.listar(ctx,corpus):
                            print(f"M{m['id']:04d} | {m['data_original']} | {m['autor'] or '[sistema]'} | {m['texto']}")
                    elif escolha in ('4','5'):
                        executar_analise(banco,ctx,'fixture' if escolha=='4' else 'api',args.estilo,args.arquivo_env,raiz)
                    elif escolha=='6':
                        try:
                            from .terminal_revisao import revisar_no_terminal
                        except ImportError:
                            raise ValueError('Instale requirements-ia.txt para revisar interpretações.') from None
                        revisar_no_terminal(banco,ctx)
                    elif escolha=='7':
                        agendar_no_terminal(banco,ctx)
                    elif escolha=='8':
                        from .agenda import Agenda
                        print(json.dumps(Agenda(banco).listar_agenda(ctx),ensure_ascii=False,indent=2))
                    elif escolha=='9':
                        conversar_sobre_visita(banco,ctx,args.arquivo_env)
                    elif escolha=='10':
                        aplicar_interpretacao_no_terminal(banco,ctx)
                    elif escolha=='11':
                        preparar_indice_no_terminal(banco,ctx,args.arquivo_env)
                    elif escolha=='12':
                        from .terminal_financeiro import financeiro_no_terminal
                        financeiro_no_terminal(banco,ctx)
                    else:
                        print('Escolha uma opção de 0 a 12.')
                except (ValueError,OSError,PermissionError) as erro:
                    print('Operação não concluída:',str(erro))
    except (ValueError,OSError,PermissionError) as erro:
        print('Erro:',str(erro))
        return 2


if __name__=='__main__':
    raise SystemExit(main())
