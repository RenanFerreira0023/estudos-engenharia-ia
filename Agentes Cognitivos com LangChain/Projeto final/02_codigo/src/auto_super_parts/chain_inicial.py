import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

# EXECUÇÃO DIRETA permite o botão do VS Code sem exigir PYTHONPATH no terminal.
# Ao importar pelo notebook ou executar com -m, o contexto do pacote já existe.
if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "auto_super_parts"

from langchain_core.exceptions import OutputParserException
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda, chain
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from .prompts import criar_templates
from .configuracao import ErroConfiguracao, obter_chave_api
from .schemas import EntradaMensagem, ResultadoProcessamento


def criar_modelo(arquivo_env=None):
    # CONFIGURAÇÃO prioriza o ambiente; o arquivo opcional pertence ao projeto copiado.
    chave = obter_chave_api(arquivo_env)
    # CHATOPENAI chama somente o modelo de chat definido na arquitetura; embeddings são de fases futuras.
    return ChatOpenAI(model="gpt-4o-mini", api_key=chave, temperature=0, max_retries=0, timeout=45)


def validar_entrada(entrada):
    return EntradaMensagem.model_validate(entrada).model_dump()


@dataclass
class Composicoes:
    lcel: Runnable
    decorada: Runnable
    prompt: Runnable
    parser: Runnable


def criar_chains(modelo=None, template="chat"):
    if template not in ("chat", "texto"):
        raise ValueError("Template deve ser chat ou texto.")
    texto, chat, parser = criar_templates()
    prompt = chat if template == "chat" else texto
    if modelo is None:
        modelo = criar_modelo()
    # LCEL declara a sequência entrada -> prompt -> modelo -> parser, sem chamar a API na montagem.
    lcel = RunnableLambda(validar_entrada) | prompt | modelo | parser

    # @CHAIN demonstra a mesma transformação com controle explícito das etapas.
    # CONFIG é propagada para manter callbacks/tags de quem executar, sem adicionar ferramentas.
    @chain
    def decorada(entrada: dict, config: RunnableConfig):
        dados = validar_entrada(entrada)
        mensagens = prompt.invoke(dados, config=config)
        resposta = modelo.invoke(mensagens, config=config)
        return parser.invoke(resposta, config=config)

    return Composicoes(lcel=lcel, decorada=decorada, prompt=prompt, parser=parser)


def processar_mensagem(fluxo, mensagem):
    # VALIDAÇÃO DE ENTRADA acontece antes de chamar a LLM, inclusive para espaços vazios.
    try:
        entrada = EntradaMensagem(mensagem=mensagem)
    except ValidationError as erro:
        return ResultadoProcessamento(status="erro_entrada", erros=[e["msg"] for e in erro.errors()])
    try:
        # INVOKE devolve um BaseModel já validado; MODEL_DUMP_JSON serializa o resultado final.
        dados = fluxo.invoke(entrada.model_dump())
        return ResultadoProcessamento(status="ok", dados=dados)
    except OutputParserException as erro:
        # ERRO DO PARSER é distinto de falha de conexão. Não há reparo ou repetição automática nesta fase.
        causa = erro.__cause__
        detalhes = [f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in causa.errors()] if isinstance(causa, ValidationError) else ["O modelo não devolveu JSON compatível com o contrato."]
        return ResultadoProcessamento(status="erro_validacao", erros=detalhes)
    except Exception as erro:
        # Exibe só a classe do erro da API: não serializa configuração, headers ou credenciais.
        return ResultadoProcessamento(status="erro_modelo", erros=[f"Falha ao executar o modelo ({type(erro).__name__})."])


def exibir_conceitos_estudados():
    print("[estudo] PromptTemplate e ChatPromptTemplate organizam a mesma tarefa.")
    print("[estudo] LCEL e @chain compõem prompt, modelo e PydanticOutputParser.")
    print("[estudo] BaseModel valida tipos; Python recalcula os campos necessários à intenção.")
    print("[estudo] invoke() processa uma entrada; batch() processa uma lista no notebook.")
    print("[estudo] input() recebe novas mensagens independentes; não há memória nesta fase.")


def main():
    parser = argparse.ArgumentParser(description="Somente fase 1: chain inicial da Auto Super Parts CWB.")
    parser.add_argument("--mensagem", help="Processa uma mensagem e encerra, sem abrir o modo interativo.")
    args = parser.parse_args()
    try:
        fluxo = criar_chains().lcel
    except ErroConfiguracao as erro:
        parser.exit(2, f"Configuração: {erro}\n")
    if args.mensagem is not None:
        print(processar_mensagem(fluxo, args.mensagem).model_dump_json(indent=2))
        return
    exibir_conceitos_estudados()
    # INPUT fica na CLI; a lógica importada pelo notebook não pede entrada interativa.
    while True:
        mensagem = input("\nMensagem (Enter ou /sair encerra): ").strip()
        if not mensagem or mensagem.lower() == "/sair":
            break
        print(processar_mensagem(fluxo, mensagem).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
