"""Importação local de WhatsApp. Nenhuma chamada de LLM ou serviço externo."""
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path, PurePosixPath
import json
import re
import stat
from zipfile import ZipFile, BadZipFile
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MAX_TEXTO=2*1024*1024
MAX_ZIP=20*1024*1024
CABECALHOS=[
    ('ios',re.compile(r'^[\u200e\u200f\ufeff]*\[(\d{2}/\d{2}/\d{2,4}), (\d{2}:\d{2}(?::\d{2})?)\]\s?(.*)$')),
    ('android',re.compile(r'^[\u200e\u200f\ufeff]*(\d{2}/\d{2}/\d{2,4}),? (\d{2}:\d{2}(?::\d{2})?) - (.*)$')),
]


@dataclass(frozen=True)
class ArquivoConversa:
    nome: str
    membro_zip: str | None
    sha256_arquivo: str
    sha256_texto: str
    texto: str


@dataclass(frozen=True)
class Mensagem:
    ordem: int
    linha_inicio: int
    linha_fim: int
    data_original: str
    instante_utc: str
    autor: str | None
    texto: str
    tipo: str
    editada: bool
    midia_omitida: bool
    original: str
    chave: str
    ocorrencia: int


@dataclass
class Leitura:
    mensagens: list[Mensagem]=field(default_factory=list)
    rejeicoes: list[dict]=field(default_factory=list)
    formatos: set[str]=field(default_factory=set)
    fuso: str='America/Sao_Paulo'


# BYTES/ZIP: não extrai anexos nem caminhos. Limites valem antes e durante a leitura.
def ler_arquivo(caminho):
    caminho=Path(caminho)
    if caminho.suffix.lower() not in ('.txt','.zip'):
        raise ValueError('Use arquivo TXT ou ZIP exportado pelo WhatsApp.')
    limite=MAX_ZIP if caminho.suffix.lower()=='.zip' else MAX_TEXTO
    with caminho.open('rb') as entrada:
        arquivo=entrada.read(limite+1)
    if len(arquivo)>limite:
        raise ValueError('Arquivo excede o limite de tamanho.')
    dados=arquivo;membro=None
    if caminho.suffix.lower()=='.zip':
        import io
        try:
            with ZipFile(io.BytesIO(arquivo)) as z:
                infos=z.infolist()
                if sum(i.file_size for i in infos)>MAX_ZIP:
                    raise ValueError('Conteúdo descompactado excede 20 MiB.')
                for info in infos:
                    partes=PurePosixPath(info.filename.replace('\\','/'))
                    if partes.is_absolute() or '..' in partes.parts or ':' in info.filename:
                        raise ValueError('ZIP contém caminho inseguro.')
                textos=[i for i in infos if not i.is_dir() and i.filename.lower().endswith('.txt')]
                chats=[i for i in textos if PurePosixPath(i.filename).name.lower()=='_chat.txt']
                candidatos=chats if chats else textos
                if len(candidatos)!=1:
                    raise ValueError('ZIP precisa conter um único _chat.txt ou um único TXT identificável.')
                info=candidatos[0]
                if info.file_size>MAX_TEXTO or info.flag_bits & 1 or stat.S_ISLNK(info.external_attr>>16):
                    raise ValueError('TXT do ZIP é muito grande, criptografado ou um link.')
                membro=info.filename
                with z.open(info) as entrada:
                    dados=entrada.read(MAX_TEXTO+1)
                if len(dados)>MAX_TEXTO:
                    raise ValueError('TXT descompactado excede 2 MiB.')
        except (BadZipFile,NotImplementedError,RuntimeError) as erro:
            raise ValueError('ZIP inválido.') from erro
    try:
        texto=dados.decode('utf-8-sig')
    except UnicodeDecodeError as erro:
        raise ValueError('Esperado texto UTF-8; não foi aplicada conversão silenciosa.') from erro
    return ArquivoConversa(caminho.name,membro,sha256(arquivo).hexdigest(),sha256(dados).hexdigest(),texto)


