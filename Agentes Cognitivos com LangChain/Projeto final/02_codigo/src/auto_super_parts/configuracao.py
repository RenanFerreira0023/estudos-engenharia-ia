import os
from pathlib import Path

from dotenv import dotenv_values


class ErroConfiguracao(RuntimeError):
    """Configuração ausente ou ilegível, sem incluir credenciais na mensagem."""


def localizar_projeto(origem=None):
    # MARCADOR identifica o pacote copiado, sem contar níveis nem conhecer a pasta do repositório externo.
    ponto = Path(origem or __file__).resolve()
    if ponto.is_file():
        ponto = ponto.parent
    for candidato in (ponto, *ponto.parents):
        if ((candidato / "INSTRUCOES_PARA_IA_PROGRAMADORA.md").is_file()
                and (candidato / "02_codigo/src/auto_super_parts").is_dir()):
            return candidato
    raise ErroConfiguracao("Pasta do projeto não localizada. Copie o projeto completo, incluindo suas instruções.")


def obter_chave_api(arquivo_env=None):
    # AMBIENTE tem prioridade inclusive quando a variável está vazia: não há fallback silencioso nesse caso.
    chave = os.environ.get("OPENAI_API_KEY")
    if chave is None:
        projeto = localizar_projeto()
        caminho = Path(arquivo_env) if arquivo_env is not None else Path(".env")
        if not caminho.is_absolute():
            caminho = projeto / caminho
        # DOTENV_VALUES lê apenas este arquivo explícito e não modifica os.environ.
        # Não há busca automática em pastas ancestrais ou no diretório de execução.
        try:
            valores = dotenv_values(caminho, encoding="utf-8") if caminho.is_file() else {}
        except OSError:
            raise ErroConfiguracao("Não foi possível ler o arquivo local de configuração informado.") from None
        chave = valores.get("OPENAI_API_KEY")
    if not isinstance(chave, str) or not chave.strip():
        raise ErroConfiguracao("Defina OPENAI_API_KEY no ambiente ou no .env da pasta deste projeto.")
    return chave.strip()
