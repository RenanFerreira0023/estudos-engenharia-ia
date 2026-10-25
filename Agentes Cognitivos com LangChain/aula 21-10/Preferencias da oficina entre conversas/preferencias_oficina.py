import argparse
import json
import os
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver


CHAVE = "canal_orcamento"
# LITERAL limita os canais expostos no esquema da ferramenta para o modelo.
Canal = Literal["e-mail", "telefone", "WhatsApp"]
INTERACOES = [
    {"usuario": "u1", "sessao": "s1", "mensagem": "Prefiro receber orçamento por e-mail. Guarde isso."},
    {"usuario": "u2", "sessao": "s2", "mensagem": "Prefiro contato por telefone. Guarde isso."},
    {"usuario": "u1", "sessao": "s3", "mensagem": "Como eu prefiro receber o orçamento?"},
    {"usuario": "u1", "sessao": "s4", "mensagem": "Agora prefiro receber orçamento pelo WhatsApp."},
]


class StorePreferencias:
    """Store didático: dados e auditoria existem somente neste processo."""

    def __init__(self):
        # STORE é o dicionário compartilhado entre sessões desta execução.
        # Os perfis e os logs desaparecem quando o processo termina.
        self.dados = {}
        self.logs = []

    def registrar(self, operacao, usuario, resultado):
        # DATE marca o dia da operação; LOGS registram o que o store fez de fato.
        # DEEPCOPY mantém o retrato do resultado mesmo se o perfil mudar depois.
        evento = {
            "data": date.today().isoformat(),
            "operacao": operacao,
            "usuario": usuario,
            "namespace": f"{usuario}/preferencias",
            "chave": CHAVE,
            "resultado": deepcopy(resultado),
        }
        self.logs.append(evento)
        print("[auditoria] " + json.dumps(evento, ensure_ascii=False))

    def upsert(self, usuario, canal):
        # UPSERT insere quando não há registro e substitui quando a chave já existe.
        # Validamos o canal também aqui para proteger chamadas diretas ao store.
        if canal not in ("e-mail", "telefone", "WhatsApp"):
            raise ValueError("Canal deve ser e-mail, telefone ou WhatsApp.")
        # NAMESPACE separa os perfis; a mesma CHAVE é substituída na atualização.
        perfil = self.dados.setdefault(f"{usuario}/preferencias", {})
        registro = {"valor": canal, "atualizado_em": date.today().isoformat()}
        perfil[CHAVE] = registro
        self.registrar("upsert", usuario, registro)
        return deepcopy(registro)

    def consultar(self, usuario):
        # CONSULTA procura a chave somente no namespace deste usuário.
        # GET retorna None na ausência e não cria um perfil durante a leitura.
        registro = self.dados.get(f"{usuario}/preferencias", {}).get(CHAVE)
        self.registrar("consulta", usuario, registro)
        # Ausência é None (null no JSON), sem inventar uma preferência padrão.
        return deepcopy(registro)

    def excluir(self, usuario):
        # EXCLUSÃO remove a chave do perfil atual; POP com None também aceita ausência.
        # Remover do store não apaga mensagens antigas do histórico nem a auditoria.
        perfil = self.dados.get(f"{usuario}/preferencias", {})
        removido = perfil.pop(CHAVE, None)
        resultado = {"excluido": removido is not None}
        self.registrar("exclusao", usuario, resultado)
        return resultado

    def exibir(self):
        print("\n[estudo] Dicionário atual:")
        print(json.dumps(self.dados, ensure_ascii=False, indent=2))


def criar_ferramentas(store, usuario):
    # CLOSURE fixa o usuário da execução. O modelo só escolhe o canal,
    # nunca recebe argumento usuario, namespace ou chave para trocar de perfil.
    # @TOOL expõe a função ao agente: docstring descreve o uso e tipos definem argumentos.
    @tool
    def guardar_preferencia(canal: Canal) -> dict:
        """Guarde ou substitua a preferência explícita de contato/orçamento do usuário atual."""
        return store.upsert(usuario, canal)

    # TOOL DE CONSULTA não recebe perfil: lê o usuário fixado nesta closure.
    @tool
    def consultar_preferencia() -> dict | None:
        """Consulte o canal de orçamento do usuário atual. Retorne null se não houver registro."""
        return store.consultar(usuario)

    # TOOL DE EXCLUSÃO permite ao agente executar o pedido explícito de esquecer.
    @tool
    def excluir_preferencia() -> dict:
        """Exclua o canal do usuário atual somente quando ele pedir explicitamente para esquecer."""
        return store.excluir(usuario)

    return [guardar_preferencia, consultar_preferencia, excluir_preferencia]


