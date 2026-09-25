-- PT: Q40. Parcela da carteira cuja modalidade da V1 não sai com certeza da
--     tabela oficial de equivalência: a ambígua, que depende do campo
--     Natureza da operação, não publicado, e a inferida pelo projeto, para
--     combinações que a tabela não cobre. Vêm o último mês e o recorte
--     inteiro.
-- EN: Q40. Portfolio share whose V1 modality is not certain from the official
--     equivalence table: ambiguous (depends on the unpublished Natureza field)
--     and inferred by the project (combinations the table does not cover).
with ultimo as (

    select max(data_base) as data_base from fct_carteira

)

select
    100 * cast(sum(case when f.data_base = ultimo.data_base and f.origem_da_modalidade_v1 = 'oficial_ambigua'
                        then f.carteira_ativa else 0 end) as double)
        / cast(sum(case when f.data_base = ultimo.data_base then f.carteira_ativa else 0 end) as double)
        as ambigua_no_ultimo_mes_pct,
    100 * cast(sum(case when f.data_base = ultimo.data_base and f.origem_da_modalidade_v1 = 'inferida_pelo_projeto'
                        then f.carteira_ativa else 0 end) as double)
        / cast(sum(case when f.data_base = ultimo.data_base then f.carteira_ativa else 0 end) as double)
        as inferida_no_ultimo_mes_pct,
    100 * cast(sum(case when f.origem_da_modalidade_v1 = 'oficial_ambigua' then f.carteira_ativa else 0 end) as double)
        / cast(sum(f.carteira_ativa) as double) as ambigua_no_recorte_pct,
    100 * cast(sum(case when f.origem_da_modalidade_v1 = 'inferida_pelo_projeto' then f.carteira_ativa else 0 end) as double)
        / cast(sum(f.carteira_ativa) as double) as inferida_no_recorte_pct,
    sum(case when f.origem_da_modalidade_v1 = 'oficial_ambigua' then 1 else 0 end) as linhas_ambiguas_no_recorte
from fct_carteira f
cross join ultimo
