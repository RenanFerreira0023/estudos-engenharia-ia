"""Valida referências declaradas no pedido, sem escolher versão ou peça por semelhança."""
import re
from .orcamento_fase02 import normalizar


def conferir_referencia(catalogo, pedido, produto_id=None, veiculo_id=None, categoria=None):
    saida={'produto_id':produto_id,'veiculo_id':veiculo_id,'categoria':categoria,'ajustes':[],'erro':None}
    if not pedido:
        return saida
    veiculos=catalogo.listar_veiculos()['veiculos']
    por_id={v['id']:v for v in veiculos}
    texto=normalizar(pedido)
    ids={m.upper() for m in re.findall(r'(?<![\w-])v\d{3}(?![\w-])',texto)}
    modelos={v['modelo'] for v in veiculos if re.search(r'\b'+re.escape(normalizar(v['modelo']))+r'\b',texto)}
    candidatos=[v for v in veiculos if (v['id'] in ids if ids else v['modelo'] in modelos)]
    # DESAMBIGUAÇÃO: nome compartilhado não identifica geração. Ano/rotulo/ID declarado restringe opções.
    texto_sem_valores=re.sub(r'r\$\s*[\d.,]+','',texto)
    anos={int(a) for a in re.findall(r'\b(?:19|20)\d{2}\b',texto_sem_valores)}
    rotulos={v['id'] for v in veiculos if any(re.search(r'\b'+re.escape(normalizar(tag))+r'\b',texto)
             for tag in v.get('rotulos_identificacao',[]))}
    if (ids or modelos) and rotulos:
        candidatos=[v for v in candidatos if v['id'] in rotulos]
    if (ids or modelos) and anos:
        candidatos=[v for v in candidatos if v['ano_modelo'] in anos]


    saida['veiculos_identificados']=candidatos

    def recusar(status,motivo):
        saida['erro']={'status':status,'produtos':[],'aplicacoes':[],'pendencias':[motivo],
                       'veiculos_referenciados':candidatos,
                       'limite':'Opções cadastradas não confirmam o veículo do cliente. Confirme a configuração quando faltar; não consulte outro modelo.'}
        return saida

    # TIPOS DE ID: só corrige V informado pelo cliente; não transforma um ID adivinhado em escolha.
    if produto_id and re.fullmatch(r'V\d{3}',produto_id.upper()):
        codigo=produto_id.upper()
        if codigo not in ids or codigo not in por_id:
            return recusar('identificador_de_veiculo_em_produto','O código V identifica veículo, não produto. Confirme o veículo e informe o tipo da peça.')
        if not categoria:
            return recusar('categoria_pendente','O código informado identifica veículo; informe o tipo da peça para consultar.')
        saida.update(produto_id=None,veiculo_id=codigo)
        saida['ajustes'].append({'campo':'produto_id','recebido':produto_id,'interpretacao':'ID de veículo explícito no pedido','veiculo_id':codigo})
        produto_id,veiculo_id=None,codigo

    # PRECEDÊNCIA: modelo/ID do pedido atual não pode ser substituído por veículo salvo no perfil.
    if veiculo_id and veiculo_id in por_id:
        if ids and veiculo_id not in ids:
            return recusar('referencia_veiculo_divergente','O veículo enviado à ferramenta difere do ID informado no pedido atual. Use o ID declarado ou esclareça a referência.')
        if modelos and por_id[veiculo_id]['modelo'] not in modelos:
            return recusar('referencia_veiculo_divergente','O modelo enviado à ferramenta difere do modelo mencionado pelo cliente. Confirme a configuração solicitada; não use o perfil de outro carro.')

    # Referência única declarada por ID ou ano+geração não deve desaparecer quando a LLM omite o filtro.
    if veiculo_id is None and len(candidatos)==1 and (ids or (anos and rotulos)):
        veiculo_id=candidatos[0]['id']
        saida['veiculo_id']=veiculo_id
        saida['ajustes'].append({'campo':'veiculo_id','recebido':None,'veiculo_id':veiculo_id,'interpretacao':'referencia unica declarada no pedido'})
    alvos={v['id'] for v in candidatos}
    if (ids or modelos) and not candidatos:
        return recusar('configuracao_nao_cadastrada','Ano, tipo de motor ou ID declarado não corresponde a um recorte cadastrado. Confirme a configuração; não use outro ano ou geração.')
    if veiculo_id and candidatos and veiculo_id not in alvos:
        return recusar('referencia_veiculo_divergente','A geração/ano do veículo consultado difere do pedido. Clássico a ar e TSI não compartilham automaticamente dados ou peças.')
    codigo_produto_declarado=produto_id and re.search(r'(?<![\w-])'+re.escape(produto_id)+r'(?![\w-])',pedido,re.I)
    comparacao=bool(re.search(r'diferenc|compar|\bambos\b|\bentre\b',texto)) and len(rotulos)>1
    if len(modelos)==1 and not ids and len(candidatos)>1 and not codigo_produto_declarado and not comparacao:
        return recusar('veiculo_ambiguo','Há mais de uma configuração desse modelo. Pergunte se é clássico a ar ou TSI e confirme ano/motor, ou peça o ID. Não escolha pelo perfil salvo ou pela peça disponível.')

    # CÓDIGO NÃO DECLARADO: produto escolhido pelo agente não pode pertencer só a outro modelo.
    explicito=produto_id and re.search(r'(?<![\w-])'+re.escape(produto_id)+r'(?![\w-])',pedido,re.I)
    if produto_id and not explicito and (ids or modelos):
        produto=catalogo.consultar(produto_id=produto_id)
        if produto.get('status')=='ok':
            aplicacoes={a['veiculo_id'] for a in produto['aplicacoes']}
            alvos={v['id'] for v in candidatos}
            if alvos and not aplicacoes.intersection(alvos):
                return recusar('produto_de_outro_veiculo','O produto escolhido não possui vínculo cadastrado com o veículo mencionado neste pedido. Consulte a configuração correta antes de informar preço ou calcular.')
    return saida


