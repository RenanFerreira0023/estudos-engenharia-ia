"""Índice FAISS preparado fora da consulta; SQLite continua sendo a fonte original."""
from hashlib import sha256
import json
import os
from pathlib import Path


def _versao(mensagens):
    digest = sha256()
    for mensagem in mensagens:
        digest.update(json.dumps(
            [mensagem['id'], mensagem['instante_utc'], mensagem['texto']],
            ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
    return digest.hexdigest()


def pasta_indice_do_banco(banco):
    """Separa índices de bancos de teste que estão na mesma pasta privada."""
    identificador = sha256(str(banco.caminho.resolve()).encode('utf-8')).hexdigest()[:12]
    return banco.caminho.parent / 'indices' / identificador


def corpora_acessiveis(banco, ctx):
    usuario = banco._usuario(ctx)
    if usuario['perfil'] == 'administrador':
        linhas = banco.con.execute(
            'SELECT id,nome,criado_por FROM corpora WHERE empresa_id=? ORDER BY id',
            (ctx.empresa_id,))
    else:
        linhas = banco.con.execute(
            '''SELECT id,nome,criado_por FROM corpora
               WHERE empresa_id=? AND criado_por=? ORDER BY id''',
            (ctx.empresa_id,ctx.usuario_id))
    return [dict(linha) for linha in linhas]


class IndiceFontes:
    def __init__(self, banco, pasta):
        self.banco = banco
        self.pasta = Path(pasta)

    def _arquivos(self, corpus_id):
        if type(corpus_id) is not int or corpus_id < 1:
            raise ValueError('ID de corpus inválido.')
        base = self.pasta / f'corpus-{corpus_id}'
        return base.with_suffix('.faiss'), base.with_suffix('.json')

    def _mensagens(self, ctx, corpus_id):
        self.banco._corpus(ctx, corpus_id)
        return [dict(linha) for linha in self.banco.con.execute(
            '''SELECT id,instante_utc,autor,texto FROM mensagens_importadas
               WHERE empresa_id=? AND corpus_id=? ORDER BY id''',
            (ctx.empresa_id, corpus_id))]

    def preparar(self, ctx, corpus_id, embeddings, modelo_id):
        """Ação explícita: pode enviar textos ao provedor de embeddings configurado."""
        import faiss
        import numpy as np

        mensagens = self._mensagens(ctx, corpus_id)
        if not mensagens:
            raise ValueError('Corpus sem mensagens para indexar.')
        if not isinstance(modelo_id, str) or not modelo_id.strip():
            raise ValueError('Identifique o modelo de embeddings.')
        indice_path, manifesto_path = self._arquivos(corpus_id)
        versao = _versao(mensagens)
        if indice_path.is_file() and manifesto_path.is_file():
            manifesto = json.loads(manifesto_path.read_text(encoding='utf-8'))
            if (manifesto.get('versao_corpus') == versao and
                    manifesto.get('modelo_id') == modelo_id and
                    manifesto.get('empresa_id') == ctx.empresa_id):
                return {'estado':'atual','mensagens':len(mensagens),'versao_corpus':versao}
        vetores = np.asarray(embeddings.embed_documents([m['texto'] for m in mensagens]),
                             dtype='float32')
        if vetores.ndim != 2 or len(vetores) != len(mensagens) or vetores.shape[1] == 0:
            raise ValueError('Embeddings incompatíveis com as mensagens.')
        faiss.normalize_L2(vetores)
        indice = faiss.IndexFlatIP(vetores.shape[1])
        indice.add(vetores)
        manifesto = {'empresa_id':ctx.empresa_id,'corpus_id':corpus_id,
                     'versao_corpus':versao,'modelo_id':modelo_id,
                     'ids':[m['id'] for m in mensagens], 'dimensoes':vetores.shape[1]}
        self.pasta.mkdir(parents=True, exist_ok=True)
        temporario_indice = indice_path.with_suffix('.faiss.tmp')
        temporario_manifesto = manifesto_path.with_suffix('.json.tmp')
        faiss.write_index(indice,str(temporario_indice))
        temporario_manifesto.write_text(json.dumps(manifesto,ensure_ascii=False),encoding='utf-8')
        os.replace(temporario_indice,indice_path)
        os.replace(temporario_manifesto,manifesto_path)
        return {'estado':'preparado','mensagens':len(mensagens),'versao_corpus':versao}

    def buscar(self, ctx, corpus_id, pergunta, embeddings, modelo_id, limite=3):
        """Carrega índice existente; recusa índice desatualizado e revalida acesso no SQLite."""
        import faiss
        import numpy as np

        if type(limite) is not int or not 1 <= limite <= 10:
            raise ValueError('Limite deve estar entre 1 e 10.')
        if not isinstance(pergunta,str) or not pergunta.strip():
            raise ValueError('Informe a pergunta.')
        mensagens = self._mensagens(ctx, corpus_id)
        indice_path, manifesto_path = self._arquivos(corpus_id)
        if not indice_path.is_file() or not manifesto_path.is_file():
            raise ValueError('Índice não preparado para este corpus.')
        manifesto = json.loads(manifesto_path.read_text(encoding='utf-8'))
        if (manifesto.get('empresa_id') != ctx.empresa_id or
                manifesto.get('corpus_id') != corpus_id or
                manifesto.get('modelo_id') != modelo_id or
                manifesto.get('versao_corpus') != _versao(mensagens) or
                manifesto.get('ids') != [m['id'] for m in mensagens]):
            raise ValueError('Índice desatualizado ou de outro corpus; prepare novamente.')
        indice = faiss.read_index(str(indice_path))
        if indice.ntotal != len(mensagens) or indice.d != manifesto.get('dimensoes'):
            raise ValueError('Índice incompatível com o manifesto.')
        vetor = np.asarray([embeddings.embed_query(pergunta)],dtype='float32')
        if vetor.ndim != 2 or vetor.shape[1] != indice.d:
            raise ValueError('Dimensões da consulta incompatíveis.')
        faiss.normalize_L2(vetor)
        escores, posicoes = indice.search(vetor,min(limite,len(mensagens)))
        return [{'corpus_id':corpus_id,'mensagem_id':mensagens[int(posicao)]['id'],
                 'instante_utc':mensagens[int(posicao)]['instante_utc'],
                 'autor':mensagens[int(posicao)]['autor'],
                 'texto':mensagens[int(posicao)]['texto'],
                 'similaridade':round(float(escore),4)}
                for escore,posicao in zip(escores[0],posicoes[0]) if posicao >= 0]
