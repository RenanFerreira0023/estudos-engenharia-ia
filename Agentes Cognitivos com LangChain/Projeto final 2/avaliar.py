"""Avalia fixtures locais ou o agente real. LangSmith só recebe dados fictícios com --langsmith."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / 'src'))
from secretaria.avaliacao import avaliar_caso, carregar_casos


def executar_api(caso, modelo):
    from secretaria.agenda import Agenda
    from secretaria.atendimento_web import responder_turno
    from secretaria.banco import Banco, Contexto
    from secretaria.memoria import MemoriaConversas
    with TemporaryDirectory() as pasta:
        with Banco(Path(pasta) / 'avaliacao.sqlite3') as banco:
            banco.preparar_demo()
            ctx = Contexto('demo', 'ana')
            Agenda(banco).cadastrar_cliente(ctx, 'Alfa Serviços', 'PF')
            corpus = banco.selecionar_corpus(ctx, 'Demonstração fictícia')
            banco.importar(ctx, corpus, RAIZ / 'dados/ficticios/conversa_empresa.txt')
            if caso['id'] == 'fonte':
                from langchain_openai import OpenAIEmbeddings
                from secretaria.agente_agenda import obter_chave_api
                from secretaria.indice_fontes import IndiceFontes, pasta_indice_do_banco
                embeddings = OpenAIEmbeddings(model='text-embedding-3-small',
                    api_key=obter_chave_api(), max_retries=0, timeout=45)
                IndiceFontes(banco, pasta_indice_do_banco(banco)).preparar(
                    ctx, corpus, embeddings, 'text-embedding-3-small')
            sessao = MemoriaConversas(banco).iniciar(ctx)
            resultado = responder_turno(banco, ctx, sessao, caso['pergunta'])
    return resultado['resposta'], resultado['ferramentas']


def main():
    from dotenv import load_dotenv
    load_dotenv(RAIZ / '.env', override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modo', choices=('fixture', 'api'), default='fixture')
    parser.add_argument('--langsmith', action='store_true', help='Envia somente casos fictícios ao LangSmith.')
    args = parser.parse_args()
    if args.langsmith and args.modo != 'api':
        parser.error('--langsmith exige --modo api; fixture local não é experimento do agente.')
    casos = carregar_casos(RAIZ)
    resultados = []
    modelo = None
    if args.modo == 'api':
        from langchain_openai import ChatOpenAI
        from secretaria.agente_agenda import obter_chave_api
        modelo = ChatOpenAI(model='gpt-4o-mini', api_key=obter_chave_api(),
                            temperature=0, max_retries=0, timeout=30)
    if args.langsmith:
        from langsmith import Client
        client = Client()
        nome = 'secretaria-ia-fixtures-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
        client.create_dataset(nome, description='Casos acadêmicos fictícios; nenhum corpus privado.')
        client.create_examples(dataset_name=nome, examples=[
            {'inputs': {'id': c['id'], 'pergunta': c['pergunta']},
             'outputs': {'resposta_referencia': c['resposta_referencia'],
                         'ferramentas_esperadas': c['ferramentas_esperadas']}}
            for c in casos if not c.get('fixture_only') and not c.get('fixture_negativa')])
        por_id = {c['id']: c for c in casos}

        def alvo(entrada):
            c = por_id[entrada['id']]
            resposta, ferramentas = executar_api(c, modelo)
            return {'resposta': resposta, 'ferramentas': ferramentas}

        def avaliar_exemplo(inputs, outputs, reference_outputs):
            c = por_id[inputs['id']]
            r = avaliar_caso(c, outputs['resposta'], outputs['ferramentas'], modelo)
            resultados.append(r)
            return [{'key': 'ferramentas_exatas', 'score': r['nota_ferramentas']},
                    {'key': 'resposta_semantica', 'score': r['nota_resposta']}]

        client.evaluate(alvo, data=nome, evaluators=[avaliar_exemplo],
                        experiment_prefix='secretaria-ia', max_concurrency=0, blocking=True)
        print('Experimento real registrado no LangSmith:', nome)
    else:
        for caso in casos:
            if args.modo == 'api' and (caso.get('fixture_only') or caso.get('fixture_negativa')):
                continue
            if args.modo == 'fixture':
                resposta, ferramentas = caso['fixture_resposta'], caso['fixture_ferramentas']
            else:
                resposta, ferramentas = executar_api(caso, modelo)
            resultados.append(avaliar_caso(caso, resposta, ferramentas, modelo))
    pasta = RAIZ / 'dados/privados/avaliacoes'
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / ('avaliacao_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json')
    destino.write_text(json.dumps({'modo': args.modo, 'langsmith': args.langsmith,
                                   'resultados': resultados}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('ID | origem | ferramentas | resposta | revisão humana')
    for r in resultados:
        print(f"{r['id']} | {r['origem']} | {r['nota_ferramentas']} | "
              f"{r['nota_resposta']} | {r['comentario_humano']}")
    print('Resultado local:', destino)


if __name__ == '__main__':
    main()
