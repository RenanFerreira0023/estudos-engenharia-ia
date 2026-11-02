"""Reproduz testes offline em uma cópia renomeada com .venv criada do zero."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from gerar_pacote import incluir


def main():
    projeto = Path(__file__).resolve().parent.parent
    temporario = Path(tempfile.mkdtemp(prefix="fase02_reproducao_"))
    copia = temporario / "pacote_renomeado"

    # CÓPIA ISOLADA exclui configuração privada e artefatos, usando a mesma regra do pacote de entrega.
    def ignorar(pasta, nomes):
        return [nome for nome in nomes if not incluir(Path(pasta).relative_to(projeto) / nome)]

    shutil.copytree(projeto, copia, ignore=ignorar)
    agora = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    evidencia = projeto / "04_avaliacao_e_evidencias/resultados" / f"fase02_reproducao_{agora}.json"
    ambiente = {k: v for k, v in os.environ.items() if k not in ("OPENAI_API_KEY", "PYTHONPATH")}
    ambiente.update(PYTHONDONTWRITEBYTECODE="1", PIP_DISABLE_PIP_VERSION_CHECK="1")
    python = copia / ".venv/Scripts/python.exe" if os.name == "nt" else copia / ".venv/bin/python"
    registro = {"fase": 2, "modo": "reprodução offline em ambiente novo", "copia": str(copia),
                "env_privado_copiado": (copia / ".env").exists(), "passos": []}

    def executar(nome, comando, esperado=0):
        # SUBPROCESSO registra o observado antes de avaliar; uma falha não vira aprovação por edição do log.
        print(nome, flush=True)
        retorno = subprocess.run([str(c) for c in comando], cwd=copia, env=ambiente,
                                 capture_output=True, text=True, encoding="utf-8", errors="replace")
        registro["passos"].append({"nome": nome, "comando": [str(c) for c in comando],
                                   "codigo_esperado": esperado, "codigo_observado": retorno.returncode,
                                   "stdout": retorno.stdout, "stderr": retorno.stderr})
        evidencia.write_text(json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if retorno.returncode != esperado:
            raise RuntimeError(f"Passo falhou: {nome}. Consulte {evidencia.name}")

    executar("Criar venv", [sys.executable, "-m", "venv", copia / ".venv"])
    executar("Instalar requirements", [python, "-m", "pip", "install", "-r", copia / "02_codigo/requirements.txt"])
    executar("pip check", [python, "-m", "pip", "check"])
    executar("Regressão fase 1", [python, "-B", copia / "02_codigo/executar_testes.py"])
    executar("Testes fase 2", [python, "-B", copia / "02_codigo/verificar_fase02.py"])
    executar("Registrar kernel local", [python, "-m", "ipykernel", "install", "--prefix", copia / ".venv",
                                        "--name", "auto-super-parts-fase01", "--display-name", "Auto Super Parts CWB (.venv)"])
    executar("Notebook fase 2 offline", [python, "-B", copia / "02_codigo/executar_notebook.py", "--fase", "2", "--modo", "simulado"])
    executar("CLI sem segredo pede configuração", [python, "-B", copia / "02_codigo/src/auto_super_parts/agente_fase02.py",
                                                   "--mensagem", "Teste sem chave"], esperado=2)
    registro["concluido"] = True
    registro["limite"] = "Reprodução offline: API real comprovada em evidências separadas; não foi copiada credencial."
    evidencia.write_text(json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Reprodução concluída:", evidencia.name, flush=True)
    print("Cópia preservada:", copia, flush=True)


if __name__ == "__main__":
    main()
