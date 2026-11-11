"""Migração 4: preserva origem e campos mínimos da consulta PJ."""

ESQUEMA_CLIENTE_API = """
BEGIN IMMEDIATE;
ALTER TABLE clientes ADD COLUMN nome_fantasia TEXT;
ALTER TABLE clientes ADD COLUMN origem_cadastro TEXT NOT NULL DEFAULT 'origem_nao_registrada';
ALTER TABLE clientes ADD COLUMN consultado_cnpj_em TEXT;
PRAGMA user_version=4;
COMMIT;
"""
