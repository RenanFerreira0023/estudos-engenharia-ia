"""Um turno do mesmo agente usado no terminal, com memória persistida por usuário."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from .agente_agenda import criar_agente_agenda, obter_chave_api
from .memoria import MemoriaConversas, pede_contexto_antigo
from .observabilidade import RastroAgente
from .preferencias import PreferenciasUsuario
from .roteamento import roteador_pedido
from .verificador import verificar_e_reparar


def responder_turno(banco, ctx, sessao_id, pergunta, arquivo_env=None, agente=None):
    memoria = MemoriaConversas(banco)
    anteriores = memoria.ultimos(ctx, sessao_id)
    rota = roteador_pedido.invoke({'pergunta': pergunta, 'anteriores': anteriores})['rota']
    historico = memoria.mensagens(ctx, sessao_id)
    recuperados = []
    if pede_contexto_antigo(pergunta):
        ha_resumo = banco.con.execute(
            'SELECT 1 FROM resumos_turnos_agente WHERE sessao_id=? AND empresa_id=? AND usuario_id=? LIMIT 1',
            (sessao_id, ctx.empresa_id, ctx.usuario_id)).fetchone()
        if ha_resumo:
            try:
                from langchain_openai import OpenAIEmbeddings
                embeddings = OpenAIEmbeddings(model='text-embedding-3-small',
                    api_key=obter_chave_api(arquivo_env), max_retries=0, timeout=20)
                recuperados = memoria.buscar_resumos_vetoriais(ctx, sessao_id, pergunta, embeddings)
            except Exception:
                recuperados = memoria.buscar_resumos(ctx, sessao_id, pergunta)
    contexto_antigo = (' Trechos antigos da conversa, não confirmados: '
                      + json.dumps(recuperados, ensure_ascii=False) + '.') if recuperados else ''
    preferencias = json.dumps(PreferenciasUsuario(banco).listar(ctx), ensure_ascii=False)
    agora = datetime.now(ZoneInfo('America/Sao_Paulo')).isoformat()
    agente = agente or criar_agente_agenda(banco, ctx, arquivo_env, canal='web')
    rastro = RastroAgente()
    try:
        resposta = agente.invoke({'messages': historico + [{'role': 'user', 'content':
            f'Agora: {agora}. Rota sugerida: {rota}. Preferências confirmadas deste usuário: '
            f'{preferencias}.{contexto_antigo} Pedido: {pergunta}'}]},
            {'recursion_limit': 12, 'callbacks': [rastro]})
    finally:
        try:
            rastro.salvar(banco.caminho.parent / 'rastros_agente.jsonl', sessao_id=sessao_id,
                         usuario_id=ctx.usuario_id, rota=rota)
        except OSError:
            pass
    novas = resposta['messages'][len(historico):]
    texto = str(resposta['messages'][-1].content)
    texto, verificacao = verificar_e_reparar(pergunta, texto, novas, rota, arquivo_env)
    memoria.registrar(ctx, sessao_id, pergunta, texto)
    chamadas = [c['name'] for m in novas for c in getattr(m, 'tool_calls', [])]
    return {'resposta': texto, 'rota': rota, 'ferramentas': chamadas,
            'verificacao': verificacao, 'recortes_antigos': len(recuperados),
            'eventos': len(rastro.eventos)}
