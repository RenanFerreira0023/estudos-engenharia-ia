"""Migração SQLite da fila; sem dependências opcionais de IA."""
ESQUEMA_REVISAO="""
BEGIN IMMEDIATE;
CREATE TABLE propostas_revisao(
 id INTEGER PRIMARY KEY,empresa_id TEXT NOT NULL,usuario_id TEXT NOT NULL,corpus_id INTEGER NOT NULL,
 chave TEXT NOT NULL,area TEXT NOT NULL CHECK(area IN ('projeto','financeiro','agenda')),
 estado TEXT NOT NULL CHECK(estado IN ('pendente','aceita','rejeitada')),
 versao INTEGER NOT NULL CHECK(versao>0),original_json TEXT NOT NULL,atual_json TEXT NOT NULL,
 origem TEXT NOT NULL CHECK(origem IN ('fixture_manual','api_real')),criado_em TEXT NOT NULL,atualizado_em TEXT NOT NULL,
 UNIQUE(empresa_id,usuario_id,corpus_id,chave),
 FOREIGN KEY(empresa_id,usuario_id) REFERENCES usuarios(empresa_id,id),
 FOREIGN KEY(empresa_id,corpus_id) REFERENCES corpora(empresa_id,id));
CREATE TABLE historico_revisao(
 id INTEGER PRIMARY KEY,proposta_id INTEGER NOT NULL,ator_usuario_id TEXT NOT NULL,
 acao TEXT NOT NULL CHECK(acao IN ('registrar','corrigir','aceitar','rejeitar')),
 versao_anterior INTEGER NOT NULL,versao_nova INTEGER NOT NULL,
 antes_json TEXT,depois_json TEXT NOT NULL,comentario TEXT NOT NULL,instante TEXT NOT NULL,
 FOREIGN KEY(proposta_id) REFERENCES propostas_revisao(id));
PRAGMA user_version=2;
COMMIT;
"""
