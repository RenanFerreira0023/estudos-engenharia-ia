import os
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


# Este e o "conhecimento" da nossa oficina.
# Neste exercicio, o modelo deve responder somente com base nestas informacoes.
# Se uma informacao nao estiver aqui, como o preco da troca de oleo, ele deve
# dizer que nao consta no contexto em vez de inventar um valor.
CONTEXTO_OFICINA = """
- Abre de segunda a sexta, das 08:00 as 18:00.
- Faz troca de oleo e alinhamento.
- O alinhamento custa R$ 120.
- Nao realiza servicos de pintura.
"""


# Cada item desta lista sera enviado separadamente para o modelo.
# Isso mostra o uso do invoke: uma chamada por pergunta.
PERGUNTAS = [
    "Quanto custa o alinhamento?",
    "Voces fazem pintura?",
    "Quanto custa a troca de oleo?",
]


def carregar_env_local():
    """Carrega OPENAI_API_KEY de um arquivo .env simples, se ele existir."""
    caminho_env = Path(__file__).with_name(".env")

    # Path(__file__).with_name(".env") procura o arquivo .env na mesma pasta
    # deste script, independentemente de onde o comando python foi executado.
    if not caminho_env.exists():
        return

    # O arquivo .env esperado e simples:
    # OPENAI_API_KEY=sua_chave_aqui
    #
    # Este loop ignora linhas vazias e comentarios, separa chave e valor pelo
    # primeiro sinal de igual, e coloca o resultado nas variaveis de ambiente.
    for linha in caminho_env.read_text(encoding="utf-8").splitlines():
        if not linha or linha.startswith("#") or "=" not in linha:
            continue

        chave, valor = linha.split("=", 1)
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")

        # Nao sobrescreve uma variavel que ja veio do sistema.
        # Assim, se OPENAI_API_KEY ja estiver definida no PowerShell, ela tem
        # prioridade sobre o valor do arquivo .env.
        os.environ.setdefault(chave, valor)


def criar_chain():
    """Cria a cadeia LCEL ligando o prompt ao modelo."""
    carregar_env_local()

    # ChatOpenAI precisa da chave da API para conseguir chamar o modelo.
    # A biblioteca langchain-openai procura automaticamente a variavel
    # OPENAI_API_KEY no ambiente.
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "Defina OPENAI_API_KEY no arquivo .env ou como variavel de ambiente."
        )

    # ChatPromptTemplate separa as mensagens por papel.
    #
    # system: regras de comportamento do assistente.
    # Aqui dizemos que ele deve responder em portugues, brevemente, usando
    # somente o contexto informado.
    #
    # human: entrada do usuario.
    # Aqui usamos variaveis do template: {contexto} e {pergunta}.
    # Essas variaveis serao preenchidas quando chamarmos chain.invoke(...).
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Responda em portugues, brevemente, somente com base no "
                "contexto informado. Nao invente informacoes.",
            ),
            (
                "human",
                "Contexto:\n{contexto}\n\nPergunta:\n{pergunta}",
            ),
        ]
    )

    # ChatOpenAI representa o modelo de chat da OpenAI dentro do LangChain.
    # temperature=0 deixa as respostas mais previsiveis, o que e bom para
    # exercicios e respostas baseadas em contexto.
    modelo = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # LCEL significa LangChain Expression Language.
    # O operador | monta uma sequencia:
    # 1. primeiro o prompt recebe as variaveis e vira mensagens;
    # 2. depois essas mensagens sao enviadas ao modelo.
    return prompt | modelo


def main():
    # Criamos a chain uma vez e reutilizamos para todas as perguntas.
    chain = criar_chain()

    for pergunta in PERGUNTAS:
        # invoke executa a chain com os valores das variaveis do template.
        # O dicionario abaixo preenche {contexto} e {pergunta}.
        resposta = chain.invoke(
            {
                "contexto": CONTEXTO_OFICINA,
                "pergunta": pergunta,
            }
        )

        # A resposta de ChatOpenAI e um objeto de mensagem.
        # O texto final fica em resposta.content.
        print(f"Pergunta: {pergunta}")
        print(f"Resposta: {resposta.content}")
        print()


if __name__ == "__main__":
    main()
