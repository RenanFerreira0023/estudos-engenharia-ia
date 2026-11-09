"""Distância Haversine entre origem cadastrada e coordenadas observadas do CEP."""
import json
import math
from decimal import Decimal,ROUND_HALF_UP
from .brasilapi import coordenadas_validas
from .configuracao import localizar_projeto
from .orcamento_fase02 import normalizar,frete_por_distancia


def distancia_linha_reta(origem,destino):
    # HAVERSINE: geodésica na esfera em quilômetros; não consulta estradas nem tempo de viagem.
    o=coordenadas_validas(origem);d=coordenadas_validas(destino)
    if o is None or d is None:
        raise ValueError('Coordenadas inválidas.')
    lat1,lon1=map(math.radians,(o['latitude'],o['longitude']))
    lat2,lon2=map(math.radians,(d['latitude'],d['longitude']))
    a=math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return float(Decimal(str(6371.0088*2*math.asin(math.sqrt(min(1,max(0,a)))))).quantize(Decimal('0.001'),rounding=ROUND_HALF_UP))


def consultar_entrega_geografica(destino,municipio,uf):
    regras=json.loads((localizar_projeto()/'02_codigo/dados/loja_regras.json').read_text(encoding='utf-8'))
    base={'frete_centavos':None,'prazo_dias_uteis':None,'distancia_km':None,'metodo_distancia':'haversine_linha_reta',
          'pendencias':[],'fontes_regras':['loja_regras.json','BrasilAPI CEP V2'],
          'limite':'Distância aproximada em linha reta até o ponto do CEP; não representa percurso rodoviário.'}
    if not isinstance(destino,dict) or destino.get('status')!='ok':
        return {**base,'status':'destino_pendente','pendencias':['Consulte primeiro o CEP informado pelo cliente.']}
    endereco=destino.get('endereco') or {}
    if normalizar(endereco.get('localidade',''))!=normalizar(municipio or '') or normalizar(endereco.get('uf',''))!=normalizar(uf or ''):
        return {**base,'status':'destino_divergente','pendencias':['Município/UF divergem do CEP consultado; não calcule para outro destino.']}
    base.update(cep_destino=destino['cep'],coordenadas_destino=destino.get('coordenadas'),origem_cep=destino['origem'])
    origem=regras['loja'].get('coordenadas')
    coords=destino.get('coordenadas')
    if coordenadas_validas(origem) and coordenadas_validas(coords):
        base['distancia_km']=distancia_linha_reta(origem,coords)
        base['coordenadas_origem']=origem
    local=(normalizar(municipio)==normalizar(regras['loja']['municipio']) and normalizar(uf)==normalizar(regras['loja']['uf']))
    if local:
        frete,prazo=regras['frete']['curitiba_pr_centavos'],regras['prazo']['curitiba_dias_uteis']
        base['regra_aplicada']='gratuidade_municipio_curitiba_pr'
        base['pendencias'].append('Prazo local ainda não definido.')
    elif base['distancia_km'] is None:
        return {**base,'status':'coordenadas_pendentes','pendencias':['Coordenadas da origem ou do CEP ausentes/inválidas; não calcular distância nem frete.']}
    else:
        frete,prazo=frete_por_distancia(base['distancia_km'],regras)
        base['regra_aplicada']='externo_proporcional_distancia_linha_reta'
    if regras['prazo']['inicio_contagem'] is None:
        base['pendencias'].append('Marco inicial da contagem do prazo pendente; não prometer data de calendário.')
    return {**base,'status':'parcial' if base['pendencias'] else 'ok','frete_centavos':frete,'prazo_dias_uteis':prazo}
