# O valor -1 em `numero_de_operacoes`: teste empírico

**Data:** 2026-09-21
**Decisão que motivou:** `docs/triagem-ontologia.md`, item 1.1. Entre publicar a inferência, testar ou perguntar ao BCB, a decisão foi testar.
**Script:** `scripts/analises/sentinela_numero_de_operacoes.py`, sobre a camada bronze no Databricks (V2 e V1, jan/2024 a jul/2026).

## A hipótese testada

A metodologia da V2 não explica o valor `-1` na coluna `numero_de_operacoes`. A metodologia da V1 dizia, no item 4.l: "Casos em que o número de operações seja inferior ou igual a 15, a informação divulgada será '<= 15'".

A leitura dos normativos (`docs/leitura-normativos.md`, pergunta 4) concluiu, "por inferência forte", que **o `-1` da V2 é o `<= 15` da V1 com outro rótulo.** A ontologia registrou isso com `confianca: inferido`.

## Resultado: a hipótese está errada

### 1. A V2 publica contagens de 1 a 15

| Valor | Linhas na V2 | Linhas na V1 |
|---|---|---|
| `-1` | 2.590.482 | nenhuma |
| `<= 15` | nenhuma | 22.120.146 |
| de 1 a 15, explícitos | 3.026.742 | nenhuma |
| 1 | 752.761 | nenhuma |

A V1 usa `<= 15` em 75% das suas linhas. **A V2 divulga as contagens pequenas abertamente**, inclusive 752 mil linhas com exatamente uma operação. Se o `-1` substituísse o `<= 15`, esses valores não existiriam. O `-1` marca outra coisa.

### 2. As linhas com -1 são pequenas, mas não por terem poucas operações

| Faixa de contagem | Linhas | Carteira mediana por linha | Parcela da carteira |
|---|---|---|---|
| `-1` | 2.590.482 (26,7%) | R$ 30,8 mil | 6,71% |
| 1 | 752.761 | R$ 28,9 mil | 0,33% |
| 2 a 15 | 2.273.981 | R$ 169,8 mil | 4,37% |
| 16 a 100 | 1.875.859 | R$ 432,3 mil | 9,89% |
| acima de 100 | 2.194.728 | R$ 4.799,1 mil | 78,69% |

A linha típica com `-1` tem o tamanho de uma linha com uma operação só. Em conjunto, porém, essas linhas somam 6,71% da carteira, e a média por linha (R$ 5,5 milhões) mostra que algumas são grandes.

### 3. O -1 se concentra em nichos e em UFs menores

| Recorte | Maior incidência | Menor incidência |
|---|---|---|
| Segmento | Arrendamento 75,4%, Outros 66,1%, Fintech 51,8% | Banco 20,5%, Instituição de pagamento 20,9% |
| Modalidade | Títulos e valores mobiliários 97,7%, Arrendamento 80,0%, Infraestrutura 68,0% | Rurais 20,3%, Adiantamentos 21,7%, Empréstimos 22,5% |
| UF | Amapá 41,6%, Roraima 39,0%, Acre 36,5% | Santa Catarina e Rio Grande do Sul 20,8%, São Paulo 21,1% |
| Cliente | PJ 36,2% | PF 20,3% |

Em geral, as UFs de economia menor têm incidência maior, e as cinco menores taxas estão em MG, PR, SP, RS e SC. A relação não é perfeita: o Rio de Janeiro, segunda maior economia, fica no meio da lista, com 26,0%. Entre segmentos e modalidades, a incidência é maior nos nichos e menor nos bancos. No tempo, fica estável: entre 26,0% e 28,0% das linhas em todos os 31 meses.

### 4. O mesmo recorte alterna entre -1 e contagem

A combinação das nove dimensões gera 474.939 recortes ao longo dos 31 meses. Destes:
- 216.503 tiveram `-1` em algum mês;
- **80.401 tiveram `-1` em alguns meses e uma contagem divulgada em outros;**
- entre os que alternam, a maior contagem já divulgada tem mediana de 14 operações;
- o máximo chega a **514.490 operações.**

