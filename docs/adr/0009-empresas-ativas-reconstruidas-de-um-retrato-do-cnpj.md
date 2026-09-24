# ADR 0009: Empresas ativas por UF, reconstruídas mês a mês de um único retrato do CNPJ

**Status:** Aceito
**Data:** 2026-09-24

## Contexto

A issue #25 traz os denominadores por UF que o SCR não tem. Eles servem às perguntas Q11, Q12 e Q14, à tela 1 do dashboard e ao indicador de espaço da camada de decisão, que é "carteira PJ por empresa ativa, comparada à mediana nacional".

- **População:** vem do IBGE, pela tabela 6579 do SIDRA, e não teve decisão difícil. É uma estimativa por ano, com referência em 1º de julho, e cabe numa chamada de API.
- **Empresas ativas:** exigiram quatro decisões, tomadas com o Yuri em 2026-09-24.

## Decisões

### 1. A fonte é o CNPJ aberto da Receita Federal

A Receita publica um retrato mensal completo do cadastro desde mai/2023, com os campos de que o denominador precisa: matriz ou filial, situação cadastral, UF, porte, natureza jurídica e opção pelo MEI.

### 2. O denominador conta matrizes, e não estabelecimentos

No SCR, a UF de pessoa jurídica é a da sede (`uf_e_domicilio_ou_sede`). O CNPJ aberto é uma tabela de estabelecimentos, com cada filial na UF onde funciona. Contar linhas ativas por UF poria no denominador de um estado empresas cuja carteira o SCR registra em outro, e o resultado ainda pareceria plausível.

### 3. A série mensal é reconstruída de um único retrato

Cada retrato do CNPJ tem cerca de 7 GB compactado, e os 30 meses do SCR somariam cerca de 210 GB. Nenhuma pergunta pré-registrada precisa de um retrato por mês.

**Um retrato só já permite reconstruir o estoque de qualquer fim de mês passado,** porque cada CNPJ traz a data de início da atividade e a data da última mudança de situação:

```
ativa no fim do mês D =
    início da atividade <= D
    e ( (ativa hoje     e última mudança <= D)
     ou (não ativa hoje e última mudança >  D) )
```

A implementação trata isso como intervalos. Cada matriz vira um intervalo semiaberto em que esteve ativa. O intervalo é dividido em antes, durante e depois do MEI, porque a condição de MEI também muda com o tempo e o Simples traz as datas de entrada e de saída. O estoque de cada fim de mês sai de uma soma acumulada de eventos (+1 quando um trecho começa e -1 quando termina), em vez de cruzar 25 milhões de matrizes com 31 meses.

**O que a reconstrução não sabe:**

- **Estados intermediários.** Uma empresa que passou de inapta para baixada depois de D conta como ativa em D, e talvez já estivesse inapta.
- **Mudança de UF da matriz.** A empresa aparece sempre na UF de hoje.
- **Porte e natureza jurídica no passado.** A Receita só publica os de hoje.
- **Matriz fora do ar sem data de saída.** Uma matriz não ativa com data de mudança ausente (a Receita publica "0") não tem como ser situada, e ficaria fora. No retrato de set/2026 não há nenhum caso, e o QA confere isso a cada execução.

**Por isso o erro é medido, e não suposto.** Também foram baixados os Estabelecimentos de dois retratos antigos, jun/2024 e jun/2025. Em cada um, a contagem real de matrizes ativas por UF é comparada com a reconstruída na data de corte daquele retrato (`mrt_erro_da_reconstrucao`). No retrato mais recente, as duas precisam ser iguais, e um teste confere isso: é a prova de que a regra do intervalo está certa antes de ser usada para o passado.

**A data de corte não é a do nome do arquivo.** O nome traz uma data, como "D60912", mas o retrato de set/2026 tem 226 matrizes abertas em 13/09, um dia depois. O de jun/2025 também vai um dia além do nome. A data de corte usada é a mais recente que aparece no próprio retrato. Na primeira medição, com a data do nome, sobravam 67 empresas de diferença no retrato mais recente. Com a data de corte, a diferença é zero em todas as UFs.

**Erro medido em 2026-09-24,** com 26.856.762 empresas ativas no retrato de set/2026. O mesmo número sai de duas implementações independentes, o SQL do dbt no Databricks e o polars de `scripts/analises/qa_fontes_externas.py` sobre os Parquets locais:

| Retrato | Distância até set/2026 | Real | Reconstruído | Erro no total | Erro por UF |
|---|---|---|---|---|---|
| jun/2024 | 27 meses | 23.126.424 | 23.173.675 | +0,20% | de -2,30% (AC) a +1,49% |
| jun/2025 | 15 meses | 24.785.601 | 24.840.786 | +0,22% | de -1,35% (AP) a +1,04% (PE) |
| set/2026 | o próprio | 26.856.762 | 26.856.762 | 0 | 0 em todas |

