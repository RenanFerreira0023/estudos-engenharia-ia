"""BrasilAPI CEP V2: endereço e coordenadas opcionais; sem chave ou fallback inventado."""
import json
import math
import re
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def requisitar_https(url, timeout):
    # HTTP: o destino é fixo e o aplicativo se identifica; a entrada só escolhe um CEP validado.
    pedido=Request(url,headers={'User-Agent':'AutoSuperPartsEstudo/1.0','Accept':'application/json'})
    with urlopen(pedido,timeout=timeout) as resposta:
        return resposta.status,resposta.read().decode('utf-8')


def coordenadas_validas(dados):
    if not isinstance(dados,dict):
        return None
    try:
        valores=[]
        for chave,limite in [('latitude',90),('longitude',180)]:
            valor=dados.get(chave)
            if isinstance(valor,bool) or valor is None:
                return None
            numero=float(valor)
            if not math.isfinite(numero) or abs(numero)>limite:
                return None
            valores.append(numero)
        return dict(zip(('latitude','longitude'),valores))
    except (TypeError,ValueError,OverflowError):
        return None


class ClienteBrasilAPI:
    usa_coordenadas=True

    def __init__(self,transporte=None,timeout=10):
        # INJEÇÃO: o teste é identificado, sem fallback silencioso para dados simulados.
        self.transporte=transporte or requisitar_https
        self.origem='brasilapi_cep_v2_real' if transporte is None else 'brasilapi_transporte_injetado_teste'
        self.timeout=timeout
        self.cache={}

    def consultar(self,cep):
        normalizado=cep.replace('-','') if isinstance(cep,str) and re.fullmatch(r'[0-9]{5}-[0-9]{3}',cep) else cep
        base={'origem':self.origem,'cep':normalizado,'endereco':None,'coordenadas':None,'tentativa_http_real':False}
        if not isinstance(normalizado,str) or not re.fullmatch(r'[0-9]{8}',normalizado):
            return {**base,'status':'cep_invalido','pendencias':['Informe CEP com oito dígitos.']}
        if normalizado in self.cache:
            # CACHE: só sucesso, por cliente de API; não reutiliza falhas nem inventa nova consulta HTTP.
            return {**self.cache[normalizado],'tentativa_http_real':False,'cache':True}
        url='https://brasilapi.com.br/api/cep/v2/'+normalizado
        base.update(url=url,tentativa_http_real=self.origem=='brasilapi_cep_v2_real',cache=False)
        try:
            codigo,corpo=self.transporte(url,self.timeout)
            base['codigo_http']=codigo
            if codigo!=200:
                return {**base,'status':'cep_nao_encontrado' if codigo==404 else 'erro_http'}
            d=json.loads(corpo)
            if (not isinstance(d,dict) or d.get('cep')!=normalizado
                    or not isinstance(d.get('city'),str) or not d['city'].strip()
                    or not isinstance(d.get('state'),str) or not re.fullmatch(r'[A-Z]{2}',d['state'])):
                return {**base,'status':'resposta_invalida'}
            endereco={'cep':normalizado[:5]+'-'+normalizado[5:],'logradouro':d.get('street'),
                      'bairro':d.get('neighborhood'),'localidade':d['city'],'uf':d['state']}
            local=d.get('location') if isinstance(d.get('location'),dict) else {}
            coords=coordenadas_validas(local.get('coordinates'))
            resultado={**base,'status':'ok','endereco':endereco,'coordenadas':coords,'servico_endereco':d.get('service'),
                'precisao':'Coordenadas aproximadas do CEP; não confirmam número do imóvel nem trajeto rodoviário.',
                'pendencias':[] if coords else ['Endereço localizado sem coordenadas válidas; distância indisponível.'],
                'limite':'BrasilAPI informa endereço e pode fornecer coordenadas; distância e frete são calculados por Python.'}
            self.cache[normalizado]=resultado
            return resultado
        except HTTPError as erro:
            return {**base,'status':'cep_nao_encontrado' if erro.code==404 else 'erro_http','codigo_http':erro.code}
        except (TimeoutError,socket.timeout):
            return {**base,'status':'timeout'}
        except (URLError,OSError):
            return {**base,'status':'indisponivel'}
        except (ValueError,UnicodeError):
            return {**base,'status':'resposta_invalida'}
