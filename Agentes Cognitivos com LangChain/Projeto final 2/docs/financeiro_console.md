# Financeiro operacional no console

O menu **12 Financeiro** usa o mesmo SQLite do projeto. O orçamento começa como **proposto**; a ação de aceitar é explícita. Depois de aceito, é possível definir parcelas cuja soma corresponde exatamente ao valor contratado. Um pagamento começa como **informado** e só reduz o saldo quando uma pessoa o confirma separadamente.

O relatório da opção financeira **1** lê um snapshot consistente e mostra projeto, cliente, CNPJ quando houver, orçamento aceito, percentual de entrada acordado, parcelas, recebimento confirmado e saldo. Sem orçamento aceito, mostra **não definido** para valores derivados. Anotações do chat não entram nos cálculos. Os valores são guardados em centavos; a apresentação em reais não usa `float`.

Fluxo para testar em um banco novo, usando apenas dados fictícios:

1. Opção **1** importa a conversa fictícia. Opção **4** cria propostas locais; opção **6** aceita a proposta de projeto Alfa; opção **10** aplica essa interpretação e cria o projeto operacional. Anote o ID do projeto.
2. Opção **12 → 2** propõe orçamento de `R$ 10.000,00`, entrada acordada `30`. **12 → 1** ainda mostra saldo indefinido.
3. **12 → 3** aceita o orçamento por ID. **12 → 4** cria duas parcelas, `R$ 3.000,00` e `R$ 7.000,00`. A soma diferente de `R$ 10.000,00` é recusada.
4. **12 → 5** informa `R$ 1.000,00` na parcela de entrada. **12 → 1** ainda mostra recebido `R$ 0,00` e saldo `R$ 10.000,00`.
5. **12 → 6** confirma o pagamento após conferir. **12 → 1** mostra recebido `R$ 1.000,00` e saldo `R$ 9.000,00`. Repetir a confirmação não duplica o valor.
6. No menu **9**, um usuário `ana` ou `bruno` pode perguntar pelo saldo do projeto Alfa: a ferramenta `consultar_financeiro_projeto` deve consultar o relatório. O usuário `carla` recebe `acesso_negado` e nenhum valor financeiro.

Os lançamentos são manuais e auditados; a conversa importada não comprova transferência bancária. O menu **12 → 7** substitui um orçamento aceito por uma revisão proposta com motivo, preservando o anterior; pagamentos vinculados impedem substituição automática. **12 → 8** cancela relato ou estorna pagamento confirmado sem apagar o lançamento, e o saldo é recalculado. Um pagamento corrigido exige novo lançamento e nova chave. O relatório em tela é a entrega definida para este projeto; não há exportação Excel.
