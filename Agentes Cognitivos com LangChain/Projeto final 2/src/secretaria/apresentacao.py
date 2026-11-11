"""Apresentação de propostas; sem executar confirmação ou escrita operacional."""
import json
from pathlib import Path
from uuid import uuid4

def moeda(centavos):
    reais,resto=divmod(centavos,100)
    return 'R$ '+format(reais,',').replace(',','.')+f',{resto:02d}'

def salvar_analise(resultado,pasta):
    pasta=Path(pasta);pasta.mkdir(parents=True,exist_ok=True)
    arquivo=pasta/('analise_'+uuid4().hex+'.json')
    arquivo.write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return arquivo

def exibir_analise(resultado):
    print('\n'+'='*64)
    print('PROPOSTAS PARA REVISÃO — nenhum registro operacional foi gravado')
    print('Origem:',resultado['origem'],'| Composição:',resultado['estilo'])
    print('Cobertura dos lotes:',resultado['mensagens_em_lotes_concluidos'],'/',resultado['mensagens_no_snapshot'])
    if resultado['origem']!='api_real':
        print('[FIXTURE LOCAL] Respostas manuais; nenhuma chamada de LLM.')
    for i,p in enumerate(resultado['propostas'],1):
        print(f"\n{i}. {p['area'].upper()} | {p['projeto'] or 'projeto não identificado'} | {p['natureza']}")
        print(p['resumo'])
        if p['financeiro']:
            f=p['financeiro'];print('Tipo:',f['tipo'])
            if f['valor_centavos'] is not None:print('Valor:',moeda(f['valor_centavos']))
            if f['percentual'] is not None:print('Percentual informado:',f['percentual']+'%')
        if p['agenda']:
            a=p['agenda'];print('Início:',a['inicio_em'] or 'a confirmar','| Fim:',a['fim_em'] or 'a confirmar')
        for fonte in p['fontes']:
            print(f"Fonte M{fonte['mensagem_id']:04d}: {fonte['trecho']}")
        for ajuste in p.get('ajustes_revisao',[]):
            print('Ajuste por regra explícita:',ajuste['regra'],'| Fonte:',ajuste['mensagem_id'])
            for campo,valor in ajuste['alteracoes'].items():
                print(f"  {campo}: {valor['antes']} -> {valor['depois']}")
        for pendencia in p['pendencias']:print('Pendente:',pendencia)
    for edicao in resultado.get('edicoes_para_revisao',[]):
        print('\nMENSAGEM EDITADA — revisão necessária; nenhum horário foi escolhido')
        fonte=edicao['fonte_editada']
        print(f"Fonte M{fonte['mensagem_id']:04d}: {fonte['trecho']}")
        for candidato in edicao['candidatos_mesmo_autor_instante']:
            print(f"Candidato ao vínculo M{candidato['mensagem_id']:04d}: {candidato['trecho']}")
        print('Pendente:',edicao['pendencia'])
    for lote in resultado['lotes']:
        for rejeitada in lote.get('propostas_rejeitadas',[]):
            print(f"Lote {lote['lote_id']} | Proposta {rejeitada['numero_proposta']} rejeitada: {rejeitada['motivo']}")
        if lote['status']=='erro':
            print(f"Lote {lote['lote_id']} não concluído: {lote['tipo_erro']} — {lote['motivo']}")
    print('Propostas com fontes válidas para revisão:',len(resultado['propostas']))
    print('Propostas rejeitadas por fonte:',resultado.get('propostas_rejeitadas_por_fonte',0))
    print('\nEstado da execução dos lotes:',resultado['status'])
    print('Cobertura não equivale a correção semântica; revise propostas e fontes.')
