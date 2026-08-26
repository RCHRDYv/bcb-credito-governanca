# Leitura dos normativos: o que os documentos oficiais respondem

**Data:** 2026-08-25
**Fontes lidas:**

| Documento | Páginas | URL |
|---|---|---|
| Metodologia do SCR.data, Versão 2 | 7 | `bcb.gov.br/pda/desig/metodologia_versao2.pdf` |
| Metodologia do SCR.data, Versão 1 | 8 | `bcb.gov.br/content/estabilidadefinanceira/scr/scr.data/scr_data_metodologia.pdf` |
| Tutorial | 3 | `bcb.gov.br/content/estabilidadefinanceira/scr/scr.data/tutorial.pdf` |
| **Equivalência de Modalidades** (XLSX) | 5 abas | `bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/Equivalencia_Modalidades.xlsx` |

**Nota sobre o tutorial:** apesar de listado como recurso do dataset no portal, ele não contém nenhuma definição de conceito. São 810 caracteres explicando como clicar em botões do painel. Não serve como fonte para a ontologia.

---

## As cinco perguntas abertas, respondidas

### 1. `carteira_inadimplida_arrastada` (V1) e `carteira_inadimplencia` (V2) são o mesmo conceito?

**Sim. As definições são textualmente idênticas.**

> **V1, item 4.u, "Carteira inadimplida arrastada":** "Somatório das operações de crédito a vencer e vencidos que possuam alguma parcela vencida há mais de 90 dias."

> **V2, item 3.x, "Carteira inadimplida (carteira_inadimplencia)":** "Somatório das operações de crédito a vencer e vencidas que possuam alguma parcela vencida há mais de 90 dias."

A única diferença é concordância verbal. O mecanismo de "arrastar" continua descrito com exatidão: **a operação inteira entra, incluindo a parte a vencer, quando qualquer parcela passa de 90 dias.**

**Consequência:** a série é continuável entre V1 e V2 para esta métrica. E é um caso instrutivo de **mudança de rótulo sem mudança de definição**, ou seja, o inverso do que a suspeita inicial apontava. Quem olhasse só o nome concluiria erradamente que houve ruptura.

**Correspondência XKOS:** exata.

### 2. As modalidades da V1 viraram submodalidades na V2?

**Não exatamente, e a realidade é mais complexa.**

> **V1, item 3.c:** "As modalidades apresentadas no relatório representam **uma agregação das submodalidades** disponíveis no Anexo 3 do Leiaute do SCR"

> **V2, item 3.h:** "As modalidades apresentadas no relatório representam **as modalidades definidas no Anexo 3** do Leiaute do SCR"

A V1 criava um **nível intermediário próprio do relatório**, agrupando submodalidades oficiais por produto e por tipo de cliente. A V2 abandonou esse nível e passou a expor a hierarquia oficial do Anexo 3 diretamente, em dois níveis.

**A correspondência é muitos-para-muitos e atravessa categorias.** Exemplo extraído da planilha oficial: "PF - Cartão de Crédito" da V1 corresponde a submodalidades distribuídas por **três modalidades diferentes** da V2:

| Modalidade V2 | Submodalidades |
|---|---|
| 02 Empréstimos | 04 (crédito rotativo vinculado a cartão), 10 (compra/fatura parcelada), 18 (não migrado) |
| 04 Financiamentos | 06 (compra ou fatura parcelada) |
| 13 Outros Créditos | 04 (compra à vista e parcelada) |

**E a correspondência depende de uma dimensão adicional:** para pessoa jurídica, o mapeamento muda conforme o **Tipo de Origem** (1 = recursos livres, 2 = recursos direcionados). A planilha tem abas separadas para cada caso.

Isso significa que o mapeamento correto não é `modalidade → submodalidade`, e sim `modalidade_v1 × origem → conjunto de (modalidade_v2, submodalidade_v2)`.

### 3. O que era a coluna `sr`, removida na V2?

> **V1, item 4.b:** "SR (Segmento Resolução nº 4.553/2017)"

