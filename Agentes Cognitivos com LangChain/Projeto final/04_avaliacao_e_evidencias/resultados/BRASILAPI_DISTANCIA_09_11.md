# BrasilAPI e distância em linha reta

## Decisão D55

Solicitação de Renan: substituir ViaCEP por serviço sem conta/chave que permita calcular raio. A implementação ativa usa BrasilAPI CEP V2; o módulo ViaCEP, seus dados e testes são preservados como legado. Não há fallback silencioso da BrasilAPI para a tabela de cidades. Funções antigas permanecem disponíveis para fixtures históricas explicitamente injetadas.

A localização fictícia da loja continua no Museu Oscar Niemeyer. Endereço e CEP conferidos no site do museu/prefeitura: Rua Marechal Hermes 999, Curitiba PR, 80530-230. Coordenadas fixas -25.4102283, -49.2661342 extraídas do cadastro do Ibram em https://cadastro.museus.gov.br/museus/museu-oscar-niemeyer-mon/ (data-latitude/data-longitude do HTML). Sem vínculo comercial com o museu.

BrasilAPI: https://brasilapi.com.br/docs#tag/CEP-V2 e código oficial em https://github.com/BrasilAPI/BrasilAPI/blob/main/pages/api/cep/v2/%5Bcep%5D.js. Sem crawling; consultas pontuais acionadas pelo usuário e cache de sucessos. HTTP se identifica como AutoSuperPartsEstudo/1.0. Endereço pode vir sem coordenadas e localização do CEP pode ser centro aproximado da região/município, não porta do imóvel.

## Fluxo

CEP declarado pelo cliente -> consultar_cep -> endereço e coordenadas opcionais -> consultar_entrega/calcular_orcamento -> Haversine em Python -> preço em centavos. Coordenadas não são argumentos que a LLM possa inventar. Distância arredondada para 0.001 km, taxa proporcional 885 centavos/200 km, arredondamento financeiro HALF_UP. Prazo externo mantém dois dias úteis por faixa de 100 km para esta regra de estudo; início da contagem pendente. Não apresentar como tempo rodoviário nem promessa de data.

Curitiba/PR continua com frete grátis por município, inclusive se faltar coordenada. Não foi criado um limite gratuito em quilômetros: raio e município são conceitos distintos. Demais cidades precisam de coordenadas válidas. Falta de CEP, erro HTTP, coordenadas ausentes e destino divergente mantêm o frete externo e total pendentes; subtotal dos itens pode ser conhecido. Dados observados são isolados por turno via ContextVar com mapa de retornos; o agente reconsulta CEP anterior quando necessário. CEP inventado e não declarado nas mensagens do cliente é recusado antes do HTTP.

## Política e evidências

politicas_loja.txt passa para V4 e o índice FAISS precisa ser refeito com embeddings reais antes de iniciar atendimento RAG. Histórico antigo não é apagado. A tabela distancias_simuladas.json não é usada pelo fluxo ativo BrasilAPI. Testes antigos com cliente ViaCEP explicitamente injetado preservam as expectativas da versão anterior.

Doze testes novos cobrem endereço/coordenadas, cache, validação do CEP sem HTTP, dados não finitos, coordenadas ausentes, falhas HTTP/timeout/JSON, Haversine, São Paulo fora da tabela, Curitiba grátis, destino divergente, orçamento com dois itens e isolamento de turnos/CEP inventado. O teste de múltiplos produtos foi atualizado com transporte BrasilAPI injetado e CEP explícito. Validação final: 175 testes locais passaram; sintaxe conferida; política V4 reindexada com text-embedding-3-small (4 documentos, 1536 dimensões).

API real: fase05_brasilapi_20261109T032359813549Z.json preserva o frete isolado aprovado/corrigido e a tentativa de orçamento que executou o cálculo antes da consulta CEP. Isso motivou resolução do CEP por Python dentro da entrega quando há um único CEP declarado. Não é fallback de dados: consulta a mesma BrasilAPI e registra consulta_cep com URL/origem/status. Havendo vários CEPs ou nenhum, pede confirmação; CEP não é inventado.

Após o ajuste, fase05_brasilapi_orcamento_final_20261109T032744735544Z.json registra a execução real final aprovada. Consulta de dois produtos do Celta retornou P013/P017; subtotal 5480 centavos, distância 337.238 km em linha reta, frete 1492 centavos e total 6972 centavos. Prazo estimado da regra: 8 dias úteis, sem data de calendário. Revisão manual confirmou valores, produtos, município/UF e indicação de linha reta na resposta. Esse resultado é uma amostra funcional, não comprova precisão dos pontos do CEP nem acerto universal do juiz.

As primeiras requisições sem identificação HTTP retornaram erro; User-Agent/Accept explícitos resultaram em respostas reais válidas. Testes de ausência de coordenadas e indisponibilidade são fixtures locais identificadas, sem alegação de terem ocorrido nas consultas reais bem-sucedidas.
