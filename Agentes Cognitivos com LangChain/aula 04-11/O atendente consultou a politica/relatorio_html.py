"""Relatório HTML autocontido dos resultados já coletados, sem novas chamadas à API."""

import argparse
from html import escape
import json
from pathlib import Path


def texto(valor):
    return escape(str(valor if valor is not None else "Pendente"), quote=True)


def nota(valor):
    if valor is None:
        return '<span class="badge pending">Pendente</span>'
    return ('<span class="badge good">Aprovada · 1</span>' if valor == 1 else
            '<span class="badge bad">Reprovada · 0</span>')


def lista(nomes):
    return (''.join('<code>' + texto(n) + '</code> ' for n in nomes)
            if nomes else '<span class="muted">Nenhuma ferramenta</span>')


def comentario(valor):
    return texto(valor or "PENDENTE").replace('\n', '<br>')


# HTML ESCAPADO: respostas e comentários são dados, nunca código executável na página.
def parecer_html(parecer):
    if not parecer:
        return '<p class="muted">Juiz não executado. Não há nota semântica disponível.</p>'
    criterios = {
        'responde_pergunta': 'Responde efetivamente à pergunta',
        'cobre_referencia': 'Cobre os fatos necessários da referência',
        'sem_contradicao_ou_invencao': 'Sem contradição ou informação inventada',
        'somente_oferece_consulta': 'É apenas uma oferta de consulta',
    }
    linhas = ''.join('<li><span>' + rotulo + '</span><strong>' +
                     ('Sim' if parecer[chave] else 'Não') + '</strong></li>'
                     for chave, rotulo in criterios.items() if chave in parecer)
    return ('<p>' + texto(parecer.get('justificativa', 'Sem justificativa registrada.')) +
            '</p><ul class="criteria">' + linhas + '</ul>')


def caso_html(caso, indice):
    eventos = []
    for evento in caso.get('trajetoria', []):
        conteudo = (evento.get('argumentos', {}) if evento.get('tipo') == 'chamada'
                    else evento.get('conteudo', ''))
        if not isinstance(conteudo, str):
            conteudo = json.dumps(conteudo, ensure_ascii=False, indent=2)
        estado = ('' if evento.get('tipo') == 'chamada' else
                  (' · retorno confirmado' if evento.get('sucesso') else ' · retorno não confirmado'))
        eventos.append('<li><div class="event-title">' + texto(evento.get('tipo')) + ' · ' +
                       texto(evento.get('nome')) + estado + '</div><small>ID: ' +
                       texto(evento.get('id')) + '</small><pre>' + texto(conteudo) + '</pre></li>')
    trajetoria = ('<ol class="timeline">' + ''.join(eventos) + '</ol>' if eventos else
                  '<p class="muted">Nenhuma chamada de ferramenta registrada neste caso.</p>')
    return f'''<details class="case" id="caso-{indice}" {'open' if indice == 1 else ''}>
<summary><span class="case-num">{indice:02d}</span><span class="case-title">{texto(caso['pergunta'])}
<small>{texto(caso['origem'])}</small></span><span class="case-notes">Consulta {nota(caso.get('nota_trajetoria'))}
Resposta {nota(caso.get('nota_resposta'))}</span><span class="chevron">⌄</span></summary>
<div class="case-body"><div class="two"><section><h3>Resposta do atendente</h3>
<blockquote>{texto(caso['resposta'])}</blockquote></section><section><h3>Resposta de referência</h3>
<p>{texto(caso['referencia'])}</p></section></div>
<h3>Consulta à ferramenta</h3><div class="tool-grid">
<div><small>Esperadas</small>{lista(caso['esperadas'])}</div>
<div><small>Chamadas observadas</small>{lista(caso['chamadas'])}</div>
<div><small>Execuções confirmadas</small>{lista(caso['executadas'])}</div></div>
<div class="two"><section><h3>Parecer do LLM juiz</h3>{parecer_html(caso.get('parecer_juiz'))}</section>
<section><h3>Revisão humana</h3><div class="human">{comentario(caso.get('comentario_humano'))}</div></section></div>
<details class="trace"><summary>Ver trajetória completa · {len(eventos)} eventos</summary>{trajetoria}</details>
</div></details>'''


