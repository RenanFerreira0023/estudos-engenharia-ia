# Base técnica manual — escopo revisado em 08/11/2026

Decisão de Renan: especializar o atendente em óleo/manutenção básica, freios, pneus, velas, correias de distribuição/acessórios e alternador, nos veículos cadastrados. A única adição é Chevrolet S10 2014 2.8 CTDI diesel. Manter os quatro recortes originais e 24 produtos comerciais; a S10 possui ficha técnica, sem produtos à venda vinculados.

O [plano ativo](../../../PLANO_ACAO_IA_PROGRAMADORA_AUTOPECAS.md) retira APIs de catálogo e scraping do atendimento. AutoTools e testes de outros sites permanecem históricos. ViaCEP continua sendo API externa real; endereço não fornece frete ou distância.

## Arquivos e consulta

- [Veículos](../02_codigo/dados/veiculos.json): identificação dos cinco recortes, sem presumir ser o veículo do cliente.
- [Conhecimento técnico](../02_codigo/dados/conhecimento_tecnico.json): assunto, campos, perguntas necessárias, situação da informação, fontes e localização no documento.
- [Fontes](../02_codigo/dados/fontes.json): origem, edição e limites. Fontes parciais antigas não passam a validar toda a ficha.
- [Consulta técnica](../02_codigo/src/auto_super_parts/consultas_complementares.py): consulta estruturada local, sem embeddings ou busca online de peças. A guarda de óleo só libera o contrato documentado consultado no turno; rejeita veículo/ano explicitamente divergente.
- [Agente](../02_codigo/src/auto_super_parts/agente_fase02.py): `@tool` expõe os assuntos ao `create_agent`; mensagens AI/Tool guardam consulta e retorno. As regras do prompt pedem o que faltar.

São 42 registros: 11 com campos verificados em manual nesta revisão, registros parciais anteriores e lacunas explícitas. Um registro verificado pode ter campos ainda pendentes. Isso não significa 11 peças homologadas ou cobertura total de manutenção.

## Cobertura atual

| Veículo | Dados acrescentados | Lacunas relevantes |
|---|---|---|
| Gol 2010 1.0 8V flex | Perguntas e pendências por assunto | Confirmar geração/identificação técnica e manual aplicável; óleo e intervalos não liberados |
| Palio 2010 1.0 Fire 8V flex | Perguntas e pendências por assunto | Manual brasileiro dessa configuração ainda não verificado; óleo e intervalos não liberados |
| Celta 2012 1.0 8V flex | Óleo, capacidades, regimes de troca, freios, pneus, velas e alternador; distinção entre correias | Código de correias, intervalos de correias/velas e aplicação comercial ainda pendentes |
| Fusca 1982 1600 a ar gasolina | Preservadas arquitetura e referências parciais de sincronismo/correia externa; perguntas nos novos assuntos | Viscosidade/litros/intervalo e aplicações de freios/pneus/peças sem manual confirmado |
| S10 2014 2.8 CTDI diesel | Óleo por norma/regime, fluido de freio e filtro de combustível | Capacidade de óleo, versões/equipamentos e demais assuntos pendentes; sem estoque/preço de peças |

As especificações novas vêm dos manuais oficiais Chevrolet [Celta 2012](https://meu.chevrolet.com.br/content/dam/gmownercenter/gmsa/gmbr/dynamic/manuals/2012/chevrolet/Celta/pt/om_ng-chevrolet_Celta_my12-pt_BR.pdf) e [S10 2014](https://meu.chevrolet.com.br/content/dam/gmownercenter/gmsa/gmbr/dynamic/manuals/2014/chevrolet/S10/pt/om_ng-chevrolet_S10_my14-pt_BR.pdf), consultados em 08/11/2026. O portal da montadora lista ambos por modelo/ano. Não houve generalização de um manual de outro mercado ou ano para completar lacunas.

Na S10, a capacidade permanece nula: o resumo do manual contém descrições ambíguas sobre motor/tração. A extração de tabelas de manutenção também perde a posição de algumas marcas; por isso não cadastramos intervalos de correia/vela sem conferência visual. Os fatos não ambíguos estão associados às seções indicadas nos registros.

## Como o atendimento deve funcionar

1. Identificar o veículo, o assunto e o tipo de peça. Não perguntar motor para uma política de pagamento.
2. Consultar a ficha local do assunto; respeitar as perguntas ainda não respondidas.
3. Óleo: separar viscosidade de norma, capacidade com/sem filtro e intervalo por uso. Km ou meses, o primeiro limite; não calcular média. Na S10, distinguir também a norma do óleo.
4. Freios: eixo/tipo e alterações; pneus: medida completa, carga e rodas; alternador/correia externa: equipamentos e referência instalada.
5. Quando faltar dado, perguntar ou explicitar a lacuna. Não inventar duração fixa de pneus/pastilhas/lonas ou oferecer vela de ignição flex para diesel.
6. Consultar produtos/preço só depois, quando solicitado. O manual do veículo não prova a especificação de um produto didático. Os atributos comerciais de óleo continuam pendentes, e `validada_para_uso_real` não foi promovido.

Isso é orientação baseada na documentação cadastrada, sem diagnóstico por sintomas, procedimento de reparo, inspeção do carro ou certificação de instalação. O verificador semântico geral continua no plano; estas guardas são específicas.

## Executar e conferir

A partir de `Projeto final`, com o ambiente instalado conforme o README:

```powershell
python -B 02_codigo/executar_testes.py
python -B 02_codigo/verificar_fase02.py
python -B 02_codigo/src/auto_super_parts/agente_fase02.py
```

Perguntas independentes para o terminal:

- `Tenho um Celta 2012 1.0 8V flex original. Qual óleo e intervalo de troca?`
- `Tenho uma S10 2014 2.8 CTDI diesel original. Qual viscosidade e intervalo de troca do óleo?`
- `Tenho Celta 2012 1.0 8V flex original com ar-condicionado. Qual amperagem de alternador consta no manual?`
- `Tenho um Fusca 1982 1600 a ar gasolina original. Qual viscosidade de óleo e quantos litros?`

Para repetir as seis chamadas com o modelo real, usando a configuração local do projeto:

```powershell
python -B 02_codigo/validar_base_manual.py --real
```

O comando real consome API. O script verifica ferramenta/assunto/veículo e trechos esperados; não é juiz semântico nem relatório LangSmith. Não existe fallback silencioso para respostas fictícias.

## Continuidade do plano

Após esta curadoria, a ordem permanece: memória curta/longa e isolamento por cliente → RAG/text-to-query → verificação → Streamlit → avaliação LangSmith e entregas. A fase 2 continua sem memória entre perguntas. Não confundir plano atualizado com implementação de todas essas fases.
