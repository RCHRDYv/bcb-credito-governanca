# ADR 0010: A Selic do projeto é a meta do Copom, vigente no último dia do mês

**Status:** Aceito
**Data:** 2026-09-24

## Contexto

As perguntas Q25 e Q26 cruzam a inadimplência com a Selic, que o SCR não traz (issue #37). Em 2026-09-24 o Yuri antecipou esta fonte para a v0.1, para o gabarito sair em SQL com o máximo de perguntas.

"Selic" não é um número só. O SGS do BCB publica pelo menos a meta definida pelo Copom (série 432, diária) e a taxa efetiva (série 4189, mensal, e série 11, diária). Os valores são próximos, mas não iguais: em set/2026, meta de 13,75% e efetiva de 13,82%. E a meta é diária, enquanto o SCR é mensal.

## Decisão

**A Selic do projeto é a meta do Copom, série 432.** Quem decide é o pré-registro, e não uma preferência do projeto. A Q25 em português diz "trajetória da Selic", mas a versão em inglês, registrada junto, diz "Selic policy rate", que é a meta. A Q26 pergunta pela defasagem entre a variação da Selic e a da inadimplência, e a variação da meta são as decisões do Copom, que têm data.

**Cada mês do SCR recebe a meta vigente no último dia do mês,** que é a data-base do SCR. O valor é buscado como o último publicado até a data-base, e a coluna `data_do_valor` diz de que dia ele veio. Um teste exige que todo mês tenha valor e que ele seja do próprio último dia.

**A consulta à API termina na data da extração.** Sem data final, a série 432 volta com datas no futuro, porque o SGS repete a meta vigente até a próxima reunião do Copom. Em 2026-09-24 ela ia até 04/11/2026. A ingestão recusa a resposta se vier alguma data depois da extração.

## Alternativas descartadas

**Taxa efetiva (série 4189).** Seria mensal, sem conversão, mas não é o que a pergunta registrada pede. Trocar uma pela outra muda a resposta sem nenhum erro aparente, e por isso a diferença está registrada como armadilha na ontologia.

**Média da meta no mês.** Num mês com reunião do Copom, a média produz uma taxa que nunca vigorou. O valor do último dia é o que estava em vigor na data-base do SCR.

**Guardar a série inteira, com as datas no futuro, e cortar no staging.** Deixaria no bronze linhas que não são observação de nada. Cortar na consulta mantém o bronze igual ao que a API devolveu para uma consulta registrada no manifesto.

## Consequências

**Positivas.**
- Q25 e Q26 passam a ser respondíveis, e a cobertura da v0.1 sobe para 35 das 41 perguntas.
- O padrão fica pronto para outras séries do SGS: `ingestion/baixar_sgs.py` recebe a lista de `SERIES_SGS`, e uma série nova é uma linha em `ingestion/fontes.py`.

**Negativas, e são reais.**
- **31 meses e 15 decisões do Copom são pouca série** para estimar defasagem com confiança, e a Q26 precisa dizer isso na resposta.
- **O sha256 do arquivo muda a cada dia,** porque a data final da consulta muda. O manifesto registra a consulta e o número de linhas, e o diff mostra o que entrou.