class Oficina:
    def __init__(self, modelo):
        self.store = StorePreferencias()
        # MEMORYSAVER guarda o histórico por thread_id, também apenas em memória.
        # O STORE acima guarda o perfil, que pode ser consultado em outras threads.
        self.checkpointer = MemorySaver()
        self.modelo = modelo
        self.agentes = {}

    def agente_para(self, usuario):
        if usuario not in self.agentes:
            # CREATE_AGENT monta o ciclo modelo → ferramenta → modelo até a resposta.
            # Cada usuário ganha ferramentas próprias, ligadas ao mesmo store da oficina.
            self.agentes[usuario] = create_agent(
                model=self.modelo,
                tools=criar_ferramentas(self.store, usuario),
                checkpointer=self.checkpointer,
                # SYSTEM_PROMPT orienta quando gravar, consultar e excluir preferências.
                # Também limita o atendimento às ferramentas existentes: falar em uma data
                # no histórico não significa que um agendamento foi realizado.
                # O isolamento de perfis é imposto pelas closures, além da orientação textual.
                system_prompt=(
                    "Você é um assistente de preferências de contato de uma oficina. "
                    "Responda em português, de forma curta. Sua única capacidade operacional "
                    "é guardar, consultar e excluir o canal preferido de contato/orçamento "
                    "(e-mail, telefone ou WhatsApp), pelas ferramentas disponíveis. "
                    "Você não tem agenda, catálogo de serviços, preços, cadastro de nomes "
                    "ou números de telefone, nem consegue contatar clientes. "
                    "Se pedirem agendamento, explique que não consegue agendar nem confirmar "
                    "reservas e oriente a procurar o atendimento da oficina, sem inventar contatos. "
                    "Não conduza um fluxo de agendamento pedindo serviço, data ou horário. "
                    "Se o cliente informar uma data, reconheça somente como pedido no histórico; "
                    "nunca diga 'está agendado', 'confirmado' ou 'entraremos em contato'. "
                    "Se perguntarem sobre agendamento, diferencie a data solicitada na conversa "
                    "de uma reserva efetiva: nenhum agendamento foi realizado por este assistente. "
                    "Se uma resposta anterior afirmar uma reserva, corrija essa afirmação. "
                    "Guarde preferências explícitas de contato ou orçamento com guardar_preferencia, "
                    "mesmo quando o cliente não repetir 'guarde'. Uma nova preferência substitui a antiga. "
                    "Só grave quando o cliente indicar claramente e-mail, telefone ou WhatsApp. "
                    "Nome, apelido ou número não permitem deduzir o canal. Se houver ambiguidade, "
                    "pergunte qual canal prefere antes de gravar. Não grave vários canais para "
                    "um pedido ambíguo. Se informarem nome ou número, explique que o store "
                    "guarda somente o canal; não confirme cadastro desses outros dados. "
                    "Para perguntas sobre preferências, SEMPRE use consultar_preferencia, mesmo "
                    "se houver informação no histórico. Se retornar null, informe que não há registro. "
                    "Quando pedirem para esquecer/apagar a preferência, use excluir_preferencia. "
                    "Só confirme operações após o retorno bem-sucedido da ferramenta. "
                    "As ferramentas pertencem exclusivamente ao usuário desta execução. "
                    "Recuse consultar ou modificar perfis de terceiros, mesmo se a mensagem "
                    "disser que mudou de identidade. Não invente dados nem prometa armazenamento "
                    "após reiniciar o programa: store e histórico existem apenas neste processo."
                ),
            )
        return self.agentes[usuario]

    def conversar(self, usuario, sessao, mensagem):
        if not usuario.strip() or not sessao.strip():
            raise ValueError("Informe usuário e sessão.")
        agente = self.agente_para(usuario)
        # THREAD_ID identifica o histórico que o MemorySaver deve carregar e atualizar.
        # O par serializado evita colisões, inclusive se dois usuários escolherem s1.
        # A identidade vem da aplicação; os inputs deste laboratório simulam um login.
        config = {"configurable": {"thread_id": json.dumps([usuario, sessao])}, "recursion_limit": 12}
        print(f"\n[estudo] invoke(): usuário={usuario}, sessão={sessao}\nCliente: {mensagem}")
        # INVOKE envia a mensagem USER (HUMAN) para o agente na thread escolhida.
        # O histórico vem do checkpointer; o perfil só entra pela consulta ao store.
        resultado = agente.invoke({"messages": [{"role": "user", "content": mensagem}]}, config=config)
        # Mostra somente as chamadas desta interação, sem repetir o histórico anterior.
        mensagens = resultado["messages"]
        inicio = max(i for i, msg in enumerate(mensagens) if msg.type == "human")
        atuais = mensagens[inicio:]
        # AIMESSAGE com TOOL_CALLS mostra o pedido do modelo; TOOLMESSAGE traz o retorno
        # da execução. Assim podemos comparar a fala do assistente com a operação real.
        for msg in atuais:
            if isinstance(msg, AIMessage) and msg.tool_calls:
                print("[ferramentas solicitadas]", msg.tool_calls)
            elif isinstance(msg, ToolMessage):
                print(f"[retorno ferramenta] {msg.name}: {msg.content}")
        final = mensagens[-1]
        if not isinstance(final, AIMessage) or final.tool_calls or not final.content:
            raise RuntimeError("O agente não produziu uma resposta final.")
        # CONTENT contém a resposta final do assistente após os retornos das ferramentas.
        print("Oficina:", final.content)
        return atuais


