-- PT: Views do esquema estrela no DuckDB, com os nomes de tabela do dbt
--     (#45, ADR 0027). O SQL do gabarito e do experimento roda sobre elas
--     sem mudar nada. Defina a base antes, local ou no Hugging Face, de
--     preferência na revisão fixada em esquema_estrela/manifesto.json:
--       set variable base = 'data/esquema_estrela';
--       set variable base = 'hf://datasets/vidayuri/bcb-credito-governanca@<revisao_hf>';
-- EN: Star schema views on DuckDB, with the dbt table names. Set the base
--     variable first, local or on Hugging Face, ideally at the revision
--     pinned in the manifest.
-- Gerado por scripts/exportar_esquema_estrela.py / generated, do not edit.

create or replace view dim_cnae_ocupacao as select * from read_parquet(getvariable('base') || '/data/dim_cnae_ocupacao.parquet');
create or replace view dim_modalidade as select * from read_parquet(getvariable('base') || '/data/dim_modalidade.parquet');
create or replace view dim_natureza_juridica as select * from read_parquet(getvariable('base') || '/data/dim_natureza_juridica.parquet');
create or replace view dim_porte as select * from read_parquet(getvariable('base') || '/data/dim_porte.parquet');
create or replace view dim_porte_receita as select * from read_parquet(getvariable('base') || '/data/dim_porte_receita.parquet');
create or replace view dim_segmento as select * from read_parquet(getvariable('base') || '/data/dim_segmento.parquet');
create or replace view dim_tempo as select * from read_parquet(getvariable('base') || '/data/dim_tempo.parquet');
create or replace view dim_uf as select * from read_parquet(getvariable('base') || '/data/dim_uf.parquet');
create or replace view fct_carteira as select * from read_parquet(getvariable('base') || '/data/fct_carteira.parquet');
create or replace view fct_carteira_v1 as select * from read_parquet(getvariable('base') || '/data/fct_carteira_v1.parquet');
create or replace view fct_empresas_ativas as select * from read_parquet(getvariable('base') || '/data/fct_empresas_ativas.parquet');
create or replace view fct_pix as select * from read_parquet(getvariable('base') || '/data/fct_pix.parquet');
create or replace view fct_populacao as select * from read_parquet(getvariable('base') || '/data/fct_populacao.parquet');
create or replace view fct_renda_do_trabalho as select * from read_parquet(getvariable('base') || '/data/fct_renda_do_trabalho.parquet');
create or replace view fct_selic as select * from read_parquet(getvariable('base') || '/data/fct_selic.parquet');