# DUAS NOTAS: contagens independentes; None permanece pendente e não vira zero ou acerto.
def gerar_html(dados, nome_fonte="Execução"):
    casos = dados['casos']
    fixture = dados.get('fixture_oferta', {})
    def contagem(chave):
        aprovados = sum(c.get(chave) == 1 for c in casos)
        pendentes = sum(c.get(chave) is None for c in casos)
        return f'{aprovados}<span> / {len(casos)}</span>', f'{pendentes} pendente(s) de avaliação'
    consultas, pend_consultas = contagem('nota_trajetoria')
    respostas, pend_respostas = contagem('nota_resposta')
    revisoes = sum(bool(c.get('comentario_humano', '').strip()) and
                   not c['comentario_humano'].strip().upper().startswith('PENDENTE') for c in casos)
    origens = ', '.join(dict.fromkeys(c['origem'] for c in casos))
    linhas = ''.join(f'''<tr><td><a href="#caso-{i}">{texto(c['pergunta'])}</a></td>
<td>{lista(c['esperadas'])}</td><td>{lista(c['executadas'])}</td>
<td>{nota(c.get('nota_trajetoria'))}</td><td>{nota(c.get('nota_resposta'))}</td></tr>'''
                     for i, c in enumerate(casos, 1))
    fp = fixture.get('falso_positivo_observado')
    fp_texto = ('Não avaliado' if fp is None else
                'Sim — o juiz inicial aprovou uma resposta incompleta' if fp else
                'Não — o juiz inicial reprovou a oferta de consulta')
    return TEMPLATE.replace('__CONTEUDO__', f'''
<header class="hero"><div class="eyebrow">CADERNO DO RENAN · AULA 04-11</div>
<h1>O atendente consultou<br>a política?</h1><p>Resposta e consulta avaliadas separadamente, com as evidências de cada caso.</p>
<span class="source">{texto(origens)}</span></header>
<div class="toolbar"><span class="muted">Fonte: {texto(nome_fonte)}</span><div>
<button id="expand">Expandir detalhes</button><button id="theme" aria-pressed="false">Tema escuro</button>
<button id="print">Imprimir / PDF</button></div></div>
<section class="metrics" aria-label="Resumo da execução">
<div class="metric"><small>Consultas aprovadas</small><strong>{consultas}</strong><p>{pend_consultas}</p></div>
<div class="metric"><small>Respostas aprovadas</small><strong>{respostas}</strong><p>{pend_respostas}</p></div>
<div class="metric"><small>Casos com revisão humana</small><strong>{revisoes}<span> / {len(casos)}</span></strong><p>Comentários registrados na execução</p></div>
</section>
<section class="panel" id="politica"><div class="section-label">01 · FONTE DA RESPOSTA</div><h2>Política fictícia da loja</h2>
<p class="policy">{texto(dados.get('politica_ficticia', 'Não informada'))}</p>
<p class="muted">A regra é uma simulação do exercício. Mesmo no modo API, ela não representa uma loja real.</p></section>
<section class="panel" id="resumo"><div class="section-label">02 · RESULTADOS LADO A LADO</div><h2>Duas perguntas diferentes</h2>
<div class="two intro"><p><b>Consultou corretamente?</b><br>Python compara exatamente as ferramentas esperadas, chamadas e retornos confirmados.</p>
<p><b>Respondeu corretamente?</b><br>O LLM juiz verifica o significado da resposta e justifica sua nota.</p></div>
<div class="table-wrap"><table><thead><tr><th>Pergunta</th><th>Esperadas</th><th>Executadas</th><th>Consulta</th><th>Resposta</th></tr></thead><tbody>{linhas}</tbody></table></div>
<p class="muted">1 = aprovada · 0 = reprovada · Pendente = sem avaliação. As contagens descrevem apenas os casos desta execução.</p></section>
<section id="casos"><div class="section-label">03 · RESPOSTAS, PARECERES E REVISÕES</div><h2>Abra cada caso para conferir</h2>
{''.join(caso_html(c, i) for i, c in enumerate(casos, 1))}</section>
<section class="panel fixture" id="fixture"><div class="section-label">04 · TESTANDO O PRÓPRIO JUIZ</div>
<h2>Oferecer consulta não é responder</h2><span class="source">Fixture escrita manualmente</span>
<blockquote>{texto(fixture.get('resposta', 'Não informada'))}</blockquote>
<p>Esta resposta foi criada para testar o avaliador. <b>Não é uma falha observada do atendente.</b></p>
<div class="tool-grid"><div><small>Nota esperada</small>{nota(fixture.get('nota_esperada'))}</div>
<div><small>Juiz inicial</small>{nota(fixture.get('nota_juiz_inicial'))}</div>
<div><small>Juiz com critério estrito</small>{nota(fixture.get('nota_juiz_estrito'))}</div></div>
<p><b>Falso positivo observado:</b> {texto(fp_texto)}.</p>
<div class="two"><section><h3>Parecer inicial</h3>{parecer_html(fixture.get('parecer_inicial'))}</section>
<section><h3>Parecer estrito</h3>{parecer_html(fixture.get('parecer_estrito'))}</section></div>
<h3>Revisão humana da fixture</h3><div class="human">{comentario(fixture.get('comentario_humano'))}</div>
<details class="trace"><summary>Ler o critério estrito</summary><pre>{texto(fixture.get('criterio_revisado', 'Juiz não executado.'))}</pre></details></section>
<footer>Relatório gerado a partir do JSON salvo. Não executa modelos nem envia dados à internet.
<br>A avaliação cobre somente esta execução; não certifica o sistema inteiro nem comprova publicação no LangSmith.</footer>
''')


