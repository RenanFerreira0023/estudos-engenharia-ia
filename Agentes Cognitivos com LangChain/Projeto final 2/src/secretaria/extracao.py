"""Lotes com contexto, validação de fontes e cobertura observável, sem gravar fatos."""
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
from .chain_extracao import criar_chain
from .importador import ler_arquivo
from .propostas import SaidaExtracao
from .revisao import revisar_cancelamentos,listar_edicoes

class FonteInvalida(ValueError):
    pass

def preparar_lotes(snapshot,tamanho=8,vizinhos=1):
    if type(tamanho) is not int or not 1<=tamanho<=20 or type(vizinhos) is not int or not 0<=vizinhos<=3:
        raise ValueError('Tamanho de lote ou contexto inválido.')
    mensagens=snapshot['mensagens']
    if len({m['id'] for m in mensagens})!=len(mensagens):
        raise ValueError('IDs de mensagens precisam ser únicos no snapshot.')
    lotes=[]
    for inicio in range(0,len(mensagens),tamanho):
        fim=min(inicio+tamanho,len(mensagens))
        foco=mensagens[inicio:fim]
        contexto=mensagens[max(0,inicio-vizinhos):inicio]+mensagens[fim:fim+vizinhos]
        lotes.append({'lote_id':len(lotes)+1,'fuso':snapshot['fuso'],
                      'mensagens_foco':foco,'contexto_vizinho':contexto})
    return lotes

def normalizar_trecho(texto):
    return ' '.join(texto.split())

MOEDA=re.compile(r'R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}|\d+)(?!\d|[.,]\d)')

def validar_fontes(saida,lote):
    # RASTREABILIDADE: IDs precisam existir, trechos precisam ser literais e valores vir das fontes citadas.
    saida=SaidaExtracao.model_validate(saida)
    mensagens={m['id']:m for m in lote['mensagens_foco']+lote['contexto_vizinho']}
    foco={m['id'] for m in lote['mensagens_foco']}
    for proposta in saida.propostas:
        ids=[f.mensagem_id for f in proposta.fontes]
        if len(ids)!=len(set(ids)):
            raise FonteInvalida('IDs de fontes repetidos na proposta.')
        if not foco.intersection(ids):
            raise FonteInvalida('Nenhuma fonte da proposta pertence às mensagens de foco do lote.')
        citados=[]
        for fonte in proposta.fontes:
            mensagem=mensagens.get(fonte.mensagem_id)
            if mensagem is None or mensagem['tipo']!='mensagem':
                raise FonteInvalida('Fonte inexistente neste lote ou sem conteúdo de mensagem.')
            if normalizar_trecho(fonte.trecho) not in normalizar_trecho(mensagem['texto']):
                raise FonteInvalida('Trecho não corresponde ao texto original da fonte.')
            citados.append(fonte.trecho)
        if proposta.financeiro:
            financeiro=proposta.financeiro
            quantias={int(Decimal(m[1].replace('.','').replace(',','.'))*100)
                      for t in citados for m in MOEDA.finditer(t)}
            if financeiro.valor_centavos is not None and financeiro.valor_centavos not in quantias:
                raise FonteInvalida('Valor monetário não está escrito nas fontes citadas; cálculo não é extração.')
            percentuais={Decimal(m[1].replace(',','.')) for t in citados
                         for m in re.finditer(r'(\d+(?:[.,]\d+)?)\s*%',t)}
            if financeiro.percentual is not None and Decimal(financeiro.percentual) not in percentuais:
                raise FonteInvalida('Percentual não está escrito nas fontes citadas.')
    return saida

