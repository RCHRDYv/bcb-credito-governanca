# ADR 0014: A matriz de decisão compara cada UF com o país, em quatro quadrantes

**Status:** Aceito
**Data:** 2026-09-24

## Contexto

O ADR 0005 fez o projeto terminar numa recomendação: onde uma financeira deve crescer em crédito para pessoa jurídica e onde o risco pesa demais para isso, com a fronteira do dado declarada junto. A issue #26 transforma isso em regra. Faltavam três escolhas de método, e cada uma muda o resultado:

- qual número de empresas usar como denominador;
- que tamanho de célula é pequeno demais para dar um número confiável;
- o que conta como "espaço alto" e "risco piorando".

**Medido em 2026-09-24:**
- jul/2026 tem 309 células de UF × modalidade para pessoa jurídica, somando R$ 2,9 trilhões;
- 161 delas têm menos de R$ 1 bilhão, mas somam só 1,5% da carteira;
- duas modalidades existem em poucas UFs.

Sem corte, a matriz seria dominada por razões instáveis de células minúsculas.

## Decisões

As três primeiras foram tomadas pelo Yuri em 2026-09-24.

### 1. O denominador é empresa de natureza empresarial, sem MEI

O espaço é a carteira PJ da modalidade na UF dividida pelas empresas ativas da UF de natureza jurídica empresarial (grupo 2), sem MEI (`fct_empresas_ativas`, ADR 0009). É o público de quem uma financeira de crédito PJ quer crescer. Saem órgão público, entidade sem fins lucrativos e o MEI, que é cerca de metade das empresas ativas e toma pouco crédito.

**Só esse denominador,** sem versões de sensibilidade com os outros, para o escopo do projeto não crescer.

### 2. Corte de materialidade de R$ 1 bilhão por célula

Uma célula entra na matriz com carteira PJ de pelo menos R$ 1 bilhão. Em jul/2026 ficam 148 das 309 células, que somam 98,5% da carteira PJ. As menores continuam no mart, marcadas como "não avaliada", com o motivo, e a recomendação diz quantas são e quanto somam.

### 3. Os limiares são contra o país, na mesma modalidade

- **Espaço alto:** carteira por empresa abaixo da mediana das UFs, na mesma modalidade, entre as células acima do corte. A UF que é a própria mediana conta como espaço baixo, porque não está abaixo dela.
- **Risco piorando:** a taxa de inadimplência da célula subiu mais, em 6 meses, que a da mesma modalidade no país, com as duas taxas calculadas como razão de somas.

Cada UF é comparada com o país na mesma modalidade, sem nenhum número arbitrário escolhido pelo projeto.

### 4. Quatro quadrantes, e não três

| | Risco estável ou melhorando | Risco piorando |
|---|---|---|
| **Espaço alto** | **Entrar** | **Observar** |
| **Espaço baixo** | **Manter** | **Não entrar** |

O ADR 0005 falava em três destinos. O "observar" separa o caso em que o espaço existe mas o risco pesa, em vez de escondê-lo dentro de "não entrar": são decisões diferentes para uma financeira, porque uma diz "espere" e a outra diz "não".

### 5. O custo de errar vai nas duas direções, em reais

- **Deixar de entrar onde havia espaço:** (mediana − carteira por empresa) × empresas. É a carteira que faltaria para a UF chegar à mediana da modalidade.
- **Entrar onde o risco piora:** carteira × aumento da taxa de inadimplência em 6 meses. É a ordem de grandeza do aumento da carteira inadimplida atribuível à piora. **Não é perda:** o dado não tem recuperação nem taxa de juros.

### 6. O alerta antecipado fica fora do quadrante

A célula recebe o alerta quando a distância entre ativo problemático e carteira inadimplida abriu, em 6 meses, mais que a do país. É a piora que o atraso ainda não mostra (ADR 0005). Ele não muda o quadrante, para a regra principal continuar simples de ler. A janela de jan a jul/2026 não cruza a quebra de critério do ativo problemático de jan/2025.

### 7. Modalidade com poucas UFs acima do corte fica de fora

Com uma célula só acima do corte, ela é a própria mediana, e a comparação não mede nada. A modalidade precisa de pelo menos 3 UFs acima do corte. Em jul/2026 isso afeta uma célula, de R$ 1,55 bilhão, em "Financiamentos com interveniência". **É um parâmetro, e o valor 3 fica para revisão do Yuri.**

### Onde a regra mora

- **Mart:** `dbt/models/marts/mrt_decisao.sql`, mart de apresentação, que a IA do experimento não consulta (ADR 0007).
- **Parâmetros:** `vars` do `dbt/dbt_project.yml`, num lugar só.
- **Documento:** `docs/recomendacao.md`, gerado por `scripts/gerar_recomendacao.py`, sem nenhum número digitado à mão.

As razões da matriz são calculadas em ponto flutuante (`double`), e as somas continuam em decimal exato. A divisão entre decimais no Spark arredonda para 6 casas, e, multiplicada por uma carteira de centenas de bilhões, desviava o custo de errar em até centenas de milhares de reais. O QA independente pegou isso.

## Alternativas descartadas

**Todas as matrizes ativas como denominador, ou natureza empresarial com MEI.** O mapa passaria a refletir onde há mais MEI, e não onde há espaço para uma financeira de crédito PJ.

**Tercis de espaço e de risco.** Dão grupos de tamanho parecido, mas sempre põem um terço das células em "piorando", mesmo num período em que tudo melhora.

**Limiar fixo,** como risco piorando acima de 0,5 ponto em 6 meses. O número seria escolha do projeto e mudaria o resultado sem nada no dado que o justifique.

**Corte de R$ 100 milhões, ou nenhum corte.** Mais células, mas com razões instáveis, e células de poucos milhões poderiam cair em "entrar" ou "não entrar" por ruído.

**Custo de errar como perda esperada.** Exigiria taxa de recuperação e de juros, que o SCR.data não tem.

## Consequências

**Positivas.**
- A recomendação é reproduzível por SQL, e cada linha traz o número que a sustenta.
- O QA independente, em `scripts/analises/qa_decisao.py`, refaz a matriz a partir dos fatos e confere quadrante, custos e alerta em todas as células.

**Negativas, e são reais.**
- **A mediana muda quando as UFs mudam.** Uma UF pode mudar de quadrante sem mudar nada nela, só porque outras mudaram. É o preço de comparar com o país.
- **O denominador é reconstruído,** com erro medido de até 2,3% por UF (ADR 0009), e o porte e a natureza jurídica usados são os de hoje.
- **Sem projeção:** a v0.1 decide com o que aconteceu. A projeção de três meses (Q27) entra na v0.2, com a #27.
