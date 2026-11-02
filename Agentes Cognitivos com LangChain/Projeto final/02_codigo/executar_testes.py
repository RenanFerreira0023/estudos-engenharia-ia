import io
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


def main():
    pasta = Path(__file__).resolve().parent
    suite = unittest.defaultTestLoader.discover(str(pasta / "tests"))
    saida = io.StringIO()
    resultado = unittest.TextTestRunner(stream=saida, verbosity=2).run(suite)
    print(saida.getvalue())
    # EVIDÊNCIA contém somente resultados realmente executados, incluindo falhas.
    agora = datetime.now(timezone.utc)
    evidencia = pasta.parent / "04_avaliacao_e_evidencias/resultados" / f"fase01_unittest_{agora.strftime('%Y%m%dT%H%M%S%fZ')}.json"
    evidencia.write_text(json.dumps({
        "fase": 1, "modo": "testes locais com modelos simulados, sem API", "data_utc": agora.isoformat(),
        "python": sys.version.split()[0], "executados": resultado.testsRun,
        "falhas": len(resultado.failures), "erros": len(resultado.errors), "log": saida.getvalue(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Evidência:", evidencia.name)
    raise SystemExit(0 if resultado.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