O erro no total é pequeno e positivo, como a regra prevê: empresas que passaram por inapta antes de serem baixadas contam como ativas por mais tempo do que estiveram. Por UF, os maiores erros são negativos e ficam em estados do Norte (AC, AM, AP, RR), onde a reconstrução conta menos que o real. Isso é compatível com matrizes que mudaram de UF depois do retrato antigo, e a reconstrução as põe na UF de hoje. **O limite declarado é de até 2,3% por UF para meses com dois anos de distância do retrato.**

**Dois defeitos do dado publicado, tratados de forma explícita** e registrados em `ontology/fontes_externas.yml`:

- **Dois marcadores de data ausente.** Estabelecimentos usa "0" e o Simples usa "00000000". A conversão estrita de datas falhou no segundo, que ninguém tinha previsto, e foi assim que ele apareceu. A macro trata exatamente os dois e continua estrita para o resto.
- **Uma empresa com cadastro defeituoso.** O CNPJ básico 08314885 tem duas matrizes ativas e aparece duas vezes na tabela Empresas, uma delas vazia. É o único caso nos três retratos. Empresa é o CNPJ básico, então ela conta uma vez, e a validação conta CNPJs básicos distintos pela mesma definição.

### 4. O download vem de um espelho, e a fonte continua sendo a Receita

Em 2026-09-24, o servidor da Receita entregava cerca de 4 MB/s, parava as conexões depois de uns 300 MB e, em seguida, deixou de responder, inclusive no navegador. A Casa dos Dados mantém um espelho público dos mesmos arquivos, servido por CDN, sem login, a cerca de 100 MB/s.

O espelho é só o meio de transporte, e isso é verificado duas vezes:

- **Byte a byte.** 613 MB baixados do servidor oficial antes da queda são idênticos ao começo dos mesmos arquivos no espelho.
- **Por tamanho, arquivo a arquivo.** Sempre que a listagem oficial responde, o tamanho de cada ZIP do espelho é conferido contra ela. O manifesto registra o resultado em `conferencia_com_a_receita`, e tamanho divergente interrompe a ingestão. Na primeira execução, os 43 arquivos foram conferidos.

### 5. O bronze guarda o dado inteiro, e o staging só o que é usado

Decidido com o Yuri: as tabelas da Receita entram no bronze como publicadas, no padrão do ADR 0004. Elas trazem nome fantasia, endereço, telefone e e-mail, que no caso do MEI são dados de uma pessoa. O staging seleciona só as colunas usadas, então esses campos param no bronze e não chegam a nenhuma tabela consultada. A tabela de Sócios, com nome e CPF parcial, não é ingerida: nenhuma pergunta a usa.

## Alternativas descartadas

**Um retrato por mês.** É exato, mas custa cerca de 210 GB e horas de download de um servidor instável, sem nenhuma pergunta que dependa disso.

**CEMPRE do IBGE.** Tem API leve, mas é anual e sai com dois a três anos de defasagem, e não cobre o período do SCR.

**Mapa de Empresas.** O painel do governo tem a contagem por UF, mas não tem arquivo nem API estável, e a ingestão não seria reprodutível.

**Base dos Dados.** Teria a contagem pronta no BigQuery, mas exige conta Google com credencial e é uma cópia mantida por terceiros. O espelho da Casa dos Dados também é de terceiros, mas entrega os arquivos originais, que podem ser conferidos contra a Receita, e não uma tabela já transformada.

**Contar estabelecimentos.** Mais simples, e errado para o SCR, pelo motivo da decisão 2.

## Consequências

**Positivas.**
- O indicador de espaço tem denominador mensal com cerca de 17 GB de download, e não 210 GB.
- O erro do método é um número publicado por UF, e não uma suposição: até 2,3% por UF e 0,2% no total do país, a dois anos de distância.
- O porte da Receita e o grupo de natureza jurídica ficam disponíveis, com aviso explícito de que o porte não equivale ao do SCR.

**Negativas, e são reais.**
- **O estoque de meses passados é aproximado.** No total do país o erro fica em 0,2% nas duas distâncias medidas, mas por UF ele cresce com a distância até o retrato: 1,35% a 15 meses e 2,3% a 27. O limite fica declarado na tela 4.
- **Porte e natureza jurídica são os de hoje** aplicados ao passado.
- **Depender de um espelho de terceiros** para o transporte. Se ele sair do ar ou divergir, a conferência contra a Receita pega a divergência, mas o download volta a depender do servidor oficial.
- **A escolha do denominador fica para a #26:** com ou sem MEI, e quais grupos de natureza jurídica. O fato guarda todas as combinações.
