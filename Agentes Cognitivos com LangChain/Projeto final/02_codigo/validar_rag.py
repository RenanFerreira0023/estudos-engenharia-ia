"""Integração real: antes/depois de recuperação, text-to-query e agente com memória."""
import argparse
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from auto_super_parts.agente_fase02 import registrar_execucao
from auto_super_parts.atendimento_memoria import criar_embeddings
from auto_super_parts.atendimento_rag import AtendimentoRAG
from auto_super_parts.catalogo_fase02 import Catalogo
from auto_super_parts.chain_inicial import criar_modelo
from auto_super_parts.memoria import MemoriaSQLite
from auto_super_parts.planos_consulta import criar_reescritor,criar_planejador_catalogo,consultar_catalogo_planejado
from auto_super_parts.rag_politicas import PoliticasRAG


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--real',action='store_true')
    parser.add_argument('--arquivo-env',type=Path)
    args=parser.parse_args()
    if not args.real:
        parser.exit(2,'Para testes offline execute executar_testes.py. Use --real para consumir APIs.\n')
    modelo=criar_modelo(args.arquivo_env)
    embeddings=criar_embeddings(args.arquivo_env)
    rag=PoliticasRAG(embeddings)
    reescrever=criar_reescritor(modelo,[d['secao'] for d in rag.manifesto['documentos']])
    recuperacoes=[]
    for pergunta,esperados in [
        ('Posso pagar ao entregador?',['POL-01']),
        ('Posso pagar com cartão em três vezes e tenho frete grátis em Curitiba?',['POL-01','POL-02']),
        ('Se eu fizer orçamento já fica reservado? E posso pagar no cartão?',['POL-04','POL-01']),
        ('Qual o prazo para trocar e o prazo de entrega em Curitiba?',['POL-03','POL-02'])]:
        antes=rag.buscar(pergunta,k=1)
        rag.reescrever=reescrever
        depois=rag.consultar(pergunta)
        ids_antes={d['id'] for d in antes}
        ids_depois={d['id'] for d in depois['documentos']}
        item={'pergunta':pergunta,'ids_necessarios':esperados,'antes':antes,'depois':depois,
              'cobertura_antes':set(esperados)<=ids_antes,'cobertura_depois':set(esperados)<=ids_depois}
        recuperacoes.append(item)
        print('Recuperação:',item['cobertura_antes'],'para',item['cobertura_depois'],flush=True)
    catalogo=Catalogo()
    try:
        planejar=criar_planejador_catalogo(modelo,catalogo.listar_veiculos()['veiculos'])
        pergunta='Liste as velas do catálogo com estoque disponível e preço de até R$ 20,00, da mais barata para a mais cara.'
        consulta=consultar_catalogo_planejado(catalogo,pergunta,planejar)
        plano=consulta.get('plano',{})
        produtos=consulta.get('produtos',[])
        query_ok=(consulta['status']=='ok' and plano.get('categoria')=='vela' and plano.get('estoque')=='disponivel'
                  and plano.get('preco_max_centavos')==2000 and plano.get('ordenacao')=='preco_crescente'
                  and bool(produtos) and all(p['categoria']=='vela' and p['estoque']>0 and p['preco_centavos']<=2000 for p in produtos)
                  and [p['preco_centavos'] for p in produtos]==sorted(p['preco_centavos'] for p in produtos))
        print('Text-to-query real:',query_ok,flush=True)
    finally:
        catalogo.fechar()
    casos=[]
    with tempfile.TemporaryDirectory(prefix='fase04_real_') as tmp:
        memoria=MemoriaSQLite(Path(tmp)/'memoria.sqlite3',embeddings=embeddings)
        sistema=AtendimentoRAG(memoria,modelo=modelo,rag=rag,planejador=planejar)
        sessao=memoria.abrir_sessao('cliente_rag_demo')
        try:
            for nome,pergunta,ferramenta,termos in [
                ('pagamento_entregador','Posso pagar ao entregador?','consultar_politicas',['antecip']),
                ('duas_politicas','Posso pagar com cartão em três vezes e tenho frete grátis em Curitiba?','consultar_politicas',['cartão','Curitiba']),
                ('garantia_cadastrada','Qual prazo de garantia vocês oferecem?','consultar_politicas',['30']),
                ('catalogo_filtrado','Liste as velas do catálogo com estoque disponível até R$ 20,00, da mais barata para a mais cara.','consultar_catalogo_estruturado',[]),
                ('assunto_sem_documento','Qual o horário de funcionamento da loja?','consultar_politicas',[]),
                ('politica_com_memoria','Qual é meu veículo salvo e posso pagar com dinheiro na retirada?','consultar_politicas',['Celta','dinheiro'])]:
                if nome=='politica_com_memoria':
                    sistema.confirmar_veiculo('cliente_rag_demo',sessao,'V003')
                r=sistema.atender('cliente_rag_demo',sessao,pergunta,salvar=False)
                chamadas=[c for m in r['trajetoria'] for c in m.get('tool_calls',[])]
                texto=(r.get('resposta') or '').lower()
                criterio=r['status']=='ok' and any(c['name']==ferramenta for c in chamadas) and all(t.lower() in texto for t in termos)
                retornos=[]
                for m in r['trajetoria']:
                    if m.get('ferramenta')==ferramenta:
                        try:
                            retornos.append(json.loads(m['conteudo']))
                        except (ValueError,TypeError):
                            pass
                if nome=='catalogo_filtrado':
                    criterio=criterio and any(t.get('status')=='ok' and t.get('produtos')
                        and t.get('plano',{}).get('categoria')=='vela'
                        and t.get('plano',{}).get('preco_max_centavos')==2000
                        and t.get('plano',{}).get('estoque')=='disponivel'
                        and t.get('plano',{}).get('ordenacao')=='preco_crescente' for t in retornos)
                elif nome=='assunto_sem_documento':
                    criterio=criterio and any(t.get('status')=='sem_evidencia' for t in retornos)
                else:
                    criterio=criterio and bool(r.get('fontes_documentais')) and any(t.get('status')=='ok' for t in retornos)
                casos.append({'caso':nome,'criterio_local_atendido':criterio,'revisao_semantica':'PENDENTE de inspeção assistida; a checagem local não prova suporte de todas as afirmações.','resultado':r})
                print(nome,'OK' if criterio else 'DIVERGENCIA',flush=True)
        finally:
            sistema.fechar()
            memoria.fechar()
    resultado={'modo':'OpenAI chat e embeddings reais; índice FAISS existente; sem ViaCEP nestes pedidos',
               'limites':'Baseline top-1 versus consulta original mais até três reescritas top-1; orçamento de recuperação maior no depois. Não isola ganho de reescrita do ganho de contextos.',
               'recuperacoes':recuperacoes,'text_to_query':{'criterio_local_atendido':query_ok,'resultado':consulta},'casos':casos}
    destino=registrar_execucao(resultado,prefixo='fase04_real')
    print('Evidência:',destino.name)
    sucesso=all(r['cobertura_depois'] for r in recuperacoes) and query_ok and all(c['criterio_local_atendido'] for c in casos)
    raise SystemExit(0 if sucesso else 1)


if __name__=='__main__':
    try:
        main()
    except Exception as erro:
        arquivo=registrar_execucao({'modo':'validação de integração interrompida','sucesso':False,
                                    'tipo_erro':type(erro).__name__,
                                    'limite':'Execução não concluída; não contabilizar como sucesso.'},prefixo='fase04_falha')
        print('Falha registrada:',arquivo.name)
        raise
