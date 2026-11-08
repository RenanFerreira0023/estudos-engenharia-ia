"""Prova de cobertura dos quatro veículos locais. Não altera aplicações ou especificações."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from auto_super_parts.autotools import ClienteAutoTools


def normalizar(valor):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(valor).casefold())
                   if not unicodedata.combining(c)).replace(' ', '')


# IDENTIDADE: o nome do modelo sozinho não comprova ano, motor, combustível ou mercado.
def conferir_identidade(local, candidato):
    campos = {'marca': candidato.get('make'), 'modelo': candidato.get('model'),
              'ano_modelo': candidato.get('year'), 'motor': candidato.get('engine'),
              'combustivel': candidato.get('fuel_type', candidato.get('fuel'))}
    pendencias = [nome for nome, valor in campos.items()
                  if valor is None or normalizar(valor) != normalizar(local[nome])]
    mercado = candidato.get('market')
    if normalizar(mercado) not in ('br', 'brazil', 'brasil'):
        pendencias.append('mercado_brasileiro_nao_confirmado')
    return {'confirmada': not pendencias, 'campos_externos': campos, 'mercado': mercado,
            'pendencias': pendencias}


def extrair_id(candidato):
    valor = candidato.get('id')
    if not isinstance(valor, bool) and re.fullmatch(r'[0-9]+', str(valor)):
        return str(valor)
    # O retorno real usa api_url. Só aceitamos ID no endpoint do host oficial.
    url = urlsplit(str(candidato.get('api_url', '')))
    if url.scheme == 'https' and url.netloc == 'autotools.brightcoding.dev' and not url.query and not url.fragment:
        match = re.fullmatch(r'/api/vehicles/([0-9]+)', url.path)
        if match:
            return match.group(1)
    return None


def investigar(veiculo, cliente):
    restrita = cliente.buscar(veiculo)
    registro = {'veiculo_local': veiculo, 'busca_restrita': restrita,
                'correspondencias': [], 'secoes': [], 'cobertura': 'inconclusiva'}
    if restrita['status'] not in ('sem_resultados', 'candidatos_retornados'):
        return registro
    candidatos = restrita['json']['data']
    if not candidatos:
        ampla = cliente.buscar(veiculo, ampla=True)
        registro['busca_ampla'] = ampla
        if ampla['status'] not in ('sem_resultados', 'candidatos_retornados'):
            return registro
        candidatos = ampla['json']['data']
        if not candidatos:
            if veiculo['modelo'] == 'Fusca':
                # Busca exploratória pelo nome internacional; não afirma que um modelo estrangeiro seja equivalente.
                alias = cliente.buscar({'modelo': 'Beetle'}, ampla=True)
                registro['busca_nome_alternativo'] = alias
                if alias['status'] not in ('sem_resultados', 'candidatos_retornados'):
                    return registro
                candidatos = alias['json']['data']
            if candidatos:
                registro['limite_nome_alternativo'] = 'Equivalência do nome/configuração exige conferência; não é automática.'
            else:
                registro['cobertura'] = 'nenhum_candidato_nas_buscas_executadas'
                return registro

    for candidato in candidatos:
        identidade = conferir_identidade(veiculo, candidato)
        item = {'candidato': candidato, 'identidade': identidade}
        # Detalha somente candidato da mesma marca/modelo/ano, sem trocar nossos carros por outro mercado.
        if all(normalizar(candidato.get(k)) == normalizar(veiculo[v]) for k, v in
               [('make', 'marca'), ('model', 'modelo'), ('year', 'ano_modelo')]):
            identificador = extrair_id(candidato)
            if identificador is not None:
                detalhe = cliente.detalhe(identificador)
                item['detalhe'] = detalhe
                if detalhe['status'] == 'ok':
                    dados = detalhe['json']['data']
                    # Não adivinhar um engine_code ou fonte de outro mercado como o motor local.
                    externo = {**candidato, **dados.get('vehicle', {})}
                    identidade = conferir_identidade(veiculo, externo)
                    item['identidade'] = identidade
                if identidade['confirmada']:
                    registro['secoes'].append({'id_externo': identificador,
                                               'parts': cliente.secao(identificador, 'parts'),
                                               'oil': cliente.secao(identificador, 'oil')})
            else:
                item['limite'] = 'Resultado sem ID externo; não foram inventados IDs para consultar seções.'
        registro['correspondencias'].append(item)
    registro['cobertura'] = ('identidade_confirmada' if any(c['identidade']['confirmada'] for c in registro['correspondencias'])
                             else 'candidatos_sem_configuracao_exata_confirmada')
    return registro


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogo', type=Path, required=True, help='veiculos.json do projeto')
    parser.add_argument('--saida', type=Path, default=Path(__file__).parent / 'evidencias')
    args = parser.parse_args()
    veiculos = json.loads(args.catalogo.read_text(encoding='utf-8-sig'))
    args.saida.mkdir(parents=True, exist_ok=True)
    nome = 'autotools_real_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json'
    destino = args.saida / nome
    resultado = {'origem': 'HTTP real AutoTools', 'documentacao': 'https://autotools.brightcoding.dev/docs',
                 'termos': 'https://autotools.brightcoding.dev/terms', 'casos': []}
    cliente = ClienteAutoTools()
    for veiculo in veiculos:
        registro = investigar(veiculo, cliente)
        resultado['casos'].append(registro)
        destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
        print(veiculo['modelo'], registro['cobertura'], registro['busca_restrita']['status'],
              registro.get('busca_ampla', {}).get('status', ''), flush=True)
    print('Evidencia:', destino)


if __name__ == '__main__':
    main()
