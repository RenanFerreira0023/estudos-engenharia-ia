"""Preferências pessoais explicitamente confirmadas pelo usuário."""

ESQUEMA_PREFERENCIAS = '''
BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS preferencias_usuario (
 empresa_id TEXT NOT NULL,
 usuario_id TEXT NOT NULL,
 chave TEXT NOT NULL,
 valor TEXT NOT NULL,
 versao INTEGER NOT NULL CHECK(versao > 0),
 atualizado_em TEXT NOT NULL,
 PRIMARY KEY(empresa_id,usuario_id,chave),
 FOREIGN KEY(empresa_id,usuario_id) REFERENCES usuarios(empresa_id,id)
);
CREATE TABLE IF NOT EXISTS historico_preferencias (
 id INTEGER PRIMARY KEY,
 empresa_id TEXT NOT NULL,
 usuario_id TEXT NOT NULL,
 chave TEXT NOT NULL,
 valor TEXT NOT NULL,
 versao INTEGER NOT NULL,
 alterado_em TEXT NOT NULL,
 origem TEXT NOT NULL CHECK(origem='comando_explicito'),
 FOREIGN KEY(empresa_id,usuario_id) REFERENCES usuarios(empresa_id,id)
);
CREATE INDEX IF NOT EXISTS historico_preferencias_usuario
 ON historico_preferencias(empresa_id,usuario_id,chave,versao);
PRAGMA user_version=9;
COMMIT;
'''