# DATA/FUSO: o export não informa UTC; a zona é uma premissa declarada do corpus.
def instante(data,hora,zona):
    if len(data.split('/')[-1])!=4:
        raise ValueError('Ano de dois dígitos é ambíguo; informe exportação com quatro dígitos.')
    formato='%d/%m/%Y %H:%M:%S' if hora.count(':')==2 else '%d/%m/%Y %H:%M'
    local=datetime.strptime(data+' '+hora,formato)
    candidatos=[]
    for fold in (0,1):
        zonado=local.replace(tzinfo=zona,fold=fold)
        utc=zonado.astimezone(timezone.utc)
        if utc.astimezone(zona).replace(tzinfo=None)==local and utc not in candidatos:
            candidatos.append(utc)
    if len(candidatos)!=1:
        raise ValueError('Horário inexistente ou ambíguo por mudança de fuso/horário de verão.')
    return candidatos[0].isoformat()


def tipo_mensagem(autor,texto):
    limpo=texto.lstrip('\u200e\u200f').strip()
    if autor is None or (texto.startswith(('\u200e','\u200f')) and re.match(
            r'As mensagens e ligações|Você foi |.+ criou este grupo$|.+ adicionou .+|.+ removeu .+',limpo)):
        return 'sistema'
    if re.fullmatch(r'(?:Esta mensagem foi apagada|Você apagou esta mensagem)[.!]?',limpo,re.I):
        return 'removida'
    if re.fullmatch(r'(?:imagem|áudio|vídeo|documento|figurinha) (?:ocultad[oa]|omitid[oa])|<Mídia oculta>',limpo,re.I):
        return 'midia_omitida'
    return 'mensagem'


# PARSING: uma mensagem continua até o próximo cabeçalho; suas linhas originais são preservadas.
def interpretar(texto,fuso='America/Sao_Paulo'):
    try:
        zona=ZoneInfo(fuso)
    except ZoneInfoNotFoundError as erro:
        raise ValueError('Fuso IANA indisponível. Instale requirements.txt (tzdata).') from erro
    leitura=Leitura(fuso=fuso)
    linhas=texto.splitlines(keepends=True)
    blocos=[];atual=None
    for numero,linha in enumerate(linhas,1):
        cabecalho=None
        for formato,padrao in CABECALHOS:
            achou=padrao.match(linha.rstrip('\r\n'))
            if achou:
                cabecalho=(formato,achou);break
        if cabecalho:
            if atual:
                blocos.append(atual)
            atual={'inicio':numero,'fim':numero,'linhas':[linha],'cabecalho':cabecalho}
        elif atual:
            atual['linhas'].append(linha);atual['fim']=numero
        else:
            leitura.rejeicoes.append({'linha_inicio':numero,'linha_fim':numero,'motivo':'Linha sem cabeçalho inicial.','original':linha})
    if atual:
        blocos.append(atual)
    if not linhas:
        leitura.rejeicoes.append({'linha_inicio':0,'linha_fim':0,'motivo':'Arquivo vazio.','original':''})
    contagens=Counter()
    for ordem,bloco in enumerate(blocos,1):
        formato,m=bloco['cabecalho'];leitura.formatos.add(formato)
        original=''.join(bloco['linhas'])
        try:
            utc=instante(m[1],m[2],zona)
        except ValueError as erro:
            leitura.rejeicoes.append({'linha_inicio':bloco['inicio'],'linha_fim':bloco['fim'],'motivo':str(erro),'original':original})
            continue
        corpo=m[3]
        autor,separador,primeira=corpo.partition(': ')
        if not separador:
            autor=None;primeira=corpo
        texto_msg=primeira
        if len(bloco['linhas'])>1:
            texto_msg+='\n'+''.join(bloco['linhas'][1:]).replace('\r\n','\n').replace('\r','\n').rstrip('\n')
        tipo=tipo_mensagem(autor,texto_msg)
        editada='<Mensagem editada>' in texto_msg
        midia_omitida=bool(re.search(r'(?:imagem|áudio|vídeo|documento|figurinha) (?:ocultad[oa]|omitid[oa])|<Mídia oculta>',texto_msg,re.I))
        identidade=json.dumps([utc,autor,texto_msg],ensure_ascii=False,separators=(',',':'))
        chave=sha256(identidade.encode('utf-8')).hexdigest();contagens[chave]+=1
        leitura.mensagens.append(Mensagem(ordem,bloco['inicio'],bloco['fim'],m[1]+', '+m[2],utc,
            autor,texto_msg,tipo,editada,midia_omitida,original,chave,contagens[chave]))
    return leitura
