# Cadeia normativa: por que o dado mudou

**Data:** 2026-09-21
**Objetivo:** explicar, com fonte oficial, as quebras que a análise empírica encontrou no SCR.data. A leitura das metodologias (`docs/leitura-normativos.md`) dizia *o que* mudou. Este documento desce um nível, até o leiaute e as instruções do documento 3040, para dizer *por que* mudou.

**Fontes lidas, além das metodologias:**

| Documento | O que traz | URL |
|---|---|---|
| Leiaute do documento 3040 (XLS) | Abas `Doc3040`, `Anexo` (inclui o Anexo 3, modalidades e submodalidades) e `HistoricoAtualizacoes` (87 entradas) | `bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/SCR3040_Leiaute.xls` |
| Instruções de preenchimento do documento 3040 (PDF, 138 páginas) | Regras de agregação, incluindo a ordem de prioridade da característica especial (p. 119) | `bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/SCR_InstrucoesDePreenchimento_Doc3040.pdf` |
| Equivalência de Modalidades (XLSX) | Abas `OutrasInformacoes` e `HistoricoAtualizacoes`, com as notas de rodapé das células | `bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/Equivalencia_Modalidades.xlsx` |

**Achado de método:** a metodologia do SCR.data aponta para o Anexo 3, e o Anexo 3 só se explica pelo histórico do leiaute. O significado de uma coluna está três documentos abaixo do arquivo que a contém.

---

## 1. A quebra do ativo problemático em janeiro de 2025

Na metodologia, o fim do critério antigo aparece entre parênteses, "(até dezembro/2024)": até dezembro de 2024 o critério combinava atraso, reestruturação e classificação de risco E a H; a partir de janeiro de 2025, vale só a característica especial 19. A metodologia não explica o motivo. O motivo está nesta sequência:

| Data | Evento | Fonte |
|---|---|---|
| 2017-05-10 | Criada a característica especial **19, "Ativo problemático"**. Existe desde então, sem uso nas agregações do SCR.data | Leiaute, `HistoricoAtualizacoes` |
| 2021 | **Resolução CMN 4.966**, novo marco contábil de instrumentos financeiros, com vigência em janeiro de 2025 | Resolução CMN 4.966/2021 |
| 2023-10-16 | Leiaute adaptado à 4.966. **Os Anexos 16 e 17 são excluídos.** Eram a classificação de risco do cliente (`ClassCli`) e da operação (`ClassOp`), ou seja, a escala E a H usada no critério antigo | Leiaute, `HistoricoAtualizacoes` |
| 2024-10-18 | **IN BCB 531** redefine a ordem de prioridade da característica especial na agregação, a partir de janeiro de 2025 | Instruções, p. 119 |
| 2024-12-06 | Leiaute atualiza os domínios do campo `CaractEspecial` da tag `Agreg` a partir da data-base de janeiro de 2025 | Leiaute, `HistoricoAtualizacoes` |
| 2025-01 | A metodologia do SCR.data passa a considerar só a característica 19 | Metodologia V2, seção 2.d |

O texto das instruções, na página 119, mostra a troca:

> "Característica especial: só agrega pela principal característica especial. Assume os valores "35", "11", "02", "01", "15", "99" e "18" (nessa ordem de prioridade). [...] A partir de janeiro/2025, a ordem de prioridade assume os valores "11", "19", "02", "01" e "99"."

**Leitura:** o valor 19 entrou na ordem de prioridade em janeiro de 2025, e os valores 35, 15 e 18 saíram. Antes disso, a característica 19 não participava da agregação e não podia ser critério de nada.

**Consequência para o projeto:** a quebra não é escolha editorial do BCB. O critério antigo dependia de uma classificação de risco que o novo marco contábil extinguiu, e a característica 19, criada em 2017, passou a ocupar o lugar. Comparar `ativo_problematico` entre dezembro de 2024 e janeiro de 2025 é comparar dois conceitos, e a causa é regulatória, não de publicação.

## 2. Outras alterações normativas dentro do recorte de 2024 em diante

