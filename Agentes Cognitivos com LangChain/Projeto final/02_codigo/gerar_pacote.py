import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path


def incluir(caminho):
    # ENTREGA contém código/documentação/evidências, sem configuração privada ou artefatos de execução.
    partes = {p.casefold() for p in caminho.parts}
    nome = caminho.name.casefold()
    return (not partes.intersection({"__pycache__", ".venv", ".git", ".ipynb_checkpoints"})
            and caminho.suffix.casefold() not in (".pyc", ".pyo")
            and (nome == ".env.example" or not (nome == ".env" or nome.startswith(".env.") or nome.endswith(".env"))))


def main():
    projeto = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Gera ZIP do projeto sem caches, .venv ou .env real.")
    parser.add_argument("--saida", type=Path, default=projeto.parent / f"{projeto.name}.zip")
    args = parser.parse_args()
    destino = args.saida.resolve()
    if destino.is_relative_to(projeto) or destino.suffix.lower() != ".zip":
        parser.error("Use um arquivo .zip fora da pasta do projeto.")
    anterior = hashlib.sha256(destino.read_bytes()).hexdigest() if destino.exists() else None
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destino.parent, suffix=".tmp", delete=False) as arquivo:
        temporario = Path(arquivo.name)
    try:
        with zipfile.ZipFile(temporario, "w", compression=zipfile.ZIP_DEFLATED) as pacote:
            for arquivo in sorted(projeto.rglob("*")):
                relativo = arquivo.relative_to(projeto)
                if arquivo.is_file() and incluir(relativo):
                    pacote.write(arquivo, Path(projeto.name) / relativo)
        # CONFERÊNCIA do ZIP ocorre antes da substituição do arquivo de entrega anterior.
        with zipfile.ZipFile(temporario) as pacote:
            nomes = pacote.namelist()
            if not all(incluir(Path(nome)) for nome in nomes) or pacote.testzip() is not None:
                raise RuntimeError("O pacote não passou na conferência de conteúdo/integridade.")
        os.replace(temporario, destino)
    finally:
        temporario.unlink(missing_ok=True)
    print(json.dumps({"arquivo": str(destino), "arquivos": len(nomes), "sha256_anterior": anterior,
                      "sha256": hashlib.sha256(destino.read_bytes()).hexdigest(),
                      "caches_env_venv_excluidos": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
