"""Migração 5: consulta de CNPJ, proposta e confirmação auditada do cliente PJ."""

ESQUEMA_CADASTRO_CLIENTE = """
BEGIN IMMEDIATE;
CREATE TABLE consultas_cnpj (
 id INTEGER PRIMARY KEY, empresa_id TEXT NOT NULL, usuario_id TEXT NOT NULL,
 cnpj TEXT NOT NULL, dados_json TEXT NOT NULL, consultado_em TEXT NOT NULL,
 UNIQUE(empresa_id,id),
 FOREIGN KEY(empresa_id,usuario_id) REFERENCES usuarios(empresa_id,id));
CREATE TABLE propostas_cliente (
 id INTEGER PRIMARY KEY, empresa_id TEXT NOT NULL, solicitante_id TEXT NOT NULL,
 consulta_id INTEGER NOT NULL, estado TEXT NOT NULL
 CHECK(estado IN ('pendente','confirmada','conflito')),
 criada_em TEXT NOT NULL, expira_em TEXT NOT NULL, confirmada_em TEXT,
 cliente_id INTEGER, UNIQUE(empresa_id,id),
 FOREIGN KEY(empresa_id,solicitante_id) REFERENCES usuarios(empresa_id,id),
 FOREIGN KEY(empresa_id,consulta_id) REFERENCES consultas_cnpj(empresa_id,id),
 FOREIGN KEY(empresa_id,cliente_id) REFERENCES clientes(empresa_id,id));
CREATE TABLE auditoria_clientes (
 id INTEGER PRIMARY KEY, empresa_id TEXT NOT NULL, ator_id TEXT NOT NULL,
 proposta_id INTEGER NOT NULL, cliente_id INTEGER NOT NULL,
 operacao TEXT NOT NULL, dados_json TEXT NOT NULL, instante TEXT NOT NULL,
 FOREIGN KEY(empresa_id,ator_id) REFERENCES usuarios(empresa_id,id),
 FOREIGN KEY(empresa_id,proposta_id) REFERENCES propostas_cliente(empresa_id,id),
 FOREIGN KEY(empresa_id,cliente_id) REFERENCES clientes(empresa_id,id));
PRAGMA user_version=5;
COMMIT;
"""