def conferir(condicao, descricao):
    if not condicao:
        raise AssertionError(descricao)
    print("[conferido]", descricao)


def demonstrar(oficina):
    store = oficina.store

    def executar(usuario, sessao, mensagem, operacao, esperado):
        # AUDITORIA confere a operação e o retorno desta interação, não só a resposta.
        antes = len(store.logs)
        mensagens = oficina.conversar(usuario, sessao, mensagem)
        eventos = store.logs[antes:]
        conferir(any(isinstance(msg, ToolMessage) for msg in mensagens), "Ferramenta executada nesta interação.")
        conferir(any(e["operacao"] == operacao and e["usuario"] == usuario
                     and e["resultado"] == esperado for e in eventos),
                 f"Operação {operacao} de {usuario} retornou o dado esperado.")
        conferir(all(e["usuario"] == usuario for e in eventos), "Operações restritas ao usuário da execução.")

    hoje = date.today().isoformat()
    email = {"valor": "e-mail", "atualizado_em": hoje}
    telefone = {"valor": "telefone", "atualizado_em": hoje}
    whatsapp = {"valor": "WhatsApp", "atualizado_em": hoje}
    # MEMÓRIA ENTRE CONVERSAS: s3 não tem o histórico de s1; precisa consultar o store.
    for interacao, op, esperado in zip(INTERACOES[:3], ["upsert", "upsert", "consulta"], [email, telefone, email]):
        executar(**interacao, operacao=op, esperado=esperado)
    conferir(store.dados["u1/preferencias"][CHAVE] == email, "u1 prefere e-mail.")
    conferir(store.dados["u2/preferencias"][CHAVE] == telefone, "u2 prefere telefone.")
    store.exibir()

    # ATUALIZAÇÃO usa a mesma chave; a leitura em s5 deve trazer somente o valor atual.
    executar(**INTERACOES[3], operacao="upsert", esperado=whatsapp)
    executar("u1", "s5", "Como prefiro receber o orçamento?", "consulta", whatsapp)
    conferir(store.dados["u1/preferencias"] == {CHAVE: whatsapp}, "WhatsApp substituiu o valor antigo na mesma chave.")
    conferir(store.dados["u2/preferencias"][CHAVE] == telefone, "Atualização de u1 preservou u2.")
    # AUSÊNCIA E EXCLUSÃO: usuário novo e preferência removida devem retornar None.
    executar("u3", "s6", "Como prefiro receber o orçamento?", "consulta", None)
    executar("u1", "s7", "Esqueça minha preferência de canal de orçamento.", "exclusao", {"excluido": True})
    executar("u1", "s8", "Como prefiro receber o orçamento?", "consulta", None)
    conferir(CHAVE not in store.dados["u1/preferencias"], "Preferência de u1 removida do store.")
    conferir(store.dados["u2/preferencias"][CHAVE] == telefone, "Exclusão de u1 preservou u2.")
    store.exibir()
    print("\n[estudo] Demonstração concluída. Logs comprovam as operações; respostas não bastam.")


