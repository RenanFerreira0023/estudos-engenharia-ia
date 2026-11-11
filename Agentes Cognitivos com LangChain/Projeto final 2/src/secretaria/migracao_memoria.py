"""Conversas do agente separadas por empresa, usuário e sessão."""

ESQUEMA_MEMORIA = '''
BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS sessoes_agente (
 id TEXT PRIMARY KEY,
 empresa_id TEXT NOT NULL,
 usuario_id TEXT NOT NULL,
 criada_em TEXT NOT NULL,
 encerrada_em TEXT,
 FOREIGN KEY(empresa_id,usuario_id) REFERENCES usuarios(empresa_id,id)
);
CREATE INDEX IF NOT EXISTS sessoes_agente_usuario
 ON sessoes_agente(empresa_id,usuario_id,criada_em);
CREATE TABLE IF NOT EXISTS turnos_agente (
 id INTEGER PRIMARY KEY,
 sessao_id TEXT NOT NULL,
 empresa_id TEXT NOT NULL,
 usuario_id TEXT NOT NULL,
 pergunta TEXT NOT NULL,
 resposta TEXT NOT NULL,
 criado_em TEXT NOT NULL,
 FOREIGN KEY(sessao_id) REFERENCES sessoes_agente(id),
 FOREIGN KEY(empresa_id,usuario_id) REFERENCES usuarios(empresa_id,id)
);
CREATE INDEX IF NOT EXISTS turnos_agente_sessao ON turnos_agente(sessao_id,id);
PRAGMA user_version=7;
COMMIT;
'''
