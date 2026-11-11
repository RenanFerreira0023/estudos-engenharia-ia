"""Recortes extrativos dos turnos que saem da janela curta."""

ESQUEMA_RESUMOS = '''
BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS resumos_turnos_agente (
 id INTEGER PRIMARY KEY,
 sessao_id TEXT NOT NULL,
 empresa_id TEXT NOT NULL,
 usuario_id TEXT NOT NULL,
 turno_id INTEGER NOT NULL UNIQUE,
 resumo TEXT NOT NULL,
 criado_em TEXT NOT NULL,
 FOREIGN KEY(sessao_id) REFERENCES sessoes_agente(id),
 FOREIGN KEY(turno_id) REFERENCES turnos_agente(id),
 FOREIGN KEY(empresa_id,usuario_id) REFERENCES usuarios(empresa_id,id)
);
CREATE INDEX IF NOT EXISTS resumos_turnos_escopo
 ON resumos_turnos_agente(sessao_id,empresa_id,usuario_id,turno_id);
PRAGMA user_version=8;
COMMIT;
'''
