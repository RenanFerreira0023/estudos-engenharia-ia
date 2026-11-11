"""Migração 11: histórico explícito de substituições e reversões financeiras."""

ESQUEMA_REVISOES_FINANCEIRAS = '''
BEGIN IMMEDIATE;
DROP INDEX IF EXISTS orcamento_aceito_por_projeto;
CREATE TABLE IF NOT EXISTS substituicoes_orcamento (
 empresa_id TEXT NOT NULL,
 anterior_id INTEGER NOT NULL,
 novo_id INTEGER NOT NULL,
 motivo TEXT NOT NULL,
 usuario_id TEXT NOT NULL,
 instante TEXT NOT NULL,
 PRIMARY KEY(empresa_id,anterior_id),
 UNIQUE(empresa_id,novo_id),
 FOREIGN KEY(empresa_id,anterior_id) REFERENCES orcamentos(empresa_id,id),
 FOREIGN KEY(empresa_id,novo_id) REFERENCES orcamentos(empresa_id,id),
 FOREIGN KEY(empresa_id,usuario_id) REFERENCES usuarios(empresa_id,id));
CREATE TABLE IF NOT EXISTS reversoes_pagamento (
 empresa_id TEXT NOT NULL,
 pagamento_id INTEGER NOT NULL,
 tipo TEXT NOT NULL CHECK(tipo IN ('cancelamento','estorno')),
 motivo TEXT NOT NULL,
 usuario_id TEXT NOT NULL,
 instante TEXT NOT NULL,
 PRIMARY KEY(empresa_id,pagamento_id),
 FOREIGN KEY(empresa_id,pagamento_id) REFERENCES pagamentos(empresa_id,id),
 FOREIGN KEY(empresa_id,usuario_id) REFERENCES usuarios(empresa_id,id));
PRAGMA user_version=11;
COMMIT;
'''
