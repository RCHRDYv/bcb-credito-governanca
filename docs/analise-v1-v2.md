# Análise da quebra entre as Versões 1 e 2 do SCR.data

**Data da análise:** 2026-08-22
**Método:** comparação de taxonomia no **mesmo período de referência** (junho de 2025), em que as duas versões coexistem. Comparar o mesmo mês isola mudança de classificação de mudança real do mercado.

Esta análise é insumo direto do mapeamento XKOS (ver [ADR 0002](adr/0002-modelo-de-ontologia-skos-datacube-xkos.md)) e da pergunta Q30 do experimento.

## Resumo

| Dimensão | V1 | V2 | Veredito |
|---|---|---|---|
| **modalidade** | 16 | 13 | **Zero valores em comum.** Reclassificação conceitual completa |
| **porte** | 14 | 13 | Mesmas categorias, mas a V2 removeu o prefixo desambiguador |
| **tcb → segmento** | 3 | 8 | Ganho real de granularidade |
| **origem** | 2 | 2 | Idêntico |
| **indexador** | 6 | 6 | Idêntico |
| **cliente** | 2 | 2 | Idêntico |
| Granularidade (linhas/mês) | 1.025.243 | 322.852 | V1 tem 3,2x mais linhas |

## 1. Modalidade: reclassificação, não renomeação

**Não existe um único valor em comum entre as duas versões.** Isso não é ajuste de nomenclatura, é troca do eixo classificatório.

| | V1 | V2 |
|---|---|---|
| **Eixo** | Finalidade do crédito, do ponto de vista do cliente | Natureza contábil da operação |
| **Prefixo** | Sempre `PF -` ou `PJ -` | Nenhum |
| **Exemplos** | PF - Cartão de crédito, PF - Habitacional, PF - Veículos, PJ - Capital de giro, PJ - Cheque especial e conta garantida | Empréstimos, Financiamentos, Operações de arrendamento, Direitos creditórios descontados, Adiantamentos a depositantes |

**Consequência prática:** qualquer série histórica que atravesse junho de 2025 agrupando por `modalidade` soma categorias incomparáveis. A ruptura é total, não parcial.

**Hipótese a confirmar nos normativos:** a granularidade da V1 provavelmente foi absorvida pela nova dimensão `submodalidade` da V2, que tem 55 valores. Se confirmado, o mapeamento correto não é modalidade V1 para modalidade V2, e sim **modalidade V1 para submodalidade V2**, o que muda a natureza da correspondência XKOS.

> **Confirmada em 2026-09-22, e mais complexa que o previsto.** A tabela oficial de equivalência mapeia cada modalidade da V1 para um conjunto de submodalidades da V2, e a chave depende também do tipo de cliente e da origem dos recursos. A contagem certa é 66 submodalidades no recorte de 2024 a 2026, e não 55, que eram rótulos distintos num mês só. Há ainda dois limites: uma regra oficial que depende de um campo não publicado, e duas combinações que a tabela não cobre. Ver [ADR 0003](adr/0003-conformacao-de-taxonomia-entre-versoes.md) e o seed em `dbt/seeds/`.

**Pista encontrada no próprio dado:** a V2 traz o label `Financiamentos rurais  (ex-financiamentos rurais e agroindustriais)`, ou seja, o BCB sinaliza renomeação dentro do próprio rótulo. Isso sugere que houve mudanças anteriores à quebra V1/V2 e que vale procurar no histórico normativo.

> **Pista seguida em 2026-09-22.** A Carta-Circular 3.806/2017 renomeou a modalidade 08, de "Financiamentos rurais e agroindustriais" para "Financiamentos rurais", a partir de julho de 2017, e criou a submodalidade 0440 para o crédito agroindustrial, dentro de Financiamentos. O rótulo do dado ainda carrega o nome antigo entre parênteses, nove anos depois. Registrado em `ontology/modalidades.yml`, conceito `mod_08`.

## 2. Porte: a V2 introduziu ambiguidade que a V1 não tinha

A coluna `porte` mistura duas taxonomias distintas: porte de empresa para pessoa jurídica, e faixa de renda em salários mínimos para pessoa física.

**Na V1 isso era desambiguado por prefixo:**

```
PF - Acima de 20 salários mínimos
PJ - Grande
```

**Na V2 o prefixo foi removido:**

```
Acima de 20 salários mínimos
Grande
```

O resultado é que, na V2, agrupar por `porte` sem filtrar `cliente` mistura categorias incompatíveis, e nada no esquema avisa. **É uma regressão de qualidade semântica introduzida pela V2**, e é um caso claro de conhecimento que só a ontologia pode restituir.

**Detalhe de parsing:** os valores da V1 vêm com padding de espaços à direita (`'PJ - Grande                    '`), exigindo normalização com `strip`.

