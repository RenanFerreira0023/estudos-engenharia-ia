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
    from openai import APIConnectionError, AuthenticationError, RateLimitError
    from .agente_agenda import criar_agente_agenda
    agente = criar_agente_agenda(banco,ctx,arquivo_env)
    historico = []
    print('Agente com ferramentas. /voltar encerra; /confirmar ID grava uma proposta sua.')
    while True:
        pergunta = input('Você: ').strip()
        if pergunta == '/voltar':
            return
        if pergunta.startswith('/confirmar '):
            from .agenda import Agenda
            try:
                print(Agenda(banco).confirmar_visita(ctx,int(pergunta.split()[1])))
            except (ValueError,PermissionError) as erro:
                print('Não confirmado:',erro)
            continue
        if not pergunta:
            continue
        agora = datetime.now(ZoneInfo('America/Sao_Paulo')).isoformat()
        try:
            resposta = agente.invoke({'messages':historico+[{'role':'user','content':f'Agora: {agora}. Pedido: {pergunta}'}]},
                                    {'recursion_limit':12})
        except AuthenticationError:
            print('A chave OPENAI_API_KEY foi recusada ou expirou. Gere outra chave e atualize o .env; nenhum agendamento foi confirmado.')
            return
        except RateLimitError:
            print('A API recusou a chamada por limite de uso ou créditos. Verifique sua conta; nenhum agendamento foi confirmado.')
            return
        except APIConnectionError:
            print('Não foi possível conectar à API OpenAI. Confira a conexão e tente novamente; nenhum agendamento foi confirmado.')
            return
        novas = resposta['messages'][len(historico):]
        historico = resposta['messages']
        ultima = resposta['messages'][-1]
        print('Secretária:',ultima.content)
        for mensagem in novas:
            for chamada in getattr(mensagem,'tool_calls',[]):
                print('Ferramenta chamada:',json.dumps({'nome':chamada['name'],'args':chamada['args']},ensure_ascii=False))
            if getattr(mensagem,'type',None)=='tool':
                print('Retorno da ferramenta:',mensagem.content)


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
                print('\n1 Importar fictícios | 2 Importar local | 3 Listar | 4 Propostas fixture | 5 Propostas OpenAI | 6 Revisar interpretações | 7 Agendar visita | 8 Minha agenda | 9 Agente de visitas | 0 Sair')
                try:
                    escolha=input('Opção: ').strip()
                except EOFError:
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
                    else:
                        print('Escolha uma opção de 0 a 9.')
                except (ValueError,OSError,PermissionError) as erro:
                    print('Operação não concluída:',str(erro))
    except (ValueError,OSError,PermissionError) as erro:
        print('Erro:',str(erro))
        return 2


if __name__=='__main__':
    raise SystemExit(main())
