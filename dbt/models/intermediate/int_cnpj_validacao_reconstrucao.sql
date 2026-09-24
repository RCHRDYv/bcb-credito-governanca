-- =============================================================================
-- PT: Mede o erro da reconstrução do estoque de empresas ativas (ADR 0009).
--
--     Para cada retrato baixado, compara duas contagens de matrizes ativas
--     por UF, na data de corte daquele retrato:
--     - real: contada no próprio retrato;
--     - reconstruída: calculada só com o retrato mais recente, pelos
--       intervalos de int_cnpj_matriz_intervalo.
--
--     A data de corte é a data mais recente que aparece no próprio retrato,
--     e não a do nome do arquivo. Medido em 2026-09-24: o retrato de set/2026
--     tem "D60912" no nome e 226 matrizes abertas em 13/09; o de jun/2025
--     também vai um dia além do nome. Comparar na data do nome deixaria essas
--     empresas de fora e criaria uma diferença que não é do método.
--
--     No retrato mais recente, as duas precisam ser iguais, por construção.
--     Esse zero prova que a implementação reproduz a regra, e não que o
--     passado está certo: o retrato que constrói é o mesmo que confere. O
--     passado é medido pelos retratos antigos, que são observações reais e
--     independentes, e a diferença neles é o erro medido da reconstrução.
--
-- EN: Measures the active-company stock reconstruction error. For each
--     downloaded snapshot, it compares, by state and on that snapshot's
--     cutoff date (the latest date present in it, which can be a day past the
--     one in the file name), the real count of active head offices with the count
--     rebuilt from the latest snapshot alone. In the latest snapshot both
--     must match by construction; in older ones, the gap is the error.
-- =============================================================================

with ufs as (

    select valor as uf from {{ ref('ontologia_dimensao') }} where dimensao = 'uf'

),

datas as (

    select
        retrato,
        max(greatest(data_inicio_atividade, data_situacao_cadastral)) as data_de_corte
    from {{ ref('stg_cnpj_estabelecimentos') }}
    group by retrato

),

real as (

    -- PT: Empresas distintas, pela mesma definição da reconstrução: uma
    --     empresa com duas matrizes ativas conta uma vez.
    -- EN: Distinct companies, same definition as the reconstruction.
    select e.retrato, d.data_de_corte, e.uf, count(distinct e.cnpj_basico) as empresas_ativas_real
    from {{ ref('stg_cnpj_estabelecimentos') }} as e
    inner join datas as d on d.retrato = e.retrato
    inner join ufs on ufs.uf = e.uf
    where e.identificador_matriz_filial = '1'
      and e.situacao_cadastral = '02'
    group by e.retrato, d.data_de_corte, e.uf

),

reconstruida as (

    select d.retrato, i.uf, count(*) as empresas_ativas_reconstruida
    from datas as d
    inner join {{ ref('int_cnpj_matriz_intervalo') }} as i
        on i.inicio_ativo <= d.data_de_corte
       and (i.fim_ativo is null or i.fim_ativo > d.data_de_corte)
    inner join ufs on ufs.uf = i.uf
    group by d.retrato, i.uf

)

select
    r.retrato,
    r.data_de_corte,
    r.uf,
    r.empresas_ativas_real,
    coalesce(c.empresas_ativas_reconstruida, 0) as empresas_ativas_reconstruida,
    coalesce(c.empresas_ativas_reconstruida, 0) - r.empresas_ativas_real as diferenca,
    (coalesce(c.empresas_ativas_reconstruida, 0) - r.empresas_ativas_real)
        / r.empresas_ativas_real as erro_relativo
from real as r
left join reconstruida as c
    on c.retrato = r.retrato and c.uf = r.uf
