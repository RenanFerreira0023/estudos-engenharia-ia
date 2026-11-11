"""Migração 10: orçamento, parcelas e pagamentos operacionais confirmados."""

ESQUEMA_FINANCEIRO = '''
BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS orcamentos (
 id INTEGER PRIMARY KEY, empresa_id TEXT NOT NULL, projeto_id INTEGER NOT NULL,
 revisao INTEGER NOT NULL CHECK(revisao>0), valor_centavos INTEGER NOT NULL CHECK(valor_centavos>0),
 percentual_entrada_acordado INTEGER CHECK(percentual_entrada_acordado BETWEEN 0 AND 100),
 status TEXT NOT NULL CHECK(status IN ('proposto','aceito')),
 criado_por TEXT NOT NULL, criado_em TEXT NOT NULL, aceito_por TEXT, aceito_em TEXT,
 UNIQUE(empresa_id,id), UNIQUE(empresa_id,projeto_id,revisao),
 FOREIGN KEY(empresa_id,projeto_id) REFERENCES projetos(empresa_id,id),
 FOREIGN KEY(empresa_id,criado_por) REFERENCES usuarios(empresa_id,id),
 FOREIGN KEY(empresa_id,aceito_por) REFERENCES usuarios(empresa_id,id));
CREATE UNIQUE INDEX IF NOT EXISTS orcamento_aceito_por_projeto
 ON orcamentos(empresa_id,projeto_id) WHERE status='aceito';
CREATE TABLE IF NOT EXISTS parcelas (
 id INTEGER PRIMARY KEY, empresa_id TEXT NOT NULL, orcamento_id INTEGER NOT NULL,
 sequencia INTEGER NOT NULL CHECK(sequencia>0), valor_previsto_centavos INTEGER NOT NULL CHECK(valor_previsto_centavos>0),
 vencimento TEXT, lembrar_cobranca TEXT, descricao TEXT NOT NULL,
 UNIQUE(empresa_id,id), UNIQUE(empresa_id,orcamento_id,sequencia),
 FOREIGN KEY(empresa_id,orcamento_id) REFERENCES orcamentos(empresa_id,id));
CREATE TABLE IF NOT EXISTS pagamentos (
 id INTEGER PRIMARY KEY, empresa_id TEXT NOT NULL, parcela_id INTEGER NOT NULL,
 valor_centavos INTEGER NOT NULL CHECK(valor_centavos>0), data_pagamento TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('informado','confirmado')),
 chave_idempotencia TEXT NOT NULL, observacao TEXT NOT NULL,
 criado_por TEXT NOT NULL, criado_em TEXT NOT NULL, confirmado_por TEXT, confirmado_em TEXT,
 UNIQUE(empresa_id,id), UNIQUE(empresa_id,chave_idempotencia),
 FOREIGN KEY(empresa_id,parcela_id) REFERENCES parcelas(empresa_id,id),
 FOREIGN KEY(empresa_id,criado_por) REFERENCES usuarios(empresa_id,id),
 FOREIGN KEY(empresa_id,confirmado_por) REFERENCES usuarios(empresa_id,id));
CREATE TABLE IF NOT EXISTS auditoria_financeiro (
 id INTEGER PRIMARY KEY, empresa_id TEXT NOT NULL, usuario_id TEXT NOT NULL,
 entidade TEXT NOT NULL, entidade_id INTEGER NOT NULL, acao TEXT NOT NULL,
 detalhes_json TEXT NOT NULL, instante TEXT NOT NULL,
 FOREIGN KEY(empresa_id,usuario_id) REFERENCES usuarios(empresa_id,id));
PRAGMA user_version=10;
COMMIT;
'''