Classificação prudencial das instituições financeiras em cinco níveis (S1 a S5), definida por porte medido como Exposição sobre PIB e por relevância de atividade internacional. S1 são as maiores (acima de 10% do PIB ou ativos no exterior acima de US$ 10 bilhões), S5 as menores com metodologia simplificada.

A coluna `tcb` da V1 era "Tipo de Consolidado Bancário", agrupando B1, B2 e B4 em "Bancário", N1, N2 e N4 em "Não Bancário", e B3S e B3C em "Cooperativas".

### 4. O sentinela `-1` em `numero_de_operacoes` é supressão por sigilo?

**Sim, por inferência forte, mas a V2 não documenta.**

> **V1, item 4.l:** "Representa o número de operações de crédito para uma dada série. **Casos em que o número de operações seja inferior ou igual a 15, a informação divulgada será '<= 15'.**"

> **V2, item 3.l:** "Representa o número de operações de crédito para um dado recorte de dados."

A V1 documentava a supressão e usava um rótulo legível. **A V2 usa o código `-1` e removeu a explicação.**

**Esta é a segunda regressão de qualidade semântica identificada na V2**, ao lado da remoção do prefixo PF/PJ da coluna `porte`.

**Nível de confiança:** `inferido`. O limiar de 15 operações e o significado de supressão vêm da V1 por continuidade, não de declaração da V2.

### 5. Quais modalidades têm garantia real?

**Lacuna. Nenhum dos dois documentos responde.**

Ambos remetem ao Anexo 3 do Leiaute do documento 3040, que é um nível de documentação abaixo. A pergunta Q17 do experimento depende disso e exige descer mais um degrau.

**Achado de método:** o PDF de metodologia é, ele próprio, um ponteiro para outro documento. O significado não está a uma consulta de distância, está a duas.

---

## Achados que não estavam nas perguntas

### A. Quebra de definição no ativo problemático em janeiro de 2025

Ambas as versões documentam, e é uma ruptura **dentro da métrica**, independente da quebra V1/V2:

> **V2, item 2.d:** "...classificando-o entre os níveis de risco E e H **(até dezembro/2024)**. [...] **A partir de janeiro/2025 são consideradas somente as operações de crédito classificadas pelas instituições financeiras como ativos problemáticos (característica especial 19).**"

**Até dez/2024:** o BCB aplicava critério próprio, combinando atraso acima de 90 dias, reestruturação identificada por algoritmo interno, e classificação de risco E a H.

**A partir de jan/2025:** vale apenas o que a própria instituição financeira classificou como ativo problemático.

**Consequência:** quem compara `ativo_problematico` entre dezembro de 2024 e janeiro de 2025 está comparando definições diferentes. A mudança é invisível no dado e só aparece em uma frase entre parênteses no PDF.

### B. A mesma palavra significa razão numa seção e soma em outra

No **mesmo documento**, nas duas versões:

> **Seção 2.c, Inadimplência:** "Calcula-se pela **divisão** do valor da carteira das operações com alguma parcela em atraso acima de 90 dias **pelo** valor da carteira de todas as operações." (é uma razão)

> **Seção 3.x, `carteira_inadimplencia`:** "**Somatório** das operações de crédito a vencer e vencidas que possuam alguma parcela vencida há mais de 90 dias." (é um valor absoluto)

O conceito "inadimplência" é um percentual. A coluna `carteira_inadimplencia` é um valor em reais. Quem lê a seção de conceitos e aplica à coluna erra por três ordens de grandeza.

### C. A advertência sobre "Outros Créditos" desapareceu na V2

> **V1, introdução:** "quando em alguma agregação o número de operações é muito baixo, ele é agrupado na modalidade **'Outros Créditos'**. Assim, a soma do total do arquivo por modalidade **não representa necessariamente o total daquela modalidade no Sistema Financeiro**."

**Esse aviso não existe na V2.**

