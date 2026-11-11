# Bateria de testes — incrementos 1 a 4

Execute na pasta `Agentes Cognitivos com LangChain/Projeto final 2`, com o `.venv` ativo. Use um banco isolado para não misturar com seus dados anteriores:

```powershell
$env:SECRETARIA_BANCO = (Join-Path (Get-Location) 'dados/privados/teste_visual.sqlite3')
python -m streamlit run app.py
```

Abra o endereço local mostrado pelo Streamlit. Para o terminal usar o **mesmo** banco, abra outro PowerShell na mesma pasta e execute:

```powershell
python executar.py --banco '.\dados\privados\teste_visual.sqlite3' --usuario ana
```

Não copie `.env`, banco privado ou backup real para o Git.

## 1. Financeiro e revisão

1. Na aba **Fontes**, importe a demonstração fictícia. Na aba **Revisão**, gere as propostas locais, abra a proposta de projeto Alfa e aceite com comentário. Confira a prévia e aplique a interpretação para criar o projeto. Anote o ID real exibido.
2. Na aba **Financeiro**, proponha orçamento de `10000,00` para o projeto, aceite pelo ID e defina duas parcelas de `300000` e `700000` centavos. O relatório deve mostrar orçamento aceito `R$ 10.000,00` e saldo igual ao orçamento.
3. Informe pagamento de `1000,00` na parcela de entrada. O saldo **não muda**. Confirme o pagamento depois de marcar a conferência: recebido `R$ 1.000,00`, saldo `R$ 9.000,00`.
4. Estorne esse pagamento com motivo. O saldo volta para `R$ 10.000,00`; o lançamento continua visível como `estorno`. Clique **Novo lançamento de pagamento** para gerar outra chave, informe o valor corrigido e confirme. Repetir o envio sem clicar nesse botão reutiliza a chave anterior.
5. Em projeto sem pagamentos, proponha outro orçamento e use **Substituir orçamento ativo** com motivo. O anterior permanece no histórico; parcelas antigas não aceitam novos pagamentos. Tentar substituir após existir pagamento no orçamento anterior deve falhar pedindo reconciliação humana.
6. Troque para `carla`: o financeiro deve negar acesso. Troque para `bruno`: leitura e operações autorizadas devem respeitar o mesmo SQLite.

## 2. Interface, memória e agenda

1. Em **Conversa**, diga `Estou falando do cliente Alfa.` e depois `Qual cliente mencionei?`. O nome deve vir do contexto. Clique **Nova conversa** e repita a segunda pergunta: não deve reaproveitar a conversa anterior. Mude o usuário para `bruno`: ele não deve ver as mensagens de Ana.
2. Na aba **Agenda**, use um cliente já cadastrado, data **futura**, duração de 60 minutos e endereço completo. Criar a proposta não a insere em **Minha agenda**; confirme pelo ID para aparecer. Uma segunda visita sobreposta para o mesmo atendente deve ser recusada.
3. Em **Fontes**, indexe a demonstração somente após marcar a autorização de envio dos textos. Pergunte no chat `Onde foi dito o orçamento do projeto Alfa?`. Espere uma fonte com ID de mensagem. Pergunte `Quantas mensagens do Bruno mencionam orçamento e Alfa?`; espere consulta estruturada com total 1 no corpus fictício.

## 3. Verificação da resposta

Execute os testes locais:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests -p 'test_verificador_avaliacao.py' -v
python -m unittest discover -s tests -p 'test_financeiro.py' -v
```

Eles cobrem contagem incompatível com SQL, valor financeiro sem suporte e a oferta `Posso consultar...`, que recebe nota zero. No chat real, confira o estado de verificação exibido com cada resposta. Se o juiz falhar ou reprovar a correção, deve aparecer uma limitação segura; isso não é evidência de que a resposta original estava certa.

## 4. Avaliação e LangSmith

```powershell
python avaliar.py --modo fixture
```

Esperado: seis linhas identificadas como `fixture_manual`; a linha `oferta_consulta` tem notas `0 | 0`. As cinco notas positivas são **gabarito da fixture**, não métricas do agente. O JSON local fica em `dados/privados/avaliacoes` e traz `comentario_humano: PENDENTE`; revise manualmente pelo menos uma resposta.

Com chave OpenAI válida, execute a avaliação real de quatro casos aplicáveis em banco temporário. Os dois casos de proposta e oferta de consulta permanecem apenas como fixtures de critério, pois exigiriam contexto prévio que não existe num turno isolado:

```powershell
python avaliar.py --modo api
```

Observe erros e notas caso a caso. Respostas do modelo variam; não suponha aprovação. Para criar experimento remoto apenas com os casos fictícios, configure `LANGSMITH_API_KEY` e rode:

```powershell
python avaliar.py --modo api --langsmith
```

Abra o experimento no LangSmith e compare, por caso, trajetória exata, nota semântica e comentário humano. Registre falhas observadas antes de concluir o relatório. O caso negativo `oferta_consulta` é teste local do juiz e não é atribuído ao agente real.

## Regressão e entrega

```powershell
python -m unittest discover -s tests -q
```

O relatório atual é textual no console e na interface. Excel, PDF final e vídeo ainda não fazem parte deste incremento.
