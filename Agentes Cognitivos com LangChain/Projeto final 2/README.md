# Secretária IA — Projeto final 2

Secretária com IA para uma equipe de trabalho: lê o backup de uma conversa de WhatsApp, propõe registros (projetos, valores, visitas, clientes) com a mensagem de origem e **só grava depois de confirmação humana explícita**. Projeto final da disciplina de agentes com LangChain, organizado em cinco fases.

## Comece por aqui

| O quê | Onde |
| --- | --- |
| Notebooks de entrega, um por fase (rodam sem chave de API) | [notebooks/](notebooks/), seção [Notebooks para o professor](#notebooks-para-o-professor) |
| Requisitos da rubrica com evidências | [docs/matriz_requisitos.md](docs/matriz_requisitos.md) |
| Avaliação real com LangSmith e análise | [docs/avaliacao_resultados.md](docs/avaliacao_resultados.md) |
| Falhas reais encontradas e como foram corrigidas | [docs/execucoes_e_falhas.md](docs/execucoes_e_falhas.md) |
| Decisões de projeto | [docs/decisoes.md](docs/decisoes.md) |

## Como executar

Nesta pasta, com o ambiente virtual ativo e `OPENAI_API_KEY` no `.env` (deste projeto ou da raiz do repositório):

```powershell
python -m pip install -r requirements-ia.txt
python -m streamlit run app.py          # interface: Conversa, Fontes, Revisão, Agenda, Financeiro
python executar.py                      # menu de terminal
python -m unittest discover -s tests -q # 141 testes locais, sem API
python avaliar.py --modo fixture        # avaliação com fixtures identificadas, sem API
python avaliar.py --modo api --langsmith  # avaliação real; exige LANGSMITH_API_KEY; só dados fictícios
```

No Streamlit, o agente **só propõe**: confirmar visita ou cadastro PJ é feito pelos botões da aba Agenda; comandos com barra são do terminal e, no chat web, não são enviados ao modelo. A escolha de usuário (ana, bruno, carla) é demonstração de permissões, não autenticação. O relatório financeiro em tela substitui a exportação Excel neste projeto.

## Estado na entrega

Agente único (`create_agent`) com 11 ferramentas: SQLite (clientes, projetos, agenda, financeiro, mensagens), RAG com FAISS e fonte citada, consulta estruturada com SQL parametrizado, ViaCEP e Minha Receita. Memória por usuário e sessão (janela, recortes antigos com FAISS, preferências confirmadas). Verificação das respostas antes de exibir. Interface Streamlit. Avaliação real em 4 execuções: respostas 16/16, trajetória exata 12/16. Pendentes da entrega: relatório PDF e vídeo.

As seções abaixo registram cada marco do desenvolvimento como estava quando foi construído; números de testes e pendências citados nelas são históricos.

### Financeiro no console e no Streamlit

O menu **12 Financeiro** registra orçamento proposto/aceito, parcelas previstas e pagamento informado/confirmado. A opção financeira 1 exibe o [relatório simples no terminal](docs/financeiro_console.md); a ferramenta `consultar_financeiro_projeto` permite ao agente ler saldo somente para perfis autorizados. O relatório também aparece na interface; exportação Excel está fora do escopo atual.
O [notebook 13](notebooks/incrementos/13_financeiro_confirmado.ipynb) executa o ciclo em banco temporário com dados fictícios e mostra como o saldo muda somente após confirmar o pagamento.

### Consulta estruturada de mensagens — fase 4

O [notebook 11](notebooks/incrementos/11_text_to_query_mensagens.ipynb) demonstra pergunta, plano tipado de fixture, SQL parametrizado e resultado. No menu 9, o agente pode usar `consultar_mensagens_estruturado` para contagens e listas filtradas. [Limites e teste](docs/consulta_estruturada_fase4.md).

O [notebook 12](notebooks/incrementos/12_diagnostico_ranking_rag.ipynb) reproduz o diagnóstico de uma falha real de ranking com a evidência salva: a mensagem que apenas pergunta pelo saldo do Gama ficou acima da mensagem que explica por que ele não é calculável. O reteste colocou a explicação em primeiro lugar, preservando os escores originais.

### Índice de fontes — início da fase 4

O [notebook 10](notebooks/incrementos/10_indice_fontes_faiss.ipynb) prepara um índice FAISS com mensagens fictícias e vetores de fixture. A busca posterior carrega esse índice, verifica versão do corpus e autorização, e retorna o trecho original com ID de fonte. O menu 11 prepara o índice do corpus escolhido com confirmação antes da API; no menu 9, `buscar_mensagens_fonte` usa somente o índice existente. Renan observou a preparação real de 40 mensagens. Na [primeira tentativa](evidencias/fase4_falha_busca_fonte_manual.json), o agente deixou de buscar a fonte; no reteste chamou a ferramenta, recebeu M0004 em primeiro lugar e citou corretamente o orçamento de Alfa. [Decisões e limites](docs/indice_fontes_fase4.md).

### Recuperação vetorial da memória — fase 3

Após seis turnos, quando a pergunta depende do contexto antigo, o menu 9 filtra recortes no SQLite por empresa, usuário e sessão; só então cria um índice FAISS temporário e usa embeddings OpenAI para escolher até dois. O [notebook 09](notebooks/incrementos/09_recuperacao_vetorial_memoria.ipynb) executa o mesmo método com vetores de fixture, sem API. [Reteste real](evidencias/fase3_faiss_reteste_manual.json) recuperou Alfa; o filtro posterior para evitar recuperação numa saudação ainda precisa de reteste real. Se a API falhar, o terminal sinaliza fallback para a busca lexical. O FAISS das mensagens importadas com fontes continua reservado à fase 4.

### Preferências confirmadas — fase 3

No menu 9, `/lembrar estilo=detalhado` grava uma preferência pessoal explícita; `/memorias` mostra o valor atual e `/esquecer-memoria estilo` o remove. O valor persiste após `/nova` e reinício, mas não passa a outro usuário. O [notebook 08](notebooks/incrementos/08_preferencias_confirmadas.ipynb) demonstra isso sem API; o [guia](docs/memoria_fase3.md) compara LangMem e Mem0. A fase 3 ainda depende do reteste real dos embeddings após a janela.

### Recortes antigos — complemento da fase 3

Quando a conversa passa de seis turnos, o SQLite v8 guarda um recorte extrativo da fala do usuário que saiu da janela. Perguntas relacionadas recuperam até dois recortes da mesma sessão; o agente recebe esses textos como contexto **não confirmado**. O [notebook 07](notebooks/incrementos/07_resumos_recuperacao.ipynb) e o [guia de memória](docs/memoria_fase3.md) explicam o fluxo e seus limites. Um [teste real](evidencias/fase3_falha_lexical_cleinte.json) mostrou que `cleinte` impedia recuperar `cliente`; após a correção, o agente retomou a sessão, recuperou o turno 9 e respondeu `Alfa`. Essa busca usa palavras, não FAISS nem embeddings.

### Orquestração observável — complemento da fase 2

O [notebook 05b](notebooks/incrementos/05b_orquestracao_agente.ipynb) mostra o prompt PTCF, exemplos few-shot, roteamento `visita`/`cliente`/`geral` e callback sem API. O [guia de orquestração](docs/fase2_orquestracao.md) compara a chain fixa, `create_agent` e um grafo LangGraph explícito, e explica as adaptações às classes antigas da rubrica. No menu 9, cada resposta agora exibe rota sugerida e quantidade de eventos; os metadados do callback são guardados em `dados/privados/rastros_agente.jsonl`, sem copiar pergunta, argumentos ou resposta. [Um turno real com cliente Alfa](evidencias/fase2_roteamento_callback_manual.json) confirmou rota, ferramenta e seis eventos; FAISS e avaliação permanecem pendentes.

### Memória conversacional — início da fase 3

No menu **9**, o agente retoma a última conversa ativa do mesmo usuário após fechar e reabrir o programa. Cada pergunta e resposta concluída é gravada como um turno; as seis interações mais recentes são enviadas ao próximo `invoke`. `/voltar` mantém a conversa e `/nova` começa uma conversa vazia. A sessão antiga permanece no banco para auditoria, mas não entra no contexto da nova. Ana, Bruno e Carla têm históricos separados. O [notebook 06](notebooks/incrementos/06_memoria_conversacional.ipynb) demonstra persistência, janela e isolamento com respostas locais escritas para teste, sem atribuí-las a um LLM.

**Teste com API da etapa inicial:** Renan confirmou que, após `/nova`, o agente pediu o cliente sem reutilizar o histórico anterior. Informou Alfa, encerrou o programa, reabriu com o mesmo usuário e banco, viu o mesmo ID de sessão e recebeu `Alfa Serviços` ao perguntar qual cliente mencionara. O registro está em [execuções e falhas](docs/execucoes_e_falhas.md). Para reproduzir, diga `Estou falando do cliente Alfa.`, saia com `/voltar`, encerre com `0`, reabra com o mesmo `--usuario` e `--banco`, entre no menu 9 e pergunte `Qual cliente mencionei?`. As etapas posteriores acrescentaram recortes e recuperação vetorial; a interface atual usa o mesmo SQLite e o mesmo serviço de memória.

### Projetos e fontes da conversa — opção 10

Após importar os dados fictícios (**1**), gerar propostas (**4**) e aceitar interpretações na fila (**6**), use **10 Aplicar interpretação ao projeto**. Para uma interpretação da área `projeto`, o sistema mostra prévia e fontes e pede confirmação separada para criar o projeto. O ID de cliente é opcional; sem ele, o vínculo com cliente fica pendente, sem inferir pelo texto. Para uma interpretação financeira ou de agenda, informe explicitamente o ID de um projeto existente com o mesmo nome; o sistema grava uma **anotação com fontes**, não um pagamento ou agendamento. Repetir a confirmação devolve o mesmo registro.

O [notebook 05](notebooks/incrementos/05_projetos_fontes.ipynb) demonstra o fluxo com dados fictícios e fixture local, inclusive persistência após reabrir o SQLite. As fontes são FKs para as mensagens importadas e só podem ser lidas por usuário autorizado ao corpus. Ainda falta testar a opção 10 manualmente e implementar os registros financeiros operacionais.

### Cadastro PJ pelo agente

Na opção **9**, peça: `Cadastre o CNPJ 33683111000280 se ainda não estiver no banco.` A ferramenta consulta o banco antes da API. Para CNPJ novo, a consulta externa salva um registro de revisão e o agente pode criar uma proposta pendente; **não cria cliente**. Confira razão social, CNPJ e nome fantasia mostrados. Para gravar, digite `/confirmar-cliente ID` usando o ID da proposta. Repetir o comando devolve o mesmo cliente; uma proposta de outro usuário ou expirada é recusada. `/confirmar ID` continua reservado para visitas.

O [notebook 04](notebooks/incrementos/04_cadastro_pj_agente.ipynb) demonstra consulta, proposta, confirmação, persistência e auditoria com fixture local identificada; não afirma chamada real à API ou ao LLM. O menu 7 continua disponível para cadastro guiado. A [trajetória real do agente](evidencias/fase2_cadastro_pj_reteste_manual.json) foi observada manualmente; o retorno da ferramenta reportou chamada à API externa.

## Fluxo de visitas — fase 2 em andamento

Migração v4: novos cadastros PJ do menu 7 guardam nome fantasia, origem (`minha_receita_real` ou manual) e instante de consulta. Registros feitos antes dessa migração recebem `origem_nao_registrada`; o sistema não deduz retroativamente que a API foi usada. A consulta externa foi observada no agente e documentada em [evidências](evidencias/fase2_cnpj_novo_agente_manual.json); ela não grava o cliente automaticamente.

O menu **7** testa cadastro/localização de cliente, disponibilidade, proposta de visita e confirmação explícita. O menu **8** mostra a agenda do usuário de demonstração. O menu **9** usa `create_agent` e ferramentas `buscar_cliente`, `consultar_disponibilidade`, `consultar_cep_viacep`, `consultar_cnpj_minha_receita` e `propor_visita`; lê `OPENAI_API_KEY` do ambiente, do `.env` deste projeto ou do `.env` na raiz do repositório (nessa ordem). `--arquivo-env` seleciona um arquivo explícito. No chat, `/confirmar ID` grava a proposta do usuário atual; `/voltar` retorna ao menu. As ferramentas do agente não têm confirmação implícita.

Para testar sem API, execute `python executar.py`, selecione **7**, informe um cliente fictício e uma data futura no formato `AAAA-MM-DD HH:MM` (horário de São Paulo), duração e endereço. A proposta aparece antes da pergunta de confirmação. Depois, veja a opção **8**. Um segundo compromisso sobreposto para o mesmo atendente é recusado; um horário adjacente ou outro atendente pode ser proposto. Reinicie com `python executar.py --usuario bruno` para ver a agenda de Bruno na opção 8. A agenda não precisa abrir o corpus de mensagens privado de Ana. O menu 7 permite CEP vazio para endereço informado manualmente; se houver CEP, tenta ViaCEP real e identifica falha. Não use dados reais da equipe nesse teste.

**Evidência local:** testes cobrem confirmação idempotente, conflito surgido após a proposta, intervalos adjacentes, agendas separadas e autorização por usuário. Os testes de CEP/CNPJ usam fixtures marcadas como locais. Ainda faltam execução real do agente/API, cadastro PJ completo, vínculo com projetos/fontes importadas, memória persistente, relatórios e demais etapas do plano. A migração v3 adiciona clientes e agenda; não transforma aceite na fila de interpretações em agendamento.

Protótipo acadêmico para organizar conversas. Autopeças foi descontinuado e preservado como histórico.
[Plano](./PLANO_PROJETO_SECRETARIA_IA.md) · [Decisões](./docs/decisoes.md) · [Execuções/falhas](./docs/execucoes_e_falhas.md) · [Matriz](./docs/matriz_requisitos.md).

## Novidade: fila de revisão persistente (início da fase 2)

Gere uma análise na opção 4 ou 5 e entre na **opção 6** para aceitar, corrigir ou rejeitar interpretações.
A decisão e seu comentário permanecem no SQLite ao reabrir o programa; fontes e histórico são preservados.
Aceitar aqui ainda não cria pagamentos ou compromissos.
[Roteiro e limites](docs/revisao_persistente.md) · [Notebook 03](notebooks/incrementos/03_revisao_persistente.ipynb).
Validação atual: 72 testes locais; seis células do notebook executadas, sem nova chamada de API.
O banco existente migra automaticamente de v1 para v2, preservando fontes.

## Marco 1 implementado

TXT/ZIP -> parser local -> fontes e mensagens no SQLite -> consulta e reimportação.
São 40 mensagens fictícias, gabarito, terminal interativo e [notebook executado](./notebooks/incrementos/01_importacao_sqlite.ipynb).
Marco 1 isolado continua sem API; o marco 2 abaixo acrescenta uma chain opcional. Ainda não há agente com ferramentas.

## Como testar

Na raiz deste projeto, com Python 3.12 (testado: 3.12.6), execute:

    python -m pip install -r requirements.txt
    python executar.py

Escolha 1: esperado 40 mensagens novas, zero rejeições e um aviso de possível edição.
Escolha 1 novamente: zero novas, 40 mensagens preservadas. Escolha 3 para listar e 0 para sair.

Modo não interativo:

    python executar.py --arquivo "dados/ficticios/conversa_empresa.txt" --listar
    python -m unittest discover -s tests -p test_importacao.py -v

O banco padrão dados/privados/secretaria.sqlite3 é criado automaticamente e persiste entre execuções.
Sem servidor ou conta. O caminho padrão parte da pasta do projeto; argumentos relativos de arquivo/banco usam a pasta atual.
Para arquivo próprio, --corpus é obrigatório; no menu será solicitado um nome separado da demonstração:

    python executar.py --arquivo "caminho/exportacao.zip" --corpus "Equipe local"

Ana é a administradora fictícia padrão. --usuario bruno ou --usuario carla selecionam identidades de demonstração,
sem autenticação real. Use outro --corpus ao trocar usuário: o corpus bruto é privado do importador, com acesso
do administrador. Permissões completas sobre financeiro, RAG e relatórios ainda não estão implementadas.

## Notebooks para o professor

    python -m pip install -r requirements-notebook.txt

A entrega usa **cinco notebooks, um por fase**, na pasta `notebooks/`. Cada um começa com o problema da fase, as decisões, os links para as evidências reais e o aviso do que é fixture. Todos rodam sem chave de API, com bancos temporários e dados fictícios:

| Fase | Notebook |
| --- | --- |
| 1 · Chain e extração estruturada | [fase1_chain_extracao.ipynb](notebooks/fase1_chain_extracao.ipynb) |
| 2 · Agente com ferramentas e gravação confiável | [fase2_agente_ferramentas.ipynb](notebooks/fase2_agente_ferramentas.ipynb) |
| 3 · Memória | [fase3_memoria.ipynb](notebooks/fase3_memoria.ipynb) |
| 4 · RAG com fontes e consulta estruturada | [fase4_rag_consulta.ipynb](notebooks/fase4_rag_consulta.ipynb) |
| 5 · Financeiro, verificação e avaliação | [fase5_financeiro_verificacao_avaliacao.ipynb](notebooks/fase5_financeiro_verificacao_avaliacao.ipynb) |

A pasta `notebooks/incrementos/` guarda os 15 notebooks criados ao longo do desenvolvimento, um por incremento. Eles são o histórico de onde vieram as células dos notebooks de fase e continuam executáveis.

Abra um notebook de fase no VS Code/Jupyter, escolha o kernel do ambiente e execute todas as células.
O notebook da fase 1 localiza o projeto sem caminho pessoal, cria banco temporário, importa TXT, reabre o banco,
reimporta e testa ZIP. Esperado: 40 mensagens, zero novas na repetição e duas ocorrências legítimas idênticas.

Usa os mesmos módulos do terminal. Banco temporário não comprova conservação após reiniciar o runtime.
A persistência entre conexões é testada; o CLI mantém banco em disco. Não houve instalação em ambiente limpo;
as dependências registram versões do ambiente testado.

## Conceitos e limites

- Parsing: iOS e Android com ano de quatro dígitos, multilinha, avisos, edição, remoção e mídia omitida.
  Datas relativas dentro do texto ainda não são interpretadas. Fuso America/Sao_Paulo é premissa configurada;
  horários ambíguos por horário de verão e anos curtos são rejeitados com motivo e fonte.
- SQLite: migração inicial, FKs compostas, parâmetros e transação BEGIN IMMEDIATE. Autoria da importação vem
  do contexto, não do autor do WhatsApp. Há empresas, usuários, corpora, lotes, mensagens, fontes e avisos.
  Clientes/projetos/financeiro/agenda operacional ainda não têm tabelas neste incremento.
- Idempotência: hash do TXT no corpus evita repetir lote, inclusive dentro de ZIP. Sobreposições com
  mesma mensagem reutilizam registros por data/autor/texto/ocorrência. Sem IDs nativos, repetições
  indistinguíveis em exportações parciais geram aviso. Edição sinalizada preserva versões e candidatas.
- CRLF/LF: normalização só no texto lógico. Conteúdo original e linhas ficam preservados nas fontes.
  O texto original decodificado também fica no SQLite local. Originais não são alterados.
- ZIP: leitura em memória, sem extrair anexos; TXT até 2 MiB e ZIP/conteúdo descompactado até 20 MiB.
  Caminhos inseguros, vários TXT sem seleção clara, links e arquivos inválidos são rejeitados.

SQLite e FAISS serão complementares: SQLite guarda fontes e registros exatos; FAISS fará busca semântica.
Top-k não é base para somar todas as parcelas. FAISS ainda não foi implementado no projeto novo.

## Verificação realizada

22 testes locais passaram. Notebook executou cinco células de código sem erro.
[Resumo estruturado](./evidencias/marco1_importacao.json). O backup real disponível ao final tinha 322 entradas;
importação local sem rejeição e zero novas na repetição. A inspeção anterior de 161 cabeçalhos descrevia
outra versão inspecionada. Somente contagens/tipos foram guardados em evidência pública.

Não transferimos os testes de autopeças. Guardar uma mensagem de prompt injection como texto comprova somente
o comportamento do importador; não é avaliação de resistência de um agente LLM.

## Dados e próximos passos

_chat.txt e dados/privados são ignorados no Git. O original contém dados internos/credencial: não enviar
a modelos externos nem publicar no Git, LangSmith ou ZIP de entrega. Notebook/demonstração usam corpus fictício.

Marco 2 acrescentou a chain de propostas descrita abaixo. Este trecho registra o estado daquela etapa; o estado atual está no início do README. Nomes do arquivo não são identidades autenticadas.

## Marco 2 — analisar a demonstração

Instale as dependências opcionais de IA:

    python -m pip install -r requirements-ia.txt
    python executar.py

Menu **4**: apresenta oito propostas manuais da fixture, com fontes; cobertura esperada 40/40.
Esse modo testa interface/contrato, não compreensão de LLM.
Menu **5**: usa OpenAI gpt-4o-mini. Configure OPENAI_API_KEY no ambiente ou no .env deste projeto,
seguindo .env.example. Também pode indicar um arquivo explicitamente:

    python executar.py --arquivo-env "caminho/.env"

Não existe herança automática de chave de outro projeto. Nunca colocar chave no notebook ou Git.
Ambas as opções analisam somente os dados fictícios; o backup real não é enviado a serviços externos.
Corpora com importações de outro arquivo são bloqueados antes de enviar dados.

Alternativas não interativas (caminhos relativos à pasta atual):

    python executar.py --analisar fixture
    python executar.py --analisar fixture --estilo imperativa
    python executar.py --analisar api --arquivo-env "caminho/.env"
    python -m unittest discover -s tests -v

As propostas têm ID/trecho das mensagens, valor em centavos quando escrito, natureza e pendências.
Não houve confirmação de projetos/pagamentos/agendamentos no banco: a saída aguarda revisão humana.
Artefatos ficam em dados/privados/analises. Cobertura completa significa lotes concluídos,
não acerto de todas as interpretações nem extração de todos os fatos possíveis.

[Notebook 02](./notebooks/incrementos/02_extracao_estruturada.ipynb) usa o mesmo código e é offline por padrão.
requirements-notebook.txt inclui agora as dependências de IA para rodar os dois notebooks sem chave.
[Contrato, dados e limites](./docs/primeira_chain.md). 40 testes locais passaram; notebooks 01/02
executaram sem erro. Naquele marco, APIs de negócio, FAISS, agente, Streamlit e LangSmith ainda estavam planejados; o estado atual está no início do README.


## Fechamento da validação do marco 2

40 testes locais passaram após os ajustes; notebook 02 executado novamente, seis células sem erro.
A fixture manual produziu oito propostas com cobertura de 40/40 mensagens; não executa LLM.

Foram preservadas três execuções reais com gpt-4o-mini, somente com as 40 mensagens fictícias:
- marco2_api_real_20261110T020146555304Z.json: parcial, 8/40 mensagens, três propostas.
- marco2_api_real_20261110T021210978750Z.json: parcial, 24/40 mensagens, sete propostas.
- marco2_api_real_20261110T021400551051Z.json: parcial, 32/40 mensagens, onze propostas.

Os arquivos estão em evidencias/. São observações de execução, não taxas de qualidade.
O último lote rejeitado citou percentual sem o correspondente trecho literal. Não foi aprovado nem apagado.
Zero gravações operacionais nas três execuções. Datas dos nomes de arquivo estão em UTC.

F003: o primeiro retorno real misturou área projeto com objeto financeiro e foi rejeitado pelo parser.
A geração passou a usar JSON Schema estrito com três contratos de área separados; Pydantic continua validando
as regras locais. Horário sem fuso e valor sem fonte também foram observados na segunda execução;
o prompt recebeu instruções explícitas de offset e de não calcular valores nesta etapa.
A terceira execução ainda foi parcial. Não há reparo automático nem garantia de extração completa.

Revisão manual assistida do último artefato:
- Recebimento Alfa de R$ 2.000,00 mantém pagamento_informado e cita as mensagens 37/38: coerente com o relato,
  sem tratar conversa como comprovante.
- Cancelamento Beta cita a mensagem 35, mas deixou projeto=null: exige revisão de completude.
- Conflito de agenda contém horários que não aparecem nos trechos citados dessa proposta:
  a verificação atual não valida toda associação de datas/contexto.
Esta é revisão do assistente, não avaliação humana de Renan nem nota de juiz LLM.
Próximo passo: fortalecer rastreabilidade semântica e revisão/confirmacão transacional antes de aplicar propostas.


## Revisão de cancelamentos e mensagens editadas

A execução enviada por Renan concluiu 40/40 mensagens e gerou 17 propostas, mas classificou
o cancelamento Beta como correção sem projeto e não exibiu claramente a visita Gama editada.
A regra local reconhece apenas pedido explícito no início do trecho, como
Cancelar reunião Beta de 12/11/2026, sem interrogação. Corrige natureza/projeto,
preserva os valores anteriores em ajustes_revisao e exige vincular/confirmar antes de aplicar.
Perguntas, negações e nomes conflitantes não são convertidos por essa regra.

Toda mensagem marcada como editada é exibida separadamente, com seu texto literal.
Outros textos do mesmo autor/instante são apenas candidatos ao vínculo, nunca versões comprovadas.
Assim, o exemplo Gama mostra 15h e 16h sem escolher horário ou alterar compromisso.
O prompt também orienta o modelo, mas a apresentação das edições independe de sua resposta.

47 testes passaram (sete regressões novas). Reprocessamento local da análise real já salva:
17 propostas preservadas; cancelamento Beta corrigido; edição M0030 e candidato M0029 exibidos.
Não houve nova chamada de LLM para essa evidência. Zero gravações operacionais.
Arquivo: evidencias/marco2_revisao_cancelamento_edicao.json.
Reexecute a opção 4 para ver o aviso da edição; a opção 5 faz uma nova chamada real e pode variar.


Andamento: [cinco fases do trabalho](docs/andamento_fases.md). A fase 1 segue em validação; 54 testes locais passaram. Propostas com fonte inválida são registradas separadamente, preservando as válidas do mesmo lote sem aprovar a execução parcial. Detalhes e evidência em [primeira chain](docs/primeira_chain.md).
