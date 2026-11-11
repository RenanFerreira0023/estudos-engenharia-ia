"""Callback local de eventos sem argumentos, respostas ou retornos sensíveis."""
from datetime import datetime, timezone
import json
from threading import Lock

from langchain_core.callbacks import BaseCallbackHandler


class RastroAgente(BaseCallbackHandler):
    def __init__(self):
        self.eventos = []
        self._lock = Lock()

    def _registrar(self, evento, run_id, nome=None):
        item = {'evento': evento, 'run_id': str(run_id),
                'instante_utc': datetime.now(timezone.utc).isoformat()}
        if nome:
            item['nome'] = nome
        with self._lock:
            self.eventos.append(item)

    # CALLBACK: registra início/fim de modelo e ferramenta para observar a trajetória.
    # Só metadados entram no log; entradas e saídas ficam fora deste rastro.
    def on_chat_model_start(self, serialized, messages, *, run_id, **kwargs):
        self._registrar('modelo_iniciado', run_id)

    def on_llm_end(self, response, *, run_id, **kwargs):
        self._registrar('modelo_concluido', run_id)

    def on_llm_error(self, error, *, run_id, **kwargs):
        self._registrar('modelo_falhou', run_id)

    def on_tool_start(self, serialized, input_str, *, run_id, **kwargs):
        self._registrar('ferramenta_iniciada', run_id, (serialized or {}).get('name'))

    def on_tool_end(self, output, *, run_id, **kwargs):
        self._registrar('ferramenta_concluida', run_id)

    def on_tool_error(self, error, *, run_id, **kwargs):
        self._registrar('ferramenta_falhou', run_id)

    def salvar(self, caminho, *, sessao_id, usuario_id, rota):
        """Um registro por atendimento, sem texto da conversa nem dados das ferramentas."""
        with open(caminho, 'a', encoding='utf-8') as arquivo:
            arquivo.write(json.dumps({'sessao_id': sessao_id, 'usuario_id': usuario_id,
                                      'rota': rota, 'eventos': self.eventos}, ensure_ascii=False) + '\n')
