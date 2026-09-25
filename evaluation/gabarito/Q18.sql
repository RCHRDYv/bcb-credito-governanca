-- PT: Q18. Ticket médio por modalidade no último mês, calculado só sobre os
--     recortes com contagem de operações divulgada, com a parcela da
--     carteira que fica de fora.
-- EN: Q18. Average ticket by modality in the latest month, over slices with a
--     disclosed operation count only, and the portfolio share left out.
select
    m.codigo_modalidade,
    m.modalidade,
    sum(case when not f.contagem_suprimida then f.carteira_ativa else 0 end) as carteira_com_contagem,
    sum(f.numero_de_operacoes) as operacoes_divulgadas,
    cast(sum(case when not f.contagem_suprimida then f.carteira_ativa else 0 end) as double)
        / nullif(sum(f.numero_de_operacoes), 0) as ticket_medio,
    100 * cast(sum(case when f.contagem_suprimida then f.carteira_ativa else 0 end) as double)
        / cast(sum(f.carteira_ativa) as double) as carteira_sem_contagem_pct
from fct_carteira f
join dim_modalidade m
    on m.codigo_submodalidade = f.codigo_submodalidade
where f.data_base = (select max(data_base) from fct_carteira)
group by m.codigo_modalidade, m.modalidade
order by ticket_medio desc nulls last