## 3. Segmento: ganho real de granularidade

| V1 (`tcb`, 3 valores) | V2 (`segmento`, 8 valores) |
|---|---|
| Bancário | Banco |
| Cooperativas | Cooperativa |
| Não bancário | Financeira, **Fintech**, **Instituição de pagamento**, Desenvolvimento/Fomento, Arrendamento, Outros |

A V2 desmembrou "Não bancário" em seis categorias, incluindo Fintech e Instituição de pagamento como classes próprias. Isso reflete a evolução do mercado e é diretamente relevante para as perguntas Q04 e Q21 do experimento, que tratam de ganho de participação de fintechs.

**Correspondência XKOS esperada:** `Bancário` e `Cooperativas` devem ter correspondência próxima ou exata. `Não bancário` deve ter correspondência **mais ampla** que cada uma das seis categorias novas.

## 4. Mudanças de esquema, além dos valores

### Dimensões

| V1 | V2 | Natureza |
|---|---|---|
| `tcb` | `segmento` | Renomeada e reclassificada |
| `sr` (valores como `S1`) | *removida* | **Confirmado em 2026-08-25:** é o Segmento da Resolução CMN 4.553/2017, classificação prudencial de S1 a S5 por porte e relevância internacional da instituição. Ver [leitura dos normativos](leitura-normativos.md), resposta 3 |
| `ocupacao`, `cnae_secao`, `cnae_subclasse` | `cnae_ocupacao` | Três colunas colapsadas em uma. **Perda de granularidade** |
| *inexistente* | `submodalidade` | Nova dimensão. Eram 55 rótulos distintos em junho de 2025; no recorte de 2024 a 2026 são 66 submodalidades, contadas por par com a modalidade |

### Medidas

| V1 | V2 | Natureza |
|---|---|---|
| `vencido_acima_de_15_dias` | `vencido_de_15_ate_90_dias` + `vencido_acima_de_90_dias` | Uma faixa dividida em duas. **Ganho** |
| *inexistente* | `carteira_a_vencer` | Novo agregado |
| *inexistente* | `carteira_vencida` | Novo agregado |
| `carteira_inadimplida_arrastada` | `carteira_inadimplencia` | **Renomeada, com o conceito de "arrastada" removido do nome** |

**O item mais crítico desta tabela é o último.** "Inadimplência arrastada" é um conceito específico: quando um cliente atrasa em uma operação, toda a exposição dele é arrastada para inadimplência. Se a V2 chama apenas de "inadimplência", há duas possibilidades, e elas têm consequências opostas:

1. O conceito é o mesmo e apenas o nome foi simplificado, caso em que a série é continuável
2. A definição mudou, caso em que a série **não** é continuável e ninguém que apenas olhe o nome da coluna perceberá

**Isso precisa ser resolvido no normativo antes de qualquer afirmação.** É o exemplo mais limpo de por que este projeto existe.

## 5. Discrepância entre documentação e dado publicado

O portal de dados abertos descreve a Versão 1 como disponível **apenas até junho de 2025** e não mais atualizada.

**O dado publicado contradiz isso:** o arquivo `planilha_2025.zip` contém os doze meses de 2025, de janeiro a dezembro.

Há, porém, uma quebra de volume observável exatamente no ponto indicado:

| Mês | Tamanho |
|---|---|
| jan a jun/2025 | 313 a 322 MB |
| jul a dez/2025 | 274 a 281 MB |

A queda de aproximadamente 15% a partir de julho sugere mudança de granularidade ou de escopo dentro da própria V1, e não descontinuação.

**Consequência para o projeto:** confiar na descrição do portal, sem verificar o dado, teria produzido um recorte temporal errado. Registrado como achado de governança, e como material adicional para a Q30.

**Atualização de 2026-09-21:** a V1 continua publicada. `planilha_2026.zip` traz de janeiro a julho de 2026. A queda de julho de 2025 aparece também na contagem de linhas, nas duas versões (V1 de 1.025.243 para 891.135, V2 de 322.852 para 308.209), e coincide com a vigência da IN BCB 627 (`docs/cadeia-normativa.md`, seção 2).

## 6. Os totais das duas versões não reconciliam

Verificado em 2026-09-21, sobre os 31 meses de janeiro de 2024 a julho de 2026 em que as duas versões coexistem, com o script de verificação da ingestão (`ingestion/verificar_bronze.py`).

**A carteira ativa da V2 é maior que a da V1 em todos os meses**, e a diferença não é pequena:

| Período | V2 acima da V1 | Exemplo |
|---|---|---|
| jan/2024 a ago/2025 | entre 3,95% e 4,88% | jan/2024: R$ 5.714,3 bi na V1, R$ 5.961,1 bi na V2 |
| set/2025 a jul/2026 | entre 5,41% e 5,94% | jul/2026: R$ 7.192,4 bi na V1, R$ 7.590,7 bi na V2 |

