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

**Pista encontrada no próprio dado:** a V2 traz o label `Financiamentos rurais  (ex-financiamentos rurais e agroindustriais)`, ou seja, o BCB sinaliza renomeação dentro do próprio rótulo. Isso sugere que houve mudanças anteriores à quebra V1/V2 e que vale procurar no histórico normativo.

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
| `sr` (valores como `S1`) | *removida* | Provável classificação prudencial por segmento. **Confirmar no normativo** |
| `ocupacao`, `cnae_secao`, `cnae_subclasse` | `cnae_ocupacao` | Três colunas colapsadas em uma. **Perda de granularidade** |
| *inexistente* | `submodalidade` | Nova dimensão, 55 valores |

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

## Próximo passo

Estas correspondências são **hipóteses derivadas do dado**, não definições. Nenhuma delas entra na ontologia sem confirmação nos normativos oficiais (metodologia V1, metodologia V2 e tutorial), com citação da fonte e nível de confiança declarado.
