-- PT: Q13, leitura pf. Correlação, entre as 27 UFs, do rendimento médio do
--     trabalho com a taxa de inadimplência da carteira de pessoa física. A
--     pergunta não diz o período, então vêm as duas janelas: 12 meses e o
--     recorte inteiro. Em cada janela, a taxa da UF é razão de somas e a
--     renda é a média dos meses, e cada mês usa o último trimestre da PNAD
--     encerrado até a data-base (ADR 0025).
-- EN: Q13, pf reading. Correlation across the 27 states between average
--     labor income and the individuals' default rate, over 12 months and over
--     the whole window. Each month uses the last PNAD quarter ended by its
--     reference date.
with limites as (

    select min(data_base) as primeiro, max(data_base) as ultimo from fct_carteira

),

trimestre_do_mes as (

    select m.data_base, max(r.fim_do_trimestre) as fim_do_trimestre
    from (select distinct data_base from fct_carteira) m
    join (select distinct fim_do_trimestre from fct_renda_do_trabalho) r
        on r.fim_do_trimestre <= m.data_base
    group by m.data_base

),

por_uf_e_mes as (

    select
        f.data_base,
        f.uf,
        sum(f.carteira_inadimplencia) as carteira_inadimplencia,
        sum(f.carteira_ativa) as carteira_ativa
    from fct_carteira f
    where f.cliente = 'PF'
    group by f.data_base, f.uf

),

com_renda as (

    select p.*, r.rendimento_medio, r.ano * 100 + r.trimestre as trimestre_da_renda
    from por_uf_e_mes p
    join trimestre_do_mes t
        on t.data_base = p.data_base
    join fct_renda_do_trabalho r
        on r.uf = p.uf and r.fim_do_trimestre = t.fim_do_trimestre

),

janelas as (

    select j.janela, j.ordem, c.*
    from (values ('12 meses', 1), ('recorte inteiro', 2)) as j(janela, ordem)
    cross join limites
    join com_renda c
        on c.data_base > case when j.ordem = 1 then last_day(limites.ultimo - interval '12' month)
                              else last_day(limites.primeiro - interval '1' month) end

),

por_uf as (

    select
        janela,
        ordem,
        uf,
        min(data_base) as primeiro_mes,
        max(data_base) as ultimo_mes,
        min(trimestre_da_renda) as primeiro_trimestre_da_renda,
        max(trimestre_da_renda) as ultimo_trimestre_da_renda,
        avg(cast(rendimento_medio as double)) as rendimento_medio,
        100 * cast(sum(carteira_inadimplencia) as double) / nullif(cast(sum(carteira_ativa) as double), 0)
            as taxa_inadimplencia_pct
    from janelas
    group by janela, ordem, uf

)

select
    janela,
    min(primeiro_mes) as primeiro_mes,
    max(ultimo_mes) as ultimo_mes,
    min(primeiro_trimestre_da_renda) as primeiro_trimestre_da_renda,
    max(ultimo_trimestre_da_renda) as ultimo_trimestre_da_renda,
    corr(rendimento_medio, taxa_inadimplencia_pct) as correlacao,
    count(rendimento_medio + taxa_inadimplencia_pct) as pares
from por_uf
group by janela, ordem
order by ordem
