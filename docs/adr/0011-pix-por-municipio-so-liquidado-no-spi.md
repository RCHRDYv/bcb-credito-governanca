# ADR 0011: O PIX do projeto é o liquidado no SPI, por mês fechado, com os dois lados guardados

**Status:** Aceito
**Data:** 2026-09-24

## Contexto

As perguntas Q22, Q23 e Q24 dependem do volume financeiro de PIX, que o SCR não traz (issue #36). Em 2026-09-24 o Yuri antecipou esta fonte para a v0.1.

O BCB publica o PIX por município no recurso `TransacoesPixPorMunicipio`, do serviço OData `Pix_DadosAbertos`: por mês e município, valor, quantidade e pessoas, separados por pagador e recebedor e por PF e PJ, com o código IBGE da UF. A investigação da API, registrada na #36, achou quatro características que decidem o desenho.

## Decisões

**A consulta é feita mês a mês, e só com meses fechados.** O parâmetro `DataBase` é "a partir de", e não o mês exato. O mês corrente vem incompleto: set/2026 somava R$ 2,5 tri, contra cerca de R$ 3,2 tri nos meses cheios. E o recurso não aceita paginação, porque a documentação o marca como `naoPaginavel` e `$skip` devolve erro 500. Por isso cada mês fechado é uma consulta com filtro de mês exato, e cada um fica num arquivo bruto próprio. A ingestão recusa a resposta se faltar um mês, se aparecer o mês corrente ou se algum município sumir de um mês para o seguinte.

**O escopo é o PIX liquidado no SPI, e isso fica declarado.** A documentação do recurso de estatísticas gerais diz que ele não inclui o PIX liquidado nos livros do próprio participante. O total nacional do recurso por município é idêntico ao dele, R$ 3.174,5 bi em ago/2026 nos dois, e então o escopo é o mesmo. O volume publicado fica abaixo do volume real de PIX, e a Q22 precisa dizer isso.

**O fato guarda os dois lados, e não escolhe um.** No total do país, pagador e recebedor somam o mesmo, mas por UF eles diferem. Escolher um lado no modelo decidiria a Q24 no lugar de quem responde, e o experimento mede justamente se a resposta diz qual lado usou.

A igualdade nacional vira teste, mês a mês. O próprio dado publicado a quebra em dois meses, ago e set/2025, por cerca de R$ 1,2 milhão em R$ 2,6 trilhões. A diferença já vem nos JSONs da API, e o teste avisa com esses dois meses e falha com um terceiro.

**A UF é a do domicílio do usuário, por inferência.** O recurso por município não define o município. O recurso irmão define a região como a do "domicílio do usuário". A ontologia registra isso com confiança de paráfrase e com a fonte. É comparável à UF do SCR, que é domicílio da pessoa ou sede da empresa.

**A linha sem município entra com UF nula.** Ela reúne cerca de 0,2% do total (R$ 7,7 bi em ago/2026), pertence ao total nacional e fica fora de qualquer recorte por UF.

**Os meses do fato são os do SCR,** para todos os fatos dividirem a mesma `dim_tempo`. O PIX publica um mês a mais, que fica de fora do modelo, mas continua no bronze.

## Alternativas descartadas

**Recurso de estatísticas gerais (`EstatisticasTransacoesPix`).** Tem mais recortes, como idade e finalidade, mas só por região, e não por UF. As perguntas pedem UF.

**Uma consulta só, com paginação.** O recurso recusa paginação, como está acima.

**Guardar só um lado no fato.** Esconderia a ambiguidade que a Q24 precisa enfrentar.

## Consequências

**Positivas.**
- Q22, Q23 e Q24 passam a ser respondíveis, e a cobertura da v0.1 sobe para 38 das 41 perguntas.
- A igualdade entre pagador e recebedor vira teste de completude do dado, de graça.

**Negativas, e são reais.**
- **O volume é o do SPI, e não o de todo PIX.** O dado não permite estimar o que fica de fora.
- **O município é inferido como domicílio,** e não afirmado pela documentação do recurso.
- **Dois municípios do RN só aparecem a partir de abr/2025.** Antes disso, o PIX deles provavelmente estava na linha sem município, e a série do RN tem um pequeno degrau ali.