São cerca de R$ 250 a R$ 400 bilhões de diferença para a mesma medida, no mesmo mês, publicada pelo mesmo órgão. **O degrau de setembro de 2025 coincide com a IN BCB 659, de 08/09/2025**, que alterou domínios e subdomínios do Anexo 3 (modalidades). É coincidência temporal, não causa verificada.

**Consequências:**

1. **A conformação do ADR 0003 continua válida para a taxonomia, mas não para os totais.** Reconstruir a série "no padrão V1" a partir do dado V2 produz a classificação da V1 com o universo da V2, cerca de 4% a 6% maior que a V1 publicada. O ADR 0003 recebeu nota sobre isso.
2. **A V2 é a fonte de verdade do projeto.** A V1 fica como fonte legada, e toda comparação entre versões precisa declarar a diferença de universo.
3. **Causa ainda não identificada.** Hipóteses a testar: escopo de modalidades (a V1 pode excluir modalidades ou submodalidades que a V2 inclui), tratamento de "Outros créditos" e limiar de supressão. Pendente.

## 7. Julho de 2025: o mecanismo da queda, medido no staging

A seção 5 registrou que os arquivos e a contagem de linhas caem em julho de 2025 nas duas versões, e deixou a causa em aberto. Com a camada de staging pronta, o **mecanismo** pôde ser medido. Ele é diferente em cada versão, e em nenhuma delas é perda de dado.

### V1: a coluna `tcb` deixou de ser publicada

A quebra é limpa, não gradual:

| Período | Valores distintos em `tcb` | Linhas com `-` | Linhas no mês |
|---|---|---|---|
| jan/2024 a jun/2025, 18 meses | 3 | 0% | de 929.671 a 1.027.060 |
| jul/2025 a jul/2026, 13 meses | 0 | 100% | de 891.135 a 924.383 |

As 11.799.814 linhas com `-` em `tcb` estão **todas** depois da quebra, e nenhuma antes. É também o que explica a queda de 13% na contagem de linhas: perder uma dimensão de três valores funde recortes que antes eram distintos. Nenhuma outra dimensão, em nenhuma das duas versões, muda de cardinalidade em nenhum mês da série.

**Consequência prática:** qualquer série da V1 agrupada por `tcb` termina em junho de 2025. Um gráfico feito sem tratar isso mostra "Bancário" caindo a zero, o que não aconteceu: a carteira dessas instituições continua no dado, agregada. A correspondência com o `segmento` da V2, descrita na seção 3, só vale até jun/2025.

### V2: mesma carteira, menos recortes

A V2 não perdeu nenhuma dimensão nem nenhum valor de dimensão. Ela perdeu 4,5% dos recortes, e a perda se concentra nos segmentos menores:

| Segmento | Linhas, jun para jul | Carteira ativa, jun para jul | Carteira mediana por linha |
|---|---|---|---|
| Instituição de pagamento | -29,6% | +2,7% | R$ 71,3 mil para R$ 112,7 mil |
| Outros | -18,3% | +0,5% | R$ 82,0 mil para R$ 114,3 mil |
| Fintech | -11,4% | +3,8% | R$ 15,0 mil para R$ 15,3 mil |
| Banco | -3,4% | 0,0% | R$ 454,6 mil para R$ 435,7 mil |
| Arrendamento | +1,7% | +1,5% | estável |

A carteira ativa total da V2 sobe de R$ 6.923,4 bi para R$ 6.941,0 bi no mês da quebra, e o valor "Indisponível" de `porte` não cresce. **Nenhum real saiu da base: o mesmo dinheiro passou a ser publicado em menos linhas, maiores.**

### O que isso muda para o projeto

1. **Totais e percentuais atravessam julho de 2025.** Carteira, inadimplência e ativo problemático continuam comparáveis.
2. **Contagem de recortes e valor médio por recorte não atravessam.** Qualquer análise de concentração ou de "quantos recortes existem" mede mudança de publicação, não mudança de mercado.
3. **A causa continua não identificada.** A IN BCB 627, de 29/05/2025 e vigente em julho de 2025, coincide no tempo, mas trata de crédito de programas governamentais, e não de remoção de coluna nem de regra de agregação. Coincidência temporal, não causa verificada.
4. **É a terceira quebra datada da série**, ao lado de janeiro de 2025 (critério do ativo problemático) e setembro de 2025 (degrau na divergência entre versões). As três estão registradas na ontologia e nenhuma é visível no dado sem documentação.

## Próximo passo

Estas correspondências são **hipóteses derivadas do dado**, não definições. Nenhuma delas entra na ontologia sem confirmação nos normativos oficiais (metodologia V1, metodologia V2 e tutorial), com citação da fonte e nível de confiança declarado.
