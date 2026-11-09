"""Índice documental preparado fora do atendimento; carregamento sem pickle."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import faiss
import numpy as np

from .configuracao import ErroConfiguracao, localizar_projeto


class ErroIndice(ErroConfiguracao):
    """Índice ausente, incompatível, desatualizado ou corrompido."""


def fonte_padrao():
    return localizar_projeto()/'02_codigo/documentos/politicas_loja.txt'


def pasta_indice_padrao():
    return localizar_projeto()/'02_codigo/indices/politicas'


def hash_bytes(conteudo):
    return hashlib.sha256(conteudo).hexdigest()


def separar_documentos(fonte):
    texto=Path(fonte).read_text(encoding='utf-8-sig')
    paragrafos=[p.strip() for p in re.split(r'\n\s*\n',texto) if p.strip()]
    # CHUNKING por parágrafo preserva regras completas em um corpus pequeno.
    if not paragrafos or not paragrafos[0].startswith('AUTO SUPER PARTS'):
        raise ValueError('Cabeçalho das políticas não reconhecido.')
    documentos=[]
    for i, texto in enumerate(paragrafos[1:],1):
        secao=texto.split(':',1)[0] if ':' in texto else 'Limites do orçamento'
        documentos.append({'id':f'POL-{i:02d}','fonte':Path(fonte).name,'secao':secao,
                           'texto':texto,'estado':'pendente' if 'políticas ainda não cadastradas' in texto else 'documentado'})
    if not documentos:
        raise ValueError('Documento sem políticas para indexar.')
    return documentos


def matriz_normalizada(vetores):
    matriz=np.asarray(vetores,dtype=np.float32)
    if matriz.ndim!=2 or not matriz.shape[0] or not 1 <= matriz.shape[1] <= 4096:
        raise ValueError('Dimensão de embeddings inválida.')
    if not np.isfinite(matriz).all() or (np.linalg.norm(matriz,axis=1)==0).any():
        raise ValueError('Embedding nulo ou não finito.')
    matriz=np.ascontiguousarray(matriz)
    faiss.normalize_L2(matriz)
    return matriz


def preparar_indice(embeddings, pasta=None, fonte=None, origem_embedding='não informada'):
    fonte=Path(fonte or fonte_padrao())
    pasta=Path(pasta or pasta_indice_padrao())
    modelo=getattr(embeddings,'model',None)
    if not modelo:
        raise ValueError('Modelo de embedding deve estar identificado.')
    documentos=separar_documentos(fonte)
    # EMBEDDINGS/FAISS: documentos são vetorizados uma vez; produto interno normalizado é cosseno.
    matriz=matriz_normalizada(embeddings.embed_documents([d['texto'] for d in documentos]))
    if len(matriz)!=len(documentos):
        raise ValueError('Quantidade de embeddings diferente dos documentos.')
    indice=faiss.IndexFlatIP(matriz.shape[1])
    indice.add(matriz)
    binario=faiss.serialize_index(indice).tobytes()
    manifesto={'schema_version':1,'modelo_embedding':modelo,'origem_embedding':origem_embedding,
               'criado_em':datetime.now(timezone.utc).isoformat(),'fonte':fonte.name,
               'sha256_fonte':hash_bytes(fonte.read_bytes()),'sha256_indice':hash_bytes(binario),
               'dimensao':matriz.shape[1],'quantidade':len(documentos),'documentos':documentos}
    pasta.mkdir(parents=True,exist_ok=True)
    (pasta/'politicas.faiss').write_bytes(binario)
    # MANIFESTO é gravado por último; pares incompletos são rejeitados ao carregar.
    (pasta/'manifesto.json').write_text(json.dumps(manifesto,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return manifesto


class PoliticasRAG:
    def __init__(self, embeddings, pasta=None, fonte=None, reescrever=None):
        self.embeddings=embeddings
        self.pasta=Path(pasta or pasta_indice_padrao())
        self.fonte=Path(fonte or fonte_padrao())
        self.reescrever=reescrever
        try:
            self.manifesto=json.loads((self.pasta/'manifesto.json').read_text(encoding='utf-8'))
            binario=(self.pasta/'politicas.faiss').read_bytes()
            m=self.manifesto
            if m['schema_version']!=1 or hash_bytes(binario)!=m['sha256_indice']:
                raise ValueError('Integridade do índice inválida.')
            if m['modelo_embedding']!=getattr(embeddings,'model',None):
                raise ValueError('Modelo de embedding incompatível.')
            self._conferir_fonte()
            if separar_documentos(self.fonte)!=m['documentos']:
                raise ValueError('Metadados não correspondem à fonte.')
            # LOAD: usa o índice existente e JSON, sem desserialização de objetos Python via pickle.
            self.indice=faiss.deserialize_index(np.frombuffer(binario,dtype=np.uint8))
            if self.indice.ntotal!=m['quantidade'] or self.indice.d!=m['dimensao'] or len(m['documentos'])!=m['quantidade']:
                raise ValueError('Índice e metadados divergentes.')
        except (OSError,ValueError,KeyError,TypeError,RuntimeError) as erro:
            raise ErroIndice('Índice de políticas indisponível/incompatível. Execute 02_codigo/preparar_politicas.py --real. '+type(erro).__name__) from None

    def _conferir_fonte(self):
        if hash_bytes(self.fonte.read_bytes())!=self.manifesto['sha256_fonte']:
            raise ValueError('Políticas alteradas: preparar o índice novamente.')

    def buscar(self, pergunta, k=1, similaridade_minima=0.25):
        if not isinstance(pergunta,str) or not 1 <= len(pergunta.strip()) <= 1000:
            raise ValueError('Pergunta deve ter de 1 a 1000 caracteres.')
        if type(k) is not int or not 1 <= k <= 4 or not -1 <= similaridade_minima <= 1:
            raise ValueError('Parâmetros de busca inválidos.')
        self._conferir_fonte()
        # RETRIEVAL faz somente embedding da consulta; nunca reindexa os documentos.
        vetor=matriz_normalizada([self.embeddings.embed_query(pergunta)])
        if vetor.shape[1]!=self.indice.d:
            raise ValueError('Embedding de consulta incompatível com o índice.')
        scores, ids=self.indice.search(vetor,min(k,self.indice.ntotal))
        return [{**self.manifesto['documentos'][int(i)],'similaridade':float(score)}
                for score,i in zip(scores[0],ids[0]) if i>=0 and float(score)>=similaridade_minima]

    def consultar(self, pergunta):
        if not isinstance(pergunta,str) or not 1<=len(pergunta.strip())<=1000:
            raise ValueError('Pergunta deve ter de 1 a 1000 caracteres.')
        consultas=[pergunta]
        ausentes=[]
        if self.reescrever:
            from .planos_consulta import PlanoBusca
            plano=PlanoBusca.model_validate(self.reescrever(pergunta))
            ausentes=plano.assuntos_sem_documento
            consultas=list(dict.fromkeys([pergunta,*plano.consultas])) if plano.consultas else []
        # MULTI-QUERY recupera por consulta e elimina repetições por ID, mantendo evidência de cada busca.
        por_id={}
        rastro=[]
        for consulta in consultas:
            trechos=self.buscar(consulta,k=1)
            rastro.append({'consulta':consulta,'ids':[d['id'] for d in trechos]})
            for d in trechos:
                if d['id'] not in por_id or d['similaridade']>por_id[d['id']]['similaridade']:
                    por_id[d['id']]=d
        documentos=list(por_id.values())
        # PROVENIÊNCIA: uma seção recuperada e documentada não é um documento ausente.
        # A sugestão do planejador fica preservada; isso não confirma todos os campos da seção.
        ausentes_sugeridos=list(ausentes)
        secoes_documentadas={d['secao'].strip().casefold() for d in documentos if d['estado']=='documentado'}
        ausentes=[a for a in ausentes if a.strip().casefold() not in secoes_documentadas]
        return {'status':'ok' if documentos else 'sem_evidencia','pergunta':pergunta,
                'estrategia':'decomposicao_multiquery' if self.reescrever else 'baseline_k1',
                'consultas_executadas':consultas,'assuntos_sem_documento':ausentes,
                'assuntos_sem_documento_sugeridos':ausentes_sugeridos,'rastro_busca':rastro,'documentos':documentos,
                'modelo_embedding':self.manifesto['modelo_embedding'],
                'limite':'Trechos da loja fictícia; ausência de política não significa negar direitos. Não invente condições.'}
