import argparse
import os
import tempfile
import sys
from datetime import datetime, timezone
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager


def main():
    parser = argparse.ArgumentParser(description="Executa o notebook da fase selecionada em kernel novo.")
    parser.add_argument("--fase", choices=("1", "2", "3"), default="1")
    parser.add_argument("--modo", choices=("real", "simulado"), default="real")
    parser.add_argument("--saida", type=Path, help="Destino opcional; por padrão atualiza o notebook da fase selecionada.")
    parser.add_argument("--kernel", default="auto-super-parts-fase01", help="Nome registrado do kernel (padrão: auto-super-parts-fase01).")
    args = parser.parse_args()
    projeto = Path(__file__).resolve().parent.parent
    nome_notebook = {"1":"fase_01_chain_inicial.ipynb", "2":"fase_02_agente_ferramentas.ipynb", "3":"fase_03_memoria.ipynb"}[args.fase]
    origem = projeto / "03_notebooks" / nome_notebook
    notebook = nbformat.read(origem, as_version=4)
    # KERNEL NOVO e limpeza de saídas evitam aproveitar variáveis ou resultados de execução anterior.
    for celula in notebook.cells:
        if celula.cell_type == "code":
            celula.outputs = []
            celula.execution_count = None
    ambiente = {**os.environ, f"FASE0{args.fase}_MODO": args.modo, "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        with tempfile.TemporaryDirectory(prefix=f"fase0{args.fase}_jupyter_") as temporario:
            ambiente["JUPYTER_RUNTIME_DIR"] = temporario
            ambiente["IPYTHONDIR"] = temporario
            # KERNEL da .venv atual tem preferência sobre registros globais com o mesmo nome.
            locais = [str(Path(sys.prefix) / "share/jupyter/kernels"), *KernelSpecManager().kernel_dirs]
            specs = KernelSpecManager(kernel_dirs=locais)
            manager = KernelManager(kernel_name=args.kernel, kernel_spec_manager=specs,
                                    connection_file=str(Path(temporario) / "kernel.json"))
            notebook.metadata.kernelspec = {"name": args.kernel, "display_name": "Auto Super Parts CWB (.venv)", "language": "python"}
            cliente = NotebookClient(notebook, timeout=600, km=manager, kernel_name=args.kernel, resources={"metadata": {"path": str(origem.parent)}})
            cliente.execute(env=ambiente, cleanup_kc=True)
    except Exception as erro:
        # Notebook parcial de falha fica separado; nunca substitui evidência anterior de sucesso.
        nome = f"fase0{args.fase}_notebook_falha_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}.ipynb"
        destino = projeto / "04_avaliacao_e_evidencias/resultados" / nome
        nbformat.write(notebook, destino)
        print(f"Falha ({type(erro).__name__}); execução parcial preservada em {destino.name}.")
        raise SystemExit(1) from None
    destino = args.saida or origem
    nbformat.write(notebook, destino)
    print(f"Notebook executado do início ao fim ({args.modo}): {destino.name}")


if __name__ == "__main__":
    main()
