# Fase 4 — primeiro incremento do índice de fontes

`IndiceFontes.preparar()` recebe um corpus autorizado, lê todas as mensagens originais e cria um índice FAISS em etapa separada da consulta. O manifesto salva ID do corpus, empresa, modelo, IDs das mensagens, dimensões e hash da versão dos textos. O índice e o manifesto ficam no diretório privado escolhido pelo chamador; não devem ser publicados no Git.

`IndiceFontes.buscar()` exige um índice existente e compara o manifesto com a versão atual do SQLite. Se mensagens forem acrescentadas ou corrigidas, pede nova preparação; não reindexa automaticamente durante uma pergunta. A consulta revalida acesso ao corpus antes de abrir os arquivos. O resultado traz ID da mensagem, instante, autor, texto original e similaridade. O texto continua no SQLite, não no manifesto.

O [notebook 10](../notebooks/10_indice_fontes_faiss.ipynb) usa apenas a conversa fictícia e vetores definidos manualmente. Demonstra preparação, reuso sem novo embedding, busca com fonte e bloqueio de outro usuário. O teste automatizado também verifica recusa de índice desatualizado. **Não é avaliação semântica com embeddings reais.**

Ainda faltam a preparação explícita com embeddings reais, integração da ferramenta ao agente, consulta estruturada para dados exaustivos e análise de uma falha real de recuperação. A busca top-k serve para localizar trechos; não calcula saldo ou soma pagamentos.
