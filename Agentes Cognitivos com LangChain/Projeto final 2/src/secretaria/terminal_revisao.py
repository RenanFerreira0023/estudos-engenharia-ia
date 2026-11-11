"""Terminal da fila: decisão humana explícita, independente de LLM."""
import json
from .fila_revisao import FilaRevisao

def revisar_no_terminal(banco,ctx):
    fila=FilaRevisao(banco)
    print('REVISÃO DA INTERPRETAÇÃO — aceitar não cria pagamento, projeto ou compromisso.')
    # INPUT/ESTADO: a versão exibida acompanha a decisão; outra alteração invalida uma tela antiga.
    while True:
        itens=fila.listar(ctx)
        if not itens:
            print('Nenhuma proposta acessível. Execute primeiro a opção 4 ou 5.')
            return
        for p in itens:
            d=p['dados']
            print(f"#{p['id']} | {p['estado']} | v{p['versao']} | {d['area']} | {d['projeto'] or 'a identificar'}")
        entrada=input('ID para revisar (Enter volta): ').strip()
        if not entrada:
            return
        try:
            atual=fila.obter(ctx,int(entrada));id=atual['id']
            print(json.dumps(atual,ensure_ascii=False,indent=2))
            print('Aceitar = interpretação revisada; rejeitar = retirar desta fila de uso; corrigir mantém pendente.')
            acao=input('[a] aceitar | [r] rejeitar | [c] corrigir | [h] histórico | Enter voltar: ').strip().lower()
            if acao=='h':
                print(json.dumps(fila.historico(ctx,id),ensure_ascii=False,indent=2))
                continue
            if acao=='c':
                print('Campos permitidos: projeto, natureza, resumo, financeiro, agenda, pendencias.')
                print('Exemplo: {"resumo":"Resumo revisado sem alterar a fonte."}')
                mudancas=json.loads(input('Correção em JSON (uma linha): '))
                comentario=input('Motivo da correção: ')
                novo=fila.corrigir(ctx,id,atual['versao'],mudancas,comentario)
                print('Correção salva. Continua pendente na versão',novo['versao'])
            elif acao in ('a','r'):
                comentario=input('Comentário da revisão: ')
                novo=fila.decidir(ctx,id,atual['versao'],'aceitar' if acao=='a' else 'rejeitar',comentario)
                print('Decisão salva:',novo['estado'],'| versão',novo['versao'])
                print('Nenhum registro operacional foi criado.')
            elif acao:
                print('Escolha a, r, c ou h.')
        except (ValueError,PermissionError) as erro:
            print('Revisão não salva:',str(erro))
