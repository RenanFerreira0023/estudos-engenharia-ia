"""Respostas manuais limitadas ao corpus fictício; não simulam compreensão de um LLM."""
import json
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

def proposta(m,area,resumo,natureza='relato',projeto='Alfa',financeiro=None,agenda=None,pendencias=None):
    return {'area':area,'projeto':projeto,'natureza':natureza,'resumo':resumo,
            'financeiro':financeiro,'agenda':agenda,
            'fontes':[{'mensagem_id':m['id'],'trecho':m['texto']}],'pendencias':pendencias or []}

def criar_modelo_fixture():
    # FIXTURE: uma tabela manual de casos serve só para exercitar parser/orquestração/interface.
    def responder(prompt):
        lote=json.loads(prompt.to_messages()[-1].content.split('):\n',1)[1])
        itens=[]
        for m in lote['mensagens_foco']:
            texto=m['texto']
            if texto.startswith('Projeto Alfa:'):
                itens.append(proposta(m,'projeto','Implantação do portal; responsável informado Ana.'))
            elif texto.startswith('Orçamento Alfa:'):
                itens.append(proposta(m,'financeiro','Orçamento Alfa informado em R$ 10.000,00.','previsto',
                    financeiro={'tipo':'orcamento_proposto','valor_centavos':1000000,'percentual':None,'data_referencia':None}))
                itens.append(proposta(m,'financeiro','Entrada combinada de 30%; não comprova pagamento.','previsto',
                    financeiro={'tipo':'condicao_prevista','valor_centavos':None,'percentual':'30','data_referencia':None}))
            elif texto.startswith('Foi informado o recebimento de R$ 3.000'):
                itens.append(proposta(m,'financeiro','Recebimento de R$ 3.000,00 informado, sujeito a revisão.',
                    financeiro={'tipo':'pagamento_informado','valor_centavos':300000,'percentual':None,'data_referencia':'2026-11-09'},
                    pendencias=['Conferir relato antes de registrar; não é comprovação bancária.']))
            elif texto.startswith('Confirmo visita Alfa'):
                itens.append(proposta(m,'agenda','Visita Alfa confirmada na conversa; local ainda pendente.','confirmacao',
                    agenda={'tipo':'visita','inicio_em':'2026-11-10T14:00:00-03:00','fim_em':'2026-11-10T15:00:00-03:00',
                            'atendente_nome':'Ana','local':None},pendencias=['Confirmar endereço e mapear atendente.']))
            elif texto.startswith('Remarcar a visita Alfa:'):
                itens.append(proposta(m,'agenda','Proposta de remarcar visita Alfa para 11/11, das 10h às 11h.','correcao',
                    agenda={'tipo':'visita','inicio_em':'2026-11-11T10:00:00-03:00','fim_em':'2026-11-11T11:00:00-03:00',
                            'atendente_nome':None,'local':None},pendencias=['Vincular ao compromisso anterior antes de aplicar.']))
            elif texto.startswith('Projeto Beta:'):
                itens.append(proposta(m,'financeiro','Orçamento Beta proposto, sem aceite confirmado.','previsto','Beta',
                    financeiro={'tipo':'orcamento_proposto','valor_centavos':400000,'percentual':None,'data_referencia':None}))
            elif texto.startswith('Projeto Gama:'):
                itens.append(proposta(m,'financeiro','Gama sem total definido: saldo não calculável.','pendencia','Gama',
                    financeiro={'tipo':'saldo_indefinido','valor_centavos':None,'percentual':None,'data_referencia':None},
                    pendencias=['Informar contrato e valor total.']))
        return AIMessage(content=json.dumps({'propostas':itens,'observacoes':['Fixture manual; não demonstra interpretação por LLM.']},ensure_ascii=False))
    return RunnableLambda(responder)
