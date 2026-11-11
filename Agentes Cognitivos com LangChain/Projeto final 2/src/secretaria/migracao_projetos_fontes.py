"""Migração 6: projeto e anotações confirmadas com FKs reais para as fontes."""

ESQUEMA_PROJETOS_FONTES = """
BEGIN IMMEDIATE;
CREATE TABLE projetos (
 id INTEGER PRIMARY KEY, empresa_id TEXT NOT NULL, cliente_id INTEGER,
 titulo TEXT NOT NULL, resumo TEXT NOT NULL, status TEXT NOT NULL,
 origem_proposta_id INTEGER NOT NULL, criado_por TEXT NOT NULL,
 criado_em TEXT NOT NULL, versao INTEGER NOT NULL CHECK(versao>0),
 UNIQUE(empresa_id,id), UNIQUE(empresa_id,origem_proposta_id),
 FOREIGN KEY(empresa_id,cliente_id) REFERENCES clientes(empresa_id,id),
 FOREIGN KEY(origem_proposta_id) REFERENCES propostas_revisao(id),
 FOREIGN KEY(empresa_id,criado_por) REFERENCES usuarios(empresa_id,id));
CREATE TABLE anotacoes_projeto (
 id INTEGER PRIMARY KEY, empresa_id TEXT NOT NULL, projeto_id INTEGER NOT NULL,
 proposta_id INTEGER NOT NULL, corpus_id INTEGER NOT NULL,
 area TEXT NOT NULL CHECK(area IN ('projeto','financeiro','agenda')),
 natureza TEXT NOT NULL, resumo TEXT NOT NULL, dados_json TEXT NOT NULL,
 criado_por TEXT NOT NULL, criado_em TEXT NOT NULL,
 UNIQUE(empresa_id,id), UNIQUE(empresa_id,proposta_id),
 FOREIGN KEY(empresa_id,projeto_id) REFERENCES projetos(empresa_id,id),
 FOREIGN KEY(proposta_id) REFERENCES propostas_revisao(id),
 FOREIGN KEY(empresa_id,corpus_id) REFERENCES corpora(empresa_id,id),
 FOREIGN KEY(empresa_id,criado_por) REFERENCES usuarios(empresa_id,id));
CREATE TABLE fontes_anotacao (
 empresa_id TEXT NOT NULL, corpus_id INTEGER NOT NULL,
 anotacao_id INTEGER NOT NULL, mensagem_id INTEGER NOT NULL,
 trecho_snapshot TEXT NOT NULL,
 PRIMARY KEY(empresa_id,anotacao_id,mensagem_id),
 FOREIGN KEY(empresa_id,anotacao_id) REFERENCES anotacoes_projeto(empresa_id,id),
 FOREIGN KEY(empresa_id,corpus_id,mensagem_id) REFERENCES mensagens_importadas(empresa_id,corpus_id,id));
CREATE INDEX anotacoes_por_projeto ON anotacoes_projeto(empresa_id,projeto_id,id);
PRAGMA user_version=6;
COMMIT;
"""