Um recorte com mais de meio milhão de operações não é suprimido por ter poucas operações. **O critério do -1 não é o número de operações.**

## Leitura

**O que se pode afirmar:**
- `-1` significa "contagem não divulgada".
- Não significa "até 15 operações".
- O critério de supressão não está publicado.

**Hipótese de trabalho, não confirmada:** sigilo aplicado quando o recorte tem poucas instituições ou poucos clientes. Ela é compatível com a concentração em nichos, em UFs menores e em PJ. Também é compatível com a alternância no tempo, que aconteceria quando um participante entra ou sai do recorte. O SCR.data não traz a instituição, então essa hipótese não pode ser testada com o dado publicado.

**Observação sem explicação:** entre 1 e 20, a contagem de linhas cai a cada valor, com uma única exceção. Há mais linhas com 6 operações (195.508) do que com 5 (158.599). É compatível com alguma regra atuando sobre recortes muito pequenos, mas não permite dizer qual.

## Busca por documentação oficial

Feita em 2026-09-21, depois do teste, para saber se o critério do `-1` estava publicado em algum lugar:

| Onde | Resultado |
|---|---|
| Metodologia V2, texto integral | Nenhuma menção a `-1`, sigilo ou supressão |
| Metodologia V1 | Só o `<= 15` e uma regra análoga para o CNAE: com 5 CNPJs ou menos, divulga só a seção |
| Página do SCR.data no portal de dados abertos, lida pela API | Nenhuma menção. A página ainda diz que a V1 parou em jun/2025, o que o dado desmente |
| Conjunto "SCR por sub-região", do mesmo departamento | Outro mecanismo: agrupa recortes pequenos em "Não Identificado", sem `-1` |
| Projetos públicos no GitHub que usam o SCR.data | Três tratam o `-1` como sigilo ou "limite de divulgação", sem citar fonte. Um deles mediu `-1` em 27% das linhas de dez/2024, o que bate com os 26,9% medidos aqui |

**Conclusão:** quem usa o dado trata o `-1` como sigilo, mas o critério não está publicado. O que este teste acrescenta é o que ninguém tinha registrado: o critério não é o número de operações. O caminho para uma resposta oficial continua sendo um pedido pela Lei de Acesso à Informação (issue #21).

## Consequências

1. **Na ontologia:** `numero_de_operacoes.valor_sentinela` passa de `inferido` para `lacuna`. O significado "contagem não divulgada" fica registrado com evidência, e a hipótese derivada da V1 fica registrada como refutada.
2. **No staging:**
   - na V2, `-1` vira nulo e ganha a marca `contagem_suprimida`;
   - na V1, `<= 15` vira nulo com o intervalo de 1 a 15 registrado;
   - somar a coluna num grupo com linhas suprimidas dá um **limite inferior**, e o mart precisa dizer isso.
3. **Errata da pergunta Q18** (`evaluation/questions.yml`, pré-registrada em 2026-08-20 e mantida sem alteração):
   - A nota da pergunta chama o `-1` de "sentinela de supressão por sigilo estatístico". A parte essencial continua certa: é sentinela, e dividir a carteira por ele sem tratamento produz resultado sem sentido.
   - "Sigilo estatístico" é hipótese.
   - O gabarito da Q18 deve dizer que o ticket médio só é calculável sobre as linhas com contagem divulgada, que excluem 6,71% da carteira, e de forma não aleatória.
4. **Próximo passo possível:** pedir o critério ao BCB por Lei de Acesso à Informação. É a única forma de passar de hipótese a fato.

## Nota de método

A primeira leitura dos normativos chegou a uma conclusão plausível, bem fundamentada e errada. O que a derrubou foi a decisão de testar em vez de publicar a inferência. O teste levou minutos sobre o bronze. É o argumento do projeto aplicado ao próprio projeto: **uma definição que ninguém verificou é hipótese, por mais bem escrita que esteja.**
