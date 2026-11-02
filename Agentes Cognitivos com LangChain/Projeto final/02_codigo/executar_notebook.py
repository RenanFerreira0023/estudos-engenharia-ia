import argparse
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def main():
    parser = argparse.ArgumentParser(description="Executa apenas o notebook da fase 1, em kernel novo.")
    parser.add_argument("--modo", choices=("real", "simulado"), default="real")
    parser.add_argument("--saida", type=Path, help="Destino opcional; por padrão atualiza o notebook da fase 1.")
    args = parser.parse_args()
    projeto = Path(__file__).resolve().parent.parent
    origem = projeto / "03_notebooks/fase_01_chain_inicial.ipynb"
    notebook = nbformat.read(origem, as_version=4)
    # KERNEL NOVO e limpeza de saídas evitam aproveitar variáveis ou resultados de execução anterior.
    for celula in notebook.cells:
        if celula.cell_type == "code":
            celula.outputs = []
            celula.execution_count = None
    ambiente = {**os.environ, "FASE01_MODO": args.modo}
    try:
        with tempfile.TemporaryDirectory(prefix="fase01_jupyter_") as temporario:
            ambiente["JUPYTER_RUNTIME_DIR"] = temporario
            ambiente["IPYTHONDIR"] = temporario
            cliente = NotebookClient(notebook, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(origem.parent)}})
            cliente.execute(env=ambiente)
    except Exception as erro:
        # Notebook parcial de falha fica separado; nunca substitui evidência anterior de sucesso.
        nome = f"fase01_notebook_falha_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}.ipynb"
        destino = projeto / "04_avaliacao_e_evidencias/resultados" / nome
        nbformat.write(notebook, destino)
        print(f"Falha ({type(erro).__name__}); execução parcial preservada em {destino.name}.")
        raise SystemExit(1) from None
    destino = args.saida or origem
    nbformat.write(notebook, destino)
    print(f"Notebook executado do início ao fim ({args.modo}): {destino.name}")


if __name__ == "__main__":
    main()
