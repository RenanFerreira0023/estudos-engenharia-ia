"""Migração 3: clientes, propostas de visita e agenda operacional."""

ESQUEMA_AGENDA = """
BEGIN IMMEDIATE;
CREATE TABLE clientes (
 id INTEGER PRIMARY KEY, empresa_id TEXT NOT NULL, nome TEXT NOT NULL,
 tipo_pessoa TEXT NOT NULL CHECK(tipo_pessoa IN ('PF','PJ')),
 cnpj TEXT, criado_por TEXT NOT NULL, criado_em TEXT NOT NULL,
 UNIQUE(empresa_id,id), FOREIGN KEY(empresa_id,criado_por) REFERENCES usuarios(empresa_id,id));
CREATE UNIQUE INDEX clientes_cnpj ON clientes(empresa_id,cnpj) WHERE cnpj IS NOT NULL;
CREATE TABLE propostas_visita (
 id INTEGER PRIMARY KEY, empresa_id TEXT NOT NULL, solicitante_id TEXT NOT NULL,
 cliente_id INTEGER NOT NULL, atendente_id TEXT NOT NULL, inicio_em TEXT NOT NULL,
 fim_em TEXT NOT NULL, endereco_json TEXT NOT NULL, estado TEXT NOT NULL
 CHECK(estado IN ('pendente','confirmada','cancelada','conflito')),
 criada_em TEXT NOT NULL, expira_em TEXT NOT NULL, confirmada_em TEXT,
 UNIQUE(empresa_id,id),
 FOREIGN KEY(empresa_id,solicitante_id) REFERENCES usuarios(empresa_id,id),
 FOREIGN KEY(empresa_id,atendente_id) REFERENCES usuarios(empresa_id,id),
 FOREIGN KEY(empresa_id,cliente_id) REFERENCES clientes(empresa_id,id));
CREATE TABLE agendamentos (
 id INTEGER PRIMARY KEY, empresa_id TEXT NOT NULL, proposta_id INTEGER NOT NULL,
 cliente_id INTEGER NOT NULL, atendente_id TEXT NOT NULL, solicitante_id TEXT NOT NULL,
 inicio_em TEXT NOT NULL, fim_em TEXT NOT NULL, endereco_snapshot_json TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('confirmado','cancelado')),
 versao INTEGER NOT NULL, criado_em TEXT NOT NULL,
 UNIQUE(empresa_id,proposta_id), UNIQUE(empresa_id,id),
 FOREIGN KEY(empresa_id,proposta_id) REFERENCES propostas_visita(empresa_id,id),
 FOREIGN KEY(empresa_id,cliente_id) REFERENCES clientes(empresa_id,id),
 FOREIGN KEY(empresa_id,atendente_id) REFERENCES usuarios(empresa_id,id),
 FOREIGN KEY(empresa_id,solicitante_id) REFERENCES usuarios(empresa_id,id));
CREATE INDEX agenda_intervalo ON agendamentos(empresa_id,atendente_id,inicio_em,fim_em);
CREATE TABLE auditoria_agenda (
 id INTEGER PRIMARY KEY, empresa_id TEXT NOT NULL, ator_id TEXT NOT NULL,
 entidade TEXT NOT NULL, entidade_id INTEGER NOT NULL, operacao TEXT NOT NULL,
 antes_json TEXT, depois_json TEXT NOT NULL, instante TEXT NOT NULL,
 FOREIGN KEY(empresa_id,ator_id) REFERENCES usuarios(empresa_id,id));
PRAGMA user_version=3;
COMMIT;
"""
