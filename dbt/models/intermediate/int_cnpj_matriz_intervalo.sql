-- =============================================================================
-- PT: Uma linha por matriz do retrato mais recente do CNPJ, com o intervalo
--     em que ela esteve ativa e o intervalo em que foi MEI. É a base da
--     reconstrução do estoque mensal de empresas ativas (ADR 0009).
--
--     Intervalos são semiabertos, [início, fim): a empresa conta como ativa
--     num dia D se início <= D < fim, e fim nulo quer dizer que continua.
--
--     O intervalo ativo sai da situação atual e da data da última mudança:
--     - ativa hoje: ativa desde a data mais recente entre o início da
--       atividade e a última mudança de situação, e continua;
--     - não ativa hoje: ativa do início da atividade até a data da mudança.
--       Sem data de mudança, não há como situar a saída, e a matriz fica fora
--       da reconstrução. É o caso de sem_data_de_saida, contado no QA.
--
--     Empresa é o CNPJ básico, e a tabela tem uma linha por empresa. Dois
--     defeitos do dado publicado são tratados aqui, medidos em 2026-09-24:
--     - uma empresa (08314885) tem duas matrizes ativas em set/2026, e três
--       em jun/2025. Fica a ativa mais antiga, e a empresa conta uma vez;
--     - a mesma empresa aparece duas vezes na tabela Empresas, uma linha
--       completa e outra vazia, com natureza 0000. Fica a completa.
--
--     Tabela, e não view: dois modelos a consomem, e ela junta as três
--     tabelas grandes do CNPJ.
--
-- EN: One row per head office in the latest CNPJ snapshot, with the interval
--     in which it was active and the interval in which it was an MEI. Base of
--     the monthly active-company stock reconstruction (ADR 0009). Intervals
--     are half-open [start, end), and a null end means ongoing. Active today:
--     active since the later of activity start and last status change.
--     Not active today: active from activity start until the status change;
--     without that date the exit cannot be placed and the head office is
--     left out. Materialized as a table because two models consume it.
-- =============================================================================

{{ config(materialized='table') }}

with retrato_do_modelo as (

    -- PT: Empresas e Simples só existem no retrato do modelo, então é ele.
    -- EN: Companies and Simples only exist in the model's snapshot.
    select max(retrato) as retrato from {{ ref('stg_cnpj_empresas') }}

),

primeiro_mes as (

    select min(data_base) as data_base from {{ ref('stg_scr_v2') }}

),

matrizes_publicadas as (

    select
        e.cnpj_basico,
        e.cnpj_ordem,
        e.uf,
        e.situacao_cadastral,
        e.data_situacao_cadastral,
        e.data_inicio_atividade,
        e.data_extracao
    from {{ ref('stg_cnpj_estabelecimentos') }} as e
    inner join retrato_do_modelo as r
        on e.retrato = r.retrato
    where e.identificador_matriz_filial = '1'

),

matrizes as (

    -- PT: Uma matriz por empresa: a ativa, e entre ativas a mais antiga.
    -- EN: One head office per company: the active one, the oldest if several.
    select * except (ordem)
    from (
        select
            *,
            row_number() over (
                partition by cnpj_basico
                order by situacao_cadastral = '02' desc, data_inicio_atividade, cnpj_ordem
            ) as ordem
        from matrizes_publicadas
    )
    where ordem = 1

),

empresas as (

    -- PT: Uma linha por empresa: a completa, se houver uma vazia repetida.
    -- EN: One row per company: the complete one, if an empty one repeats.
    select * except (ordem)
    from (
        select
            *,
            row_number() over (
                partition by cnpj_basico
                order by natureza_juridica = '0000', natureza_juridica
            ) as ordem
        from {{ ref('stg_cnpj_empresas') }}
    )
    where ordem = 1

),

intervalos as (

    select
        *,
        case
            when situacao_cadastral = '02'
                then greatest(data_inicio_atividade, data_situacao_cadastral)
            else data_inicio_atividade
        end as inicio_ativo,
        case
            when situacao_cadastral = '02' then null
            else data_situacao_cadastral
        end as fim_ativo,
        situacao_cadastral != '02' and data_situacao_cadastral is null as sem_data_de_saida
    from matrizes

)

select
    i.cnpj_basico,
    i.uf,
    i.situacao_cadastral,
    i.data_extracao,
    i.inicio_ativo,
    i.fim_ativo,
    i.sem_data_de_saida,

    -- PT: Porte em branco vira nulo. Branco não é o código 00 ("não
    --     informado") do leiaute, e tratá-lo como 00 afirmaria o que o dado
    --     não diz. Em set/2026 são 5 empresas ativas, as mesmas que têm
    --     natureza 0000, o código de domínio da Receita para "não informada".
    -- EN: A blank size becomes null: blank is not the layout's "00" code.
    nullif(emp.porte_empresa, '') as porte_empresa,
    left(emp.natureza_juridica, 1) as grupo_natureza_juridica,

    -- PT: Intervalo MEI. Com opção "S", a saída costuma ser nula e o
    --     intervalo continua. Com opção "N", a empresa já saiu, e sem data de
    --     saída o intervalo fica vazio, em vez de ser tratado como MEI até hoje.
    -- EN: MEI interval. With option "S" the exit is usually null and the
    --     interval continues. With "N" the company already left; without an
    --     exit date the interval is empty rather than MEI until today.
    s.data_opcao_mei as inicio_mei,
    case
        when s.opcao_mei = 'S' then s.data_exclusao_mei
        else coalesce(s.data_exclusao_mei, s.data_opcao_mei)
    end as fim_mei

from intervalos as i
cross join primeiro_mes as p
left join empresas as emp
    on emp.cnpj_basico = i.cnpj_basico
left join {{ ref('stg_cnpj_simples') }} as s
    on s.cnpj_basico = i.cnpj_basico

-- PT: Fica fora o que não tem como estar ativo em nenhum mês do SCR. Uma
--     matriz que deixou de ser ativa antes do primeiro fim de mês soma +1 e
--     -1 antes dele, e não muda nenhum estoque: tirá-la não altera o
--     resultado e poupa a maior parte das linhas.
-- EN: Excluded: what cannot be active in any SCR month. A head office that
--     stopped being active before the first month end adds +1 and -1 before
--     it and changes no stock: removing it does not alter the result.
where i.inicio_ativo is not null
  and not i.sem_data_de_saida
  and (i.fim_ativo is null or i.fim_ativo > p.data_base)
  and (i.fim_ativo is null or i.fim_ativo > i.inicio_ativo)
