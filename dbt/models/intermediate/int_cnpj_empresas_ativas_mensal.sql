-- =============================================================================
-- PT: Estoque de matrizes ativas no fim de cada mês do SCR, por UF, porte da
--     Receita, grupo de natureza jurídica e condição de MEI no mês. É a
--     reconstrução do ADR 0009, feita por eventos em vez de cruzar cada
--     matriz com cada mês:
--
--     1. cada matriz vira até três trechos semiabertos [início, fim), o
--        trecho ativo dividido em antes, durante e depois do MEI, porque a
--        condição de MEI também muda com o tempo;
--     2. cada trecho gera +1 no fim do mês em que começa e -1 no fim do mês
--        em que termina;
--     3. o estoque de um fim de mês é a soma de todos os eventos até ele.
--
--     O +1 cai em last_day(início) porque esse é o primeiro fim de mês em que
--     início <= D. O -1 cai em last_day(fim) porque esse é o primeiro fim de
--     mês em que D >= fim, quando a empresa deixa de contar.
--
--     O porte e a natureza jurídica são os do retrato mais recente: a Receita
--     não publica o histórico deles, e a reconstrução os supõe constantes.
--
-- EN: Stock of active head offices at each SCR month end, by state, Receita
--     size, legal nature group and MEI status in the month. ADR 0009's
--     reconstruction, done with events: each head office becomes up to three
--     half-open segments (before, during and after MEI); each segment adds +1
--     at the month end where it starts and -1 at the month end where it ends;
--     a month end's stock is the running sum of events up to it. Size and
--     legal nature are the latest snapshot's, assumed constant.
-- =============================================================================

with intervalos as (

    select i.*
    from {{ ref('int_cnpj_matriz_intervalo') }} as i
    -- PT: Só as 27 UFs da ontologia. Sai o "EX", de estabelecimentos no
    --     exterior (ontology/fontes_externas.yml, uf_exterior_no_cnpj).
    -- EN: Only the ontology's 27 states; "EX" (abroad) is dropped.
    inner join {{ ref('ontologia_dimensao') }} as d
        on d.dimensao = 'uf' and d.valor = i.uf

),

-- -----------------------------------------------------------------------------
-- PT: Os três trechos. Em funções do Spark, least e greatest ignoram nulo, e
--     aqui fim nulo quer dizer "continua": least(fim nulo, x) = x é exatamente
--     o fim que se quer.
-- EN: The three segments. In Spark, least and greatest skip nulls, and a null
--     end here means ongoing, so least(null end, x) = x is the intended end.
-- -----------------------------------------------------------------------------
trechos as (

    -- PT: sem MEI, antes de virar MEI (ou o trecho todo, se nunca foi)
    -- EN: not MEI, before becoming one (or the whole segment if never)
    select
        uf, porte_empresa, grupo_natureza_juridica,
        false as mei,
        inicio_ativo as inicio,
        case when inicio_mei is null then fim_ativo else least(fim_ativo, inicio_mei) end as fim
    from intervalos

    union all

    -- PT: como MEI
    -- EN: as MEI
    select
        uf, porte_empresa, grupo_natureza_juridica,
        true as mei,
        greatest(inicio_ativo, inicio_mei) as inicio,
        least(fim_ativo, fim_mei) as fim
    from intervalos
    where inicio_mei is not null

    union all

    -- PT: sem MEI, depois de sair do MEI
    -- EN: not MEI, after leaving it
    select
        uf, porte_empresa, grupo_natureza_juridica,
        false as mei,
        greatest(inicio_ativo, fim_mei) as inicio,
        fim_ativo as fim
    from intervalos
    where fim_mei is not null

),

trechos_validos as (

    select * from trechos
    where fim is null or inicio < fim

),

eventos as (

    select last_day(inicio) as mes, uf, porte_empresa, grupo_natureza_juridica, mei, 1 as variacao
    from trechos_validos

    union all

    select last_day(fim) as mes, uf, porte_empresa, grupo_natureza_juridica, mei, -1 as variacao
    from trechos_validos
    where fim is not null

),

variacao_por_mes as (

    select mes, uf, porte_empresa, grupo_natureza_juridica, mei, sum(variacao) as variacao
    from eventos
    group by mes, uf, porte_empresa, grupo_natureza_juridica, mei

),

meses as (

    select distinct data_base from {{ ref('stg_scr_v2') }}

)

select
    m.data_base,
    v.uf,
    v.porte_empresa,
    v.grupo_natureza_juridica,
    v.mei,
    sum(v.variacao) as empresas_ativas
from meses as m
inner join variacao_por_mes as v
    on v.mes <= m.data_base
group by m.data_base, v.uf, v.porte_empresa, v.grupo_natureza_juridica, v.mei
-- PT: Grupo zerado some. Negativo seria erro de lógica, e não fica
--     escondido: o teste de valores positivos em _intermediate.yml o pega.
-- EN: Zeroed groups drop out. A negative would be a logic error, and the
--     positive-values test catches it instead of hiding it.
having sum(v.variacao) != 0
