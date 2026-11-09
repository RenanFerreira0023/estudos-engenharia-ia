# Entrega para a IA programadora — Auto Super Parts CWB

Este pacote contém dados e direcionamentos, não uma aplicação pronta. Renan usará outra IA para escrever o código. Começar pela leitura deste arquivo e dos JSON. Todas as decisões novas devem ficar identificadas como propostas.

## Escopo e estado
Assistente de balcão de loja fictícia em Curitiba, com catálogo, contexto da conversa, políticas e orçamento com entrega. ViaCEP é a API externa real. Não construir pagamentos, e-commerce, WhatsApp ou diagnóstico mecânico.
Quatro configurações originais: Gol 2010 1.0 8V flex, Palio 2010 1.0 Fire 8V flex, Celta 2012 1.0 8V flex e Fusca clássico 1982 1600 gasolina. Adicionar apenas Chevrolet S10 2014 2.8 CTDI diesel como quinto recorte técnico, sem produtos comerciais novos por enquanto. São recortes acadêmicos propostos, não veículos reais inspecionados.

## Separação obrigatória das informações
Preços, marcas, SKUs, estoque, aplicações de produtos e distâncias são SIMULADOS. Não apresentar compatibilidade simulada como certificação técnica. Nenhum código fabricante real foi homologado. Informações pesquisadas estão em conhecimento_tecnico.json e fontes.json, com limites. Não inferir que uma fonte de arquitetura valida todos os produtos.
O Fusca não recebe automaticamente as mesmas seis categorias dos outros carros. Para ele, o conjunto didático usa peneira, juntas, vela, cabos, correia externa e óleo. Configuração de filtro, freio, gerador e cabeçotes precisa ser conferida antes de aplicação real. Correia dentada e de acessórios são componentes distintos.
Produtos comerciais de óleo mantêm embalagem/preço/estoque e atributos pendentes até verificar o produto específico. A base técnica separada pode ter viscosidade, norma, capacidade e intervalo do veículo já confirmados em manual. Não preencher 20W-50 ou 5W-30 por palpite. Não recomendar tecnicamente um óleo pendente; informar a limitação. Se Renan quiser aplicações reais, pesquisar fontes primárias por configuração e registrar evidência antes de marcar validada_para_uso_real=true.

## Dados e relações
veiculos.json: chave id. produtos.json: chave id. aplicacoes.json relaciona produto_id com veiculo_id. conhecimento_tecnico.json registra afirmações e fontes. loja_regras.json é a fonte das regras determinísticas. distancias_simuladas.json usa município+UF; não calcula rotas reais. casos_aceitacao.json descreve resultados esperados, NÃO resultados executados. contratos.json descreve entradas e saídas sugeridas.
Importar os dados em SQLite preservando IDs, dinheiro em centavos e metadados de simulação. Não substituir os arquivos por respostas fixas no prompt.

## Entrega e pagamento
Curitiba/PR: frete zero, prazo local pendente. Fora: distância simulada × 885 / 200 centavos, Decimal ROUND_HALF_UP; prazo ceil(distância/100) × 2 dias úteis. Não arredondar a distância para calcular o frete. Marco inicial do prazo pendente; não prometer datas de calendário. Cidade sem distância: sem cotação automática, não frete zero. ViaCEP identifica endereço, não distância ou frete. Site Pix antecipado; balcão Pix/dinheiro inclusive retirada; nunca pagamento ao entregador.

## Sequência de implementação
1. Criar estrutura mínima em .py com notebook que importe a mesma lógica. Incluir README, versões, .env.example sem segredos.
2. Primeira entrega de código: chain que extrai intenção/entidades e produz JSON validado; demonstrar PromptTemplate/ChatPromptTemplate, parser, invoke e os estilos @chain/LCEL segundo o enunciado. Não implementar todo o agente de uma vez.
3. Importar catálogo, implementar consultas e cálculo determinístico; demonstrar text-to-query quando chegar à fase pertinente.
4. Acrescentar ferramentas ViaCEP, políticas via FAISS e memória. Separar API real de dummy; dummy ajuda avaliação offline, não substitui evidência da chamada real.
5. Integrar verificação factual/lógica à resposta e avaliar qualidade e trajetória no LangSmith. Guardar evidências de cada incremento.
Não substituir requisitos literais de classes antigas por equivalentes modernos silenciosamente: conferir enunciado, versões e orientação do professor. Não instalar uma stack incompatível para satisfazer nomes sem testar.

## Documentos e evidências
Fases de construção são cinco; entregas finais são quatro: código/notebook, PDF técnico, avaliação LangSmith e vídeo. Este pacote é insumo de planejamento. Não garante cumprimento de toda a rubrica. Manter registro decisão/motivo/teste/evidência e citar IA/fontes. Não criar saídas de API, falhas de recuperação ou métricas fictícias como se tivessem sido observadas.

## Pendências que não podem ser inventadas
Prazo Curitiba; início da contagem do prazo de entrega; frete de devolução e prazo de avaliação; regras de reserva e falta de estoque; validação técnica de versões/peças/óleo. O catálogo permite exercícios acadêmicos enquanto isso, com rótulos explícitos. Política comercial não preenchida significa informar ausência, não negar direitos reais.


