"""Exemplo reprodutível importado pelo notebook, com fixture claramente identificada."""
from pathlib import Path
import re
import tempfile

from .atendimento_memoria import criar_embeddings
from .catalogo_fase02 import Catalogo
from .chain_inicial import criar_modelo
from .planos_consulta import PlanoBusca,criar_reescritor,criar_planejador_catalogo,consultar_catalogo_planejado
from .rag_politicas import PoliticasRAG,preparar_indice


class VetoresDemonstracao:
    model='fixture-rag-notebook-sem-API'
    def embed_documents(self,textos):
        return [[float(j==i) for j in range(4)] for i,_ in enumerate(textos)]
    def embed_query(self,texto):
        i=1 if re.search(r'\bentrega\b|\bfrete\b',texto.lower()) else 0
        return [float(j==i) for j in range(4)]


def demonstrar(modo='simulado',arquivo_env=None):
    if modo not in ('real','simulado'):
        raise ValueError('Modo deve ser real ou simulado.')
    pergunta='Posso pagar com cartão em três vezes e tenho frete grátis em Curitiba?'
    pergunta_catalogo='Liste as velas com estoque até R$ 20,00, da mais barata para a mais cara.'
    catalogo=Catalogo()
    try:
        with tempfile.TemporaryDirectory(prefix='rag_notebook_') as tmp:
            if modo=='real':
                modelo=criar_modelo(arquivo_env)
                rag=PoliticasRAG(criar_embeddings(arquivo_env))
                reescrever=criar_reescritor(modelo,[d['secao'] for d in rag.manifesto['documentos']])
                planejador=criar_planejador_catalogo(modelo,catalogo.listar_veiculos()['veiculos'])
            else:
                # FIXTURE: rotas/vetores explícitos só demonstram infraestrutura, sem compreensão de LLM.
                emb=VetoresDemonstracao()
                preparar_indice(emb,Path(tmp)/'indice',origem_embedding='fixture local identificada, sem API')
                rag=PoliticasRAG(emb,Path(tmp)/'indice')
                reescrever=lambda _:PlanoBusca(consultas=['pagamento cartão parcelamento','entrega frete Curitiba'],assuntos_sem_documento=[])
                planejador=lambda _:{'consulta_valida':True,'veiculo_id':None,'categoria':'vela','estoque':'disponivel',
                                    'preco_max_centavos':2000,'ordenacao':'preco_crescente','limite':10,'pendencias':[]}
            antes=rag.buscar(pergunta,k=1)
            rag.reescrever=reescrever
            depois=rag.consultar(pergunta)
            consulta=consultar_catalogo_planejado(catalogo,pergunta_catalogo,planejador)
            return {'modo':modo,'origem_embedding':rag.manifesto['origem_embedding'],
                    'pergunta':pergunta,'antes':antes,'depois':depois,
                    'pergunta_catalogo':pergunta_catalogo,'consulta_catalogo':consulta,
                    'limite':'Simulado não mede qualidade semântica. O depois usa mais consultas/contextos; comparar esse custo explicitamente.'}
    finally:
        catalogo.fechar()