| Norma | Vigência | O que mudou | Relação com o dado |
|---|---|---|---|
| IN BCB 627, 2025-05-29 | julho de 2025 | Leiaute e instruções sobre crédito de programas governamentais | Coincide com a queda de tamanho dos arquivos mensais da V1 em julho de 2025, de cerca de 320 MB para 273 MB. **Coincidência temporal, não causalidade verificada** |
| IN BCB 659, 2025-09-08 | a confirmar | Anexo 3: descrição do domínio 15 da modalidade e inclusão e exclusão de subdomínios | Explica parte da diferença de contagem de submodalidades (seção 3) |

## 3. Por que a planilha de equivalência tem 76 submodalidades e o dado tem 55

Três fatores, com graus de verificação diferentes:

1. **Escopo de modalidades.** O SCR.data usa apenas as modalidades 01 a 13 do Anexo 3, que vai além disso. A contagem de submodalidades nas modalidades 01 a 13 do Anexo 3 dá cerca de 75, compatível com as 76 da planilha. *Verificado por contagem no leiaute.*
2. **Descontinuações.** O Anexo 3 marca submodalidades como "descontinuado a partir da data-base maio/2026", e a IN 659 incluiu e excluiu subdomínios. *Verificado no leiaute.*
3. **Ausência de operação no mês.** Uma submodalidade vigente sem operação em junho de 2026 não gera linha. *Hipótese, ainda não medida submodalidade a submodalidade.*

**Pendente:** cruzar a lista das 76 com as 55 e atribuir cada uma das 21 ausentes a um dos três fatores. Até lá, a ontologia registra a explicação como parcial.

## 4. O rótulo "duplo" na planilha de equivalência não é erro

A aba `de-para_PJ - Tipo Origem 1` traz, numa célula mesclada (A9:A11), o texto `PJ - Capital de Giro Rotativo PJ - Cheque Especial e Conta Garantidaf`. A triagem inicial tratou isso como corrupção. **É renomeação**, e a planilha diz isso explicitamente:

> Nota "f", aba `OutrasInformacoes`, repetida em `HistoricoAtualizacoes` com data de 2022-03-08: "Alteração de nomenclatura da Modalidade PJ: de "PJ - Capital de Giro Rotativo" (tipo de origem: Recursos Livres)" para "PJ - Cheque Especial e Conta Garantida (tipo de origem: Recursos Livres)"."

**Verificação no dado:** nos 12 meses de 2025 da V1, só aparece o nome novo, "PJ - Cheque especial e conta garantida", com carteira ativa entre R$ 59,7 bi e R$ 64,4 bi. O nome antigo não aparece em nenhum mês.

O mesmo padrão existe no Anexo 3 do leiaute (`03 | Títulos descontados Direitos creditórios descontados`, com alteração de descrição registrada em 2016-07-12). **É a convenção do BCB para registrar renomeação: nome antigo e novo lado a lado na mesma célula.**

## 5. Regra de extração: notas de rodapé coladas ao texto

As chamadas de nota de rodapé da planilha de equivalência são sobrescritas no Excel, mas chegam como texto comum na leitura programática, grudadas ao rótulo:

| Texto lido | Rótulo real | Nota |
|---|---|---|
| `cheque especial e conta garantidaa1` | cheque especial e conta garantida | a1 |
| `cheque especiala2` | cheque especial | a2 |
| `capital de giro com teto rotativoc1` | capital de giro com teto rotativo | c1 |
| `PJ - ... Conta Garantidaf` | PJ - Cheque Especial e Conta Garantida | f |

**Regra:** a extração do seed de correspondência separa o sufixo de nota do rótulo e guarda a nota numa coluna própria. Sem isso, a chave de lookup não casa com o dado e a junção falha em silêncio.

As notas também são conteúdo útil para a ontologia, porque registram a história de cada submodalidade:

- **a1:** exclusão dos subdomínios 01 (cheque especial e conta garantida), 05 e 06 (capital de giro por prazo)
- **a2:** inclusão dos subdomínios 13 (cheque especial), 14 (conta garantida), 15 e 16 (capital de giro por prazo, nova faixa)
- **c1:** inclusão do subdomínio 17 (capital de giro com teto rotativo), a partir de maio de 2017

## 6. O que a quebra de janeiro de 2025 faz no dado