## Organização deste pacote
Dados: 02_codigo/dados. Políticas: 02_codigo/documentos. Casos de aceitação: 04_avaliacao_e_evidencias/casos. Código futuro: 02_codigo/src. Notebooks: 03_notebooks. Consulte README.md antes de implementar. Os nomes das pastas são convenção proposta, não exigência do professor.

## Escopo revisado — 08/11/2026

Seguir o [plano atualizado](../../PLANO_ACAO_IA_PROGRAMADORA_AUTOPECAS.md), seção 6: óleo/manutenção básica, freios, pneus, velas, correias e alternador nos seis recortes. Base técnica curada em JSON com fontes/status e perguntas para ambiguidades. Sem catálogo externo dinâmico ou scraping no fluxo; ViaCEP é a API externa. Provas antigas são históricas, não dependências a ativar.

Periodicidade é km ou meses, o primeiro limite, condicionada ao uso normal/severo e à norma do óleo. Não calcular média nem transferir regra de flex para diesel. Uma especificação do manual não homologa produto fictício. Quando a base estiver verificada, retomar a sequência original de memória, RAG, verificação, interface e avaliações; registrar limites e evidências por incremento.

## Estado após a fase 3

Memória implementada em `atendimento_memoria.py`/`memoria.py`, com confirmação explícita, SQLite e janela+recuperação de resumos por cliente. A CLI antiga da fase 2 continua independente. Ver `01_documentacao/MEMORIA_FASE_03.md` para execução e limites. Prosseguir pelo Incremento 3 do plano; não reiniciar as fases anteriores nem afirmar RAG de políticas, verificador geral ou LangSmith já implementados.

## Estado após a fase 4

RAG e text-to-query restrito implementados em `atendimento_rag.py`, `rag_politicas.py` e `planos_consulta.py`, preservando a fachada de memória. Ver `01_documentacao/RAG_FASE_04.md` e o relatório real de falhas/correções. O próximo incremento é verificação factual/lógica geral; não confundir consulta de fonte ou plano tipado com NLI, nem declarar LangSmith/Streamlit já concluídos.

## Estado após a fase 5

A nova CLI é atendimento_verificado.py. Verificacao.py classifica afirmações por juiz LLM e checa valores com Python; isso é adaptação documentada, não classificador NLI especializado. Não remover o limite de um reparo ou a reavaliação, não usar histórico como fonte de preço e não gravar a candidata reprovada na memória. Evidências incluem erros do próprio juiz e injeção controlada identificada. Consulte o guia VERIFICACAO_FASE_05.md e seus resultados antes de continuar para Streamlit, LangSmith e entregas.

## Política vigente: garantia

Renan definiu 30 dias de garantia para as peças. Fonte ativa: politicas_loja.txt e loja_regras.json. Consultar a política V3 para início da contagem, cobertura e condições de troca. Frete de devolução e prazo de avaliação não foram definidos. Fixtures com garantia desconhecida são cenários independentes, e registros anteriores refletem a política antiga.

## Política V3 — troca e condições de garantia

Renan autorizou criar regras fictícias: garantia 30 dias corridos e troca por preferência 7 dias corridos, a partir do recebimento/retirada. Consultar as condições detalhadas no documento e no JSON; não confundir prazo de troca com garantia de defeito ou aprovar operação automaticamente. Frete de devolução e prazo de análise ainda dependem do atendimento. Preservar evidências históricas de política incompleta e fixtures independentes.

## Base atual: seis recortes, incluindo Fusca TSI

Renan autorizou adicionar Fusca TSI; V006 corresponde ao recorte 2014 2.0 gasolina, com fonte SRC08. Nao cobre todos os anos nem cria produtos comerciais. V004 e V006 nao compartilham automaticamente aplicacoes. Pergunta tecnica/comercial so com Fusca pode exigir identificacao controlada antes de LLM/juiz; status identificacao_pendente nao e nota semantica. Referencia declarada na sessao nao altera perfil permanente. Ver FUSCA_TSI_08_11.md e decisoes D45-D46.

## Preferencia reforcada por Renan   respostas ao cliente

Nao repetir avisos didatico/simulado/academico nas respostas; manter origem nos registros. Pendencia tecnica deve explicar concretamente o dado que falta, sem inventar compatibilidade. D47 registra essa preferencia; sua anotacao nao significa implementacao concluida. D48 registra uma falha aberta: estoque zero deve ser separado da existencia do produto e nao implica disponibilidade imediata.

## Pendencia solicitada: exemplos comerciais por veiculo

D49: Renan pediu ANOTAR para cadastrar depois exemplos comerciais para S10 V005 e Fusca TSI V006. Planejar um exemplo por categoria pertinente a cada recorte, com preco e estoque ficticios. Nao copiar automaticamente pecas do classico nem cadastrar itens inadequados, como vela de ignicao em diesel. Separar vinculo de estudo de aplicacao mecanica homologada e sincronizar produtos/aplicacoes/agregado. Este registro nao executou o cadastro; Renan continua os testes com outras pecas.
