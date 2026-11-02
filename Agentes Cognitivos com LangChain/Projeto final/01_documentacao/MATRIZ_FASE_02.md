# Fase 2 — requisitos, evidências e equivalências

Referências disponíveis: [arquitetura inicial](./arquitetura_inicial_auto_super_parts_cwb.html),
[definição](./definicao_projeto.html), [instruções](../INSTRUCOES_PARA_IA_PROGRAMADORA.md)
e os pedidos de correção da fase 2 feitos por Renan. A arquitetura define o destino
final do projeto; nem todos os seus componentes pertencem à fase 2.

O enunciado original do professor não foi localizado entre os arquivos do projeto.
Esta matriz compara a entrega com os documentos disponíveis; **não certifica a
rubrica literal da disciplina**. Uma confirmação de equivalência não foi presumida.

| Requisito / escopo | Implementação e evidência | Situação |
| --- | --- | --- |
| Agente que decide ferramentas | `AtendimentoFase02`, `create_agent`, ChatOpenAI/gpt-4o-mini; notebook real mostra decisões e ciclo completo | Atendido no escopo implementado |
| Ferramentas descritas e tipadas | `@tool` para veículos, catálogo, CEP e cálculo; BaseModel no orçamento; schema exibido no notebook | Atendido |
| Catálogo consultado, sem respostas fixas no prompt | JSON importado em SQLite, consultas parametrizadas; SQL/argumentos, produtos e metadados retornados | Atendido; não equivale a text-to-SQL |
| Cálculo determinístico e origem do preço | Preço e estoque relidos do catálogo; Decimal e regras do JSON; subtotal comparado com multiplicação independente | Atendido |
| API externa real | ViaCEP retorna HTTP 200 e endereço nos dois CEPs de entrega; endereço alimenta município/UF do cálculo | Atendido com evidência real |
| Dados ausentes e falhas de API | Formato inválido sem rede; CEP inexistente, timeout, indisponibilidade e JSON inválido em testes com transporte injetado identificado | Atendido em testes; falhas simuladas não apresentadas como incidentes da API real |
| Prompt, limites e exemplos | Persona/tarefa/contexto/formato explícitos; estratégias ilustrativas, configuração incompleta pede esclarecimento, óleo técnico e dados comerciais pendentes não são inventados | Implementado; não é garantia universal de comportamento da LLM |
| Orçamento de destino cadastrado | CEP 84010000 → Ponta Grossa/PR; 120 km simulados; frete 531 centavos, total 4231; 4 dias úteis sem marco inicial definido | Atendido, com pendência comercial explícita |
| Destino sem distância | CEP 01001000 → São Paulo/SP; subtotal conhecido, frete/prazo/total com entrega null; resposta explica ausência | Atendido |
| Correção do argumento minItems | Binding estrito no middleware; teste intercepta o JSON enviado pelo SDK; replay dos argumentos antigos continua rejeitado | Atendido sem afrouxar validação |
| Código modular e notebook executado | `fase_02_agente_ferramentas.ipynb` importa `.py`, mostra prompt/schema, ferramentas/argumentos/retornos/resposta final | Atendido; execução real e simulação separadas |
| Dependências e reprodução | Versões fixadas; `reproduzir_fase02.py` cria cópia renomeada sem segredos, instala venv nova e executa testes/notebook offline | Resultado observado no relatório de reprodução |
| Evidências e histórico | Falha original intacta; novos arquivos únicos; snapshots de schema e conferência por hashes | Atendido |
| Preservação da fase 1 | Código e notebook anteriores preservados; suíte de 23 testes repetida | Atendido |

## Equivalências que precisam de confirmação do enunciado original

- Foi usado **`create_agent`**, com a stack instalada e testada. Se a rubrica exigir
  literalmente `AgentExecutor`, `create_react_agent`, um agente textual ReAct ou
  comparação entre executores, esta entrega não demonstra esses nomes/abordagens.
  O ciclo modelo → ferramenta → modelo atende ao objetivo funcional, mas não
  comprova equivalência acadêmica a toda API antiga. Não se instalou stack
  incompatível apenas para reproduzir um nome.
- O erro controlado pelas ferramentas e o limite de recursão do agente não
  equivalem automaticamente a parâmetros legados específicos como
  `handle_parsing_errors` ou `max_iterations`, caso sejam literalmente exigidos.
- As quatro ferramentas são funções tipadas expostas por `@tool`. Se forem
  exigidas ferramentas externas/bibliotecas nomeadas ou comparação de toolkits,
  é necessário conferir a redação original; isso não é declarado como atendido.
- Os exemplos no prompt são **estratégias ilustrativas**, não uma comparação
  experimental zero-shot versus few-shot nem transcrições observadas. Uma
  eventual exigência dessa comparação permanece sem demonstração.

## Fora desta fase e pendências de domínio

Memória de sessão/perfil persistente pertence à fase 3; SQL gerado por linguagem
natural e políticas via FAISS pertencem à fase 4; auditor integrado e LangSmith
pertencem à integração/avaliação. Não foram implementados como parte desta
correção. PDF técnico e vídeo são entregas finais separadas.

Prazo local de Curitiba, marco inicial da contagem, regras de reserva/falta,
troca/garantia e homologação técnica de peças/óleo continuam pendentes. Um
orçamento didático não reserva estoque nem confirma compra.

Consulte os [resultados observados](../04_avaliacao_e_evidencias/resultados/RESULTADOS_FASE_02.md)
para os nomes dos arquivos e limites de cada verificação.
