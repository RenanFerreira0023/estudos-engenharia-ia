# Entrega para a IA programadora — Auto Super Parts CWB

Este pacote contém dados e direcionamentos, não uma aplicação pronta. Renan usará outra IA para escrever o código. Começar pela leitura deste arquivo e dos JSON. Todas as decisões novas devem ficar identificadas como propostas.

## Escopo e estado
Assistente de balcão de loja fictícia em Curitiba, com catálogo, contexto da conversa, políticas e orçamento com entrega. ViaCEP é a API externa real. Não construir pagamentos, e-commerce, WhatsApp ou diagnóstico mecânico.
Quatro configurações propostas: Gol 2010 1.0 8V flex, Palio 2010 1.0 Fire 8V flex, Celta 2012 1.0 8V flex e Fusca clássico 1982 1600 gasolina. São recortes acadêmicos propostos, não veículos reais inspecionados.

## Separação obrigatória das informações
Preços, marcas, SKUs, estoque, aplicações de produtos e distâncias são SIMULADOS. Não apresentar compatibilidade simulada como certificação técnica. Nenhum código fabricante real foi homologado. Informações pesquisadas estão em conhecimento_tecnico.json e fontes.json, com limites. Não inferir que uma fonte de arquitetura valida todos os produtos.
O Fusca não recebe automaticamente as mesmas seis categorias dos outros carros. Para ele, o conjunto didático usa peneira, juntas, vela, cabos, correia externa e óleo. Configuração de filtro, freio, gerador e cabeçotes precisa ser conferida antes de aplicação real. Correia dentada e de acessórios são componentes distintos.
Óleos têm embalagem/preço/estoque, mas viscosidade, base e norma permanecem null até consulta ao manual correto. Não preencher 20W-50 ou 5W-30 por palpite. Não recomendar tecnicamente um óleo pendente; informar a limitação. Se Renan quiser aplicações reais, pesquisar fontes primárias por configuração e registrar evidência antes de marcar validada_para_uso_real=true.

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
Prazo Curitiba; início da contagem; troca e garantia; regras de reserva e falta de estoque; validação técnica de versões/peças/óleo. O catálogo permite exercícios acadêmicos enquanto isso, com rótulos explícitos. Política comercial não preenchida significa informar ausência, não negar direitos reais.


## Organização deste pacote
Dados: 02_codigo/dados. Políticas: 02_codigo/documentos. Casos de aceitação: 04_avaliacao_e_evidencias/casos. Código futuro: 02_codigo/src. Notebooks: 03_notebooks. Consulte README.md antes de implementar. Os nomes das pastas são convenção proposta, não exigência do professor.
