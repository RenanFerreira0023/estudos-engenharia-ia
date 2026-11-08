"""Seis verificações com API real, ativadas explicitamente; não substituem avaliação semântica."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from auto_super_parts.agente_fase02 import AtendimentoFase02, registrar_execucao
from auto_super_parts.chain_inicial import criar_modelo
from auto_super_parts.configuracao import ErroConfiguracao

CASOS = [
    ('celta_oleo', 'Tenho um Celta 2012 1.0 8V flex original. Qual óleo e intervalo de troca?', 'oleo', 'V003', ['5W-30','API SL','10.000 km','5.000 km']),
    ('s10_oleo', 'Tenho uma S10 2014 2.8 CTDI diesel original. Qual viscosidade e intervalo de troca do óleo?', 'oleo', 'V005', ['dexos2','20.000 km','API CI-4']),
    ('fusca_oleo_pendente', 'Tenho um Fusca 1982 1600 a ar gasolina original. Qual viscosidade de óleo e quantos litros?', 'oleo', 'V004', ['Não tenho especificações verificadas']),
    ('celta_pneus', 'Tenho Celta 2012 1.0 8V flex, rodas originais e pneus 165/70 R13 79T. Qual pressão a frio com até três pessoas?', 'pneus', 'V003', ['27']),
    ('celta_alternador', 'Tenho Celta 2012 1.0 8V flex original com ar-condicionado. Qual amperagem de alternador consta no manual?', 'alternador', 'V003', ['90']),
    ('celta_correia', 'Tenho Celta 2012 1.0 8V flex original. Tem correia dentada? Qual intervalo de troca consta na base?', 'sincronismo', 'V003', ['correia dentada','precisam de confirmação']),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--real',action='store_true',help='Autoriza as seis chamadas reais ao modelo configurado.')
    parser.add_argument('--arquivo-env',type=Path,help='Arquivo opcional explicitamente escolhido; segredo nunca é registrado.')
    args = parser.parse_args()
    if not args.real:
        parser.exit(2,'Use --real para executar com API. Para testes offline, execute executar_testes.py.\n')
    try:
        sistema = AtendimentoFase02(modelo=criar_modelo(arquivo_env=args.arquivo_env))
    except ErroConfiguracao as erro:
        parser.exit(2,f'Configuração: {erro}\n')
    registros = []
    try:
        # INVOKE independente: verifica o agente atual, sem atribuir memória entre casos.
        for nome, pergunta, assunto, vid, trechos in CASOS:
            r = sistema.atender(pergunta,salvar=False)
            chamadas = [c for m in r['trajetoria'] for c in m.get('tool_calls',[])]
            consulta = any(c['name']=='consultar_informacao_tecnica' and c['args'].get('assunto')==assunto and c['args'].get('veiculo_id')==vid for c in chamadas)
            texto = r.get('resposta') or ''
            criterio = r['status']=='ok' and consulta and all(t in texto for t in trechos)
            if nome=='fusca_oleo_pendente':
                criterio = criterio and '20W' not in texto and '5W' not in texto
            registros.append({'caso':nome,'assunto_esperado':assunto,'veiculo_esperado':vid,'consulta_correta':consulta,'criterio_local_atendido':criterio,'resultado':r})
            print(nome, 'OK' if criterio else 'DIVERGENCIA', 'consulta:',consulta)
    finally:
        sistema.fechar()
    # EVIDÊNCIA é da execução observada; checagem por trechos não prova correção universal.
    arquivo = registrar_execucao({'modo':'API real OpenAI; fonte técnica JSON local; ViaCEP não solicitado','criterio':'Consulta correta e trechos esperados; avaliação limitada, sem juiz LLM ou LangSmith','casos':registros},prefixo='base_manual_real')
    print('Evidência:',arquivo.name)
    raise SystemExit(0 if all(r['criterio_local_atendido'] for r in registros) else 1)


if __name__ == '__main__':
    main()
