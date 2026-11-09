"""Contexto operacional observado: IDs/pedido, isolados por sessão e sem preços memorizados."""
import json


def atualizar_contexto_comercial(anterior, trajetoria):
    # TRAJETÓRIA: só retornos reais de ferramentas atualizam IDs; texto do assistente não prova produto.
    contexto = dict(anterior)
    chamadas = {}
    contexto.pop('ultimo_orcamento', None)
    for m in trajetoria:
        for c in m.get('tool_calls', []):
            chamadas[c['id']] = c
        if m.get('tipo') != 'tool':
            continue
        try:
            dados = json.loads(m['conteudo'])
        except (ValueError, TypeError):
            continue
        chamada = chamadas.get(m.get('tool_call_id'), {})
        args = chamada.get('args', {})
        if m.get('ferramenta') in ('consultar_catalogo', 'consultar_catalogo_estruturado') and dados.get('status') == 'ok' and dados.get('produtos'):
            contexto['produtos_consultados'] = [{k:p[k] for k in ('id','sku','nome','categoria')}
                                                for p in dados['produtos']]
            # ESTADO usa a referência efetiva retornada, não argumento descartado ou normalizado.
            if 'referencia_consulta' in dados:
                vid = dados['referencia_consulta'].get('veiculo_id')
            elif 'filtros_descartados' in dados:
                vid = None
            else:
                vid = args.get('veiculo_id') or dados.get('plano', {}).get('veiculo_id')
            if vid:
                contexto['veiculo_do_pedido'] = vid
            else:
                contexto.pop('veiculo_do_pedido', None)
        # REFERÊNCIA TÉCNICA também identifica o veículo da sessão, sem alterar perfil ou copiar peças.
        if m.get('ferramenta') == 'consultar_informacao_tecnica' and dados.get('status') in ('informacao_disponivel','informacao_pendente') and dados.get('veiculo_id'):
            vid=dados['veiculo_id']
            if contexto.get('veiculo_do_pedido') != vid:
                contexto.pop('produtos_consultados',None)
            contexto['veiculo_do_pedido']=vid
        if m.get('ferramenta') == 'calcular_orcamento' and dados.get('status') in ('ok', 'parcial', 'pendencia_estoque', 'cotacao_entrega_pendente'):
            contexto['ultimo_orcamento'] = {
                'itens': [{'produto_id':i['produto_id'], 'quantidade_solicitada':i['quantidade'],
                           'saldo_observado':i['estoque_consultado']} for i in dados['itens']],
                'modalidade':args.get('modalidade'), 'municipio':args.get('municipio'), 'uf':args.get('uf'),
                'status':dados['status'], 'limite':'Reconsultar estoque/preço e recalcular; não é reserva.'}
    return contexto
