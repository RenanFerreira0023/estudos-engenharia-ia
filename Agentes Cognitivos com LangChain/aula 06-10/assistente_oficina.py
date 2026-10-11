import os
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


# Este e o "conhecimento" da oficina.
# O assistente deve responder somente com base nessas informacoes.
CONTEXTO_OFICINA = """
- Abre de segunda a sexta, das 08:00 as 18:00.
- Faz troca de oleo e alinhamento.
- O alinhamento custa R$ 120.
- Nao realiza servicos de pintura.
"""


def carregar_env_local():
    """Carrega a OPENAI_API_KEY do arquivo .env da mesma pasta."""
    caminho_env = Path(__file__).with_name(".env")

    if not caminho_env.exists():
        return

    for linha in caminho_env.read_text(encoding="utf-8").splitlines():
        if not linha or linha.startswith("#") or "=" not in linha:
            continue

        chave, valor = linha.split("=", 1)
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")

        os.environ.setdefault(chave, valor)


def criar_chain():
    """Cria a chain do LangChain conectando prompt e modelo."""
    carregar_env_local()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "Defina OPENAI_API_KEY no arquivo .env ou como variavel de ambiente."
        )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Responda em portugues, brevemente, somente com base no "
                "contexto informado. Se a informacao nao estiver no contexto, "
                "diga que ela nao consta no contexto. Nao invente informacoes.",
            ),
            (
                "human",
                "Contexto:\n{contexto}\n\nPergunta:\n{pergunta}",
            ),
        ]
    )

    modelo = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # LCEL: conecta a saida do prompt diretamente ao modelo.
    return prompt | modelo


def main():
    chain = criar_chain()

    print("Assistente da oficina")
    print("Digite sua pergunta ou escreva 'sair' para encerrar.")
    print()

    while True:
        pergunta = input("Voce: ").strip()

        if pergunta.lower() == "sair":
            print("Assistente: Ate mais!")
            break

        if not pergunta:
            print("Assistente: Digite uma pergunta para eu responder.")
            continue

        resposta = chain.invoke(
            {
                "contexto": CONTEXTO_OFICINA,
                "pergunta": pergunta,
            }
        )

        print(f"Assistente: {resposta.content}")
        print()


if __name__ == "__main__":
    main()
