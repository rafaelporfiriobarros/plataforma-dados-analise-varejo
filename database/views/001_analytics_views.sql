CREATE OR REPLACE VIEW gold.vw_kpis AS
SELECT
  (SELECT COALESCE(SUM(total_venda),0) FROM gold.fato_vendas_horario) AS faturamento_loja,
  (SELECT COALESCE(SUM(qtd_clientes),0) FROM gold.fato_vendas_horario) AS clientes,
  (SELECT COALESCE(SUM(qtd_produtos),0) FROM gold.fato_vendas_horario) AS produtos,
  (SELECT COALESCE(SUM(total_venda) / NULLIF(SUM(qtd_clientes),0),0) FROM gold.fato_vendas_horario) AS ticket_medio,
  COALESCE(SUM(valor_bruto) FILTER (WHERE status='Aprovada'),0) AS volume_cartoes,
  COALESCE(SUM(valor_liquido) FILTER (WHERE status='Aprovada'),0) AS receita_liquida_cartoes,
  COALESCE(SUM(valor_taxa) FILTER (WHERE status='Aprovada'),0) AS taxas_cartoes,
  COALESCE(SUM(valor_taxa) FILTER (WHERE status='Aprovada') / NULLIF(SUM(valor_bruto) FILTER (WHERE status='Aprovada'),0),0) AS taxa_efetiva
FROM gold.fato_pagamentos;

CREATE OR REPLACE VIEW gold.vw_vendas_por_hora AS
SELECT f.hora_key AS hora, h.turno, SUM(f.total_venda) AS total_venda,
       SUM(f.qtd_clientes) AS qtd_clientes, SUM(f.qtd_produtos) AS qtd_produtos,
       COALESCE(SUM(f.total_venda)/NULLIF(SUM(f.qtd_clientes),0),0) AS ticket_medio
FROM gold.fato_vendas_horario f JOIN gold.dim_horario h ON h.hora_key=f.hora_key
GROUP BY f.hora_key,h.turno;

CREATE OR REPLACE VIEW gold.vw_meios_pagamento AS
SELECT p.forma_pagamento, COUNT(*) AS transacoes, SUM(f.valor_bruto) AS valor_bruto,
       SUM(f.valor_taxa) AS valor_taxa, SUM(f.valor_liquido) AS valor_liquido
FROM gold.fato_pagamentos f JOIN gold.dim_pagamento p ON p.pagamento_key=f.pagamento_key
GROUP BY p.forma_pagamento;
