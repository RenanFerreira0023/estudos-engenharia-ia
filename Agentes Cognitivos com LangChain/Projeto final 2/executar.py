"""Ponto de entrada portátil do projeto acadêmico; não depende do repositório de autopeças."""
from pathlib import Path
import sys

# PACOTE LOCAL: resolve src a partir deste arquivo, sem caminho pessoal de Windows.
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from secretaria.cli import main

if __name__=='__main__':
    raise SystemExit(main())
