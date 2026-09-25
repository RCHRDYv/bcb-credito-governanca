-- PT: Q30, parte 2. A série no padrão antigo (V1) reconstruída a partir da
--     V2 pela tabela oficial de equivalência, contra a V1 publicada, por
--     modalidade da V1, no último mês. A diferença não é uniforme.
-- EN: Q30, part 2. The old-taxonomy (V1) series rebuilt from V2 through the
--     official equivalence table, against published V1, by V1 modality, in
--     the latest month. The gap is not uniform.
with ultimo as (

    select max(data_base) as data_base from fct_carteira

),

v2 as (

    select f.modalidade_v1_efetiva as modalidade_v1, sum(f.carteira_ativa) as carteira_v2_conformada
    from fct_carteira f
    join ultimo
        on f.data_base = ultimo.data_base
    group by f.modalidade_v1_efetiva

),

v1 as (

    select f.modalidade_v1, sum(f.carteira_ativa) as carteira_v1_publicada
    from fct_carteira_v1 f
    join ultimo
        on f.data_base = ultimo.data_base
    group by f.modalidade_v1

)

select
    coalesce(v1.modalidade_v1, v2.modalidade_v1) as modalidade_v1,
    v1.carteira_v1_publicada,
    v2.carteira_v2_conformada,
    100 * (cast(v2.carteira_v2_conformada as double) / cast(v1.carteira_v1_publicada as double) - 1)
        as diferenca_pct
from v1
full outer join v2
    on v2.modalidade_v1 = v1.modalidade_v1
order by diferenca_pct desc nulls last