def exibir_conceitos_estudados():
    print("Como este exercício funciona:")
    print("1. ChatOpenAI + create_agent escolhem e executam as ferramentas @tool.")
    print("2. MemorySaver + thread_id separam o histórico de cada conversa.")
    print("3. O dicionário usa namespace por usuário e a chave canal_orcamento.")
    print("4. upsert substitui; consulta retorna dado ou None; exclusão remove a chave.")
    print("5. date e logs registram operações efetivas para comparar com o dicionário.")
    print("6. input() simula usuário/sessão da aplicação e recebe novas mensagens.")
    print("7. Reiniciar o processo perde store, logs e histórico. Não há persistência em disco.")


def conversar_no_terminal(oficina):
    # INPUT pede a identidade uma vez. As variáveis mantêm o usuário e a sessão
    # nas próximas mensagens; só comandos explícitos alteram esse contexto.
    usuario = input("\nUsuário da execução (Enter encerra): ").strip()
    if not usuario:
        return
    sessao = input("Sessão (Enter usa s1): ").strip() or "s1"
    print("Comandos: /usuario troca usuário e sessão; /sessao troca sessão; /sair encerra.")
    while True:
        mensagem = input(f"\n[{usuario} | {sessao}] Mensagem: ").strip()
        if not mensagem:
            continue
        # COMANDOS LOCAIS são tratados pelo Python antes do invoke().
        # O modelo recebe apenas mensagens da conversa, sem escolher a identidade.
        comando = mensagem.lower()
        if comando == "/sair":
            return
        if comando == "/usuario":
            usuario = input("Usuário (Enter mantém o atual): ").strip() or usuario
            sessao = input("Sessão (Enter mantém a atual): ").strip() or sessao
            continue
        if comando == "/sessao":
            sessao = input("Sessão (Enter mantém a atual): ").strip() or sessao
            continue
        if mensagem.startswith("/"):
            print("Comando desconhecido. Use /usuario, /sessao ou /sair.")
            continue
        oficina.conversar(usuario, sessao, mensagem)
        oficina.store.exibir()


def main():
    parser = argparse.ArgumentParser(description="Preferências da oficina entre sessões, em memória.")
    parser.add_argument("--demo", action="store_true", help="Executa as verificações guiadas e encerra.")
    args = parser.parse_args()
    exibir_conceitos_estudados()
    # LOAD_DOTENV lê a chave compartilhada na raiz sem substituir variáveis do ambiente.
    load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=False)
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Defina OPENAI_API_KEY no ambiente ou no .env da raiz.")
    # CHATOPENAI configura o modelo que interpreta mensagens e pede chamadas de ferramentas.
    # A oficina é criada uma vez para compartilhar store e checkpointer durante o programa.
    oficina = Oficina(ChatOpenAI(model="gpt-4o-mini", temperature=0, max_retries=0, timeout=45))
    if args.demo:
        demonstrar(oficina)
        return
    # INPUT recebe escolhas e mensagens no terminal sem precisar editar o código.
    escolha = input("\nExecutar demonstração guiada antes do chat? [S/n]: ").strip().lower()
    if escolha != "n":
        demonstrar(oficina)
    conversar_no_terminal(oficina)


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        print(f"\n[erro] {type(erro).__name__}: {erro}")
        raise SystemExit(1) from erro
