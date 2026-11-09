"""Fase 5: mesmo agente e memória, com verificação antes de persistir/exibir a resposta."""
from pathlib import Path
import sys
if __name__ == '__main__' and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = 'auto_super_parts'

from .atendimento_rag import AtendimentoRAG
from .atendimento_memoria import main as main_memoria
from .agente_fase02 import registrar_execucao
from .verificacao import VerificadorResposta, criar_juiz, criar_reparador, criar_modelo_verificacao


class AtendimentoVerificado(AtendimentoRAG):
    def __init__(self, memoria, modelo=None, cliente_cep=None, rag=None, planejador=None,
                 modelo_planejamento=None, verificador=None, modelo_verificacao=None):
        # INJEÇÃO separa fixtures de testes dos modelos configurados para a execução real.
        if verificador is None:
            modelo_verificacao = modelo_verificacao if modelo_verificacao is not None else criar_modelo_verificacao()
            verificador = VerificadorResposta(criar_juiz(modelo_verificacao), criar_reparador(modelo_verificacao),
                origem=type(modelo_verificacao).__name__ + ":" + str(getattr(modelo_verificacao, "model_name", "modelo injetado")))
        self.verificador = verificador
        super().__init__(memoria, modelo=modelo, cliente_cep=cliente_cep, rag=rag,
                         planejador=planejador, modelo_planejamento=modelo_planejamento)

    def finalizar_resposta(self, resultado):
        resultado = super().finalizar_resposta(resultado)
        if resultado['status'] != 'ok':
            resultado['verificacao_geral'] = {'status': 'nao_aplicavel'}
            return resultado
        # HOOK roda antes do registrar_turno da memória: histórico recebe somente a resposta liberada.
        if resultado.get('controle_identificacao'):
            resultado['verificacao_geral']={'status':'identificacao_pendente','metodo':'pergunta_controlada_por_dados_faltantes',
                'reparos_executados':0,'juiz_executado':False}
            return resultado
        resultado['resposta_antes_da_verificacao'] = resultado['resposta']
        resposta, auditoria = self.verificador.processar(resultado)
        if auditoria['status'] == 'corrigida' and resultado.get('fontes_documentais'):
            linhas = [l for l in resposta.splitlines() if not l.strip().strip('*').startswith('Fontes consultadas:')]
            fontes = '; '.join(f"{f['secao']} ({f['fonte']})" for f in resultado['fontes_documentais'])
            resposta = '\n'.join(linhas).strip() + '\n\nFontes consultadas: ' + fontes + '.'
        resultado.update(resposta=resposta, verificacao_geral=auditoria)
        return resultado

    def atender(self, cliente, sessao, mensagem, salvar=True):
        resultado = super().atender(cliente, sessao, mensagem, salvar=False)
        resultado['fase'] = 5
        if salvar:
            resultado['arquivo_evidencia'] = registrar_execucao(resultado, prefixo='fase05').name
        return resultado


def main():
    print('[estudo] Mesmo agente RAG e memoria; resposta verificada antes de salvar e exibir.')
    print('[estudo] Valores por Python; sustentacao, contradicao e falta de suporte por juiz LLM.')
    print('[estudo] No maximo um reparo; falha de verificacao produz limitacao segura.')
    main_memoria(fabrica_sistema=AtendimentoVerificado, descricao='Fase 5: atendimento com verificacao por evidencias.')


if __name__ == '__main__':
    main()
