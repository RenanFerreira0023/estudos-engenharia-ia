import os
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


# CONTEXTO:
# Aqui fica a base de conhecimento do assistente.
# O modelo nao consulta banco de dados nem internet; ele recebe este texto
# junto com cada pergunta do usuario.
CONTEXTO_OFICINA = """
- Abre de segunda a sexta, das 08:00 as 18:00.
- Faz troca de oleo e alinhamento.
- O alinhamento custa R$ 120.
- Nao realiza servicos de pintura.
"""


def carregar_env_local():
    """Carrega a OPENAI_API_KEY do arquivo .env da mesma pasta."""
    # VARIAVEL DE AMBIENTE:
    # A chave da API nao fica escrita no codigo. Ela fica no .env e e carregada
    # para os.environ, que e onde a biblioteca da OpenAI procura a chave.
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

    # PROMPT TEMPLATE:
    # O ChatPromptTemplate cria uma estrutura de mensagens reutilizavel.
    # As partes {contexto} e {pergunta} sao variaveis preenchidas no invoke.
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                # SYSTEM:
                # Define as regras de comportamento do assistente.
                # Aqui pedimos resposta curta, em portugues e limitada ao contexto.
                "system",
                "Responda em portugues, brevemente, somente com base no "
                "contexto informado. Se a informacao nao estiver no contexto, "
                "diga que ela nao consta no contexto. Nao invente informacoes.",
            ),
            (
                # HUMAN:
                # Representa a mensagem do usuario enviada ao modelo.
                # Neste exercicio, juntamos o contexto fixo com a pergunta digitada.
                "human",
                "Contexto:\n{contexto}\n\nPergunta:\n{pergunta}",
            ),
        ]
    )

    # MODELO:
    # ChatOpenAI e a classe do LangChain que chama um modelo de chat da OpenAI.
    # temperature=0 deixa as respostas mais previsiveis para estudo.
    modelo = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # LCEL:
    # O operador | conecta as etapas da chain:
    # entrada do usuario -> prompt formatado -> modelo -> resposta.
    return prompt | modelo


def exibir_conceitos_estudados():
    """Mostra no terminal o fluxo do exercicio em linguagem de estudo."""
    print("Como este exercicio funciona:")
    print("1. O CONTEXTO guarda o que a oficina sabe responder.")
    print("2. O PROMPT separa as regras em system e a pergunta em human.")
    print("3. O MODELO usado e o ChatOpenAI.")
    print("4. A CHAIN liga prompt e modelo com LCEL: prompt | modelo.")
    print("5. O input() pega sua pergunta no terminal.")
    print("6. O invoke() envia contexto + pergunta para a chain.")
    print("7. O .content pega apenas o texto da resposta do modelo.")
    print()


def main():
    # CHAIN:
    # A chain junta prompt e modelo. Depois podemos reutiliza-la para varias
    # perguntas sem recriar tudo a cada interacao.
    chain = criar_chain()

    print("Assistente da oficina")
    print("Digite sua pergunta ou escreva 'sair' para encerrar.")
    print()
    exibir_conceitos_estudados()

    while True:
        # INPUT:
        # input() torna o exercicio interativo, permitindo que o usuario digite
        # perguntas no terminal.
        pergunta = input("Voce: ").strip()

        if pergunta.lower() == "sair":
            print("Assistente: Ate mais!")
            break

        if not pergunta:
            print("Assistente: Digite uma pergunta para eu responder.")
            continue

        # INVOKE:
        # Executa a chain uma vez, preenchendo as variaveis do template.
        print("[estudo] Agora o invoke() vai executar a chain com sua pergunta.")
        resposta = chain.invoke(
            {
                "contexto": CONTEXTO_OFICINA,
                "pergunta": pergunta,
            }
        )

        # CONTENT:
        # O retorno do modelo e um objeto de mensagem.
        # O texto final da resposta fica no atributo .content.
        print(f"Assistente: {resposta.content}")
        print()


if __name__ == "__main__":
    main()