**Script:** `scripts/analises/quebra_ativo_problematico.py`, sobre a V1, que cobre 2023 a 2025 com a mesma taxonomia.

### O salto existe

| | dez/2024 | jan/2025 | Variação |
|---|---|---|---|
| Carteira ativa | R$ 6.397,9 bi | R$ 6.395,6 bi | 0,0% |
| Carteira inadimplida | R$ 195,4 bi | R$ 214,4 bi | **+9,7%** (+R$ 19,0 bi) |
| Ativo problemático | R$ 421,0 bi | R$ 452,6 bi | **+7,5%** (+R$ 31,6 bi) |
| Ativo problemático fora do atraso acima de 90 dias | R$ 225,7 bi | R$ 238,2 bi | +5,5% (+R$ 12,5 bi) |

Em 2024, a variação mensal do ativo problemático ficou entre -0,8% e +3,2%.

### Mas não pode ser atribuído só à mudança de definição

**A carteira inadimplida, cuja definição não mudou, subiu mais que o ativo problemático no mesmo mês.** O controle de sazonalidade não explica: na virada de dez/2023 para jan/2024, a carteira inadimplida subiu 2,4% e o ativo problemático, 0,5%. (É um único ano de controle, e a conclusão vale com essa limitação.)

**Explicação candidata, não confirmada:** a Instrução Normativa BCB 414, de 16/10/2023, alterou a descrição do campo "Valor dos Vencimentos" (`Venc`) do documento 3040 **a partir da data-base de janeiro de 2025**, a mesma data de vigência da Resolução CMN 4.966. É desse campo que saem as faixas de vencimento, e portanto a carteira inadimplida. O leiaute atual traz só a descrição nova e a norma não transcreve a antiga. A versão anterior do leiaute não foi localizada nesta leitura (Internet Archive fora do ar em 2026-09-21). **Pendente.**

### A decomposição por modalidade mostra a assinatura da mudança de definição

Onde o ativo problemático sobe muito mais que a inadimplência, a diferença vem de operações classificadas como problemáticas sem atraso acima de 90 dias, que é exatamente a parte que depende do critério:

| Modalidade | Variação da inadimplência | Variação do ativo problemático |
|---|---|---|
| PF - Habitacional | +R$ 1,4 bi | **+R$ 11,9 bi** (R$ 45,5 bi para R$ 57,5 bi, +26%) |
| PF - Empréstimo com consignação em folha | +R$ 1,1 bi | +R$ 5,8 bi |
| PJ - Financiamento de infraestrutura e projeto | +R$ 0,1 bi | +R$ 3,6 bi |
| PJ - Capital de giro | +R$ 2,5 bi | **-R$ 2,4 bi** |
| PJ - Outros créditos | +R$ 1,1 bi | **-R$ 3,4 bi** |

**Leitura:** o total líquido esconde movimentos em direções opostas. No crédito imobiliário e no consignado, as instituições classificam como problemático mais do que o algoritmo anterior do BCB classificava. Em capital de giro e em outros créditos PJ, classificam menos.

**Consequência:** a variação de janeiro de 2025 não pode ser lida como piora de crédito nem como efeito puro de definição. O dado mistura as duas coisas e não oferece meio de separá-las. Uma análise que compare dezembro com janeiro sem essa ressalva está errada, e o erro não gera nenhum sinal.

---

## Decisões registradas a partir desta leitura

| Item da triagem | Decisão | Quem decidiu |
|---|---|---|
| 1.1 Sentinela `-1` | Testar empiricamente, como artefato do projeto | Desenvolvedor |
| 1.2 "Outros créditos" | A regra continua valendo. O aviso saiu da V2 por estar implícito em agregações do tipo "outros", não por mudança de regra | Desenvolvedor, com base em conhecimento de domínio |
| 1.3 Recorte temporal | 2024 em diante | Desenvolvedor |
| 1.4 Anexo 3 | Buscado, e lido neste documento | Desenvolvedor |
| 3.1 Rótulo duplo | Renomeação, resolvido na seção 4 | Verificado na fonte e no dado |
| 3.2 76 contra 55 | Explicação parcial, seção 3, com pendência declarada | Verificado em parte |
