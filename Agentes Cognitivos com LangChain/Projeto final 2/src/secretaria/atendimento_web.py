"""Um turno do mesmo agente usado no terminal, com memória persistida por usuário."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from .agente_agenda import criar_agente_agenda, obter_chave_api
from .memoria import MemoriaConversas, pede_contexto_antigo
from .observabilidade import RastroAgente
from .preferencias import PreferenciasUsuario
from .roteamento import roteador_pedido
from .verificador import _retornos, verificar_e_reparar


RESPOSTA_COMANDO_WEB = ('Comandos com barra (como /confirmar ou /confirmar-cliente) só existem no terminal. '
    'Aqui no Streamlit, a confirmação é feita na aba Agenda: botão "Confirmar visita no banco" para visita '
    'e "Confirmar cadastro PJ proposto" para cliente, informando o ID. '
    'Este comando não foi enviado ao agente e nada foi gravado.')


def orientacao_confirmacao(mensagens):
    """Monta, em Python, como confirmar as propostas criadas neste turno.

    Não depende do LLM: a orientação gerada pelo modelo pode sumir na reescrita do verificador
    (observado em teste real) ou citar comandos que não existem no Streamlit."""
    linhas = []
    for nome, dados in _retornos(mensagens):
        if not isinstance(dados, dict) or dados.get('estado') != 'pendente' or not dados.get('proposta_id'):
            continue
        if nome == 'propor_visita':
            prazo = ''
            if dados.get('expira_em'):
                prazo = ' até ' + datetime.fromisoformat(dados['expira_em']).astimezone(
                    ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
            extra = ' Esta proposta já existia; nenhuma nova foi criada.' if dados.get('reutilizada') else ''
            linhas.append(f'Para confirmar a visita: aba Agenda → "Confirmar visita no banco", '
                          f'ID {dados["proposta_id"]}{prazo}.{extra}')
        elif nome == 'propor_cadastro_cliente':
            linhas.append(f'Para confirmar o cadastro: aba Agenda → "Confirmar cadastro PJ proposto", '
                          f'ID {dados["proposta_id"]}.')
    return '\n'.join(dict.fromkeys(linhas))


def responder_turno(banco, ctx, sessao_id, pergunta, arquivo_env=None, agente=None):
    # COMANDO LOCAL: no canal web, texto iniciado por "/" não vai ao LLM. Antes desta regra, o agente
    # recebia "/confirmar-cliente 1" como pedido comum e respondia "cadastro confirmado" sem gravar nada.
    if pergunta.strip().startswith('/'):
        return {'resposta': RESPOSTA_COMANDO_WEB, 'rota': 'comando_local', 'ferramentas': [],
                'verificacao': {'estado': 'nao_aplicavel'}, 'recortes_antigos': 0, 'eventos': 0}
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
    orientacao = orientacao_confirmacao(novas)
    if orientacao:
        texto = texto.rstrip() + '\n\n' + orientacao
    memoria.registrar(ctx, sessao_id, pergunta, texto)
    chamadas = [c['name'] for m in novas for c in getattr(m, 'tool_calls', [])]
    return {'resposta': texto, 'rota': rota, 'ferramentas': chamadas,
            'verificacao': verificacao, 'recortes_antigos': len(recuperados),
            'eventos': len(rastro.eventos)}
