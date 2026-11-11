"""Regras conservadoras sobre fontes explícitas; não aplicam alterações operacionais."""
import re

CANCELAR=re.compile(r"^Cancelar\s+(?:reunião|reuniao|visita|atendimento)\s+(.+?)\s+(?:de|em)\s+\d{1,2}/\d{1,2}/\d{4}\b",re.IGNORECASE)

def revisar_cancelamentos(propostas):
    # PÓS-PROCESSAMENTO: corrige apenas pedido imperativo explícito, citando a regra e os campos anteriores.
    for proposta in propostas:
        if proposta['area']!='agenda':
            continue
        encontrados=[(f,CANCELAR.match(f['trecho'].strip())) for f in proposta['fontes'] if '?' not in f['trecho']]
        encontrados=[(f,m) for f,m in encontrados if m]
        nomes={m[1].strip().casefold() for _,m in encontrados}
        if len(nomes)!=1:
            continue
        fonte,match=encontrados[0]
        nome=match[1].strip()
        alteracoes={}
        for campo,novo in [('natureza','cancelamento'),('projeto',nome)]:
            if proposta[campo]!=novo:
                alteracoes[campo]={'antes':proposta[campo],'depois':novo}
                proposta[campo]=novo
        if alteracoes:
            proposta.setdefault('ajustes_revisao',[]).append({
                'regra':'pedido_explicito_de_cancelamento','mensagem_id':fonte['mensagem_id'],
                'alteracoes':alteracoes})
        pendencia='Vincular ao compromisso e confirmar o cancelamento antes de aplicar.'
        if pendencia not in proposta['pendencias']:
            proposta['pendencias'].append(pendencia)

def listar_edicoes(snapshot):
    # RASTREABILIDADE: mesmo autor/instante sugere candidato, mas não prova que são versões da mesma mensagem.
    mensagens=snapshot['mensagens']
    avisos=[]
    for m in mensagens:
        if m.get('editada') and m['tipo']=='mensagem':
            candidatos=[{'mensagem_id':a['id'],'trecho':a['texto']} for a in mensagens
                        if a['id']!=m['id'] and a['tipo']=='mensagem'
                        and a.get('autor')==m.get('autor') and a['instante_utc']==m['instante_utc']
                        and a['texto']!=m['texto']]
            avisos.append({'fonte_editada':{'mensagem_id':m['id'],'trecho':m['texto']},
                           'candidatos_mesmo_autor_instante':candidatos,
                           'pendencia':'Conferir vínculo e horários; não substituir compromisso automaticamente.'})
    return avisos
