-- PT: Q35. Crédito pessoal consignado (0202) com cliente pessoa jurídica: em
--     quantos meses aparece, entre quais datas, o tamanho, e a que modalidade
--     da V1 a tabela oficial de equivalência o atribui.
-- EN: Q35. Payroll-deducted personal loans (0202) with a corporate client:
--     months present, first and last month, size, and the V1 modality the
--     official equivalence table assigns.
with consignado_por_mes as (

    select
        data_base,
        sum(case when cliente = 'PJ' then carteira_ativa else 0 end) as carteira_pj,
        sum(carteira_ativa) as carteira_total
    from fct_carteira
    where codigo_submodalidade = '0202'
    group by data_base

),

pj as (

    select data_base, modalidade_v1_efetiva, carteira_ativa
    from fct_carteira
    where codigo_submodalidade = '0202'
      and cliente = 'PJ'

)

select
    pj.modalidade_v1_efetiva as modalidade_v1_atribuida,
    count(distinct pj.data_base) as meses_com_ocorrencia,
    count(*) as recortes,
    min(pj.data_base) as primeiro_mes,
    max(pj.data_base) as ultimo_mes,
    max(c.carteira_pj) as maior_carteira_mensal,
    100 * max(cast(c.carteira_pj as double) / cast(c.carteira_total as double))
        as maior_participacao_no_consignado_pct
from pj
join consignado_por_mes c
    on c.data_base = pj.data_base
group by pj.modalidade_v1_efetiva
