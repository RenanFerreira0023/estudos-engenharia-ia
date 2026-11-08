"""Executa seis situações de memória, isoladas dos dados pessoais de uso da CLI."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from auto_super_parts.agente_fase02 import registrar_execucao
from auto_super_parts.demonstracao_memoria import demonstrar


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--real',action='store_true',help='Usa OpenAI chat e embeddings reais; sem a opção usa fixtures identificadas.')
    parser.add_argument('--arquivo-env',type=Path)
    args = parser.parse_args()
    resultado = demonstrar('real' if args.real else 'simulado',args.arquivo_env)
    arquivo = registrar_execucao(resultado,prefixo='fase03_real' if args.real else 'fase03_simulado')
    print('Evidência:',arquivo.name)
    ok = resultado['persistencia_ok'] and resultado['recuperacao_vetorial_executada'] and all(c['criterio_local_atendido'] for c in resultado['casos'])
    print('Persistência em processo separado:',resultado['persistencia_ok'])
    print('Recuperação vetorial observada:',resultado['recuperacao_vetorial_executada'])
    raise SystemExit(0 if ok else 1)


if __name__=='__main__':
    main()
