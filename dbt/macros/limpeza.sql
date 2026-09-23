{# =============================================================================
   PT: Macros de limpeza do staging. Existem porque a mesma conversão se repete
       em quinze colunas de valor, nas duas versões do arquivo. Escrita à mão a
       cada coluna, uma divergência entre elas seria invisível: bastaria um
       `replace` esquecido para uma coluna virar nula em silêncio.

       Todas as conversões foram medidas antes de serem escritas, sobre os
       9.687.811 registros da V2 e os 29.471.540 da V1 (2026-09-23):
       - nenhuma medida usa separador de milhar, então trocar a vírgula por
         ponto basta e não há `.` a remover;
       - nenhuma medida passa de 12 dígitos inteiros e todas têm 2 casas
         decimais, o que torna decimal(18,2) folgado e exato;
       - os únicos valores não inteiros em `numero_de_operacoes` são os dois
         sentinelas, `-1` na V2 e `<= 15` na V1.

   EN: Staging cleaning macros. They exist because the same conversion repeats
       across fifteen value columns in two versions of the file. Hand-written
       per column, a divergence between them would be invisible: one forgotten
       `replace` would silently null out a column.

       Every conversion was measured before being written, over V2's 9,687,811
       records and V1's 29,471,540 (2026-09-23): no measure uses a thousands
       separator; none exceeds 12 integer digits and all have 2 decimal places;
       the only non-integer values in `numero_de_operacoes` are the two
       sentinels, `-1` in V2 and `<= 15` in V1.
   ============================================================================= #}


{# ---------------------------------------------------------------------------
   PT: Rótulo de dimensão. O trim não é cosmético: é o que torna o valor igual
       ao `rotulo_no_dado` da ontologia, que é a chave de junção. Na V2,
       `submodalidade` traz espaço à direita em 720.339 linhas, e na V1 todas
       as 29.471.540 linhas têm `porte` preenchido com espaços à direita.
   EN: Dimension label. The trim is not cosmetic: it is what makes the value
       equal the ontology's `rotulo_no_dado`, which is the join key. In V2,
       `submodalidade` carries a trailing space in 720,339 rows; in V1 every
       one of the 29,471,540 rows has a right-padded `porte`.
   --------------------------------------------------------------------------- #}
{% macro rotulo(coluna) %}trim({{ coluna }}){% endmacro %}


{# ---------------------------------------------------------------------------
   PT: Rótulo de dimensão da V1 que usa o marcador "-" onde a coluna não se
       aplica. O marcador não está documentado em nenhuma metodologia (ver
       ontology/dimensoes.yml, avisos_gerais.marcadores_nao_documentados_na_v1)
       e, mantido como texto, produz uma categoria fantasma em qualquer
       contagem de valores distintos. Aqui ele vira nulo, que é o que ele
       significa.
   EN: V1 dimension label that uses "-" where the column does not apply. The
       marker is undocumented in every methodology and, kept as text, produces
       a phantom category in any distinct-value count. Here it becomes null,
       which is what it means.
   --------------------------------------------------------------------------- #}
{% macro rotulo_sem_marcador(coluna) %}nullif(trim({{ coluna }}), '-'){% endmacro %}


{# ---------------------------------------------------------------------------
   PT: Valor monetário em reais. O arquivo usa vírgula decimal e o texto da V1
       vem com espaços. decimal, e não float: são valores contábeis que precisam
       somar exatamente, e os testes de identidade da carteira comparam somas.
   EN: Monetary value in reais. The file uses a decimal comma and V1 text comes
       padded. decimal, not float: these are accounting values that must add up
       exactly, and the portfolio identity tests compare sums.
   --------------------------------------------------------------------------- #}
{% macro valor_em_reais(coluna) %}cast(replace(trim({{ coluna }}), ',', '.') as decimal(18, 2)){% endmacro %}


{# ---------------------------------------------------------------------------
   PT: Data-base. Sempre o último dia do mês de referência, publicada como
       texto AAAA-MM-DD.
   EN: Reference date. Always the last day of the reference month, published as
       YYYY-MM-DD text.
   --------------------------------------------------------------------------- #}
{% macro data_de_referencia(coluna) %}to_date(trim({{ coluna }})){% endmacro %}


{# ---------------------------------------------------------------------------
   PT: Contagem de operações com o sentinela de supressão convertido em nulo.
       O `nullif` vem antes do cast de propósito: com o sentinela fora, o cast
       é estrito e qualquer valor inesperado faz o modelo falhar em vez de
       virar nulo escondido. É o comportamento desejado, porque um sentinela
       novo é exatamente o tipo de mudança que precisa ser vista.
   EN: Operation count with the suppression sentinel turned into null. The
       `nullif` comes before the cast on purpose: with the sentinel removed the
       cast is strict, and any unexpected value fails the model instead of
       becoming a hidden null. That is the desired behaviour, because a new
       sentinel is exactly the kind of change that needs to be seen.
   --------------------------------------------------------------------------- #}
{% macro contagem_sem_sentinela(coluna, sentinela) %}cast(nullif(trim({{ coluna }}), '{{ sentinela }}') as bigint){% endmacro %}
