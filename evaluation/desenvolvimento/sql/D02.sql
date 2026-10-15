-- PT: D02. Empresas ativas no Ceará, MEI incluídos, no último mês.
-- EN: D02. Active companies in Ceará, MEI included, in the latest month.
select
    max(data_base) as mes,
    sum(empresas_ativas) as empresas_ativas
from fct_empresas_ativas
where uf = 'CE'
  and data_base = (select max(data_base) from fct_empresas_ativas)