def referencia_declarada(catalogo, pedido):
    """Referência do pedido para esta sessão; não confirma nem altera o perfil permanente."""
    r=conferir_referencia(catalogo,pedido)
    candidatos=r.get('veiculos_identificados',[])
    if r['erro'] or len(candidatos)!=1:
        return None
    v=candidatos[0]
    texto=normalizar(pedido)
    por_id=bool(re.search(r'(?<![\w-])'+v['id'].lower()+r'(?![\w-])',texto))
    ano=bool(re.search(r'\b'+str(v['ano_modelo'])+r'\b',texto))
    geracao=any(re.search(r'\b'+re.escape(normalizar(tag))+r'\b',texto) for tag in v.get('rotulos_identificacao',[]))
    return v['id'] if por_id or (ano and geracao) else None


def identificacao_pendente(catalogo, pedido):
    """Pergunta de identificação determinística antes de consultar preço/especificação."""
    texto=normalizar(pedido)
    tecnica=bool(re.search(r'\b(?:vela|velas|oleo|motor|correia|correias|bomba|arrefecimento|refrigerado|pneu|pneus|freio|freios|alternador|peca|pecas)\b',texto))
    politica=bool(re.search(r'garantia|politica|pagamento|pagar|pix|dinheiro|cartao|parcel|preferencia|devol|reembolso',texto))
    if not tecnica or politica:
        return None
    r=conferir_referencia(catalogo,pedido)
    if not r['erro'] or r['erro']['status']!='veiculo_ambiguo':
        return None
    opcoes=r['erro']['veiculos_referenciados']
    resumo=' ou '.join(f"{v['modelo']} {v['ano_modelo']} {v['motor']} ({v['id']})" for v in opcoes)
    return {'resposta':f'Você se refere ao {resumo}? Confirme ano e motor ou informe o ID do veículo.',
            'opcoes':opcoes,'origem':'validacao deterministica de configuracoes cadastradas; modelo nao executado'}
