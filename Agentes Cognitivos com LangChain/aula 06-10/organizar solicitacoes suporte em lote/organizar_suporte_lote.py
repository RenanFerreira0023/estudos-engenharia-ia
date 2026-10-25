import os
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class FichaSuporte(BaseModel):
    # SAIDA ESTRUTURADA:
    # O BaseModel define os campos que o modelo deve devolver. O Field explica
    # como preencher cada campo, como se fosse a ficha que o sistema espera.
    cliente: str = Field(
        description=(
            "Nome informado na mensagem. Quando nao houver nome, use "
            "'Nao informado'."
        )
    )
    resumo: str = Field(
        description="Descricao curta da solicitacao, sem adicionar fatos."
    )
    categoria: str = Field(
        description=(
            "Use 'erro' quando houver uma falha relatada, ou 'duvida' quando "
            "o cliente pedir orientacao."
        )
    )


MENSAGENS_EXEMPLO = [
    "Sou Ana. Nao consigo entrar no sistema desde hoje cedo.",
    "Meu nome e Bruno. Gostaria de saber como alterar meu e-mail.",
    "O relatorio de vendas aparece em branco quando abro a pagina.",
]


def carregar_env_raiz():
    """Carrega o .env da raiz do repositorio, preservando o ambiente existente."""
    # CONFIGURACAO COMPARTILHADA: partimos deste script e subimos de exercicio
    # para aula, disciplina e raiz. O caminho independe da pasta do terminal.
    caminho_env = Path(__file__).resolve().parents[3] / ".env"
    if not caminho_env.is_file():
        return
    for linha in caminho_env.read_text(encoding="utf-8-sig").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        # SETDEFAULT preserva variaveis ja definidas no sistema ou no terminal.
        os.environ.setdefault(chave.strip(), valor.strip().strip("\"'"))


def criar_chain():
    """Cria a chain para transformar mensagens livres em fichas estruturadas."""
    carregar_env_raiz()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "Defina OPENAI_API_KEY no .env da raiz do repositorio ou como variavel de ambiente."
        )

    # PROMPT TEMPLATE:
    # O prompt orienta a extracao e recebe a variavel {mensagem}. Cada mensagem
    # digitada pelo usuario vai preencher essa variavel.
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Extraia os dados da mensagem de suporte e preencha a ficha. "
                "Nao invente informacoes. Se o nome do cliente nao aparecer, "
                "use exatamente 'Nao informado'. A categoria deve ser somente "
                "'erro' ou 'duvida'.",
            ),
            ("human", "Mensagem do cliente:\n{mensagem}"),
        ]
    )

    # MODELO ESTRUTURADO:
    # with_structured_output pede ao modelo uma resposta no formato da classe
    # FichaSuporte, em vez de devolver apenas um texto livre.
    modelo = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    modelo_estruturado = modelo.with_structured_output(FichaSuporte)

    # LCEL:
    # O operador | liga as etapas do fluxo: entrada -> prompt -> modelo com
    # saida estruturada.
    return prompt | modelo_estruturado


def exibir_conceitos_estudados():
    """Mostra no terminal o fluxo do exercicio em linguagem de estudo."""
    print("Como este exercicio funciona:")
    print("1. O BaseModel define a ficha que queremos receber.")
    print("2. O Field explica como preencher cada campo da ficha.")
    print("3. O input() coleta mensagens digitadas no terminal.")
    print("4. O PROMPT recebe cada mensagem na variavel {mensagem}.")
    print("5. O MODELO ESTRUTURADO usa with_structured_output(FichaSuporte).")
    print("6. A CHAIN liga prompt e modelo com LCEL: prompt | modelo_estruturado.")
    print("7. O BATCH processa a lista de mensagens digitadas de uma vez.")
    print("8. Cada resposta volta como objeto FichaSuporte.")
    print()


def coletar_mensagens():
    """Coleta mensagens no terminal para montar o lote de suporte."""
    mensagens = []

    print("Digite mensagens de clientes para organizar em lote.")
    print("Pressione Enter vazio para usar os exemplos do desafio.")
    print("Digite 'fim' para processar as mensagens informadas.")
    print()
    print("Exemplos do desafio:")
    for mensagem in MENSAGENS_EXEMPLO:
        print(f"- {mensagem}")
    print()

    while True:
        # INPUT:
        # Cada input() adiciona uma mensagem ao lote. Assim o exercicio continua
        # usando batch, mas com dados digitados por voce no terminal.
        mensagem = input("Mensagem do cliente: ").strip()

        if not mensagem:
            if mensagens:
                print("[estudo] Entrada vazia: vou processar o lote digitado.")
                break

            print("[estudo] Nenhuma mensagem digitada: vou usar os exemplos.")
            return MENSAGENS_EXEMPLO

        if mensagem.lower() == "fim":
            if mensagens:
                break

            print("Digite pelo menos uma mensagem ou pressione Enter para usar exemplos.")
            continue

        mensagens.append(mensagem)
        print(f"[estudo] Mensagem {len(mensagens)} adicionada ao lote.")

    return mensagens


def main():
    chain = criar_chain()

    exibir_conceitos_estudados()
    mensagens = coletar_mensagens()

    # BATCH:
    # O batch processa varias entradas de uma vez. Cada dicionario precisa ter a
    # chave mensagem, porque esse e o nome da variavel usada no prompt.
    entradas = [{"mensagem": mensagem} for mensagem in mensagens]

    print()
    print("[estudo] Agora o batch() vai processar as mensagens dos clientes.")
    print()
    fichas = chain.batch(entradas)

    # OBJETO RETORNADO:
    # Cada resultado ja vem como FichaSuporte, entao o codigo acessa cliente,
    # resumo e categoria diretamente pelos atributos.
    for indice, ficha in enumerate(fichas, start=1):
        print(f"Ficha {indice}")
        print(f"Cliente: {ficha.cliente}")
        print(f"Resumo: {ficha.resumo}")
        print(f"Categoria: {ficha.categoria}")
        print()


if __name__ == "__main__":
    main()