Se a regra continua valendo, e não há indicação de que tenha mudado, então "Outros créditos" é parcialmente um **balde de supressão**, e não uma categoria de negócio. Na V2 essa modalidade representa **10,42% da carteira ativa**, e quem usa a V2 não recebe o aviso.

**Este é possivelmente o achado mais consequente da leitura**, porque afeta qualquer análise por modalidade e não é sinalizado em lugar nenhum da documentação vigente.

### D. Há quebras de taxonomia anteriores, por Carta Circular

A aba `OutrasInformacoes` da planilha de equivalência documenta alterações de subdomínio determinadas por:

- Carta Circular 3.617/2013
- Carta Circular 3.773/2016
- Carta Circular 3.806/2017
- Carta Circular 3.817/2017

Cada uma incluiu, excluiu ou renomeou submodalidades. **A série histórica tem múltiplas descontinuidades, não uma.**

A aba `HistoricoAtualizacoes` mostra que a própria tabela de equivalência tem versionamento próprio: publicação original em 01/10/2021 e alteração de nomenclatura em 08/03/2022.

### E. Perda de granularidade no CNAE, com regra de supressão

> **V1, item 4.h:** o CNAE era disponibilizado em **duas colunas** (Seção e Subclasse), com subclasse de 7 dígitos apenas quando a combinação CNAE Subclasse × UF × Porte tivesse **mais de 5 CNPJs** no cadastro da Receita Federal. Abaixo disso, reportava só a Seção.

> **V2, item 3.e:** uma coluna só, preenchida com a **Seção** (primeiro nível).

### F. Confirmação: `cnae_ocupacao` é polimórfica, como `porte`

> **V2, itens 3.e e 3.f:** para pessoa jurídica o campo traz o CNAE. Para pessoa física, traz a natureza da ocupação.

**Mesma coluna, duas taxonomias, decididas pelo valor de `cliente`.** É o mesmo padrão já identificado em `porte`, e agora confirmado no normativo.

Na V1 as naturezas de ocupação vinham prefixadas com "PF - ", o que desambiguava. Na V2 o prefixo foi removido, exatamente como aconteceu com `porte`. **Terceira regressão de qualidade semântica na V2.**

### G. Detalhe semântico da dimensão geográfica

> **Ambas as versões:** "A informação segregada por unidades da federação é baseada no **CEP de residência das pessoas físicas ou da Sede das pessoas jurídicas**."

UF não é onde o crédito foi tomado nem onde a atividade acontece. É onde a pessoa mora ou onde a empresa tem sede. Uma empresa sediada em São Paulo com operação na Bahia conta como São Paulo.

Isso afeta diretamente as perguntas Q11 a Q15 do experimento, que tratam de distribuição geográfica.

### H. Limiar de valor mudou em junho de 2016

> **Ambas as versões:** operações de valor superior a **R$ 1.000 até maio/2016**, e superior a **R$ 200 a partir de junho/2016**.

Mais uma descontinuidade histórica, anterior a todas as outras.

---

## Consequências para a construção da ontologia

**O que ficou mais fácil:** existe tabela de equivalência oficial. A correspondência V1 para V2 não precisa ser inferida, e sim transcrita e estruturada.

**O que ficou mais difícil:** a correspondência é muitos-para-muitos e depende de `origem`, o que exige um modelo mais rico que uma correspondência simples entre conceitos.

**O que a ontologia precisa registrar e o dado não carrega:**

1. A polimorfia de `porte` e de `cnae_ocupacao` conforme `cliente`
2. O significado do sentinela `-1`, marcado como inferido
3. Que "Outros créditos" acumula supressão e não é categoria pura
4. A quebra de janeiro de 2025 no ativo problemático
5. A distinção entre inadimplência como razão e `carteira_inadimplencia` como soma
6. Que UF é domicílio ou sede, não local da operação
7. As descontinuidades por Carta Circular e o limiar de junho de 2016

**Nível de confiança das definições coletadas:** as sete listadas acima são `verbatim` ou `parafraseado`, com exceção do item 2, que é `inferido`, e da questão de garantia real, que permanece `lacuna`.