TEMPLATE = '''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aula 04-11 · Avaliação do atendente</title><style>
:root{--bg:#f3f6fa;--paper:#fff;--ink:#20334a;--muted:#61738a;--line:#e0e7ef;--soft:#edf4f8;--teal:#087d6d;--human:#ecf8f3;--good:#126a4b;--good-bg:#e4f5ec;--bad:#a33c49;--bad-bg:#fcebee;--pending:#815e17;--pending-bg:#fff4d9;color-scheme:light}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 system-ui,-apple-system,Segoe UI,sans-serif}
body.dark{--bg:#101a2a;--paper:#18263a;--ink:#e1eaf5;--muted:#a1b4ca;--line:#314359;--soft:#21364a;--teal:#7ce4ce;--human:#183b36;--good:#a1edc7;--good-bg:#204435;--bad:#ffb3bf;--bad-bg:#4a2832;--pending:#ffdd94;--pending-bg:#4a3a21;color-scheme:dark}
aside{position:fixed;inset:0 auto 0 0;width:238px;background:#112238;color:#c6d4e5;padding:36px 24px;display:flex;flex-direction:column}.brand{color:white;font-size:22px;font-weight:800;letter-spacing:-.6px}.brand span{color:#6ee3cb}.side-sub{font-size:12px;margin:9px 0 34px;color:#9bb0c8;letter-spacing:1px}nav a{display:block;color:#c6d4e5;text-decoration:none;padding:12px;border-radius:9px;margin:5px 0}nav a:hover{background:#223c55;color:#7cebd7}.side-foot{margin-top:auto;font-size:12px;color:#9bb0c8}
main{margin-left:238px;max-width:1500px;padding:36px clamp(20px,4vw,60px)}.hero{background:linear-gradient(120deg,#12263f,#23556a);border-radius:24px;padding:38px 42px;color:white}.eyebrow,.section-label{font-size:11px;letter-spacing:1.7px;font-weight:800;color:var(--teal)}.hero .eyebrow{color:#81ebd6}h1{font-size:clamp(30px,4vw,48px);line-height:1.12;letter-spacing:-1.3px;margin:18px 0}h2{font-size:23px;line-height:1.3;margin:10px 0 20px;letter-spacing:-.5px}h3{font-size:14px;margin:0 0 10px}.hero p{color:#d3e3ef;max-width:660px}.source{display:inline-block;border:1px solid #7cc2c750;border-radius:30px;font-size:11px;padding:5px 12px}.hero .source{background:#ffffff10;color:#c8faee}
.toolbar{display:flex;justify-content:space-between;align-items:center;gap:12px;margin:20px 0;flex-wrap:wrap}.toolbar>div{display:flex;gap:8px;flex-wrap:wrap}.toolbar>span{font-size:11px;overflow-wrap:anywhere}button{font:600 12px system-ui;padding:10px 13px;background:var(--paper);color:var(--ink);border:1px solid var(--line);border-radius:9px;cursor:pointer}button:hover{border-color:var(--teal)}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid var(--teal);outline-offset:3px}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin:24px 0}.metric,.panel,.case{background:var(--paper);border:1px solid var(--line);border-radius:17px}.metric{padding:22px}.metric small,.muted{color:var(--muted)}.metric strong{display:block;font-size:35px;line-height:1.4;letter-spacing:-1px;margin:8px 0}.metric strong span{font-size:20px;color:var(--muted);font-weight:500}.metric p{font-size:12px;color:var(--muted);margin:0}.panel{padding:28px;margin:22px 0}.panel p{margin:12px 0}.policy{background:var(--soft);border-left:3px solid var(--teal);border-radius:0 8px 8px 0;padding:17px 20px;font-weight:600}.two{display:grid;grid-template-columns:1fr 1fr;gap:26px}.intro p{font-size:13px}.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:12px}th,td{padding:15px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}th{background:var(--soft);color:var(--muted);font-size:10px;letter-spacing:.5px;text-transform:uppercase}td:first-child{min-width:170px;font-weight:600}a{color:var(--teal)}code{font-size:11px;overflow-wrap:anywhere}.badge{display:inline-block;white-space:nowrap;padding:4px 9px;border-radius:30px;font-size:11px;font-weight:700}.good{color:var(--good);background:var(--good-bg)}.bad{color:var(--bad);background:var(--bad-bg)}.pending{color:var(--pending);background:var(--pending-bg)}.panel>.muted{font-size:12px}
#casos{margin:34px 0}.case{margin:14px 0;overflow:hidden}.case>summary{display:flex;align-items:center;gap:14px;cursor:pointer;padding:21px;list-style:none}.case>summary::-webkit-details-marker{display:none}.case-num{border-radius:10px;background:var(--soft);color:var(--teal);font-size:13px;font-weight:800;padding:10px}.case-title{flex:1;font-weight:700;font-size:16px}.case-title small{display:block;font-size:11px;color:var(--muted);font-weight:400;margin-top:3px}.case-notes{display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:10px}.chevron{font-size:20px;color:var(--muted)}.case[open] .chevron{transform:rotate(180deg)}.case-body{padding:0 25px 25px;border-top:1px solid var(--line)}.case-body>.two,.case-body>h3{margin-top:24px}blockquote{margin:0;border-left:3px solid var(--teal);padding:12px 17px;background:var(--soft);border-radius:0 10px 10px 0;white-space:pre-wrap;overflow-wrap:anywhere}.two p{font-size:13px}.tool-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:14px 0 23px}.tool-grid>div{border:1px solid var(--line);border-radius:10px;padding:15px;overflow-wrap:anywhere}.tool-grid small{display:block;color:var(--muted);font-size:11px;margin-bottom:8px}.tool-grid code{display:block}.human{background:var(--human);border:1px solid var(--line);border-radius:11px;padding:17px;overflow-wrap:anywhere;font-size:13px;white-space:pre-wrap}.criteria{padding:0;list-style:none;font-size:12px}.criteria li{display:flex;justify-content:space-between;gap:15px;padding:9px 0;border-bottom:1px solid var(--line)}.trace{margin-top:23px;border-top:1px solid var(--line);padding-top:14px}.trace summary{font-size:12px;color:var(--teal);cursor:pointer;font-weight:700}.timeline{padding-left:24px}.timeline li{padding:12px 0}.event-title{font-size:12px;font-weight:700}.timeline small{color:var(--muted);overflow-wrap:anywhere}.trace pre{font:12px/1.7 Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:var(--soft);padding:14px;border-radius:10px}.fixture{border-top:4px solid #c7a54e}.fixture blockquote{margin:20px 0}.fixture .source{color:var(--muted)}footer{font-size:12px;color:var(--muted);text-align:center;padding:12px 0 30px}
@media(max-width:1100px){aside{width:190px;padding:30px 15px}main{margin-left:190px;padding:24px}.case-notes{max-width:160px}.tool-grid{gap:8px}}
@media(max-width:760px){aside{position:static;width:auto;padding:17px 20px}.side-sub{margin:4px 0 10px}nav{display:flex;gap:5px;flex-wrap:wrap}nav a{font-size:12px;padding:5px 9px;margin:0}.side-foot{display:none}main{margin:0;padding:18px}.hero{padding:28px 24px}.metrics{grid-template-columns:1fr}.metric{display:flex;align-items:center;gap:14px;flex-wrap:wrap}.metric strong{margin:0 0 0 auto}.metric p{width:100%}.two,.tool-grid{grid-template-columns:1fr}.panel{padding:21px}.case>summary{flex-wrap:wrap;padding:17px}.case-title{min-width:180px}.case-notes{max-width:none;width:100%;padding-left:52px}.chevron{display:none}.case-body{padding:0 18px 18px}}
@page{size:A4;margin:14mm}@media print{aside,.toolbar{display:none!important}body,body.dark{--bg:#fff;--paper:#fff;--ink:#20334a;--muted:#526276;--line:#d5dee7;--soft:#edf4f8;--teal:#087d6d;--human:#ecf8f3;--good:#126a4b;--good-bg:#e4f5ec;--bad:#a33c49;--bad-bg:#fcebee;--pending:#815e17;--pending-bg:#fff4d9;background:white;font-size:10pt}main{margin:0;padding:0;max-width:none}.hero{padding:8mm;background:#15334c!important;color:white;print-color-adjust:exact}.hero h1{font-size:28pt}.metrics{grid-template-columns:repeat(3,1fr)}.metric{padding:4mm}.metric strong{font-size:24pt}.panel{padding:5mm}.case>summary{padding:4mm}.case-body{padding:0 5mm 5mm}.case-notes{max-width:none}.panel,.case{break-inside:auto}.metric,blockquote,.human,tr{break-inside:avoid}h2,h3,summary{break-after:avoid}thead{display:table-header-group}.table-wrap{overflow:visible}.two{gap:5mm}.badge{print-color-adjust:exact}.trace pre{font-size:8pt}a{text-decoration:none;color:inherit}footer{font-size:8pt}}
</style></head><body><aside><div class="brand">Professor <span>IA</span></div><div class="side-sub">AVALIAÇÃO DO ATENDENTE</div>
<nav aria-label="Seções do relatório"><a href="#politica">01 · Política simulada</a><a href="#resumo">02 · Quadro de resultados</a><a href="#casos">03 · Evidências por caso</a><a href="#fixture">04 · Teste do juiz</a></nav>
<div class="side-foot">Aula 04-11<br>Agentes Cognitivos com LangChain</div></aside><main>__CONTEUDO__</main>
<script>
const theme=document.getElementById('theme');
theme.addEventListener('click',()=>{const dark=document.body.classList.toggle('dark');theme.textContent=dark?'Tema claro':'Tema escuro';theme.setAttribute('aria-pressed',String(dark));});
const expand=document.getElementById('expand');
expand.addEventListener('click',()=>{const all=[...document.querySelectorAll('details')];const open=all.some(d=>!d.open);all.forEach(d=>d.open=open);expand.textContent=open?'Recolher detalhes':'Expandir detalhes';});
document.getElementById('print').addEventListener('click',()=>window.print());
let previous=[];
window.addEventListener('beforeprint',()=>{previous=[...document.querySelectorAll('details')].map(d=>[d,d.open]);previous.forEach(([d])=>d.open=true);});
window.addEventListener('afterprint',()=>previous.forEach(([d,open])=>d.open=open));
document.querySelectorAll('a[href^="#caso-"]').forEach(a=>a.addEventListener('click',()=>{const target=document.querySelector(a.getAttribute('href'));if(target)target.open=true;}));
</script></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('json', type=Path, nargs='?', help='JSON já salvo; padrão: mais recente em resultados/.')
    args = parser.parse_args()
    arquivo = args.json
    if arquivo is None:
        arquivos = sorted((Path(__file__).parent / 'resultados').glob('execucao-*.json'))
        if not arquivos:
            parser.error('Nenhum resultado encontrado. Execute avaliar_atendente.py primeiro.')
        arquivo = arquivos[-1]
    dados = json.loads(arquivo.read_text(encoding='utf-8'))
    destino = arquivo.with_suffix('.html')
    destino.write_text(gerar_html(dados, arquivo.name), encoding='utf-8')
    print('Relatório HTML:', destino)


if __name__ == '__main__':
    main()
