"""Operações financeiras locais e relatório legível, sem exportação de arquivo."""
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from .financeiro import Financeiro


def centavos(texto):
    bruto = texto.strip().replace('R$', '').replace(' ', '')
    if ',' in bruto:
        bruto = bruto.replace('.', '').replace(',', '.')
    try:
        numero = Decimal(bruto)
    except InvalidOperation as erro:
        raise ValueError('Informe valor monetário como 10000,00.') from erro
    if not numero.is_finite() or numero <= 0 or numero.as_tuple().exponent < -2:
        raise ValueError('Valor deve ser positivo e ter até duas casas decimais.')
    return int(numero * 100)


def moeda(valor):
    if valor is None:
        return 'não definido'
    inteiro, cent = divmod(valor, 100)
    return 'R$ ' + f'{inteiro:,}'.replace(',', '.') + f',{cent:02d}'


def mostrar_relatorio(financeiro, ctx):
    relatorio = financeiro.relatorio(ctx)
    print('\nRELATÓRIO FINANCEIRO —',relatorio['data_base_utc'])
    if not relatorio['projetos']:
        print('Nenhum projeto operacional cadastrado. A opção 10 aplica interpretações aceitas a projetos.')
    for projeto in relatorio['projetos']:
        print(f"\n#{projeto['projeto_id']} {projeto['projeto']} | cliente: {projeto['cliente'] or 'não vinculado'}")
        print('Orçamento aceito:',moeda(projeto['valor_aceito_centavos']))
        print('Entrada acordada:',str(projeto['percentual_entrada_acordado']) + '%'
              if projeto['percentual_entrada_acordado'] is not None else 'não definida')
        print('Recebido confirmado:',moeda(projeto['recebido_confirmado_centavos']))
        print('Saldo:',moeda(projeto['saldo_centavos']))
        for parcela in projeto['parcelas']:
            print(f"  Parcela #{parcela['id']} — {parcela['descricao']}: "
                  f"previsto {moeda(parcela['valor_previsto_centavos'])}, "
                  f"confirmado {moeda(parcela['recebido_confirmado_centavos'])}, "
                  f"vence {parcela['vencimento'] or 'sem data'}")
            for pagamento in parcela['pagamentos']:
                print(f"    Pagamento #{pagamento['id']}: {moeda(pagamento['valor_centavos'])} "
                      f"| {pagamento['status']}")
    print('\n',relatorio['limite'])


def financeiro_no_terminal(banco, ctx):
    financeiro = Financeiro(banco)
    financeiro._permitir(ctx)
    while True:
        print('\nFINANCEIRO | 1 Relatório | 2 Propor orçamento | 3 Aceitar orçamento '
              '| 4 Definir parcelas | 5 Informar pagamento | 6 Confirmar pagamento '
              '| 7 Substituir orçamento | 8 Reverter pagamento | 0 Voltar')
        opcao = input('Opção financeira: ').strip()
        if opcao in ('0',''):
            return
        try:
            if opcao == '1':
                mostrar_relatorio(financeiro,ctx)
            elif opcao == '2':
                projeto = int(input('ID do projeto operacional: '))
                valor = centavos(input('Valor do orçamento (R$): '))
                percentual = input('Entrada acordada em % (Enter se desconhecida): ').strip()
                percentual = int(percentual) if percentual else None
                print(financeiro.criar_orcamento(ctx,projeto,valor,percentual))
                print('Orçamento apenas proposto; aceite é ação separada.')
            elif opcao == '3':
                identificador = int(input('ID do orçamento proposto: '))
                atual = financeiro._orcamento(ctx,identificador)
                print(f"Projeto #{atual['projeto_id']} | revisão {atual['revisao']} | "
                      f"valor {moeda(atual['valor_centavos'])} | status {atual['status']}")
                if input('Aceitar este orçamento? [s/N] ').strip().lower() == 's':
                    print(financeiro.aceitar_orcamento(ctx,identificador))
            elif opcao == '4':
                identificador = int(input('ID do orçamento aceito: '))
                quantidade = int(input('Quantidade de parcelas: '))
                if not 1 <= quantidade <= 24:
                    raise ValueError('Quantidade de parcelas deve ser de 1 a 24.')
                parcelas = []
                for numero in range(1,quantidade+1):
                    print(f'Parcela {numero}')
                    parcelas.append({
                        'descricao':input('Descrição: ').strip(),
                        'valor_centavos':centavos(input('Valor previsto (R$): ')),
                        'vencimento':input('Vencimento AAAA-MM-DD (Enter se desconhecido): ').strip() or None,
                        'lembrar_cobranca':input('Lembrar cobrança AAAA-MM-DD (Enter se indefinido): ').strip() or None})
                print('Total previsto:',moeda(sum(p['valor_centavos'] for p in parcelas)))
                if input('Gravar parcelas? [s/N] ').strip().lower() == 's':
                    print(financeiro.definir_parcelas(ctx,identificador,parcelas))
            elif opcao == '5':
                parcela = int(input('ID da parcela: '))
                valor = centavos(input('Valor informado (R$): '))
                data = input('Data informada AAAA-MM-DD: ').strip()
                observacao = input('Observação: ').strip()
                chave = input('Chave do lançamento (Enter gera uma): ').strip() or uuid4().hex
                print(financeiro.informar_pagamento(ctx,parcela,valor,data,chave,observacao))
                print('Ainda não entra no saldo. Confirme apenas após conferir o recebimento.')
            elif opcao == '6':
                identificador = int(input('ID do pagamento informado: '))
                pagamento = banco.con.execute(
                    'SELECT valor_centavos,data_pagamento,status FROM pagamentos WHERE empresa_id=? AND id=?',
                    (ctx.empresa_id,identificador)).fetchone()
                if pagamento is None:
                    raise ValueError('Pagamento não encontrado nesta empresa.')
                print('Valor:',moeda(pagamento['valor_centavos']),
                      '| data:',pagamento['data_pagamento'],'| status:',pagamento['status'])
                if input('Recebimento conferido e confirmado? [s/N] ').strip().lower() == 's':
                    print(financeiro.confirmar_pagamento(ctx,identificador))
            elif opcao == '7':
                identificador = int(input('ID do novo orçamento proposto: '))
                motivo = input('Motivo da substituição: ').strip()
                if input('Substituir o orçamento ativo por esta revisão? [s/N] ').strip().lower() == 's':
                    print(financeiro.substituir_orcamento(ctx,identificador,motivo))
            elif opcao == '8':
                identificador = int(input('ID do pagamento a reverter: '))
                motivo = input('Motivo da reversão: ').strip()
                if input('Confirmar reversão auditada? [s/N] ').strip().lower() == 's':
                    print(financeiro.reverter_pagamento(ctx,identificador,motivo))
            else:
                print('Escolha uma opção de 0 a 8.')
        except (ValueError,PermissionError) as erro:
            print('Operação financeira não concluída:',erro)
