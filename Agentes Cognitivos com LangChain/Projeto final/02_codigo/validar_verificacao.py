"""Avaliação do verificador. Sem --real: só fixtures/regras, sem fingir notas semânticas."""
import argparse
from pathlib import Path
import os
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from langchain_core.messages import AIMessage
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from auto_super_parts.verificacao import criar_modelo_verificacao
from auto_super_parts.configuracao import obter_chave_api
from auto_super_parts.demonstracao_verificacao import demonstrar
from auto_super_parts.atendimento_verificado import AtendimentoVerificado
from auto_super_parts.memoria import MemoriaSQLite
from auto_super_parts.agente_fase02 import registrar_execucao


class ModeloFalhaControlada(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


class RAGNaoAcionado:
    manifesto = {'modelo_embedding': 'fixture nao acionada neste teste', 'sha256_fonte': 'nao aplicavel'}
    def consultar(self, pergunta):
        raise AssertionError('Este cenário não solicita política')


def integrar(modelo):
    # INJEÇÃO CONTROLADA: a resposta incorreta é escrita para o teste; não é falha observada do LLM atendente.
    with tempfile.TemporaryDirectory(prefix='verificacao_integrada_') as tmp:
        mem = MemoriaSQLite(Path(tmp)/'m.sqlite3')
        falso = ModeloFalhaControlada(responses=[
            AIMessage(content='', tool_calls=[{'name': 'consultar_catalogo', 'args': {'produto_id': 'P009'}, 'id': 'consulta'}]),
            AIMessage(content='', tool_calls=[{'name': 'calcular_orcamento', 'args': {'itens': [{'produto_id': 'P009', 'quantidade': 7}], 'modalidade': 'retirada'}, 'id': 'calculo'}]),
            AIMessage(content='Total: R$ 100,00.')])
        controlado = AtendimentoVerificado(mem, modelo=falso, rag=RAGNaoAcionado(), planejador=lambda p:{}, modelo_verificacao=modelo)
        real = None
        try:
            s = mem.abrir_sessao('injecao_controlada')
            r = controlado.atender('injecao_controlada', s, 'Calcule 7 unidades do P009 para retirada.', salvar=False)
            r['origem_candidata'] = 'fixture manual injetada no agente; ferramentas locais, juiz e reparador com API real'
            guardado = mem.historico('injecao_controlada', s)[-1]['content']
            v = r.get('verificacao_geral', {})
            criterio = (r['status'] == 'ok' and not v.get('avaliacoes', [{}])[0].get('aprovada', True)
                        and v.get('status') in ('corrigida', 'limitacao') and guardado == r['resposta']
                        and 'R$ 100,00' not in guardado)
            resultados = [{'id': 'falha_controlada', 'criterio_atendido': criterio, 'resultado': r}]
            real = AtendimentoVerificado(mem, modelo_verificacao=modelo)
            for id, pergunta in [('orcamento_real', 'Calcule 7 unidades do P009 para retirada.'),
                                  ('garantia_real', 'Qual o prazo de garantia das peças? Posso trocar depois de 30 dias?')]:
                s = mem.abrir_sessao(id)
                resposta = real.atender(id, s, pergunta, salvar=False)
                v = resposta.get('verificacao_geral', {})
                criterio = resposta['status'] == 'ok' and v.get('status') in ('aprovada', 'corrigida')
                if id == 'orcamento_real':
                    criterio = criterio and '118,30' in resposta['resposta']
                if id == 'garantia_real':
                    criterio = criterio and '30' in resposta['resposta'] and any(m.get('ferramenta') == 'consultar_politicas' for m in resposta['trajetoria'])
                resultados.append({'id': id, 'criterio_atendido': criterio, 'resultado': resposta})
            return resultados
        finally:
            controlado.fechar()
            if real:
                real.fechar()
            mem.fechar()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--real', action='store_true')
    parser.add_argument('--arquivo-env', type=Path)
    args = parser.parse_args()
    if args.real:
        os.environ['OPENAI_API_KEY'] = obter_chave_api(args.arquivo_env)
    modelo = criar_modelo_verificacao() if args.real else None
    payload = demonstrar(modelo)
    payload['integracao'] = integrar(modelo) if args.real else []
    for c in payload['casos']:
        observado = c['avaliacao_juiz']
        print(c['id'], '| esperado:', c['esperado_aprovada'], '| juiz:', observado['aprovada'] if observado else 'NAO EXECUTADO',
              '| comparacao:', c['conferiu_gabarito'])
    arquivo = registrar_execucao(payload, prefixo='fase05_verificacao_real' if args.real else 'fase05_fixtures_locais')
    print('Evidencia:', arquivo.name)
    if args.real and (not all(c['conferiu_gabarito'] for c in payload['casos']) or not all(c['criterio_atendido'] for c in payload['integracao'])):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
