# ADR 0025: A renda por UF é a do trabalho, da PNAD Contínua, nominal e pelo último trimestre encerrado

**Status:** Aceito
**Data:** 2026-10-07

## Contexto

A Q13 cruza a renda média por UF com a inadimplência, e a Q15 cruza a carteira de pessoa física com a massa salarial da UF (issue #38). O SCR não traz renda, e a #47, o pré-registro, só congela o gabarito com as duas preenchidas.

"Renda por UF" não é um número só:
- **A PNAD Contínua trimestral** publica o rendimento médio e a massa de rendimento do trabalho por UF. Sai cerca de 45 dias depois do fim do trimestre, com o valor real e o nominal.
- **A PNAD anual** publica o rendimento domiciliar per capita, que inclui aposentadoria e programas sociais. Sai com um ano de defasagem: em 2026-10-07, o último ano era 2025.
- **O valor "real"** das tabelas trimestrais é deflacionado a preços do último trimestre. O IBGE refaz a série inteira a cada divulgação. No RJ, a massa do 1º trimestre de 2024 era R$ 32.342 mi em valor real e R$ 29.297 mi em nominal. No 2º trimestre de 2026, os dois coincidiam.

E o SCR é mensal: o mês mais recente, jul/2026, está num trimestre que só sai em novembro.

## Decisão

Decisões do Yuri, em 2026-10-07:

1. **A renda é a do trabalho, da PNAD Contínua trimestral.**
   - O rendimento médio vem da tabela 6472 (variável 5929) e é a "renda média" da Q13.
   - A massa de rendimento vem da tabela 6474 (variável 6288) e é a "massa salarial" da Q15.
   - As duas medem o que é habitualmente recebido em todos os trabalhos pelas pessoas de 14 anos ou mais ocupadas.
   - O coeficiente de variação entra junto (5937 e 6289).
2. **O valor é o nominal,** como o do SCR. O real mudaria a cada trimestre, o sha256 da ingestão mudaria sem nenhuma revisão de fato, e o gabarito congelado deixaria de bater.
3. **Cada mês do SCR usa o último trimestre encerrado até a data-base,** no mesmo espírito da Selic (ADR 0010). A resposta diz qual trimestre usou. Jul/2026 usa o 2º trimestre de 2026. O mês que fecha o trimestre usa o próprio trimestre, que termina na data-base: mar/2024 usa o 1º trimestre de 2024.
4. **A Q13 tem duas leituras aceitas:** a inadimplência da carteira de pessoa física e a da carteira inteira.
5. **Na Q15, a UF sugere sobre-endividamento** quando a razão carteira PF por massa de rendimento fica acima da mesma razão no Brasil. A razão do Brasil é a soma das carteiras sobre a soma das massas das 27 UFs.

**A busca parte dos dados que o projeto já tem.** Ela vai do 4º trimestre de 2023, que serve jan e fev/2024, até o último publicado, e não traz o histórico desde 2012. O primeiro trimestre vem do primeiro ano do SCR em `ingestion/fontes.py`. Os trimestres vão numa lista explícita, porque o SIDRA ignora em silêncio um período que ainda não saiu.

## Alternativas descartadas

**Renda domiciliar per capita (tabela 7395), sozinha ou como segunda leitura.** É o conceito mais amplo de renda, mas é anual e não tem 2026. A segunda leitura custaria mais uma tabela, e o limite de três leituras do ADR 0015 já vai com as duas da inadimplência.

**Valor real.** Pelo motivo da decisão 2.

**O trimestre do próprio mês.** O mês mais recente do dado, e às vezes os dois anteriores, ficariam sem renda. O "último mês" da Q15 viraria outro mês, diferente do das outras perguntas.

**Espalhar o trimestre pelos meses no fato.** O fato fica no grão que o IBGE publica, como a população. A junção com o mês fica no SQL, pela coluna `fim_do_trimestre`.

## Consequências

**Positivas.**
- Q13 e Q15 passam a ser respondíveis, e as 41 perguntas ficam com gabarito. A #47 fica destravada.
- `ingestion/baixar_ibge.py` passa a ler uma lista de tabelas do SIDRA. Uma tabela nova é uma linha em `TABELAS_SIDRA`.
- O manifesto distingue trimestre novo de revisão do IBGE.

**Negativas, e são reais.**
- **A renda do trabalho subestima a renda disponível** onde aposentadoria e transferências pesam mais. A ontologia registra isso como aviso, e a resposta precisa dizer qual renda usou.
- **Vinte e sete pares são poucos para uma correlação,** e a PNAD é imprecisa nas UFs pequenas: o CV do rendimento vai de 1,5% em SC a 6,8% em RR.
- **O critério da Q15 é relativo à média do país,** então perto de metade das UFs fica acima por construção. No gabarito de 2026-07-31 foram 14 das 27, duas delas (AP e PI) a menos de 1% da razão nacional. A regra de comparação da #47 decide como tratar valor perto do limiar.
- **A cada trimestre publicado, o arquivo e o sha256 mudam.** O gabarito congelado fica no trimestre da data de referência dele.
