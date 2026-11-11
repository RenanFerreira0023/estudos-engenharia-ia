# Revisão persistente — início da fase 2

A extração continua na chain. Este incremento acrescenta uma fila de interpretações no SQLite,
com decisão humana explícita. Ainda não é um agente com ferramentas.

## Testar pelo terminal

Na raiz do repositório:

    python ".\Agentes Cognitivos com LangChain\Projeto final 2\executar.py" --arquivo-env ".env"

1. Escolha 4 (fixture local) ou 5 (OpenAI). Propostas com fontes válidas são cadastradas na fila.
2. Escolha 6. Selecione um dos IDs mostrados e confira os dados e fontes.
3. Digite a para aceitar a interpretação, r para rejeitar, c para corrigir ou h para ver histórico.
4. Informe o comentário solicitado. Na correção, informe um JSON de campos a substituir, por exemplo:

       {"resumo":"Implantação do portal de atendimento da Alfa."}

5. Correção mantém a proposta pendente e incrementa a versão. Para aceitar a versão corrigida,
   selecione o mesmo ID, confira o novo conteúdo e escolha a.
6. Enter no campo ID volta ao menu. Saia com 0, execute novamente e escolha 6:
   decisões e histórico devem permanecer.

Não é necessário gastar uma chamada de API para testar: opção 4 exercita o mesmo serviço.
Análises antigas em JSON não são automaticamente importadas na fila; gere uma análise com esta versão.
O notebook [03_revisao_persistente](../notebooks/03_revisao_persistente.ipynb) usa banco temporário e
demonstra correção, decisão, versão obsoleta, isolamento e reabertura, sem LLM.

## Estados e efeitos

- pendente: interpretação aguardando revisão.
- aceita: usuário conferiu a interpretação. Pendências podem permanecer; não significa pagamento recebido
  ou compromisso reservado. O serviço operacional futuro ainda deve validar campos e regras.
- rejeitada: interpretação retirada do conjunto utilizável; fonte e histórico permanecem.

A fila não reabre decisões concluídas neste incremento. Repetir a mesma decisão é idempotente.
Não há tabelas de projetos, pagamentos ou agendamentos operacionais, nem confirmação desses registros.
Atores do WhatsApp não são automaticamente responsáveis autenticados de compromissos.

## Contratos e fronteiras

FilaRevisao recebe Contexto do serviço, nunca identidade escolhida pelo modelo.
Cada usuário revisa somente sua fila pessoal e um corpus que pode acessar. Administrador também
não confirma fila pessoal de colega. Administrador revisa todas as áreas próprias; financeiro apenas
financeiro; atendente projeto/agenda. Essa é a premissa restrita dos perfis fictícios do plano.
O terminal padrão continua Ana, sem autenticação. Isso não comprova login nem permissões completas do produto.

Fontes/área/autoria são imutáveis. Correções aceitam projeto, natureza, resumo, financeiro, agenda e
pendencias; precisam passar pelo contrato e nova validação das fontes do corpus.
Um valor corrigido que não aparece na fonte é rejeitado. Dados novos informados pelo usuário devem
seguir um fluxo de nova evidência/proposta no futuro; não são atribuídos falsamente ao histórico importado.
Resumo/projeto corrigidos manualmente ficam auditados, mas isso não é verificação semântica automática.

BEGIN IMMEDIATE envolve validação de versão e gravação da decisão/histórico.
Uma versão antiga não pode aceitar conteúdo que mudou após a tela ser exibida.
O registro mantém original_json e atual_json, e o histórico contém antes/depois, ator, motivo e instante.
O modelo não tem ferramenta que execute esse serviço automaticamente.

A chave da fila usa conteúdo estruturado, corpus, empresa e usuário; repetir a mesma análise não duplica
nem desfaz decisão manual. Paráfrases diferentes do modelo podem gerar novas propostas: consolidação
semântica ainda não existe e não há aplicação automática.

## Migração e validação

O SQLite sobe de v1 para v2 com duas tabelas novas: propostas_revisao e historico_revisao.
Fontes e importações anteriores são preservadas. Importar/listar continuam sem pacotes de IA;
a migração é um módulo separado sem Pydantic/LangChain. tzdata continua dependência básica.

72 testes passaram, incluindo 18 testes novos de revisão. Notebook 03: seis células executadas sem erro.
O roteiro 4 → 6 → aceitar foi executado em processo separado com banco temporário.
A [evidência](../evidencias/marco3_revisao_persistente.json) usa fixture identificada, sem nova API.
Antes da migração, um teste antigo exigia user_version=1; foi atualizado para 2 e acrescentado
teste que migra um banco v1 populado, preserva as fontes e confirma reimportação sem duplicação.
