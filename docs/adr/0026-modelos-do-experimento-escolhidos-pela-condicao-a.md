# ADR 0026: Os modelos do experimento se escolhem pela condição A, só com o esquema

**Status:** Aceito
**Data:** 2026-10-07

## Contexto

O ADR 0012 decidiu que o experimento usa dois modelos abertos de classes diferentes, rodando localmente em 12 GB de VRAM: um da classe de ~14B parâmetros em 4 bits e outro da classe de ~7 a 8B. Os nomes se escolhem no momento da execução, pelo próprio gabarito do projeto, porque modelos abertos mudam rápido. A seleção é a #48, e é a primeira execução contra o gabarito.

O ADR 0012 não diz em que condição a seleção roda, e a escolha não é neutra. A seleção usa as mesmas 41 perguntas do experimento, e o modelo que fica é o que foi melhor numa condição. Essa condição sai favorecida nas comparações em que entra:

- **Escolher pelo acerto em B** puxaria o resultado a favor da ontologia, nas H1, H3 e H5 do ADR 0013.
- **Escolher pelo acerto em A** puxa para o outro lado: o modelo que fica é o que se vira melhor sem contexto, o que joga contra a H1 e a H2.
- **Escolher pela média das quatro condições** exigiria rodar C e D, e o corpus e o índice do RAG (#46) ainda não existem.

## Decisão

Decidido pelo Yuri em 2026-10-06, e registrado pela #47 junto das hipóteses (`evaluation/hipoteses.yml`):

1. **A seleção roda na condição A,** só com o esquema, com as 41 perguntas do `questions_v3.yml`.
2. **Fica, em cada classe, o candidato com mais perguntas certas,** pela regra de comparação registrada no `hipoteses.yml`: 5 execuções por pergunta, temperatura de 0,2, seeds de 1 a 5, e acerto quando 3 ou mais das 5 execuções acertam. Decidido pelo Yuri em 2026-10-07.
3. **Empate é o mesmo número de perguntas certas,** e o desempate é o menor uso de VRAM. Decidido pelo Yuri em 2026-10-07.
4. **A execução da seleção não entra no experimento.** A condição A roda de novo, com o modelo escolhido, junto de B, C e D. Decidido pelo Yuri em 2026-10-07.
5. **O registro da escolha,** antes do experimento, traz:
   - a versão exata e a quantização de cada modelo;
   - os parâmetros de geração;
   - o resultado de todos os candidatos, publicado.
6. **O viés é declarado junto do resultado:** a seleção pela condição A é conservadora contra a H1 e a H2.

Este ADR complementa a decisão 4 do ADR 0012, que continua valendo.

## Alternativas descartadas

**Seleção pela condição B.** Escolheria o modelo que melhor usa a ontologia e inflaria as hipóteses a favor dela, que são o centro do experimento.

**Seleção pela média das quatro condições.** Dependeria do RAG pronto, e ainda assim escolheria pelo próprio resultado que o experimento mede.

**Ranking externo, como um leaderboard de text-to-SQL.** O ADR 0012 já decidiu que a escolha sai do gabarito do projeto, em português e no domínio do SCR.data, e não de um ranking em inglês e sobre outras bases.

**Reaproveitar a execução da seleção como a condição A do experimento.** Economizaria execuções, mas a condição A passaria a ser aquela em que o modelo foi escolhido por ir bem. Isso somaria um viés a favor de A, além do que esta decisão já declara.

## Consequências

**Positivas.**
- O viés da seleção tem direção conhecida, e é contra as hipóteses do projeto. Um efeito da ontologia que apareça mesmo assim é mais crível.
- A seleção não depende do RAG, e a #48 pode rodar antes da #46.

**Negativas, e são reais.**
- **A H1 e a H2 ficam mais difíceis de sustentar.** Um modelo escolhido por ir bem sem contexto tem menos a ganhar com contexto.
- **A condição A roda duas vezes,** na seleção e no experimento, e isso dobra o custo dessa condição.
- **A seleção usa as mesmas perguntas do experimento.** Não há conjunto separado para escolher, porque as 41 perguntas são todo o conjunto registrado. O efeito é o do item anterior, e é declarado junto do resultado.