def analisar_snapshot(snapshot,modelo,origem,estilo='lcel',tamanho=8):
    lotes=preparar_lotes(snapshot,tamanho=tamanho)
    runnable=criar_chain(modelo,estilo)
    entradas=[];indices=[];respostas={}
    for i,lote in enumerate(lotes):
        pacote=json.dumps(lote,ensure_ascii=False)
        if len(pacote)>24000:
            respostas[i]=ValueError('Lote excede limite de entrada; sem truncamento.')
        else:
            entradas.append({'pacote':pacote});indices.append(i)
    # RUNNABLE/BATCH: só leituras independentes; erro fica restrito ao lote e a cobertura é explícita.
    if entradas:
        if len(entradas)==1:
            try:resultados=[runnable.invoke(entradas[0])]
            except Exception as erro:resultados=[erro]
        else:
            resultados=runnable.batch(entradas,config={'max_concurrency':2},return_exceptions=True)
        respostas.update(dict(zip(indices,resultados)))
    propostas=[];relatorios=[];chaves=set()
    for i,lote in enumerate(lotes):
        base={'lote_id':lote['lote_id'],'mensagens_foco':[m['id'] for m in lote['mensagens_foco']],
              'contexto_vizinho':[m['id'] for m in lote['contexto_vizinho']]}
        try:
            resposta=respostas[i]
            if isinstance(resposta,Exception):raise resposta
            # VALIDAÇÃO POR PROPOSTA: um erro de fonte não elimina propostas válidas do mesmo lote.
            # JSON/contrato inválido ainda bloqueia o lote; somente saídas estruturadas chegam aqui.
            saida=SaidaExtracao.model_validate(resposta)
            rejeitadas=[];aceitas=0
            for numero,proposta in enumerate(saida.propostas,1):
                try:
                    validar_fontes(SaidaExtracao(propostas=[proposta],observacoes=[]),lote)
                except FonteInvalida as erro:
                    rejeitadas.append({'numero_proposta':numero,'tipo_erro':'FonteInvalida','motivo':str(erro),
                                       'proposta':proposta.model_dump(mode='json'),'status':'rejeitada_por_fonte'})
                    continue
                aceitas+=1
                dados=proposta.model_dump(mode='json')
                chave=sha256(json.dumps(dados,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
                if chave not in chaves:
                    propostas.append({**dados,'status':'aguardando_revisao','lote_id':lote['lote_id']})
                    chaves.add(chave)
            relatorio={**base,'status':'parcial' if rejeitadas else 'ok','observacoes':saida.observacoes,
                       'propostas_retornadas':len(saida.propostas),'propostas_com_fontes_validas':aceitas,
                       'propostas_rejeitadas':rejeitadas}
            if rejeitadas:
                relatorio.update(tipo_erro='FonteInvalida',
                                 motivo='Há propostas rejeitadas por fonte; as demais foram preservadas.')
            relatorios.append(relatorio)
        except Exception as erro:
            # ERRO: não expõe chave/prompt em mensagens de exceção nem transforma falha em análise completa.
            causa=erro.__cause__
            campos=[{'campo':'.'.join(map(str,e['loc'])),'tipo':e['type'],'motivo':e['msg']}
                    for e in causa.errors(include_input=False,include_url=False)[:8]] if hasattr(causa,'errors') else []
            relatorios.append({**base,'status':'erro','tipo_erro':type(erro).__name__,'erros_contrato':campos,
                               'motivo':str(erro) if isinstance(erro,FonteInvalida) else 'Lote não concluído; revise configuração, conexão ou contrato.'})
    revisar_cancelamentos(propostas)
    edicoes=listar_edicoes(snapshot)
    concluidos=[i for r in relatorios if r['status']=='ok' for i in r['mensagens_foco']]
    return {'status':'vazia' if not snapshot['mensagens'] else 'completa' if len(concluidos)==len(snapshot['mensagens']) else 'parcial',
            'origem':origem,'estilo':estilo,'modelo':'gpt-4o-mini' if origem=='api_real' else 'fixture_manual_sem_llm',
            'empresa_id':snapshot['empresa_id'],'usuario_id':snapshot['usuario_id'],'corpus_id':snapshot['corpus_id'],
            'fuso':snapshot['fuso'],'criado_em':datetime.now(timezone.utc).isoformat(),
            'mensagens_no_snapshot':len(snapshot['mensagens']),'mensagens_em_lotes_concluidos':len(concluidos),
            'lotes':relatorios,'propostas':propostas,
            'propostas_rejeitadas_por_fonte':sum(len(r.get('propostas_rejeitadas',[])) for r in relatorios),'edicoes_para_revisao':edicoes,'gravacoes_operacionais':0,
            'limite':'Completa indica cobertura dos lotes, não acerto semântico. Fontes e números validados não provam toda interpretação; propostas exigem revisão. Duplicação semântica entre lotes ainda pode ocorrer.'}

def analisar_demonstracao(banco,ctx,modelo,origem,estilo='lcel'):
    raiz=Path(__file__).resolve().parents[2]
    arquivo=raiz/'dados/ficticios/conversa_empresa.txt'
    corpus=banco.selecionar_corpus(ctx,'Demonstração fictícia')
    banco.importar(ctx,corpus,arquivo)
    snapshot=banco.snapshot_analise(ctx,corpus)
    # FRONTEIRA DE DADOS: menu de API só permite o corpus fictício sem lotes de outra origem.
    if set(snapshot['hashes_importados'])!={ler_arquivo(arquivo).sha256_texto}:
        raise ValueError('Corpus contém outros arquivos. Análise externa bloqueada; selecione demonstração limpa.')
    return analisar_snapshot(snapshot,modelo,origem,estilo)
