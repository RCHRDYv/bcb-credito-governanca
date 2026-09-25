-- PT: Q17, prova da ausência. As definições que citam garantia. Só a do home
--     equity (0211) declara garantia real; 0215 e 0216 citam "garantias"
--     apenas como item do contrato de capital de giro.
-- EN: Q17, proof of absence. Definitions that mention collateral: only home
--     equity (0211) declares real collateral.
select codigo_submodalidade, modalidade, submodalidade, definicao
from dim_modalidade
where lower(definicao) like '%garant%'
order by codigo_submodalidade
